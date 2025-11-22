from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import current_user
from models import db, User, Comment, PFAProject, ProjectComment
from datetime import datetime, timedelta
import json
from sqlalchemy import func, desc, or_

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def home():
    """Page d'accueil enrichie avec statistiques en temps réel"""
    # Statistiques globales
    stats = get_global_statistics()
    
    # Projets populaires
    popular_projects = PFAProject.query.filter_by(status='published')\
        .order_by(desc(PFAProject.likes_count))\
        .limit(6).all()
    
    # Commentaires les plus recommandés
    top_comments = Comment.query.filter_by(is_public=True)\
        .order_by(desc(Comment.recommendations))\
        .limit(4).all()
    
    # Derniers projets publiés
    recent_projects = PFAProject.query.filter_by(status='published')\
        .order_by(desc(PFAProject.created_at))\
        .limit(4).all()
    
    return render_template('public/home.html',
                         stats=stats,
                         popular_projects=popular_projects,
                         top_comments=top_comments,
                         recent_projects=recent_projects)

@public_bp.route('/classement')
def ranking():
    """Classement avancé avec multiples critères"""
    period = request.args.get('period', 'all')
    category = request.args.get('category', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Récupération avec pagination
    pagination = get_ranking_data(period, category, page, per_page)
    top_comments = pagination.items
    
    # Statistiques
    stats = get_ranking_statistics()
    
    return render_template('public/ranking.html',
                         top_comments=top_comments,
                         stats=stats,
                         period=period,
                         category=category,
                         page=page,
                         pages=pagination.pages)

@public_bp.route('/explorer')
def explore():
    """Page d'exploration avancée des projets"""
    domain = request.args.get('domain', 'all')
    technology = request.args.get('technology', '')
    sort_by = request.args.get('sort', 'recent')
    search_query = request.args.get('q', '')
    
    # Filtrage intelligent
    projects = explore_projects(domain, technology, sort_by, search_query)
    
    # Statistiques de filtrage
    filter_stats = get_exploration_statistics()
    
    return render_template('public/explore.html',
                         projects=projects,
                         domain=domain,
                         technology=technology,
                         sort_by=sort_by,
                         search_query=search_query,
                         filter_stats=filter_stats)

@public_bp.route('/projets/<int:project_id>')
def project_detail_public(project_id):
    """Détail d'un projet accessible publiquement"""
    project = PFAProject.query.get_or_404(project_id)
    
    if project.status != 'published' and (not current_user.is_authenticated or current_user.id != project.student_id):
        flash('Ce projet n\'est pas accessible publiquement', 'error')
        return redirect(url_for('public.explore'))
    
    # Incrémenter les vues
    project.increment_views()
    
    # Documents publics
    documents = project.documents.filter_by(is_public=True).all()
    
    # Commentaires publics
    comments = project.comments.order_by(desc(ProjectComment.created_at)).all()
    
    # Projets similaires
    similar_projects = get_similar_projects(project)
    
    return render_template('public/project_detail.html',
                         project=project,
                         documents=documents,
                         comments=comments,
                         similar_projects=similar_projects)

@public_bp.route('/jurys')
def juries():
    """Page de présentation des jurys"""
    juries_list = User.query.filter_by(role='jury', is_active=True).all()
    
    # Statistiques des jurys
    jury_stats = get_jury_statistics()
    
    return render_template('public/juries.html',
                         juries=juries_list,
                         jury_stats=jury_stats)

@public_bp.route('/stats')
def statistics():
    """Page de statistiques détaillées"""
    stats = get_detailed_statistics()
    return render_template('public/statistics.html', stats=stats)

@public_bp.route('/recherche-avancee')
def advanced_search():
    """Page de recherche avancée"""
    return render_template('public/advanced_search.html')

@public_bp.route('/api/trending-projects')
def trending_projects_api():
    """API pour les projets tendance"""
    trending = get_trending_projects()
    return jsonify(trending)

@public_bp.route('/api/global-stats')
def global_stats_api():
    """API pour les statistiques globales"""
    stats = get_global_statistics()
    return jsonify(stats)

# ================================
# FONCTIONS UTILITAIRES CORRIGÉES
# ================================

def get_ranking_data(period='all', category='all', page=1, per_page=10):
    """Récupère les données de classement avec pagination"""
    query = Comment.query.filter_by(is_public=True)
    
    # Filtrage temporel
    if period == 'week':
        last_week = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Comment.created_at >= last_week)
    elif period == 'month':
        last_month = datetime.utcnow() - timedelta(days=30)
        query = query.filter(Comment.created_at >= last_month)
    elif period == 'year':
        last_year = datetime.utcnow() - timedelta(days=365)
        query = query.filter(Comment.created_at >= last_year)
    
    # Filtrage par catégorie
    if category != 'all':
        category_keywords = {
            'web': ['web', 'site', 'application web'],
            'mobile': ['mobile', 'application mobile'],
            'ai': ['ai', 'intelligence', 'machine learning'],
            'data': ['data', 'analyse', 'big data']
        }
        
        if category in category_keywords:
            keywords = category_keywords[category]
            conditions = [Comment.project_title.ilike(f'%{keyword}%') for keyword in keywords]
            query = query.filter(or_(*conditions))
    
    # Pagination
    pagination = query.order_by(desc(Comment.recommendations)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return pagination

def get_global_statistics():
    """Statistiques globales de la plateforme"""
    return {
        'total_projects': PFAProject.query.filter_by(status='published').count(),
        'total_students': User.query.filter_by(role='student', is_active=True).count(),
        'total_juries': User.query.filter_by(role='jury', is_active=True).count(),
        'total_comments': Comment.query.filter_by(is_public=True).count(),
        'total_recommendations': db.session.query(func.sum(Comment.recommendations)).scalar() or 0,
        'avg_project_rating': db.session.query(func.avg(Comment.recommendations)).scalar() or 0,
        'active_this_week': get_active_users_this_week()
    }

def get_ranked_comments(period, category, sort_by):
    """Système de classement intelligent"""
    query = Comment.query.filter_by(is_public=True)
    
    # Filtrage temporel
    if period == 'week':
        last_week = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Comment.created_at >= last_week)
    elif period == 'month':
        last_month = datetime.utcnow() - timedelta(days=30)
        query = query.filter(Comment.created_at >= last_month)
    elif period == 'year':
        last_year = datetime.utcnow() - timedelta(days=365)
        query = query.filter(Comment.created_at >= last_year)
    
    # Filtrage par catégorie (basé sur les mots-clés du titre)
    if category != 'all':
        category_keywords = {
            'web': ['web', 'site', 'application web', 'développement web'],
            'mobile': ['mobile', 'application mobile', 'android', 'ios'],
            'ai': ['ai', 'intelligence', 'machine learning', 'deep learning'],
            'data': ['data', 'analyse', 'big data', 'data science']
        }
        
        if category in category_keywords:
            keywords = category_keywords[category]
            conditions = [Comment.project_title.ilike(f'%{keyword}%') for keyword in keywords]
            query = query.filter(or_(*conditions))
    
    # Tri
    if sort_by == 'recent':
        query = query.order_by(desc(Comment.created_at))
    elif sort_by == 'engagement':
        # Score d'engagement basé sur les recommandations et la récence
        query = query.order_by(desc(Comment.recommendations))
    else:  # recommendations (par défaut)
        query = query.order_by(desc(Comment.recommendations))
    
    return query.limit(50).all()

