from datetime import date
import math
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


def finite(value):
    if not math.isfinite(value):raise ValidationError("Enter a finite number.")

def number(label, maximum=None):
    validators = [finite, MinValueValidator(0)]
    if maximum is not None: validators.append(MaxValueValidator(maximum))
    return models.FloatField(label, blank=True, null=True, validators=validators)

class Patient(models.Model):
    study_id = models.CharField('Research number / study ID', max_length=40, unique=True)
    sex = models.CharField('Biological sex', max_length=16, choices=[('Male','Male'),('Female','Female'),('Other','Other'),('Unknown','Unknown')])
    age = models.PositiveSmallIntegerField('Age at enrolment (years)', validators=[MaxValueValidator(120)])
    enrolled_on = models.DateField(default=timezone.localdate)
    diagnosis = models.CharField(max_length=200, blank=True)
    synthetic = models.BooleanField(default=True, editable=False)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
        permissions = [('view_identity','View restricted identifiers'),('change_identity','Change restricted identifiers'),('export_research','Export research records'),('view_audit','View audit trail')]
    def clean(self):
        if self.enrolled_on and self.enrolled_on>timezone.localdate():raise ValidationError({"enrolled_on":"Enrolment date cannot be in the future."})
    def __str__(self): return self.study_id

class Identity(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='identity')
    hospital_number = models.CharField(max_length=100, blank=True)
    initials = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

class Procedure(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='procedures')
    date = models.DateField('Surgery date')
    approach = models.CharField(max_length=30, choices=[('Endoscopic','Endoscopic'),('Open','Open')])
    endoscopic_type = models.CharField(max_length=30, blank=True, choices=[('Uniportal','Uniportal'),('Biportal','Biportal')])
    operation = models.CharField('Specific operation', max_length=200)
    levels = models.CharField('Operated levels (comma-separated)', max_length=200)
    instrumented = models.BooleanField(default=False)
    duration_hours = number('Surgery duration (hours)')
    blood_loss_ml = number('Estimated blood loss (mL)')
    anaesthesia = models.CharField(max_length=30, choices=[('Local','Local'),('Regional','Regional'),('General','General'),('Combined','Combined'),('Other','Other')])
    asa = models.PositiveSmallIntegerField('ASA grade', blank=True, null=True, validators=[MinValueValidator(1),MaxValueValidator(6)])
    admission_date = models.DateField(blank=True, null=True)
    discharge_date = models.DateField(blank=True, null=True)
    hospital_days = number('Hospital stay (days)')
    details = models.JSONField(default=dict, blank=True)
    class Meta: ordering=['date','pk']
    def clean(self):
        errors={}
        if self.date and self.date>timezone.localdate(): errors['date']='Record completed surgery only; future dates are not allowed.'
        if self.approach=='Open' and self.endoscopic_type: errors['endoscopic_type']='Leave blank for open surgery.'
        if self.approach=='Endoscopic' and not self.endoscopic_type: errors['endoscopic_type']='Choose uniportal or biportal.'
        if self.admission_date and self.date and self.admission_date>self.date: errors['admission_date']='Admission cannot follow surgery.'
        if self.discharge_date and self.date and self.discharge_date<self.date: errors['discharge_date']='Discharge cannot precede surgery.'
        if self.admission_date and self.discharge_date and self.discharge_date<self.admission_date: errors['discharge_date']='Discharge cannot precede admission.'
        if errors: raise ValidationError(errors)
    def __str__(self): return f'{self.patient.study_id}: {self.date} — {self.operation}'

