from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, User, Comment, PFAProject, ProjectComment, Notification
from datetime import datetime, timedelta
import json
from sqlalchemy import func, desc, or_

jury_bp = Blueprint('jury', __name__)

@jury_bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord jury enrichi"""
    if not current_user.is_jury():
        flash('Accès réservé aux membres du jury', 'error')
        return redirect(url_for('public.home'))
    
    # Statistiques avancées
    stats = {
        'total_projects': PFAProject.query.filter_by(status='published').count(),
        'projects_evaluated': Comment.query.filter_by(jury_id=current_user.id).count(),
        'total_comments': Comment.query.filter_by(jury_id=current_user.id).count(),
        'avg_recommendations': db.session.query(func.avg(Comment.recommendations))
            .filter_by(jury_id=current_user.id).scalar() or 0,
        'pending_evaluations': PFAProject.query.filter_by(status='published').count() - 
                             Comment.query.filter_by(jury_id=current_user.id).count(),
        'top_performing_domain': get_top_performing_domain(current_user.id)
    }
    
    # Projets récents à évaluer (avec intelligence)
    recent_projects = get_projects_for_evaluation(current_user.id)
    
    # Commentaires récents du jury
    recent_comments = Comment.query.filter_by(jury_id=current_user.id)\
        .order_by(Comment.created_at.desc()).limit(5).all()
    
    # Alertes et notifications
    alerts = get_evaluation_alerts(current_user.id)
    
    return render_template('jury/dashboard.html',
                         stats=stats,
                         recent_projects=recent_projects,
                         recent_comments=recent_comments,
                         alerts=alerts)

@jury_bp.route('/projets-a-evaluer')
@login_required
def projects_to_evaluate():
    """Liste intelligente des projets à évaluer"""
    if not current_user.is_jury():
        flash('Accès réservé aux membres du jury', 'error')
        return redirect(url_for('public.home'))
    
    # Algorithmes de recommandation de projets
    domain = request.args.get('domain', 'all')
    priority = request.args.get('priority', 'all')
    
    projects = get_smart_project_recommendations(current_user.id, domain, priority)
    
    return render_template('jury/projects_to_evaluate.html',
                         projects=projects,
                         domain=domain,
                         priority=priority)

@jury_bp.route('/projet/<int:project_id>/evaluation', methods=['GET', 'POST'])
@login_required
def evaluate_project(project_id):
    """Évaluation détaillée d'un projet avec grille de notation"""
    if not current_user.is_jury():
        flash('Accès réservé aux membres du jury', 'error')
        return redirect(url_for('public.home'))
    
    project = PFAProject.query.get_or_404(project_id)
    
    if request.method == 'POST':
        return submit_evaluation(project_id, request.form)
    
    # Vérifier si une évaluation existe déjà
    existing_evaluation = Comment.query.filter_by(
        jury_id=current_user.id,
        student_id=project.student_id,
        project_title=project.title
    ).first()
    
    return render_template('jury/evaluate_project.html',
                         project=project,
                         existing_evaluation=existing_evaluation)

@jury_bp.route('/mes-evaluations')
@login_required
def my_evaluations():
    """Historique et gestion des évaluations du jury"""
    if not current_user.is_jury():
        flash('Accès réservé aux membres du jury', 'error')
        return redirect(url_for('public.home'))
    
    filter_type = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'recent')
    
    evaluations = get_evaluations_with_filters(current_user.id, filter_type, sort_by)
    
    return render_template('jury/my_evaluations.html',
                         evaluations=evaluations,
                         filter_type=filter_type,
                         sort_by=sort_by)

@jury_bp.route('/api/evaluations/statistiques')
@login_required
def evaluation_statistics():
    """API pour les statistiques d'évaluation du jury"""
    if not current_user.is_jury():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    stats = get_jury_evaluation_stats(current_user.id)
    return jsonify(stats)

@jury_bp.route('/grille-evaluation')
@login_required
def evaluation_grid():
    """Grille d'évaluation standardisée"""
    if not current_user.is_jury():
        flash('Accès réservé aux membres du jury', 'error')
        return redirect(url_for('public.home'))
    
    return render_template('jury/evaluation_grid.html')

