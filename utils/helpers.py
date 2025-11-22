from datetime import datetime
from flask import request
import json

def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Formatter une date"""
    if value is None:
        return ""
    return value.strftime(format)

def get_client_ip():
    """Récupérer l'IP du client"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        return request.remote_addr

def paginate_query(query, page, per_page=10):
    """Paginer une requête"""
    return query.paginate(page=page, per_page=per_page, error_out=False)

def to_dict(obj):
    """Convertir un objet SQLAlchemy en dict"""
    if hasattr(obj, '__table__'):
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    return {}

def allowed_file(filename, allowed_extensions=None):
    """Vérifier si un fichier est autorisé"""
    if allowed_extensions is None:
        allowed_extensions = {'pdf', 'doc', 'docx', 'txt'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions