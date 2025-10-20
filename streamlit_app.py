import streamlit as st
from audio_recorder_streamlit import audio_recorder
import os
from datetime import datetime
import base64
import json
import requests

# Configuration de la page
st.set_page_config(page_title="Messagerie Vocale", page_icon="🎤", layout="wide")

# Code administrateur
ADMIN_CODE = "ruffucelechien"

# Configuration GitHub depuis Streamlit Secrets
def get_github_config():
    """Récupère la configuration GitHub depuis les secrets Streamlit"""
    try:
        return {
            "token": st.secrets["GITHUB_TOKEN"],
            "repo": st.secrets["GITHUB_REPO"],
            "branch": st.secrets.get("GITHUB_BRANCH", "main")
        }
    except:
        return None

def load_data_from_github():
    """Charge les données depuis GitHub"""
    config = get_github_config()
    if not config:
        return {"codes": [], "messages": []}
    
    try:
        url = f"https://api.github.com/repos/{config['repo']}/contents/data.json"
        headers = {
            "Authorization": f"token {config['token']}",
            "Accept": "application/vnd.github.v3+json"
        }
        params = {"ref": config['branch']}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            content = response.json()
            # Décoder le contenu base64
            data_json = base64.b64decode(content['content']).decode('utf-8')
            return json.loads(data_json)
        elif response.status_code == 404:
            # Le fichier n'existe pas encore, on le crée
            initial_data = {"codes": [], "messages": []}
            save_data_to_github(initial_data)
            return initial_data
    except Exception as e:
        st.error(f"Erreur de chargement: {str(e)}")
    
    return {"codes": [], "messages": []}

def save_data_to_github(data):
    """Sauvegarde les données sur GitHub"""
    config = get_github_config()
    if not config:
        return False
    
    try:
        url = f"https://api.github.com/repos/{config['repo']}/contents/data.json"
        headers = {
            "Authorization": f"token {config['token']}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Vérifier si le fichier existe pour obtenir le SHA
        response = requests.get(url, headers=headers, params={"ref": config['branch']}, timeout=10)
        sha = None
        if response.status_code == 200:
            sha = response.json()['sha']
        
        # Préparer le contenu
        content_json = json.dumps(data, indent=2, ensure_ascii=False)
        content_base64 = base64.b64encode(content_json.encode('utf-8')).decode('utf-8')
        
        # Créer ou mettre à jour le fichier
        payload = {
            "message": f"Update data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": content_base64,
            "branch": config['branch']
        }
        
        if sha:
            payload['sha'] = sha
        
        response = requests.put(url, headers=headers, json=payload, timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erreur de sauvegarde: {str(e)}")
        return False

# Initialisation des variables de session
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'data' not in st.session_state:
    st.session_state.data = load_data_from_github()
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = True

# Fonctions de gestion des données
def get_user_codes():
    return st.session_state.data.get("codes", [])

def add_user_code(code):
    if code not in st.session_state.data["codes"]:
        st.session_state.data["codes"].append(code)
        return save_data_to_github(st.session_state.data)
    return False

def delete_user_code(code):
    if code in st.session_state.data["codes"]:
        st.session_state.data["codes"].remove(code)
        save_data_to_github(st.session_state.data)

def get_messages():
    return st.session_state.data.get("messages", [])

def add_message(author, audio_base64):
    message = {
        "id": int(datetime.now().timestamp() * 1000),
        "author": author,
        "audio": audio_base64,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.data["messages"].append(message)
    save_data_to_github(st.session_state.data)

def delete_message(message_id):
    st.session_state.data["messages"] = [
        m for m in st.session_state.data["messages"] 
        if m["id"] != message_id
    ]
    save_data_to_github(st.session_state.data)

def delete_all_messages():
    st.session_state.data["messages"] = []
    save_data_to_github(st.session_state.data)

def reload_data():
    """Recharge les données depuis GitHub"""
    st.session_state.data = load_data_from_github()

# Fonction de connexion
def login(code):
    if code == ADMIN_CODE:
        st.session_state.authenticated = True
        st.session_state.user_type = "admin"
        return True
    elif code in get_user_codes():
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
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.title("🎤 Messagerie Vocale")
        user_badge = "👑 Administrateur" if st.session_state.user_type == "admin" else "👤 Utilisateur"
        st.markdown(f"**{user_badge}**")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualiser", help="Recharger les données depuis GitHub"):
            reload_data()
            st.success("Données actualisées ✅")
            st.rerun()
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
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
                            st.warning("Ce code existe déjà ou erreur de sauvegarde")
                    else:
                        st.error("Veuillez entrer un code")
            
            user_codes = get_user_codes()
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
    
    messages = sorted(get_messages(), key=lambda x: x['timestamp'], reverse=True)
    
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
    st.sidebar.metric("📊 Messages totaux", len(get_messages()))
    if st.session_state.user_type == "admin":
        st.sidebar.metric("👥 Codes utilisateurs", len(get_user_codes()))
        
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