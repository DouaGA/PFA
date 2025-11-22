# models.py - VERSION CORRIGÉE SANS WARNINGS
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modèle utilisateur avec relations corrigées"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations CORRIGÉES sans overlaps
    comments_as_jury = db.relationship('Comment', 
                                      foreign_keys='Comment.jury_id', 
                                      backref='jury_user', 
                                      lazy='dynamic')
    
    comments_as_student = db.relationship('Comment', 
                                         foreign_keys='Comment.student_id', 
                                         backref='student_user', 
                                         lazy='dynamic')
    
    pfa_projects = db.relationship('PFAProject', 
                                  foreign_keys='PFAProject.student_id', 
                                  backref='project_student', 
                                  lazy='dynamic')
    
    project_comments = db.relationship('ProjectComment', 
                                      foreign_keys='ProjectComment.user_id', 
                                      backref='comment_author', 
                                      lazy='dynamic')
    
    notifications = db.relationship('Notification', 
                                   foreign_keys='Notification.user_id', 
                                   backref='user', 
                                   lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_jury(self):
        return self.role == 'jury'
    
    def is_student(self):
        return self.role == 'student'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Comment(db.Model):
    """Modèle commentaire avec foreign keys explicites"""
    
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    jury_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    project_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    recommendations = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index composites
    __table_args__ = (
        db.Index('idx_student_created', 'student_id', 'created_at'),
        db.Index('idx_jury_created', 'jury_id', 'created_at'),
        db.Index('idx_recommendations', 'recommendations', 'created_at'),
    )

    def increment_recommendations(self):
        self.recommendations += 1
        db.session.commit()
    
    def get_truncated_content(self, length=150):
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + '...'
    
    def __repr__(self):
        return f'<Comment {self.id} - {self.project_title}>'

class PFAProject(db.Model):
    """Modèle pour les projets PFA des étudiants"""
    
    __tablename__ = 'pfaprojects'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    technologies = db.Column(db.String(300), nullable=True)
    github_url = db.Column(db.String(500), nullable=True)
    demo_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='draft')
    is_public = db.Column(db.Boolean, default=True)
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ai_analysis_data = db.Column(db.JSON, nullable=True)
    ai_adaptability_score = db.Column(db.Integer, default=0)
    ai_analysis_date = db.Column(db.DateTime, nullable=True)
    has_ai_analysis = db.Column(db.Boolean, default=False)
    
    # Relations CORRIGÉES
    documents = db.relationship('ProjectDocument', 
                               backref='project', 
                               lazy='dynamic', 
                               cascade='all, delete-orphan')
    
    comments = db.relationship('ProjectComment', 
                              backref='project', 
                              lazy='dynamic', 
                              cascade='all, delete-orphan')
    
    def increment_views(self):
        self.views_count += 1
        db.session.commit()
    
    def increment_likes(self):
        self.likes_count += 1
        db.session.commit()
    
    def get_documents_count(self):
        return self.documents.count()
    
    def get_comments_count(self):
        return self.comments.count()
    
    def __repr__(self):
        return f'<PFAProject {self.id} - {self.title}>'

class GuideStage(db.Model):
    """Modèle pour les guides de structure des rapports"""
    
    __tablename__ = 'guide_stages'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    domain = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation
    creator = db.relationship('User', foreign_keys=[created_by])

class ProjectComment(db.Model):
    """Modèle pour les commentaires sur les projets PFA"""
    
    __tablename__ = 'project_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('pfaprojects.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_helpful = db.Column(db.Boolean, default=True)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def increment_likes(self):
        self.likes_count += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<ProjectComment {self.id} - Projet {self.project_id}>'

class ProjectDocument(db.Model):
    """Modèle pour les documents des projets"""
    
    __tablename__ = 'project_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('pfaprojects.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    downloads_count = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def increment_downloads(self):
        self.downloads_count += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<ProjectDocument {self.id} - {self.title}>'

class Notification(db.Model):
    """Modèle notification"""
    
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(50), default='info')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def mark_as_read(self):
        self.is_read = True
        db.session.commit()
    
    def __repr__(self):
        return f'<Notification {self.id} - {self.title}>'

def init_db():
    db.create_all()
    print("✓ Base de données initialisée")

def drop_db():
    db.drop_all()
    print("✓ Base de données supprimée")

# Dans models.py - AJOUTER CETTE CLASSE
class UploadedGuide(db.Model):
    """Modèle pour les guides uploadés par les utilisateurs"""
    
    __tablename__ = 'uploaded_guides'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    domain = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation
    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<UploadedGuide {self.id} - {self.title}>'