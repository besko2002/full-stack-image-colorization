from datetime import datetime, timedelta
import secrets
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from backend.extensions import db
from backend.models import User, UserPreference, PasswordResetToken, ActivityLog


auth_bp = Blueprint('auth', __name__)


def _log(user_id: int, action: str):
    db.session.add(ActivityLog(user_id=user_id, action=action))
    db.session.commit()


@auth_bp.post('/register')
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required'}), 400
    if '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    role = 'admin' if User.query.count() == 0 else 'user'
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    db.session.add(UserPreference(user_id=user.id))
    db.session.commit()
    _log(user.id, 'Account created')

    access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
    return jsonify({
        'message': 'Account created successfully',
        'access_token': access_token,
        'token_type': 'bearer',
        'user': user.to_dict(),
        'preferences': user.preference.to_dict(),
    }), 201


@auth_bp.post('/login')
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    if not user.is_active:
        return jsonify({'error': 'User account is disabled'}), 403

    access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
    _log(user.id, 'Logged in')
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'token_type': 'bearer',
        'user': user.to_dict(),
        'preferences': user.preference.to_dict() if user.preference else {'dark_mode': False, 'notifications': True},
    })


@auth_bp.post('/forgot-password')
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'If this email exists, a reset token has been generated.'})

    token = secrets.token_urlsafe(32)
    reset = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.session.add(reset)
    db.session.commit()
    _log(user.id, 'Requested password reset')

    return jsonify({
        'message': 'Reset token generated. In production, email this token to the user.',
        'reset_token': token,
        'expires_at': reset.expires_at.isoformat() + 'Z',
    })


@auth_bp.post('/reset-password')
def reset_password():
    data = request.get_json(silent=True) or {}
    token = data.get('token') or ''
    password = data.get('password') or ''

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    reset = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset or reset.expires_at < datetime.utcnow():
        return jsonify({'error': 'Invalid or expired reset token'}), 400

    user = User.query.get(reset.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.set_password(password)
    reset.used = True
    db.session.commit()
    _log(user.id, 'Password reset completed')

    return jsonify({'message': 'Password updated successfully'})
