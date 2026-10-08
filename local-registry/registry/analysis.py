"""Descriptive summaries with explicit units and denominators; no inference."""
from collections import Counter
from statistics import mean, stdev, median
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from .models import Patient, Procedure, Assessment, Event, Treatment
TIMEPOINTS=['baseline','postop','3m','6m','9m','1y','2y']
SCORES=['vas_main','vas_worst_radicular','vas_other_radicular','odi','ndi','walking_m','sf_physical_functioning','sf_role_physical','sf_bodily_pain','sf_general_health','sf_vitality','sf_social_functioning','sf_role_emotional','sf_mental_health','sf_pcs','sf_mcs']
UNITS={'vas_main':'0–10','vas_worst_radicular':'0–10','vas_other_radicular':'0–10','odi':'0–100','ndi':'0–100','walking_m':'m'}

def describe(values):
    vals=[v for v in values if v is not None]
    return {'n':len(vals),'mean':round(mean(vals),3) if vals else None,'sd':round(stdev(vals),3) if len(vals)>1 else None,'median':round(median(vals),3) if vals else None,'min':min(vals) if vals else None,'max':max(vals) if vals else None}

def cohort(cleaned):
    cutoff=cleaned.get('as_of') or timezone.localdate()
    patients=Patient.objects.filter(enrolled_on__lte=cutoff)
    if cleaned.get('q'):patients=patients.filter(Q(study_id__icontains=cleaned['q'])|Q(diagnosis__icontains=cleaned['q']))
    if cleaned.get('sex'):patients=patients.filter(sex=cleaned['sex'])
    procedures=Procedure.objects.filter(patient__in=patients,date__lte=cutoff)
    if cleaned.get('approach'):procedures=procedures.filter(approach=cleaned['approach'])
    if cleaned.get('surgery_from'):procedures=procedures.filter(date__gte=cleaned['surgery_from'])
    if cleaned.get('surgery_to'):procedures=procedures.filter(date__lte=cleaned['surgery_to'])
    if any(cleaned.get(k) for k in ['approach','surgery_from','surgery_to']):patients=patients.filter(procedures__in=procedures).distinct()
    return patients, procedures, cutoff

def make_report(cleaned):
    patients,procedures,cutoff=cohort(cleaned)
    # Link scores to operations in the selected cohort, keep unlinked baseline for non-operative patients.
    linked=Q(procedure__in=procedures)
    if not any(cleaned.get(k) for k in ['approach','surgery_from','surgery_to']):linked|=Q(procedure__isnull=True)
    visits=Assessment.objects.filter(patient__in=patients,date__lte=cutoff).filter(linked)
    events=Event.objects.filter(patient__in=patients,date__lte=cutoff).filter(linked)
    complete=list(visits.filter(status='Completed').select_related('procedure'))
    versions={v.sf_version for v in complete if any(getattr(v,k) is not None for k in SCORES if k.startswith("sf_"))}
    component_methods={(v.sf_version,v.sf_scoring_method) for v in complete if v.sf_pcs is not None or v.sf_mcs is not None}
    suppressed=[k for k in SCORES if k.startswith("sf_") and (len(versions)>1 or k in ["sf_pcs","sf_mcs"] and len(component_methods)>1)]
    summaries=[]
    for tp in TIMEPOINTS:
        subset=[v for v in complete if v.timepoint==tp]
        for score in SCORES:
            stats=describe([getattr(v,score) for v in subset])
            if score in suppressed:stats.update({k:None for k in ['mean','sd','median','min','max']})
            summaries.append(dict(pooling_suppressed=score in suppressed,timepoint=tp,score=score,unit=UNITS.get(score,'component score' if score in ['sf_pcs','sf_mcs'] else '0–100'),available_visits=len(subset),missing=len(subset)-stats['n'],**stats))
    # No visit averaging: one baseline and one follow-up per procedure are enforced by constraints.
    baseline={v.procedure_id:v for v in complete if v.timepoint=='baseline' and v.procedure_id}
    paired=[]
    for tp in TIMEPOINTS[1:]:
        for score in SCORES:
            if score in suppressed:continue
            changes=[]
            for v in complete:
                b=baseline.get(v.procedure_id)
                if v.timepoint==tp and b:
                    a,z=getattr(b,score),getattr(v,score)
                    if a is not None and z is not None:
                        if score=='walking_m' and (not b.walking_definition or b.walking_definition!=v.walking_definition):continue
                        changes.append(a-z)
            if changes:paired.append(dict(timepoint=tp,score=score,direction='baseline minus follow-up',**describe(changes)))
    complications=events.filter(kind__endswith='complication')
    report={
        'hospital':settings.HOSPITAL_NAME,
        'generated_at':timezone.now().isoformat(),'cutoff':cutoff.isoformat(),'filters':{k:str(v) for k,v in cleaned.items() if v},
        'patients':patients.count(),'procedures':procedures.count(),'age':describe(list(patients.values_list('age',flat=True))),
        'sex':dict(Counter(patients.values_list('sex',flat=True))),'approaches':dict(Counter(procedures.values_list('approach',flat=True))),
        'hospital_stay_days':describe(list(procedures.values_list('hospital_days',flat=True))),
        'duration_hours':describe(list(procedures.values_list('duration_hours',flat=True))),
        'blood_loss_ml':describe(list(procedures.values_list('blood_loss_ml',flat=True))),
        'complication_events':complications.count(),'patients_with_complication':complications.values('patient_id').distinct().count(),
        'reoperation_events':events.filter(kind='Reoperation').count(),
        'visit_status':dict(Counter(visits.values_list('status',flat=True))),
        'sf36_methods':list(visits.exclude(sf_scoring_method='').values_list('sf_version','sf_scoring_method').distinct()),
        'summary':summaries,'paired':paired,
        'analysis_version':'0.1.0',
        'pooling_suppressed':suppressed,
        'treatment_duration_weeks':describe([t.weeks(cutoff) for t in Treatment.objects.filter(patient__in=patients,start_date__lte=cutoff)]),
        'methods':'Descriptive analysis of available records at the specified cutoff. SD is sample SD (undefined at n<2). No imputation, inferential tests, risk adjustment or causal comparisons. Paired changes use baseline minus follow-up for the same procedure. Summaries are visit/procedure-level and can include multiple operations per patient. Complication patient denominator is the number of distinct patients in the filtered cohort; unrecorded events cannot be assumed absent. Follow-up completeness among all eligible operations is not yet estimated. SF-36 component scores are entered externally and are not computed by this software. SF-36 pooling is suppressed when instrument versions differ, and component pooling is suppressed when scoring methods differ; counts remain visible. Walking pairs require an identical non-empty measurement protocol. Labelled timepoints use recorded visit categories, not validated time windows. Historical cutoffs select dates from current records and do not restore earlier database versions. Unscheduled visits remain in raw exports but are not pooled into scheduled summaries.'
    }
    return report,patients,procedures,visits,events
