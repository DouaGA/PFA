from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
student_bp = Blueprint('student', __name__)
from models import db, User, Comment, PFAProject, ProjectComment
from datetime import datetime, timedelta

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':
        return redirect(url_for('public.home'))
    
    # Statistiques des projets
    projects = PFAProject.query.filter_by(student_id=current_user.id).all()
    
    stats = {
        'total_projects': len(projects),
        'total_views': sum(p.views_count for p in projects),
        'total_likes': sum(p.likes_count for p in projects),
        'total_comments': ProjectComment.query.filter_by(project_id=current_user.id).count()
    }
    
    # Projets récents (limité à 5)
    recent_projects = PFAProject.query.filter_by(student_id=current_user.id)\
                                     .order_by(PFAProject.created_at.desc())\
                                     .limit(5).all()
    
    # Projets populaires (tous les projets publics)
    popular_projects = PFAProject.query.filter_by(status='published', is_public=True)\
                                      .order_by(PFAProject.likes_count.desc())\
                                      .limit(5).all()
    
    return render_template('student/dashboard.html',
                         stats=stats,
                         recent_projects=recent_projects,
                         popular_projects=popular_projects)

# ... (garder les autres fonctions existantes)
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