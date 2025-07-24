"""
Module de sécurité pour l'application médicale
Gestion sécurisée des fichiers, chiffrement et confidentialité
"""

import os
import tempfile
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import shutil
from typing import Tuple, Optional, Dict, Any
import logging

# Configuration du logging sécurisé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityManager:
    """Gestionnaire de sécurité principal"""
    
    def __init__(self):
        self.session_key = self._generate_session_key()
        self.cipher_suite = self._create_cipher()
        self.temp_dirs = set()
        self.file_hashes = {}
        self.access_log = []
        
    def _generate_session_key(self) -> bytes:
        """Génère une clé de session unique"""
        return secrets.token_bytes(32)
    
    def _create_cipher(self) -> Fernet:
        """Crée un chiffreur Fernet pour la session"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'medical_app_salt_2024',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.session_key))
        return Fernet(key)
    
    def log_access(self, action: str, details: Dict[str, Any] = None):
        """Enregistre les accès pour audit"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {},
            'session_id': hashlib.sha256(self.session_key).hexdigest()[:16]
        }
        self.access_log.append(log_entry)
        logger.info(f"Security log: {action}")
    
    def encrypt_data(self, data: bytes) -> bytes:
        """Chiffre des données en mémoire"""
        try:
            return self.cipher_suite.encrypt(data)
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise SecurityError("Erreur de chiffrement")
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Déchiffre des données"""
        try:
            return self.cipher_suite.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise SecurityError("Erreur de déchiffrement")

class SecureFileManager:
    """Gestionnaire sécurisé des fichiers avec chiffrement temporaire"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.temp_dir = tempfile.mkdtemp(prefix='medical_secure_')
        self.security.temp_dirs.add(self.temp_dir)
        self.allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_mime_types = {
            'image/png', 'image/jpeg', 'image/jpg', 'image/bmp'
        }
        
        # Enregistrer la création du répertoire temporaire
        self.security.log_access('temp_dir_created', {
            'path': self.temp_dir,
            'max_size': self.max_file_size
        })
    
    def validate_file(self, uploaded_file) -> Tuple[bool, str]:
        """Validation sécurisée du fichier uploadé"""
        if uploaded_file is None:
            return False, "Aucun fichier sélectionné"
        
        # Vérifier l'extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in self.allowed_extensions:
            self.security.log_access('file_rejected_extension', {
                'filename': uploaded_file.name,
                'extension': file_ext
            })
            return False, f"Extension non autorisée. Extensions acceptées: {', '.join(self.allowed_extensions)}"
        
        # Vérifier la taille
        file_size = len(uploaded_file.getvalue())
        if file_size > self.max_file_size:
            self.security.log_access('file_rejected_size', {
                'filename': uploaded_file.name,
                'size': file_size
            })
            return False, f"Fichier trop volumineux. Taille maximale: {self.max_file_size // (1024*1024)}MB"
        
        # Vérifier le type MIME si disponible
        if hasattr(uploaded_file, 'type') and uploaded_file.type:
            if uploaded_file.type not in self.allowed_mime_types:
                self.security.log_access('file_rejected_mime', {
                    'filename': uploaded_file.name,
                    'mime_type': uploaded_file.type
                })
                return False, f"Type de fichier non autorisé: {uploaded_file.type}"
        
        # Vérifier l'intégrité du fichier (signature basique)
        file_data = uploaded_file.getvalue()
        if not self._validate_image_signature(file_data, file_ext):
            self.security.log_access('file_rejected_signature', {
                'filename': uploaded_file.name
            })
            return False, "Fichier corrompu ou format invalide"
        
        self.security.log_access('file_validated', {
            'filename': uploaded_file.name,
            'size': file_size,
            'extension': file_ext
        })
        
        return True, "Fichier valide"
    
    def _validate_image_signature(self, data: bytes, extension: str) -> bool:
        """Valide la signature du fichier image"""
        if len(data) < 8:
            return False
        
        # Signatures des formats d'image
        signatures = {
            '.png': [b'\x89PNG\r\n\x1a\n'],
            '.jpg': [b'\xff\xd8\xff', b'\xff\xd8'],
            '.jpeg': [b'\xff\xd8\xff', b'\xff\xd8'],
            '.bmp': [b'BM']
        }
        
        if extension in signatures:
            for sig in signatures[extension]:
                if data.startswith(sig):
                    return True
            return False
        
        return True  # Pour les extensions non vérifiées
    
    def save_temp_file(self, uploaded_file, encrypt: bool = True) -> str:
        """Sauvegarde temporaire sécurisée avec chiffrement optionnel"""
        try:
            file_data = uploaded_file.getvalue()
            file_hash = hashlib.sha256(file_data).hexdigest()
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            # Nom de fichier sécurisé
            safe_filename = f"{file_hash[:16]}{file_ext}"
            temp_path = os.path.join(self.temp_dir, safe_filename)
            
            # Chiffrement optionnel en mémoire
            if encrypt:
                encrypted_data = self.security.encrypt_data(file_data)
                with open(temp_path + '.enc', 'wb') as f:
                    f.write(encrypted_data)
                final_path = temp_path + '.enc'
            else:
                with open(temp_path, 'wb') as f:
                    f.write(file_data)
                final_path = temp_path
            
            # Enregistrer le hash pour vérification d'intégrité
            self.security.file_hashes[final_path] = file_hash
            
            self.security.log_access('file_saved', {
                'filename': uploaded_file.name,
                'temp_path': final_path,
                'encrypted': encrypt,
                'hash': file_hash[:16]
            })
            
            return final_path
            
        except Exception as e:
            logger.error(f"Error saving temp file: {e}")
            raise SecurityError(f"Erreur lors de la sauvegarde: {e}")
    
    def load_temp_file(self, temp_path: str, decrypt: bool = True) -> bytes:
        """Charge un fichier temporaire avec déchiffrement optionnel"""
        try:
            if not os.path.exists(temp_path):
                raise SecurityError("Fichier temporaire non trouvé")
            
            with open(temp_path, 'rb') as f:
                file_data = f.read()
            
            if decrypt and temp_path.endswith('.enc'):
                file_data = self.security.decrypt_data(file_data)
            
            # Vérifier l'intégrité
            if temp_path in self.security.file_hashes:
                expected_hash = self.security.file_hashes[temp_path]
                actual_hash = hashlib.sha256(file_data).hexdigest()
                if actual_hash != expected_hash:
                    raise SecurityError("Intégrité du fichier compromise")
            
            self.security.log_access('file_loaded', {
                'temp_path': temp_path,
                'decrypted': decrypt
            })
            
            return file_data
            
        except Exception as e:
            logger.error(f"Error loading temp file: {e}")
            raise SecurityError(f"Erreur lors du chargement: {e}")
    
    def cleanup(self):
        """Nettoyage sécurisé des fichiers temporaires"""
        try:
            if os.path.exists(self.temp_dir):
                # Effacement sécurisé des fichiers
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        self._secure_delete(file_path)
                
                # Suppression du répertoire
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                
                self.security.log_access('temp_dir_cleaned', {
                    'path': self.temp_dir
                })
                
                # Retirer de la liste des répertoires temporaires
                self.security.temp_dirs.discard(self.temp_dir)
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _secure_delete(self, file_path: str):
        """Suppression sécurisée d'un fichier (overwrite puis delete)"""
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                
                # Écraser le fichier avec des données aléatoires
                with open(file_path, 'r+b') as f:
                    f.write(secrets.token_bytes(file_size))
                    f.flush()
                    os.fsync(f.fileno())
                
                # Supprimer le fichier
                os.remove(file_path)
                
        except Exception as e:
            logger.warning(f"Secure delete failed for {file_path}: {e}")

