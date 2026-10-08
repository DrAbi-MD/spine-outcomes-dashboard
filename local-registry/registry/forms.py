from django import forms
from .models import Patient, Identity, Procedure, Assessment, Treatment, Event
from .schema import PATIENT_FIELDS, PROCEDURE_FIELDS, ASSESSMENT_FIELDS

class DetailForm(forms.ModelForm):
    supplemental=[]
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for key,label,kind,choices in self.supplemental:
            if kind=='choice': field=forms.ChoiceField(choices=[('','Not recorded')]+[(x,x) for x in choices],required=False,label=label)
            elif kind in ['number','signed']: field=forms.FloatField(required=False,label=label, min_value=0 if kind=='number' else None)
            else: field=forms.CharField(required=False,label=label,widget=forms.Textarea(attrs={'rows':3}) if kind=='long' else forms.TextInput())
            field.initial=(self.instance.details or {}).get(key)
            self.fields['extra_'+key]=field
        for name,field in self.fields.items():
            if isinstance(field,forms.DateField): field.widget=forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d')
            if isinstance(field,forms.FloatField): field.widget.attrs['step']='any'
            if isinstance(field.widget,forms.Textarea): field.widget.attrs['rows']=3
    def save(self,commit=True):
        obj=super().save(commit=False)
        obj.details={key:self.cleaned_data.get('extra_'+key) for key,*_ in self.supplemental if self.cleaned_data.get('extra_'+key) not in [None,'']}
        if isinstance(obj,Patient):
            h=obj.details.get('height_cm'); w=obj.details.get('weight_kg')
            if h and w:obj.details['bmi']=round(w/(h/100)**2,2)
        if commit:obj.save()
        return obj

class PatientForm(DetailForm):
    supplemental=PATIENT_FIELDS
    class Meta:
        model=Patient
        fields=['study_id','sex','age','enrolled_on','diagnosis']
    def clean_extra_height_cm(self):
        v=self.cleaned_data.get('extra_height_cm')
        if v is not None and v<=0:raise forms.ValidationError('Height must be greater than zero.')
        return v

class IdentityForm(forms.ModelForm):
    class Meta: model=Identity;fields=['hospital_number','initials','address']

class ProcedureForm(DetailForm):
    supplemental=PROCEDURE_FIELDS
    class Meta:
        model=Procedure
        exclude=['patient','details']
    def clean_levels(self):
        values=[x.strip().upper() for x in self.cleaned_data['levels'].split(',') if x.strip()]
        if not values:raise forms.ValidationError('Specify at least one operated level.')
        if len(set(values))!=len(values):raise forms.ValidationError('Remove duplicate levels.')
        return ', '.join(values)
    def clean(self):
        data=super().clean()
        a,b=data.get('admission_date'),data.get('discharge_date')
        if a and b and b>=a:
            computed=(b-a).days
            entered=data.get('hospital_days')
            if entered is not None and entered!=computed:self.add_error('hospital_days','Does not match admission/discharge dates. Same-day stay is 0 calendar days.')
            else:data['hospital_days']=computed
        return data

class AssessmentForm(DetailForm):
    supplemental=ASSESSMENT_FIELDS
    class Meta:model=Assessment;exclude=['patient','details']
    def __init__(self,*args,patient,**kwargs):
        super().__init__(*args,**kwargs)
        self.patient=patient
        self.fields['procedure'].queryset=patient.procedures.all()
        self.fields['procedure'].help_text='Link baseline and follow-up to the same operation for paired analysis.'
        self.fields['ndi'].help_text='Enter normalised percent, not the raw 0–50 score.'
        self.fields['sf_pcs'].help_text='Enter an externally scored summary. No automatic component scoring is applied.'
        self.fields['date'].help_text='For missed visits use the planned assessment date.'

    def clean(self):
        data=super().clean()
        procedure=data.get('procedure');tp=data.get('timepoint')
        if procedure and tp and tp!='unscheduled':
            existing=Assessment.objects.filter(patient=self.patient,procedure=procedure,timepoint=tp).exclude(pk=self.instance.pk)
            if existing.exists():self.add_error('timepoint','This operation already has that visit. Edit the existing visit or choose Unscheduled.')
        return data

class TreatmentForm(forms.ModelForm):
    class Meta:
        model=Treatment;exclude=['patient']
        widgets={'start_date':forms.DateInput(attrs={'type':'date'}),'end_date':forms.DateInput(attrs={'type':'date'}),'outcome':forms.Textarea(attrs={'rows':3}),'injection_outcome':forms.Textarea(attrs={'rows':3})}

class EventForm(forms.ModelForm):
    class Meta:
        model=Event;exclude=['patient']
        widgets={'date':forms.DateInput(attrs={'type':'date'}),'management':forms.Textarea(attrs={'rows':3})}
    def __init__(self,*args,patient,**kwargs):
        super().__init__(*args,**kwargs);self.fields['procedure'].queryset=patient.procedures.all()

class CohortForm(forms.Form):
    q=forms.CharField(label='Study ID or diagnosis',required=False)
    sex=forms.ChoiceField(choices=[('','All sexes')]+Patient._meta.get_field('sex').choices,required=False)
    approach=forms.ChoiceField(choices=[('','All approaches')]+Procedure._meta.get_field('approach').choices,required=False)
    surgery_from=forms.DateField(label='Surgery from',required=False,widget=forms.DateInput(attrs={'type':'date'}))
    surgery_to=forms.DateField(label='Surgery to',required=False,widget=forms.DateInput(attrs={'type':'date'}))
    as_of=forms.DateField(label='Data cutoff',required=False,widget=forms.DateInput(attrs={'type':'date'}))
    def clean(self):
        from django.utils import timezone
        data=super().clean()
        if data.get('surgery_from') and data.get('surgery_to') and data['surgery_from']>data['surgery_to']:raise forms.ValidationError('Surgery start date must precede end date.')
        if data.get('as_of') and data['as_of']>timezone.localdate():self.add_error('as_of','Cutoff cannot be in the future.')
        return data
