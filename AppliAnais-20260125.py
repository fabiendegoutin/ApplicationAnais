import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# CSS : BARRE ET SCORE FIXES
st.markdown("""
    <style>
    .fixed-header {
        position: fixed; top: 50px; right: 15px; width: 160px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 12px; border-radius: 25px;
        font-weight: bold; z-index: 9999; text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3); border: 2px solid white;
    }
    /* Boutons plus fins et aérés */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 15px !important; height: 3.5em !important; 
        font-size: 1.1em !important; box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name='models/gemini-2.0-flash',
    system_instruction="Tu es le coach d'Anaïs. Tu crées des questions QCM basées UNIQUEMENT sur le cours fourni. Ne parle jamais de fautes d'orthographe ou de la structure des phrases."
)

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0
if "lancer_ballons" not in st.session_state: st.session_state.lancer_ballons = False

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Réglages")
    total_q = st.slider("Objectif questions", 1, 20, 10)
    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

# HEADER FIXE
st.markdown(f'<div class="fixed-header">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)

st.title("✨ Le Coach d'Anaïs")

# --- 1. LECTURE DU COURS ---
if not st.session_state.cours_texte:
    img_cam = st.camera_input("📸 Photo du cours")
    img_file = st.file_uploader("📂 Ou bibliothèque", type=['jpg', 'png'])
    photo = img_cam if img_cam else img_file

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        with st.spinner("Analyse du cours..."):
            img = Image.open(photo).convert("RGB")
            res = model.generate_content(["Extrais le texte de ce cours de 6ème.", img])
            st.session_state.cours_texte = res.text
            # Première question cadrée
            prompt = f"Basé sur ce cours : {st.session_state.cours_texte}. Pose une question QCM courte avec 3 choix A, B, C. Saute une ligne entre chaque choix."
            q = model.generate_content(prompt)
            st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
            st.rerun()

# --- 2. LE QUIZZ (AFFICHAGE INVERSÉ) ---
elif st.session_state.nb_q < total_q:
    # Barre de progression sous le titre
    st.write(f"**Progression : Question {st.session_state.nb_q} sur {total_q}**")
    st.progress(st.session_state.nb_q / total_q)

    # Zone de boutons (toujours visible en haut)
    st.write("### 🧩 Choisis ta réponse :")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A", use_container_width=True): choix = "A"
    if c2.button("B", use_container_width=True): choix = "B"
    if c3.button("C", use_container_width=True): choix = "C"

    if choix:
        st.session_state.nb_q += 1
        with st.spinner("Vérification..."):
            prompt_v = f"Cours : {st.session_state.cours_texte}. Question précédente : {st.session_state.messages[0]['content']}. Anaïs a répondu {choix}. Dis si c'est juste (BRAVO) ou faux. Puis pose la question QCM suivante (A, B, C) avec des sauts de ligne."
            res = model.generate_content(prompt_v)
            if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                st.session_state.xp += 20
                st.session_state.lancer_ballons = True
            st.session_state.messages.insert(0, {"role": "user", "content": f"Ma réponse : {choix}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    if st.session_state.lancer_ballons:
        st.balloons()
        st.session_state.lancer_ballons = False

    st.write("---")
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"v_{i}"):
                    txt = msg["content"].replace("A)", "Réponse A,").replace("B)", "Réponse B,").replace("C)", "Réponse C,")
                    tts = gTTS(text=txt, lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

if st.session_state.nb_q >= total_q:
    st.success(f"🏆 Séance finie ! Tu as gagné {st.session_state.xp} XP !")
