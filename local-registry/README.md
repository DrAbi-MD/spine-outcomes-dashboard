# Zoe International Hospitals — local spine registry

A Django prototype that turns the spine outcomes dashboard into a local workspace for continuous patient entry, repeated operations, follow-up assessments, descriptive analysis and research exports. **Use synthetic data only at this stage.** The source code can be public on GitHub; the database stays on your computer.

## Start on Windows

1. Install Python **3.12 or 3.13** from python.org, including the Windows Python launcher.
2. Download this repository branch as a ZIP and **extract it** into a local folder outside OneDrive/Dropbox. Open `local-registry` inside the extracted repository. Do not run inside the ZIP.
3. In that folder, open PowerShell (right-click an empty area → Open in Terminal).
4. Run the commands below. Paste one line at a time. No PowerShell activation or execution-policy change is required.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py setup_roles
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Choose your own username and strong password when prompted. Password typing is hidden. There is **no shared default password**. Open **http://127.0.0.1:8000/** in your browser and sign in. Leave the terminal running. Press Ctrl+C to stop. On later days you only need the last command. An optional `start-windows.cmd` does this for you by double-clicking it after setup. You do not need a router or an internet connection to use the installed prototype. Installation downloads Python packages.

If the port is busy, use `127.0.0.1:8001` and open that address instead. If `py` is not found, reopen your terminal after installing Python or substitute `python` for `py -3`.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py setup_roles
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

## Your first walkthrough

- Overview: filter by sex, procedure approach, operation dates or report cutoff; switch between VAS, ODI and NDI charts; export the current chart as SVG.
- Patient registry → Register patient: create a synthetic research ID such as `PILOT-001`. Required fields are ID, sex, age and enrolment date; other fields can remain unrecorded.
- Open the patient's record → Add treatment: enter start/end dates, or mark ongoing. Duration is calculated in **weeks**.
- Add procedure: choose open or endoscopic, uniportal/biportal if endoscopic, levels and anaesthesia. Duration is **hours**, blood loss **mL**. Stay is the difference between admission/discharge calendar dates when both are entered; same-day stay is zero days.
- Add assessment: link it to the correct operation. Enter baseline and follow-up dates, VAS, ODI or normalised NDI, walking distance in **metres**, SF-36 domains and component scores as applicable. Link both baseline and follow-up to the same operation for paired changes.
- Add event: complications, recurrence or reoperation. A new operation can also be entered as a separate procedure, with its own assessments.
- Analysis & reports: export a report, summary tables, visit-level CSV, the complete allowlisted research ZIP, or analysis JSON.

The seed command adds **60 synthetic patients, 60 procedures, 240 visit records, 60 treatments and 6 events**. It does not overwrite your entries. Running it again does nothing if any `DEMO-` records already exist. The demonstration data are fabricated, not clinical expectations or validated outcomes.

## Accounts and confidentiality boundaries

Run `setup_roles` after migration; rerunning it resets the standard group's permission sets. Create individual accounts rather than sharing the owner account:

```powershell
.\.venv\Scripts\python.exe manage.py create_registry_user research_entry --role "Data Entry"
.\.venv\Scripts\python.exe manage.py create_registry_user researcher --role "Analyst"
.\.venv\Scripts\python.exe manage.py create_registry_user identifier_custodian --role "Identifier Manager"
.\.venv\Scripts\python.exe manage.py create_registry_user reviewer --role "Auditor"
```

| Role | Capabilities |
| --- | --- |
| Data Entry | Create/edit clinical records and view dashboard; no identifier access or research export by default |
| Analyst | View dashboard and patient summaries; export research datasets; no editing or identifier access |
| Identifier Manager | View/edit hospital ID, initials and address, which are separate from research variables |
| Auditor | View dashboard and recent audit entries; no identifier access or exports |
| Owner / superuser | All prototype permissions; keep this account for administration |

Roles can be combined by repeating `--role`. User creation is through the local command line; account editing, password resets and deactivation do not yet have a web administration screen. The owner can reset a password with `manage.py changepassword username`.

The application provides login, CSRF protection, server-side role checks, persistent failed-login throttling, a 30-minute sliding session expiry, no-store response headers and an application audit trail recording actions and changed field names rather than values. Hospital number, initials and address are in a separately permissioned record. Direct identifiers and clinical narrative fields are excluded from research exports. Research IDs, dates, level labels and scoring metadata can still disclose information if entered carelessly; exported data are **pseudonymised, not guaranteed anonymous**. Only Data Entry/owner accounts see detailed clinical notes. Do not place real identifiers in research IDs or other free-text fields.

**Local storage is not automatic encryption.** The SQLite database, restricted identifiers and user password hashes are in `private_data/registry.sqlite3`; the application secret is `private_data/secret.key`. These files are excluded by `.gitignore`, and the upload contains no database or credentials. Anyone with access to the computer's files may bypass application permissions. This prototype has no database encryption, tamper-proof audit system, field-level record locking, automatic backups or formal compliance certification. Windows folder permissions and disk encryption need separate configuration before any real-data pilot. Avoid cloud-synced folders. Never upload a database, backup or research export to the public repository.

