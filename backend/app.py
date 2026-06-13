import os
from flask import Flask, jsonify, send_from_directory
from backend.config import Config
from backend.extensions import db, jwt, cors
from backend.routes.auth import auth_bp
from backend.routes.users import users_bp
from backend.routes.images import images_bp
from backend.routes.feedback import feedback_bp
from backend.routes.admin import admin_bp
from backend.services.model_service import ModelService
from backend.models import User


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    app.model_service = ModelService(
        checkpoint_path=app.config['MODEL_CHECKPOINT'],
        device=app.config['MODEL_DEVICE'],
    )

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(images_bp, url_prefix='/api/images')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    with app.app_context():
        db.create_all()
        _ensure_admin_seed()

    @app.get('/api/health')
    def health():
        return jsonify({'status': 'API Working'})

    @app.get('/')
    def index():
        return send_from_directory(app.config['FRONTEND_DIR'], 'index.html')

    @app.get('/<path:path>')
    def frontend_files(path):
        full = os.path.join(app.config['FRONTEND_DIR'], path)
        if os.path.exists(full):
            return send_from_directory(app.config['FRONTEND_DIR'], path)
        return send_from_directory(app.config['FRONTEND_DIR'], 'index.html')

    return app


def _ensure_admin_seed():
    if User.query.count() == 0:
        admin = User(name='Admin User', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
