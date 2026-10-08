# Deployment and collaboration phases

## 1. Current: laptop synthetic prototype

Continuous entry, local SQLite database, individual accounts, restricted identity records, repeat operations/visits, descriptive analysis, allowlisted exports and audit actions. Validate the workflow with Zoe International Hospitals using synthetic records. Review the uploaded-form mapping. Confirm required instruments, definitions, follow-up windows and study-specific variables with the clinical/research team.

Acceptance: enter a synthetic patient; baseline; treatment; surgery; follow-up; complication; second surgery and its baseline. Confirm filters and paired denominators, edit a visit without duplication, review scoring metadata, export and open all report formats. Practise backup and restore. Validate role boundaries with separate accounts.

## 2. Hospital pilot

Replace the development server with a maintained production web/application service and PostgreSQL, migrate data, validate disk/backup encryption and access rights, add HTTPS and private networking, review login/session security, formalise account administration and patient consent/legal basis, audit retention, incident response, data correction and deletion rules. Add optimistic concurrency controls, import validation, structured diagnostic/operation/treatment coding, instrument-specific validation, immutable dataset versions and scheduled backup/restore verification. Add separate test/production environments and automated deployment checks.

Decide how complications are actively ascertained, eligible follow-up windows are calculated and multiple operations per patient are handled. Agree a statistical analysis plan and validate any inferential analysis before real research use. The current export service deliberately does not export clinical narratives. Do not relabel fabricated data as real or remove the synthetic banner to begin a live pilot.

## 3. Multicentre collaboration

Each hospital hosts a separate local registry/database and uses a shared versioned data dictionary. Add site codes, common coding systems, governance agreements, approved aggregation rules, small-cell suppression and disclosure review. First exchange approved cohort summaries manually. Then add an authenticated coordinator, auditable query approval and local execution to return aggregate results. Federation does not automatically guarantee privacy; a separate disclosure threat model is necessary. Individual-level records remain local.

## 4. Research analysis service

Add study-specific cohort definitions, checked eligibility windows, missingness reports, immutable analysis snapshots, manuscript tables/figures, and validated models that address clustering and confounding. Exports should carry the study specification, software version, provenance, methods and limitations. Statistical review remains part of publication preparation.
