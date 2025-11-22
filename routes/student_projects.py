# routes/student_projects.py - VERSION CORRIGÉE
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, PFAProject, ProjectDocument, ProjectComment
from datetime import datetime

student_projects_bp = Blueprint('student_projects', __name__)

@student_projects_bp.route('/mes-projets')
@login_required
def my_projects():
    """Afficher les projets de l'étudiant"""
    projects = PFAProject.query.filter_by(student_id=current_user.id).order_by(PFAProject.created_at.desc()).all()
    return render_template('student/my_projects.html', projects=projects)

@student_projects_bp.route('/projet/<int:project_id>')
@login_required
def project_detail(project_id):
    """Détails d'un projet spécifique"""
    project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
    
    # Incrémenter le compteur de vues
    project.increment_views()
    
    # Récupérer les documents du projet
    documents = ProjectDocument.query.filter_by(project_id=project_id).order_by(ProjectDocument.uploaded_at.desc()).all()
    
    # Récupérer les commentaires
    comments = ProjectComment.query.filter_by(project_id=project_id).order_by(ProjectComment.created_at.desc()).all()
    
    return render_template('student/project_detail.html', 
                         project=project, 
                         documents=documents, 
                         comments=comments)

@student_projects_bp.route('/projet/<int:project_id>/upload-document', methods=['GET', 'POST'])
@login_required
def upload_project_document(project_id):
    """Uploader un document pour un projet - NOUVEAU NOM"""
    # Vérifier que le projet existe et appartient à l'étudiant
    project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            print("📤 Début de l'upload...")
            
            if 'document' not in request.files:
                flash('Aucun fichier sélectionné', 'error')
                return redirect(request.referrer)
            
            file = request.files['document']
            print(f"📄 Fichier reçu: {file.filename}")
            
            if file.filename == '':
                flash('Aucun fichier sélectionné', 'error')
                return redirect(request.referrer)
            
            # Vérifier l'extension
            allowed_extensions = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
            if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
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
                print(f"📁 Dossier: {documents_folder}")
                
                file_path = os.path.join(documents_folder, unique_filename)
                print(f"💾 Sauvegarde vers: {file_path}")
                
                # Sauvegarder le fichier
                file.save(file_path)
                print("✅ Fichier sauvegardé")
                
                # Créer l'entrée dans la base de données
                document = ProjectDocument(
                    project_id=project_id,
                    title=request.form.get('title', filename.rsplit('.', 1)[0]),
                    description=request.form.get('description', ''),
                    file_type=filename.rsplit('.', 1)[1].lower(),
                    file_path=unique_filename,
                    file_size=os.path.getsize(file_path),
                    is_public=True
                )
                
                db.session.add(document)
                db.session.commit()
                print("✅ Document enregistré en base")
                
                flash('Document uploadé avec succès!', 'success')
                return redirect(url_for('student_projects.project_detail', project_id=project_id))
                
            else:
                flash('Type de fichier non autorisé. Formats acceptés: PDF, DOC, DOCX, PNG, JPG, JPEG', 'error')
                return redirect(request.referrer)
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur upload: {str(e)}")
            flash(f'Erreur lors de l\'upload: {str(e)}', 'error')
            return redirect(request.referrer)
    
    # GET request - afficher le formulaire
    return render_template('student/upload_document.html', project=project)

@student_projects_bp.route('/document/<int:document_id>/supprimer', methods=['POST'])
@login_required
def delete_project_document(document_id):
    """Supprimer un document - NOUVEAU NOM"""
    try:
        document = ProjectDocument.query.get_or_404(document_id)
        project = PFAProject.query.get(document.project_id)
        
        # Vérifier les permissions
        if current_user.id != project.student_id and current_user.role != 'admin':
            flash('Vous n\'avez pas la permission de supprimer ce document', 'error')
            return redirect(url_for('student_projects.project_detail', project_id=project.id))
        
        # Supprimer le fichier physique
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', document.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Supprimer de la base de données
        db.session.delete(document)
        db.session.commit()
        
        flash('Document supprimé avec succès', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors de la suppression du document', 'error')
        print(f"❌ Erreur suppression document: {str(e)}")
    
    return redirect(url_for('student_projects.project_detail', project_id=project.id))

@student_projects_bp.route('/projet/<int:project_id>/publier', methods=['POST'])
@login_required
def publish_project(project_id):
    """Publier un projet"""
    project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
    
    try:
        project.status = 'published'
        db.session.commit()
        flash('Projet publié avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors de la publication du projet', 'error')
    
    return redirect(url_for('student_projects.project_detail', project_id=project_id))

@student_projects_bp.route('/projet/<int:project_id>/commenter', methods=['POST'])
@login_required
def add_project_comment(project_id):
    """Ajouter un commentaire à un projet"""
    project = PFAProject.query.get_or_404(project_id)
    
    try:
        content = request.form.get('content')
        is_helpful = request.form.get('is_helpful') == 'true'
        
        comment = ProjectComment(
            project_id=project_id,
            user_id=current_user.id,
            content=content,
            is_helpful=is_helpful
        )
        
        db.session.add(comment)
        db.session.commit()
        flash('Commentaire ajouté avec succès!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors de l\'ajout du commentaire', 'error')
    
    return redirect(url_for('student_projects.project_detail', project_id=project_id))

# Routes API pour les likes
@student_projects_bp.route('/api/commentaires/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    """Like un commentaire"""
    try:
        comment = ProjectComment.query.get_or_404(comment_id)
        comment.increment_likes()
        
        return {
            'success': True,
            'likes_count': comment.likes_count
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }, 500
    

# routes/student_projects.py - AJOUTER cette fonction
@student_projects_bp.route('/rechercher-projets')
@login_required
def search_projects():
    """Rechercher des projets publics"""
    # Récupérer les paramètres de recherche
    query = request.args.get('q', '')
    domain = request.args.get('domain', '')
    page = request.args.get('page', 1, type=int)
    
    # Construire la requête de base
    projects_query = PFAProject.query.filter_by(status='published', is_public=True)
    
    # Appliquer les filtres
    if query:
        projects_query = projects_query.filter(
            PFAProject.title.ilike(f'%{query}%') | 
            PFAProject.description.ilike(f'%{query}%') |
            PFAProject.technologies.ilike(f'%{query}%')
        )
    
    if domain:
        projects_query = projects_query.filter_by(domain=domain)
    
    # Pagination
    projects = projects_query.order_by(PFAProject.created_at.desc()).paginate(
        page=page, 
        per_page=9, 
        error_out=False
    )
    
    # Domaines disponibles pour le filtre
    domains = db.session.query(PFAProject.domain).distinct().all()
    domains = [d[0] for d in domains if d[0]]
    
    return render_template('student/search_projects.html',
                         projects=projects,
                         query=query,
                         domain=domain,
                         domains=domains)

# routes/student_projects.py - AJOUTER cette fonction
@student_projects_bp.route('/nouveau-projet', methods=['GET', 'POST'])
@login_required
def new_project():
    """Créer un nouveau projet"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            title = request.form.get('title')
            description = request.form.get('description')
            domain = request.form.get('domain')
            technologies = request.form.get('technologies')
            github_url = request.form.get('github_url')
            demo_url = request.form.get('demo_url')
            
            # Créer le projet
            project = PFAProject(
                student_id=current_user.id,
                title=title,
                description=description,
                domain=domain,
                technologies=technologies,
                github_url=github_url,
                demo_url=demo_url,
                status='draft'
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('Projet créé avec succès!', 'success')
            return redirect(url_for('student_projects.project_detail', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du projet: {str(e)}', 'error')
    
    return render_template('student/new_project.html')