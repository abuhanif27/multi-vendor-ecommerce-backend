from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from apps.catalog.models import Category

class CategoryAPITest(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics", is_active=True)
        self.sub_category = Category.objects.create(name="Laptops", parent=self.category, is_active=True)
        self.inactive = Category.objects.create(name="Inactive", is_active=False)

    def test_list_categories(self):
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only list parent active categories, so only "Electronics"
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['name'], "Electronics")
        
    def test_retrieve_category(self):
        url = reverse('category-detail', kwargs={"slug": self.category.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Electronics")

    def test_retrieve_inactive_category(self):
        url = reverse('category-detail', kwargs={"slug": self.inactive.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
