# Bulk Certificate Generator

A Django REST Framework API that accepts a batch of recipients, creates one PDF certificate per recipient from a fixed template, records per-recipient results in a relational database, and serves successful certificates as downloads.

## Requirements

- Python 3.10 or newer
- pip

## Setup

From the project root, create and activate a virtual environment, then install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Apply database migrations:

```powershell
python manage.py migrate
```

## Run the application

```powershell
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000`. Open the root URL to see a JSON status page listing the API endpoints. SQLite is used by default. Set `DATABASE_NAME` to choose a different SQLite database file and `CERTIFICATE_DIR` to choose where generated PDFs are stored. Set `DJANGO_SECRET_KEY` and configure `DJANGO_ALLOWED_HOSTS` before deployment.

## Create a generation job

Submit the whole batch in one JSON request:

```powershell
$body = @{
  event_name = "Python Fundamentals"
  issue_date = "2026-10-09"
  recipients = @(
    @{ name = "Ada Lovelace"; email = "ada@example.com" },
    @{ name = "Grace Hopper"; email = "grace@example.com" }
  )
} | ConvertTo-Json -Depth 5

$job = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/jobs `
  -ContentType "application/json" `
  -Body $body

$job.id
```

`event_name` and recipient `name` must be non-blank and at most 200 characters. Emails must be valid. A batch contains 1–5,000 recipients. Invalid input returns HTTP `400` with field-level validation details.

## Check job status

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/jobs/$($job.id)"
```

The response contains the job status, counts, and each recipient's status and error (when applicable). Successful recipients have a `certificate_url`.

## Retrieve a generated certificate

```powershell
Invoke-WebRequest `
  -Uri "http://127.0.0.1:8000$($job.recipients[0].certificate_url)" `
  -OutFile certificate.pdf
```

The download endpoint is `GET /api/certificates/{recipient_id}/`. It returns a PDF with content type `application/pdf`, or `404` if the file is unavailable or generation failed.

## Run tests

```powershell
python manage.py test tests
```

The tests use Django's isolated test database and temporary certificate directories. They cover job creation and status, input validation, PDF generation, per-recipient failure handling, and certificate downloads.

## Design decisions

- **Django REST Framework + SQLite:** DRF serializers validate the request and Django ORM persists job and recipient state using relational tables.
- **Synchronous bulk generation:** The API creates the job and all recipient rows before generating PDFs in the same request. This keeps the example straightforward and makes all statuses and results available immediately; the request may take longer for large batches. A durable production system should move processing to a worker queue such as Celery rather than use request workers for long-running generation.
- **Failure isolation:** Each recipient is handled and persisted independently. A certificate error is recorded against that recipient; remaining recipients still generate. A job with one or more failures ends in `completed_with_errors`.
- **Single certificate design:** `app/generator.py` draws a fixed landscape PDF; there is no template editor or multi-template behavior.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/jobs` | Validate a batch and generate certificates |
| `GET` | `/api/jobs/{job_id}` | Retrieve job progress and per-recipient results |
| `GET` | `/api/certificates/{recipient_id}/` | Download a generated PDF |
