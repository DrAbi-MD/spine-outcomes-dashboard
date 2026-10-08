# Uploaded data-form mapping

The uploaded 115-column form is reorganised into linked records for Zoe International Hospitals. No patient workbook data are imported or committed. Text labels replace spreadsheet numeric choices. Baseline, postoperative and scheduled follow-up assessments are separate rows rather than repeating columns.

| Source column | Original heading | Prototype destination / decision |
| --- | --- | --- |
| A | S/N | Database record key; spreadsheet row number is not a clinical variable. |
| B | RN (Research Number) | Patient.study_id — unique synthetic research ID. |
| C | HOSPITAL ID | Identity.hospital_number — separately restricted. |
| D | INITIALS(NAME) | Identity.initials — separately restricted. |
| E | SEX(BIOLOGICAL; 1, Male  /  2, Female  /  3, Other) | Patient.sex — labels replace numeric codes; Unknown added. |
| F | AGE(Years) | Patient.age — years at enrolment. |
| G | MARITAL STATUS (1, Single  / 2, Married  / 3, Divrced/Separated /  4, Widowed) | Patient.details.marital_status. |
| H | RESIDENCE (1, Urban /  2, Rural) | Patient.details.residence. |
| I | ADDRESS (LGA, State, Country) | Identity.address; optional Patient.details.state/country provide research geography separately. |
| J | OCCUPATION | Patient.details.occupation. |
| K | EMPLOYMENT (1, Employed /  2, Unemployed /  3, Student /  4, Retired) | Patient.details.employment. |
| L | EDUCATION (1, None /  2, Primary /  3, Secondary /  4, Tertiary) | Patient.details.education. |
| M | INSURANCE (1, Yes /  2, No) | Patient.details.insurance. |
| N | REFERAL (1, Self /  2, Primary facility /  3, Secondary /  4, Tertiary /  5, Others | Patient.details.referral. |
| O | SMOKING (1, Never /  2, Former /  3, Current) | Patient.details.smoking. |
| P | PACK YRS | Patient.details.pack_years. |
| Q | ALCHOHOL (1, Never /  2, Former /  3, Current | Patient.details.alcohol. |
| R | UNITS PER WEEK | Patient.details.alcohol_units_week — record unit definition in comments. |
| S | DRUG USAGE (RECREATIONAL) | Patient.details.recreational_drugs. |
| T | PHYSICAL ACTIVITY (1, Low /  2, Moderate /  3, High) | Patient.details.physical_activity. |
| U | EXCERCISE REGULAR (1, Yes /  2, No) | Patient.details.exercise. |
| V | HEAVY LIFTING (1, Yes /  2, No) | Patient.details.heavy_lifting. |
| W | PROLONGED SITTING/DRIVING (1, Yes /  2, No) | Patient.details.prolonged_sitting. |
| X | WEIGHT(Kg) | Patient.details.weight_kg. |
| Y | HEIGHT(Cm) | Patient.details.height_cm. |
| Z | BODY MASS INDEX(BMI) | Patient.details.bmi — derived from height/weight, not independently entered. |
| AA | COMORBIDITIES(1, Yes /  2, No) | Patient.details.comorbidities_present — Yes/No/Unknown. |
| AB | LIST COMOBIDITIES (For each: Diagnosis, Duration, Current Tx) | Patient.details.comorbidities — diagnosis, duration and treatment narrative. |
| AC | SYMPTOMS/DURATION(List all) | Patient.details.symptoms. |
| AD | PRIMARY SYMPTOM | Patient.details.primary_symptom. |
| AE | DURATION OF PRI SYMPTOM (1, Acute <3wks /  2, Subacute 3-6wks /  3, Chronic >6wks) | Patient.details.symptom_duration — source categories retained. |
| AF | VAS MAIN AT ADMISSION (Primary Complaint ie Back or Neck pain) | Assessment.vas_main at baseline; pain_site identifies Back/Neck/Other. |
| AG | VAS RADICULAR AT ADMISSION (WORST Radicular LIMB) | Assessment.vas_worst_radicular at baseline; worst_limb recorded at each visit. |
| AH | VAS RADICULAR AT ADMISSION (LEAST Radicular LIMB) | Assessment.vas_other_radicular at baseline. |
| AI | ODI/NDI AT ADMISSION | Assessment.odi and Assessment.ndi, separate normalised 0–100 scores, baseline. |
| AJ | SF 36 AT ADMISSION | Assessment SF-36 eight domains plus PCS/MCS, baseline; version/method required as applicable. |
| AK | WALKING DISTANCE BEFORE SUGRERY | Assessment.walking_m at baseline; walking_definition records protocol. |
| AL | ANY PREVIOUS SPINAL SURGERIES? | Patient.details.previous_surgery_present — Yes/No/Unknown. |
| AM | IF YES, SPECIFY PREVIOUS SPINE SURGERY | Patient.details.previous_surgery — procedure/date narrative. |
| AN | EXAMINATION KEY FINDINGS | Patient.details.examination. |
| AO | NEUROLOGIC DEFICIENCY (1, Yes /  2, No) | Patient.details.neurological_deficit. |
| AP | SPECIFY NEURO. DEFICIET | Patient.details.deficit_description. |
| AQ | XRAY FINDINGS | Patient.details.xray. |
| AR | MRI  FINDINGS | Patient.details.mri. |
| AS | CT SCAN  FINDINGS | Patient.details.ct. |
| AT | LAB RESUTS | Patient.details.labs — include units. |
| AU | SPINOPELVIC PARAMETERS | Assessment baseline spinopelvic_notes plus pi/pt/ss/ll/cobb in degrees and sva in mm. |
| AV | OTHER INVESTIGATIONS | Patient.details.other_investigations. |
| AW | DIAGNOSIS | Patient.diagnosis. |
| AX | NON OPERATIVE TX | Treatment.treatment — repeatable treatment records. |
| AY | TX DURATION | Treatment.start_date/end_date/ongoing; calculated weeks through cutoff. |
| AZ | TX OUTCOME | Treatment.outcome. |
| BA | STEROID INJECTION | Treatment.steroid_injection. |
| BB | INJECTION FREQUENCY | Treatment.injection_frequency. |
| BC | INJECTION OUTCOME | Treatment.injection_outcome. |
| BD | INDICATION FOR SURGERY | Procedure.details.indication. |
| BE | SURGICAL TX | Procedure.operation. |
| BF | DATE OF SURGERY | Procedure.date. |
| BG | ANAESTHESIA | Procedure.anaesthesia. |
| BH | ASA GRADE | Procedure.asa — 1–6. |
| BI | FRAILTY INDEX | Procedure.details.frailty_index — value and instrument recorded together. |
| BJ | CHARLSON COMOBIDITY INDEX | Procedure.details.charlson_index. |
| BK | SPECIAL ANAESTHETIC CONSIDERATIONS AND DIFFICULTIES | Procedure.details.anaesthetic_considerations. |
| BL | ANAESTHETIC COMPLICATIONS | Procedure.details.anaesthetic_complications plus Event kind Anaesthetic complication. |
| BM | SURGERY TYPE (1, Endoscopic /  2, Open) | Procedure.approach — Endoscopic/Open. |
| BN | TYPE OF ENDOSCOPIC PROCEDURE PERFORMED (1, Uniportal /  2, Biportal) | Procedure.endoscopic_type — Uniportal/Biportal when endoscopic. |
| BO | SINGLE LEVEL (SPECIFY) | Procedure.levels — comma-separated level labels. |
| BP | MULTIPLE LEVELS OPERATED (1, 2 levels /  2, 3 levels /  3, >3levels), SPECIFY | Procedure.levels — multiple labels in the same field; count can be derived. |
| BQ | INTRUMENTED | Procedure.instrumented. |
| BR | DURATION OF SURGERY | Procedure.duration_hours. |
| BS | NEUROMONITORING (1,Yes /  2, No) | Procedure.details.neuromonitoring. |
| BT | INTRA-OPERATIVE COMPLICATIONS? | Procedure.details.intraoperative_complications — Yes/No/Unknown. |
| BU | YES,(SPECIFY) | Event with kind Intraoperative complication; description/severity/management. |
| BV | ESTIMATED BLOOD LOSS | Procedure.blood_loss_ml. |
| BW | TRANSFUSION (1,Yes /  2, No) | Procedure.details.transfusion. |
| BX | LENGTH OF HOSPITAL STAY(IN DAYS) | Procedure.hospital_days; derived if admission/discharge dates provided. |
| BY | POST-OPERATIVE PAIN SEVERITY (VAS SCALE) | Assessment.vas_main/vas_worst_radicular/vas_other_radicular, postop. |
| BZ | IMPROVEMENT IN WALKING DISTANCE | Assessment.walking_m and details.walking_change, postop. |
| CA | RETURN TO NORMAL  ACTIVITIES | Assessment.details.return_activities. |
| CB | POST-OPERATIVE COMPLICATIONS? | Assessment.details.postoperative_complications — Yes/No/Unknown. |
| CC | OTHERS(SPECIFY) | Event with kind Postoperative complication; description/severity/management. |
| CD | LEVEL OF SATISFACTION WITH SURGERY | Assessment.details.surgery_satisfaction. |
| CE | IMPROVEMENT IN SYMPTOMS | Assessment.details.symptom_improvement. |
| CF | WOULD YOU RECOMMEND THIS PROCEDURE TO OTHERS? | Assessment.details.recommendation. |
| CG | OVERALL SATISFACTION (1, Very Satisfied /  2, Satisfied /  3, Neutral /  4, Dissatisfied /  5, Very Dissatisfied) | Assessment.details.satisfaction. |
| CH | PATIENT PERCIEVED OUTCOME(1, EXCELLENT /  2, GOOD /  3, FAIR /  4, POOR)Macnab criteria | Assessment.details.macnab. |
| CI | GLOBAL IMPRESSION OF CHANGE (1, Much worse /  2, Worse /  3, No chnage /  4, Improved /  5, Much improved) | Assessment.details.global_change. |
| CJ | ODI /NDI AT 3 MONTHS | Assessment.odi/ndi at 3m. |
| CK | ODI/NDI AT 6 MONTHS | Assessment.odi/ndi at 6m. |
| CL | ODI/NDI  AT 9 MONTHS | Assessment.odi/ndi at 9m. |
| CM | ODI/NDI, SF36 AT 1 YEAR | Assessment.odi/ndi and SF-36 at 1y; duplicate one-year SF-36 source heading is merged. |
| CN | ODI/NDI AT 2 YEAR | Assessment.odi/ndi at 2y. |
| CO | SF 36 AT 3MONTHS | Assessment SF-36 eight domains plus PCS/MCS at 3m. |
| CP | SF 36 AT 6MONTHS | Assessment SF-36 eight domains plus PCS/MCS at 6m. |
| CQ | SF 36 AT 1YEAR | Assessment SF-36 at 1y; same record as CM, not duplicated. |
| CR | SF 36 AT 2YEAR | Assessment SF-36 eight domains plus PCS/MCS at 2y. |
| CS | VAS - MAIN (BACK/NECK) AT  3 MONTHS | Assessment.vas_main at 3m. |
| CT | VAS - WORST RADICULAR AT 3MONTHS | Assessment.vas_worst_radicular at 3m. |
| CU | VAS - RADICULAR (OTHER LEG/ARM) AT 3 MONTHS | Assessment.vas_other_radicular at 3m. |
| CV | VAS -MAIN (BACK/NECK) AT  6 MONTHS | Assessment.vas_main at 6m. |
| CW | VAS - WORST RADICULAR LIMB AT 6 MONTHS | Assessment.vas_worst_radicular at 6m. |
| CX | VAS - OTHER RADICULAR LIMB AT 6 MONTHS | Assessment.vas_other_radicular at 6m. |
| CY | VAS -MAIN (BACK/NECK) AT 1YEAR | Assessment.vas_main at 1y. |
| CZ | VAS - WORST RADICULAR LIMB AT 1 YR | Assessment.vas_worst_radicular at 1y. |
| DA | VAS - OTHER RADICULAR LEG AT 1 YR | Assessment.vas_other_radicular at 1y. |
| DB | VAS- MAIN (BACK/NECK)YEARS AT 2 YEAR | Assessment.vas_main at 2y. |
| DC | VAS - WORST RADICULAR LEG/LIMB AT 2 YEAR | Assessment.vas_worst_radicular at 2y. |
| DD | VAS - OTHER RADICULAR LIMB/LEG AT 2 YEAR | Assessment.vas_other_radicular at 2y. |
| DE | SPINOPELVIC PARAMETER AT 3MONTHS | Assessment spinopelvic fields at 3m. |
| DF | SPINOPELVIC PARAMETER AT 6MONTHS | Assessment spinopelvic fields at 6m. |
| DG | SPINOPELVIC PARAMETER AT 1YR | Assessment spinopelvic fields at 1y. |
| DH | SPINOPELVIC PARAMETER AT 2YR | Assessment spinopelvic fields at 2y. |
| DI | RECURRENCE OF SYMPTOMS? | Assessment.details.symptom_recurrence — Yes/No/Unknown. |
| DJ | Yes(Specify) | Event with kind Symptom recurrence; description/date. |
| DK | ADDITIONAL OBSERVATION OR COMMENTS? | Patient.details.comments and Assessment.details.comments, as appropriate. |

## Additional rules

Patient enrolment date is required. Procedures, treatments, events and assessments can repeat. Scheduled visits have one row per operation/timepoint; unscheduled assessments may repeat. SF-36 version and scoring method, walking protocol and visit status are explicit. Blank outcome values mean unrecorded, not zero. Yes/No/Unknown complication declarations are retained in supplemental fields; current complication summaries count Event records and do not yet reconcile these declarations automatically. Add individual Event records when Yes is selected. Severity and free-text fields are excluded from research exports pending a structured study dictionary. The form is implemented through manual entry; automated spreadsheet import is not provided.
