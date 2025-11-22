#!/usr/bin/env python3
"""
Script principal pour lancer l'application RemarqPFA
"""

import os
from app import create_app

# Charger la configuration
env = os.environ.get('FLASK_ENV', 'development')
app = create_app()

if __name__ == '__main__':
    if app is not None:
        print(f"🚀 Lancement de RemarqPFA en mode {env}...")
        print("📧 Comptes de test disponibles:")
        print("   Admin: admin@example.com / admin123")
        print("   Jury: jury@example.com / jury123")
        print("   Étudiant: student@example.com / student123")
        
        app.run(
            host=os.environ.get('HOST', '0.0.0.0'),
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('DEBUG', 'True').lower() == 'true'
        )
    else:
        print("❌ Erreur lors de la création de l'application")