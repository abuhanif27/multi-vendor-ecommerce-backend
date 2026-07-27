# Multi-Vendor E-Commerce Backend

Production-oriented Django REST API for a multi-vendor marketplace. The project is structured for deployment, maintainability, and technical presentation on a public portfolio.

## Overview

This backend provides the API and operational services for a marketplace-style commerce platform. It is organized around focused Django apps, JWT authentication, OpenAPI documentation, asynchronous background jobs, and payment gateway integrations.

## Live Entry Points

- Developer Portal: `/`
- Swagger UI: `/docs/`
- ReDoc: `/redoc/`
- OpenAPI Schema: `/schema/`
- Health Check: `/health/`
- Django Admin: `/admin/`

## Architecture

- Django + Django REST Framework for the API layer.
- Service-layer boundaries for business logic.
- Celery for asynchronous background jobs.
- Redis for queueing and cache-backed workflows.
- PostgreSQL for production data storage.
- WhiteNoise for static asset delivery.
- TailwindCSS-powered Django template portal for presentation.

## Technology Stack

- Python 3.12+
- Django 5.2
- Django REST Framework
- drf-spectacular
- Simple JWT
- PostgreSQL
- Redis
- Celery
- Gunicorn
- WhiteNoise
- TailwindCSS

## Verified Platform Modules

- Authentication
- Users
- Vendors
- Shops
- Categories
- Products
- Inventory
- Cart
- Checkout
- Orders
- Payments
- Refunds
- Returns
- Shipping
- Reviews
- Notifications
- Promotions
- Analytics
- Administration

## Installation

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and populate the values.
4. Run migrations with `python manage.py migrate`.
5. Create a superuser with `python manage.py createsuperuser`.

## Local Development

1. Start Redis and PostgreSQL locally if you want to exercise the production stack.
2. Run the server with `python manage.py runserver`.
3. Open the developer portal at `/`.

## Environment Variables

The project reads the following runtime variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `DATABASE_SSLMODE`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CORS_ALLOWED_ORIGINS`
- `SECURE_SSL_REDIRECT`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `SECURE_HSTS_SECONDS`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `SECURE_HSTS_PRELOAD`
- `DEFAULT_FROM_EMAIL`
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `SSLCOMMERZ_STORE_ID`
- `SSLCOMMERZ_STORE_PASSWORD`
- `SSLCOMMERZ_SANDBOX`
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_TEST_MODE`

See `.env.example` for a complete template.

## Production Deployment

Deployment instructions for DigitalOcean App Platform are documented in [docs/deployment/DigitalOcean_App_Platform.md](docs/deployment/DigitalOcean_App_Platform.md).

## Screenshots

Screenshot placeholders live in [docs/screenshots/README.md](docs/screenshots/README.md).

- Developer portal placeholder: [docs/screenshots/developer-portal.png](docs/screenshots/developer-portal.png)
- Swagger UI placeholder: [docs/screenshots/swagger-ui.png](docs/screenshots/swagger-ui.png)
- ReDoc placeholder: [docs/screenshots/redoc.png](docs/screenshots/redoc.png)
- Health check placeholder: [docs/screenshots/health-check.png](docs/screenshots/health-check.png)

## API Documentation

- Swagger UI: `/docs/`
- ReDoc: `/redoc/`
- OpenAPI Schema: `/schema/`

## Live Demo

Placeholder: add the public App Platform URL here after deployment.

## Deployment Checklist

See [docs/deployment/Deployment_Readiness_Report.md](docs/deployment/Deployment_Readiness_Report.md) for the step-by-step DigitalOcean App Platform checklist.

## Readiness Score

Portfolio readiness is rated 88/100. The remaining items are documented in [docs/deployment/Deployment_Readiness_Report.md](docs/deployment/Deployment_Readiness_Report.md).

## License

MIT License.
