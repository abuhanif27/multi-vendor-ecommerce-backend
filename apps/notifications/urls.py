from django.urls import path
from apps.notifications.views import (
    NotificationListAPIView,
    NotificationReadAPIView,
    NotificationReadAllAPIView
)

urlpatterns = [
    path('notifications/', NotificationListAPIView.as_view(), name='notification-list'),
    path('notifications/read-all/', NotificationReadAllAPIView.as_view(), name='notification-read-all'),
    path('notifications/<uuid:pk>/read/', NotificationReadAPIView.as_view(), name='notification-read'),
]
