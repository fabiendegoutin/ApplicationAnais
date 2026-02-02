import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time
from google.api_core import exceptions

# --- CONFIGURATION STYLE ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    .fixed-header {
        position: fixed; top: 50px; right: 15px; width: 140px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 10px; border-radius: 20px;
        font-weight: bold; z-index: 9999; text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); border: 2px solid white;
    }
    .stProgress > div > div > div > div { background-color: #FF69B4; }
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 15px !important; height: 3.5em !important; font-size: 1.1em !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name='models/gemini-1.5-flash', # Plus stable pour le quota gratuit
    system_instruction="Tu es le coach d'Anaïs. Pose uniquement des QCM (A, B, C) basés sur le texte. Saute une ligne entre chaque choix."
)

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0
if "lancer_ballons" not in st.session_state: st.session_state.lancer_ballons = False

with st.sidebar:
    total_q = st.slider("Objectif questions", 1, 20, 10)
    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

# HEADER FIXE
st.markdown(f'<div class="fixed-header">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- 1. CHARGEMENT (AVEC SÉCURITÉ) ---
if not st.session_state.cours_texte:
    img_cam = st.camera_input("📸 Prends ton cours")
    img_file = st.file_uploader("📂 Ou choisis une photo", type=['jpg', 'png'])
    photo = img_cam if img_cam else img_file

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Analyse du cours..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((800, 800)) # Réduit la charge
                res = model.generate_content(["Extrais le texte de ce cours.", img])
                st.session_state.cours_texte = res.text
                
                # Première question
                q = model.generate_content(f"Cours: {st.session_state.cours_texte}. Pose une question QCM.")
                st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
                st.rerun()
        except exceptions.ResourceExhausted:
            st.error("⚠️ Le coach reprend son souffle ! Attends 15 secondes et reclique sur le bouton. 😊")

# --- 2. LE QUIZZ (ORDRE INVERSÉ) ---
elif st.session_state.nb_q < total_q:
    # Barre de progression fixe sous le titre
    st.write(f"Question {st.session_state.nb_q} / {total_q}")
    st.progress(st.session_state.nb_q / total_q)

    # Zone de réponse TOUJOURS EN HAUT
    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        try:
            st.session_state.nb_q += 1
            with st.spinner("Vérification..."):
                prompt = f"Cours: {st.session_state.cours_texte}. Question: {st.session_state.messages[0]['content']}. Réponse: {rep}. Dis BRAVO si juste. Pose la question QCM suivante."
                res = model.generate_content(prompt)
                
                if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                    st.session_state.xp += 20
                    st.session_state.lancer_ballons = True
                
                st.session_state.messages.insert(0, {"role": "user", "content": f"Ma réponse : {rep}"})
                st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
                st.rerun()
        except exceptions.ResourceExhausted:
            st.warning("⏱️ Trop vite ! Attends 10 secondes, le coach arrive !")
            st.session_state.nb_q -= 1 # On ne compte pas la question si erreur

    if st.session_state.lancer_ballons:
        st.balloons()
        st.session_state.lancer_ballons = False

    st.write("---")
    # Affichage du chat (récent en haut)
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and st.button("🔊 Écouter", key=f"v_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

if st.session_state.nb_q >= total_q:
    st.success(f"🏆 Bravo Anaïs ! Tu as gagné {st.session_state.xp} XP !")
