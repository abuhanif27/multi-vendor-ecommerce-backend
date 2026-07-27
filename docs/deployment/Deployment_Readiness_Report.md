# Deployment Readiness Report

## Score

Production readiness score: 88/100.

The score is not 100 because several items are still intentionally left as follow-up work for a public deployment.

## Required Before Production

- Replace placeholder environment values in `.env.example` with real deployment secrets in App Platform.
- Attach managed PostgreSQL and Redis in the live DO deployment.
- Provide a persistent strategy for user-uploaded media files if the app needs uploads.
- Add the final production domain to `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Replace the placeholder `example.com` domain in `app.yaml` with the real domain.

## Recommended

- Capture real screenshots after the app is deployed and replace the placeholder art in `docs/screenshots/`.
- Add a real Open Graph share image asset if you want richer social previews.
- Confirm `CORS_ALLOWED_ORIGINS` is restricted to the actual frontend domains.
- Set up an external email provider instead of console or SMTP placeholders.
- Enable automatic backups and monitoring on managed PostgreSQL and Redis.

## Nice To Have

- Add a DigitalOcean App Platform badge to the README.
- Add a status page or uptime badge to the developer portal.
- Add a dedicated changelog for future portfolio updates.
- Add automated smoke tests against the production URL after deploys.

## Why Not 100

- The deployment is technically ready, but some live-ops items still depend on the actual DigitalOcean environment and final domain values.
- Documentation screenshots are still placeholders until the production deployment exists.
- The app spec is complete enough to deploy, but the final resource names and domain entries need to be matched to the live DO account.

## Deployment Checklist

1. Push the repository to GitHub.
2. Create the DigitalOcean App from `app.yaml` or the GitHub repo.
3. Add the web service, Celery worker, and Celery beat components.
4. Attach managed PostgreSQL and Redis.
5. Set `DJANGO_SECRET_KEY` and all production environment variables.
6. Set `DJANGO_DEBUG=False`.
7. Configure `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.
8. Configure `DATABASE_URL`, `REDIS_URL`, `CORS_ALLOWED_ORIGINS`, and payment gateway keys.
9. Set the custom domain and wait for HTTPS issuance.
10. Run the build with `collectstatic` and verify the portal loads.
11. Confirm `/health/`, `/docs/`, `/redoc/`, `/schema/`, and `/admin/` all respond correctly.
12. Run `python manage.py check`, `python manage.py test`, `python manage.py spectacular --validate`, `python manage.py makemigrations --check`, and `python manage.py collectstatic --noinput` in the deployment pipeline.
13. Replace README screenshot placeholders with real captures from the live app.