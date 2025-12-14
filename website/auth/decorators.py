"""
Authentication Decorators
=========================

Custom decorators for role-based access control and authentication utilities.
"""

from functools import wraps
from flask import flash, redirect, url_for, abort, current_app
from flask_login import current_user
from ..models.user import UserRole


def role_required(*roles):
    """
    Decorator to restrict access to users with specific roles.

    Usage:
        @role_required(UserRole.ADMIN, UserRole.COACH)
        def admin_or_coach_only():
            pass

    Args:
        *roles: Variable number of UserRole enum values

    Returns:
        Decorated function that checks user role before execution
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            # Check if user has one of the required roles
            if current_user.role not in roles:
                current_app.logger.warning(
                    f'Unauthorized access attempt by {current_user.username} '
                    f'to role-restricted resource. Required: {[r.value for r in roles]}, '
                    f'User has: {current_user.role.value}'
                )
                flash('You do not have permission to access this page.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to restrict access to admin users only.

    Convenience decorator for @role_required(UserRole.ADMIN).

    Usage:
        @admin_required
        def admin_only():
            pass

    Args:
        f: Function to decorate

    Returns:
        Decorated function that checks for admin role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_admin():
            current_app.logger.warning(
                f'Unauthorized admin access attempt by {current_user.username}'
            )
            flash('Admin access required.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def coach_required(f):
    """
    Decorator to restrict access to coach users only.

    Convenience decorator for @role_required(UserRole.COACH).

    Usage:
        @coach_required
        def coach_only():
            pass

    Args:
        f: Function to decorate

    Returns:
        Decorated function that checks for coach role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_coach() and not current_user.is_admin():
            current_app.logger.warning(
                f'Unauthorized coach access attempt by {current_user.username}'
            )
            flash('Coach access required.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def active_user_required(f):
    """
    Decorator to ensure user account is active.

    Checks if authenticated user's account is active before allowing access.

    Usage:
        @active_user_required
        def active_users_only():
            pass

    Args:
        f: Function to decorate

    Returns:
        Decorated function that checks for active account status
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_active:
            current_app.logger.warning(
                f'Inactive user access attempt: {current_user.username}'
            )
            flash('Your account is inactive. Please contact support.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def account_not_locked(f):
    """
    Decorator to ensure user account is not locked.

    Checks if authenticated user's account is locked before allowing access.

    Usage:
        @account_not_locked
        def unlocked_accounts_only():
            pass

    Args:
        f: Function to decorate

    Returns:
        Decorated function that checks for account lock status
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if current_user.is_locked():
            current_app.logger.warning(
                f'Locked account access attempt: {current_user.username}'
            )
            flash('Your account is locked. Please reset your password.', 'danger')
            return redirect(url_for('auth.reset_password_request'))

        return f(*args, **kwargs)
    return decorated_function


def anonymous_required(f):
    """
    Decorator to restrict access to anonymous users only.

    Redirects authenticated users to home page. Useful for login/register pages.

    Usage:
        @anonymous_required
        def login():
            pass

    Args:
        f: Function to decorate

    Returns:
        Decorated function that redirects authenticated users
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash('You are already logged in.', 'info')
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)
    return decorated_function


# Utility Functions

def check_account_status(user):
    """
    Check if user account is in good standing.

    Verifies:
    - Account is active
    - Account is not locked

    Args:
        user: User object to check

    Returns:
        Tuple of (bool, str): (is_valid, error_message)
    """
    if not user.is_active:
        return False, 'Account is inactive. Please contact support.'

    if user.is_locked():
        return False, 'Account is locked due to too many failed login attempts.'

    return True, None


def log_failed_login_attempt(username_or_email, ip_address=None):
    """
    Log failed login attempt for security monitoring.

    Args:
        username_or_email: Username or email used in attempt
        ip_address: IP address of the request (optional)
    """
    from flask import request

    if ip_address is None:
        ip_address = request.remote_addr

    current_app.logger.warning(
        f'Failed login attempt - Username/Email: {username_or_email}, '
        f'IP: {ip_address}, User-Agent: {request.user_agent.string}'
    )


def log_successful_login(user, ip_address=None):
    """
    Log successful login for security monitoring.

    Args:
        user: User object that logged in
        ip_address: IP address of the request (optional)
    """
    from flask import request

    if ip_address is None:
        ip_address = request.remote_addr

    current_app.logger.info(
        f'Successful login - User: {user.username}, '
        f'IP: {ip_address}, User-Agent: {request.user_agent.string}'
    )


def require_password_confirmation(password, user):
    """
    Verify password matches current user's password.

    Useful for sensitive operations requiring password confirmation.

    Args:
        password: Password to verify
        user: User object to check against

    Returns:
        bool: True if password matches, False otherwise
    """
    if not password:
        return False

    return user.check_password(password)
