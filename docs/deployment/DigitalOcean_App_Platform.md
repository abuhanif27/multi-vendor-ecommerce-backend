# DigitalOcean App Platform Deployment

This guide describes a production deployment for the Django API on DigitalOcean App Platform.

## 1. Create The App

1. Push the repository to GitHub.
2. In DigitalOcean, create a new App from the GitHub repository.
3. Use the Django service as the web component.
4. Set the build command to:

```bash
python manage.py collectstatic --noinput
```

5. Set the run command to:

```bash
gunicorn config.wsgi:application
```

The repository also includes a `Procfile` with the same web command for portability.

If you run Celery on App Platform, add a separate worker component using:

```bash
celery -A config worker -l info
```

If you need scheduled tasks, add a beat component using:

```bash
celery -A config beat -l info
```

## 2. Environment Variables

Set the following variables in the App Platform console:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `REDIS_URL`
- `CORS_ALLOWED_ORIGINS`
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_SECONDS=31536000`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- `SECURE_HSTS_PRELOAD=True`
- `DEFAULT_FROM_EMAIL`
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS=True`
- `PROJECT_REPOSITORY_URL`
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_TEST_MODE=False`
- `SSLCOMMERZ_STORE_ID`
- `SSLCOMMERZ_STORE_PASSWORD`
- `SSLCOMMERZ_SANDBOX=False`

App Platform can inject `DATABASE_URL` automatically when a managed PostgreSQL database is attached.

## 3. Managed PostgreSQL

Attach a managed PostgreSQL database from the App Platform resource panel.

Use the generated `DATABASE_URL` instead of hardcoding database credentials. The settings layer reads `DATABASE_URL` and enables persistent connections through `CONN_MAX_AGE`.

Recommended production options:

- Enable automatic backups.
- Use the smallest environment that matches production traffic.
- Enable monitoring on the database resource.

## 4. Managed Redis

Attach a managed Redis database and expose its connection string as `REDIS_URL`.

Redis is used for:

- Celery broker traffic
- Celery result backend
- Django cache storage

If Redis is not attached, the application falls back to local in-memory caching, but production deployments should use Redis.

## 5. Static And Media Files

Static assets are served through WhiteNoise and collected into `staticfiles/` during the build step.

Media uploads are configured through `MEDIA_ROOT` and `MEDIA_URL`, but App Platform storage is ephemeral unless you attach persistent storage or move uploads to object storage such as DigitalOcean Spaces.

Recommended production approach:

- Keep static assets on WhiteNoise.
- Store uploads on persistent storage or Spaces.

## 6. Custom Domain And HTTPS

1. Add your custom domain in App Platform.
2. Update DNS records as instructed by DigitalOcean.
3. Wait for certificate issuance.
4. Verify the application is served over HTTPS.

The settings enforce secure cookies and HSTS once the production variables are enabled.

## 7. Deployment Flow

1. Push changes to the default branch.
2. App Platform rebuilds the container automatically.
3. Static files are collected during build.
4. Gunicorn starts the WSGI application.
5. Confirm the root portal, health check, and Swagger pages load successfully.

## 8. Rollback

If a deployment fails:

1. Use the App Platform deployment history to redeploy the previous release.
2. Inspect the build logs and runtime logs.
3. Confirm environment variables and attached resources match the prior working revision.

## 9. Troubleshooting

### `DEBUG=False` startup errors

Ensure the following variables are present:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

### Static files not loading

Verify `python manage.py collectstatic --noinput` completed during build and that WhiteNoise middleware is enabled.

### Database connection failures

Confirm `DATABASE_URL` is set by the managed PostgreSQL attachment and that SSL mode matches the provider defaults.

### Redis or Celery failures

Confirm `REDIS_URL` is attached and reachable, then review worker logs for task serialization or connection errors.

### Payment gateway issues

Check the Stripe and SSLCommerz environment variables, especially the webhook secrets and sandbox flags.
