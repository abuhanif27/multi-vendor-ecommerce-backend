from apps.shops.permissions import IsProductOwner, IsVendor, IsShopOwner
from apps.shops.serializers import ShopSerializer, ProductSerializer
from django_filters.rest_framework import DjangoFilterBackend

from apps.shops.filters import ProductFilter
from apps.shops.models import Shop, Product
from rest_framework import generics
from rest_framework import filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view


@extend_schema_view(
    get=extend_schema(
        tags=["Shops"],
        summary="List shops",
        description="""
Returns all approved shops.

This endpoint is public.

Supports:
- Pagination
""",
        responses={
            200: ShopSerializer,
        },
    ),
    post=extend_schema(
        tags=["Shops"],
        summary="Create shop",
        description="""
Creates a new shop for the authenticated vendor.

Authentication:
- Vendor only
""",
        request=ShopSerializer,
        responses={
            201: ShopSerializer,
            400: None,
            401: None,
            403: None,
        },
    ),
)
class ShopListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ShopSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsVendor()]

        return []

    def get_queryset(self):
        return (
            Shop.objects
            .filter(
                status=Shop.ShopStatus.APPROVED,
            )
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@extend_schema_view(
    get=extend_schema(
        tags=["Products"],
        summary="List products",
        description="""
Returns active products from approved shops.

Features:

- Pagination
- Category filtering
- Shop filtering
- Price filtering
- Search
- Ordering

Public endpoint.
""",
        parameters=[
            OpenApiParameter(
                name="category",
                type=str,
                description="Category slug.",
            ),
            OpenApiParameter(
                name="shop",
                type=str,
                description="Shop slug.",
            ),
            OpenApiParameter(
                name="min_price",
                type=float,
                description="Minimum product price.",
            ),
            OpenApiParameter(
                name="max_price",
                type=float,
                description="Maximum product price.",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                description="Search by product name, description, shop name or category name.",
            ),
            OpenApiParameter(
                name="ordering",
                type=str,
                description="Available values: price, -price, name, created_at, -created_at.",
            ),
        ],
        responses={
            200: ProductSerializer,
        },
    ),
    post=extend_schema(
        tags=["Products"],
        summary="Create product",
        description="""
Creates a new product for the authenticated vendor.

Requirements:

- Authenticated user
- Vendor role
""",
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: None,
            401: None,
            403: None,
        },
    ),
)
class ProductListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = ProductFilter

    search_fields = ['name', 'description', 'shop__name', 'category__name']
    ordering_fields = ['price', 'created_at', 'name']

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsVendor()]
        return []

    def get_queryset(self):
        return (Product.objects
                .select_related('shop', 'category')
                .filter(status=Product.ProductStatus.ACTIVE, shop__status=Shop.ShopStatus.APPROVED)
                )


@extend_schema_view(
    get=extend_schema(
        tags=["Products"],
        summary="Retrieve product",
        description="""
Retrieve a single active product by its slug.

This endpoint is public.
""",
        responses={
            200: ProductSerializer,
            404: None,
        },
    ),
    patch=extend_schema(
        tags=["Products"],
        summary="Update product",
        description="""
Partially update a product.

Requirements:
- Authenticated user
- Vendor role
- Product owner
""",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: None,
            401: None,
            403: None,
            404: None,
        },
    ),
    put=extend_schema(
        exclude=True,
    ),
    delete=extend_schema(
        tags=["Products"],
        summary="Delete product",
        description="""
Delete a product.

Requirements:
- Authenticated user
- Vendor role
- Product owner
""",
        responses={
            204: None,
            401: None,
            403: None,
            404: None,
        },
    ),
)
class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Product.objects
            .select_related("shop")
            .filter(
                status=Product.ProductStatus.ACTIVE,
                shop__status=Shop.ShopStatus.APPROVED,
            )
        )


class MyProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return (
            Product.objects
            .select_related("shop")
            .filter(
                shop__owner=self.request.user,
            )
        )


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("shop")
    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsVendor(), IsProductOwner()]
        return [IsAuthenticatedOrReadOnly()]


class MyShopListAPIView(generics.ListAPIView):
    serializer_class = ShopSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return (
            Shop.objects
            .filter(
                owner=self.request.user,
            )
        )


class ShopDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShopSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [
                IsVendor(),
                IsShopOwner(),
            ]

        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        if self.request.method == "GET":
            return Shop.objects.filter(
                status=Shop.ShopStatus.APPROVED,
            )

        return Shop.objects.all()
