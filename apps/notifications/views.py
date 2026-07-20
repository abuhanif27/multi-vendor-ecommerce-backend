from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from apps.notifications.models import Notification, NotificationDelivery
from apps.notifications.serializers import NotificationSerializer
from apps.common.pagination import DefaultPagination

class NotificationListAPIView(generics.ListAPIView):
    """
    GET: Returns a paginated list of IN_APP notifications for the authenticated user.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        # We fetch Notifications that have an IN_APP delivery attached.
        # This prevents returning SMS/Email only notifications to the frontend inbox.
        return Notification.objects.filter(
            recipient=self.request.user,
            deliveries__channel=NotificationDelivery.DeliveryChannel.IN_APP
        ).distinct()

class NotificationReadAPIView(APIView):
    """
    PATCH: Marks a specific notification as read.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: NotificationSerializer})
    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=['read_at'])

        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationReadAllAPIView(APIView):
    """
    POST: Bulk marks all unread IN_APP notifications as read for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}})
    def post(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            read_at__isnull=True,
            deliveries__channel=NotificationDelivery.DeliveryChannel.IN_APP
        ).update(read_at=timezone.now())

        return Response({"detail": f"Marked {count} notifications as read."}, status=status.HTTP_200_OK)