## Reports and analysis

- Filters apply consistently to charts, tables and exports. Operation filters exclude unlinked assessments and events; without those filters, unlinked baseline records are included. Patients without operations remain visible in the all-patient cohort.
- Mean, sample SD, median, range, available-score count and missing count are calculated from recorded values. Zero is a value; blank is missing. SD is undefined for fewer than two observations.
- Paired changes are **baseline minus follow-up** for the same procedure. This is a score reduction, not always clinical improvement: SF-36 and walking generally have a different favourable direction to VAS/ODI/NDI. Walking pairs require identical non-empty protocol labels.
- Scheduled visits are unique per patient/operation/timepoint. Unscheduled visits are repeatable and exported, but do not enter scheduled summaries. Labels such as 3 months are user-selected; elapsed-time windows are not yet enforced.
- SF-36 accepts eight domain scores (0–100) and externally scored PCS/MCS, with instrument version and component scoring method/reference norms. It does **not** score questionnaire items, calculate components, validate licensing or average domains into PCS/MCS. Pooling is suppressed across mixed instrument versions; component pooling is also suppressed across mixed methods. No instrument-specific clinical interpretation is automated.
- A historical cutoff uses dates from the current database. It is not an immutable snapshot of what was known on that day. Ongoing treatment duration is measured through cutoff; ended treatment duration is capped at cutoff. Treatments are selected by patient cohort, not a specific operation.
- Recorded complication counts do not establish that all other patients had no complication. Event ascertainment and eligible follow-up denominators need further design. These are descriptive summaries, without inferential tests, propensity adjustment, causal claims or patient-level clustered analysis.
- Reports include cohort filters, cutoff, generation timestamp, software analysis version and methods. Save the exported ZIP to retain a reviewable dataset/summary at that point in time.

| Export | Contents |
| --- | --- |
| Report HTML | Editable tables and methods; open in a browser and Print → Save as PDF, or open with Word |
| Summary CSV | Scheduled outcome statistics, denominators, missing counts and pooling flags |
| Visits CSV | One row per selected visit, linked typed procedure variables and scores |
| Research ZIP | Separate patients, procedures, visits, events, treatments, summaries and paired-change CSVs; analysis JSON and interpretation notes |
| Analysis JSON | Cohort summary, metadata, all statistics and methods |
| Chart SVG | Current recovery plot in a scalable format; screenshot-like figure, not a complete publication figure with uncertainty estimates |

CSV text starting with common spreadsheet formula characters is escaped. Missing clinical narratives, diagnoses, treatment names and event descriptions are intentional: exports contain allowlisted structured research variables. Additional structured study variables can be added after agreeing a study-specific dictionary. These outputs support research preparation; statistical review and manuscript-specific tables remain necessary for publication.

## Back up and restore

Create a folder outside the repository, preferably on an encrypted external drive. Stop entry while practising a restore. Example backup command (change the path):

```powershell
.\.venv\Scripts\python.exe manage.py backup_registry "E:\ZoeBackups\registry-2026-10-08.sqlite3"
```

The command creates a consistent SQLite backup, refuses to overwrite a file, and refuses destinations inside the source project. **The backup contains confidential identifiers and password hashes.** It is not a public research export. Securely back up `private_data/secret.key` separately. For restore: stop the server, preserve the current database, copy the backup to `private_data/registry.sqlite3`, restore the secret if needed, run `manage.py migrate`, then start the server and check record counts and account access. Do not copy a live SQLite file manually; use the backup command. Test restoration before relying on a backup policy.

`ZOE_DATA_DIR` can point to a private data directory outside the source tree. Set it consistently for all commands. Optional `ZOE_HOSPITAL_NAME` changes the hospital display name. Do not point a second hospital at another hospital's database.

## Verification and source layout

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test registry
```

Tests cover authenticated access, denied identifier access, editing/export permissions, CSRF-protected entry, audit contents, all main pages/export types, login throttling, duplicate/foreign procedure rejection, score/date validation, zero/missing handling, paired denominators, cohort isolation, mixed SF-36 scoring and synthetic seed idempotency. See [the source-form mapping](docs/FIELD_MAPPING.md) and [the next-phase plan](docs/ROADMAP.md).

## Hosting boundary

GitHub stores the code and serves the original public static demonstration. **GitHub Pages cannot run this Django backend.** This registry starts on your computer at a loopback address and stores records there. Do not change the bind address to `0.0.0.0` or expose Django's development server to the internet. It is a single-computer synthetic prototype; simultaneous hospital-network entry and global collaboration are not yet implemented.

A real hospital deployment needs a production server, PostgreSQL, HTTPS, centrally managed accounts, operational security, approved data governance, tested backups and statistical validation. Internet access can later use an authenticated hospital endpoint or VPN while the database remains hospital-hosted. Federated collaboration should exchange approved aggregate outputs rather than synchronise patient-level databases. These are future phases, not features claimed by this prototype.
