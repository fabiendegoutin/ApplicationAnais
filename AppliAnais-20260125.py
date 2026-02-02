import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# CSS : Interface optimisée
st.markdown("""
    <style>
    .fixed-header {
        position: fixed; top: 50px; right: 15px; width: 150px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 10px; border-radius: 20px;
        font-weight: bold; z-index: 9999; text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); border: 2px solid white;
    }
    .stProgress > div > div > div > div { background-color: #FF69B4; }
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 15px !important; height: 3.5em !important; 
        font-size: 1.1em !important;
    }
    /* Couleurs boutons */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name='models/gemini-2.0-flash',
    system_instruction="Tu es le coach d'Anaïs (6ème). Propose TOUJOURS 3 choix : A, B et C. Saute une ligne entre chaque choix."
)

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0
if "bravo" not in st.session_state: st.session_state.bravo = False

# RÉGLAGES DANS LA SIDEBAR
with st.sidebar:
    total_q = st.slider("Objectif questions", 1, 20, 10)
    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

# HEADER FIXE (Score + Barre)
st.markdown(f'<div class="fixed-header">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)

st.title("✨ Le Coach d'Anaïs")

# --- 1. CHARGEMENT ---
if not st.session_state.cours_texte:
    img_cam = st.camera_input("📸 Photo du cours")
    img_file = st.file_uploader("📂 Ou bibliothèque", type=['jpg', 'png'])
    photo = img_cam if img_cam else img_file

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        with st.spinner("Lecture..."):
            img = Image.open(photo).convert("RGB")
            res = model.generate_content(["Extrais le texte.", img])
            st.session_state.cours_texte = res.text
            q = model.generate_content(f"Cours: {st.session_state.cours_texte}. Pose une question QCM (A, B, C).")
            # On insère au début de la liste pour l'affichage inversé
            st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
            st.rerun()

# --- 2. LE QUIZZ ---
elif st.session_state.nb_q < total_q:
    # Barre de progression toujours visible sous le titre
    st.write(f"Question {st.session_state.nb_q} / {total_q}")
    st.progress(st.session_state.nb_q / total_q)

    # Zone de réponse TOUJOURS en haut pour éviter le scroll
    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A", use_container_width=True): choix = "A"
    if c2.button("B", use_container_width=True): choix = "B"
    if c3.button("C", use_container_width=True): choix = "C"

    if choix:
        st.session_state.nb_q += 1
        with st.spinner("Vérification..."):
            prompt = f"Cours: {st.session_state.cours_texte}. Question: {st.session_state.messages[0]['content']}. Réponse: {choix}. Dis BRAVO si juste. Pose la question QCM suivante."
            res = model.generate_content(prompt)
            
            if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                st.session_state.xp += 20
                st.session_state.bravo = True # On marque pour afficher les ballons après rerun
            
            st.session_state.messages.insert(0, {"role": "user", "content": f"Ma réponse : {choix}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    # Affichage des ballons si besoin
    if st.session_state.bravo:
        st.balloons()
        st.session_state.bravo = False

    st.write("---")
    # Affichage du chat (le plus récent est déjà en haut grâce au .insert(0, ...))
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"s_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

if st.session_state.nb_q >= total_q:
    st.success(f"🏆 Bravo Anaïs ! {st.session_state.xp} XP gagnés !")
