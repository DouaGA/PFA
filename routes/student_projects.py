from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, PFAProject, ProjectDocument, ProjectComment, User
from datetime import datetime

student_projects_bp = Blueprint('student_projects', __name__)

@student_projects_bp.route('/projets')
@login_required
def my_projects():
    """Afficher les projets de l'étudiant connecté"""
    if current_user.role != 'student':
        flash('Accès réservé aux étudiants', 'error')
        return redirect(url_for('public.home'))
    
    projects = PFAProject.query.filter_by(student_id=current_user.id).order_by(PFAProject.created_at.desc()).all()
    
    stats = {
        'total_projects': len(projects),
        'published_projects': len([p for p in projects if p.status == 'published']),
        'total_views': sum(p.views_count for p in projects),
        'total_likes': sum(p.likes_count for p in projects)
    }
    
    return render_template('student/my_projects.html', 
                         projects=projects, 
                         stats=stats)

@student_projects_bp.route('/projets/nouveau', methods=['GET', 'POST'])
@login_required
def new_project():
    """Créer un nouveau projet PFA"""
    if current_user.role != 'student':
        flash('Accès réservé aux étudiants', 'error')
        return redirect(url_for('public.home'))
    
    if request.method == 'POST':
        try:
            project = PFAProject(
                student_id=current_user.id,
                title=request.form['title'],
                description=request.form['description'],
                domain=request.form['domain'],
                technologies=request.form.get('technologies', ''),
                github_url=request.form.get('github_url', ''),
                demo_url=request.form.get('demo_url', ''),
                status=request.form.get('status', 'draft')
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('Projet créé avec succès!', 'success')
            return redirect(url_for('student_projects.my_projects'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erreur lors de la création du projet: ' + str(e), 'error')
    
    return render_template('student/new_project.html')

@student_projects_bp.route('/projets/<int:project_id>')
@login_required
def project_detail(project_id):
    """Détails d'un projet spécifique"""
    project = PFAProject.query.get_or_404(project_id)
    
    # Vérifier que l'utilisateur est propriétaire du projet
    if project.student_id != current_user.id and current_user.role != 'admin':
        flash('Accès non autorisé à ce projet', 'error')
        return redirect(url_for('student_projects.my_projects'))
    
    # Incrémenter les vues si ce n'est pas le propriétaire
    if current_user.id != project.student_id:
        project.increment_views()
    
    documents = ProjectDocument.query.filter_by(project_id=project_id).all()
    comments = ProjectComment.query.filter_by(project_id=project_id).order_by(ProjectComment.created_at.desc()).all()
    
    return render_template('student/project_detail.html',
                         project=project,
                         documents=documents,
                         comments=comments)

@student_projects_bp.route('/projets/<int:project_id>/commenter', methods=['POST'])
@login_required
def add_comment(project_id):
    """Ajouter un commentaire à un projet - CORRIGÉ"""
    project = PFAProject.query.get_or_404(project_id)
    
    # Empêcher de commenter son propre projet
    if current_user.id == project.student_id:
        flash('Vous ne pouvez pas commenter votre propre projet', 'warning')
        return redirect(url_for('student_projects.project_detail', project_id=project_id))
    
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Le commentaire ne peut pas être vide', 'error')
        return redirect(url_for('student_projects.project_detail', project_id=project_id))
    
    # Créer le commentaire
    comment = ProjectComment(
        project_id=project_id,
        user_id=current_user.id,
        content=content,
        is_helpful=request.form.get('is_helpful') == 'true'
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        flash('Commentaire ajouté avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors de l\'ajout du commentaire: ' + str(e), 'error')
    
    return redirect(url_for('student_projects.project_detail', project_id=project_id))

@student_projects_bp.route('/projets/rechercher')
@login_required
def search_projects():
    """Rechercher des projets PFA"""
    query = request.args.get('q', '')
    domain = request.args.get('domain', 'all')
    sort_by = request.args.get('sort_by', 'newest')
    
    # Construction de la requête de base
    projects_query = PFAProject.query.filter_by(status='published')
    
    # Filtre par recherche textuelle
    if query:
        projects_query = projects_query.filter(
            db.or_(
                PFAProject.title.ilike(f'%{query}%'),
                PFAProject.description.ilike(f'%{query}%'),
                PFAProject.technologies.ilike(f'%{query}%')
            )
        )
    
    # Filtre par domaine
    if domain != 'all':
        projects_query = projects_query.filter_by(domain=domain)
    
    # Tri
    if sort_by == 'popular':
        projects_query = projects_query.order_by(PFAProject.views_count.desc())
    elif sort_by == 'likes':
        projects_query = projects_query.order_by(PFAProject.likes_count.desc())
    else:  # newest
        projects_query = projects_query.order_by(PFAProject.created_at.desc())
    
    projects = projects_query.all()
    
    return render_template('student/search_projects.html',
                         projects=projects,
                         query=query,
                         domain=domain,
                         sort_by=sort_by)

# === ROUTES API CORRIGÉES ===

@student_projects_bp.route('/api/projets/<int:project_id>/like', methods=['POST'])
@login_required
def like_project(project_id):
    """API pour liker un projet - CORRIGÉ"""
    try:
        project = PFAProject.query.get_or_404(project_id)
        
        if current_user.id == project.student_id:
            return jsonify({
                'success': False, 
                'message': 'Vous ne pouvez pas liker votre propre projet'
            }), 400
        
        project.likes_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'likes_count': project.likes_count,
            'message': 'Projet liké avec succès!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erreur serveur lors du like: ' + str(e)
        }), 500

@student_projects_bp.route('/api/commentaires/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    """API pour liker un commentaire - CORRIGÉ"""
    try:
        comment = ProjectComment.query.get_or_404(comment_id)
        
        # Vérifier que l'utilisateur ne like pas son propre commentaire
        if current_user.id == comment.user_id:
            return jsonify({
                'success': False, 
                'message': 'Vous ne pouvez pas liker votre propre commentaire'
            }), 400
        
        comment.likes_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'likes_count': comment.likes_count,
            'message': 'Commentaire liké avec succès!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erreur serveur lors du like: ' + str(e)
        }), 500

@student_projects_bp.route('/projets/<int:project_id>/publier', methods=['POST'])
@login_required
def publish_project(project_id):
    """Publier un projet (changer le statut de brouillon à publié)"""
    project = PFAProject.query.filter_by(
        id=project_id, 
        student_id=current_user.id
    ).first_or_404()
    
    project.status = 'published'
    db.session.commit()
    
    flash('Projet publié avec succès!', 'success')
    return redirect(url_for('student_projects.my_projects'))