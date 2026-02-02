import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# --- 1. CONFIGURATION & STYLE (XP + BOUTONS COLORES) ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    /* Badge XP flottant */
    .fixed-header {
        position: fixed; top: 50px; right: 15px; width: 140px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 10px; border-radius: 20px;
        font-weight: bold; z-index: 9999; text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); border: 2px solid white;
    }
    /* Couleurs des boutons A, B, C */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 15px !important; height: 3.5em !important; font-weight: bold !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion avec Gemini 2.5
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

# Initialisation des variables
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None

# Affichage du score XP
st.markdown(f'<div class="fixed-header">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- 2. CHARGEMENT DU COURS ---
if not st.session_state.cours_texte:
    photo = st.camera_input("📸 Prends ton cours")
    if not photo:
        photo = st.file_uploader("📂 Ou choisis une photo", type=['jpg', 'png'])

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Lecture du cours..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((600, 600))
                res = model.generate_content(["Extrais le texte de ce cours de 6ème.", img])
                st.session_state.cours_texte = res.text
                st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- 3. LE QUIZZ & SON ---
elif len(st.session_state.messages) < 15:
    # Génération auto de la 1ère question
    if not st.session_state.messages:
        q = model.generate_content(f"Cours : {st.session_state.cours_texte}. Pose un QCM (A, B, C).")
        st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
        st.rerun()

    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        with st.spinner("Vérification..."):
            prompt = f"Cours : {st.session_state.cours_texte}. Réponse : {rep}. Dis si c'est juste, puis nouvelle question."
            res = model.generate_content(prompt)
            if "BRAVO" in res.text.upper() or "JUSTE" in res.text.upper():
                st.session_state.xp += 20
                st.balloons()
            st.session_state.messages.insert(0, {"role": "user", "content": f"Choix {rep}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    # Affichage des messages avec icône SON
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊", key=f"v_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)
