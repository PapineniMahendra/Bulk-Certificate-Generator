from rest_framework import serializers

from app.models import CertificateStatus, GenerationJob, RecipientCertificate


class RecipientInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, allow_blank=False, trim_whitespace=True)
    email = serializers.EmailField(max_length=320)

    def validate_name(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError("Name must not be blank.")
        return value


class CreateJobSerializer(serializers.Serializer):
    event_name = serializers.CharField(max_length=200, allow_blank=False, trim_whitespace=True)
    issue_date = serializers.DateField()
    recipients = RecipientInputSerializer(many=True, allow_empty=False, max_length=5000)

    def validate_event_name(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError("Event name must not be blank.")
        return value


class RecipientResultSerializer(serializers.ModelSerializer):
    certificate_url = serializers.SerializerMethodField()

    class Meta:
        model = RecipientCertificate
        fields = ["id", "name", "email", "status", "error", "certificate_url"]

    def get_certificate_url(self, recipient: RecipientCertificate) -> str | None:
        if recipient.status != CertificateStatus.COMPLETED:
            return None
        return f"/api/certificates/{recipient.pk}/"


class JobResultSerializer(serializers.ModelSerializer):
    completed_count = serializers.SerializerMethodField()
    failed_count = serializers.SerializerMethodField()
    recipients = RecipientResultSerializer(many=True, read_only=True)

    class Meta:
        model = GenerationJob
        fields = [
            "id",
            "event_name",
            "issue_date",
            "status",
            "total_count",
            "completed_count",
            "failed_count",
            "created_at",
            "recipients",
        ]

    def get_completed_count(self, job: GenerationJob) -> int:
        return job.recipients.filter(status=CertificateStatus.COMPLETED).count()

    def get_failed_count(self, job: GenerationJob) -> int:
        return job.recipients.filter(status=CertificateStatus.FAILED).count()
