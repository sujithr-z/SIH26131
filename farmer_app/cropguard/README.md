# CropGuard — Backend Data Pipeline & Live Monitor

This adds a backend observation pipeline on top of the existing
farmer-facing prototype (login → diagnose → analyze → report). Nothing
about the existing pages changed structurally — see "What changed" below.

## Project structure

```
cropguard/
├── index.php / login.php / diagnose.php / analyze.php / report.php / logout.php
├── css/, js/, uploads/
├── data/
│   ├── farmers.json          existing farmer "database"
│   └── observations.json     NEW: disease observation "database"
├── includes/
│   └── ObservationRepository.php   NEW: single read/write boundary for observations
├── api/
│   └── save_observation.php  NEW: standalone JSON HTTP endpoint
└── monitor/
    └── monitor.py             NEW: live read-only terminal viewer (pure stdlib)
```

## What changed in the existing app

Only **one** file was touched: `analyze.php`. A small block was added
right after the (still-stubbed) diagnosis is finalized, which saves it
as an observation via `ObservationRepository`. It's wrapped in
try/catch so a storage problem can never break the existing
diagnose → report flow. Nothing else in the app was modified.

## Observation schema (`data/observations.json`)

```json
{
  "observations": [
    {
      "observation_id": "OBS-000001",
      "farmer_id": "001",
      "disease": "Tomato Early Blight",
      "confidence": 0.94,
      "timestamp": "2026-08-26T13:30:21+05:30",
      "crop": "Tomato",
      "image_path": "uploads/farmer001_1787733980.jpg"
    }
  ]
}
```

- `farmer_id` — always a **string**, leading zeros preserved. Matches
  the existing 3-digit format in `farmers.json` (`001`, `002`, ...).
- `confidence` — always **0.0–1.0**. The diagnose/report UI shows
  confidence as 0–100 with a `%`; `analyze.php` divides by 100 before
  calling the repository. Don't mix the two scales anywhere else.
- `crop`, `image_path` — optional extension fields, included whenever
  the caller has them. Not required.
- Reserved for later (not implemented yet, but the repository already
  whitelists them so adding is a one-line change): `field_id`,
  `latitude`, `longitude`, `crop_stage`, `weather_snapshot`,
  `validation_status`, `expert_result`.

Images are **not** stored in the JSON. Only `image_path` (a relative
path into `uploads/`) is stored. Base64-embedding images into a JSON
file that's read/written on every request would bloat the file
linearly with every observation and make the read-modify-write lock
hold much longer — bad for concurrency and for a file that's supposed
to stay diffable/human-readable.

## Two ways an observation gets saved

**1. In-app (already wired up):** `analyze.php` calls
`ObservationRepository::save()` directly as a PHP class — no HTTP
round-trip, since it's already inside the trusted, session-authenticated
backend.

**2. External API (for anything else — curl, a future JS `fetch()`,
a future mobile client):**

```
POST /api/save_observation.php
Content-Type: application/json

{ "farmer_id": "001", "disease": "Tomato Early Blight", "confidence": 0.94 }
```

Responses:
| Situation | HTTP | Body |
|---|---|---|
| Saved | 200 | `{"success":true,"observation_id":"OBS-000001","message":"Observation saved successfully"}` |
| Missing field | 422 | `{"success":false,"error":"farmer_id, disease and confidence are all required."}` |
| Confidence out of 0–1 range | 422 | `{"success":false,"error":"confidence must be a number between 0.0 and 1.0."}` |
| Malformed JSON / not POST | 400 | `{"success":false,"error":"..."}` |
| Storage failure | 500 | `{"success":false,"error":"Server error while saving observation."}` (no internal paths ever leaked) |

Both paths write through the same `ObservationRepository`, so there's
exactly one place that knows how to persist an observation.

## Concurrency / data safety

`ObservationRepository` takes an exclusive `flock()` lock around the
whole read-modify-write cycle, writes to a temp file, then `rename()`s
it over the real file (atomic on both Linux and Windows). This was
load-tested with 20 simultaneous requests — all 20 landed with unique
sequential IDs and no corruption or lost writes.

## Running it

```bash
cd cropguard
php -S localhost:8000
```
Open `http://localhost:8000` in Chrome.

In a second terminal:
```bash
cd cropguard/monitor
python3 monitor.py
```
No `pip install` needed — the monitor is pure standard library
(`os`, `json`, `time`, `datetime`). Polls `data/observations.json`
every second; Ctrl+C to quit.

## End-to-end test

1. Start the PHP server and `monitor.py` as above.
2. In Chrome, log in as farmer "John Doe" / any phone number.
3. Drop/upload a leaf photo, click **Analyze Crop Health**.
4. The report page appears — and within ~1 second the terminal running
   `monitor.py` redraws showing that observation, no restart needed.
5. Log out, log in as a second farmer with a different phone number,
   repeat step 3 — watch the terminal pick up farmer `002` automatically.

## Direct API test (independent of the frontend)

```bash
curl -X POST http://localhost:8000/api/save_observation.php \
  -H "Content-Type: application/json" \
  -d '{"farmer_id":"001","disease":"Tomato Early Blight","confidence":0.94}'
```

## Evolving past JSON

`ObservationRepository` is the abstraction boundary. To move to
SQLite/PostgreSQL later:

```
Frontend → analyze.php / api/save_observation.php → ObservationRepository → JSON file   (today)
Frontend → analyze.php / api/save_observation.php → ObservationRepository → SQLite/Postgres  (later)
```

Rewrite the internals of `save()` and `all()` in
`ObservationRepository.php` to use PDO instead of `file_get_contents`/
`rename()`, keeping the same method signatures. Nothing in
`analyze.php` or `api/save_observation.php` needs to change — that's
the entire point of routing everything through one repository class.

## Security note

This is a **local prototype**. Basic hygiene is in place (input
validation, a fixed allow-list for extra fields, no raw PHP
warnings/paths returned to clients, filenames sanitized on upload).
It has **no** authentication on `api/save_observation.php` itself, no
rate limiting, and no HTTPS — all of that is a production concern, not
a prototype one. Don't expose this port to the open internet as-is.
