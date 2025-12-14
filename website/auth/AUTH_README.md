# Authentication System Documentation

**Phase 2: Complete Authentication & Authorization System**

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Routes](#routes)
4. [Forms & Validation](#forms--validation)
5. [Security Features](#security-features)
6. [Role-Based Access Control](#role-based-access-control)
7. [Templates](#templates)
8. [Usage Examples](#usage-examples)
9. [Testing](#testing)
10. [Future Enhancements](#future-enhancements)

---

## Overview

This authentication system provides a complete, production-ready solution for user management in the Flask application. Built on Flask-Login, Flask-WTF, and SQLAlchemy, it includes:

- User registration with comprehensive validation
- Secure login with rate limiting
- Password reset via secure tokens
- Profile management
- Account locking after failed attempts
- Role-based access control (RBAC)
- CSRF protection on all forms

**Security First**: All features are designed with security best practices, including bcrypt password hashing, CSRF tokens, rate limiting, and secure session management.

---

## Architecture

### File Structure

```
website/auth/
├── __init__.py           # Blueprint initialization
├── routes.py             # All authentication routes
├── forms.py              # Flask-WTF forms with validation
├── decorators.py         # Custom access control decorators
└── AUTH_README.md        # This documentation

website/templates/auth/
├── login.html                    # Login page
├── register.html                 # User registration
├── reset_password_request.html   # Request password reset
├── reset_password.html           # Set new password
└── profile.html                  # User profile management
```

### Integration Points

1. **User Model** (`website/models/user.py`)
   - Flask-Login UserMixin integration
   - Bcrypt password hashing
   - Account locking mechanism
   - Role-based permissions

2. **Application Factory** (`website/__init__.py`)
   - Flask-Login initialization
   - Blueprint registration
   - CSRF protection
   - Rate limiting

3. **Configuration** (`website/config.py`)
   - Session security settings
   - CSRF configuration
   - Rate limiting rules
   - Bcrypt complexity

---

## Routes

All routes are prefixed with `/auth/`.

### Public Routes (No Authentication Required)

#### `GET/POST /auth/login`
**Purpose**: User login with rate limiting

**Rate Limit**: 5 attempts per minute per IP address

**Features**:
- Accepts username or email
- Remember me option (7-day cookie)
- Account lock checking
- Failed login attempt tracking
- Secure password verification

**Success**: Redirects to `next` parameter or home page
**Failure**: Flash message with error, account locked after 5 failed attempts

**Example**:
```python
# Access
http://localhost:8080/auth/login?next=/profile
```

---

#### `GET/POST /auth/register`
**Purpose**: Create new user account

**Features**:
- Username uniqueness validation
- Email format and uniqueness validation
- Strong password requirements
- Optional full name field
- Automatic bcrypt hashing

**Validation Rules**:
- Username: 3-80 chars, alphanumeric + underscore only
- Email: Valid format, unique in database
- Password: See [Password Strength](#password-strength-requirements)

**Success**: Redirects to login with success message
**Failure**: Form re-renders with validation errors

---

#### `GET/POST /auth/reset-password-request`
**Purpose**: Request password reset link

**Features**:
- Secure token generation (URLSafeTimedSerializer)
- Email privacy (doesn't reveal if email exists)
- Token expires after 1 hour

**Current Implementation**: Logs reset URL (email sending to be implemented)

**Future**: Will send email with reset link

---

#### `GET/POST /auth/reset-password/<token>`
**Purpose**: Set new password using reset token

**Features**:
- Token validation and expiry check (1 hour)
- Strong password requirements
- Automatically unlocks locked accounts
- Invalidates token after use

**Success**: Redirects to login
**Failure**: Redirects to reset request page with error

---

### Protected Routes (Authentication Required)

#### `GET /auth/logout`
**Purpose**: Log out current user

**Decorator**: `@login_required`

**Features**:
- Clears session
- Logs logout event
- Flash message confirmation

**Success**: Redirects to home page

---

#### `GET/POST /auth/profile`
**Purpose**: View and update user profile

**Decorator**: `@login_required`

**Features**:
- Update full name, email, bio
- Change password (requires current password)
- Account deletion option
- Profile photo placeholder

**Editable Fields**:
- Full Name (optional, max 200 chars)
- Email (unique, validated)
- Bio (optional, max 1000 chars)
- Password (optional, requires current password)

---

#### `POST /auth/account/delete`
**Purpose**: Permanently delete user account

**Decorator**: `@login_required`

**Features**:
- Requires password confirmation
- Cascading deletes (all user data)
- Immediate logout
- Irreversible action

**Security**: Requires password re-entry via modal confirmation

---

## Forms & Validation

All forms use Flask-WTF for CSRF protection and WTForms for validation.

### LoginForm
**Fields**:
- `username_or_email`: String (3-120 chars, required)
- `password`: Password (required)
- `remember_me`: Boolean (optional)

**Validation**: Basic required field checks

---

### RegistrationForm
**Fields**:
- `username`: String (3-80 chars, alphanumeric + underscore)
- `email`: Email (validated format, unique)
- `full_name`: String (optional, max 200 chars)
- `password`: Password (8+ chars, strength validated)
- `password_confirm`: Password (must match)

**Custom Validators**:
1. `validate_username()`: Checks database for existing username
2. `validate_email()`: Checks database for existing email
3. `validate_password()`: Enforces password strength requirements

---

### PasswordResetRequestForm
**Fields**:
- `email`: Email (required, validated format)

**Validation**: Email format only (doesn't check existence for security)

---

### PasswordResetForm
**Fields**:
- `password`: Password (8+ chars, strength validated)
- `password_confirm`: Password (must match)

**Custom Validators**:
1. `validate_password()`: Enforces password strength requirements

---

### ProfileUpdateForm
**Fields**:
- `full_name`: String (optional, max 200 chars)
- `email`: Email (validated, unique unless unchanged)
- `bio`: TextArea (optional, max 1000 chars)
- `current_password`: Password (required if changing password)
- `new_password`: Password (optional, strength validated)
- `new_password_confirm`: Password (must match new_password)

**Custom Validators**:
1. `validate_email()`: Checks uniqueness unless it's user's current email
2. `validate_new_password()`: Enforces strength and requires current password

---

### Password Strength Requirements

All passwords must meet these criteria:

1. **Minimum Length**: 8 characters
2. **Uppercase Letter**: At least one (A-Z)
3. **Lowercase Letter**: At least one (a-z)
4. **Digit**: At least one (0-9)
5. **Special Character**: At least one from: `!@#$%^&*(),.?":{}|<>_-+=[]\/;~` `

**Example Valid Password**: `MyP@ssw0rd!`

**Regex Validation**: All requirements checked via `re.search()` in form validators

---

## Security Features

### 1. Password Security

**Bcrypt Hashing**:
- Development: 12 rounds (balanced)
- Production: 13 rounds (higher security)
- Testing: 4 rounds (faster tests)

**Implementation**:
```python
# In User model
def set_password(self, password: str) -> None:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def check_password(self, password: str) -> bool:
    password_bytes = password.encode('utf-8')
    hash_bytes = self.password_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)
```

---

### 2. Account Locking

**Trigger**: 5 failed login attempts
**Duration**: 30 minutes
**Reset**: Successful login or password reset

**Implementation** (User model):
```python
def increment_failed_login(self, max_attempts: int = 5) -> None:
    self.failed_login_attempts += 1
    if self.failed_login_attempts >= max_attempts:
        self.lock_account()  # Locks for 30 minutes

def is_locked(self) -> bool:
    if self.locked_until is None:
        return False
    return datetime.now(timezone.utc) < self.locked_until
```

---

### 3. Rate Limiting

**Login Route**: 5 attempts per minute per IP

**Configuration** (`config.py`):
```python
RATELIMIT_ENABLED = True
RATELIMIT_STORAGE_URL = 'memory://'  # Or Redis for production
RATELIMIT_DEFAULT = '200 per day, 50 per hour'
```

**Route Implementation**:
```python
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    # ...
```

---

### 4. CSRF Protection

**Configuration**: Enabled globally via Flask-WTF

**Template Usage**:
```html
<form method="POST">
    {{ form.hidden_tag() }}  <!-- Includes CSRF token -->
    <!-- Form fields -->
</form>
```

**Settings** (`config.py`):
```python
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None  # Use session expiry instead
```

---

### 5. Session Security

**Configuration** (`config.py`):
```python
# Cookie Security
SESSION_COOKIE_HTTPONLY = True     # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'    # CSRF protection
SESSION_COOKIE_SECURE = True       # HTTPS only (production)

# Session Duration
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

# Remember Me
REMEMBER_COOKIE_DURATION = timedelta(days=7)
REMEMBER_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SAMESITE = 'Lax'
```

---

### 6. Password Reset Tokens

**Token Generation**:
```python
from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
token = serializer.dumps(user.email, salt='password-reset-salt')
```

**Token Validation**:
```python
try:
    email = serializer.loads(
        token,
        salt='password-reset-salt',
        max_age=3600  # 1 hour expiry
    )
except SignatureExpired:
    # Token expired
except BadSignature:
    # Invalid token
```

---

## Role-Based Access Control

### User Roles

Three roles defined in `UserRole` enum:

1. **USER** (`'user'`): Standard user access
2. **COACH** (`'coach'`): Coach-level access (user data + coaching features)
3. **ADMIN** (`'admin'`): Full system access

### Decorators

All decorators located in `auth/decorators.py`.

#### `@role_required(*roles)`
**Purpose**: Restrict access to specific roles

**Usage**:
```python
from website.auth.decorators import role_required
from website.models.user import UserRole

@app.route('/admin/dashboard')
@role_required(UserRole.ADMIN)
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/coaching/sessions')
@role_required(UserRole.COACH, UserRole.ADMIN)
def coaching_sessions():
    # Coaches and admins can access
    return render_template('coaching/sessions.html')
```

**Behavior**:
- Unauthenticated: Redirects to login
- Unauthorized: HTTP 403 Forbidden, flash message
- Logs unauthorized access attempts

---

#### `@admin_required`
**Purpose**: Shortcut for admin-only access

**Usage**:
```python
from website.auth.decorators import admin_required

@app.route('/admin/users')
@admin_required
def manage_users():
    return render_template('admin/users.html')
```

**Equivalent to**: `@role_required(UserRole.ADMIN)`

---

#### `@coach_required`
**Purpose**: Coach or admin access

**Usage**:
```python
from website.auth.decorators import coach_required

@app.route('/coaching/new-session')
@coach_required
def new_coaching_session():
    return render_template('coaching/new_session.html')
```

**Allows**: `UserRole.COACH` OR `UserRole.ADMIN`

---

#### `@active_user_required`
**Purpose**: Ensure user account is active

**Usage**:
```python
from website.auth.decorators import active_user_required

@app.route('/dashboard')
@active_user_required
def dashboard():
    return render_template('dashboard.html')
```

**Checks**: `user.is_active == True`

---

#### `@account_not_locked`
**Purpose**: Ensure account is not locked

**Usage**:
```python
from website.auth.decorators import account_not_locked

@app.route('/settings')
@account_not_locked
def settings():
    return render_template('settings.html')
```

**Checks**: `user.is_locked() == False`

---

#### `@anonymous_required`
**Purpose**: Restrict to logged-out users only

**Usage**:
```python
from website.auth.decorators import anonymous_required

@app.route('/auth/login')
@anonymous_required
def login():
    # Redirects authenticated users to home
    return render_template('auth/login.html')
```

**Behavior**: Redirects authenticated users with flash message

---

### Utility Functions

#### `check_account_status(user)`
**Returns**: `(bool, str)` - (is_valid, error_message)

```python
from website.auth.decorators import check_account_status

is_valid, error = check_account_status(user)
if not is_valid:
    flash(error, 'danger')
    return redirect(url_for('auth.login'))
```

---

#### `log_failed_login_attempt(username_or_email, ip_address=None)`
**Purpose**: Security logging for failed logins

```python
from website.auth.decorators import log_failed_login_attempt

log_failed_login_attempt('john_doe', request.remote_addr)
# Logs: "Failed login attempt - Username/Email: john_doe, IP: 127.0.0.1, ..."
```

---

#### `log_successful_login(user, ip_address=None)`
**Purpose**: Security logging for successful logins

```python
from website.auth.decorators import log_successful_login

log_successful_login(current_user, request.remote_addr)
# Logs: "Successful login - User: john_doe, IP: 127.0.0.1, ..."
```

---

#### `require_password_confirmation(password, user)`
**Returns**: `bool` - True if password matches

```python
from website.auth.decorators import require_password_confirmation

if require_password_confirmation(form.password.data, current_user):
    # Proceed with sensitive operation
    pass
else:
    flash('Invalid password', 'danger')
```

---

## Templates

All templates extend `base.html` and use consistent styling with the existing application design.

### Styling Philosophy

- **Modern & Clean**: Glassmorphic cards, subtle gradients
- **Responsive**: Mobile-first design with breakpoints
- **Accessible**: Proper labels, ARIA attributes, keyboard navigation
- **Consistent**: Matches "Vitruvian Developer" brand colors

### Common Elements

**Flash Messages**: All templates include flash message handling

```html
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        <div class="flash-messages">
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">
                    {{ message }}
                </div>
            {% endfor %}
        </div>
    {% endif %}
{% endwith %}
```

**Form Structure**:
```html
<form method="POST" action="{{ url_for('auth.login') }}" class="auth-form">
    {{ form.hidden_tag() }}  <!-- CSRF token -->

    <div class="form-group">
        {{ form.field.label(class="form-label") }}
        {{ form.field(class="form-control") }}
        {% if form.field.errors %}
            <div class="invalid-feedback">
                {% for error in form.field.errors %}
                    <span>{{ error }}</span>
                {% endfor %}
            </div>
        {% endif %}
    </div>
</form>
```

---

### Template Breakdown

#### `login.html`
- Centered auth card
- Username/email input with autocomplete
- Remember me checkbox
- Forgot password link
- Register link in footer

**Key Features**:
- Autofocus on first field
- Password toggle (can be added)
- Mobile responsive

---

#### `register.html`
- 5-field registration form
- Inline validation hints
- Password strength indicator (can be added)
- Terms of service checkbox (can be added)

**Key Features**:
- Real-time validation feedback
- Helper text for username/password rules
- Link to login for existing users

---

#### `reset_password_request.html`
- Simple email input
- Security-conscious messaging
- Link back to login

**Key Features**:
- Minimal design
- Privacy-preserving (doesn't reveal if email exists)

---

#### `reset_password.html`
- Two password fields (new + confirm)
- Token validated server-side
- Password strength requirements displayed

**Key Features**:
- Token expiry handling
- Clear error messages
- Direct link to login after success

---

#### `profile.html`
- User info section with avatar
- Profile update form
- Password change section
- Danger zone (account deletion)

**Key Features**:
- Modal confirmation for account deletion
- Role badge display
- Member since date
- Separate sections for profile vs password

---

## Usage Examples

### Basic Authentication Flow

```python
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from website.auth.decorators import admin_required

my_bp = Blueprint('my_routes', __name__)

# Public route
@my_bp.route('/public')
def public_page():
    return render_template('public.html')

# Protected route (any authenticated user)
@my_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# Admin-only route
@my_bp.route('/admin/settings')
@admin_required
def admin_settings():
    return render_template('admin/settings.html')
```

---

### Accessing Current User

```python
from flask_login import current_user

# Check if user is authenticated
if current_user.is_authenticated:
    username = current_user.username
    email = current_user.email

# Check user role
if current_user.is_admin():
    # Admin-specific logic
    pass

if current_user.is_coach():
    # Coach-specific logic
    pass

# Get user data as dict
user_data = current_user.to_dict(include_sensitive=True)
```

---

### Creating Users Programmatically

```python
from website.models.user import User, UserRole
from website.models import db

# Create regular user
user = User(
    username='john_doe',
    email='john@example.com',
    full_name='John Doe',
    role=UserRole.USER,
    is_active=True
)
user.set_password('SecureP@ssw0rd!')

db.session.add(user)
db.session.commit()

# Create admin user
admin = User(
    username='admin',
    email='admin@example.com',
    role=UserRole.ADMIN,
    is_active=True
)
admin.set_password('AdminP@ssw0rd!')

db.session.add(admin)
db.session.commit()
```

---

### Template Usage

```html
<!-- In any template -->
{% if current_user.is_authenticated %}
    <p>Welcome, {{ current_user.username }}!</p>
    <a href="{{ url_for('auth.profile') }}">Profile</a>
    <a href="{{ url_for('auth.logout') }}">Logout</a>
{% else %}
    <a href="{{ url_for('auth.login') }}">Login</a>
    <a href="{{ url_for('auth.register') }}">Register</a>
{% endif %}

<!-- Admin-only content -->
{% if current_user.is_authenticated and current_user.is_admin() %}
    <a href="{{ url_for('admin.dashboard') }}">Admin Dashboard</a>
{% endif %}
```

---

## Testing

### Manual Testing Checklist

#### Registration Flow
- [ ] Register with valid data → Success
- [ ] Register with existing username → Error
- [ ] Register with existing email → Error
- [ ] Register with weak password → Validation errors
- [ ] Register with mismatched passwords → Error
- [ ] Register with invalid email format → Error

#### Login Flow
- [ ] Login with correct credentials → Success
- [ ] Login with incorrect password → Error, failed attempts increment
- [ ] Login after 5 failed attempts → Account locked
- [ ] Login with locked account → Error message
- [ ] Login with inactive account → Error message
- [ ] Login with "Remember Me" → Session persists after browser close

#### Password Reset Flow
- [ ] Request reset with valid email → Token generated (check logs)
- [ ] Request reset with invalid email → Generic success message
- [ ] Use valid token → Password reset successful
- [ ] Use expired token (>1 hour) → Error
- [ ] Use invalid token → Error
- [ ] Reset unlocks locked account → Can login after reset

#### Profile Management
- [ ] Update full name → Success
- [ ] Update email to unique address → Success
- [ ] Update email to existing address → Error
- [ ] Update bio → Success
- [ ] Change password with correct current password → Success
- [ ] Change password with incorrect current password → Error
- [ ] Delete account with correct password → Account deleted
- [ ] Delete account with incorrect password → Error

#### Access Control
- [ ] Access protected route as anonymous → Redirect to login
- [ ] Access admin route as regular user → 403 Forbidden
- [ ] Access admin route as admin → Success
- [ ] Access coach route as coach → Success
- [ ] Access coach route as admin → Success

---

### Automated Testing

**Example Test File** (`tests/test_auth.py`):

```python
import pytest
from website.models.user import User, UserRole
from website import create_app, db

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_register_success(client):
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestP@ssw0rd!',
        'password_confirm': 'TestP@ssw0rd!',
        'csrf_token': 'test-token'  # Disable CSRF for testing
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Registration successful' in response.data

    user = User.query.filter_by(username='testuser').first()
    assert user is not None
    assert user.email == 'test@example.com'

def test_login_success(client):
    # Create user
    user = User(username='testuser', email='test@example.com')
    user.set_password('TestP@ssw0rd!')
    db.session.add(user)
    db.session.commit()

    # Login
    response = client.post('/auth/login', data={
        'username_or_email': 'testuser',
        'password': 'TestP@ssw0rd!',
        'csrf_token': 'test-token'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Welcome back' in response.data

def test_account_locking(client):
    # Create user
    user = User(username='testuser', email='test@example.com')
    user.set_password('TestP@ssw0rd!')
    db.session.add(user)
    db.session.commit()

    # Attempt 5 failed logins
    for i in range(5):
        client.post('/auth/login', data={
            'username_or_email': 'testuser',
            'password': 'WrongPassword',
            'csrf_token': 'test-token'
        })

    # Check account is locked
    user = User.query.filter_by(username='testuser').first()
    assert user.is_locked()

    # Attempt login with correct password
    response = client.post('/auth/login', data={
        'username_or_email': 'testuser',
        'password': 'TestP@ssw0rd!',
        'csrf_token': 'test-token'
    }, follow_redirects=True)

    assert b'Account is locked' in response.data
```

---

## Future Enhancements

### Phase 3: Email Integration
- [ ] Send password reset emails via SMTP
- [ ] Email verification on registration
- [ ] Account activation via email link
- [ ] Email notification for security events (password change, etc.)

**Configuration** (already in `config.py`, commented out):
```python
MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
```

---

### Phase 4: Advanced Features
- [ ] Two-factor authentication (TOTP)
- [ ] OAuth integration (Google, GitHub)
- [ ] Password history (prevent reuse)
- [ ] Session management (view/revoke active sessions)
- [ ] IP-based login restrictions
- [ ] User activity logs
- [ ] Account recovery questions

---

### Phase 5: UI/UX Improvements
- [ ] Real-time password strength indicator
- [ ] Show/hide password toggle
- [ ] Remember username on login page
- [ ] Profile photo upload
- [ ] Dark mode support
- [ ] Animated form transitions
- [ ] Toast notifications instead of flash messages

---

## Security Best Practices

### Deployment Checklist

Before deploying to production:

1. **Environment Variables**:
   - [ ] Set strong `SECRET_KEY` (generate with `scripts/generate_secret_key.py`)
   - [ ] Set `POSTGRES_PASSWORD`
   - [ ] Set `FLASK_ENV=production`

2. **HTTPS Configuration**:
   - [ ] Enable `SESSION_COOKIE_SECURE=True`
   - [ ] Enable `REMEMBER_COOKIE_SECURE=True`
   - [ ] Set up SSL certificates

3. **Rate Limiting**:
   - [ ] Configure Redis for rate limiting storage (multi-server)
   - [ ] Adjust rate limits based on traffic patterns

4. **Logging**:
   - [ ] Set up log rotation
   - [ ] Configure log monitoring/alerting
   - [ ] Review security logs regularly

5. **Database**:
   - [ ] Enable SSL connections to PostgreSQL
   - [ ] Set up database backups
   - [ ] Review user permissions

6. **Session Security**:
   - [ ] Set `SESSION_COOKIE_SAMESITE='Strict'` in production
   - [ ] Configure session timeout appropriately

---

## Troubleshooting

### Common Issues

**Issue**: CSRF token validation failed
**Solution**: Ensure `{{ form.hidden_tag() }}` is in all forms

**Issue**: Account locked but user can't reset password
**Solution**: Password reset automatically unlocks accounts

**Issue**: Rate limiting not working
**Solution**: Check `RATELIMIT_ENABLED=True` in config, verify storage backend

**Issue**: Users redirected to login after successful authentication
**Solution**: Check `is_active` flag on user, verify session cookie settings

**Issue**: Password strength validation not working
**Solution**: Verify regex patterns in `forms.py`, check form submission data

---

## Support & Maintenance

### Logging

All authentication events are logged:

```python
# Login attempts
current_app.logger.warning('Failed login attempt for user: username')
current_app.logger.info('Successful login for user: username')

# Account changes
current_app.logger.info('Password reset successful for user: username')
current_app.logger.info('Profile updated for user: username')
current_app.logger.info('Account deleted: username')

# Security events
current_app.logger.warning('Locked account access attempt: username')
current_app.logger.warning('Unauthorized access attempt by username')
```

### Monitoring Queries

```sql
-- Find locked accounts
SELECT username, email, locked_until, failed_login_attempts
FROM users
WHERE locked_until > NOW();

-- Find inactive users
SELECT username, email, last_login
FROM users
WHERE last_login < NOW() - INTERVAL '30 days';

-- Count users by role
SELECT role, COUNT(*) as count
FROM users
GROUP BY role;

-- Recent registrations
SELECT username, email, created_at
FROM users
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

---

## License & Credits

**Author**: Phase 2 Implementation - Complete Authentication System
**Date**: December 2024
**Framework**: Flask, Flask-Login, Flask-WTF
**Database**: PostgreSQL with SQLAlchemy ORM

---

**End of Documentation**

For questions or issues, review the code comments in `routes.py`, `forms.py`, and `decorators.py`.
