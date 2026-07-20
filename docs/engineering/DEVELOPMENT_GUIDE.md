# Development Guide

This guide walks through spinning up the Core Commerce Platform locally.

## Prerequisites
- Docker & docker-compose
- Python 3.10+
- virtualenv

## Local Setup

### 1. Environment
Copy the example environment variables:
```bash
cp .env.example .env
```

### 2. Infrastructure (Docker)
Start the backing services (PostgreSQL, Redis):
```bash
docker-compose up -d db redis
```

### 3. Python Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Database Initialization
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Running the Servers
You need to run the web server and the Celery worker concurrently.

**Terminal 1 (Web):**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 (Celery):**
```bash
celery -A config worker -l INFO
```

## Testing
Run the complete test suite:
```bash
python manage.py test
```
To run a specific domain's tests:
```bash
python manage.py test apps.analytics
```
