import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# CSS : Barre fixe et boutons
st.markdown("""
    <style>
    .fixed-header {
        position: fixed; top: 50px; right: 15px; width: 150px;
        background: #FF69B4; color: white; padding: 10px; border-radius: 20px;
        font-weight: bold; z-index: 9999; text-align: center; border: 2px solid white;
    }
    .stProgress > div > div > div > div { background-color: #FF69B4; }
    div[data-testid="stHorizontalBlock"] button { border-radius: 15px !important; height: 3.5em !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API - Modèle 1.5 Flash (le plus stable pour les photos)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0
if "bravo" not in st.session_state: st.session_state.bravo = False

# Score fixe
st.markdown(f'<div class="fixed-header">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)

st.title("✨ Le Coach d'Anaïs")

# --- 1. LECTURE DU COURS ---
if not st.session_state.cours_texte:
    # Caméra ou Fichier selon l'appareil utilisé
    source = st.camera_input("📸 Prends ton cours")
    if not source:
        source = st.file_uploader("📂 Ou choisis ta photo", type=['jpg', 'png'])

    if source and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Lecture du cours en cours..."):
                img = Image.open(source).convert("RGB")
                img.thumbnail((600, 600)) # Réduction pour éviter le crash API
                
                # On demande le texte et la 1ère question d'un coup
                res = model.generate_content([
                    "Tu es le coach d'Anaïs. Extrais le texte de ce cours de 6ème. "
                    "Puis pose une première question QCM (A, B, C) avec des sauts de ligne.", 
                    img
                ])
                st.session_state.cours_texte = res.text
                st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
                st.rerun()
        except Exception:
            st.error("Délai dépassé. Attends 5 secondes et réessaie, l'image est un peu lourde ! 😊")

# --- 2. LE QUIZZ (Ordre Inversé : Nouveau en haut) ---
elif st.session_state.nb_q < 10:
    # Barre de progression fixe sous le titre
    st.write(f"Question {st.session_state.nb_q} / 10")
    st.progress(st.session_state.nb_q / 10)

    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        st.session_state.nb_q += 1
        with st.spinner("Vérification..."):
            prompt = f"Cours: {st.session_state.cours_texte}. Réponse d'Anaïs: {rep}. Dis si c'est juste. Puis pose la question suivante."
            res = model.generate_content(prompt)
            if "BRAVO" in res.text.upper() or "JUSTE" in res.text.upper():
                st.session_state.xp += 20
                st.session_state.bravo = True
            
            st.session_state.messages.insert(0, {"role": "user", "content": f"Choix {rep}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    if st.session_state.bravo:
        st.balloons()
        st.session_state.bravo = False

    st.write("---")
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"audio_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

if st.session_state.nb_q >= 10:
    st.success(f"🏆 Séance terminée ! Bravo Anaïs pour tes {st.session_state.xp} XP !")
