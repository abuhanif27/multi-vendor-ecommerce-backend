from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import HealthCheckSerializer


from drf_spectacular.utils import extend_schema, OpenApiResponse
class HealthCheckAPIView(APIView):

    @extend_schema(
        summary="Health Check",
        description="Returns the status of the API.",
        responses={200: HealthCheckSerializer},
        tags=['Core']
    )
    def get(self, request):
        data = {
            "status": "ok",
            "message": "Multi-Vendor E-commerce Backend is running.",
        }

        serializer = HealthCheckSerializer(instance=data)

        return Response(serializer.data)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Current User",
        description="Returns the currently authenticated user's basic info.",
        responses={200: OpenApiResponse(response=dict, description="User info")},
        tags=['Core']
    )
    def get(self, request):
        return Response(
            {
                "id": str(request.user.id),
                "email": request.user.email,
            }
        )
