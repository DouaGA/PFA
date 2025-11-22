# migrate_database.py
import sqlite3
import os
from app import create_app
from models import db

def migrate_database():
    app = create_app()
    
    with app.app_context():
        # Chemin vers la base de données
        db_path = 'remarqpfa.db'
        
        if os.path.exists(db_path):
            # Sauvegarder l'ancienne base
            backup_path = 'remarqpfa_backup.db'
            os.rename(db_path, backup_path)
            print(f"📦 Ancienne base sauvegardée comme {backup_path}")
            
            # Créer une nouvelle base avec le bon schéma
            db.create_all()
            print("✅ Nouvelle base créée avec le bon schéma")
            
            # Migrer les données depuis la sauvegarde
            old_conn = sqlite3.connect(backup_path)
            new_conn = sqlite3.connect(db_path)
            
            # Migrer les tables une par une
            tables = ['users', 'comments', 'pfaprojects', 'project_comments', 'project_documents', 'notifications']
            
            for table in tables:
                old_conn.row_factory = sqlite3.Row
                old_data = old_conn.execute(f'SELECT * FROM {table}').fetchall()
                
                if old_data:
                    columns = ', '.join(old_data[0].keys())
                    placeholders = ', '.join(['?' for _ in old_data[0].keys()])
                    
                    for row in old_data:
                        new_conn.execute(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})', tuple(row))
                    
                    print(f"✅ Données migrées pour {table}: {len(old_data)} lignes")
            
            # Migrer guide_stages avec la nouvelle colonne domain
            try:
                old_guides = old_conn.execute('SELECT * FROM guide_stages').fetchall()
                for guide in old_guides:
                    # Ajouter une valeur par défaut pour domain
                    new_conn.execute('''
                        INSERT INTO guide_stages (id, title, description, content, file_path, domain, is_active, created_by, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        guide['id'], guide['title'], guide['description'], guide['content'], 
                        guide['file_path'], 'web', guide['is_active'], guide['created_by'], guide['created_at']
                    ))
                print(f"✅ Guides migrés avec domaine par défaut: {len(old_guides)} guides")
            except Exception as e:
                print(f"⚠️  Aucun guide à migrer: {e}")
            
            new_conn.commit()
            old_conn.close()
            new_conn.close()
            
            print("🎉 Migration terminée avec succès!")
        else:
            print("❌ Fichier de base de données non trouvé")

if __name__ == '__main__':
    migrate_database()