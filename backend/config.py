import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
ORIGINALS_DIR = os.path.join(STATIC_DIR, 'originals')
OUTPUTS_DIR = os.path.join(STATIC_DIR, 'outputs')

os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(ORIGINALS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    ORIGINALS_DIR = ORIGINALS_DIR
    OUTPUTS_DIR = OUTPUTS_DIR
    MODEL_CHECKPOINT = r"C:\models\colorization_best.pth"
    MODEL_DEVICE = os.environ.get('MODEL_DEVICE', 'cpu')
    FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))
