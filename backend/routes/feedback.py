from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.extensions import db
from backend.models import Feedback, User, ActivityLog


feedback_bp = Blueprint('feedback', __name__)


def _current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


def _log(user_id: int, action: str):
    db.session.add(ActivityLog(user_id=user_id, action=action))
    db.session.commit()


@feedback_bp.post('')
@feedback_bp.post('/')
@jwt_required()
def create_feedback():
    user = _current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    rating = int(data.get('rating') or 0)

    if not message:
        return jsonify({'error': 'Feedback message is required'}), 400
    if rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400

    feedback = Feedback(user_id=user.id, message=message, rating=rating)
    db.session.add(feedback)
    db.session.commit()
    _log(user.id, 'Submitted feedback')
    return jsonify({'message': 'Feedback submitted successfully', 'feedback': feedback.to_dict()}), 201


@feedback_bp.get('/me')
@jwt_required()
def my_feedback():
    user = _current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    entries = Feedback.query.filter_by(user_id=user.id).order_by(Feedback.created_at.desc()).all()
    return jsonify({'feedback': [f.to_dict() for f in entries]})
