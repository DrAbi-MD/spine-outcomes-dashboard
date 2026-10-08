# Prototype validation record

Validated on 8 October 2026 with Python 3.11 and Django 5.2.18 in a Linux test environment. Windows instructions use Python 3.12/3.13; they have not been run on the owner's Windows computer.

- Django system checks: passed.
- Django tests: 16 passed, with isolated temporary test database.
- JavaScript syntax: `node --check registry/static/registry/charts.js` passed.
- Initial schema migrations and role setup: passed.
- Synthetic seed: 60 patients, 60 operations, 240 visit records, 60 treatments, 6 events.
- SQLite backup: `PRAGMA integrity_check` returned `ok`; patient, procedure, assessment, treatment, event and role table counts matched the source database.
- Source mapping: all 115 uploaded-form columns accounted for; supplemental narrative and declared Yes/No/Unknown fields retained, with export/analysis limitations documented.
- Authenticated server-rendered pages and all five research export formats exercised through Django's test client.

The tests cover role restrictions, CSRF-protected entry, zero/missing distinction, paired denominators including repeat operations, filters, foreign procedure rejection, duplicate visits, date and finite-score validation, SF-36 metadata/mixed-method suppression, event validation, identifier access auditing, export allowlisting/formula escaping, persistent login throttling and idempotent seeding.

This is automated functional validation, not a completed human usability review, clinical validation, penetration test, formal compliance review or real hospital deployment. Browser chart interactions and figure downloads require a first-run visual review on the user's computer. Acceptance steps are in ROADMAP.md.
