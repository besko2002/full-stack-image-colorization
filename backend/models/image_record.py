from datetime import datetime
from backend.extensions import db


class ImageRecord(db.Model):
    __tablename__ = 'images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_original_path = db.Column(db.String(500), nullable=False)
    stored_output_path = db.Column(db.String(500), nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(30), default='uploaded', nullable=False)
    processing_time = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'original_image_url': self.stored_original_path,
            'output_image_url': self.stored_output_path,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'status': self.status,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() + 'Z',
            'updated_at': self.updated_at.isoformat() + 'Z',
        }
