# Configuration & Dependencies Guide

This guide explains the configuration and dependency management system for the Primary Assistant Flask application.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Security](#security)
- [Development vs Production](#development-vs-production)

## Overview

The application uses:

- **Flask Application Factory Pattern** for clean initialization
- **Environment-based Configuration** for different deployment scenarios
- **SQLAlchemy** for database ORM
- **Flask-Login** for authentication
- **PostgreSQL** for production database (SQLite option for development)
- **Comprehensive Security** with CSRF protection, rate limiting, and secure sessions

## Installation

### 1. Install Python Dependencies

**Production:**
```bash
cd /Users/nathanbowman/primary-assistant/website
pip install -r requirements.txt
```

**Development (includes testing tools):**
```bash
pip install -r requirements-dev.txt
```

### 2. Environment Configuration

**Copy the environment template:**
```bash
cp /Users/nathanbowman/primary-assistant/.env.example /Users/nathanbowman/primary-assistant/.env
```

**Generate a secure SECRET_KEY:**
```bash
python /Users/nathanbowman/primary-assistant/scripts/generate_secret_key.py
```

**Edit `.env` file** and update the following required values:
- `SECRET_KEY` - Use the generated key from above
- `POSTGRES_PASSWORD` - Set a strong database password

### 3. Database Setup

**For PostgreSQL (Recommended for Production):**

```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database and user
psql postgres
CREATE DATABASE portfolio_db;
CREATE USER portfolio_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE portfolio_db TO portfolio_user;
\q
```

**For SQLite (Development Only):**

Set in `.env`:
```
USE_SQLITE_DEV=true
```

## Configuration

### Configuration Files

The application uses a modular configuration system:

**`website/config.py`** - Main configuration file with three environments:

1. **BaseConfig** - Shared settings for all environments
   - Security settings (SECRET_KEY, CSRF, sessions)
   - Database configuration
   - Rate limiting
   - File uploads
   - Logging

2. **DevelopmentConfig** - Local development
   - DEBUG mode enabled
   - Less strict security for local testing
   - Detailed logging
   - Optional SQLite database
   - Rate limiting disabled

3. **ProductionConfig** - Production deployment
   - DEBUG mode disabled
   - Strict security (HTTPS required)
   - Enhanced bcrypt rounds
   - Production-level rate limiting
   - Warning-level logging

4. **TestingConfig** - Unit testing
   - In-memory SQLite database
   - CSRF disabled for testing
   - Fast bcrypt (for speed)
   - No caching

### Application Factory

**`website/__init__.py`** - Application factory with:

- Extension initialization (SQLAlchemy, Flask-Login, CSRF, etc.)
- Blueprint registration
- Error handlers
- Security headers
- Logging configuration

**Usage:**
```python
from website import create_app

# Create app with specific config
app = create_app('production')

# Or use environment variable FLASK_ENV
app = create_app()  # Uses FLASK_ENV
```

## Environment Variables

### Required Variables

These MUST be set in `.env`:

- `SECRET_KEY` - Flask secret key for sessions
- `POSTGRES_PASSWORD` - Database password

### Core Settings

```bash
FLASK_ENV=development          # development, production, testing
FLASK_DEBUG=true               # Enable debug mode
APP_NAME=Primary Assistant     # Application name
ADMIN_EMAIL=your@email.com     # Admin contact
```

### Database

```bash
POSTGRES_USER=portfolio_user
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=portfolio_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
USE_SQLITE_DEV=false          # Use SQLite in dev
```

### Security

```bash
# Rate limiting
RATELIMIT_DEFAULT=200 per day, 50 per hour
RATELIMIT_STORAGE_URL=memory://

# File uploads
MAX_UPLOAD_SIZE_MB=16
```

### Logging

```bash
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/app.log
LOG_MAX_BYTES=10485760        # 10MB
LOG_BACKUP_COUNT=5
```

## Database Setup

### Initialize Database Migrations

```bash
cd /Users/nathanbowman/primary-assistant/website

# Initialize migrations (first time only)
flask db init

# Create initial migration
flask db migrate -m "Initial database schema"

# Apply migration
flask db upgrade
```

### Common Migration Commands

```bash
# Create new migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade

# Show migration history
flask db history
```

## Security

### Security Features

The application implements comprehensive security:

1. **CSRF Protection** - Enabled on all forms
2. **Secure Sessions** - HTTPOnly, SameSite cookies
3. **Password Hashing** - Bcrypt with configurable rounds
4. **Rate Limiting** - Prevents abuse and brute force
5. **Security Headers** - XSS, clickjacking, MIME sniffing protection
6. **HTTPS Enforcement** - Required in production
7. **Input Validation** - Flask-WTF forms with validation

### SECRET_KEY Generation

**CRITICAL:** Never use a hardcoded SECRET_KEY. Always generate:

```bash
python scripts/generate_secret_key.py
```

This creates a cryptographically secure random key. Each environment should have its own unique SECRET_KEY.

### Password Requirements

- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, and special characters
- Hashed with bcrypt (12 rounds in production, 13 in production config)

## Development vs Production

### Development Environment

**Setup:**
```bash
export FLASK_ENV=development
export FLASK_DEBUG=true
USE_SQLITE_DEV=true  # Optional for SQLite
```

**Features:**
- Debug mode enabled
- Auto-reload templates
- Detailed logging
- Rate limiting disabled
- Less strict security (HTTP allowed)

**Running:**
```bash
cd /Users/nathanbowman/primary-assistant/website
python app.py  # Or app-private.py
```

### Production Environment

**Setup:**
```bash
export FLASK_ENV=production
export FLASK_DEBUG=false
```

**Features:**
- Debug mode disabled
- HTTPS required
- Strict security headers
- Enhanced rate limiting
- Production-level logging (WARNING/ERROR)
- Stronger bcrypt hashing

**Running with Gunicorn:**
```bash
cd /Users/nathanbowman/primary-assistant/website
gunicorn -w 4 -b 0.0.0.0:8080 "website:create_app('production')"
```

## Testing

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=website --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Testing Configuration

Tests automatically use `TestingConfig`:
- In-memory SQLite database
- CSRF disabled
- Fast bcrypt (4 rounds)
- No rate limiting

## Troubleshooting

### Common Issues

**"SECRET_KEY environment variable must be set"**
- Generate key: `python scripts/generate_secret_key.py`
- Add to `.env` file

**"POSTGRES_PASSWORD environment variable must be set"**
- Set password in `.env` file
- Or use SQLite for development: `USE_SQLITE_DEV=true`

**Database connection errors**
- Verify PostgreSQL is running: `brew services list`
- Check credentials in `.env`
- Ensure database exists: `psql -l`

**Import errors**
- Ensure virtual environment is activated
- Install dependencies: `pip install -r requirements.txt`

### Logs

Check application logs for errors:
```bash
tail -f /Users/nathanbowman/primary-assistant/website/logs/app.log
```

## Dependencies Reference

### Core Dependencies

- **Flask** - Web framework
- **Flask-SQLAlchemy** - Database ORM
- **Flask-Migrate** - Database migrations
- **Flask-Login** - User authentication
- **Flask-WTF** - Form handling and CSRF
- **psycopg2-binary** - PostgreSQL adapter
- **bcrypt** - Password hashing
- **Flask-Limiter** - Rate limiting
- **gunicorn** - Production WSGI server

### Development Dependencies

- **pytest** - Testing framework
- **black** - Code formatting
- **flake8** - Code linting
- **ipython** - Enhanced Python shell
- **Flask-DebugToolbar** - Debug toolbar

See `requirements.txt` and `requirements-dev.txt` for complete lists with version constraints.

## Next Steps

After configuration:

1. **Phase 4**: Database models (User, etc.)
2. **Phase 5**: Authentication routes (login, register, logout)
3. **Phase 6**: Protected routes and permissions
4. **Phase 7**: Docker containerization
5. **Phase 8**: Deployment

## Support

For issues or questions:
- Check logs: `logs/app.log`
- Review configuration: `website/config.py`
- Environment variables: `.env` file
- Contact: nbowman189@gmail.com
