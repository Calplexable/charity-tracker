# Charity Tracker

A small web app for tracking volunteer hours and donations — built for
the kind of record-keeping a small charity or community group actually
needs: who volunteered, how long for, who donated, and how much, all
in one place with a quick dashboard summary.

## Features

- **People** — keep a simple contact list of volunteers and donors.
- **Volunteer hours** — log hours against an activity and a date, see
  totals per person and overall.
- **Donations** — log donations with amount, currency, method, and date.
- **Dashboard** — at-a-glance totals, a leaderboard of top volunteers
  and donors, and recent activity.
- **Person profile pages** — every person has their own page showing
  their full history of hours and donations.
- Built on **SQLite** — zero setup, the database is just a file.

## Installation

```bash
git clone https://github.com/Calplexable/charity-tracker.git
cd charity-tracker
pip install -r requirements.txt
```

## Running it

```bash
python run.py
```

Then open `http://127.0.0.1:5000` in your browser. The database file
(`charity_tracker.db`) is created automatically on first run, in the
project folder.

## Running tests

```bash
python -m unittest discover -s tests -v
```

33 tests covering the data layer (people, hours, donations, summary
stats, and cascading deletes) and the Flask routes (every page loads,
every form submission works correctly).

## Project structure

```
charity-tracker/
├── run.py                      # Entry point
├── app/
│   ├── main.py                 # Flask routes
│   ├── db.py                   # SQLite schema + connection handling
│   ├── repository.py           # Data access layer (all queries live here)
│   ├── templates/              # Jinja2 templates
│   └── static/style.css
├── tests/
│   ├── test_repository.py
│   └── test_routes.py
└── requirements.txt
```

## Design notes

- All database access goes through `app/repository.py` — no raw SQL
  anywhere else in the codebase, which makes the data layer easy to
  test in isolation from Flask.
- Deleting a person cascades to delete their logged hours and donations
  (enforced at the database level via `ON DELETE CASCADE`), so there's
  no orphaned data left behind.
- The database path is configurable via the `CHARITY_TRACKER_DB`
  environment variable, which is what makes the test suite able to run
  against a disposable temp database instead of your real data.

## Possible extensions

- Export hours/donations to CSV for accountancy or grant reporting
- Email receipts for donations
- Simple authentication if this were used by more than one coordinator
- Date-range filtering on the dashboard (e.g. "this quarter")
