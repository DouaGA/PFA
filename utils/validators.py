import re
from datetime import datetime

def validate_email(email):
    """Valide une adresse email"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valide un mot de passe"""
    if not password:
        return False
    
    # Au moins 8 caractères
    if len(password) < 8:
        return False
    
    return True

def validate_username(username):
    """Valide un nom d'utilisateur"""
    if not username or len(username) < 3:
        return False
    
    # Lettres, chiffres, underscore uniquement
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

def validate_name(name):
    """Valide un prénom ou nom"""
    if not name:
        return False
    
    # Lettres, espaces, apostrophes et tirets uniquement
    pattern = r'^[a-zA-ZÀ-ÿ\s\'-]+$'
    return re.match(pattern, name) is not None and len(name) >= 2

def validate_project_title(title):
    """Valide un titre de projet"""
    if not title or len(title) < 5:
        return False
    
    if len(title) > 200:
        return False
    
    return True

def validate_comment_content(content):
    """Valide le contenu d'un commentaire"""
    if not content or len(content.strip()) < 10:
        return False
    
    if len(content) > 5000:
        return False
    
    return True

def sanitize_input(text):
    """Nettoie le texte des caractères dangereux"""
    if not text:
        return ""
    
    # Échapper les caractères HTML dangereux
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '&': '&amp;'
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text

def validate_date(date_string, fmt='%Y-%m-%d'):
    """Valide une date"""
    try:
        datetime.strptime(date_string, fmt)
        return True
    except ValueError:
        return False

def validate_role(role):
    """Valide un rôle utilisateur"""
    valid_roles = ['admin', 'jury', 'student']
    return role in valid_roles

def validate_positive_integer(value):
    """Valide un entier positif"""
    try:
        num = int(value)
        return num >= 0
    except (ValueError, TypeError):
        return False