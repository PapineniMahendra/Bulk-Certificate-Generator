import uuid

from django.db import models


class JobStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors", "Completed with errors"


class CertificateStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class GenerationJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_name = models.CharField(max_length=200)
    issue_date = models.DateField()
    status = models.CharField(
        max_length=32, choices=JobStatus.choices, default=JobStatus.PENDING
    )
    total_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class RecipientCertificate(models.Model):
    job = models.ForeignKey(
        GenerationJob, related_name="recipients", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=320)
    status = models.CharField(
        max_length=16, choices=CertificateStatus.choices, default=CertificateStatus.PENDING
    )
    certificate_path = models.TextField(blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]
