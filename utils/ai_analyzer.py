# [file name]: utils/ai_analyzer.py
import os
import PyPDF2
import re
from datetime import datetime
from typing import Dict, List, Tuple

class PFAReportAnalyzer:
    def __init__(self):
        # Vérifier si OpenAI est disponible
        self.openai_available = False
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key and api_key != 'sk-fake-key-for-testing' and api_key.startswith('sk-'):
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=api_key)
                self.openai_available = True
                print("✓ OpenAI configuré")
            except Exception as e:
                print(f"⚠️ Erreur OpenAI: {e}")
                self.openai_available = False
        else:
            print("⚠️ Mode simulation - OpenAI non configuré")
        
        self.guide_requirements = self.load_guide_requirements()
    
    def load_guide_requirements(self) -> Dict:
        """Charge les exigences du guide de stage"""
        return {
            "sections_obligatoires": [
                "introduction", "contexte", "methodologie", "resultats", 
                "discussion", "conclusion", "bibliographie"
            ],
            "formatage": {
                "police": "Times New Roman ou Arial",
                "taille_police": "11 ou 12",
                "interligne": "1.5",
                "marges": "2.5cm minimum"
            },
            "structure": {
                "pages_minimum": 20,
                "pages_maximum": 60,
                "figures_obligatoires": True,
                "tableaux_requis": True
            }
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte d'un PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            raise Exception(f"Erreur extraction PDF: {str(e)}")
    
    def analyze_layout_issues(self, pdf_path: str) -> Dict:
        """Analyse les problèmes de mise en page"""
        issues = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                
                # Vérification nombre de pages
                if total_pages < self.guide_requirements["structure"]["pages_minimum"]:
                    issues.append({
                        "type": "structure",
                        "severity": "high",
                        "message": f"Nombre de pages insuffisant ({total_pages} au lieu de {self.guide_requirements['structure']['pages_minimum']} minimum)",
                        "page": "global"
                    })
                
                if total_pages > self.guide_requirements["structure"]["pages_maximum"]:
                    issues.append({
                        "type": "structure", 
                        "severity": "medium",
                        "message": f"Rapport trop long ({total_pages} pages, maximum recommandé: {self.guide_requirements['structure']['pages_maximum']})",
                        "page": "global"
                    })
                
                # Analyse basique du contenu par page
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    
                    # Vérifier pages vides ou presque vides
                    if len(text.strip()) < 50:
                        issues.append({
                            "type": "contenu",
                            "severity": "high",
                            "message": "Page contenant très peu de texte",
                            "page": page_num
                        })
                    
                    # Détecter les pages avec uniquement des images
                    lines = text.split('\n')
                    if len(lines) < 3 and any(word in text.lower() for word in ['figure', 'image', 'graphique']):
                        issues.append({
                            "type": "formatage",
                            "severity": "low", 
                            "message": "Page potentiellement dédiée uniquement à une figure",
                            "page": page_num
                        })
                
                return {
                    "total_pages": total_pages,
                    "layout_issues": issues,
                    "pages_analyzed": total_pages
                }
                
        except Exception as e:
            raise Exception(f"Erreur analyse mise en page: {str(e)}")
    
    def analyze_content_with_openai(self, text: str, guide_text: str = "") -> Dict:
        """Analyse le contenu avec l'IA OpenAI"""
        try:
            prompt = f"""
            Tu es un expert en évaluation de rapports de stage PFA. Analyse ce rapport selon le guide fourni.
            
            GUIDE DE STAGE:
            {guide_text}
            
            RAPPORT À ANALYSER:
            {text[:12000]}  # Limite pour éviter les tokens excessifs
            
            Fournis une analyse structurée avec:
            1. Score d'adaptabilité au guide (0-100%)
            2. Points forts
            3. Problèmes détectés avec pages concernées
            4. Recommandations spécifiques
            
            Format de réponse:
            SCORE: [score]%
            POINTS FORTS:
            - [point fort 1]
            - [point fort 2]
            PROBLEMES:
            - Page [X]: [description problème]
            - Page [Y]: [description problème]
            RECOMMANDATIONS:
            - [recommandation 1]
            - [recommandation 2]
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Tu es un évaluateur expert de rapports PFA. Réponds toujours dans le format demandé."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return self.parse_ai_response(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "error": f"Erreur analyse IA: {str(e)}",
                "adaptability_score": 0,
                "strengths": [],
                "issues": [],
                "recommendations": []
            }
    
    def analyze_content_simulation(self, text: str, guide_text: str = "") -> Dict:
        """Analyse le contenu - Version simulée sans OpenAI"""
        try:
            # Simulation d'analyse basique
            score = 65  # Score simulé
            
            # Détection de sections
            sections_trouvees = []
            for section in self.guide_requirements["sections_obligatoires"]:
                if section in text.lower():
                    sections_trouvees.append(section)
            
            # Points forts simulés
            strengths = [
                "Bonne structure générale détectée",
                f"Sections présentes: {', '.join(sections_trouvees[:3])}",
                "Contenu bien réparti entre les pages"
            ]
            
            # Problèmes simulés
            issues = []
            if len(sections_trouvees) < 4:
                issues.append({
                    "description": f"Sections manquantes: seulement {len(sections_trouvees)} sections détectées sur {len(self.guide_requirements['sections_obligatoires'])} attendues",
                    "page": "multiple",
                    "type": "structure"
                })
            
            if len(text) < 5000:
                issues.append({
                    "description": "Contenu potentiellement insuffisant pour un rapport complet",
                    "page": "global", 
                    "type": "contenu"
                })
            
            # Détection de problèmes spécifiques
            if "bibliographie" not in text.lower():
                issues.append({
                    "description": "Section bibliographie manquante ou incomplète",
                    "page": "N/A",
                    "type": "structure"
                })
            
            recommendations = [
                "Vérifier que toutes les sections obligatoires sont présentes",
                "S'assurer que le rapport fait au moins 20 pages",
                "Relire l'orthographe et la grammaire",
                "Ajouter des figures et tableaux si manquants"
            ]
            
            return {
                "adaptability_score": score,
                "strengths": strengths,
                "issues": issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "adaptability_score": 50,
                "strengths": ["Analyse basique activée"],
                "issues": [{"description": "Mode simulation - Vérification manuelle recommandée", "page": "N/A", "type": "info"}],
                "recommendations": ["Cette analyse est simulée. Pour une analyse complète, configurez OpenAI API."]
            }
    
    def analyze_content_with_ai(self, text: str, guide_text: str = "") -> Dict:
        """Analyse le contenu - Choix automatique entre OpenAI et simulation"""
        if self.openai_available:
            return self.analyze_content_with_openai(text, guide_text)
        else:
            return self.analyze_content_simulation(text, guide_text)
    
    def parse_ai_response(self, response: str) -> Dict:
        """Parse la réponse de l'IA en structure de données"""
        try:
            analysis = {
                "adaptability_score": 50,
                "strengths": [],
                "issues": [],
                "recommendations": []
            }
            
            # Extraire le score
            score_match = re.search(r'SCORE:\s*(\d+)%', response, re.IGNORECASE)
            if score_match:
                analysis["adaptability_score"] = int(score_match.group(1))
            
            # Extraire les points forts
            strengths_section = re.search(r'POINTS FORTS:(.*?)(?=PROBLEMES:|RECOMMANDATIONS:|$)', response, re.IGNORECASE | re.DOTALL)
            if strengths_section:
                strengths_text = strengths_section.group(1)
                strengths = re.findall(r'-\s*(.+?)(?=\n|$)', strengths_text)
                analysis["strengths"] = [s.strip() for s in strengths if s.strip()]
            
            # Extraire les problèmes
            problems_section = re.search(r'PROBLEMES:(.*?)(?=RECOMMANDATIONS:|$)', response, re.IGNORECASE | re.DOTALL)
            if problems_section:
                problems_text = problems_section.group(1)
                problems = re.findall(r'-\s*Page\s*(\d+):\s*(.+?)(?=\n|$)', problems_text)
                for page, description in problems:
                    analysis["issues"].append({
                        "description": description.strip(),
                        "page": page,
                        "type": "contenu"
                    })
            
            # Extraire les recommandations
            recommendations_section = re.search(r'RECOMMANDATIONS:(.*?)$', response, re.IGNORECASE | re.DOTALL)
            if recommendations_section:
                recs_text = recommendations_section.group(1)
                recommendations = re.findall(r'-\s*(.+?)(?=\n|$)', recs_text)
                analysis["recommendations"] = [r.strip() for r in recommendations if r.strip()]
            
            return analysis
            
        except Exception as e:
            return {
                "adaptability_score": 50,
                "strengths": ["Analyse automatique activée"],
                "issues": [{"description": "Erreur d'analyse détaillée", "page": "N/A", "type": "système"}],
                "recommendations": ["Vérifier manuellement le rapport"]
            }
    
    def comprehensive_analysis(self, pdf_path: str, guide_content: str = "") -> Dict:
        """Analyse complète du rapport"""
        try:
            # Extraction texte
            text = self.extract_text_from_pdf(pdf_path)
            
            # Analyse mise en page
            layout_analysis = self.analyze_layout_issues(pdf_path)
            
            # Analyse contenu avec IA
            content_analysis = self.analyze_content_with_ai(text, guide_content)
            
            # Mode d'analyse
            analysis_mode = "openai" if self.openai_available else "simulation"
            
            # Combinaison des résultats
            return {
                "summary": {
                    "adaptability_score": content_analysis.get("adaptability_score", 0),
                    "total_issues": len(layout_analysis["layout_issues"]) + len(content_analysis.get("issues", [])),
                    "pages_count": layout_analysis["total_pages"],
                    "analysis_date": datetime.now().isoformat(),
                    "mode": analysis_mode
                },
                "layout_analysis": layout_analysis,
                "content_analysis": content_analysis,
                "recommendations": self.generate_recommendations(layout_analysis, content_analysis)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "summary": {"adaptability_score": 0, "total_issues": 0, "mode": "erreur"}
            }
    
    def generate_recommendations(self, layout: Dict, content: Dict) -> List[str]:
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        # Recommandations basées sur la mise en page
        layout_issues = layout.get("layout_issues", [])
        if any(issue["severity"] == "high" for issue in layout_issues):
            recommendations.append("❌ **Problèmes critiques de structure détectés** - Révision urgente nécessaire")
        
        if layout["total_pages"] < self.guide_requirements["structure"]["pages_minimum"]:
            recommendations.append(f"📄 **Ajouter du contenu** - Objectif: {self.guide_requirements['structure']['pages_minimum']} pages minimum")
        
        if layout["total_pages"] > self.guide_requirements["structure"]["pages_maximum"]:
            recommendations.append(f"📝 **Raccourcir le rapport** - Maximum recommandé: {self.guide_requirements['structure']['pages_maximum']} pages")
        
        # Recommandations basées sur le contenu
        score = content.get("adaptability_score", 0)
        if score < 50:
            recommendations.append("🚨 **Adaptabilité faible** - Revoir la structure selon le guide")
        elif score < 70:
            recommendations.append("⚠️ **Adaptabilité moyenne** - Améliorations recommandées")
        else:
            recommendations.append("✅ **Bonne adaptabilité** - Maintenir la qualité")
        
        # Recommandations spécifiques basées sur les problèmes détectés
        content_issues = content.get("issues", [])
        if any("bibliographie" in issue.get("description", "").lower() for issue in content_issues):
            recommendations.append("📚 **Compléter la bibliographie** - Vérifier les références")
        
        if any("section" in issue.get("description", "").lower() for issue in content_issues):
            recommendations.append("📋 **Vérifier la structure** - S'assurer que toutes les sections obligatoires sont présentes")
        
        if not self.openai_available:
            recommendations.append("🔧 **Mode simulation** - Configurez une vraie clé OpenAI API pour une analyse complète")
        
        return recommendations

# Instance globale
report_analyzer = PFAReportAnalyzer()
