import os
import time
import uuid
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from PIL import Image
from backend.extensions import db
from backend.models import ImageRecord, User, ActivityLog


images_bp = Blueprint('images', __name__)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}


def _current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


def _log(user_id: int, action: str):
    db.session.add(ActivityLog(user_id=user_id, action=action))
    db.session.commit()


def _is_allowed(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@images_bp.post('/upload')
@jwt_required()
def upload_image():
    user = _current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if 'image' not in request.files:
        return jsonify({'error': 'Image file is required'}), 400

    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not _is_allowed(file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400

    image_bytes = file.read()
    if not image_bytes:
        return jsonify({'error': 'Uploaded file is empty'}), 400

    try:
        Image.open(io := __import__('io').BytesIO(image_bytes)).verify()
    except Exception:
        return jsonify({'error': 'Invalid image file'}), 400

    start = time.time()
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    output_name = f"{uuid.uuid4().hex}.png"

    original_abs = os.path.join(current_app.config['ORIGINALS_DIR'], unique_name)
    output_abs = os.path.join(current_app.config['OUTPUTS_DIR'], output_name)

    with open(original_abs, 'wb') as f:
        f.write(image_bytes)

    record = ImageRecord(
        user_id=user.id,
        original_filename=file.filename,
        stored_original_path=f'/static/originals/{unique_name}',
        mime_type=file.mimetype,
        file_size=len(image_bytes),
        status='processing',
    )
    db.session.add(record)
    db.session.commit()

    try:
        result_image = current_app.model_service.predict_image(image_bytes)
        result_image.save(output_abs)
        record.stored_output_path = f'/static/outputs/{output_name}'
        record.status = 'completed'
        record.processing_time = round(time.time() - start, 4)
        db.session.commit()
        _log(user.id, f'Uploaded and colorized {file.filename}')
        return jsonify({
            'message': 'Image colorized successfully',
            'image': record.to_dict(),
        }), 201
    except Exception as exc:
        record.status = 'failed'
        db.session.commit()
        return jsonify({'error': f'Colorization failed: {exc}'}), 500


@images_bp.get('/my-history')
@jwt_required()
def my_history():
    user = _current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    images = ImageRecord.query.filter_by(user_id=user.id).order_by(ImageRecord.created_at.desc()).all()
    return jsonify({'images': [img.to_dict() for img in images]})


@images_bp.get('/<int:image_id>')
@jwt_required()
def get_image(image_id: int):
    user = _current_user()
    image = ImageRecord.query.get(image_id)
    if not image or (image.user_id != user.id and user.role != 'admin'):
        return jsonify({'error': 'Image not found'}), 404
    return jsonify({'image': image.to_dict()})


@images_bp.delete('/<int:image_id>')
@jwt_required()
def delete_image(image_id: int):
    user = _current_user()
    image = ImageRecord.query.get(image_id)
    if not image or (image.user_id != user.id and user.role != 'admin'):
        return jsonify({'error': 'Image not found'}), 404

    if image.stored_original_path:
        original_abs = os.path.join(current_app.root_path, image.stored_original_path.lstrip('/'))
        if os.path.exists(original_abs):
            os.remove(original_abs)
    if image.stored_output_path:
        output_abs = os.path.join(current_app.root_path, image.stored_output_path.lstrip('/'))
        if os.path.exists(output_abs):
            os.remove(output_abs)

    db.session.delete(image)
    db.session.commit()
    _log(user.id, f'Deleted image record {image_id}')
    return jsonify({'message': 'Image deleted'})
