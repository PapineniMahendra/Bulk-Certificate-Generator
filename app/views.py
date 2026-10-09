import logging
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import CertificateStatus, GenerationJob, RecipientCertificate
from app.processor import process_job
from app.serializers import CreateJobSerializer, JobResultSerializer

logger = logging.getLogger(__name__)


class GenerationJobView(APIView):
    def post(self, request):
        serializer = CreateJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data

        job = GenerationJob.objects.create(
            event_name=values["event_name"],
            issue_date=values["issue_date"],
            total_count=len(values["recipients"]),
        )
        RecipientCertificate.objects.bulk_create(
            [
                RecipientCertificate(
                    job=job,
                    name=item["name"],
                    email=item["email"],
                    status=CertificateStatus.PENDING,
                )
                for item in values["recipients"]
            ]
        )

        process_job(job.pk)
        job.refresh_from_db()
        return Response(JobResultSerializer(job).data, status=status.HTTP_201_CREATED)

    def get(self, request, job_id):
        job = get_object_or_404(
            GenerationJob.objects.prefetch_related("recipients"), pk=job_id
        )
        return Response(JobResultSerializer(job).data)


class CertificateDownloadView(APIView):
    def get(self, request, recipient_id):
        recipient = get_object_or_404(RecipientCertificate, pk=recipient_id)
        if recipient.status != CertificateStatus.COMPLETED or not recipient.certificate_path:
            raise Http404("Certificate is not available.")

        path = Path(recipient.certificate_path)
        if not path.is_file():
            logger.error("Generated certificate file is missing: %s", path)
            raise Http404("Generated certificate file is missing.")
        return FileResponse(
            path.open("rb"),
            as_attachment=True,
            filename=f"certificate-{recipient.pk}.pdf",
            content_type="application/pdf",
        )
