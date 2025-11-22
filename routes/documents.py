from flask import Blueprint, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, ProjectDocument, PFAProject

documents_bp = Blueprint('documents', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@documents_bp.route('/upload/<int:project_id>', methods=['POST'])
@login_required
def upload_document(project_id):
    try:
        # Vérifier que le projet existe et appartient à l'utilisateur
        project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
        
        if 'document' not in request.files:
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.referrer)
        
        file = request.files['document']
        if file.filename == '':
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.referrer)
        
        if file and allowed_file(file.filename):
            # Sécuriser le nom du fichier
            filename = secure_filename(file.filename)
            
            # Créer un nom unique pour éviter les collisions
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            
            # Chemin de sauvegarde
            upload_folder = current_app.config['UPLOAD_FOLDER']
            documents_folder = os.path.join(upload_folder, 'documents')
            os.makedirs(documents_folder, exist_ok=True)
            
            file_path = os.path.join(documents_folder, unique_filename)
            
            # Sauvegarder le fichier
            file.save(file_path)
            
            # Créer l'entrée dans la base de données
            document = ProjectDocument(
                project_id=project_id,
                title=request.form.get('title', filename),
                description=request.form.get('description', ''),
                file_type=filename.rsplit('.', 1)[1].lower(),
                file_path=unique_filename,  # Stocker seulement le nom du fichier
                file_size=os.path.getsize(file_path),
                is_public=bool(request.form.get('is_public', True))
            )
            
            db.session.add(document)
            db.session.commit()
            
            flash('Document uploadé avec succès!', 'success')
            return redirect(request.referrer)
        else:
            flash('Type de fichier non autorisé', 'error')
            return redirect(request.referrer)
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur upload: {str(e)}")
        flash('Erreur lors de l\'upload du document', 'error')
        return redirect(request.referrer)