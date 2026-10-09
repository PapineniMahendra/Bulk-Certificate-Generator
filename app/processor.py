import logging
from pathlib import Path

from django.conf import settings

from app import generator
from app.models import CertificateStatus, GenerationJob, JobStatus

logger = logging.getLogger(__name__)


def process_job(job_id) -> None:
    job = GenerationJob.objects.get(pk=job_id)
    job.status = JobStatus.PROCESSING
    job.save(update_fields=["status"])

    for recipient in job.recipients.all():
        recipient.status = CertificateStatus.PROCESSING
        recipient.save(update_fields=["status"])
        output_path = Path(settings.MEDIA_ROOT) / (
            f"job-{job.pk}-recipient-{recipient.pk}.pdf"
        )
        try:
            generator.generate_certificate(
                output_path=output_path,
                recipient_name=recipient.name,
                event_name=job.event_name,
                issue_date=job.issue_date,
            )
            recipient.certificate_path = str(output_path.resolve())
            recipient.status = CertificateStatus.COMPLETED
            recipient.error = ""
        except Exception as exc:
            logger.exception(
                "Certificate generation failed for recipient %s in job %s.",
                recipient.pk,
                job.pk,
            )
            recipient.certificate_path = ""
            recipient.status = CertificateStatus.FAILED
            recipient.error = f"{type(exc).__name__}: {exc}"
            if output_path.exists():
                output_path.unlink()
        recipient.save(update_fields=["certificate_path", "status", "error"])

    has_failures = job.recipients.filter(status=CertificateStatus.FAILED).exists()
    job.status = JobStatus.COMPLETED_WITH_ERRORS if has_failures else JobStatus.COMPLETED
    job.save(update_fields=["status"])
