# routes/documents.py
from flask import Blueprint, request, jsonify, current_app, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, ProjectDocument, PFAProject
from datetime import datetime

documents_bp = Blueprint('documents', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@documents_bp.route('/upload/<int:project_id>', methods=['GET', 'POST'])
@login_required
def upload_document(project_id):
    # Vérifier que le projet existe et appartient à l'utilisateur
    project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            print("📤 Début de l'upload...")  # Debug
            
            if 'document' not in request.files:
                flash('Aucun fichier sélectionné', 'error')
                return redirect(request.referrer)
            
            file = request.files['document']
            print(f"📄 Fichier reçu: {file.filename}")  # Debug
            
            if file.filename == '':
                flash('Aucun fichier sélectionné', 'error')
                return redirect(request.referrer)
            
            if file and allowed_file(file.filename):
                # Sécuriser le nom du fichier
                filename = secure_filename(file.filename)
                
                # Créer un nom unique
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{filename}"
                
                # Chemin de sauvegarde
                upload_folder = current_app.config['UPLOAD_FOLDER']
                documents_folder = os.path.join(upload_folder, 'documents')
                
                # Créer le dossier s'il n'existe pas
                os.makedirs(documents_folder, exist_ok=True)
                print(f"📁 Dossier: {documents_folder}")  # Debug
                
                file_path = os.path.join(documents_folder, unique_filename)
                print(f"💾 Sauvegarde vers: {file_path}")  # Debug
                
                # Sauvegarder le fichier
                file.save(file_path)
                print("✅ Fichier sauvegardé")  # Debug
                
                # Créer l'entrée dans la base de données
                document = ProjectDocument(
                    project_id=project_id,
                    title=request.form.get('title', filename.rsplit('.', 1)[0]),
                    description=request.form.get('description', ''),
                    file_type=filename.rsplit('.', 1)[1].lower(),
                    file_path=unique_filename,
                    file_size=os.path.getsize(file_path),
                    is_public=bool(request.form.get('is_public', True))
                )
                
                db.session.add(document)
                db.session.commit()
                print("✅ Document enregistré en base")  # Debug
                
                flash('Document uploadé avec succès!', 'success')
                return redirect(url_for('student.project_detail', project_id=project_id))
                
            else:
                flash('Type de fichier non autorisé. Formats acceptés: PDF, DOC, DOCX, PNG, JPG, JPEG', 'error')
                return redirect(request.referrer)
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur upload: {str(e)}")  # Debug
            flash(f'Erreur lors de l\'upload: {str(e)}', 'error')
            return redirect(request.referrer)
    
    # GET request - afficher le formulaire
    return render_template('student/upload_document.html', project=project)