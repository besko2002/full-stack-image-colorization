from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.extensions import db
from backend.models import User, UserPreference, ActivityLog


users_bp = Blueprint('users', __name__)


def _current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


def _log(user_id: int, action: str):
    db.session.add(ActivityLog(user_id=user_id, action=action))
    db.session.commit()


@users_bp.get('/me')
@jwt_required()
def get_me():
    user = _current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    preference = user.preference.to_dict() if user.preference else {'dark_mode': False, 'notifications': True}
    return jsonify({'user': user.to_dict(), 'preferences': preference})


@users_bp.put('/me')
@jwt_required()
def update_me():
    user = _current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()

    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400

    existing = User.query.filter(User.email == email, User.id != user.id).first()
    if existing:
        return jsonify({'error': 'Email already in use'}), 409

    user.name = name
    user.email = email
    db.session.commit()
    _log(user.id, 'Profile updated')
    return jsonify({'message': 'Profile updated', 'user': user.to_dict()})


@users_bp.put('/preferences')
@jwt_required()
def update_preferences():
    user = _current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json(silent=True) or {}
    pref = user.preference
    if pref is None:
        pref = UserPreference(user_id=user.id)
        db.session.add(pref)

    if 'dark_mode' in data:
        pref.dark_mode = bool(data['dark_mode'])
    if 'notifications' in data:
        pref.notifications = bool(data['notifications'])

    db.session.commit()
    _log(user.id, 'Preferences updated')
    return jsonify({'message': 'Preferences updated', 'preferences': pref.to_dict()})


@users_bp.put('/change-password')
@jwt_required()
def change_password():
    user = _current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or ''
    new_password = data.get('new_password') or ''

    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400

    user.set_password(new_password)
    db.session.commit()
    _log(user.id, 'Password changed')
    return jsonify({'message': 'Password changed successfully'})
