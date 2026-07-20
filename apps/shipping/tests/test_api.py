from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
import uuid

from apps.shops.models import Shop, Product, ProductVariant
from apps.catalog.models import Category
from apps.orders.models import Order, VendorOrder
from apps.shipping.models import Courier, Shipment
from apps.shipping.services.shipping import ShippingService

User = get_user_model()

class ShippingAPIIntegrationTestCase(APITestCase):
    def setUp(self):
        # Users
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="password123",
            first_name="Buyer"
        )
        self.vendor = User.objects.create_user(
            email="vendor@example.com",
            password="password123",
            first_name="Vendor",
            role="vendor"
        )
        self.other_vendor = User.objects.create_user(
            email="other@example.com",
            password="password123",
            role="vendor"
        )
        
        self.category = Category.objects.create(name="Electronics")
        self.shop = Shop.objects.create(owner=self.vendor, name="Tech Store", status=Shop.ShopStatus.APPROVED)
        
        self.order = Order.objects.create(
            user=self.buyer,
            subtotal=100.00,
            grand_total=100.00,
            status=Order.OrderStatus.PENDING,
            shipping_address={"street": "123 Test St"}
        )
        
        self.vendor_order = VendorOrder.objects.create(
            order=self.order,
            shop=self.shop,
            vendor_total=100.00,
            status=VendorOrder.FulfillmentStatus.PROCESSING
        )
        
        self.courier = Courier.objects.create(
            name="Pathao",
            tracking_url_template="https://pathao.com/track?id={tracking_number}"
        )
        
        # Initialize the shipment (simulating what OrderService does)
        self.shipment = ShippingService.initialize_shipment(self.vendor_order.id)

    def test_buyer_can_list_shipments(self):
        self.client.force_authenticate(user=self.buyer)
        url = reverse('buyer-shipments') + f"?order_id={self.order.id}"
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], Shipment.ShipmentStatus.PENDING)
        self.assertEqual(len(response.data['results'][0]['tracking_events']), 1)

    def test_vendor_can_assign_courier(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse('vendor-shipment-assign-courier', kwargs={'pk': self.shipment.id})
        
        data = {
            "courier_id": str(self.courier.id),
            "tracking_number": "PT-999"
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.shipment.refresh_from_db()
        self.assertEqual(self.shipment.tracking_number, "PT-999")
        self.assertEqual(self.shipment.tracking_url, "https://pathao.com/track?id=PT-999")

    def test_other_vendor_cannot_modify_shipment(self):
        self.client.force_authenticate(user=self.other_vendor)
        url = reverse('vendor-shipment-assign-courier', kwargs={'pk': self.shipment.id})
        
        data = {
            "courier_id": str(self.courier.id),
            "tracking_number": "PT-999"
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vendor_can_update_fsm_status(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse('vendor-shipment-update-status', kwargs={'pk': self.shipment.id})
        
        data = {
            "status": Shipment.ShipmentStatus.READY_FOR_PICKUP,
            "location": "Dhaka Warehouse",
            "description": "Packed and ready."
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.shipment.refresh_from_db()
        self.assertEqual(self.shipment.status, Shipment.ShipmentStatus.READY_FOR_PICKUP)
        self.assertEqual(self.shipment.tracking_events.count(), 2)

    def test_invalid_fsm_update_returns_400(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse('vendor-shipment-update-status', kwargs={'pk': self.shipment.id})
        
        # PENDING -> DELIVERED is illegal
        data = {
            "status": Shipment.ShipmentStatus.DELIVERED
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid transition", response.data['detail'][0])
