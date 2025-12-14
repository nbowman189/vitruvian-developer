"""
Authentication Routes
=====================

Handles all authentication-related routes including login, logout, registration,
password reset, and profile management.
"""

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone
from urllib.parse import urlparse

from . import auth_bp
from .forms import (
    LoginForm,
    RegistrationForm,
    PasswordResetRequestForm,
    PasswordResetForm,
    ProfileUpdateForm
)
from ..models import db
from ..models.user import User, UserRole
from .. import limiter


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """
    User login route with rate limiting and account lock checking.

    Rate limited to 5 attempts per minute to prevent brute force attacks.
    Checks for account locks and validates credentials.
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        # Find user by username or email
        user = User.query.filter(
            (User.username == form.username_or_email.data) |
            (User.email == form.username_or_email.data)
        ).first()

        # Check if user exists
        if user is None:
            current_app.logger.warning(f'Failed login attempt for non-existent user: {form.username_or_email.data}')
            flash('Invalid username/email or password', 'danger')
            return render_template('auth/login.html', form=form)

        # Check if account is locked
        if user.is_locked():
            current_app.logger.warning(f'Login attempt for locked account: {user.username}')
            flash('Account is locked due to too many failed login attempts. Please try again later or reset your password.', 'danger')
            return render_template('auth/login.html', form=form)

        # Check if account is active
        if not user.is_active:
            current_app.logger.warning(f'Login attempt for inactive account: {user.username}')
            flash('Account is inactive. Please contact support.', 'danger')
            return render_template('auth/login.html', form=form)

        # Verify password
        if not user.check_password(form.password.data):
            # Increment failed login attempts
            user.increment_failed_login()
            db.session.commit()

            current_app.logger.warning(
                f'Failed login attempt for user {user.username}. '
                f'Failed attempts: {user.failed_login_attempts}'
            )

            flash('Invalid username/email or password', 'danger')
            return render_template('auth/login.html', form=form)

        # Successful login
        user.reset_failed_login()
        user.update_last_login()
        db.session.commit()

        # Log user in
        login_user(user, remember=form.remember_me.data)

        current_app.logger.info(f'Successful login for user: {user.username}')
        flash(f'Welcome back, {user.username}!', 'success')

        # Redirect to next page or home
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')

        return redirect(next_page)

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout route.

    Requires authentication. Logs out current user and redirects to home.
    """
    username = current_user.username
    logout_user()
    current_app.logger.info(f'User logged out: {username}')
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.

    Creates new user account with validation and password hashing.
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data if form.full_name.data else None,
            role=UserRole.USER,
            is_active=True
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()

            current_app.logger.info(f'New user registered: {user.username}')
            flash('Registration successful! You can now log in.', 'success')

            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error registering user: {e}')
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Password reset request route.

    Allows users to request a password reset via email.
    Generates secure token for password reset.
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = PasswordResetRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            # Generate password reset token
            from itsdangerous import URLSafeTimedSerializer
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = serializer.dumps(user.email, salt='password-reset-salt')

            # TODO: Send email with reset link
            # For now, just log the token (in production, send via email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            current_app.logger.info(f'Password reset requested for {user.email}. Reset URL: {reset_url}')

            # Always show success message (security: don't reveal if email exists)
            flash('If an account exists with that email, a password reset link has been sent.', 'info')
        else:
            # Don't reveal that email doesn't exist (security)
            flash('If an account exists with that email, a password reset link has been sent.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password_request.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Password reset confirmation route.

    Validates token and allows user to set new password.
    Token expires after 1 hour for security.
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # Verify token
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)  # 1 hour expiry
    except SignatureExpired:
        flash('The password reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.reset_password_request'))
    except BadSignature:
        flash('Invalid password reset link.', 'danger')
        return redirect(url_for('auth.reset_password_request'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid password reset link.', 'danger')
        return redirect(url_for('auth.reset_password_request'))

    form = PasswordResetForm()

    if form.validate_on_submit():
        # Set new password
        user.set_password(form.password.data)

        # Unlock account if locked
        if user.is_locked():
            user.unlock_account()

        db.session.commit()

        current_app.logger.info(f'Password reset successful for user: {user.username}')
        flash('Your password has been reset successfully. You can now log in.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    User profile management route.

    Allows authenticated users to view and update their profile information.
    """
    form = ProfileUpdateForm(obj=current_user)

    if form.validate_on_submit():
        # Update user profile
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data

        # Update password if provided
        if form.new_password.data:
            # Verify current password
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('auth/profile.html', form=form)

            current_user.set_password(form.new_password.data)
            current_app.logger.info(f'Password changed for user: {current_user.username}')

        try:
            db.session.commit()
            current_app.logger.info(f'Profile updated for user: {current_user.username}')
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating profile: {e}')
            flash('An error occurred while updating your profile.', 'danger')

    return render_template('auth/profile.html', form=form)


@auth_bp.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    """
    Account deletion route.

    Allows users to permanently delete their account.
    Requires password confirmation.
    """
    password = request.form.get('password')

    if not password or not current_user.check_password(password):
        flash('Invalid password. Account deletion failed.', 'danger')
        return redirect(url_for('auth.profile'))

    username = current_user.username

    try:
        db.session.delete(current_user)
        db.session.commit()
        logout_user()

        current_app.logger.info(f'Account deleted: {username}')
        flash('Your account has been deleted successfully.', 'info')
        return redirect(url_for('main.index'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting account: {e}')
        flash('An error occurred while deleting your account.', 'danger')
        return redirect(url_for('auth.profile'))
