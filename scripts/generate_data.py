"""Generate fictional spine patients; assumptions are illustrative, not evidence."""
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def generate(seed=2026, n=240):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        diagnosis = rng.choice(['Lumbar disc herniation', 'Lumbar stenosis', 'Degenerative spondylolisthesis'])
        procedure = rng.choice(['Full endoscopic', 'UBE', 'Open decompression', 'Decompression + fusion'])
        vas = rng.randint(5, 10)
        odi = rng.randrange(30, 83, 2)
        visits = {}
        for time, loss in [('3m', .09), ('6m', .17)]:
            attended = rng.random() >= loss
            visits['vas_' + time] = max(0, min(10, round(vas - rng.uniform(2, 6) - (time == '6m'), 1))) if attended else None
            visits['odi_' + time] = max(0, min(100, round(odi - rng.uniform(10, 38) - 5 * (time == '6m'), 1))) if attended else None
        rows.append(dict(patient_id=f'SYN-{i+1:04}', age=rng.randint(22, 82), sex=rng.choice(['Female','Male']), diagnosis=diagnosis, procedure=procedure, levels=rng.choice([1,1,2,2,3]), surgery_date=f'{rng.choice([2024,2025])}-{rng.randint(1,12):02}-{rng.randint(1,28):02}', hospital_days=rng.randint(1,4) if procedure in ['Full endoscopic','UBE'] else rng.randint(2,8), complication=rng.choices(['None','Dural tear','Superficial infection','Transient neurological deficit'],[88,5,4,3])[0], vas_baseline=vas, odi_baseline=odi, **visits))
    return rows

if __name__ == '__main__':
    rows = generate()
    (ROOT / 'dist').mkdir(exist_ok=True)
    (ROOT / 'dist/patients.json').write_text(json.dumps(rows, indent=2) + '\n')
    with (ROOT / 'dist/patients.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Generated {len(rows)} synthetic patients (seed 2026).')
