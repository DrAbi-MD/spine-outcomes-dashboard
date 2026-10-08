import random
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from registry.models import Patient, Procedure, Assessment, Treatment, Event

class Command(BaseCommand):
    help='Add 60 deterministic synthetic patients. No patient records are deleted or changed.'
    @transaction.atomic
    def handle(self,*args,**options):
        if Patient.objects.filter(study_id__startswith='DEMO-').exists():
            self.stdout.write('DEMO records already exist; no records changed.');return
        rng=random.Random(3107);today=timezone.localdate()
        for i in range(1,61):
            d=today-timedelta(days=210+i*4)
            p=Patient.objects.create(study_id=f'DEMO-{i:03}',sex=rng.choice(['Male','Female']),age=rng.randint(24,78),enrolled_on=d-timedelta(days=42),diagnosis=rng.choice(['Lumbar disc herniation','Lumbar canal stenosis','Cervical radiculopathy']),details={'country':'Nigeria','weight_kg':70,'height_cm':170,'bmi':24.22})
            op=Procedure.objects.create(patient=p,date=d,approach='Open' if i%3==0 else 'Endoscopic',endoscopic_type='' if i%3==0 else ('Uniportal' if i%2 else 'Biportal'),operation='Synthetic decompression',levels='L4-L5',anaesthesia='General',asa=2,duration_hours=round(rng.uniform(1,4),2),blood_loss_ml=rng.choice([30,50,100,200]),admission_date=d-timedelta(days=1),discharge_date=d+timedelta(days=2),hospital_days=3)
            Treatment.objects.create(patient=p,treatment='Synthetic physiotherapy',start_date=d-timedelta(days=42),end_date=d-timedelta(days=1),ongoing=False,outcome='Synthetic partial response')
            for tp,days,base in [('baseline',-1,7),('postop',2,4),('3m',90,3),('6m',180,2)]:
                missing=tp=='6m' and i%9==0
                values={} if missing else {'vas_main':round(max(0,min(10,base+rng.uniform(-1,1))),1),'odi':round(max(0,base*9+rng.uniform(-8,8)),1),'walking_m':max(20,1000-base*110),'walking_definition':'Synthetic self-reported distance before symptom limitation','sf_version':'Synthetic demonstration (not a scored instrument)','sf_scoring_method':'Synthetic component values; no clinical norms','sf_pcs':round(55-base*3,1),'sf_mcs':round(55-base,1)}
                if not missing:
                    for field in Assessment._meta.fields:
                        if field.name.startswith('sf_') and field.name not in ['sf_pcs','sf_mcs','sf_version','sf_scoring_method']:values[field.name]=round(min(100,100-base*8+rng.uniform(-5,5)),1)
                a=Assessment(patient=p,procedure=op,date=d+timedelta(days=days),timepoint=tp,status='Missed' if missing else 'Completed',**values);a.full_clean();a.save()
            if i%10==0:Event.objects.create(patient=p,procedure=op,date=d+timedelta(days=3),kind='Postoperative complication',description='Synthetic wound complication',severity='Minor',management='Synthetic management')
        self.stdout.write(self.style.SUCCESS('Added 60 synthetic patients, 60 procedures, 240 visit records, 60 treatments and 6 events.'))
