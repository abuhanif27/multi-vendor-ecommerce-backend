from django.urls import path

from apps.api.views import HealthCheckAPIView, MeAPIView

urlpatterns = [
    path("health/", HealthCheckAPIView.as_view(), name="health-check"),
    path('me/', MeAPIView.as_view(), name='me'),
]
