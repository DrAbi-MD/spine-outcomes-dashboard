import csv
import hashlib
import io
import json
import zipfile
from datetime import timedelta
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Patient, Identity, Procedure, Assessment, Treatment, Event, Audit, LoginThrottle
from .forms import PatientForm, IdentityForm, ProcedureForm, AssessmentForm, TreatmentForm, EventForm, CohortForm
from .analysis import make_report, cohort, SCORES

class RegistryLoginView(LoginView):
    def post(self,request,*args,**kwargs):
        # Persistent per-client throttle for this loopback-only prototype.
        key=hashlib.sha256(request.META.get('REMOTE_ADDR','').encode()).hexdigest()
        obj,_=LoginThrottle.objects.get_or_create(key=key)
        if obj.blocked_until and obj.blocked_until>timezone.now():return HttpResponse('Too many unsuccessful login attempts. Try again in 15 minutes.',status=429)
        if obj.blocked_until:
            obj.failures=0;obj.blocked_until=None;obj.save()
        self.throttle=obj
        return super().post(request,*args,**kwargs)
    def form_invalid(self,form):
        obj=self.throttle;obj.failures+=1
        if obj.failures>=5:obj.blocked_until=timezone.now()+timedelta(minutes=15)
        obj.save();return super().form_invalid(form)
    def form_valid(self,form):
        self.throttle.delete()
        response=super().form_valid(form)
        Audit.objects.create(actor=self.request.user,action='login',entity='session')
        return response


def permitted(codename):
    def outer(func):
        @wraps(func)
        @login_required
        def inner(request,*args,**kwargs):
            if not request.user.has_perm('registry.'+codename):raise PermissionDenied
            return func(request,*args,**kwargs)
        return inner
    return outer


def get_report(request):
    form=CohortForm(request.GET or None)
    if not request.GET:
        cleaned={}
    elif form.is_valid():cleaned=form.cleaned_data
    else:return form,None
    return form,make_report(cleaned)

@permitted('view_patient')
def dashboard(request):
    form,result=get_report(request)
    if result is None:return render(request,'registry/dashboard.html',{'filter_form':form,'invalid':True},status=400)
    report,patients,procedures,visits,events=result
    return render(request,'registry/dashboard.html',{'filter_form':form,'report':report,'patients':patients[:15],'query':request.GET.urlencode()})

@permitted('view_patient')
def patient_list(request):
    from django.core.paginator import Paginator
    form,result=get_report(request)
    if result is None:return render(request,'registry/patients.html',{'filter_form':form},status=400)
    _,patients,*_=result
    return render(request,'registry/patients.html',{'filter_form':form,'page':Paginator(patients,25).get_page(request.GET.get('page'))})

@permitted('view_patient')
def patient_detail(request,pk):
    patient=get_object_or_404(Patient,pk=pk)
    # Free text may contain identifiers; detailed clinical notes limited to entry users.
    show_notes=request.user.has_perm('registry.change_patient')
    Audit.objects.create(actor=request.user,action='view',entity='Patient',object_id=str(pk))
    return render(request,'registry/patient.html',{'patient':patient,'show_notes':show_notes,'assessments':patient.assessments.select_related('procedure'),'procedures':patient.procedures.all(),'treatments':patient.treatments.all(),'events':patient.events.all()})

@login_required
def patient_form(request,pk=None):
    perm='change_patient' if pk else 'add_patient'
    if not request.user.has_perm('registry.'+perm):raise PermissionDenied
    instance=get_object_or_404(Patient,pk=pk) if pk else None
    form=PatientForm(request.POST or None,instance=instance)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            obj=form.save()
            Audit.objects.create(actor=request.user,action='update' if pk else 'create',entity='Patient',object_id=str(obj.pk),changed_fields=form.changed_data)
        messages.success(request,'Patient record saved.');return redirect('patient',pk=obj.pk)
    return render(request,'registry/form.html',{'form':form,'title':'Edit patient' if pk else 'Register patient','back':instance})

