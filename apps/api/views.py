from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckAPIView(APIView):
    """
    Simple API to verify the backend is running.
    """

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "message": "Multi-Vendor E-commerce Backend is running.",
            }
        )
