from django.urls import path

from app.views import CertificateDownloadView, GenerationJobView

urlpatterns = [
    path("jobs", GenerationJobView.as_view(), name="generation-jobs"),
    path("jobs/<uuid:job_id>", GenerationJobView.as_view(), name="generation-job"),
    path(
        "certificates/<int:recipient_id>/",
        CertificateDownloadView.as_view(),
        name="certificate-download",
    ),
]
