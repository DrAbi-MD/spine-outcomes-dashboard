# Spine Outcomes — synthetic clinical dashboard

An interactive portfolio by **Israel Abi** demonstrating reproducible data generation, cohort analysis, longitudinal outcome summaries, and a responsive clinical dashboard.

**All 240 patients are fictional. This project is a software demonstration, not clinical evidence or a medical decision tool.**

## Live demo

[Open the public dashboard](https://drabi-md.github.io/spine-outcomes-dashboard/)

The demo URL will work after GitHub Pages is enabled. In repository Settings → Pages, choose Deploy from a branch, select `main` and `/docs`, then Save.

## Run locally

Requires Python 3.10+; Node.js 18+ is needed only for tests. No third-party packages or external chart services are required.

```bash
python scripts/generate_data.py
python -m http.server 8000 --directory dist
```

Open http://localhost:8000. Opening the HTML file directly will not load JSON in browsers that restrict local file requests.

```bash
npm test
```

## Features

- Filter by procedure, diagnosis, sex, and age group.
- Cohort size, mean hospital stay, complication rate, and observed 6-month follow-up rate.
- VAS/ODI trajectories with visit-specific denominators and fixed score axes.
- Paired baseline-to-6-month score reductions.
- Searchable, paginated patient registry and filtered cohort CSV export.
- Accessible chart descriptions and responsive layouts.

## Data and analytical choices

The Python standard-library generator uses `random.Random(2026)`. It creates 240 records with surgeries in 2024–2025. Age is 22–82; procedure and diagnosis allocation are independent illustrative draws, not a representation of clinical case selection. Simulated hospital stay varies by procedure. Illustrative missing follow-up probabilities are 9% at 3 months and 17% at 6 months; actual proportions vary with the deterministic random draws.

Recovery is deliberately simulated as baseline minus random improvement, bounded to the instrument range. Complication probabilities and all observed patterns are assumptions. The generator does not model genuine treatment effects, confounding, natural history, or dependencies between visits. These limitations mean the dashboard cannot support comparative effectiveness claims.

VAS is displayed on a 0–10 scale, ODI on a 0–100 scale. Means use available records at each visit; the population can change between visits. Paired reductions include only patients with baseline and 6-month scores. Nulls are omitted from means, never treated as zero. No MCID threshold or inference is applied. Complications are mutually exclusive per record in this simple simulation; the rate is patients with any non-None complication divided by the filtered cohort size.

Registry ID search affects the table only. Dashboard filters affect all metrics, charts, table records, and CSV export. CSV export includes the whole filtered cohort, not just the current page or ID search.

## Structure

- `scripts/generate_data.py`: reproducible synthetic data generation.
- `dist/analytics.js`: pure analysis functions.
- `dist/app.js`: dashboard interaction and chart rendering.
- `dist/index.html`, `dist/styles.css`: interface.
- `dist/patients.json`, `dist/patients.csv`: synthetic datasets.
- `tests/analytics.test.js`: missingness, bounds, filtering and export checks.

## Skills demonstrated

Python, JavaScript modules, descriptive statistics, longitudinal data handling, data visualisation with SVG, responsive CSS, CSV export, Git, and automated testing.

A future research version would need an appropriately approved dataset, validated outcome definitions, data-quality checks, and an analysis plan before clinical interpretation.
