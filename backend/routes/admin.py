from flask import Blueprint, jsonify, request
from sqlalchemy import func
from backend.extensions import db
from backend.models import User, ImageRecord, Feedback, ActivityLog
from backend.routes.helpers import admin_required


admin_bp = Blueprint('admin', __name__)


@admin_bp.get('/stats')
@admin_required
def stats():
    total_users = User.query.count()
    total_images = ImageRecord.query.count()
    total_feedback = Feedback.query.count()
    completed_images = ImageRecord.query.filter_by(status='completed').count()
    failed_images = ImageRecord.query.filter_by(status='failed').count()
    avg_processing_time = db.session.query(func.avg(ImageRecord.processing_time)).scalar() or 0

    return jsonify({
        'total_users': total_users,
        'total_images': total_images,
        'total_feedback': total_feedback,
        'completed_images': completed_images,
        'failed_images': failed_images,
        'avg_processing_time': round(float(avg_processing_time), 4) if avg_processing_time else 0,
        'api_server': 'Online',
        'database': 'Connected',
        'model': 'Ready',
    })


@admin_bp.get('/users')
@admin_required
def users():
    search = (request.args.get('search') or '').strip().lower()
    page = max(int(request.args.get('page', 1)), 1)
    per_page = min(max(int(request.args.get('per_page', 10)), 1), 50)

    query = User.query
    if search:
        like = f'%{search}%'
        query = query.filter(db.or_(User.name.ilike(like), User.email.ilike(like)))

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    results = []
    for user in pagination.items:
        results.append({
            **user.to_dict(),
            'image_count': ImageRecord.query.filter_by(user_id=user.id).count(),
            'feedback_count': Feedback.query.filter_by(user_id=user.id).count(),
        })

    return jsonify({
        'users': results,
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'pages': pagination.pages,
    })


@admin_bp.get('/images')
@admin_required
def images():
    rows = ImageRecord.query.order_by(ImageRecord.created_at.desc()).limit(100).all()
    return jsonify({'images': [row.to_dict() for row in rows]})


@admin_bp.get('/feedback')
@admin_required
def feedback():
    rows = Feedback.query.order_by(Feedback.created_at.desc()).limit(100).all()
    return jsonify({'feedback': [row.to_dict() for row in rows]})


@admin_bp.get('/activity')
@admin_required
def activity():
    rows = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(50).all()
    return jsonify({'activity': [row.to_dict() for row in rows]})
