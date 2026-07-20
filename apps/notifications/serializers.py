from rest_framework import serializers
from apps.notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the frontend notification bell/inbox.
    """
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'action_url', 'created_at', 'is_read']

    def get_is_read(self, obj) -> bool:
        return obj.read_at is not None
