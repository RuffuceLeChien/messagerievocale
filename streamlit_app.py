import streamlit as st
from audio_recorder_streamlit import audio_recorder
import os
from datetime import datetime
import base64
import sqlite3
from pathlib import Path
import hashlib

# Configuration de la page
st.set_page_config(page_title="Messagerie Vocale", page_icon="🎤", layout="wide")

# Chemin de la base de données
DB_PATH = "/mount/data/messagerie_vocale.db"

# Code administrateur
ADMIN_CODE = "ruffucelechien"

# Initialisation de la base de données
def init_database():
    """Initialise la base de données SQLite avec les tables nécessaires"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table des codes utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des messages vocaux
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            audio_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Fonctions de gestion des codes utilisateurs
def get_all_user_codes():
    """Récupère tous les codes utilisateurs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM user_codes ORDER BY created_at DESC")
    codes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return codes

def add_user_code(code):
    """Ajoute un nouveau code utilisateur"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_codes (code) VALUES (?)", (code,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def delete_user_code(code):
    """Supprime un code utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_codes WHERE code = ?", (code,))
    conn.commit()
    conn.close()

# Fonctions de gestion des messages
def get_all_messages():
    """Récupère tous les messages"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, author, audio_data, created_at 
        FROM messages 
        ORDER BY created_at DESC
    """)
    messages = []
    for row in cursor.fetchall():
        messages.append({
            "id": row[0],
            "author": row[1],
            "audio": row[2],
            "timestamp": row[3]
        })
    conn.close()
    return messages

def add_message(author, audio_base64):
    """Ajoute un nouveau message"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messages (author, audio_data) 
        VALUES (?, ?)
    """, (author, audio_base64))
    conn.commit()
    conn.close()

def delete_message(message_id):
    """Supprime un message"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()

def delete_all_messages():
    """Supprime tous les messages"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

def get_message_count():
    """Compte le nombre total de messages"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Initialiser la base de données au démarrage
init_database()

# Initialisation des variables de session
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

# Fonction de connexion
def login(code):
    if code == ADMIN_CODE:
        st.session_state.authenticated = True
        st.session_state.user_type = "admin"
        return True
    elif code in get_all_user_codes():
        st.session_state.authenticated = True
        st.session_state.user_type = "user"
        return True
    return False

# Fonction de déconnexion
def logout():
    st.session_state.authenticated = False
    st.session_state.user_type = None

# Fonction pour convertir audio en base64
def audio_to_base64(audio_bytes):
    return base64.b64encode(audio_bytes).decode()

# Fonction pour afficher le lecteur audio
def display_audio_player(audio_base64):
    audio_html = f"""
    <audio controls style="width: 100%;">
        <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
        Votre navigateur ne supporte pas l'élément audio.
    </audio>
    """
    return audio_html

# Interface de connexion
if not st.session_state.authenticated:
    st.title("🎤 Messagerie Vocale")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Connexion")
        code_input = st.text_input("Entrez votre code d'accès", type="password", key="login_code")
        
        if st.button("Se connecter", type="primary", use_container_width=True):
            if login(code_input):
                st.success(f"Connexion réussie en tant que {'Administrateur' if st.session_state.user_type == 'admin' else 'Utilisateur'}")
                st.rerun()
            else:
                st.error("Code incorrect")

# Interface principale (après connexion)
else:
    # En-tête
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🎤 Messagerie Vocale")
        user_badge = "👑 Administrateur" if st.session_state.user_type == "admin" else "👤 Utilisateur"
        st.markdown(f"**{user_badge}**")
    with col2:
        if st.button("Déconnexion", type="secondary"):
            logout()
            st.rerun()
    
    st.markdown("---")
    
    # Gestion des codes utilisateurs (Admin uniquement)
    if st.session_state.user_type == "admin":
        with st.expander("⚙️ Gestion des codes utilisateurs"):
            st.subheader("Codes autorisés")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                new_code = st.text_input("Ajouter un nouveau code", key="new_code")
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Ajouter", use_container_width=True):
                    if new_code:
                        if add_user_code(new_code):
                            st.success(f"Code '{new_code}' ajouté avec succès ✅")
                            st.rerun()
                        else:
                            st.warning("Ce code existe déjà")
                    else:
                        st.error("Veuillez entrer un code")
            
            user_codes = get_all_user_codes()
            if user_codes:
                st.write("**Liste des codes actifs:**")
                for idx, code in enumerate(user_codes):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"🔑 {code}")
                    with col2:
                        if st.button("🗑️", key=f"del_code_{idx}", help="Supprimer"):
                            delete_user_code(code)
                            st.success("Code supprimé ✅")
                            st.rerun()
            else:
                st.info("Aucun code utilisateur configuré")
        
        st.markdown("---")
    
    # Section d'enregistrement
    st.subheader("📝 Enregistrer un message vocal")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**Maintenez le bouton pour enregistrer :**")
        audio_bytes = audio_recorder(
            text="Cliquez et maintenez pour enregistrer",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_name="microphone",
            icon_size="3x",
            pause_threshold=2.0
        )
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("💾 Sauvegarder", type="primary", use_container_width=True, disabled=not audio_bytes):
            if audio_bytes:
                audio_base64 = audio_to_base64(audio_bytes)
                add_message(st.session_state.user_type, audio_base64)
                st.success("Message vocal enregistré et sauvegardé! ✅")
                st.rerun()
    
    if audio_bytes:
        st.info("✅ Message vocal prêt à être sauvegardé")
    
    st.markdown("---")
    
    # Liste des messages
    st.subheader("📬 Messages vocaux")
    
    messages = get_all_messages()
    
    if messages:
        for msg in messages:
            with st.container():
                col1, col2, col3 = st.columns([2, 4, 1])
                
                with col1:
                    author_icon = "👑" if msg["author"] == "admin" else "👤"
                    st.markdown(f"**{author_icon} {msg['author'].capitalize()}**")
                    st.caption(msg["timestamp"])
                
                with col2:
                    st.markdown(display_audio_player(msg["audio"]), unsafe_allow_html=True)
                
                with col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_msg_{msg['id']}", help="Supprimer"):
                        delete_message(msg['id'])
                        st.success("Message supprimé ✅")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("Aucun message enregistré pour le moment")
    
    # Statistiques dans la sidebar
    st.sidebar.metric("📊 Messages totaux", get_message_count())
    if st.session_state.user_type == "admin":
        st.sidebar.metric("👥 Codes utilisateurs", len(get_all_user_codes()))
        
        # Option pour effacer toutes les données (Admin uniquement)
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚠️ Zone dangereuse")
        
        with st.sidebar.expander("🗑️ Supprimer tous les messages"):
            st.warning("Cette action est irréversible!")
            confirm = st.checkbox("Je confirme vouloir supprimer tous les messages")
            if st.button("Supprimer définitivement", type="secondary", disabled=not confirm):
                delete_all_messages()
                st.success("Tous les messages ont été supprimés")
                st.rerun()

# CSS personnalisé
st.markdown("""
<style>
    .stButton button {
        border-radius: 10px;
    }
    div[data-testid="stExpander"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
    audio {
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)