# fix_database.py
import os
import sqlite3
from app import create_app
from models import db, User, GuideStage
import json

def fix_database():
    app = create_app()
    
    with app.app_context():
        print("🔧 Réparation de la base de données...")
        
        # Supprimer et recréer la base
        db_path = 'remarqpfa.db'
        if os.path.exists(db_path):
            os.remove(db_path)
            print("🗑️ Ancienne base supprimée")
        
        db.create_all()
        print("✅ Nouvelle base créée")
        
        # Créer les utilisateurs de test
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='System',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        jury = User(
            username='jury',
            email='jury@example.com',
            first_name='Jury',
            last_name='Member',
            role='jury'
        )
        jury.set_password('jury123')
        db.session.add(jury)
        
        student = User(
            username='student',
            email='student@example.com',
            first_name='Étudiant',
            last_name='Test',
            role='student'
        )
        student.set_password('student123')
        db.session.add(student)
        
        # Créer des guides
        guides = [
            {
                'title': 'Guide Web Development',
                'domain': 'web',
                'content': {
                    'required_sections': ['introduction', 'methodologie', 'resultats', 'conclusion'],
                    'section_patterns': {
                        'introduction': r'introduction|contexte',
                        'methodologie': r'méthodologie|technologie',
                        'resultats': r'résultat|test',
                        'conclusion': r'conclusion|perspective'
                    }
                }
            }
        ]
        
        for guide_data in guides:
            guide = GuideStage(
                title=guide_data['title'],
                domain=guide_data['domain'],
                content=json.dumps(guide_data['content']),
                created_by=admin.id
            )
            db.session.add(guide)
        
        db.session.commit()
        print("✅ Utilisateurs et guides créés")
        
        # Vérification
        user_count = User.query.count()
        guide_count = GuideStage.query.count()
        print(f"✅ Vérification: {user_count} utilisateurs, {guide_count} guides")
        
        print("🎉 Base de données réparée avec succès!")
        print("\n🔑 Comptes de test:")
        print("   Admin: admin@example.com / admin123")
        print("   Jury: jury@example.com / jury123")
        print("   Étudiant: student@example.com / student123")

if __name__ == '__main__':
    fix_database()