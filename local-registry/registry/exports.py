"""Allowlisted typed exports. Never export identifier records or clinical narratives."""
import csv
import io
import json
import zipfile
from .models import Treatment
from .analysis import SCORES

def safe(value):
    if value is None:return ''
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@','\t','\r')):return "'"+value
    return value

def research_bundle(result):
    report,patients,procedures,visits,events=result
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        def table(name,keys,rows):
            b=io.StringIO(newline='');w=csv.writer(b);w.writerow(keys)
            for row in rows:w.writerow([safe(x) for x in row])
            archive.writestr(name,b.getvalue())
        table('patients.csv',['study_id','sex','age_at_enrolment','enrolled_on','synthetic'],patients.values_list('study_id','sex','age','enrolled_on','synthetic'))
        table('procedures.csv',['procedure_id','study_id','date','approach','endoscopic_type','levels','instrumented','duration_hours','blood_loss_ml','anaesthesia','asa','hospital_days'],procedures.values_list('pk','patient__study_id','date','approach','endoscopic_type','levels','instrumented','duration_hours','blood_loss_ml','anaesthesia','asa','hospital_days'))
        fields=['patient__study_id','procedure_id','date','timepoint','status']+SCORES+['sf_version','sf_scoring_method']
        table('visits.csv',['study_id','procedure_id','assessment_date','timepoint','status']+SCORES+['sf_version','sf_scoring_method'],visits.values_list(*fields))
        table('events.csv',['study_id','procedure_id','date','kind'],events.values_list('patient__study_id','procedure_id','date','kind'))
        treatments=Treatment.objects.filter(patient__in=patients,start_date__lte=report['cutoff']).select_related('patient')
        from datetime import date
        cutoff=date.fromisoformat(report['cutoff'])
        table('treatments.csv',['study_id','treatment_record_id','start_date','end_date_at_cutoff','ongoing_at_cutoff','duration_weeks','steroid_injection'],([t.patient.study_id,t.pk,t.start_date,t.end_date if t.end_date and t.end_date<=cutoff else None,not t.end_date or t.end_date>cutoff,t.weeks(cutoff),t.steroid_injection] for t in treatments))
        table('summary.csv',['timepoint','score','unit','n','mean','sd','median','min','max','available_visits','missing','pooling_suppressed'],([r.get(k) for k in ['timepoint','score','unit','n','mean','sd','median','min','max','available_visits','missing','pooling_suppressed']] for r in report['summary']))
        table('paired_changes.csv',['timepoint','score','direction','n','mean','sd','median','min','max'],([r.get(k) for k in ['timepoint','score','direction','n','mean','sd','median','min','max']] for r in report['paired']))
        archive.writestr('analysis.json',json.dumps(report,indent=2))
        archive.writestr('README.txt','Synthetic research export. Study IDs are pseudonyms, not proof of anonymity. Dates and rare combinations may identify individuals in real datasets. Restricted identity records and clinical narratives are excluded. SF-36 version/method metadata, level labels and study IDs are entered by users: keep them free of direct identifiers. See analysis.json for filters, cutoff, version, missing counts and methods. Treatment durations are patient-cohort records, not limited to the selected operations. This dataset is for local review, not an automatic safe-to-share or publication-ready release.')
    return output.getvalue()
