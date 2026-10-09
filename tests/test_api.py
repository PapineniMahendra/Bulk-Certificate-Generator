from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from app import generator
from app.models import CertificateStatus, GenerationJob, JobStatus, RecipientCertificate
from app.processor import process_job


class BulkCertificateApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_api_root_shows_available_endpoints(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "running")
        self.assertIn("POST /api/jobs", response.json()["endpoints"]["create_job"])

    @staticmethod
    def payload():
        return {
            "event_name": "Python Fundamentals",
            "issue_date": "2026-10-09",
            "recipients": [
                {"name": "Ada Lovelace", "email": "ada@example.com"},
                {"name": "Grace Hopper", "email": "grace@example.com"},
            ],
        }

    def test_create_job_and_track_progress(self):
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            response = self.client.post("/api/jobs", self.payload(), format="json")

            self.assertEqual(response.status_code, 201)
            result = response.json()
            self.assertEqual(result["status"], JobStatus.COMPLETED)
            self.assertEqual(result["total_count"], 2)
            self.assertEqual(result["completed_count"], 2)
            self.assertEqual(result["failed_count"], 0)
            self.assertTrue(all(item["certificate_url"] for item in result["recipients"]))

            status_response = self.client.get(f"/api/jobs/{result['id']}")
            self.assertEqual(status_response.status_code, 200)
            self.assertEqual(status_response.json()["status"], JobStatus.COMPLETED)

    def test_invalid_input_is_rejected(self):
        payloads = (
            {"event_name": "Course", "issue_date": "2026-10-09", "recipients": []},
            {
                "event_name": "Course",
                "issue_date": "2026-10-09",
                "recipients": [{"name": " ", "email": "valid@example.com"}],
            },
            {
                "event_name": "Course",
                "issue_date": "2026-10-09",
                "recipients": [{"name": "Valid Name", "email": "not-an-email"}],
            },
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/jobs", payload, format="json")
                self.assertEqual(response.status_code, 400)
        self.assertEqual(GenerationJob.objects.count(), 0)

    def test_certificate_generation_creates_pdf(self):
        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "certificate.pdf"
            generator.generate_certificate(
                output, "Ada Lovelace", "Python Fundamentals", date(2026, 10, 9)
            )
            self.assertTrue(output.read_bytes().startswith(b"%PDF"))

    def test_one_certificate_failure_does_not_stop_job(self):
        job = GenerationJob.objects.create(
            event_name="Python Fundamentals",
            issue_date=date(2026, 10, 9),
            total_count=2,
        )
        first = RecipientCertificate.objects.create(
            job=job, name="Ada Lovelace", email="ada@example.com"
        )
        second = RecipientCertificate.objects.create(
            job=job, name="Grace Hopper", email="grace@example.com"
        )
        original_generate = generator.generate_certificate

        def fail_for_ada(output_path, recipient_name, event_name, issue_date):
            if recipient_name == "Ada Lovelace":
                raise RuntimeError("simulated rendering issue")
            original_generate(output_path, recipient_name, event_name, issue_date)

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            with patch("app.processor.generator.generate_certificate", side_effect=fail_for_ada):
                process_job(job.pk)

        job.refresh_from_db()
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(job.status, JobStatus.COMPLETED_WITH_ERRORS)
        self.assertEqual(first.status, CertificateStatus.FAILED)
        self.assertIn("simulated rendering issue", first.error)
        self.assertEqual(second.status, CertificateStatus.COMPLETED)

    def test_generated_certificate_can_be_retrieved(self):
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            result = self.client.post("/api/jobs", self.payload(), format="json").json()
            recipient_id = result["recipients"][0]["id"]
            response = self.client.get(f"/api/certificates/{recipient_id}/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/pdf")
            self.assertTrue(b"".join(response.streaming_content).startswith(b"%PDF"))

    def test_missing_resources_return_404(self):
        missing_job = "/api/jobs/00000000-0000-0000-0000-000000000000"
        self.assertEqual(self.client.get(missing_job).status_code, 404)
        self.assertEqual(self.client.get("/api/certificates/999999/").status_code, 404)
