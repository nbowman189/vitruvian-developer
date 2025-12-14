# Primary Assistant

A multi-user personal development platform integrating health & fitness tracking, AI learning curriculum, and project management.

## 🎯 Project Vision

The **Vitruvian Developer** concept - synthesizing Code, AI, and Fitness disciplines into a unified personal growth system.

## 🏗️ Architecture

- **Backend**: Flask (Python 3.11) with PostgreSQL
- **Authentication**: Flask-Login with bcrypt password hashing
- **Deployment**: Docker containers (Nginx + Flask + PostgreSQL)
- **Frontend**: Vanilla JavaScript with modern CSS

## 🚀 Quick Start

### Development Environment

```bash
# 1. Clone repository
git clone https://github.com/nbowman189/primary-assistant.git
cd primary-assistant

# 2. Copy environment template
cp .env.example .env
# Edit .env with your configuration

# 3. Start development environment
docker-compose -f docker-compose.dev.yml up

# 4. Access application
open http://localhost:8000
```

### Production Deployment

```bash
# 1. Set production environment variables
# Generate SECRET_KEY: python scripts/generate_secret_key.py

# 2. Build and start containers
docker-compose up -d

# 3. Create initial admin user
docker-compose exec web flask create-admin

# 4. Access application
open http://localhost
```

## 📁 Project Structure

```
primary-assistant/
├── website/                    # Flask application
│   ├── models/                # SQLAlchemy database models
│   ├── api/                   # RESTful API endpoints
│   ├── auth/                  # Authentication system
│   ├── templates/             # Jinja2 templates
│   └── static/                # CSS, JavaScript, images
├── docker/                    # Docker configuration
├── migrations/                # Database migrations (Alembic)
├── scripts/                   # Utility scripts
├── AI_Development/docs/       # Shared AI learning content
├── Health_and_Fitness/docs/   # Shared fitness content
└── tests/                     # Test suite
```

## 🗄️ Database Schema

Multi-user database with strict data isolation:

- **Users & Authentication**: User accounts, sessions, access control
- **Health Tracking**: Metrics, measurements, progress photos
- **Workout Logging**: Sessions, exercises, performance data
- **Coaching**: Session notes, goals, action items
- **Nutrition**: Meal logging and tracking

Each user can only access their own data.

## 🔐 Security Features

- ✅ Bcrypt password hashing (cost factor 12)
- ✅ Session-based authentication with HTTP-only cookies
- ✅ CSRF protection on all state-changing requests
- ✅ Rate limiting (login attempts, API requests)
- ✅ Security headers (XSS, clickjacking, MIME sniffing)
- ✅ Row-level data isolation per user
- ✅ Docker security (non-root user, internal networks)

## 🛠️ Technology Stack

**Backend:**
- Flask 3.0+
- PostgreSQL 15
- SQLAlchemy ORM
- Flask-Login
- Flask-WTF (CSRF)
- Alembic (migrations)
- Gunicorn (WSGI server)

**Frontend:**
- Vanilla JavaScript
- Modern CSS with CSS variables
- Chart.js (data visualization)
- Markdown rendering

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- PostgreSQL (database)

## 📊 Key Features

### Public Portfolio
- Project showcases with case studies
- Blog with tag-based filtering
- Technical documentation
- Professional presentation

### Private Workspace (Authentication Required)
- **Health & Fitness Tracking**
  - Weight, body fat %, measurements
  - Workout logging with exercise details
  - Progress photos and graphs
  - Coaching session notes

- **Goal Management**
  - Set and track personal goals
  - Progress visualization
  - Achievement tracking

- **AI Development Curriculum**
  - Structured learning path
  - Progress tracking
  - Reference materials

## 🧪 Testing

```bash
# Run test suite
docker-compose exec web pytest

# Run with coverage
docker-compose exec web pytest --cov=website

# Run specific test
docker-compose exec web pytest tests/test_auth.py
```

## 📝 Database Migrations

```bash
# Create new migration
docker-compose exec web flask db migrate -m "Description"

# Apply migrations
docker-compose exec web flask db upgrade

# Rollback migration
docker-compose exec web flask db downgrade
```

## 🔧 Development Commands

```bash
# Create admin user
docker-compose exec web flask create-admin

# Migrate data from markdown files
docker-compose exec web python scripts/migrate_health_data.py --user-id 1

# Generate secret key
python scripts/generate_secret_key.py

# View logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx
```

## 🌐 Environment Variables

See `.env.example` for complete list. Required variables:

- `SECRET_KEY`: Flask secret (generate with `scripts/generate_secret_key.py`)
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user

## 📖 Documentation

- [Deployment Guide](docs/DEPLOYMENT.md)
- [API Documentation](docs/API.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Contributing Guide](CONTRIBUTING.md)

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

Private project - All rights reserved.

## 👤 Author

**Nathan Bowman**
- Email: nbowman189@gmail.com
- LinkedIn: [nathan-bowman](https://www.linkedin.com/in/nathan-bowman-b27484103/)
- GitHub: [@nbowman189](https://github.com/nbowman189)

---

🔥 Built with discipline, code, and continuous improvement.
