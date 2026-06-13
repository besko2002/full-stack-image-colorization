from datetime import datetime
from backend.extensions import db


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    dark_mode = db.Column(db.Boolean, default=False, nullable=False)
    notifications = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            'dark_mode': self.dark_mode,
            'notifications': self.notifications,
            'updated_at': self.updated_at.isoformat() + 'Z',
        }