@jury_bp.route('/commentaire/<int:comment_id>/modifier', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    """Modifier une évaluation existante"""
    if not current_user.is_jury():
        flash('Accès réservé aux membres du jury', 'error')
        return redirect(url_for('public.home'))
    
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.jury_id != current_user.id:
        flash('Vous ne pouvez pas modifier cette évaluation', 'error')
        return redirect(url_for('jury.my_evaluations'))
    
    if request.method == 'POST':
        comment.content = request.form['content']
        comment.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Évaluation modifiée avec succès', 'success')
        return redirect(url_for('jury.my_evaluations'))
    
    student = User.query.get(comment.student_id)
    return render_template('jury/edit_comment.html',
                         comment=comment,
                         student_name=student.get_full_name())

@jury_bp.route('/commentaire/<int:comment_id>/supprimer', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Supprimer une évaluation"""
    if not current_user.is_jury():
        return jsonify({'success': False, 'message': 'Accès non autorisé'}), 403
    
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.jury_id != current_user.id:
        return jsonify({'success': False, 'message': 'Action non autorisée'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Évaluation supprimée'})

@jury_bp.route('/projets/suggestions')
@login_required
def project_suggestions():
    """Système de suggestions intelligentes de projets"""
    if not current_user.is_jury():
        flash('Accès réservé aux membres du jury', 'error')
        return redirect(url_for('public.home'))
    
    suggestions = get_ai_project_suggestions(current_user.id)
    
    return render_template('jury/project_suggestions.html',
                         suggestions=suggestions)

@jury_bp.route('/api/auto-complete', methods=['POST'])
@login_required
def auto_complete():
    """API d'auto-complétion pour les commentaires"""
    if not current_user.is_jury():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    data = request.get_json()
    prompt = data.get('prompt', '')
    
    # Simulation d'IA pour les suggestions de commentaires
    suggestions = generate_comment_suggestions(prompt)
    
    return jsonify({'suggestions': suggestions})

@jury_bp.route('/api/comment/<int:comment_id>')
@login_required
def get_comment_api(comment_id):
    """API pour récupérer un commentaire"""
    if not current_user.is_jury():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.jury_id != current_user.id:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    student = User.query.get(comment.student_id)
    
    return jsonify({
        'project_title': comment.project_title,
        'student_name': student.get_full_name(),
        'content': comment.content,
        'recommendations': comment.recommendations,
        'created_at': comment.created_at.strftime('%d/%m/%Y à %H:%M')
    })

# ================================
# FONCTIONS UTILITAIRES MANQUANTES
# ================================

def get_projects_for_evaluation(jury_id, limit=5):
    """Récupère les projets à évaluer pour un jury"""
    # Récupérer les titres des projets déjà évalués par ce jury
    evaluated_titles = [c.project_title for c in Comment.query.filter_by(jury_id=jury_id).all()]
    
    # Projets non évalués par ce jury
    projects = PFAProject.query.filter(
        PFAProject.status == 'published',
        ~PFAProject.title.in_(evaluated_titles)
    ).order_by(
        desc(PFAProject.likes_count),
        desc(PFAProject.views_count)
    ).limit(limit).all()
    
    return projects

def get_smart_project_recommendations(jury_id, domain='all', priority='all'):
    """Algorithmes de recommandation de projets"""
    # Récupérer les titres des projets déjà évalués
    evaluated_titles = [c.project_title for c in Comment.query.filter_by(jury_id=jury_id).all()]
    
    # Requête de base
    query = PFAProject.query.filter(
        PFAProject.status == 'published',
        ~PFAProject.title.in_(evaluated_titles)
    )
    
    # Filtrage par domaine
    if domain != 'all':
        query = query.filter(PFAProject.domain == domain)
    
    # Priorisation intelligente
    if priority == 'popular':
        query = query.order_by(desc(PFAProject.likes_count))
    elif priority == 'commented':
        # Trier par nombre de commentaires (approximation)
        query = query.order_by(desc(PFAProject.views_count))
    elif priority == 'recent':
        query = query.order_by(desc(PFAProject.created_at))
    elif priority == 'domain_expertise':
        # Prioriser les projets dans le domaine d'expertise du jury
        # Pour l'instant, on utilise les vues comme proxy
        query = query.order_by(desc(PFAProject.views_count))
    else:
        # Par défaut: mélange de popularité et récence
        query = query.order_by(desc(PFAProject.likes_count), desc(PFAProject.created_at))
    
    return query.limit(20).all()

def get_evaluation_alerts(jury_id):
    """Système d'alertes intelligentes"""
    alerts = []
    
    # Projets populaires non évalués
    evaluated_titles = [c.project_title for c in Comment.query.filter_by(jury_id=jury_id).all()]
    
    popular_unevaluated = PFAProject.query.filter(
        PFAProject.status == 'published',
        ~PFAProject.title.in_(evaluated_titles)
    ).order_by(desc(PFAProject.likes_count)).limit(3).all()
    
    for project in popular_unevaluated:
        alerts.append({
            'type': 'popular',
            'message': f'Projet populaire à évaluer: "{project.title}"',
            'project_id': project.id
        })
    
    # Évaluations en retard (projets créés il y a plus de 7 jours)
    week_ago = datetime.utcnow() - timedelta(days=7)
    old_unevaluated = PFAProject.query.filter(
        PFAProject.status == 'published',
        PFAProject.created_at < week_ago,
        ~PFAProject.title.in_(evaluated_titles)
    ).limit(2).all()
    
    for project in old_unevaluated:
        alerts.append({
            'type': 'urgent',
            'message': f'Évaluation en retard: "{project.title}"',
            'project_id': project.id
        })
    
    return alerts

def get_jury_evaluation_stats(jury_id):
    """Statistiques détaillées des évaluations du jury"""
    total_evaluations = Comment.query.filter_by(jury_id=jury_id).count()
    
    # Distribution par domaine (approximation basée sur les titres)
    domain_stats = db.session.query(
        Comment.project_title,
        func.count(Comment.id)
    ).filter_by(jury_id=jury_id).group_by(Comment.project_title).all()
    
    # Évolution mensuelle
    monthly_stats = db.session.query(
        func.strftime('%Y-%m', Comment.created_at).label('month'),
        func.count(Comment.id).label('count')
    ).filter_by(jury_id=jury_id)\
     .group_by('month')\
     .order_by(desc('month')).limit(6).all()
    
    return {
        'total_evaluations': total_evaluations,
        'domain_distribution': [{'domain': d[0], 'count': d[1]} for d in domain_stats],
        'monthly_evolution': [{'month': m[0], 'count': m[1]} for m in monthly_stats],
        'avg_recommendations': db.session.query(func.avg(Comment.recommendations))
            .filter_by(jury_id=jury_id).scalar() or 0
    }

def get_ai_project_suggestions(jury_id):
    """Suggestions de projets basées sur l'historique du jury"""
    # Récupérer les domaines des projets évalués par le jury
    jury_evaluations = Comment.query.filter_by(jury_id=jury_id).all()
    
    if not jury_evaluations:
        # Si pas d'historique, retourner des projets populaires
        return PFAProject.query.filter_by(status='published')\
            .order_by(desc(PFAProject.likes_count)).limit(4).all()
    
    # Extraire les domaines des projets évalués
    evaluated_titles = [e.project_title for e in jury_evaluations]
    evaluated_projects = PFAProject.query.filter(PFAProject.title.in_(evaluated_titles)).all()
    
    domain_counts = {}
    for project in evaluated_projects:
        domain_counts[project.domain] = domain_counts.get(project.domain, 0) + 1
    
    # Domaines préférés du jury (top 2)
    preferred_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:2]
    
    suggested_projects = []
    
    for domain, count in preferred_domains:
        # Projets dans ce domaine non encore évalués
        evaluated_titles_all = [c.project_title for c in Comment.query.filter_by(jury_id=jury_id).all()]
        
        projects = PFAProject.query.filter(
            PFAProject.domain == domain,
            PFAProject.status == 'published',
            ~PFAProject.title.in_(evaluated_titles_all)
        ).order_by(desc(PFAProject.likes_count)).limit(2).all()
        
        suggested_projects.extend(projects)
    
    # Si pas assez de suggestions, ajouter des projets populaires
    if len(suggested_projects) < 4:
        additional = PFAProject.query.filter(
            PFAProject.status == 'published',
            ~PFAProject.title.in_([p.title for p in suggested_projects] + evaluated_titles_all)
        ).order_by(desc(PFAProject.likes_count)).limit(4 - len(suggested_projects)).all()
        
        suggested_projects.extend(additional)
    
    return suggested_projects

def generate_comment_suggestions(prompt):
    """Génération de suggestions de commentaires (simulation IA)"""
    suggestions = []
    
    prompt_lower = prompt.lower()
    
    # Templates de commentaires basés sur le prompt
    if any(word in prompt_lower for word in ['interface', 'design', 'ui', 'ux']):
        suggestions.extend([
            "L'interface utilisateur est bien conçue mais pourrait bénéficier d'une meilleure hiérarchie visuelle.",
            "La navigation est intuitive, cependant quelques améliorations d'UX seraient bénéfiques.",
            "Le design est moderne et responsive, bravo pour l'attention portée aux détails."
        ])
    
    if any(word in prompt_lower for word in ['fonctionnalité', 'feature', 'fonction']):
        suggestions.extend([
            "Les fonctionnalités implémentées couvrent bien les besoins, mais certaines pourraient être optimisées.",
            "La gestion des données est efficace, cependant il manque des validations côté client.",
            "L'architecture technique est solide, suggestion d'ajouter des tests unitaires."
        ])
    
    if any(word in prompt_lower for word in ['performance', 'rapide', 'lent']):
        suggestions.extend([
            "Les performances globales sont bonnes, optimisation possible sur les requêtes base de données.",
            "Le temps de chargement est acceptable, mais pourrait être amélioré par la mise en cache.",
            "L'utilisation des ressources est optimale, bravo pour les optimisations techniques."
        ])
    
    if any(word in prompt_lower for word in ['code', 'programmation', 'technique']):
        suggestions.extend([
            "Le code est bien structuré et maintenable, bonne utilisation des design patterns.",
            "La documentation du code pourrait être améliorée pour faciliter la maintenance.",
            "Bonne séparation des préoccupations, l'architecture est scalable."
        ])
    
    # Suggestions générales si aucune correspondance
    if not suggestions:
        suggestions = [
            "Le projet démontre une bonne compréhension des concepts fondamentaux.",
            "L'approche méthodologique est solide, avec une planification efficace.",
            "Bonne communication des résultats et des limitations du projet."
        ]
    
    return suggestions[:3]  # Retourne max 3 suggestions

def submit_evaluation(project_id, form_data):
    """Soumission d'une évaluation complète"""
    project = PFAProject.query.get_or_404(project_id)
    
    # Vérifier si une évaluation existe déjà
    existing_evaluation = Comment.query.filter_by(
        jury_id=current_user.id,
        student_id=project.student_id,
        project_title=project.title
    ).first()
    
    if existing_evaluation:
        # Mise à jour de l'évaluation existante
        existing_evaluation.content = form_data.get('content', '')
        existing_evaluation.recommendations = form_data.get('recommendations', 0, type=int)
        existing_evaluation.updated_at = datetime.utcnow()
        comment = existing_evaluation
    else:
        # Création d'une nouvelle évaluation
        comment = Comment(
            student_id=project.student_id,
            jury_id=current_user.id,
            project_title=project.title,
            content=form_data.get('content', ''),
            recommendations=form_data.get('recommendations', 0, type=int)
        )
        db.session.add(comment)
    
    try:
        # Notification à l'étudiant
        notification = Notification(
            user_id=project.student_id,
            title=f'Nouvelle évaluation - {project.title}',
            message=f'Le jury {current_user.get_full_name()} a évalué votre projet',
            type='info'
        )
        db.session.add(notification)
        
        db.session.commit()
        flash('Évaluation enregistrée avec succès!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors de l\'enregistrement de l\'évaluation', 'error')
    
    return redirect(url_for('jury.dashboard'))

def get_evaluations_with_filters(jury_id, filter_type, sort_by):
    """Filtrage et tri des évaluations"""
    query = Comment.query.filter_by(jury_id=jury_id)
    
    # Filtres
    if filter_type == 'high_impact':
        query = query.filter(Comment.recommendations >= 10)
    elif filter_type == 'recent':
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Comment.created_at >= week_ago)
    
    # Tri
    if sort_by == 'recommendations':
        query = query.order_by(desc(Comment.recommendations))
    elif sort_by == 'recent':
        query = query.order_by(desc(Comment.created_at))
    else:  # alphabetic
        query = query.order_by(Comment.project_title)
    
    return query.all()

def get_top_performing_domain(jury_id):
    """Domaine où le jury est le plus performant (basé sur les recommandations)"""
    # Cette fonction est simplifiée - dans une vraie implémentation, 
    # on lierait les commentaires aux projets pour avoir les domaines
    evaluations = Comment.query.filter_by(jury_id=jury_id).all()
    
    if not evaluations:
        return "N/A"
    
    # Pour l'instant, on retourne le domaine du projet le plus recommandé
    best_evaluation = max(evaluations, key=lambda x: x.recommendations)
    
    # Trouver le projet correspondant
    project = PFAProject.query.filter_by(title=best_evaluation.project_title).first()
    
    return project.domain if project else "N/A"