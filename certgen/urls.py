from django.http import JsonResponse
from django.urls import include, path


def api_root(request):
    return JsonResponse(
        {
            "name": "Bulk Certificate Generator",
            "status": "running",
            "endpoints": {
                "create_job": "POST /api/jobs",
                "check_job": "GET /api/jobs/{job_id}",
                "download_certificate": "GET /api/certificates/{recipient_id}/",
            },
        }
    )


urlpatterns = [
    path("", api_root, name="api-root"),
    path("api/", include("app.urls")),
]
