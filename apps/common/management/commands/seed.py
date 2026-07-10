from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.choices import UserRole
from apps.catalog.models import Category
from apps.shops.models import Product, Shop

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo marketplace data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete demo data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.reset_demo_data()

        self.stdout.write(
            self.style.NOTICE("🌱 Seeding database...")
        )

        self.create_categories()
        self.create_users()
        self.create_shops()
        self.create_products()

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Database seeded successfully!"
            )
        )

    def reset_demo_data(self):
        self.stdout.write(
            self.style.WARNING("🗑 Removing demo data...")
        )

        demo_emails = [
            "apple@example.com",
            "samsung@example.com",
            "dell@example.com",
            "customer1@example.com",
            "customer2@example.com",
        ]

        Product.objects.filter(
            shop__owner__email__in=demo_emails
        ).delete()

        Shop.objects.filter(
            owner__email__in=demo_emails
        ).delete()

        User.objects.filter(
            email__in=demo_emails
        ).delete()

        Category.objects.filter(
            name__in=[
                "Phones",
                "Laptops",
                "Accessories",
                "Fashion",
                "Books",
            ]
        ).delete()

        self.stdout.write(
            self.style.SUCCESS("✓ Demo data removed.")
        )

    def create_categories(self):
        self.stdout.write("Creating categories...")

        categories = [
            "Phones",
            "Laptops",
            "Accessories",
            "Fashion",
            "Books",
        ]

        for name in categories:
            _, created = Category.objects.get_or_create(
                name=name,
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ {name}")
                )
            else:
                self.stdout.write(
                    f"  • {name} already exists"
                )

    def create_users(self):
        self.stdout.write("Creating users...")

        users = [
            {
                "email": "apple@example.com",
                "role": UserRole.VENDOR,
            },
            {
                "email": "samsung@example.com",
                "role": UserRole.VENDOR,
            },
            {
                "email": "dell@example.com",
                "role": UserRole.VENDOR,
            },
            {
                "email": "customer1@example.com",
                "role": UserRole.CUSTOMER,
            },
            {
                "email": "customer2@example.com",
                "role": UserRole.CUSTOMER,
            },
        ]

        for data in users:

            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "role": data["role"],
                    "is_verified": True,
                },
            )

            if created:
                user.set_password("password123")
                user.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ {user.email}"
                    )
                )

            else:
                self.stdout.write(
                    f"  • {user.email} already exists"
                )

    def create_shops(self):
        self.stdout.write("Creating shops...")

        shops = [
            {
                "name": "Apple Store",
                "owner_email": "apple@example.com",
            },
            {
                "name": "Samsung Store",
                "owner_email": "samsung@example.com",
            },
            {
                "name": "Dell Store",
                "owner_email": "dell@example.com",
            },
        ]

        for data in shops:
            owner = User.objects.get(
                email=data["owner_email"],
            )

            shop, created = Shop.objects.get_or_create(
                owner=owner,
                name=data["name"],
                defaults={
                    "status": Shop.ShopStatus.APPROVED,
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ {shop.name}"
                    )
                )
            else:
                self.stdout.write(
                    f"  • {shop.name} already exists"
                )

    def create_products(self):
        self.stdout.write("Creating products...")

        categories = {
            category.name: category
            for category in Category.objects.all()
        }

        shops = {
            shop.name: shop
            for shop in Shop.objects.all()
        }

        products = [
            {
                "shop": "Apple Store",
                "category": "Phones",
                "name": "iPhone 16 Pro",
                "price": Decimal("1499.00"),
                "stock": 20,
            },
            {
                "shop": "Apple Store",
                "category": "Laptops",
                "name": "MacBook Air M4",
                "price": Decimal("1999.00"),
                "stock": 10,
            },
            {
                "shop": "Apple Store",
                "category": "Accessories",
                "name": "AirPods Pro",
                "price": Decimal("349.00"),
                "stock": 50,
            },
            {
                "shop": "Samsung Store",
                "category": "Phones",
                "name": "Galaxy S25 Ultra",
                "price": Decimal("1399.00"),
                "stock": 30,
            },
            {
                "shop": "Samsung Store",
                "category": "Accessories",
                "name": "Galaxy Buds 3",
                "price": Decimal("249.00"),
                "stock": 40,
            },
            {
                "shop": "Dell Store",
                "category": "Laptops",
                "name": "Dell XPS 13",
                "price": Decimal("1799.00"),
                "stock": 15,
            },
        ]

        for data in products:

            product, created = Product.objects.get_or_create(
                shop=shops[data["shop"]],
                name=data["name"],
                defaults={
                    "category": categories[data["category"]],
                    "description": f'{data["name"]} demo product.',
                    "price": data["price"],
                    "stock": data["stock"],
                    "status": Product.ProductStatus.ACTIVE,
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ {product.name}'
                    )
                )
            else:
                self.stdout.write(
                    f'  • {product.name} already exists'
                )
