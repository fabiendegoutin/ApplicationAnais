import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time
from google.api_core import exceptions

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    .fixed-score {
        position: fixed; top: 60px; right: 15px;
        background-color: #FF69B4; color: white;
        padding: 12px 20px; border-radius: 30px;
        font-weight: bold; z-index: 9999;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        border: 2px solid white; font-size: 1.1em;
    }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name='models/gemini-2.0-flash',
    system_instruction="Tu es le coach d'Anaïs (12 ans, TDAH). Tu es ultra-positif, encourageant, et tu fais des phrases courtes. Utilise des emojis. Ne pose qu'une seule question à la fois."
)

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_questions" not in st.session_state: st.session_state.nb_questions = 0
if "palier_atteint" not in st.session_state: st.session_state.palier_atteint = False

# --- SIDEBAR (RÉGLAGES) ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    total_q = st.slider("Nombre de questions :", 1, 20, 10)
    if st.button("🗑️ Recommencer une leçon"):
        st.session_state.clear()
        st.rerun()

st.markdown(f'<div class="fixed-score">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- ETAPE 1 : CHARGEMENT DU COURS ---
if not st.session_state.cours_texte:
    st.write("### 📸 Prends ton cours en photo")
    img_file = st.camera_input("Souris ! 📸") # Utilisation du mode caméra natif
    if not img_file:
        img_file = st.file_uploader("Ou télécharge une image", type=['jpg', 'png', 'jpeg'])

    if img_file and st.button("🚀 PRÉPARER LE QUIZZ"):
        try:
            with st.spinner("Je lis ton cours..."):
                img = Image.open(img_file).convert("RGB")
                # Optimisation : on réduit l'image avant envoi pour économiser
                img.thumbnail((800, 800))
                res = model.generate_content(["Extrais le texte de ce cours pour une élève de 6ème.", img])
                st.session_state.cours_texte = res.text
                st.rerun()
        except exceptions.ResourceExhausted:
            st.error("Le coach est un peu fatigué (limite API). Attends une minute et réessaie ! ☕")

# --- ETAPE 2 : LE QUIZZ ---
if st.session_state.cours_texte and st.session_state.nb_questions < total_q:
    # Générer la première question si vide
    if not st.session_state.messages:
        try:
            q = model.generate_content(f"Cours: {st.session_state.cours_texte}. Pose une question QCM (A, B, C) joyeuse.")
            st.session_state.messages.append({"role": "assistant", "content": q.text})
        except exceptions.ResourceExhausted:
            st.warning("Minute papillon ! Le coach reprend son souffle... Réessaie dans 10 secondes.")

    # Affichage du chat
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"v_{i}"):
                    clean = msg["content"].replace("A)", "Réponse A").replace("B)", "Réponse B").replace("C)", "Réponse C")
                    tts = gTTS(text=clean, lang='fr', slow=False)
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

    # Boutons de réponse
    st.write(f"📊 Question {st.session_state.nb_questions + 1} sur {total_q}")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A", use_container_width=True): choix = "A"
    if c2.button("B", use_container_width=True): choix = "B"
    if c3.button("C", use_container_width=True): choix = "C"

    if choix:
        st.session_state.nb_questions += 1
        try:
            with st.spinner("Vérification..."):
                prompt = f"Cours: {st.session_state.cours_texte}. Question: {st.session_state.messages[-1]['content']}. Anaïs a dit {choix}. Juste ou faux ? Si juste, dis 'BRAVO'. Pose la question suivante."
                res = model.generate_content(prompt)
                
                if any(w in res.text.upper() for w in ["BRAVO", "CORRECT", "JUSTE"]):
                    st.balloons()
                    st.session_state.xp += 20
                
                st.session_state.messages.append({"role": "user", "content": f"Ma réponse : {choix}"})
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                
                # Vérification du palier 200 XP
                if st.session_state.xp >= 200 and not st.session_state.palier_atteint:
                    st.session_state.palier_atteint = True
                
                st.rerun()
        except exceptions.ResourceExhausted:
            st.error("Trop de questions d'un coup ! Attends 30 secondes, le coach se repose. 😊")

# --- RÉCOMPENSE ---
if st.session_state.palier_atteint:
    st.snow()
    st.success("### 🏆 INCROYABLE ! TU AS ATTEINT 200 XP !")
    # Image aléatoire d'animal mignon pour la récompense
    st.image("https://loremflickr.com/400/300/cute,puppy,kitten", caption="Voici ton cadeau, Anaïs ! Tu es une championne ! 🌟")
    if st.button("Super ! Je continue"):
        st.session_state.palier_atteint = False
        st.rerun()

# FIN DU QUIZZ
if st.session_state.nb_questions >= total_q:
    st.balloons()
    st.info(f"🎯 Quiz terminé ! Tu as gagné {st.session_state.xp} XP aujourd'hui. Tu peux être fière de toi !")
