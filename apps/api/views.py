from rest_framework.permissions import IsAuthenticated
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


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "id": str(request.user.id),
                "email": request.user.email,
            }
        )
