# Authentication System - Quick Start Guide

**Get your authentication system up and running in 5 minutes!**

---

## Prerequisites

Before starting, ensure you have:
- ✅ PostgreSQL installed and running
- ✅ Python 3.8+ installed
- ✅ All dependencies from Phase 1 installed

---

## Step 1: Install Dependencies (if not already installed)

The authentication system requires these Python packages:

```bash
# Activate your virtual environment first
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install required packages
pip install flask flask-sqlalchemy flask-migrate flask-login flask-wtf wtforms bcrypt flask-limiter flask-cors flask-caching email-validator
```

---

## Step 2: Set Environment Variables

Create a `.env` file in your project root or export these variables:

```bash
# Required
export SECRET_KEY="your-secret-key-here-generate-with-openssl"
export POSTGRES_PASSWORD="your-postgres-password"

# Optional (with defaults)
export POSTGRES_USER="portfolio_user"
export POSTGRES_DB="portfolio_db"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export FLASK_ENV="development"
```

**Generate a secure SECRET_KEY**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 3: Run Database Migrations

The User model already exists from Phase 1, so just ensure it's up to date:

```bash
cd website

# Initialize migrations (if not already done)
flask db init

# Create migration for User model (if needed)
flask db migrate -m "Add authentication models"

# Apply migrations
flask db upgrade
```

---

## Step 4: Create Your First User (Optional)

You can create users through the web interface at `/auth/register`, or create an admin user via Python:

```python
# Start Python shell in your website directory
python

# Create admin user
from website import create_app, db
from website.models.user import User, UserRole

app = create_app('development')
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        full_name='Admin User',
        role=UserRole.ADMIN,
        is_active=True
    )
    admin.set_password('AdminP@ssw0rd!')

    db.session.add(admin)
    db.session.commit()
    print(f"Admin user created: {admin.username}")
```

---

## Step 5: Start the Application

```bash
# From the project root directory
cd /Users/nathanbowman/primary-assistant/website

# Run the Flask application
python app.py  # Or however you normally start your app
```

Your application should now be running on `http://localhost:8080`

---

## Step 6: Test the Authentication System

### Test Registration
1. Visit: `http://localhost:8080/auth/register`
2. Fill out the form with:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `TestP@ssw0rd!` (must meet strength requirements)
3. Click "Register"
4. Should redirect to login page with success message

### Test Login
1. Visit: `http://localhost:8080/auth/login`
2. Enter credentials from registration
3. Click "Login"
4. Should redirect to home page with welcome message

### Test Profile
1. While logged in, visit: `http://localhost:8080/auth/profile`
2. Update your profile information
3. Test password change
4. Should see success message

### Test Password Reset
1. Visit: `http://localhost:8080/auth/reset-password-request`
2. Enter your email
3. Check application logs for reset URL (email not yet configured)
4. Copy token from URL and visit the reset page
5. Set new password

### Test Account Locking
1. Logout
2. Attempt login with wrong password 5 times
3. Account should be locked with message
4. Try password reset to unlock

---

## Available Routes

All authentication routes are prefixed with `/auth/`:

| Route | Method | Description | Auth Required |
|-------|--------|-------------|---------------|
| `/auth/login` | GET, POST | User login | No |
| `/auth/logout` | GET | User logout | Yes |
| `/auth/register` | GET, POST | User registration | No |
| `/auth/reset-password-request` | GET, POST | Request password reset | No |
| `/auth/reset-password/<token>` | GET, POST | Confirm password reset | No |
| `/auth/profile` | GET, POST | View/edit profile | Yes |
| `/auth/account/delete` | POST | Delete account | Yes |

---

## Protecting Your Routes

### Basic Protection (Any Authenticated User)

```python
from flask import Blueprint, render_template
from flask_login import login_required

my_bp = Blueprint('my_routes', __name__)

@my_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
```

### Admin-Only Protection

```python
from website.auth.decorators import admin_required

@my_bp.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin.html')
```

### Role-Based Protection

```python
from website.auth.decorators import role_required
from website.models.user import UserRole

@my_bp.route('/coaching')
@role_required(UserRole.COACH, UserRole.ADMIN)
def coaching_area():
    return render_template('coaching.html')
```

---

## Accessing Current User in Templates

