from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import User, db
from werkzeug.security import generate_password_hash
from utils.validators import validate_email, validate_password, validate_username, validate_name

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('public.home'))
        
    # Récupérer les statistiques
    stats = {
        'total_students': User.query.filter_by(role='student').count(),
        'total_juries': User.query.filter_by(role='jury').count()
    }
    
    # Récupérer la liste des utilisateurs
    users = User.query.all()
    
    return render_template('admin/dashboard.html', stats=stats, users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('public.home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', 'student')
        
        errors = []
        if not validate_username(username):
            errors.append('Nom d\'utilisateur invalide (3+ caractères, lettres chiffres ou _).')
        if not validate_email(email):
            errors.append('Adresse email invalide.')
        if not validate_password(password):
            errors.append('Le mot de passe doit contenir au moins 8 caractères.')
        if first_name and not validate_name(first_name):
            errors.append('Prénom invalide.')
        if last_name and not validate_name(last_name):
            errors.append('Nom invalide.')
        if role not in ['admin', 'jury', 'student']:
            errors.append('Rôle invalide.')

        if User.query.filter_by(username=username).first():
            errors.append('Ce nom d\'utilisateur est déjà pris.')
        if User.query.filter_by(email=email).first():
            errors.append('Un compte avec cet email existe déjà.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.add_user'))

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True
        )
        user.password_hash = generate_password_hash(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Utilisateur {username} créé avec succès.', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/add_user.html')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('public.home'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', user.role)
        is_active = request.form.get('is_active') == 'on'

        errors = []
        if not validate_email(email):
            errors.append('Adresse email invalide.')
        if first_name and not validate_name(first_name):
            errors.append('Prénom invalide.')
        if last_name and not validate_name(last_name):
            errors.append('Nom invalide.')
        if role not in ['admin', 'jury', 'student']:
            errors.append('Rôle invalide.')

        # Check email conflict (only if email changed)
        if email != user.email:
            if User.query.filter_by(email=email).first():
                errors.append('Cet email est déjà utilisé par un autre compte.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))

        # Update user
        user.email = email
        user.first_name = first_name or None
        user.last_name = last_name or None
        user.role = role
        user.is_active = is_active

        db.session.commit()
        flash(f'Utilisateur {user.username} mis à jour avec succès.', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('public.home'))

    user = User.query.get_or_404(user_id)

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin.dashboard'))

    db.session.delete(user)
    db.session.commit()

    flash(f'Utilisateur {user.username} supprimé avec succès.', 'success')
    return redirect(url_for('admin.dashboard'))
