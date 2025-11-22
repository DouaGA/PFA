# routes/guide_routes.py - SYSTÈME COMPLET DE GESTION DES GUIDES
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from models import db, GuideStage
import json
import os
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

guide_bp = Blueprint('guide', __name__)

@guide_bp.route('/guides')
@login_required
def list_guides():
    """Lister tous les guides"""
    if not current_user.is_admin():
        flash('❌ Accès réservé aux administrateurs', 'error')
        return redirect(url_for('student.dashboard'))
    
    guides = GuideStage.query.all()
    return render_template('admin/guides.html', guides=guides)

@guide_bp.route('/guide/new', methods=['GET', 'POST'])
@login_required
def new_guide():
    """Créer un nouveau guide"""
    if not current_user.is_admin():
        flash('❌ Accès réservé aux administrateurs', 'error')
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            domain = request.form.get('domain')
            description = request.form.get('description')
            
            # Structure du guide
            guide_structure = {
                'required_sections': request.form.getlist('required_sections'),
                'optional_sections': request.form.getlist('optional_sections'),
                'section_patterns': {},
                'evaluation_criteria': {
                    'structure_weight': float(request.form.get('structure_weight', 0.4)),
                    'technical_weight': float(request.form.get('technical_weight', 0.3)),
                    'content_weight': float(request.form.get('content_weight', 0.3))
                }
            }
            
            # Récupérer les patterns pour chaque section
            for section in guide_structure['required_sections'] + guide_structure['optional_sections']:
                pattern = request.form.get(f'pattern_{section}', f'\\b{section}\\b')
                if pattern:
                    guide_structure['section_patterns'][section] = pattern
            
            guide = GuideStage(
                title=title,
                domain=domain,
                description=description,
                content=json.dumps(guide_structure, ensure_ascii=False),
                created_by=current_user.id
            )
            
            db.session.add(guide)
            db.session.commit()
            
            flash('✅ Guide créé avec succès!', 'success')
            return redirect(url_for('guide.list_guides'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erreur: {str(e)}', 'error')
    
    # Sections prédéfinies
    default_sections = [
        'introduction', 'methodologie', 'resultats', 'conclusion', 
        'bibliographie', 'abstract', 'annexes', 'remerciements'
    ]
    
    return render_template('admin/new_guide.html', sections=default_sections)

@guide_bp.route('/guide/<int:guide_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_guide(guide_id):
    """Modifier un guide existant"""
    if not current_user.is_admin():
        flash('❌ Accès réservé aux administrateurs', 'error')
        return redirect(url_for('student.dashboard'))
    
    guide = GuideStage.query.get_or_404(guide_id)
    
    if request.method == 'POST':
        try:
            guide.title = request.form.get('title')
            guide.domain = request.form.get('domain')
            guide.description = request.form.get('description')
            guide.is_active = request.form.get('is_active') == 'on'
            
            # Mettre à jour la structure
            guide_structure = json.loads(guide.content)
            guide_structure['required_sections'] = request.form.getlist('required_sections')
            guide_structure['optional_sections'] = request.form.getlist('optional_sections')
            
            # Mettre à jour les patterns
            for section in guide_structure['required_sections'] + guide_structure['optional_sections']:
                pattern = request.form.get(f'pattern_{section}', f'\\b{section}\\b')
                guide_structure['section_patterns'][section] = pattern
            
            guide.content = json.dumps(guide_structure, ensure_ascii=False)
            db.session.commit()
            
            flash('✅ Guide modifié avec succès!', 'success')
            return redirect(url_for('guide.list_guides'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erreur: {str(e)}', 'error')
    
    guide_data = json.loads(guide.content)
    default_sections = [
        'introduction', 'methodologie', 'resultats', 'conclusion', 
        'bibliographie', 'abstract', 'annexes', 'remerciements'
    ]
    
    return render_template('admin/edit_guide.html', 
                         guide=guide, 
                         guide_data=guide_data, 
                         sections=default_sections)

@guide_bp.route('/guide/<int:guide_id>/delete', methods=['POST'])
@login_required
def delete_guide(guide_id):
    """Supprimer un guide"""
    if not current_user.is_admin():
        flash('❌ Accès réservé aux administrateurs', 'error')
        return redirect(url_for('student.dashboard'))
    
    guide = GuideStage.query.get_or_404(guide_id)
    
    try:
        db.session.delete(guide)
        db.session.commit()
        flash('✅ Guide supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erreur: {str(e)}', 'error')
    
    return redirect(url_for('guide.list_guides'))

@guide_bp.route('/api/guides/<domain>')
@login_required
def get_guides_by_domain(domain):
    """API pour récupérer les guides par domaine"""
    guides = GuideStage.query.filter_by(domain=domain, is_active=True).all()
    
    guides_data = []
    for guide in guides:
        guides_data.append({
            'id': guide.id,
            'title': guide.title,
            'domain': guide.domain,
            'description': guide.description,
            'structure': json.loads(guide.content) if guide.content else {}
        })
    
    return jsonify({'success': True, 'guides': guides_data})

@guide_bp.route('/guide/<int:guide_id>/download')
@login_required
def download_guide(guide_id):
    """Télécharger un guide en PDF"""
    guide = GuideStage.query.get_or_404(guide_id)
    guide_data = json.loads(guide.content)
    
    # Créer le PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph(f"GUIDE: {guide.title}", title_style))
    
    # Informations
    story.append(Paragraph(f"<b>Domaine:</b> {guide.domain}", styles['Normal']))
    story.append(Paragraph(f"<b>Description:</b> {guide.description}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Sections requises
    story.append(Paragraph("SECTIONS REQUISES:", styles['Heading2']))
    for section in guide_data.get('required_sections', []):
        story.append(Paragraph(f"• {section.title()}", styles['Normal']))
    
    story.append(Spacer(1, 15))
    
    # Sections optionnelles
    if guide_data.get('optional_sections'):
        story.append(Paragraph("SECTIONS OPTIONNELLES:", styles['Heading2']))
        for section in guide_data['optional_sections']:
            story.append(Paragraph(f"• {section.title()}", styles['Normal']))
    
    story.append(Spacer(1, 15))
    
    # Critères d'évaluation
    eval_criteria = guide_data.get('evaluation_criteria', {})
    story.append(Paragraph("CRITÈRES D'ÉVALUATION:", styles['Heading2']))
    story.append(Paragraph(f"Structure: {eval_criteria.get('structure_weight', 0.4) * 100}%", styles['Normal']))
    story.append(Paragraph(f"Technique: {eval_criteria.get('technical_weight', 0.3) * 100}%", styles['Normal']))
    story.append(Paragraph(f"Contenu: {eval_criteria.get('content_weight', 0.3) * 100}%", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"guide_{guide.title.replace(' ', '_')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')