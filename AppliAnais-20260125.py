import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time
from google.api_core import exceptions

# --- CONFIGURATION STYLE MODERNE ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    /* Badge XP Flottant avec Dégradé */
    .fixed-score {
        position: fixed; top: 70px; right: 20px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 10px 22px; border-radius: 50px;
        font-weight: 800; z-index: 9999;
        box-shadow: 0 4px 15px rgba(255, 105, 180, 0.4);
        border: 2px solid rgba(255, 255, 255, 0.8);
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Boutons de réponse style "Bulle" */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 18px !important;
        border: none !important;
        height: 4.5em !important;
        font-size: 1.2em !important;
        transition: transform 0.2s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="stHorizontalBlock"] button:active { transform: scale(0.95); }
    
    /* Style des cartes de messages */
    .stChatMessage { border-radius: 20px !important; padding: 15px !important; margin-bottom: 10px !important; }
    
    /* Bouton Lancer Le Quizz */
    .main-button button {
        background: linear-gradient(90deg, #4CAF50, #45a049) !important;
        color: white !important;
        font-size: 1.1em !important;
        height: 3.5em !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONNEXION & LOGIQUE ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction="Tu es le coach d'Anaïs. Ton style est 'Minimaliste & Fun'. Phrases ultra-courtes. Utilise ✨, ⚡, 🎈. Ne pose qu'UNE question à la fois."
    )
except:
    st.error("Défaut de connexion à l'IA.")

# Initialisation
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0
if "recompense" not in st.session_state: st.session_state.recompense = False

# Sidebar
with st.sidebar:
    st.markdown("### 🧩 Menu Anaïs")
    max_questions = st.slider("Objectif :", 1, 20, 10)
    if st.button("🗑️ Nouveau cours"):
        st.session_state.clear()
        st.rerun()

# Score
st.markdown(f'<div class="fixed-score">⚡ {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- 1. CAPTURE ---
if not st.session_state.cours_texte:
    st.write("### 📸 Prends ton cours en photo")
    img_cap = st.camera_input("Capture ton cours ici")
    if not img_cap:
        img_cap = st.file_uploader("Ou télécharge une image", type=['jpg', 'png'])

    if img_cap:
        st.markdown('<div class="main-button">', unsafe_allow_html=True)
        if st.button("🚀 PRÉPARER MON QUIZZ", use_container_width=True):
            try:
                with st.spinner("Lecture magique en cours..."):
                    img = Image.open(img_cap).convert("RGB")
                    img.thumbnail((1024, 1024))
                    res = model.generate_content(["Extrais le texte de ce cours.", img])
                    st.session_state.cours_texte = res.text
                    st.rerun()
            except exceptions.ResourceExhausted:
                st.warning("L'IA se repose 30 secondes... ☕")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 2. LE QUIZZ ---
elif st.session_state.nb_q < max_questions:
    if not st.session_state.messages:
        try:
            res = model.generate_content(f"Cours: {st.session_state.cours_texte}. Pose une question QCM courte.")
            st.session_state.messages.append({"role": "assistant", "content": res.text})
        except: st.error("Le coach a un petit souci technique.")

    # Chat
    for i, msg in enumerate(st.session_state.messages):
        avatar = "🌈" if msg["role"]=="assistant" else "⭐"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"a_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

    # Zone de réponse
    st.markdown(f"**Question {st.session_state.nb_q + 1} / {max_questions}**")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("🅰️", use_container_width=True): choix = "A"
    if c2.button("🅱️", use_container_width=True): choix = "B"
    if c3.button("🅲", use_container_width=True): choix = "C"

    if choix:
        st.session_state.nb_q += 1
        try:
            with st.spinner("Vérification..."):
                prompt = f"Cours: {st.session_state.cours_texte}. Réponse d'Anaïs: {choix}. Si juste dis BRAVO. Pose la suite."
                res = model.generate_content(prompt)
                
                if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                    st.balloons()
                    st.session_state.xp += 20
                    if st.session_state.xp % 200 == 0:
                        st.session_state.recompense = True
                
                st.session_state.messages.append({"role": "user", "content": f"Je choisis la {choix}"})
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                st.rerun()
        except exceptions.ResourceExhausted:
            st.error("On attend un peu le coach ! 😊")

# --- 3. RÉCOMPENSE ---
if st.session_state.recompense:
    st.snow()
    st.success("### 🏆 NIVEAU SUPÉRIEUR !")
    st.image(f"https://loremflickr.com/600/400/cute,puppy?lock={st.session_state.xp}", caption="Ton cadeau spécial !")
    if st.button("Continuer l'aventure ✨"):
        st.session_state.recompense = False
        st.rerun()

if st.session_state.nb_q >= max_questions:
    st.info("🎯 Mission accomplie ! Tu as bien travaillé aujourd'hui !")
