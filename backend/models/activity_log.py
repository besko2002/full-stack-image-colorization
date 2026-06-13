from datetime import datetime
from backend.extensions import db


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'action': self.action,
            'created_at': self.created_at.isoformat() + 'Z',
        }
