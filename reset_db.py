import os
import sys

# Ajouter le dossier courant au path
sys.path.append(os.path.dirname(__file__))

from models import db

# Créer une application Flask minimale pour initialiser la base
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///remarqpfa.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    print("🗑️  Suppression des tables...")
    db.drop_all()
    
    print("🔄 Création des tables avec le nouveau schéma...")
    db.create_all()
    
    print("✅ Base de données réinitialisée avec succès!")
    print("📊 Tables créées:")
    print("   - users")
    print("   - comments") 
    print("   - pfaprojects")
    print("   - guide_stages")
    print("   - project_comments")
    print("   - project_documents")
    print("   - notifications")