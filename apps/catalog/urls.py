from django.urls import path
from apps.catalog.views import CategoryListAPIView, CategoryDetailAPIView

urlpatterns = [
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
    path("categories/<slug:slug>/",
         CategoryDetailAPIView.as_view(), name="category-detail"),
]
