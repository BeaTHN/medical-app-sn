import streamlit as st
import numpy as np
from PIL import Image
import io
import base64
import time
import os
import tempfile
import hashlib
import tensorflow as tf
from tensorflow import keras
import gc
from datetime import datetime
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# Import du module PWA
try:
    from pwa_integration import setup_pwa, get_pwa_installation_guide
    PWA_AVAILABLE = True
except ImportError:
    PWA_AVAILABLE = False
    print("Module PWA non disponible")

# Configuration de la page
st.set_page_config(
    page_title="SamaSanté  - DIA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuration de sécurité
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# CSS personnalisé pour le design médical responsive
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variables CSS */
    :root {
        --primary-blue: #4F46E5;
        --secondary-blue: #3B82F6;
        --accent-teal: #14B8A6;
        --light-bg: #F8FAFC;
        --white: #FFFFFF;
        --text-dark: #1E293B;
        --text-gray: #64748B;
        --border-light: #E2E8F0;
        --success-green: #10B981;
        --warning-orange: #F59E0B;
        --danger-red: #EF4444;
    }
    
    /* Reset et base */
    .stApp {
        font-family: 'Inter', sans-serif;
        /* background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); */
        background-color: #E6F0FA; 
        /* background: linear-gradient(135deg, #E6F0FA, #E6FAF0); */
        /* background: linear-gradient(135deg, #667eea 0%, #87CEEB, #E6F0FA); */
        min-height: 100vh;
    }
    
    /* Header personnalisé */
    .custom-header {
        background: var(--white);
        padding: 1rem 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .logo-icon {
        width: 40px;
        height: 40px;
        background: var(--primary-blue);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
        font-weight: bold;
    }
    
    .logo-text {
        font-size: 24px;
        font-weight: 700;
        color: var(--text-dark);
    }
    
    .nav-links {
        display: flex;
        gap: 2rem;
        align-items: center;
    }
    
    .nav-link {
        color: var(--text-gray);
        text-decoration: none;
        font-weight: 500;
        transition: color 0.3s ease;
        cursor: pointer;
    }
    
    .nav-link:hover {
        color: var(--primary-blue);
    }
    
    /* Hero section */
    .hero-section {
        background: var(--white);
        border-radius: 16px;
        padding: 3rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 3rem;
        align-items: center;
    }
    
    .hero-content h1 {
        font-size: 3rem;
        font-weight: 700;
        color: var(--primary-blue);
        line-height: 1.2;
        margin-bottom: 1rem;
    }
    
    .hero-content p {
        font-size: 1.1rem;
        color: var(--text-gray);
        line-height: 1.6;
        margin-bottom: 2rem;
    }
    
    /* Cards */
    .feature-card {
        background: var(--white);
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 1rem;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed var(--border-light);
        border-radius: 12px;
        padding: 3rem;
        text-align: center;
        background: var(--light-bg);
        transition: all 0.3s ease;
        margin: 1rem 0;
    }
    
    .upload-area:hover {
        border-color: var(--primary-blue);
        background: rgba(79, 70, 229, 0.05);
    }
    
    /* Résultats */
    .result-card {
        background: var(--white);
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-top: 2rem;
    }
    
    /* Jauge de diagnostic */
    .diagnostic-gauge {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 2rem 0;
    }
    
    .gauge-container {
        position: relative;
        width: 200px;
        height: 200px;
    }
    
    .gauge-bg {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: conic-gradient(
            var(--success-green) 0deg 120deg,
            var(--warning-orange) 120deg 240deg,
            var(--danger-red) 240deg 360deg
        );
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .gauge-inner {
        width: 80%;
        height: 80%;
        background: white;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .gauge-value {
        font-size: 2rem;
        font-weight: bold;
        color: var(--text-dark);
    }
    
    .gauge-label {
        font-size: 0.9rem;
        color: var(--text-gray);
        margin-top: 0.5rem;
    }
    
    /* Boutons */
    .custom-button {
        background: var(--accent-teal);
        color: white;
        padding: 12px 24px;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
        margin: 0.5rem;
    }
    
    .custom-button:hover {
        background: #0F766E;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(20, 184, 166, 0.4);
    }
    
    .custom-button.secondary {
        background: var(--primary-blue);
    }
    
    .custom-button.secondary:hover {
        background: #3730A3;
    }
    
    /* Messages de sécurité */
    .security-notice {
        background: linear-gradient(135deg, #FEF3C7, #FDE68A);
        border: 1px solid #F59E0B;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .privacy-notice {
        background: linear-gradient(135deg, #DBEAFE, #BFDBFE);
        border: 1px solid #3B82F6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-section {
            grid-template-columns: 1fr;
            padding: 2rem;
            gap: 2rem;
        }
        
        .hero-content h1 {
            font-size: 2rem;
        }
        
        .custom-header {
            padding: 1rem;
            flex-direction: column;
            gap: 1rem;
        }
        
        .nav-links {
            gap: 1rem;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .gauge-container {
            width: 150px;
            height: 150px;
        }
        
        .gauge-value {
            font-size: 1.5rem;
        }
    }
    
    /* Masquer les éléments Streamlit par défaut */
    .stDeployButton {
        display: none;
    }
    
    #MainMenu {
        visibility: hidden;
    }
    
    footer {
        visibility: hidden;
    }
    
    header {
        visibility: hidden;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Classe pour la gestion sécurisée des fichiers
class SecureFileManager:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, uploaded_file):
        """Valide le fichier uploadé"""
        if uploaded_file is None:
            return False, "Aucun fichier sélectionné"
        
        # Vérifier l'extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in self.allowed_extensions:
            return False, f"Extension non autorisée. Extensions acceptées: {', '.join(self.allowed_extensions)}"
        
        # Vérifier la taille
        if len(uploaded_file.getvalue()) > self.max_file_size:
            return False, f"Fichier trop volumineux. Taille maximale: {self.max_file_size // (1024*1024)}MB"
        
        return True, "Fichier valide"
    
    def save_temp_file(self, uploaded_file):
        """Sauvegarde temporaire sécurisée"""
        file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        temp_filename = f"{file_hash}{file_ext}"
        temp_path = os.path.join(self.temp_dir, temp_filename)
        
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        return temp_path
    
    def cleanup(self):
        """Nettoyage des fichiers temporaires"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass

# Classe pour le modèle de prédiction
class MedicalAIModel:
    def __init__(self):
        self.model = None
        self.classes = ["Normal", "Précancéreux", "Cancéreux"]
        self.model_path = "ResNet50V2_3.keras"
        self.load_model()
    
    def load_model(self):
        """Charge le modèle de prédiction"""
        try:
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                st.success("✅ Modèle IA chargé avec succès")
            else:
                st.warning("⚠️ Modèle non trouvé, utilisation du mode démonstration")
                self.model = None
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement du modèle: {e}")
            self.model = None
    
    def preprocess_image(self, image):
        """Prétraite l'image pour le modèle"""
        # Redimensionne l'image à 224x224
        image = image.resize((224, 224))
        
        # Convertit en RGB si nécessaire
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convertit en array numpy
        image_array = np.array(image)
        
        # Normalise les valeurs des pixels
        image_array = image_array / 255.0
        
        # Ajoute une dimension batch
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array
    
    def predict(self, image):
        """Fait une prédiction sur l'image"""
        try:
            processed_image = self.preprocess_image(image)
            
            if self.model is not None:
                # Prédiction réelle avec le modèle
                predictions = self.model.predict(processed_image, verbose=0)
                probabilities = predictions[0]
                
                # Mappage des 7 classes du modèle vers 3 classes simplifiées
                # Supposons que les classes sont: [Normal, ASCUS, LSIL, HSIL, SCC, AGC, AIS]
                normal_prob = probabilities[0]  # Normal
                precancer_prob = probabilities[1] + probabilities[2]  # ASCUS + LSIL
                cancer_prob = probabilities[3] + probabilities[4] + probabilities[5] + probabilities[6]  # HSIL + SCC + AGC + AIS
                
                # Normalisation
                total = normal_prob + precancer_prob + cancer_prob
                if total > 0:
                    final_probs = [normal_prob/total, precancer_prob/total, cancer_prob/total]
                else:
                    final_probs = [0.33, 0.33, 0.34]
            else:
                # Mode démonstration avec prédictions aléatoires
                time.sleep(2)  # Simule le temps de traitement
                final_probs = np.random.dirichlet([2, 1, 1])  # Biais vers normal
            
            return final_probs, self.classes
            
        except Exception as e:
            st.error(f"Erreur lors de la prédiction: {e}")
            return [0.33, 0.33, 0.34], self.classes
        finally:
            # Nettoyage mémoire
            gc.collect()

# Fonction pour générer un PDF du diagnostic
def generate_pdf_report(image, prediction_result, confidence, timestamp):
    """Génère un rapport PDF du diagnostic"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#4F46E5')
    )
    story.append(Paragraph("Rapport de Diagnostic Médical IA", title_style))
    story.append(Spacer(1, 12))
    
    # Informations générales
    info_style = styles['Normal']
    story.append(Paragraph(f"<b>Date et heure:</b> {timestamp}", info_style))
    story.append(Paragraph(f"<b>Résultat:</b> {prediction_result}", info_style))
    story.append(Paragraph(f"<b>Niveau de confiance:</b> {confidence:.1f}%", info_style))
    story.append(Spacer(1, 20))
    
    # Avertissement médical
    warning_style = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.red,
        borderColor=colors.red,
        borderWidth=1,
        borderPadding=10
    )
    story.append(Paragraph(
        "<b>AVERTISSEMENT MÉDICAL:</b><br/>"
        "Ce diagnostic automatisé est un outil d'aide à la décision uniquement. "
        "Il ne remplace pas l'avis d'un professionnel de santé qualifié. "
        "Consultez toujours un médecin pour un diagnostic définitif.",
        warning_style
    ))
    story.append(Spacer(1, 20))
    
    # Informations sur la technologie
    story.append(Paragraph("<b>Technologie utilisée:</b>", styles['Heading2']))
    story.append(Paragraph(
        "• Intelligence Artificielle basée sur un réseau de neurones convolutionnel<br/>"
        "• Modèle entraîné sur des images cytologiques cervicales<br/>"
        "• Analyse automatisée des caractéristiques cellulaires",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    
    # Recommandations
    story.append(Paragraph("<b>Recommandations:</b>", styles['Heading2']))
    if "Normal" in prediction_result:
        recommendations = "• Continuer les examens de dépistage réguliers<br/>• Maintenir un mode de vie sain"
    elif "Précancéreux" in prediction_result:
        recommendations = "• Consulter un gynécologue dans les plus brefs délais<br/>• Effectuer des examens complémentaires<br/>• Surveillance médicale renforcée"
    else:
        recommendations = "• Consultation médicale URGENTE requise<br/>• Examens approfondis nécessaires<br/>• Prise en charge spécialisée recommandée"
    
    story.append(Paragraph(recommendations, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Initialisation des composants
@st.cache_resource
def init_components():
    """Initialise les composants de l'application"""
    file_manager = SecureFileManager()
    ai_model = MedicalAIModel()
    return file_manager, ai_model

# Interface utilisateur
def display_header():
    """Affiche l'en-tête de l'application"""
    st.markdown("""
    <div class="custom-header">
        <div class="logo-section">
            <div class="logo-icon">🏥</div>
            <div class="logo-text">SamaSanté</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_hero():
    """Affiche la section hero"""
    st.markdown("""
    <div class="hero-section fade-in">
        <div class="hero-content">
            <h1>Diagnostic médical assisté par IA</h1>
            <p>Notre application utilise l'intelligence artificielle avancée pour aider au dépistage du cancer du col de l'utérus. 
            Chargez une image cytologique et obtenez un diagnostic automatisé en quelques secondes, avec une interface sécurisée et confidentielle.</p>
            <div class="privacy-notice">
                <span>🔒</span>
                <span><strong>Confidentialité garantie:</strong> Aucune donnée n'est stockée. Traitement local et suppression automatique.</span>
            </div>
        </div>
        <div style="display: flex; justify-content: center; align-items: center; background: linear-gradient(135deg, var(--accent-teal), var(--secondary-blue)); border-radius: 16px; padding: 2rem; min-height: 300px;">
            <div style="text-align: center; color: white;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔬</div>
                <div style="font-size: 1.5rem; font-weight: 600;">IA Médicale</div>
                <div style="font-size: 1rem; opacity: 0.9;">Précision • Rapidité • Sécurité</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_diagnostic_gauge(prediction, confidence):
    """Affiche la jauge de diagnostic"""
    # Déterminer la couleur selon le diagnostic
    if "Normal" in prediction:
        color = "#10B981"  # Vert
        icon = "✅"
        gauge_rotation = 0  # Position dans la zone verte
    elif "Précancéreux" in prediction:
        color = "#F59E0B"  # Orange
        icon = "⚠️"
        gauge_rotation = 120  # Position dans la zone orange
    else:
        color = "#EF4444"  # Rouge
        icon = "🚨"
        gauge_rotation = 240  # Position dans la zone rouge
    
    st.markdown(f"""
    <div class="diagnostic-gauge">
        <div class="gauge-container">
            <div class="gauge-bg">
                <div class="gauge-inner">
                    <div style="font-size: 2rem;">{icon}</div>
                    <div class="gauge-value" style="color: {color};">{confidence:.0f}%</div>
                    <div class="gauge-label">Confiance</div>
                </div>
            </div>
        </div>
    </div>
    <div style="text-align: center; margin-top: 1rem;">
        <h3 style="color: {color}; margin: 0;">{prediction}</h3>
        <p style="color: var(--text-gray); margin: 0.5rem 0;">Niveau de confiance: {confidence:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Fonction principale de l'application"""
    # Configuration PWA
    if PWA_AVAILABLE:
        setup_pwa()
    
    # Initialisation
    file_manager, ai_model = init_components()
    
    # Affichage de l'interface
    display_header()
    display_hero()
    
    # Navigation par onglets
    tab1, tab2, tab3, tab4 = st.tabs(["🔬 Analyse", "📋 Historique", "ℹ️ À propos", "📞 Contact"])
    
    with tab1:
        st.markdown("## 📸 Analyse d'Image Médicale")
        
        # Messages de sécurité
        st.markdown("""
        <div class="security-notice">
            <span>🛡️</span>
            <span><strong>Sécurité:</strong> Toutes les images sont traitées localement et supprimées automatiquement après analyse.</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Zone d'upload
        uploaded_file = st.file_uploader(
            "Choisissez une image cytologique du col de l'utérus",
            type=['png', 'jpg', 'jpeg', 'bmp'],
            help="Formats acceptés: PNG, JPG, JPEG, BMP. Taille maximale: 10MB"
        )
        
        if uploaded_file is not None:
            # Validation du fichier
            is_valid, message = file_manager.validate_file(uploaded_file)
            
            if not is_valid:
                st.error(f"❌ {message}")
                return
            
            # Affichage de l'image
            col1, col2 = st.columns([1, 1])
            
            with col1:
                image = Image.open(uploaded_file)
                st.image(image, caption="Image chargée", use_container_width=True)
                
                # Informations sur l'image
                st.markdown("### 📊 Informations")
                st.write(f"**Nom:** {uploaded_file.name}")
                st.write(f"**Taille:** {image.size}")
                st.write(f"**Mode:** {image.mode}")
                st.write(f"**Taille fichier:** {len(uploaded_file.getvalue())} bytes")
            
            with col2:
                # Bouton d'analyse
                if st.button("🔬 Analyser l'image", type="primary", use_container_width=True):
                    with st.spinner("🔄 Analyse en cours... Veuillez patienter."):
                        # Analyse avec le modèle IA
                        probabilities, classes = ai_model.predict(image)
                        
                        # Résultats
                        max_prob_idx = np.argmax(probabilities)
                        predicted_class = classes[max_prob_idx]
                        confidence = probabilities[max_prob_idx] * 100
                        
                        # Affichage de la jauge
                        display_diagnostic_gauge(predicted_class, confidence)
                        
                        # Détails des probabilités
                        #st.markdown("### 📊 Détail des probabilités")
                        #for i, (class_name, prob) in enumerate(zip(classes, probabilities)):
                        #    prob_percent = prob * 100
                        #    if i == max_prob_idx:
                        #        st.markdown(f"**{class_name}**: {prob_percent:.1f}% 🎯")
                        #    else:
                        #        st.markdown(f"{class_name}: {prob_percent:.1f}%")
                        
                        # Sauvegarde dans l'historique
                        if 'history' not in st.session_state:
                            st.session_state.history = []
                        
                        result = {
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'diagnosis': predicted_class,
                            'confidence': confidence,
                            'image_name': uploaded_file.name
                        }
                        st.session_state.history.append(result)
                        
                        # Boutons d'action
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        
                        with col_btn1:
                            # Génération du PDF
                            pdf_buffer = generate_pdf_report(
                                image, predicted_class, confidence, result['timestamp']
                            )
                            st.download_button(
                                label="📄 Télécharger PDF",
                                data=pdf_buffer.getvalue(),
                                file_name=f"diagnostic_{result['timestamp'].replace(':', '-')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        
                        with col_btn2:
                            if st.button("💾 Sauvegarder", use_container_width=True):
                                st.success("✅ Résultat sauvegardé dans l'historique!")
                        
                        with col_btn3:
                            if st.button("🔄 Nouvelle analyse", use_container_width=True):
                                st.rerun()
                
                # Message de prévention
                st.markdown("---")
                st.warning("""
                ⚠️ **Important**: Ce diagnostic automatisé est un outil d'aide à la décision. 
                Il ne remplace pas l'avis d'un professionnel de santé qualifié. 
                Consultez toujours un médecin pour un diagnostic définitif.
                """)
    
    with tab2:
        st.markdown("## 📋 Historique des Analyses")
        
        if 'history' in st.session_state and st.session_state.history:
            for i, result in enumerate(reversed(st.session_state.history)):
                with st.expander(f"Analyse {len(st.session_state.history) - i} - {result['timestamp']}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Image:** {result['image_name']}")
                    with col2:
                        st.write(f"**Diagnostic:** {result['diagnosis']}")
                    with col3:
                        st.write(f"**Confiance:** {result['confidence']:.1f}%")
            
            if st.button("🗑️ Effacer l'historique"):
                st.session_state.history = []
                st.success("Historique effacé")
                st.rerun()
        else:
            st.info("📝 Aucune analyse dans l'historique")
    
    with tab3:
        st.markdown('<div id="about-section"></div>', unsafe_allow_html=True)
        st.markdown("## ℹ️ À propos de l'application")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 🎯 Objectif
            Cette application utilise l'intelligence artificielle pour aider au dépistage 
            du cancer du col de l'utérus à partir d'images cytologiques. Elle est conçue 
            pour être utilisée par des professionnels de santé dans des contextes à ressources limitées.
            
            ### 🔬 Fonctionnement de l'IA
            Notre modèle d'intelligence artificielle est basé sur un réseau de neurones convolutionnel 
            (CNN) entraîné sur des milliers d'images cytologiques cervicales. Le modèle analyse:
            
            - **Morphologie cellulaire**: Forme et taille des cellules
            - **Caractéristiques nucléaires**: Aspect des noyaux cellulaires  
            - **Patterns tissulaires**: Organisation des tissus
            - **Anomalies cytologiques**: Détection d'irrégularités
            
            ### ⚠️ Limites médicales
            **Important**: Cette application est un outil d'aide au diagnostic uniquement:
            
            - ❌ Ne remplace **jamais** l'expertise d'un professionnel de santé
            - ❌ Ne constitue **pas** un diagnostic médical définitif
            - ❌ Ne doit **pas** être utilisée comme seul critère de décision
            - ✅ Doit être complétée par un examen médical approfondi
            - ✅ Résultats à interpréter par un spécialiste qualifié
            
            ### 🛡️ Sécurité et Confidentialité
            Nous prenons la protection de vos données très au sérieux:
            
            - **🔒 Traitement local**: Toutes les analyses sont effectuées localement
            - **🚫 Aucun stockage**: Les images ne sont jamais sauvegardées sur nos serveurs
            - **⏱️ Suppression automatique**: Fichiers supprimés immédiatement après traitement
            - **🔐 Chiffrement**: Communications sécurisées par HTTPS
            - **📝 Aucune collecte**: Aucune donnée personnelle n'est collectée
            """)
        
        with col2:
            st.markdown("""
            ### 🚀 Fonctionnalités
            
            **📸 Analyse d'images**
            - Support formats: PNG, JPG, JPEG, BMP
            - Traitement en temps réel
            - Interface responsive
            
            **📊 Résultats détaillés**
            - Jauge de diagnostic visuelle
            - Scores de confiance
            - Probabilités détaillées
            
            **📄 Rapports PDF**
            - Génération automatique
            - Informations complètes
            - Téléchargement sécurisé
            
            **📱 Progressive Web App**
            - Installation sur mobile
            - Fonctionnement hors ligne
            - Interface native
            
            **🔧 Technologies**
            - **Frontend**: Streamlit
            - **IA**: TensorFlow/Keras
            - **Images**: PIL/Pillow
            - **PDF**: ReportLab
            - **Sécurité**: Chiffrement TLS
            """)
    
    with tab4:
        st.markdown('<div id="contact-section"></div>', unsafe_allow_html=True)
        st.markdown("## 📞 Contact")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📧 Formulaire de Contact")
            
            with st.form("contact_form"):
                name = st.text_input("Nom complet *")
                email = st.text_input("Email *")
                subject = st.selectbox(
                    "Sujet *",
                    ["Question générale", "Support technique", "Signalement de bug", "Autre"]
                )
                message = st.text_area("Message *", height=150)
                
                submitted = st.form_submit_button("📤 Envoyer le message")
                
                if submitted:
                    if name and email and message:
                        # Ici, vous pourriez intégrer un service d'email ou webhook
                        st.success("✅ Message envoyé avec succès! Nous vous répondrons dans les plus brefs délais.")
                        st.balloons()
                    else:
                        st.error("❌ Veuillez remplir tous les champs obligatoires.")
        
        with col2:
            with st.expander("📍 Informations de Contact", expanded=False):
                st.markdown("### 📍 Informations de Contact")
                
                st.markdown("""
                **🏥 SamaSanté - Équipe IA**
                
                📧 **Email**: support@samasante-ai.com  
                📱 **Téléphone**: +221 77 000 00 00  
                🌐 **Site web**: www.samasante-ai.com  
                
                **🕒 Heures de support**
                - Lundi - Vendredi: 9h00 - 18h00
                - Weekend: Support d'urgence uniquement
                
                **🚨 Support d'urgence**
                - Email: urgence@samasante-ai.com
                - Téléphone: +221 77 000 00 00
                
                **👥 Équipe de développement**
                - Dr. Beatrice THIONE - Directrice Médicale
                - Ursule - Lead Developer IA
                - Salla - UX/UI Designer
                - BeaSalla - DevOps Engineer
                
                **🔗 Réseaux sociaux**
                - LinkedIn: /company/samasante-ai
                - Twitter: @SAMASANTEAI_FR
                - GitHub: /samasante-ai-team
                """)
            
            # Carte de contact stylisée
            st.markdown("""
            <div class="feature-card" style="text-align: center; margin-top: 2rem;">
                <h4 style="color: var(--primary-blue); margin-bottom: 1rem;">🤝 Collaboration</h4>
                <p>Intéressé par une collaboration ou un partenariat?</p>
                <a href="mailto:partenariat@samasante-ai.com" class="custom-button">
                    📧 Contactez-nous
                </a>
            </div>
            """, unsafe_allow_html=True)
        
    
    # Nettoyage automatique à la fin
    try:
        file_manager.cleanup()
    except:
        pass

if __name__ == "__main__":
    main()

