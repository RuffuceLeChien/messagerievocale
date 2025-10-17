import streamlit as st
import os
from datetime import datetime
import json

# Configuration de la page
st.set_page_config(page_title="Messagerie Vocale", page_icon="🎤", layout="wide")

# Initialisation des variables de session
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_codes' not in st.session_state:
    st.session_state.user_codes = []
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Code administrateur
ADMIN_CODE = "ruffucelechien"

# Fonction de connexion
def login(code):
    if code == ADMIN_CODE:
        st.session_state.authenticated = True
        st.session_state.user_type = "admin"
        return True
    elif code in st.session_state.user_codes:
        st.session_state.authenticated = True
        st.session_state.user_type = "user"
        return True
    return False

# Fonction de déconnexion
def logout():
    st.session_state.authenticated = False
    st.session_state.user_type = None

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
            
            new_code = st.text_input("Ajouter un nouveau code", key="new_code")
            if st.button("Ajouter le code"):
                if new_code and new_code not in st.session_state.user_codes:
                    st.session_state.user_codes.append(new_code)
                    st.success(f"Code '{new_code}' ajouté avec succès")
                    st.rerun()
                elif new_code in st.session_state.user_codes:
                    st.warning("Ce code existe déjà")
            
            if st.session_state.user_codes:
                st.write("**Liste des codes actifs:**")
                for idx, code in enumerate(st.session_state.user_codes):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"🔑 {code}")
                    with col2:
                        if st.button("Supprimer", key=f"del_code_{idx}"):
                            st.session_state.user_codes.remove(code)
                            st.rerun()
            else:
                st.info("Aucun code utilisateur configuré")
        
        st.markdown("---")
    
    # Section d'enregistrement
    st.subheader("📝 Enregistrer un message")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        message_text = st.text_area(
            "Contenu du message (simulé - audio à implémenter avec audio-recorder-streamlit)",
            height=100,
            placeholder="Maintenez le bouton micro pour enregistrer votre message vocal..."
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🎤 Enregistrer", type="primary", use_container_width=True):
            if message_text:
                new_message = {
                    "id": len(st.session_state.messages),
                    "author": st.session_state.user_type,
                    "content": message_text,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.messages.append(new_message)
                st.success("Message enregistré!")
                st.rerun()
            else:
                st.warning("Veuillez saisir un message")
    
    st.info("💡 **Note**: Pour un vrai enregistrement audio, installez: `pip install audio-recorder-streamlit`")
    
    st.markdown("---")
    
    # Liste des messages
    st.subheader("📬 Messages vocaux")
    
    if st.session_state.messages:
        for msg in reversed(st.session_state.messages):
            with st.container():
                col1, col2, col3 = st.columns([2, 3, 1])
                
                with col1:
                    author_icon = "👑" if msg["author"] == "admin" else "👤"
                    st.markdown(f"**{author_icon} {msg['author'].capitalize()}**")
                    st.caption(msg["timestamp"])
                
                with col2:
                    st.text(msg["content"])
                
                with col3:
                    if st.button("🗑️ Supprimer", key=f"del_msg_{msg['id']}"):
                        st.session_state.messages = [m for m in st.session_state.messages if m['id'] != msg['id']]
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("Aucun message enregistré pour le moment")

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
</style>
""", unsafe_allow_html=True)