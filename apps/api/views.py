from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import HealthCheckSerializer


class HealthCheckAPIView(APIView):

    def get(self, request):
        data = {
            "status": "ok",
            "message": "Multi-Vendor E-commerce Backend is running.",
        }

        serializer = HealthCheckSerializer(instance=data)

        return Response(serializer.data)