FORMS={'procedure':(Procedure,ProcedureForm),'assessment':(Assessment,AssessmentForm),'treatment':(Treatment,TreatmentForm),'event':(Event,EventForm)}
@login_required
def record_form(request,patient_pk,kind,pk=None):
    if kind not in FORMS:return HttpResponse(status=404)
    model,formclass=FORMS[kind]
    if not request.user.has_perm(f'registry.{"change" if pk else "add"}_{kind}'):raise PermissionDenied
    patient=get_object_or_404(Patient,pk=patient_pk)
    instance=get_object_or_404(model,pk=pk,patient=patient) if pk else model(patient=patient)
    kwargs={'patient':patient} if kind in ['assessment','event'] else {}
    form=formclass(request.POST or None,instance=instance,**kwargs)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            obj=form.save()
            Audit.objects.create(actor=request.user,action='update' if pk else 'create',entity=model.__name__,object_id=str(obj.pk),changed_fields=form.changed_data)
        messages.success(request,'Record saved.');return redirect('patient',pk=patient.pk)
    return render(request,'registry/form.html',{'form':form,'title':('Edit ' if pk else 'Add ')+kind,'back':patient})

@login_required
def identity(request,pk):
    if not request.user.has_perm('registry.view_identity'):raise PermissionDenied
    patient=get_object_or_404(Patient,pk=pk)
    obj=Identity.objects.filter(patient=patient).first() or Identity(patient=patient)
    form=IdentityForm(request.POST or None,instance=obj)
    if request.method=='POST':
        if not request.user.has_perm('registry.change_identity'):raise PermissionDenied
        if form.is_valid():
            with transaction.atomic():
                form.save();Audit.objects.create(actor=request.user,action='update',entity='Identity',object_id=str(patient.pk),changed_fields=form.changed_data)
            return redirect('patient',pk=patient.pk)
    if request.method=='GET':Audit.objects.create(actor=request.user,action='view',entity='Identity',object_id=str(patient.pk))
    return render(request,'registry/form.html',{'form':form,'title':'Restricted identification record','back':patient,'restricted':True,'readonly':not request.user.has_perm('registry.change_identity')})

@permitted('view_audit')
def audit(request):
    return render(request,'registry/audit.html',{'logs':Audit.objects.select_related('actor')[:300]})

@permitted('view_patient')
def analysis(request):
    form,result=get_report(request)
    return render(request,'registry/analysis.html',{'filter_form':form,'report':result[0] if result else None,'query':request.GET.urlencode()},status=200 if result else 400)


def csv_safe(value):
    if value is None:return ''
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@','\t','\r')):return "'"+value
    return value

@permitted('export_research')
def export(request,kind):
    form,result=get_report(request)
    if not result:return HttpResponse('Correct the cohort filter values before exporting.',status=400)
    report,patients,procedures,visits,events=result
    if kind not in ['report','json','summary','data','bundle']:return HttpResponse(status=404)
    Audit.objects.create(actor=request.user,action='export',entity=kind)
    if kind=='bundle':
        from .exports import research_bundle
        response=HttpResponse(research_bundle(result),content_type='application/zip');extension='zip'
    elif kind=='json':
        response=HttpResponse(json.dumps(report,indent=2),content_type='application/json');extension='json'
    elif kind=='report':
        response=HttpResponse(render_to_string('registry/report.html',{'report':report}),content_type='text/html; charset=utf-8');extension='html'
    else:
        buffer=io.StringIO(newline='');writer=csv.writer(buffer)
        if kind=='summary':
            keys=['timepoint','score','unit','n','mean','sd','median','min','max','available_visits','missing','pooling_suppressed']
            writer.writerow(keys)
            for row in report['summary']:writer.writerow([csv_safe(row.get(k)) for k in keys])
        else:
            # Typed research variables only; no identity or narrative free text.
            keys=['study_id','sex','age','procedure_id','approach','operation_date','duration_hours','blood_loss_ml','hospital_days','assessment_date','timepoint','status']+SCORES+['sf_version','sf_scoring_method']
            writer.writerow(keys)
            for v in visits.select_related('patient','procedure'):
                p=v.procedure
                row=[v.patient.study_id,v.patient.sex,v.patient.age,p.pk if p else None,p.approach if p else None,p.date if p else None,p.duration_hours if p else None,p.blood_loss_ml if p else None,p.hospital_days if p else None,v.date,v.timepoint,v.status]+[getattr(v,s) for s in SCORES]+[v.sf_version,v.sf_scoring_method]
                writer.writerow([csv_safe(x) for x in row])
        response=HttpResponse(buffer.getvalue(),content_type='text/csv; charset=utf-8');extension='csv'
    response['Content-Disposition']=f'attachment; filename="zoe-{kind}-{report["cutoff"]}.{extension}"'
    return response
