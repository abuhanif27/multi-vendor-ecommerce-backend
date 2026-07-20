from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, NotificationDelivery
from apps.notifications.services.notification import NotificationService

User = get_user_model()

class NotificationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="buyer@example.com", password="password")
        self.other_user = User.objects.create_user(email="other@example.com", password="password")
        
        # Create a notification for self.user
        self.notification = Notification.objects.create(
            recipient=self.user,
            title="Order Shipped",
            message="Your order is on the way."
        )
        NotificationDelivery.objects.create(
            notification=self.notification,
            channel=NotificationDelivery.DeliveryChannel.IN_APP
        )
        
        # Create an email ONLY notification (should not show up in inbox)
        self.email_notif = Notification.objects.create(
            recipient=self.user,
            title="Email Only",
            message="Email message."
        )
        NotificationDelivery.objects.create(
            notification=self.email_notif,
            channel=NotificationDelivery.DeliveryChannel.EMAIL
        )
        
        self.list_url = reverse('notification-list')
        self.read_url = reverse('notification-read', kwargs={'pk': self.notification.id})
        self.read_all_url = reverse('notification-read-all')

    def test_list_notifications(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return the IN_APP notification
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Order Shipped")
        self.assertFalse(response.data['results'][0]['is_read'])

    def test_mark_as_read(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.read_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
        
        self.notification.refresh_from_db()
        self.assertIsNotNone(self.notification.read_at)

    def test_cannot_read_others_notification(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(self.read_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_all_as_read(self):
        # Create another IN_APP notif
        n2 = Notification.objects.create(recipient=self.user, title="Second", message="Second message")
        NotificationDelivery.objects.create(notification=n2, channel=NotificationDelivery.DeliveryChannel.IN_APP)
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.read_all_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Marked 2 notifications", response.data['detail'])
        
        self.notification.refresh_from_db()
        n2.refresh_from_db()
        
        self.assertIsNotNone(self.notification.read_at)
        self.assertIsNotNone(n2.read_at)
