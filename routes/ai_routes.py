# routes/ai_routes.py - VERSION COMPLÈTE AVEC UPLOAD DE GUIDES
import os
import re
import json
import math
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from datetime import datetime
from models import db, PFAProject, ProjectDocument, GuideStage, UploadedGuide
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

ai_bp = Blueprint('ai', __name__)

# ========== ROUTES UPLOAD GUIDES ==========

@ai_bp.route('/upload-guide', methods=['GET', 'POST'])
@ai_bp.route('/upload-guide/<int:project_id>', methods=['GET', 'POST'])
@login_required
def upload_guide(project_id=None):
    """Uploader un guide personnalisé"""
    if request.method == 'POST':
        try:
            if 'guide_file' not in request.files:
                flash('❌ Aucun fichier sélectionné', 'error')
                return redirect(request.url)
            
            file = request.files['guide_file']
            if file.filename == '':
                flash('❌ Aucun fichier sélectionné', 'error')
                return redirect(request.url)
            
            # Vérifier l'extension
            allowed_extensions = {'json', 'txt', 'pdf'}
            file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            
            if file_extension not in allowed_extensions:
                flash('❌ Format non supporté. Utilisez JSON, TXT ou PDF.', 'error')
                return redirect(request.url)
            
            # Sauvegarder le fichier
            upload_folder = os.path.join('static', 'uploads', 'guides')
            os.makedirs(upload_folder, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # Créer l'entrée en base
            guide = UploadedGuide(
                user_id=current_user.id,
                title=request.form.get('title', f"Guide {timestamp}"),
                description=request.form.get('description', ''),
                file_path=filename,
                file_name=file.filename,
                file_size=os.path.getsize(file_path),
                domain=request.form.get('domain', 'general')
            )
            
            db.session.add(guide)
            db.session.commit()
            
            flash('✅ Guide uploadé avec succès!', 'success')
            
            if project_id:
                return redirect(url_for('ai.guided_analysis', project_id=project_id))
            else:
                return redirect(url_for('ai.my_guides'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erreur lors de l\'upload: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('student/upload_guide.html', project_id=project_id)

@ai_bp.route('/my-guides')
@login_required
def my_guides():
    """Mes guides uploadés"""
    guides = UploadedGuide.query.filter_by(user_id=current_user.id).order_by(UploadedGuide.uploaded_at.desc()).all()
    return render_template('student/my_guides.html', guides=guides)

@ai_bp.route('/delete-guide/<int:guide_id>', methods=['POST'])
@login_required
def delete_guide(guide_id):
    """Supprimer un guide"""
    guide = UploadedGuide.query.filter_by(id=guide_id, user_id=current_user.id).first_or_404()
    
    try:
        file_path = os.path.join('static', 'uploads', 'guides', guide.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.session.delete(guide)
        db.session.commit()
        flash('✅ Guide supprimé!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erreur suppression: {str(e)}', 'error')
    
    return redirect(url_for('ai.my_guides'))

# ========== ROUTES ANALYSE ==========

@ai_bp.route('/analysis/<int:project_id>')
@login_required
def analysis_page(project_id):
    """Page analyse principale"""
    project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
    document = ProjectDocument.query.filter_by(project_id=project_id).order_by(ProjectDocument.uploaded_at.desc()).first()
    uploaded_guides = UploadedGuide.query.filter_by(user_id=current_user.id, is_active=True).all()
    default_guides = GuideStage.query.filter_by(domain=project.domain, is_active=True).all()
    
    return render_template('student/ai_analysis.html', 
                         project=project, 
                         document=document,
                         uploaded_guides=uploaded_guides,
                         default_guides=default_guides)

@ai_bp.route('/guided-analysis/<int:project_id>', methods=['GET', 'POST'])
@login_required
def guided_analysis(project_id):
    """Analyse avec guide"""
    if request.method == 'GET':
        project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
        document = ProjectDocument.query.filter_by(project_id=project_id).order_by(ProjectDocument.uploaded_at.desc()).first()
        uploaded_guides = UploadedGuide.query.filter_by(user_id=current_user.id, is_active=True).all()
        
        if not document:
            flash('❌ Uploader un PDF d\'abord', 'error')
            return redirect(url_for('ai.analysis_page', project_id=project_id))
        
        return render_template('student/guided_analysis_selection.html',
                             project=project,
                             document=document,
                             uploaded_guides=uploaded_guides)
    
    else:
        try:
            project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
            document = ProjectDocument.query.filter_by(project_id=project_id).order_by(ProjectDocument.uploaded_at.desc()).first()
            
            if not document:
                flash('❌ Uploader un PDF d\'abord', 'error')
                return redirect(url_for('ai.analysis_page', project_id=project_id))
            
            guide_id = request.form.get('guide_id')
            if not guide_id:
                flash('❌ Sélectionnez un guide', 'error')
                return redirect(url_for('ai.guided_analysis', project_id=project_id))
            
            guide = UploadedGuide.query.filter_by(id=guide_id, user_id=current_user.id).first()
            if not guide:
                flash('❌ Guide non trouvé', 'error')
                return redirect(url_for('ai.guided_analysis', project_id=project_id))
            
            # Charger le guide
            guide_file_path = os.path.join('static', 'uploads', 'guides', guide.file_path)
            guide_data = load_guide_data(guide_file_path, guide.file_name)
            
            if not guide_data:
                flash('❌ Erreur chargement guide', 'error')
                return redirect(url_for('ai.guided_analysis', project_id=project_id))
            
            # Analyser
            file_path = os.path.join('static', 'uploads', 'documents', document.file_path)
            content = extract_text_from_pdf(file_path)
            analysis_result = analyze_with_uploaded_guide(content, project.domain, guide_data, guide.title)
            
            # Sauvegarder
            project.has_ai_analysis = True
            project.ai_analysis_data = analysis_result
            project.ai_analysis_date = datetime.now()
            project.ai_adaptability_score = analysis_result['overall_score']
            db.session.commit()
            
            return render_template('student/guided_analysis_results.html',
                                 project=project,
                                 analysis=analysis_result,
                                 document=document,
                                 guide=guide)
            
        except Exception as e:
            flash(f'❌ Erreur analyse: {str(e)}', 'error')
            return redirect(url_for('ai.analysis_page', project_id=project_id))

@ai_bp.route('/real-analysis/<int:project_id>')
@login_required
def real_analysis(project_id):
    """Analyse réelle"""
    try:
        project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
        document = ProjectDocument.query.filter_by(project_id=project_id).order_by(ProjectDocument.uploaded_at.desc()).first()
        
        if not document:
            flash('❌ Uploader un PDF d\'abord', 'error')
            return redirect(url_for('ai.analysis_page', project_id=project_id))
        
        file_path = os.path.join('static', 'uploads', 'documents', document.file_path)
        content = extract_text_from_pdf(file_path)
        analysis_result = analyze_with_mathematical_models(content, project.domain)
        
        project.has_ai_analysis = True
        project.ai_analysis_data = analysis_result
        project.ai_analysis_date = datetime.now()
        project.ai_adaptability_score = analysis_result['overall_score']
        db.session.commit()
        
        return redirect(url_for('ai.real_analysis_results', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erreur analyse: {str(e)}', 'error')
        return redirect(url_for('ai.analysis_page', project_id=project_id))

@ai_bp.route('/real-analysis-results/<int:project_id>')
@login_required
def real_analysis_results(project_id):
    """Résultats analyse réelle"""
    project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
    
    if not project.has_ai_analysis:
        flash('ℹ️ Aucune analyse disponible', 'info')
        return redirect(url_for('ai.analysis_page', project_id=project_id))
    
    return render_template('student/real_analysis_results.html',
                         project=project,
                         analysis=project.ai_analysis_data)

@ai_bp.route('/download-real-analysis/<int:project_id>')
@login_required
def download_real_analysis(project_id):
    """Télécharger PDF analyse"""
    try:
        project = PFAProject.query.filter_by(id=project_id, student_id=current_user.id).first_or_404()
        
        if not project.has_ai_analysis:
            flash('❌ Aucune analyse disponible', 'error')
            return redirect(url_for('ai.analysis_page', project_id=project_id))
        
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
        story.append(Paragraph("ANALYSE DU RAPPORT PFA", title_style))
        
        # Informations
        story.append(Paragraph(f"<b>Projet:</b> {project.title}", styles['Normal']))
        story.append(Paragraph(f"<b>Domaine:</b> {project.domain}", styles['Normal']))
        story.append(Paragraph(f"<b>Score global:</b> {project.ai_analysis_data['overall_score']}/100", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {project.ai_analysis_date.strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Scores
        story.append(Paragraph("SCORES DÉTAILLÉS:", styles['Heading2']))
        
        scores_data = [
            ['Catégorie', 'Score', 'Détails'],
            ['Structure', f"{project.ai_analysis_data['structure']['score']}/100", 
             f"{len(project.ai_analysis_data['structure']['sections_detected'])} sections"],
            ['Technique', f"{project.ai_analysis_data['technical']['score']}/100", 
             f"{project.ai_analysis_data['technical']['terms_count']} termes"],
            ['Mathématique', f"{project.ai_analysis_data['mathematical']['score']}/100", 
             f"{project.ai_analysis_data['mathematical']['complexity_level']}"],
            ['Qualité', f"{project.ai_analysis_data['quality']['score']}/100", 
             f"{project.ai_analysis_data['quality']['readability']} lisibilité"]
        ]
        
        scores_table = Table(scores_data, colWidths=[4*cm, 2*cm, 4*cm])
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(scores_table)
        story.append(Spacer(1, 20))
        
        # Recommandations
        if project.ai_analysis_data['recommendations']:
            story.append(Paragraph("RECOMMANDATIONS:", styles['Heading2']))
            for rec in project.ai_analysis_data['recommendations']:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        filename = f"analyse_{project.title.replace(' ', '_')}.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
        
    except Exception as e:
        flash(f'❌ Erreur génération PDF: {str(e)}', 'error')
        return redirect(url_for('ai.real_analysis_results', project_id=project_id))

# ========== FONCTIONS UTILITAIRES ==========

def load_guide_data(file_path, file_name):
    """Charger données guide"""
    try:
        file_extension = file_name.rsplit('.', 1)[1].lower() if '.' in file_name else ''
        
        if file_extension == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                'required_sections': ['introduction', 'methodologie', 'resultats', 'conclusion'],
                'section_patterns': {
                    'introduction': r'introduction|contexte|problématique',
                    'methodologie': r'méthodologie|méthode|approche',
                    'resultats': r'résultat|expérimentation|test',
                    'conclusion': r'conclusion|perspective|bilan'
                }
            }
    except:
        return None

def analyze_with_uploaded_guide(content, domain, guide_data, guide_title):
    """Analyser avec guide uploadé"""
    structure_score = calculate_guide_structure_score(content, guide_data)
    technical_score = calculate_technical_score_math(content, domain)
    math_complexity = calculate_mathematical_complexity(content)
    quality_score = calculate_quality_score_math(content)
    
    overall_score = calculate_overall_score_math(
        structure_score, technical_score, math_complexity, quality_score
    )
    
    compliance = calculate_guide_compliance(content, guide_data)
    
    return {
        'overall_score': round(overall_score, 2),
        'structure': {
            'score': round(structure_score, 2),
            'sections_detected': detect_sections_with_guide(content, guide_data),
            'sections_missing': find_missing_sections(content, guide_data),
            'compliance': f"{compliance}%",
            'guide_used': guide_title
        },
        'technical': {
            'score': round(technical_score, 2),
            'terms_found': extract_technical_terms(content),
            'terms_count': len(extract_technical_terms(content))
        },
        'mathematical': {
            'score': round(math_complexity, 2),
            'equations_count': count_mathematical_elements(content),
            'complexity_level': get_complexity_level(math_complexity)
        },
        'quality': {
            'score': round(quality_score, 2),
            'readability': round(calculate_readability_index(content), 2),
            'coherence': round(calculate_coherence_score(content), 2)
        },
        'recommendations': generate_guided_recommendations(content, guide_data, structure_score, technical_score)
    }

# ========== FONCTIONS D'ANALYSE (GARDER CELLES EXISTANTES) ==========

def calculate_guide_structure_score(content, guide_data):
    required_sections = guide_data.get('required_sections', [])
    section_patterns = guide_data.get('section_patterns', {})
    
    if not required_sections:
        return 50
    
    detected_count = 0
    for section in required_sections:
        pattern = section_patterns.get(section, f'\\b{section}\\b')
        if re.search(pattern, content.lower(), re.IGNORECASE):
            detected_count += 1
    
    score = (detected_count / len(required_sections)) * 100
    return min(100, score)

def calculate_guide_compliance(content, guide_data):
    required_sections = guide_data.get('required_sections', [])
    section_patterns = guide_data.get('section_patterns', {})
    
    if not required_sections:
        return 0
    
    detected_count = 0
    for section in required_sections:
        pattern = section_patterns.get(section, f'\\b{section}\\b')
        if re.search(pattern, content.lower(), re.IGNORECASE):
            detected_count += 1
    
    return round((detected_count / len(required_sections)) * 100, 1)

def detect_sections_with_guide(content, guide_data):
    sections = []
    section_patterns = guide_data.get('section_patterns', {})
    all_sections = guide_data.get('required_sections', []) + guide_data.get('optional_sections', [])
    
    for section in all_sections:
        pattern = section_patterns.get(section, f'\\b{section}\\b')
        if re.search(pattern, content.lower(), re.IGNORECASE):
            sections.append(section)
    
    return sections

def find_missing_sections(content, guide_data):
    required_sections = guide_data.get('required_sections', [])
    section_patterns = guide_data.get('section_patterns', {})
    missing = []
    
    for section in required_sections:
        pattern = section_patterns.get(section, f'\\b{section}\\b')
        if not re.search(pattern, content.lower(), re.IGNORECASE):
            missing.append(section)
    
    return missing

def generate_guided_recommendations(content, guide_data, structure_score, technical_score):
    recommendations = []
    
    if structure_score < 70:
        missing_sections = find_missing_sections(content, guide_data)
        if missing_sections:
            recommendations.append(f"Ajouter: {', '.join(missing_sections)}")
    
    if technical_score < 60:
        recommendations.append("Approfondir aspects techniques")
    
    if structure_score >= 80 and technical_score >= 70:
        recommendations.append("Excellent travail!")
    
    return recommendations

# [GARDER TOUTES LES AUTRES FONCTIONS MATHÉMATIQUES EXISTANTES...]
def extract_text_from_pdf(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
                text = ""
                try:
                    text_matches = re.findall(b'[\\x20-\\x7E]{4,}', content)
                    for match in text_matches:
                        try:
                            text += match.decode('utf-8', errors='ignore') + " "
                        except:
                            continue
                except:
                    text = "Contenu PDF non extractible"
            
            text = re.sub(r'[^\x00-\x7F]+', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            return text[:10000]
        return "RAPPORT DE PROJET PFA - ANALYSE AUTOMATIQUE"
    except Exception as e:
        print(f"Erreur extraction PDF: {e}")
        return "RAPPORT DE PROJET PFA - ANALYSE AUTOMATIQUE"

def analyze_with_mathematical_models(content, domain):
    structure_score = calculate_structural_score_math(content)
    technical_score = calculate_technical_score_math(content, domain)
    math_complexity = calculate_mathematical_complexity(content)
    quality_score = calculate_quality_score_math(content)
    
    overall_score = calculate_overall_score_math(
        structure_score, technical_score, math_complexity, quality_score
    )
    
    return {
        'overall_score': round(overall_score, 2),
        'structure': {
            'score': round(structure_score, 2),
            'sections_detected': detect_sections_math(content),
            'complexity': round(calculate_structure_complexity(content), 2)
        },
        'technical': {
            'score': round(technical_score, 2),
            'terms_found': extract_technical_terms(content),
            'terms_count': len(extract_technical_terms(content))
        },
        'mathematical': {
            'score': round(math_complexity, 2),
            'equations_count': count_mathematical_elements(content),
            'complexity_level': get_complexity_level(math_complexity)
        },
        'quality': {
            'score': round(quality_score, 2),
            'readability': round(calculate_readability_index(content), 2),
            'coherence': round(calculate_coherence_score(content), 2)
        },
        'recommendations': generate_mathematical_recommendations(
            structure_score, technical_score, math_complexity, quality_score
        )
    }

def calculate_structural_score_math(content):
    sections = detect_sections_math(content)
    section_score = min(100, len(sections) * 20)
    return section_score

def calculate_technical_score_math(content, domain):
    technical_terms = extract_technical_terms(content)
    if not technical_terms:
        return 30
    return min(100, len(technical_terms) * 10)

def calculate_mathematical_complexity(content):
    elements = count_mathematical_elements(content)
    if elements > 0:
        complexity = math.log2(elements + 1) * 10
    else:
        complexity = 10
    return min(100, complexity)

def calculate_quality_score_math(content):
    readability = calculate_readability_index(content)
    coherence = calculate_coherence_score(content)
    return (readability + coherence) / 2

def calculate_overall_score_math(structure, technical, math_complexity, quality):
    weights = [0.3, 0.3, 0.2, 0.2]
    weighted_score = (
        structure * weights[0] +
        technical * weights[1] +
        math_complexity * weights[2] +
        quality * weights[3]
    )
    return min(100, weighted_score)

def detect_sections_math(content):
    sections = ['introduction', 'methodologie', 'resultats', 'conclusion', 'bibliographie']
    detected = []
    for section in sections:
        if detect_section(content, section):
            detected.append(section)
    return detected

def detect_section(content, section):
    patterns = {
        'introduction': r'introduction|contexte|problématique|objectif',
        'methodologie': r'méthodologie|méthode|approche|implémentation',
        'resultats': r'résultat|expérimentation|test|performance',
        'conclusion': r'conclusion|perspective|recommandation|bilan',
        'bibliographie': r'bibliographie|référence|source'
    }
    pattern = patterns.get(section, section)
    return bool(re.search(pattern, content.lower()))

def extract_technical_terms(content):
    technical_terms = re.findall(r'\b(html|css|javascript|python|react|vue|angular|flask|django|tensorflow|pytorch|machine learning|deep learning|android|ios|react native|flutter|pandas|numpy|sql|database|api|rest|graphql)\b', content.lower())
    return list(set(technical_terms))

def count_mathematical_elements(content):
    return len(re.findall(r'\$[^$]+\$', content)) + len(re.findall(r'[a-zA-Z]\s*=\s*[^\\n]+', content))

def calculate_structure_complexity(content):
    paragraphs = len(re.split(r'\n\s*\n', content))
    sections = len(detect_sections_math(content))
    if paragraphs > 0 and sections > 0:
        return math.log(paragraphs * sections) / math.log(10)
    return 1.0

def calculate_readability_index(content):
    words = content.split()
    sentences = re.split(r'[.!?]+', content)
    if len(sentences) == 0 or len(words) == 0:
        return 50
    avg_sentence_length = len(words) / len(sentences)
    avg_word_length = sum(len(word) for word in words) / len(words)
    readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / 100)
    return max(0, min(100, readability))

def calculate_coherence_score(content):
    transition_words = ['premièrement', 'deuxièmement', 'ensuite', 'en conclusion', 'par conséquent']
    transition_count = sum(1 for word in transition_words if word in content.lower())
    sections = detect_sections_math(content)
    section_score = min(1.0, len(sections) / 5)
    transition_score = min(0.5, transition_count * 0.1)
    return (section_score + transition_score) * 50

def get_complexity_level(score):
    if score >= 80: return "Avancé"
    elif score >= 60: return "Intermédiaire"
    elif score >= 40: return "Basique"
    else: return "Débutant"

def generate_mathematical_recommendations(structure, technical, math_complexity, quality):
    recommendations = []
    if structure < 70: recommendations.append("Améliorer la structure")
    if technical < 60: recommendations.append("Approfondir technique")
    if math_complexity < 50: recommendations.append("Enrichir contenu math")
    if quality < 65: recommendations.append("Améliorer qualité")
    if not recommendations: recommendations.append("Excellent travail!")
    return recommendations