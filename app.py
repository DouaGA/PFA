from flask import Flask, render_template
from flask_login import LoginManager, current_user
from config import Config
from models import db, User, Comment
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_default_users():
    """Crée les utilisateurs par défaut pour chaque rôle."""
    # Création compte admin
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@example.com",
            role="admin",
            first_name="Admin",
            last_name="System",
            is_active=True
        )
        admin.password_hash = generate_password_hash("admin123")
        db.session.add(admin)
        print("✓ Utilisateur admin créé (admin@example.com / admin123)")
    
    # Création compte jury
    jury = User.query.filter_by(username="jury").first()
    if not jury:
        jury = User(
            username="jury",
            email="jury@example.com",
            role="jury",
            first_name="Jean",
            last_name="Dupont",
            is_active=True
        )
        jury.password_hash = generate_password_hash("jury123")
        db.session.add(jury)
        print("✓ Utilisateur jury créé (jury@example.com / jury123)")
    
    # Création compte étudiant
    student = User.query.filter_by(username="student").first()
    if not student:
        student = User(
            username="student",
            email="student@example.com",
            role="student",
            first_name="Marie",
            last_name="Martin",
            is_active=True
        )
        student.password_hash = generate_password_hash("student123")
        db.session.add(student)
        print("✓ Utilisateur étudiant créé (student@example.com / student123)")
    if PFAProject.query.count() == 0:
        test_projects = [
            {
                'student_id': 3,  # ID de l'étudiant
                'title': 'Application E-commerce React',
                'description': 'Une application e-commerce moderne avec React et Node.js',
                'domain': 'web',
                'technologies': 'React, Node.js, MongoDB, Express',
                'status': 'published'
            },
            {
                'student_id': 3,
                'title': 'Application Mobile de Fitness',
                'description': 'Application mobile de suivi fitness avec React Native',
                'domain': 'mobile', 
                'technologies': 'React Native, Firebase, Redux',
                'status': 'published'
            }
        ]
        
        for project_data in test_projects:
            project = PFAProject(**project_data)
            db.session.add(project)
        
        db.session.commit()
        print("✓ Projets de test créés")
    # Création de commentaires de démonstration
    if Comment.query.count() == 0:
        comments_data = [
            {
                'jury_id': 2,  # ID du jury
                'student_id': 3,  # ID de l'étudiant
                'project_title': 'Application E-commerce Mobile',
                'content': 'Excellente interface utilisateur! La navigation est fluide et intuitive. Suggestions: ajouter un système de paiement intégré et optimiser les temps de chargement.',
                'recommendations': 12
            },
            {
                'jury_id': 2,
                'student_id': 3,
                'project_title': 'Système de Gestion Scolaire',
                'content': 'Architecture solide et code bien structuré. Recommandation: implémenter plus de tests unitaires et documenter les APIs.',
                'recommendations': 8
            },
            {
                'jury_id': 2,
                'student_id': 3,
                'project_title': 'Plateforme de Cours en Ligne',
                'content': 'Design responsive et fonctionnalités complètes. Améliorations possibles: ajouter un système de chat en temps réel et des analytics avancés.',
                'recommendations': 15
            }
        ]
        
        for comment_data in comments_data:
            comment = Comment(**comment_data)
            db.session.add(comment)
        print("✓ Commentaires de démonstration créés")
    
    db.session.commit()

from flask import Flask, render_template
from flask_login import LoginManager, current_user
from config import Config
from models import db, User, Comment, PFAProject, ProjectComment  # AJOUT DES IMPORTATIONS
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

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
    
    # Import des blueprints - VÉRIFIER QUE TOUS SONT IMPORTÉS
    try:
        from routes.auth import auth_bp
        from routes.jury import jury_bp
        from routes.student import student_bp
        from routes.admin import admin_bp
        from routes.public import public_bp
        from routes.student_projects import student_projects_bp  # IMPORT CRITIQUE
        
        # Enregistrement des blueprints
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(jury_bp, url_prefix='/jury')
        app.register_blueprint(student_bp, url_prefix='/student')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(public_bp)
        app.register_blueprint(student_projects_bp, url_prefix='/student')  # ENREGISTREMENT CRITIQUE
        
        print("✓ Blueprints chargés avec succès")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return None
    
    
    # Route de base
    @app.route('/')
    def index():
        return render_template('public/home.html')

    # Jinja filter: format datetime objects in templates
    @app.template_filter('datetime')
    def format_datetime(value, fmt='%d/%m/%Y à %H:%M'):
        """Format a datetime or ISO datetime string for templates."""
        if not value:
            return ''
        # If already a datetime object
        if isinstance(value, datetime):
            try:
                return value.strftime(fmt)
            except Exception:
                return str(value)

        # Try parsing ISO-format strings
        try:
            if isinstance(value, str):
                # Handle different datetime string formats
                for fmt_str in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S.%f']:
                    try:
                        parsed = datetime.strptime(value, fmt_str)
                        return parsed.strftime(fmt)
                    except ValueError:
                        continue
                # Try ISO format
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return parsed.strftime(fmt)
        except Exception:
            # Fallback: return original
            return str(value)
        
        return str(value)
    
    # Context processor pour rendre les données disponibles dans tous les templates
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

            # Initialiser les utilisateurs par défaut
            init_default_users()

        print("🚀 Application démarrée sur http://localhost:5000")
        print("📧 Comptes de test:")
        print("   Admin: admin@example.com / admin123")
        print("   Jury: jury@example.com / jury123")
        print("   Étudiant: student@example.com / student123")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Erreur lors de la création de l'application")