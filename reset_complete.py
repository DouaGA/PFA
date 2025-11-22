# reset_complete.py
import os
from app import create_app
from models import db, User, GuideStage
import json

def reset_complete():
    app = create_app()
    
    with app.app_context():
        print("🔄 Réinitialisation complète...")
        
        # Supprimer la base existante
        db_path = 'remarqpfa.db'
        if os.path.exists(db_path):
            os.remove(db_path)
            print("🗑️ Base de données supprimée")
        
        # Créer les tables
        db.create_all()
        print("✅ Tables créées")
        
        # Créer les utilisateurs AVEC LA BONNE MÉTHODE
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'System', 
                'role': 'admin',
                'password': 'admin123'
            },
            {
                'username': 'jury',
                'email': 'jury@example.com',
                'first_name': 'Jury',
                'last_name': 'Member',
                'role': 'jury',
                'password': 'jury123'
            },
            {
                'username': 'student', 
                'email': 'student@example.com',
                'first_name': 'Student',
                'last_name': 'Test',
                'role': 'student',
                'password': 'student123'
            }
        ]
        
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role']
            )
            # UTILISER set_password() CORRECTEMENT
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"✅ {user_data['role']} créé: {user_data['email']} / {user_data['password']}")
        
        # Créer un guide simple
        guide = GuideStage(
            title='Guide Structure Standard',
            domain='web',
            content=json.dumps({
                'required_sections': ['introduction', 'methodologie', 'resultats', 'conclusion'],
                'section_patterns': {
                    'introduction': 'introduction',
                    'methodologie': 'méthodologie', 
                    'resultats': 'résultats',
                    'conclusion': 'conclusion'
                }
            }),
            created_by=1  # ID de l'admin
        )
        db.session.add(guide)
        print("✅ Guide créé")
        
        db.session.commit()
        
        # VÉRIFICATION
        print("\n🔍 Vérification...")
        users = User.query.all()
        for user in users:
            print(f"👤 {user.email} - Vérif mot de passe: {user.check_password('admin123' if user.email == 'admin@example.com' else 'student123' if user.email == 'student@example.com' else 'jury123')}")
        
        print("\n🎉 RÉINITIALISATION TERMINÉE!")
        print("\n🔑 VOUS POUVEZ MAINTENANT VOUS CONNECTER AVEC:")
        print("   📧 student@example.com")
        print("   🔐 student123")

if __name__ == '__main__':
    reset_complete()