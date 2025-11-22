# fix_upload_urgent.py
import os
import sys

# Ajouter le dossier parent au path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from config import Config

def fix_upload_system():
    app = create_app()
    
    with app.app_context():
        # 1. Créer les dossiers d'upload
        upload_folders = [
            Config.UPLOAD_FOLDER,
            os.path.join(Config.UPLOAD_FOLDER, 'documents'),
            os.path.join(Config.UPLOAD_FOLDER, 'projects')
        ]
        
        for folder in upload_folders:
            try:
                os.makedirs(folder, exist_ok=True)
                print(f"✅ Dossier créé: {folder}")
                
                # Vérifier les permissions
                test_file = os.path.join(folder, 'test.txt')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"✅ Permissions OK: {folder}")
                
            except Exception as e:
                print(f"❌ Erreur avec {folder}: {e}")
        
        # 2. Vérifier la configuration
        print(f"\n📋 Configuration upload:")
        print(f"   - UPLOAD_FOLDER: {Config.UPLOAD_FOLDER}")
        print(f"   - MAX_CONTENT_LENGTH: {Config.MAX_CONTENT_LENGTH} bytes")
        print(f"   - ALLOWED_EXTENSIONS: {Config.ALLOWED_EXTENSIONS}")
        
        # 3. Vérifier si le dossier existe vraiment
        if os.path.exists(Config.UPLOAD_FOLDER):
            print(f"✅ Le dossier upload existe: {Config.UPLOAD_FOLDER}")
        else:
            print(f"❌ Le dossier upload n'existe PAS: {Config.UPLOAD_FOLDER}")
        
        print("\n🎉 Réparation terminée!")

if __name__ == '__main__':
    fix_upload_system()