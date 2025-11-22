# app.py - CORRIGER la section des blueprints
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from config import Config
from models import db, User, Comment, PFAProject, GuideStage, ProjectComment, ProjectDocument, Notification
import os
from werkzeug.security import generate_password_hash
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
# Ajouter cette fonction après les imports
def init_default_data():
    """Initialiser les données par défaut"""
    from models import User
    from werkzeug.security import generate_password_hash
    
    # Créer admin si n'existe pas
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='System',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Créer d'autres utilisateurs de test...
        db.session.commit()
        print("✓ Données par défaut initialisées")


def create_app():
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config.from_object(Config)
    
    # Initialisation de la base de données
    db.init_app(app)
    
    # Configuration de Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Import des blueprints - IMPORTANT: faire les imports APRÈS db.init_app()
    from routes.auth import auth_bp
    from routes.jury import jury_bp
    from routes.student import student_bp
    from routes.admin import admin_bp
    from routes.public import public_bp
    from routes.student_projects import student_projects_bp
    from routes.ai_routes import ai_bp
    
    # Enregistrement des blueprints - UNIQUEMENT UNE FOIS
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(jury_bp, url_prefix='/jury')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(public_bp)
    app.register_blueprint(student_projects_bp, url_prefix='/student')
    app.register_blueprint(ai_bp, url_prefix='/ai')  # UNIQUEMENT CETTE LIGNE
    
    print("✓ Blueprints chargés avec succès")
    
    # Route de base
    @app.route('/')
    def index():
        return render_template('public/home.html')

    # Jinja filter
    @app.template_filter('datetime')
    def format_datetime(value, fmt='%d/%m/%Y à %H:%M'):
        if not value:
            return ''
        if isinstance(value, datetime):
            try:
                return value.strftime(fmt)
            except Exception:
                return str(value)
        try:
            if isinstance(value, str):
                for fmt_str in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S.%f']:
                    try:
                        parsed = datetime.strptime(value, fmt_str)
                        return parsed.strftime(fmt)
                    except ValueError:
                        continue
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return parsed.strftime(fmt)
        except Exception:
            return str(value)
        return str(value)
    
    # Context processor
    @app.context_processor
    def inject_global_data():
        return {
            'current_year': datetime.now().year,
            'app_name': 'RemarqPFA'
        }
    
    # Gestion des erreurs
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    return app

# Création de l'application
app = create_app()

if __name__ == '__main__':
    if app is not None:
        with app.app_context():
            # Créer les tables
            db.create_all()
            print("✓ Base de données initialisée")

            # Initialiser les données par défaut
            init_default_data()

        print("🚀 Application démarrée sur http://localhost:5000")
        print("📧 Comptes de test:")
        print("   Admin: admin@example.com / admin123")
        print("   Jury: jury@example.com / jury123")
        print("   Étudiant: student@example.com / student123")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Erreur lors de la création de l'application")


# app.py - CORRECTION
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from config import Config
from models import db, User, Comment, PFAProject, GuideStage, ProjectComment, ProjectDocument, Notification
import os
import json  # AJOUTER CET IMPORT
from werkzeug.security import generate_password_hash
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def init_default_data():
    """Initialiser les données par défaut - VERSION COMPLÈTE"""
    from werkzeug.security import generate_password_hash
    
    # Créer admin si n'existe pas
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='System',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Créer utilisateur jury
        jury = User(
            username='jury',
            email='jury@example.com',
            first_name='Jury',
            last_name='Member',
            role='jury'
        )
        jury.set_password('jury123')
        db.session.add(jury)
        
        # Créer utilisateur étudiant
        student = User(
            username='student',
            email='student@example.com',
            first_name='Student',
            last_name='Test',
            role='student'
        )
        student.set_password('student123')
        db.session.add(student)
        
        # Créer des guides par défaut
        default_guides = [
            {
                'title': 'Guide Structure Web Development',
                'domain': 'web',
                'content': json.dumps({
                    'required_sections': ['introduction', 'methodologie', 'resultats', 'conclusion', 'bibliographie'],
                    'optional_sections': ['abstract', 'annexes', 'remerciements'],
                    'section_patterns': {
                        'introduction': r'\b(introduction|context|problématique|objectif)\b',
                        'methodologie': r'\b(méthodologie|méthode|approche|architecture|technologies)\b',
                        'resultats': r'\b(résultat|expérimentation|test|performance|métrique)\b',
                        'conclusion': r'\b(conclusion|perspective|recommandation|bilan)\b',
                        'bibliographie': r'\b(référence|bibliographie|source|citation)\b'
                    }
                })
            },
            {
                'title': 'Guide Structure AI/Data Science',
                'domain': 'ai',
                'content': json.dumps({
                    'required_sections': ['introduction', 'methodologie', 'algorithmes', 'resultats', 'discussion', 'conclusion'],
                    'optional_sections': ['abstract', 'bibliographie', 'annexes'],
                    'section_patterns': {
                        'introduction': r'\b(introduction|context|problématique)\b',
                        'methodologie': r'\b(méthodologie|méthode|dataset|features)\b',
                        'algorithmes': r'\b(algorithme|modèle|machine learning|deep learning)\b',
                        'resultats': r'\b(résultat|performance|précision|recall|f1-score)\b',
                        'discussion': r'\b(discussion|analyse|limitation|interprétation)\b',
                        'conclusion': r'\b(conclusion|perspective|recommandation)\b'
                    }
                })
            }
        ]
        
        for guide_data in default_guides:
            if not GuideStage.query.filter_by(title=guide_data['title']).first():
                guide = GuideStage(
                    title=guide_data['title'],
                    domain=guide_data['domain'],
                    content=guide_data['content'],
                    created_by=admin.id
                )
                db.session.add(guide)
        
        db.session.commit()
        print("✓ Données par défaut initialisées")
