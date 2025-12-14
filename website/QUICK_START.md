# Quick Start Guide

Get up and running with the Primary Assistant application in minutes.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL (or use SQLite for development)
- pip (Python package installer)

## Quick Setup

### Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
cd /Users/nathanbowman/primary-assistant
python scripts/setup_environment.py
```

This will:
- Check Python version
- Create `.env` file from template
- Generate SECRET_KEY
- Create necessary directories
- Verify PostgreSQL installation

Then install dependencies:

```bash
cd website
pip install -r requirements.txt
```

### Option 2: Manual Setup

**1. Create environment file:**
```bash
cp /Users/nathanbowman/primary-assistant/.env.example /Users/nathanbowman/primary-assistant/.env
```

**2. Generate SECRET_KEY:**
```bash
python scripts/generate_secret_key.py
```

**3. Edit `.env` file:**
- Copy the generated SECRET_KEY
- Set POSTGRES_PASSWORD
- Adjust other settings as needed

**4. Install dependencies:**
```bash
cd website
pip install -r requirements.txt
```

## Running the Application

### Development Mode

**Public Portfolio Server (Port 8080):**
```bash
cd /Users/nathanbowman/primary-assistant/website
python app.py
```

**Private Workspace Server (Port 8081):**
```bash
cd /Users/nathanbowman/primary-assistant/website
python app-private.py
```

**Both Servers Simultaneously:**
```bash
cd /Users/nathanbowman/primary-assistant/website
./start-servers.sh
```

### Production Mode

**Using Gunicorn:**
```bash
cd /Users/nathanbowman/primary-assistant/website
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:8080 "website:create_app('production')"
```

## Database Setup

### PostgreSQL (Production)

**Install PostgreSQL:**
```bash
# macOS
brew install postgresql
brew services start postgresql
```

**Create database:**
```bash
psql postgres
CREATE DATABASE portfolio_db;
CREATE USER portfolio_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE portfolio_db TO portfolio_user;
\q
```

**Initialize migrations:**
```bash
cd /Users/nathanbowman/primary-assistant/website
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

### SQLite (Development Only)

**Set in `.env`:**
```bash
USE_SQLITE_DEV=true
```

**Initialize migrations:**
```bash
cd /Users/nathanbowman/primary-assistant/website
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

## Verify Installation

**Check Python version:**
```bash
python --version
# Should be 3.8 or higher
```

**Check dependencies:**
```bash
cd /Users/nathanbowman/primary-assistant/website
pip list | grep -i flask
# Should show Flask, Flask-SQLAlchemy, Flask-Login, etc.
```

**Test database connection:**
```bash
cd /Users/nathanbowman/primary-assistant/website
python -c "from website import create_app; app = create_app(); print('✓ App created successfully')"
```

## Common Tasks

### Generate New SECRET_KEY
```bash
python scripts/generate_secret_key.py
```

### Run Tests
```bash
cd /Users/nathanbowman/primary-assistant/website
pip install -r requirements-dev.txt
pytest
```

### View Logs
```bash
tail -f /Users/nathanbowman/primary-assistant/website/logs/app.log
```

### Create Database Migration
```bash
cd /Users/nathanbowman/primary-assistant/website
flask db migrate -m "Description of changes"
flask db upgrade
```

### Update Dependencies
```bash
cd /Users/nathanbowman/primary-assistant/website
pip install -r requirements.txt --upgrade
```

## Environment Variables

### Required
- `SECRET_KEY` - Generate with `python scripts/generate_secret_key.py`
- `POSTGRES_PASSWORD` - Your database password

### Common Settings
```bash
FLASK_ENV=development          # or production
FLASK_DEBUG=true               # or false
USE_SQLITE_DEV=true           # Use SQLite instead of PostgreSQL
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
```

## Troubleshooting

### "SECRET_KEY environment variable must be set"
1. Run: `python scripts/generate_secret_key.py`
2. Copy the generated key
3. Add to `.env`: `SECRET_KEY=<generated-key>`

### "POSTGRES_PASSWORD environment variable must be set"
1. Edit `.env` file
2. Set: `POSTGRES_PASSWORD=your-password`
3. Or use SQLite: `USE_SQLITE_DEV=true`

### Database connection errors
```bash
# Check PostgreSQL is running
brew services list

# Verify database exists
psql -l

# Test connection
psql -U portfolio_user -d portfolio_db
```

### Import errors
```bash
# Ensure you're in the right directory
cd /Users/nathanbowman/primary-assistant/website

# Reinstall dependencies
pip install -r requirements.txt
```

### Port already in use
```bash
# Check what's using the port
lsof -i :8080

# Kill the process (replace PID with actual process ID)
kill -9 <PID>
```

## Next Steps

After setup:

1. **Review configuration:** See `CONFIGURATION_GUIDE.md` for detailed settings
2. **Database models:** Phase 4 will add User and other models
3. **Authentication:** Phase 5 will add login/register functionality
4. **Docker:** Phase 7 will add containerization
5. **Deployment:** Phase 8 will cover production deployment

## Getting Help

- **Configuration Details:** `CONFIGURATION_GUIDE.md`
- **Architecture:** `ARCHITECTURE.md`
- **Deployment:** `DEPLOYMENT_GUIDE.md`
- **Contact:** nbowman189@gmail.com

## Files Overview

```
primary-assistant/
├── .env.example              # Environment template
├── .env                      # Your environment (create from template)
├── scripts/
│   ├── generate_secret_key.py    # Generate SECRET_KEY
│   └── setup_environment.py       # Automated setup
└── website/
    ├── requirements.txt           # Production dependencies
    ├── requirements-dev.txt       # Development dependencies
    ├── config.py                  # Configuration classes
    ├── __init__.py               # Application factory
    ├── app.py                    # Public server
    ├── app-private.py            # Private server
    ├── QUICK_START.md            # This file
    └── CONFIGURATION_GUIDE.md    # Detailed configuration
```

## Development Workflow

1. **Make changes** to code
2. **Test locally** with `python app.py`
3. **Run tests** with `pytest`
4. **Create migration** if models changed
5. **Commit changes** to git
6. **Deploy** to production

That's it! You're ready to develop. Happy coding!