def get_ranking_statistics():
    """Statistiques pour la page de classement"""
    return {
        'total_comments': Comment.query.filter_by(is_public=True).count(),
        'total_recommendations': db.session.query(func.sum(Comment.recommendations)).scalar() or 0,
        'active_juries': User.query.filter_by(role='jury', is_active=True).count()
    }

def get_top_juries():
    """Classement des jurys les plus actifs - CORRIGÉ avec relations explicites"""
    return db.session.query(
        User,
        func.count(Comment.id).label('comments_count'),
        func.avg(Comment.recommendations).label('avg_recommendations')
    ).join(Comment, User.id == Comment.jury_id)\
     .filter(User.role == 'jury', User.is_active == True)\
     .group_by(User.id)\
     .order_by(desc('comments_count'))\
     .limit(10).all()

def explore_projects(domain, technology, sort_by, search_query):
    """Exploration avancée des projets"""
    query = PFAProject.query.filter_by(status='published')
    
    # Filtrage par domaine
    if domain != 'all':
        query = query.filter(PFAProject.domain == domain)
    
    # Filtrage par technologie
    if technology:
        query = query.filter(PFAProject.technologies.ilike(f'%{technology}%'))
    
    # Recherche textuelle
    if search_query:
        query = query.filter(
            or_(
                PFAProject.title.ilike(f'%{search_query}%'),
                PFAProject.description.ilike(f'%{search_query}%'),
                PFAProject.technologies.ilike(f'%{search_query}%')
            )
        )
    
    # Tri
    if sort_by == 'popular':
        query = query.order_by(desc(PFAProject.likes_count))
    elif sort_by == 'views':
        query = query.order_by(desc(PFAProject.views_count))
    elif sort_by == 'recent':
        query = query.order_by(desc(PFAProject.created_at))
    else:  # trending (mix popularité et récence)
        query = query.order_by(
            desc(PFAProject.likes_count + PFAProject.views_count),
            desc(PFAProject.created_at)
        )
    
    return query.limit(48).all()

