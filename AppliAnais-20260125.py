import streamlit as st
from google import genai
from google.genai import types

# ==============================
# CONFIGURATION & DESIGN
# ==============================
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", page_icon="🌈", layout="centered")

# Style personnalisé
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #f0f2f6; }
    .stButton>button { border-radius: 25px; font-weight: bold; transition: 0.3s; }
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
    st.session_state.messages = [{"role": "assistant", "content": "Coucou Anaïs ! 👋 Prête à t'entraîner pour ta classe de 6ème ? Envoie-moi tes photos ! ✨"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🚀 Espace d'Anaïs</h1>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FFEB3B, #FFC107); padding: 20px; border-radius: 15px; text-align: center; color: black;'>
            <h2 style='margin: 0;'>⭐ {st.session_state.xp} XP</h2>
            <p style='margin: 0; font-weight: bold;'>Tu es super !</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    uploaded_files = st.file_uploader("📥 Photos du cours", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if st.button("🚀 LANCER LE DÉFI", use_container_width=True, type="primary"):
        if uploaded_files:
            st.session_state.quiz_en_cours = True
            st.session_state.messages = [] 
            st.session_state.first_run = True 
            st.rerun()

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

if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Anaïs, je prépare tes questions... ✨"):
            prompt_init = """Tu es un coach scolaire ultra encourageant pour Anaïs, une élève de 6ème.
            Analyse les photos. Pose la 1ère question en QCM (A, B ou C). 
            Important : Les questions doivent porter UNIQUEMENT sur le cours en photo.
            """
            contenu = [prompt_init]
            for f in uploaded_files:
                contenu.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type))
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=contenu)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.session_state.first_run = False
            st.rerun()

if prompt := st.chat_input("Réponds ici (A, B ou C)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant", avatar="🌟"):
        instruction = f"""Anaïs a répondu : '{prompt}'. 
        1. Félicite-la. Si c'est juste, dis 'BRAVO Anaïs !' et utilise des emojis de fête.
        2. Si c'est faux, explique avec douceur en utilisant tes connaissances pour l'aider à comprendre.
        3. Pose la question suivante en QCM (A, B ou C) basée sur le cours.
        """
        
        historique = [msg["content"] for msg in st.session_state.messages]
        historique.append(instruction)
        
        response = client.models.generate_content(model="gemini-2.0-flash", contents=historique)
        
        # Effet visuel si c'est correct (on cherche "bravo" dans la réponse)
        if "bravo" in response.text.lower():
            st.balloons()
            st.session_state.xp += 20
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()
