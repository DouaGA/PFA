from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from models import User, db
from utils.validators import validate_email, validate_password, validate_username, validate_name

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        if not email or not password:
            flash('Veuillez saisir une adresse email et un mot de passe.', 'danger')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            flash('Connexion réussie !', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('public.home'))
        else:
            flash('Adresse email ou mot de passe incorrect.', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('public.home'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', 'student')

        # Validation
        errors = []
        if not validate_username(username):
            errors.append('Nom d\'utilisateur invalide (3+ caractères, lettres chiffres ou _).')
        if not validate_email(email):
            errors.append('Adresse email invalide.')
        if not validate_password(password):
            errors.append('Le mot de passe doit contenir au moins 8 caractères.')
        if password != confirm_password:
            errors.append('Les mots de passe ne correspondent pas.')
        if first_name and not validate_name(first_name):
            errors.append('Prénom invalide.')
        if last_name and not validate_name(last_name):
            errors.append('Nom invalide.')

        if User.query.filter_by(username=username).first():
            errors.append('Ce nom d\'utilisateur est déjà pris.')
        if User.query.filter_by(email=email).first():
            errors.append('Un compte avec cet email existe déjà.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return redirect(url_for('auth.register'))

        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name or None,
            last_name=last_name or None,
            role=role,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Inscription réussie. Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if email and not validate_email(email):
            errors.append('Adresse email invalide.')
        if first_name and not validate_name(first_name):
            errors.append('Prénom invalide.')
        if last_name and not validate_name(last_name):
            errors.append('Nom invalide.')
        if password:
            if not validate_password(password):
                errors.append('Le mot de passe doit contenir au moins 8 caractères.')
            if password != confirm_password:
                errors.append('Les mots de passe ne correspondent pas.')

        # Check email conflict
        if email and email != current_user.email:
            if User.query.filter_by(email=email).first():
                errors.append('Cet email est déjà utilisé par un autre compte.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return redirect(url_for('auth.edit_profile'))

        # Apply changes
        if email:
            current_user.email = email
        current_user.first_name = first_name or None
        current_user.last_name = last_name or None
        if password:
            current_user.set_password(password)

        db.session.commit()
        flash('Profil mis à jour avec succès.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/edit_profile.html', user=current_user)
