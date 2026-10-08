import csv
import io
import json
import math
import sqlite3
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Patient, Identity, Procedure, Assessment, Treatment, Event, Audit
from .forms import AssessmentForm, ProcedureForm
from .analysis import make_report, describe

class RegistryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('setup_roles',stdout=io.StringIO())
        U=get_user_model()
        cls.entry=U.objects.create_user('entry',password='An example password 740!')
        cls.entry.groups.add(Group.objects.get(name='Data Entry'))
        cls.analyst=U.objects.create_user('analyst',password='Another example 752!')
        cls.analyst.groups.add(Group.objects.get(name='Analyst'))
        cls.admin=U.objects.create_superuser('owner',password='An admin example 755!')
        cls.d=timezone.localdate()-timedelta(days=200)
        cls.p=Patient.objects.create(study_id='TEST-001',sex='Female',age=48,enrolled_on=cls.d-timedelta(days=20),diagnosis='Clinical narrative SECRET-NOTE',details={'comments':'SECRET-NOTE'})
        Identity.objects.create(patient=cls.p,hospital_number='SECRET-HOSPITAL-ID',initials='SECRET-INITIALS',address='SECRET-ADDRESS')
        cls.op=Procedure.objects.create(patient=cls.p,date=cls.d,approach='Open',operation='Synthetic decompression',levels='L4-L5',anaesthesia='General',duration_hours=2,blood_loss_ml=100,hospital_days=3)
        Assessment.objects.create(patient=cls.p,procedure=cls.op,date=cls.d-timedelta(days=1),timepoint='baseline',vas_main=8,odi=60,walking_m=100,walking_definition='Self-report')
        Assessment.objects.create(patient=cls.p,procedure=cls.op,date=cls.d+timedelta(days=90),timepoint='3m',vas_main=0,odi=None,walking_m=1000,walking_definition='Self-report')
    def login(self,user):self.client.force_login(user)
    def test_authentication_permissions_and_private_cache(self):
        self.assertEqual(self.client.get('/').status_code,302)
        self.login(self.analyst)
        self.assertEqual(self.client.get(reverse('identity',args=[self.p.pk])).status_code,403)
        self.assertEqual(self.client.get(reverse('patient_new')).status_code,403)
        self.assertEqual(self.client.post(reverse('patient_edit',args=[self.p.pk]),{'study_id':'ALTER'}).status_code,403)
        r=self.client.get('/');self.assertEqual(r.status_code,200);self.assertIn('no-store',r['Cache-Control'])
        self.assertIn("frame-ancestors 'none'",r['Content-Security-Policy'])
        self.login(self.entry);self.assertEqual(self.client.get(reverse('export',args=['data'])).status_code,403)
    def test_csrf_required_for_mutation(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.entry)
        self.assertEqual(c.post(reverse('patient_new'),{'study_id':'TEST-002'}).status_code,403)
        c.get(reverse('patient_new'));token=c.cookies['csrftoken'].value
        r=c.post(reverse('patient_new'),{'study_id':'TEST-002','sex':'Male','age':30,'enrolled_on':timezone.localdate().isoformat(),'csrfmiddlewaretoken':token})
        self.assertEqual(r.status_code,302)
        p=Patient.objects.get(study_id='TEST-002');self.assertTrue(p.synthetic)
        audit=Audit.objects.get(action='create',entity='Patient',object_id=str(p.pk))
        self.assertIn('study_id',audit.changed_fields);self.assertNotIn('TEST-002',json.dumps(audit.changed_fields))
    def test_all_screens_and_export_types_render(self):
        self.login(self.admin)
        urls=['/',reverse('patients'),reverse('analysis'),reverse('patient',args=[self.p.pk]),reverse('patient_new'),reverse('patient_edit',args=[self.p.pk]),reverse('identity',args=[self.p.pk]),reverse('audit')]
        urls += [reverse('record_new',args=[self.p.pk,kind]) for kind in ['procedure','assessment','treatment','event']]
        urls += [reverse('export',args=[kind]) for kind in ['report','summary','data','json','bundle']]
        for url in urls:
            with self.subTest(url=url):self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.client.get('/?as_of=2099-01-01').status_code,400)
    def test_zero_missing_and_paired_denominators(self):
        report,*_=make_report({})
        vas=next(r for r in report['summary'] if r['timepoint']=='3m' and r['score']=='vas_main')
        odi=next(r for r in report['summary'] if r['timepoint']=='3m' and r['score']=='odi')
        self.assertEqual((vas['n'],vas['mean'],vas['missing']),(1,0,0));self.assertEqual((odi['n'],odi['missing']),(0,1))
        pair=next(r for r in report['paired'] if r['timepoint']=='3m' and r['score']=='vas_main');self.assertEqual(pair['mean'],8)
        self.assertFalse(any(r['timepoint']=='3m' and r['score']=='odi' for r in report['paired']))
        self.assertEqual(describe([0,None,2])['mean'],1);self.assertIsNone(describe([3])['sd'])
    def test_surgical_filters_exclude_other_operations_and_unlinked_visits(self):
        op=Procedure.objects.create(patient=self.p,date=self.d,approach='Endoscopic',endoscopic_type='Uniportal',operation='Other',levels='L3-L4',anaesthesia='General')
        Assessment.objects.create(patient=self.p,procedure=op,date=self.d,timepoint='baseline',vas_main=10)
        Assessment.objects.create(patient=self.p,date=self.d,timepoint='baseline',vas_main=9)
        report,*_=make_report({'approach':'Open'})
        row=next(r for r in report['summary'] if r['timepoint']=='baseline' and r['score']=='vas_main')
        self.assertEqual((report['patients'],report['procedures'],row['n'],row['mean']),(1,1,1,8))
        self.assertEqual(make_report({'as_of':self.d-timedelta(days=2)})[0]['procedures'],0)
    def test_form_rejects_foreign_procedure_and_duplicate_timepoint(self):
        other=Patient.objects.create(study_id='OTHER',sex='Male',age=20,enrolled_on=self.d)
        data={'procedure':self.op.pk,'date':self.d.isoformat(),'timepoint':'baseline','status':'Completed'}
        f=AssessmentForm(data,patient=other,instance=Assessment(patient=other));self.assertFalse(f.is_valid());self.assertIn('procedure',f.errors)
        f=AssessmentForm(data,patient=self.p,instance=Assessment(patient=self.p));self.assertFalse(f.is_valid());self.assertIn('timepoint',f.errors)
    def test_score_validation_sf_method_and_visit_status(self):
        a=Assessment(patient=self.p,procedure=self.op,date=self.d,timepoint='unscheduled',vas_main=11)
        with self.assertRaises(ValidationError):a.full_clean()
        a.vas_main=float('nan')
        with self.assertRaises(ValidationError):a.full_clean()
        a.vas_main=None;a.sf_pcs=40
        with self.assertRaises(ValidationError) as err:a.full_clean()
        self.assertIn('sf_version',err.exception.message_dict);self.assertIn('sf_scoring_method',err.exception.message_dict)
        a.sf_version='v1';a.sf_scoring_method='Norm A';a.full_clean()
        a.status='Missed'
        with self.assertRaises(ValidationError):a.full_clean()
    def test_sf36_incompatible_pooling_is_suppressed(self):
        a,b=list(self.p.assessments.all())
        for v,method in [(a,'A'),(b,'B')]:v.sf_pcs=40;v.sf_version='v1';v.sf_scoring_method=method;v.save()
        report=make_report({})[0]
        self.assertIn('sf_pcs',report['pooling_suppressed'])
        row=next(r for r in report['summary'] if r['timepoint']=='baseline' and r['score']=='sf_pcs')
        self.assertEqual(row['n'],1);self.assertIsNone(row['mean'])
        self.assertFalse(any(r['score']=='sf_pcs' for r in report['paired']))
    def test_treatment_dates_ongoing_duration_and_cutoff(self):
        t=Treatment(patient=self.p,treatment='Synthetic',start_date=self.d,ongoing=True)
        t.full_clean();self.assertEqual(t.weeks(self.d+timedelta(days=21)),3)
        t.end_date=self.d+timedelta(days=42)
        with self.assertRaises(ValidationError):t.full_clean()
        t.ongoing=False;t.full_clean();self.assertEqual(t.weeks(self.d+timedelta(days=21)),3)
        t.end_date=self.d-timedelta(days=1)
        with self.assertRaises(ValidationError):t.full_clean()
    def test_procedure_dates_and_hospital_stay(self):
        data={'date':self.d.isoformat(),'approach':'Open','operation':'Demo','levels':'l4-l5','anaesthesia':'General','admission_date':self.d.isoformat(),'discharge_date':(self.d+timedelta(days=3)).isoformat()}
        f=ProcedureForm(data,instance=Procedure(patient=self.p));self.assertTrue(f.is_valid(),f.errors);self.assertEqual(f.cleaned_data['hospital_days'],3)
        data['hospital_days']=4;f=ProcedureForm(data,instance=Procedure(patient=self.p));self.assertFalse(f.is_valid());self.assertIn('hospital_days',f.errors)
    def test_research_exports_omit_identity_narratives_and_escape_formulas(self):
        self.p.study_id='=1+1';self.p.save();self.login(self.analyst)
        for kind in ['data','bundle','json','report']:
            r=self.client.get(reverse('export',args=[kind]));self.assertEqual(r.status_code,200)
            if kind=='bundle':
                z=zipfile.ZipFile(io.BytesIO(r.content));contents='\n'.join(z.read(n).decode() for n in z.namelist())
                self.assertEqual(len(list(csv.reader(io.StringIO(z.read('patients.csv').decode())))),2)
                self.assertIn("'=1+1",z.read('patients.csv').decode())
            else:contents=r.content.decode()
            for secret in ['SECRET-HOSPITAL-ID','SECRET-INITIALS','SECRET-ADDRESS','SECRET-NOTE']:self.assertNotIn(secret,contents)
        self.assertIn("'=1+1",self.client.get(reverse('export',args=['data'])).content.decode())
    def test_login_throttle_persists(self):
        for _ in range(5):self.client.post(reverse('login'),{'username':'bad','password':'wrong'})
        self.assertEqual(self.client.post(reverse('login'),{'username':'bad','password':'wrong'}).status_code,429)
    def test_synthetic_seed_is_idempotent_and_complete(self):
        call_command('seed_demo',stdout=io.StringIO());counts=(Patient.objects.count(),Procedure.objects.count(),Assessment.objects.count())
        call_command('seed_demo',stdout=io.StringIO());self.assertEqual(counts,(Patient.objects.count(),Procedure.objects.count(),Assessment.objects.count()))
        self.assertEqual(Patient.objects.filter(study_id__startswith='DEMO-').count(),60)
        self.assertEqual(Assessment.objects.filter(patient__study_id__startswith='DEMO-').count(),240)
    def test_second_operation_pairs_are_independent(self):
        op=Procedure.objects.create(patient=self.p,date=self.d+timedelta(days=100),approach='Open',operation='Second surgery',levels='L3-L4',anaesthesia='General')
        Assessment.objects.create(patient=self.p,procedure=op,date=op.date,timepoint='baseline',vas_main=6)
        Assessment.objects.create(patient=self.p,procedure=op,date=op.date+timedelta(days=30),timepoint='3m',vas_main=4)
        report=make_report({})[0]
        row=next(r for r in report['paired'] if r['score']=='vas_main' and r['timepoint']=='3m')
        self.assertEqual((report['patients'],report['procedures'],row['n'],row['mean']),(1,2,2,5))
    def test_events_validate_patient_dates_and_reoperation(self):
        e=Event(patient=self.p,procedure=self.op,date=self.d-timedelta(days=1),kind='Reoperation',description='Synthetic')
        with self.assertRaises(ValidationError) as err:e.full_clean()
        self.assertIn('date',err.exception.message_dict);self.assertIn('reoperation_procedure',err.exception.message_dict)
        e.date=self.d+timedelta(days=20);e.reoperation_procedure='Synthetic revision';e.full_clean();e.save()
        self.assertEqual(make_report({})[0]['reoperation_events'],1)
    def test_identifier_manager_access_is_separately_audited(self):
        u=get_user_model().objects.create_user('custodian',password='Example custodian 743!')
        u.groups.add(Group.objects.get(name='Identifier Manager'));self.login(u)
        r=self.client.get(reverse('identity',args=[self.p.pk]));self.assertContains(r,'SECRET-HOSPITAL-ID')
        self.assertTrue(Audit.objects.filter(actor=u,entity='Identity',action='view').exists())
        self.assertEqual(self.client.get(reverse('patient_edit',args=[self.p.pk])).status_code,403)