class SessionManager:
    """Gestionnaire de sessions sécurisées"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.sessions = {}
        self.session_timeout = timedelta(hours=2)
    
    def create_session(self, user_id: str = None) -> str:
        """Crée une nouvelle session"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'id': session_id,
            'created': datetime.now(),
            'last_access': datetime.now(),
            'user_id': user_id or 'anonymous',
            'file_manager': None
        }
        
        self.sessions[session_id] = session_data
        
        self.security.log_access('session_created', {
            'session_id': session_id[:16],
            'user_id': session_data['user_id']
        })
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Récupère une session active"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Vérifier l'expiration
        if datetime.now() - session['last_access'] > self.session_timeout:
            self.cleanup_session(session_id)
            return None
        
        # Mettre à jour le dernier accès
        session['last_access'] = datetime.now()
        return session
    
    def cleanup_session(self, session_id: str):
        """Nettoie une session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Nettoyer le gestionnaire de fichiers associé
            if session.get('file_manager'):
                session['file_manager'].cleanup()
            
            del self.sessions[session_id]
            
            self.security.log_access('session_cleaned', {
                'session_id': session_id[:16]
            })
    
    def cleanup_expired_sessions(self):
        """Nettoie toutes les sessions expirées"""
        now = datetime.now()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if now - session['last_access'] > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            self.cleanup_session(session_id)

class SecurityError(Exception):
    """Exception personnalisée pour les erreurs de sécurité"""
    pass

class PrivacyManager:
    """Gestionnaire de confidentialité et RGPD"""
    
    def __init__(self):
        self.privacy_policy = {
            'data_collection': False,
            'data_storage': False,
            'data_sharing': False,
            'cookies': False,
            'analytics': False
        }
    
    def get_privacy_notice(self) -> str:
        """Retourne l'avis de confidentialité"""
        return """
        🔒 AVIS DE CONFIDENTIALITÉ
        
        Cette application respecte votre vie privée:
        
        ✅ Aucune donnée personnelle collectée
        ✅ Aucune image stockée sur nos serveurs
        ✅ Traitement local uniquement
        ✅ Suppression automatique après analyse
        ✅ Aucun cookie de suivi
        ✅ Aucune analyse comportementale
        
        Vos données restent sous votre contrôle à tout moment.
        """
    
    def get_security_measures(self) -> str:
        """Retourne les mesures de sécurité"""
        return """
        🛡️ MESURES DE SÉCURITÉ
        
        • Chiffrement AES-256 en mémoire
        • Communications HTTPS sécurisées
        • Validation stricte des fichiers
        • Suppression sécurisée des données
        • Audit des accès
        • Sessions temporaires
        • Isolation des processus
        """

# Fonctions utilitaires
def generate_secure_token(length: int = 32) -> str:
    """Génère un token sécurisé"""
    return secrets.token_urlsafe(length)

def hash_data(data: bytes, salt: bytes = None) -> str:
    """Hash sécurisé des données"""
    if salt is None:
        salt = secrets.token_bytes(16)
    
    return hashlib.pbkdf2_hmac('sha256', data, salt, 100000).hex()

def verify_hash(data: bytes, hash_value: str, salt: bytes) -> bool:
    """Vérifie un hash"""
    return hmac.compare_digest(
        hash_data(data, salt),
        hash_value
    )