def get_exploration_statistics():
    """Statistiques pour la page d'exploration"""
    return {
        'domains': get_domain_distribution(),
        'technologies': get_technology_cloud(),
        'active_projects': PFAProject.query.filter_by(status='published').count()
    }

def get_domain_distribution():
    """Distribution des projets par domaine"""
    return db.session.query(
        PFAProject.domain,
        func.count(PFAProject.id).label('count')
    ).filter_by(status='published')\
     .group_by(PFAProject.domain)\
     .all()

def get_technology_cloud():
    """Nuage de technologies les plus populaires"""
    all_technologies = []
    projects = PFAProject.query.filter_by(status='published').all()
    
    for project in projects:
        if project.technologies:
            tech_list = [tech.strip() for tech in project.technologies.split(',')]
            all_technologies.extend(tech_list)
    
    # Compter les occurrences
    from collections import Counter
    tech_counter = Counter(all_technologies)
    
    return tech_counter.most_common(20)

def get_similar_projects(project):
    """Recommandation de projets similaires"""
    similar = PFAProject.query.filter(
        PFAProject.status == 'published',
        PFAProject.domain == project.domain,
        PFAProject.id != project.id
    ).order_by(desc(PFAProject.likes_count)).limit(4).all()
    
    # Si pas assez de projets dans le même domaine, élargir la recherche
    if len(similar) < 4:
        additional = PFAProject.query.filter(
            PFAProject.status == 'published',
            PFAProject.id != project.id,
            ~PFAProject.id.in_([p.id for p in similar])
        ).order_by(desc(PFAProject.likes_count)).limit(4 - len(similar)).all()
        similar.extend(additional)
    
    return similar

def get_jury_statistics():
    """Statistiques des jurys"""
    return {
        'total_juries': User.query.filter_by(role='jury', is_active=True).count(),
        'avg_comments_per_jury': db.session.query(
            func.count(Comment.id) / func.count(User.id.distinct())
        ).select_from(Comment).join(User, User.id == Comment.jury_id).filter(User.role == 'jury').scalar() or 0,
        'most_active_jury': User.query.filter_by(role='jury')\
            .join(Comment, User.id == Comment.jury_id)\
            .group_by(User.id).order_by(desc(func.count(Comment.id))).first()
    }

def get_detailed_statistics():
    """Statistiques détaillées de la plateforme"""
    # Évolution mensuelle
    monthly_stats = db.session.query(
        func.strftime('%Y-%m', PFAProject.created_at).label('month'),
        func.count(PFAProject.id).label('projects_count')
    ).filter_by(status='published')\
     .group_by('month')\
     .order_by(desc('month')).limit(12).all()
    
    # Top domaines
    top_domains = db.session.query(
        PFAProject.domain,
        func.count(PFAProject.id).label('count'),
        func.avg(PFAProject.likes_count).label('avg_likes')
    ).filter_by(status='published')\
     .group_by(PFAProject.domain)\
     .order_by(desc('count')).limit(5).all()
    
    return {
        'monthly_evolution': [{'month': m[0], 'count': m[1]} for m in monthly_stats],
        'top_domains': [{'domain': d[0], 'count': d[1], 'avg_likes': d[2] or 0} for d in top_domains],
        'engagement_metrics': get_engagement_metrics()
    }

def get_engagement_metrics():
    """Métriques d'engagement"""
    return {
        'avg_project_views': db.session.query(func.avg(PFAProject.views_count)).scalar() or 0,
        'avg_project_likes': db.session.query(func.avg(PFAProject.likes_count)).scalar() or 0,
        'avg_comments_per_project': db.session.query(
            func.count(ProjectComment.id) / func.count(PFAProject.id.distinct())
        ).scalar() or 0
    }

def get_active_users_this_week():
    """Utilisateurs actifs cette semaine"""
    last_week = datetime.utcnow() - timedelta(days=7)
    
    # Étudiants ayant publié des projets
    active_students = User.query.join(PFAProject, User.id == PFAProject.student_id)\
        .filter(
            User.role == 'student',
            PFAProject.created_at >= last_week
        ).distinct().count()
    
    # Jurys ayant commenté
    active_juries = User.query.join(Comment, User.id == Comment.jury_id)\
        .filter(
            User.role == 'jury',
            Comment.created_at >= last_week
        ).distinct().count()
    
    return active_students + active_juries

def get_trending_projects():
    """Projets tendance (mix popularité et récence)"""
    trending = PFAProject.query.filter_by(status='published')\
        .order_by(
            desc(PFAProject.likes_count + PFAProject.views_count),
            desc(PFAProject.created_at)
        ).limit(8).all()
    
    return [{
        'id': p.id,
        'title': p.title,
        'domain': p.domain,
        'likes_count': p.likes_count,
        'views_count': p.views_count,
        'student_name': p.project_student.get_full_name()
    } for p in trending]