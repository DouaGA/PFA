import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///remarqpfa.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # App
    APP_NAME = "RemarqPFA"
    VERSION = "2.0.0"
    
    # Pagination
    ITEMS_PER_PAGE = 10

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# config.py - Ajoutez cette méthode
import os

def ensure_upload_folders():
    """Crée les dossiers d'upload s'ils n'existent pas"""
    upload_folders = [
        Config.UPLOAD_FOLDER,
        os.path.join(Config.UPLOAD_FOLDER, 'documents'),
        os.path.join(Config.UPLOAD_FOLDER, 'projects')
    ]
    
    for folder in upload_folders:
        os.makedirs(folder, exist_ok=True)