"""
Authentication Forms
====================

Flask-WTF forms for user authentication, registration, and profile management.
Includes comprehensive validation for security.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError,
    Optional,
    Regexp
)
import re
from ..models.user import User


class LoginForm(FlaskForm):
    """
    User login form.

    Accepts either username or email for flexibility.
    Includes remember me option for persistent sessions.
    """
    username_or_email = StringField(
        'Username or Email',
        validators=[
            DataRequired(message='Username or email is required'),
            Length(min=3, max=120, message='Must be between 3 and 120 characters')
        ],
        render_kw={'placeholder': 'Enter your username or email', 'autofocus': True}
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required')
        ],
        render_kw={'placeholder': 'Enter your password'}
    )

    remember_me = BooleanField('Remember Me')

    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    """
    User registration form.

    Validates username uniqueness, email format, and password strength.
    """
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required'),
            Length(min=3, max=80, message='Username must be between 3 and 80 characters'),
            Regexp(
                r'^[a-zA-Z0-9_]+$',
                message='Username can only contain letters, numbers, and underscores'
            )
        ],
        render_kw={'placeholder': 'Choose a username', 'autofocus': True}
    )

    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address'),
            Length(max=120, message='Email must be less than 120 characters')
        ],
        render_kw={'placeholder': 'Enter your email address'}
    )

    full_name = StringField(
        'Full Name (Optional)',
        validators=[
            Optional(),
            Length(max=200, message='Full name must be less than 200 characters')
        ],
        render_kw={'placeholder': 'Enter your full name (optional)'}
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=8, message='Password must be at least 8 characters long')
        ],
        render_kw={'placeholder': 'Create a strong password'}
    )

    password_confirm = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={'placeholder': 'Re-enter your password'}
    )

    submit = SubmitField('Register')

    def validate_username(self, username):
        """
        Validate username is unique.

        Args:
            username: Username field

        Raises:
            ValidationError: If username already exists
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        """
        Validate email is unique.

        Args:
            email: Email field

        Raises:
            ValidationError: If email already exists
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or login.')

    def validate_password(self, password):
        """
        Validate password strength.

        Password must contain:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Args:
            password: Password field

        Raises:
            ValidationError: If password doesn't meet strength requirements
        """
        pwd = password.data

        if len(pwd) < 8:
            raise ValidationError('Password must be at least 8 characters long.')

        if not re.search(r'[A-Z]', pwd):
            raise ValidationError('Password must contain at least one uppercase letter.')

        if not re.search(r'[a-z]', pwd):
            raise ValidationError('Password must contain at least one lowercase letter.')

        if not re.search(r'\d', pwd):
            raise ValidationError('Password must contain at least one digit.')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', pwd):
            raise ValidationError('Password must contain at least one special character.')


class PasswordResetRequestForm(FlaskForm):
    """
    Password reset request form.

    Requests password reset link via email.
    """
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ],
        render_kw={'placeholder': 'Enter your email address', 'autofocus': True}
    )

    submit = SubmitField('Request Password Reset')


class PasswordResetForm(FlaskForm):
    """
    Password reset form.

    Allows user to set new password after email verification.
    """
    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=8, message='Password must be at least 8 characters long')
        ],
        render_kw={'placeholder': 'Enter your new password', 'autofocus': True}
    )

    password_confirm = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={'placeholder': 'Re-enter your new password'}
    )

    submit = SubmitField('Reset Password')

    def validate_password(self, password):
        """
        Validate password strength.

        Password must contain:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Args:
            password: Password field

        Raises:
            ValidationError: If password doesn't meet strength requirements
        """
        pwd = password.data

        if len(pwd) < 8:
            raise ValidationError('Password must be at least 8 characters long.')

        if not re.search(r'[A-Z]', pwd):
            raise ValidationError('Password must contain at least one uppercase letter.')

        if not re.search(r'[a-z]', pwd):
            raise ValidationError('Password must contain at least one lowercase letter.')

        if not re.search(r'\d', pwd):
            raise ValidationError('Password must contain at least one digit.')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', pwd):
            raise ValidationError('Password must contain at least one special character.')


class ProfileUpdateForm(FlaskForm):
    """
    Profile update form.

    Allows users to update their profile information and password.
    """
    full_name = StringField(
        'Full Name',
        validators=[
            Optional(),
            Length(max=200, message='Full name must be less than 200 characters')
        ],
        render_kw={'placeholder': 'Enter your full name'}
    )

    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address'),
            Length(max=120, message='Email must be less than 120 characters')
        ],
        render_kw={'placeholder': 'Enter your email address'}
    )

    bio = TextAreaField(
        'Bio',
        validators=[
            Optional(),
            Length(max=1000, message='Bio must be less than 1000 characters')
        ],
        render_kw={
            'placeholder': 'Tell us about yourself (optional)',
            'rows': 5
        }
    )

    # Password change fields
    current_password = PasswordField(
        'Current Password',
        validators=[Optional()],
        render_kw={'placeholder': 'Enter current password to change password'}
    )

    new_password = PasswordField(
        'New Password',
        validators=[Optional()],
        render_kw={'placeholder': 'Enter new password (leave blank to keep current)'}
    )

    new_password_confirm = PasswordField(
        'Confirm New Password',
        validators=[
            EqualTo('new_password', message='Passwords must match')
        ],
        render_kw={'placeholder': 'Re-enter new password'}
    )

    submit = SubmitField('Update Profile')

    def __init__(self, *args, **kwargs):
        """Initialize form with current user data."""
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.original_email = None

    def validate_email(self, email):
        """
        Validate email is unique (unless it's the user's current email).

        Args:
            email: Email field

        Raises:
            ValidationError: If email is already in use by another user
        """
        from flask_login import current_user

        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already in use. Please use a different email.')

    def validate_new_password(self, new_password):
        """
        Validate new password strength if provided.

        Args:
            new_password: New password field

        Raises:
            ValidationError: If password doesn't meet strength requirements
        """
        if not new_password.data:
            return  # Skip validation if no new password provided

        pwd = new_password.data

        if len(pwd) < 8:
            raise ValidationError('Password must be at least 8 characters long.')

        if not re.search(r'[A-Z]', pwd):
            raise ValidationError('Password must contain at least one uppercase letter.')

        if not re.search(r'[a-z]', pwd):
            raise ValidationError('Password must contain at least one lowercase letter.')

        if not re.search(r'\d', pwd):
            raise ValidationError('Password must contain at least one digit.')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', pwd):
            raise ValidationError('Password must contain at least one special character.')

        # If new password provided, current password is required
        if not self.current_password.data:
            raise ValidationError('Current password is required to set a new password.')