```html
{% if current_user.is_authenticated %}
    <p>Welcome, {{ current_user.username }}!</p>
    <p>Email: {{ current_user.email }}</p>

    {% if current_user.is_admin() %}
        <a href="{{ url_for('admin.dashboard') }}">Admin Dashboard</a>
    {% endif %}

    <a href="{{ url_for('auth.profile') }}">My Profile</a>
    <a href="{{ url_for('auth.logout') }}">Logout</a>
{% else %}
    <a href="{{ url_for('auth.login') }}">Login</a>
    <a href="{{ url_for('auth.register') }}">Register</a>
{% endif %}
```

---

## Accessing Current User in Python

```python
from flask_login import current_user

# Check authentication
if current_user.is_authenticated:
    print(f"User: {current_user.username}")

# Check roles
if current_user.is_admin():
    # Admin logic
    pass

if current_user.is_coach():
    # Coach logic
    pass

# Get user data
user_dict = current_user.to_dict(include_sensitive=True)
```

---

## Common Issues & Solutions

### Issue: "No module named 'flask_login'"
**Solution**: Install dependencies
```bash
pip install flask-login flask-wtf wtforms bcrypt
```

### Issue: "SECRET_KEY environment variable must be set"
**Solution**: Set SECRET_KEY environment variable
```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

### Issue: "POSTGRES_PASSWORD environment variable must be set"
**Solution**: Set your PostgreSQL password
```bash
export POSTGRES_PASSWORD="your-postgres-password"
```

### Issue: "Module 'website.auth' has no attribute 'auth_bp'"
**Solution**: Check that `website/__init__.py` registers the blueprint correctly

### Issue: Rate limiting not working
**Solution**: Check `RATELIMIT_ENABLED=True` in config.py, or disable for development

### Issue: CSRF token validation failed
**Solution**: Ensure `{{ form.hidden_tag() }}` is in all forms

---

## Security Checklist for Production

Before deploying to production:

- [ ] Set strong `SECRET_KEY` (minimum 32 bytes)
- [ ] Set `FLASK_ENV=production`
- [ ] Enable `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Enable `REMEMBER_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Configure Redis for rate limiting (multi-server)
- [ ] Set up SSL/TLS certificates
- [ ] Configure email for password resets
- [ ] Set up log monitoring
- [ ] Configure database backups
- [ ] Review and adjust rate limits

---

## Next Steps

Once your authentication system is working:

1. **Customize Templates**: Modify templates to match your brand
2. **Add Email**: Configure Flask-Mail for password reset emails
3. **Create Admin Panel**: Build user management interface
4. **Add Profile Photos**: Implement file upload for avatars
5. **Enable 2FA**: Add two-factor authentication
6. **OAuth Integration**: Add social login (Google, GitHub)

---

## Getting Help

### Documentation
- **Full Documentation**: See `AUTH_README.md` for complete details
- **Implementation Summary**: See `IMPLEMENTATION_SUMMARY.md` for overview
- **Code Comments**: All Python files include comprehensive docstrings

### Verification
Run the verification script to check installation:
```bash
python website/auth/verify_installation.py
```

### Logging
All authentication events are logged. Check application logs for:
- Login attempts (successful and failed)
- Account locking events
- Password resets
- Unauthorized access attempts

---

## Example: Complete Setup Session

Here's a complete example of setting up from scratch:

```bash
# 1. Navigate to project
cd /Users/nathanbowman/primary-assistant/website

# 2. Activate virtual environment
source ../venv/bin/activate

# 3. Set environment variables
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export POSTGRES_PASSWORD="your_password_here"
export FLASK_ENV="development"

# 4. Run migrations
flask db upgrade

# 5. Create admin user (optional)
python -c "
from website import create_app, db
from website.models.user import User, UserRole

app = create_app('development')
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        role=UserRole.ADMIN,
        is_active=True
    )
    admin.set_password('AdminP@ssw0rd!')
    db.session.add(admin)
    db.session.commit()
    print('Admin created')
"

# 6. Start application
python app.py
```

Then visit:
- Registration: `http://localhost:8080/auth/register`
- Login: `http://localhost:8080/auth/login`
- Profile: `http://localhost:8080/auth/profile`

---

**You're all set! Your authentication system is ready to use.**

For detailed documentation, see `AUTH_README.md`.