class Treatment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='treatments')
    treatment = models.CharField('Non-operative treatment', max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    ongoing = models.BooleanField(default=False)
    outcome = models.TextField(blank=True)
    steroid_injection = models.BooleanField(default=False)
    injection_frequency = models.CharField(max_length=100, blank=True)
    injection_outcome = models.TextField(blank=True)
    class Meta: ordering=['start_date','pk']
    def clean(self):
        errors={}
        if self.start_date and self.start_date>timezone.localdate(): errors['start_date']='Start date cannot be in the future.'
        if self.ongoing and self.end_date: errors['end_date']='Ongoing treatment must not have an end date.'
        if not self.ongoing and not self.end_date: errors['end_date']='Provide the end date or mark ongoing.'
        if self.end_date and self.start_date and self.end_date<self.start_date: errors['end_date']='End date cannot precede start date.'
        if self.end_date and self.end_date>timezone.localdate(): errors['end_date']='End date cannot be in the future.'
        if errors: raise ValidationError(errors)
    def weeks(self, as_of=None):
        finish=min(self.end_date or as_of or timezone.localdate(),as_of or timezone.localdate())
        return round((finish-self.start_date).days/7,2)

class Assessment(models.Model):
    TIMEPOINTS=[('baseline','Baseline'),('postop','Immediate postoperative'),('3m','3 months'),('6m','6 months'),('9m','9 months'),('1y','1 year'),('2y','2 years'),('unscheduled','Unscheduled')]
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='assessments')
    procedure = models.ForeignKey(Procedure, on_delete=models.PROTECT, related_name='assessments', blank=True, null=True)
    date = models.DateField('Assessment date')
    timepoint = models.CharField(max_length=20, choices=TIMEPOINTS)
    vas_main = number('VAS main complaint (0–10)',10)
    pain_site = models.CharField(max_length=10, blank=True, choices=[('Back','Back'),('Neck','Neck'),('Other','Other')])
    vas_worst_radicular = number('VAS worst radicular limb (0–10)',10)
    vas_other_radicular = number('VAS other radicular limb (0–10)',10)
    worst_limb = models.CharField('Worst radicular limb at this visit',max_length=20,blank=True,choices=[('Left arm','Left arm'),('Right arm','Right arm'),('Left leg','Left leg'),('Right leg','Right leg'),('None','None')])
    odi = number('ODI (0–100)',100)
    ndi = number('NDI normalised score (0–100)',100)
    walking_m = number('Walking distance (metres)')
    walking_definition = models.CharField('Walking measurement definition / protocol',max_length=200,blank=True)
    sf_physical_functioning = number('SF-36 physical functioning (0–100)',100)
    sf_role_physical = number('SF-36 role physical (0–100)',100)
    sf_bodily_pain = number('SF-36 bodily pain (0–100)',100)
    sf_general_health = number('SF-36 general health (0–100)',100)
    sf_vitality = number('SF-36 vitality (0–100)',100)
    sf_social_functioning = number('SF-36 social functioning (0–100)',100)
    sf_role_emotional = number('SF-36 role emotional (0–100)',100)
    sf_mental_health = number('SF-36 mental health (0–100)',100)
    sf_pcs = models.FloatField('SF-36 PCS',blank=True,null=True,validators=[finite])
    sf_mcs = models.FloatField('SF-36 MCS',blank=True,null=True,validators=[finite])
    sf_version = models.CharField('SF-36 instrument version',max_length=100,blank=True)
    sf_scoring_method = models.CharField('SF-36 component scoring method / reference norms',max_length=250,blank=True)
    status = models.CharField('Visit status',max_length=20,choices=[('Completed','Completed'),('Missed','Missed'),('Declined','Declined'),('Not due','Not due')],default='Completed')
    details = models.JSONField(default=dict,blank=True)
    class Meta:
        ordering=['date','pk']
        constraints=[models.UniqueConstraint(fields=['patient','procedure','timepoint'],condition=models.Q(procedure__isnull=False)&~models.Q(timepoint='unscheduled'),name='unique_procedure_visit')]
    def clean(self):
        errors={}
        if self.date and self.date>timezone.localdate() and self.status!='Not due': errors['date']='Future dates require the Not due status.'
        if self.procedure_id and self.procedure.patient_id!=self.patient_id: errors['procedure']='Procedure must belong to this patient.'
        if self.timepoint!='baseline' and not self.procedure_id: errors['procedure']='Link postoperative follow-up to an operation.'
        if self.procedure_id and self.date:
            if self.timepoint=='baseline' and self.date>self.procedure.date: errors['date']='Baseline cannot follow the operation.'
            elif self.timepoint!='baseline' and self.date<self.procedure.date: errors['date']='Follow-up cannot precede the operation.'
        scores=['vas_main','vas_worst_radicular','vas_other_radicular','odi','ndi','walking_m']+[f.name for f in self._meta.fields if f.name.startswith('sf_') and isinstance(f,models.FloatField)]
        if self.status!='Completed' and any(getattr(self,f) is not None for f in scores): errors['status']='Non-completed visits must not contain outcome scores.'
        if any(getattr(self,f.name) is not None for f in self._meta.fields if f.name.startswith('sf_') and isinstance(f,models.FloatField)) and not self.sf_version: errors['sf_version']='Record instrument version when entering SF-36 scores.'
        if (self.sf_pcs is not None or self.sf_mcs is not None) and not self.sf_scoring_method: errors['sf_scoring_method']='Record the scoring method for PCS/MCS.'
        if errors: raise ValidationError(errors)

class Event(models.Model):
    patient=models.ForeignKey(Patient,on_delete=models.PROTECT,related_name='events')
    procedure=models.ForeignKey(Procedure,on_delete=models.PROTECT,blank=True,null=True,related_name='events')
    date=models.DateField()
    kind=models.CharField(max_length=30,choices=[('Intraoperative complication','Intraoperative complication'),('Postoperative complication','Postoperative complication'),('Anaesthetic complication','Anaesthetic complication'),('Reoperation','Reoperation'),('Symptom recurrence','Symptom recurrence')])
    description=models.CharField(max_length=250)
    severity=models.CharField(max_length=40,blank=True)
    management=models.TextField(blank=True)
    reoperation_procedure=models.CharField(max_length=200,blank=True)
    class Meta: ordering=['date','pk']
    def clean(self):
        errors={}
        if self.date and self.date>timezone.localdate():errors['date']='Event date cannot be in the future.'
        if self.procedure_id and self.procedure.patient_id!=self.patient_id:errors['procedure']='Procedure must belong to this patient.'
        if self.procedure_id and self.date and self.date<self.procedure.date:errors['date']='Event cannot precede the linked operation.'
        if self.kind=='Reoperation' and not self.reoperation_procedure:errors['reoperation_procedure']='Specify the reoperation performed.'
        if errors:raise ValidationError(errors)

class Audit(models.Model):
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)
    action=models.CharField(max_length=30)
    entity=models.CharField(max_length=50)
    object_id=models.CharField(max_length=60,blank=True)
    changed_fields=models.JSONField(default=list)
    timestamp=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-timestamp']

class LoginThrottle(models.Model):
    key=models.CharField(max_length=64,unique=True)
    failures=models.PositiveIntegerField(default=0)
    blocked_until=models.DateTimeField(null=True,blank=True)
