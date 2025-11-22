from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db, User, Comment, PFAProject, ProjectComment, GuideStage
from datetime import datetime, timedelta

student_bp = Blueprint('student', __name__)
# routes/student.py - VERSION CORRIGÉE
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, PFAProject, ProjectComment
# SUPPRIMER l'import de GuideStage s'il cause des problèmes

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord étudiant - VERSION SÉCURISÉE"""
    try:
        # Calculer les statistiques
        stats = {
            'total_projects': PFAProject.query.filter_by(student_id=current_user.id).count(),
            'total_views': db.session.query(db.func.sum(PFAProject.views_count))
                          .filter_by(student_id=current_user.id).scalar() or 0,
            'total_likes': db.session.query(db.func.sum(PFAProject.likes_count))
                          .filter_by(student_id=current_user.id).scalar() or 0,
            'total_comments': ProjectComment.query.join(PFAProject)
                              .filter(PFAProject.student_id == current_user.id).count()
        }
        
        # Projets récents
        recent_projects = PFAProject.query.filter_by(student_id=current_user.id)\
                            .order_by(PFAProject.created_at.desc()).limit(5).all()
        
        # Projets populaires
        popular_projects = PFAProject.query.filter_by(status='published', is_public=True)\
                             .order_by(PFAProject.likes_count.desc()).limit(5).all()
        
        return render_template('student/dashboard.html',
                            stats=stats,
                            recent_projects=recent_projects,
                            popular_projects=popular_projects)
    
    except Exception as e:
        # En cas d'erreur, afficher un dashboard basique
        print(f"⚠️ Erreur dashboard: {e}")
        return render_template('student/dashboard.html',
                            stats={'total_projects': 0, 'total_views': 0, 'total_likes': 0, 'total_comments': 0},
                            recent_projects=[],
                            popular_projects=[])
    
@student_bp.route('/comment/<int:comment_id>/recommend', methods=['POST'])
@login_required
def recommend_comment(comment_id):
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if comment is not from current student
    if comment.student_id == current_user.id:
        return jsonify({'success': False, 'message': 'Vous ne pouvez pas recommander vos propres commentaires'}), 400
    
    # Increment recommendations
    comment.recommendations += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'recommendations': comment.recommendations
    })

@student_bp.route('/api/active-guide')
@login_required
def get_active_guide():
    """Récupère le guide de stage actif"""
    if current_user.role != 'student':
        return jsonify({'error': 'Non autorisé'}), 403
    
    active_guide = GuideStage.query.filter_by(is_active=True).first()
    
    if active_guide:
        return jsonify({
            'success': True,
            'guide': {
                'id': active_guide.id,
                'title': active_guide.title,
                'description': active_guide.description,
                'content': active_guide.content
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Aucun guide actif disponible'
        })
    
# routes/student.py - AJOUTER cette fonction
@student_bp.route('/nouveau-projet', methods=['GET', 'POST'])
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