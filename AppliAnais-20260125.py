import streamlit as st
from google import genai
from google.genai import types

# ==============================
# CONFIGURATION & DESIGN
# ==============================
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", page_icon="🌈", layout="centered")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #f0f2f6; }
    .stButton>button { border-radius: 25px; font-weight: bold; transition: 0.3s; width: 100%; }
    /* Style pour le conteneur de téléchargement au centre */
    .upload-container { background-color: #f9f9f9; padding: 20px; border-radius: 15px; border: 2px dashed #FFC107; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==============================
# INITIALISATION DE LA SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Coucou Anaïs ! 👋 Prête à t'entraîner pour ta classe de 6ème ? Envoie-moi tes photos juste en dessous ! ✨"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False

# ==============================
# SIDEBAR (Uniquement pour le Score)
# ==============================
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🚀 Progression</h1>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FFEB3B, #FFC107); padding: 20px; border-radius: 15px; text-align: center; color: black;'>
            <h2 style='margin: 0;'>⭐ {st.session_state.xp} XP</h2>
            <p style='margin: 0; font-weight: bold;'>Bravo Anaïs !</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🗑️ Recommencer tout"):
        st.session_state.messages = [{"role": "assistant", "content": "C'est reparti ! 🎈"}]
        st.session_state.quiz_en_cours = False
        st.session_state.xp = 0
        st.rerun()

# ==============================
# ZONE CENTRALE : TÉLÉCHARGEMENT
# ==============================
st.title("🌟 Mon Coach Magique")

# On n'affiche la zone de téléchargement que si le quiz n'est pas déjà lancé 
# ou on la laisse pour pouvoir rajouter des pages.
with st.container():
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader("📸 Dépose tes photos de cours ici pour Anaïs", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if st.button("🚀 LANCER LE DÉFI QCM", type="primary"):
        if uploaded_files:
            st.session_state.quiz_en_cours = True
            st.session_state.messages = [{"role": "assistant", "content": "C'est parti ! Je prépare tes questions... ⏳"}] 
            st.session_state.first_run = True 
            # On ne fait pas de rerun ici pour laisser la logique s'exécuter
        else:
            st.warning("Ajoute des photos de ton cours d'abord ! 😊")
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ZONE DE CHAT
# ==============================
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🌟"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            with st.expander("🔊 Écouter"):
                st.audio(f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=fr&q={message['content'].replace(' ', '+')}", format="audio/mp3")

# ==============================
# LOGIQUE DU COACH
# ==============================

# 1. Lancement (Envoi des images)
if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Lecture du cours..."):
            prompt_init = """Tu es un coach scolaire ultra encourageant pour Anaïs (élève de 6ème).
            Pose la 1ère question en QCM (A, B ou C) basée uniquement sur les photos.
            IMPORTANT : Saute une ligne entre chaque option A, B et C.
            """
            contenu = [prompt_init]
            for f in uploaded_files:
                contenu.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type))
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=contenu)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.session_state.first_run = False
            st.rerun()

# 2. Réponses au Chat
if prompt := st.chat_input("Ta réponse ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant", avatar="🌟"):
        instruction = f"""Anaïs a répondu : '{prompt}'. 
        1. Félicite-la chaleureusement.
        2. Si c'est faux, explique pédagogiquement en utilisant tes connaissances.
        3. Pose la question suivante en QCM (A, B ou C).
        Saute bien une ligne entre chaque option.
        """
        
        historique = [msg["content"] for msg in st.session_state.messages]
        historique.append(instruction)
        
        response = client.models.generate_content(model="gemini-2.0-flash", contents=historique)
        
        if "bravo" in response.text.lower() or "super" in response.text.lower():
            st.balloons()
            st.session_state.xp += 20
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()
