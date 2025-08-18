import gdown
import streamlit as st
import numpy as np
from PIL import Image
import io
import base64
import time
import os
import tempfile
import hashlib
try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("TensorFlow non disponible")
import gc
from datetime import datetime
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import cv2

# Import du module PWA
try:
    from pwa_integration import setup_pwa, get_pwa_installation_guide
    PWA_AVAILABLE = True
except ImportError:
    PWA_AVAILABLE = False
    print("Module PWA non disponible")
    
# Configuration de la page
st.set_page_config(
    page_title="SamaSanté - Diagnostic IA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuration de sécurité
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# CSS personnalisé pour le design médical responsive
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url(\'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap\' );
    
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
        font-family: \'Inter\', sans-serif;
        /* background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); */
        /* background-color: #E6F0FA; */
        background: linear-gradient(135deg, #E6F0FA, #E6FAF0); 
        /*background: linear-gradient(135deg, #667eea 0%, #87CEEB, #E6F0FA);*/
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
    
    /* Affichage des résultats sans jauge */
    .result-display {
        text-align: center;
        padding: 2rem;
        border-radius: 12px;
        margin: 2rem 0;
    }
    
    .result-normal {
        background: linear-gradient(135deg, #DCFCE7, #BBF7D0);
        border: 2px solid var(--success-green);
        color: #065F46;
    }
    
    .result-precancer {
        background: linear-gradient(135deg, #FEF3C7, #FDE68A);
        border: 2px solid var(--warning-orange);
        color: #92400E;
    }
    
    .result-cancer {
        background: linear-gradient(135deg, #FEE2E2, #FECACA);
        border: 2px solid var(--danger-red);
        color: #991B1B;
    }
    
    .result-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .result-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .result-description {
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    
    .result-confidence {
        font-size: 1rem;
        opacity: 0.8;
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
    
    .custom-button.danger {
        background: var(--danger-red);
    }
    
    .custom-button.danger:hover {
        background: #DC2626;
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
    
    /* Historique */
    .history-item {
        background: var(--white);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .history-info {
        flex-grow: 1;
    }
    
    .history-actions {
        display: flex;
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
        
        .result-icon {
            font-size: 3rem;
        }
        
        .result-title {
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
        self.allowed_extensions = {".png", ".jpg", ".jpeg", ".bmp"}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, uploaded_file):
        """Valide le fichier uploadé"""
        if uploaded_file is None:
            return False, "Aucun fichier sélectionné"
        
        # Vérifier l\'extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in self.allowed_extensions:
            return False, f"Extension non autorisée. Extensions acceptées: {\", \".join(self.allowed_extensions)}"
        
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
        
        with open(temp_path, \'wb\') as f:
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
        self.detailed_classes = self.load_labels()
        self.model_path = "ResNet50V23.keras"
        self.load_model()
    
    def load_labels(self):
        """Charge labels.json (mapping nom->index) et retourne une liste index->nom."""
        hardcoded = [
            \'normal_columnar\', \'normal_intermediate\', \'normal_superficiel\',
            \'light_dysplastic\', \'moderate_dysplastic\', \'severe_dysplastic\',
            \'carcinoma_in_situ\'
        ]
        try:
            with open(\'labels.json\',\'r\',encoding=\'utf-8\') as f:
                class_indices = json.load(f)  # ex: {"carcinoma_in_situ":6, ...}
            idx_to_class = [None]*len(class_indices)
            for name, idx in class_indices.items():
                idx_to_class[idx] = name
            return idx_to_class
        except Exception as e:
            st.warning(f"labels.json introuvable ou illisible ({e}) — j\'utilise l\'ordre codé en dur.")
            return hardcoded


    def load_model(self):
        """Charge le modèle de prédiction (essaie plusieurs chemins, y compris Google Drive)."""
        try:
            if not TF_AVAILABLE:
                st.warning("⚠️ TensorFlow non disponible, mode démo")
                self.model = None
                return

            model_local_path = "ResNet50V23.keras"
            google_drive_file_id = "1nf8CpWwvDuQUaHjuju1OdPlXvvOFUwc0"

            if not os.path.exists(model_local_path):
                st.info("Téléchargement du modèle depuis Google Drive...")
                try:
                    gdown.download(id=google_drive_file_id, output=model_local_path, quiet=False)
                    st.success("✅ Modèle téléchargé avec succès !")
                except Exception as e:
                    st.error(f"❌ Erreur lors du téléchargement du modèle depuis Google Drive: {e}")
                    self.model = None
                    return

            if os.path.exists(model_local_path):
                self.model = keras.models.load_model(model_local_path)
                st.success(f"✅ Modèle chargé localement")
            else:
                st.warning("⚠️ Aucun fichier modèle trouvé localement après tentative de téléchargement, mode démo")
                self.model = None
        except Exception as e:
            st.error(f"❌ Erreur chargement modèle: {e}")
            self.model = None

    
    def preprocess_image(self, image):
        """Pré-traitement aligné avec l\'entraînement (RGB + resize 224 + /255)."""
        image = image.convert(\'RGB\').resize((224, 224))
        x = np.array(image).astype(\'float32\') / 255.0
        x = np.expand_dims(x, axis=0)
        return x


    
    def predict(self, image):
        """Fait une prédiction sur l\'image (robuste à l\'ordre des classes)."""
        try:
            processed_image = self.preprocess_image(image)

            # Par sécurité, assure l\'ordre des classes 3-niveaux
            # (doit être défini dans __init__ par ex.: self.classes = ["Normal","Précancéreux","Cancéreux"])
            if not hasattr(self, "classes"):
                self.classes = ["Normal", "Précancéreux", "Cancéreux"]

            # Noms des classes détaillées par groupe (doivent correspondre à tes dossiers)
            normal_names = {"normal_columnar", "normal_intermediate", "normal_superficiel"}
            prec_names   = {"light_dysplastic", "moderate_dysplastic", "severe_dysplastic"}
            cancer_names = {"carcinoma_in_situ"}

            if self.model is not None:
                # Prédiction réelle
                predictions = self.model.predict(processed_image, verbose=0)
                probabilities = predictions[0].astype(float)  # shape (7,)

                # Index et nom de la classe détaillée la plus probable
                predicted_class_idx = int(np.argmax(probabilities))
                # self.detailed_classes doit venir de labels.json -> idx -> name
                detailed_class = (
                    self.detailed_classes[predicted_class_idx]
                    if getattr(self, "detailed_classes", None) and\
                    predicted_class_idx < len(self.detailed_classes)
                    else "unknown"
                )

                # Mapping 7->3 par NOM de classe détaillée (pas par index)
                if detailed_class in normal_names:
                    prediction_result = "Normal"
                elif detailed_class in prec_names:
                    prediction_result = "Précancéreux"
                elif detailed_class in cancer_names:
                    prediction_result = "Cancéreux"
                else:
                    # Si le nom n\'est pas reconnu (sécurité), on choisit le groupe au max des sommes
                    prediction_result = None

                # Somme des probas par groupes en se basant sur les NOMS réels
                sums = {"Normal": 0.0, "Précancéreux": 0.0, "Cancéreux": 0.0}
                for idx, p in enumerate(probabilities):
                    # Récupère le nom réel de la classe pour cet index
                    cls_name = (
                        self.detailed_classes[idx]
                        if getattr(self, "detailed_classes", None) and idx < len(self.detailed_classes)
                        else None
                    )
                    if cls_name in normal_names:
                        sums["Normal"] += float(p)
                    elif cls_name in prec_names:
                        sums["Précancéreux"] += float(p)
                    elif cls_name in cancer_names:
                        sums["Cancéreux"] += float(p)

                total = sum(sums.values())
                if total > 0:
                    final_probs = [
                        sums["Normal"] / total,
                        sums["Précancéreux"] / total,
                        sums["Cancéreux"] / total,
                    ]
                else:
                    final_probs = [1/3, 1/3, 1/3]

                # Si le mapping direct n\'a pas donné (nom inconnu), on prend le groupe au max
                if prediction_result is None:
                    prediction_result = self.classes[int(np.argmax(final_probs))]

            else:
                # Mode démonstration
                time.sleep(2)
                final_probs = [
                    0.7, 0.2, 0.1
                ]  # Exemple de probabilités pour le mode démo
                prediction_result = "Normal"  # Exemple de résultat pour le mode démo
                detailed_class = "normal_columnar" # Exemple de classe détaillée

            confidence = final_probs[self.classes.index(prediction_result)] * 100
            return final_probs, self.classes, detailed_class
            
        except Exception as e:
            st.error(f"Erreur lors de la prédiction: {e}")
            # Retourne des valeurs par défaut en cas d\'erreur
            return [0.33, 0.33, 0.34], self.classes, "normal_columnar"

# Fonction pour générer un PDF du diagnostic
def generate_pdf_report(prediction_result, confidence, timestamp, filename, detailed_class):
    """Génère un rapport PDF du diagnostic"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        \'CustomTitle\',
        parent=styles[\'Heading1\'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor(\'#4F46E5\')
    )
    story.append(Paragraph("Rapport de Diagnostic Médical IA", title_style))
    story.append(Spacer(1, 12))
    
    # Informations générales
    info_style = styles[\'Normal\']
    story.append(Paragraph(f"<b>Date et heure:</b> {timestamp}", info_style))
    story.append(Paragraph(f"<b>Nom du fichier:</b> {filename}</b>", info_style))
    story.append(Paragraph(f"<b>Résultat:</b> {prediction_result}", info_style))
    story.append(Paragraph(f"<b>Classe détaillée:</b> {detailed_class}", info_style))
    story.append(Paragraph(f"<b>Niveau de confiance:</b> {confidence:.1f}%", info_style))
    story.append(Spacer(1, 20))
    
    # Avertissement médical
    warning_style = ParagraphStyle(
        \'Warning\',
        parent=styles[\'Normal\'],
        fontSize=12,
        textColor=colors.red,
        borderColor=colors.red,
        borderWidth=1,
        borderPadding=10
    )
    story.append(Paragraph(
        "<b>AVERTISSEMENT MÉDICAL:</b>  
"
        "Ce diagnostic automatisé est un outil d\'aide à la décision uniquement. "
        "Il ne remplace pas l\'avis d\'un professionnel de santé qualifié. "
        "Consultez toujours un médecin pour un diagnostic définitif.",
        warning_style
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Interface utilisateur
def display_header():
    """Affiche l\'en-tête de l\'application"""
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
            <p>Notre application utilise l\'intelligence artificielle avancée pour aider au dépistage du cancer du col de l\'utérus. 
            Chargez une image cytologique et obtenez un diagnostic automatisé en quelques secondes, avec une interface sécurisée et confidentielle.</p>
            <div class="privacy-notice">
                <span>🔒</span>
                <span><strong>Confidentialité garantie:</strong> Aucune donnée n\'est stockée. Traitement local et suppression automatique.</span>
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

def display_result_without_gauge(prediction, confidence, detailed_class):
    """Affiche le résultat sans jauge, avec couleurs selon la gravité"""
    if "Normal" in prediction:
        css_class = "result-normal"
        icon = "✅"
        title = "Cellules Normales"
        description = "Les cellules analysées présentent des caractéristiques normales."
    elif "Précancéreux" in prediction:
        css_class = "result-precancer"
        icon = "⚠️"
        title = "Cellules Précancéreuses"
        description = "Les cellules présentent des anomalies nécessitant une surveillance médicale."
    else:
        css_class = "result-cancer"
        icon = "🚨"
        title = "Cellules Cancéreuses"
        description = "Les cellules présentent des caractéristiques cancéreuses. Consultation urgente requise."
    
    st.markdown(f"""
    <div class="result-display {css_class} fade-in">
        <div class="result-icon">{icon}</div>
        <div class="result-title">{title}</div>
        <div class="result-description">{description}</div>
        <div class="result-confidence">Classe détaillée: {detailed_class}</div>
        <div class="result-confidence">Niveau de confiance: {confidence:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

def display_recommendations(prediction):
    """Affiche les recommandations selon la gravité"""
    st.markdown("### 📋 Recommandations")
    
    if "Normal" in prediction:
        st.success("""
        **Cellules normales détectées :**
        - Continuer les examens de dépistage réguliers selon les recommandations médicales
        - Maintenir un mode de vie sain
        - Surveillance gynécologique de routine
        """)
    elif "Précancéreux" in prediction:
        st.warning("""
        **Cellules précancéreuses détectées :**
        - **Consulter un gynécologue dans les plus brefs délais**
        - Effectuer des examens complémentaires (colposcopie, biopsie)
        - Surveillance médicale renforcée
        - Suivi régulier recommandé
        """)
    else:
        st.error("""
        **Cellules cancéreuses détectées :**
        - **Consultation médicale URGENTE requise**
        - Examens approfondis nécessaires
        - Prise en charge spécialisée recommandée
        - Ne pas retarder la consultation médicale
        """)

def display_history():
    """Affiche l\'historique des analyses"""
    st.markdown("### 📊 Historique des analyses")
    
    if not st.session_state.history:
        st.info("Aucune analyse dans l\'historique.")
        return
    
    # Bouton pour supprimer tout l\'historique
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ Tout supprimer", type="secondary"):
            st.session_state.history = []
            st.rerun()
    
    # Affichage des éléments de l\'historique
    for i, item in enumerate(reversed(st.session_state.history)):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                st.write(f"**{item[\'filename\']}**")
                st.write(f"📅 {item[\'timestamp\']}")
                st.write(f"🔬 {item[\'result\']} ({item[\'detailed_class\]})")
            
            with col2:
                st.write(f"**Confiance:** {item[\'confidence\']:.1f}%")
            
            with col3:
                # Bouton pour re-télécharger le PDF
                pdf_buffer = generate_pdf_report(
                    item[\'result\'], item[\'confidence\'], 
                    item[\'timestamp\'], item[\'filename\'], item[\'detailed_class\']
                )
                st.download_button(
                    label="📄 PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"diagnostic_{item[\'filename\']}_{item[\'timestamp\'].replace(\':\', \'-\').replace(\' \', \'_\')}.pdf",
                    mime="application/pdf",
                    key=f"download_{len(st.session_state.history)-1-i}"
                )
            
            with col4:
                # Bouton pour supprimer cet élément
                if st.button("🗑️", key=f"delete_{len(st.session_state.history)-1-i}"):
                    st.session_state.history.pop(len(st.session_state.history)-1-i)
                    st.rerun()
            
            st.divider()

# Application principale
def main():
    display_header()
    display_hero()
    
    # Initialisation du modèle
    ai_model = MedicalAIModel()
    
    # Onglets de navigation
    tab1, tab2, tab3 = st.tabs(["🔬 Analyse", "📊 Historique", "ℹ️ À propos"])
    
    with tab1:
        st.markdown("### 📤 Charger une image cytologique")
        
        # Zone d\'upload
        uploaded_file = st.file_uploader(
            "Choisissez une image cytologique",
            type=[\'png\', \'jpg\', \'jpeg\', \'bmp\'],
            help="Formats acceptés: PNG, JPG, JPEG, BMP (max 10MB)"
        )
        
        if uploaded_file is not None:
            # Affichage de l\'image
            image = Image.open(uploaded_file)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🖼️ Image chargée")
                st.image(image, caption=uploaded_file.name, use_column_width=True)
            
            with col2:
                st.markdown("#### 🔬 Analyse en cours...")
                
                # Barre de progression
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Simulation du traitement
                for i in range(100):
                    progress_bar.progress(i + 1)
                    if i < 30:
                        status_text.text("Prétraitement de l\'image...")
                    elif i < 70:
                        status_text.text("Analyse par IA...")
                    else:
                        status_text.text("Génération du rapport...")
                    time.sleep(0.02)
                
                # Prédiction
                probabilities, classes, detailed_class = ai_model.predict(image)
                
                # Détermination du résultat
                max_prob_idx = np.argmax(probabilities)
                prediction_result = classes[max_prob_idx]
                confidence = probabilities[max_prob_idx] * 100
                
                # Effacer la barre de progression
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ Analyse terminée!")
            
            # Affichage des résultats sans jauge
            display_result_without_gauge(prediction_result, confidence, detailed_class)
            
            # Affichage des recommandations
            display_recommendations(prediction_result)
            
            # Génération du PDF et ajout à l\'historique
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Bouton de téléchargement PDF
                pdf_buffer = generate_pdf_report(
                    prediction_result, confidence, timestamp, 
                    uploaded_file.name, detailed_class
                )
                
                st.download_button(
                    label="📄 Télécharger le rapport PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"diagnostic_{uploaded_file.name}_{timestamp.replace(\':\', \'-\').replace(\' \', \'_\')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            
            with col2:
                # Bouton pour ajouter à l\'historique
                if st.button("💾 Ajouter à l\'historique", type="secondary"):
                    history_item = {
                        \'filename\': uploaded_file.name,
                        \'timestamp\': timestamp,
                        \'result\': prediction_result,
                        \'detailed_class\': detailed_class,
                        \'confidence\': confidence
                    }
                    st.session_state.history.append(history_item)
                    st.success("✅ Ajouté à l\'historique!")
    
    with tab2:
        display_history()
    
    with tab3:
        st.markdown("### ℹ️ À propos de l\'application")
        
        st.markdown("""
        **SamaSanté - Diagnostic IA** est une application d\'aide au diagnostic médical utilisant l\'intelligence artificielle 
        pour l\'analyse d\'images cytologiques cervicales.
        
        #### 🧠 Technologie
        - **Modèle:** ResNet50V2 entraîné sur le dataset Herlev
        - **Classes détectées:** 7 types cellulaires regroupés en 3 catégories
        - **Prétraitement:** Conversion LAB + CLAHE pour améliorer la qualité
        
        #### 🎯 Classes détectées
        - **Normales:** normal_columnar, normal_intermediate, normal_superficiel
        - **Précancéreuses:** light_dysplastic, moderate_dysplastic, severe_dysplastic  
        - **Cancéreuses:** carcinoma_in_situ
        
        #### ⚠️ Avertissements importants
        - Cette application est un **outil d\'aide à la décision** uniquement
        - Elle **ne remplace pas** l\'avis d\'un professionnel de santé
        - Toujours **consulter un médecin** pour un diagnostic définitif
        - Particulièrement adapté aux pays en voie de développement avec accès limité aux spécialistes
        
        #### 🔒 Sécurité et confidentialité
        - Aucune donnée n\'est stockée sur nos serveurs
        - Traitement local et suppression automatique
        - Conformité RGPD garantie
        """)

if __name__ == "__main__":
    main()
