import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# ==============================
# CONFIGURATION & STYLE
# ==============================
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", page_icon="🌈")

# Design adapté au pouce sur mobile
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stButton>button { border-radius: 25px; height: 60px; font-size: 18px !important; }
    .main-title { text-align: center; color: #FFC107; font-size: 30px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Connexion à Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# ==============================
# INITIALISATION MÉMOIRE
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Coucou Anaïs ! 👋 Prends une photo de ton cours pour commencer !"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False
if "photos_valides" not in st.session_state: st.session_state.photos_valides = []

# ==============================
# INTERFACE D'ACCUEIL
# ==============================
st.markdown('<p class="main-title">🌟 Mon Coach Magique</p>', unsafe_allow_html=True)

if not st.session_state.quiz_en_cours:
    # Utilisation du composant CAMERA direct (plus fiable sur Android)
    photo_capture = st.camera_input("📸 Prends ton cours en photo ici")
    
    if photo_capture:
        # On transforme et on stocke immédiatement
        img = Image.open(photo_capture)
        st.session_state.photos_valides = [img] # On peut en mettre plusieurs ici
        st.success("✅ Photo capturée ! Elle est prête.")
        
        if st.button("🚀 CLIQUE ICI POUR LANCER LE QUIZ", type="primary"):
            st.session_state.quiz_en_cours = True
            st.session_state.messages = [{"role": "assistant", "content": "C'est parti ! J'analyse ta photo... ⏳"}]
            st.session_state.first_run = True
            st.rerun()

# ==============================
# ZONE DE CHAT (QUIZ)
# ==============================
if st.session_state.quiz_en_cours:
    # Affichage du score en haut
    st.info(f"⭐ Points d'Anaïs : {st.session_state.xp} XP")

    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar=("👤" if msg["role"] == "user" else "🌟")):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"v_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

# ==============================
# LOGIQUE DU COACH
# ==============================
def interroger_coach(instruction):
    # On force l'envoi de la photo à chaque fois
    reponse = model.generate_content([instruction] + st.session_state.photos_valides)
    return reponse.text

if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.spinner("Je lis ta leçon..."):
        res = interroger_coach("Tu es le coach d'Anaïs (6ème). Pose la 1ère question QCM (A, B, C) basée sur la photo. Saute des lignes entre les choix.")
        st.session_state.messages.append({"role": "assistant", "content": res})
        st.session_state.first_run = False
        st.rerun()

if prompt := st.chat_input("Ta réponse (A, B ou C)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Je vérifie... ✨"):
        res = interroger_coach(f"Anaïs a répondu '{prompt}'. Vérifie sur la photo. Félicite-la et pose la question suivante en QCM.")
        if any(w in res.lower() for w in ["bravo", "juste", "super"]):
            st.balloons()
            st.session_state.xp += 20
        st.session_state.messages.append({"role": "assistant", "content": res})
        st.rerun()
