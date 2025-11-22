# reset_database.py
import os
from app import create_app
from models import db

def reset_database():
    app = create_app()
    
    with app.app_context():
        # Supprimer toutes les tables
        db.drop_all()
        print("🗑️  Toutes les tables supprimées")
        
        # Recréer toutes les tables avec le nouveau schéma
        db.create_all()
        print("✅ Tables recréées avec le nouveau schéma")
        
        # Initialiser les données par défaut
        from models import User, GuideStage
        import json
        from werkzeug.security import generate_password_hash
        
        # Créer admin
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='System',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Créer jury
        jury = User(
            username='jury',
            email='jury@example.com',
            first_name='Jury',
            last_name='Member',
            role='jury'
        )
        jury.set_password('jury123')
        db.session.add(jury)
        
        # Créer étudiant
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
        guides_data = [
            {
                'title': 'Guide Structure Web Development',
                'domain': 'web',
                'content': {
                    'required_sections': ['introduction', 'methodologie', 'resultats', 'conclusion', 'bibliographie'],
                    'optional_sections': ['abstract', 'annexes', 'remerciements'],
                    'section_patterns': {
                        'introduction': r'\b(introduction|context|problématique|objectif)\b',
                        'methodologie': r'\b(méthodologie|méthode|approche|architecture|technologies)\b',
                        'resultats': r'\b(résultat|expérimentation|test|performance|métrique)\b',
                        'conclusion': r'\b(conclusion|perspective|recommandation|bilan)\b',
                        'bibliographie': r'\b(référence|bibliographie|source|citation)\b'
                    }
                }
            },
            {
                'title': 'Guide Structure AI/Data Science',
                'domain': 'ai',
                'content': {
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
                }
            },
            {
                'title': 'Guide Structure Mobile Development',
                'domain': 'mobile',
                'content': {
                    'required_sections': ['introduction', 'methodologie', 'interface', 'resultats', 'conclusion'],
                    'optional_sections': ['abstract', 'bibliographie', 'annexes'],
                    'section_patterns': {
                        'introduction': r'\b(introduction|context|problématique)\b',
                        'methodologie': r'\b(méthodologie|méthode|technologie|framework)\b',
                        'interface': r'\b(interface|design|ux|ui|expérience utilisateur)\b',
                        'resultats': r'\b(résultat|test|performance|utilisabilité)\b',
                        'conclusion': r'\b(conclusion|perspective|recommandation)\b'
                    }
                }
            }
        ]
        
        for guide_data in guides_data:
            guide = GuideStage(
                title=guide_data['title'],
                domain=guide_data['domain'],
                content=json.dumps(guide_data['content']),
                created_by=admin.id
            )
            db.session.add(guide)
        
        db.session.commit()
        print("✅ Données par défaut initialisées")
        print("✅ Guides créés avec colonne 'domain'")
        
        # Vérifier que la colonne domain existe
        guide = GuideStage.query.first()
        if guide and hasattr(guide, 'domain'):
            print(f"✅ Vérification: Guide '{guide.title}' a le domaine '{guide.domain}'")
        else:
            print("❌ Problème avec la colonne domain")

if __name__ == '__main__':
    reset_database()