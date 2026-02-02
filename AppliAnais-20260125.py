import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# --- CONFIGURATION STYLE MODERNE ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    .fixed-score {
        position: fixed; top: 70px; right: 20px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 10px 22px; border-radius: 50px;
        font-weight: 800; z-index: 9999;
        box-shadow: 0 4px 15px rgba(255, 105, 180, 0.4);
        border: 2px solid white;
    }
    /* Boutons de réponse modernes */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 20px !important;
        height: 5em !important;
        font-size: 1.5em !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Connexion API avec instructions de cadrage strictes
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name='models/gemini-2.0-flash',
    system_instruction="""Tu es le coach d'Anaïs (6ème). 
    Tu dois TOUJOURS poser des questions en format QCM avec 3 options : A, B et C.
    Ne pose jamais de question ouverte. Reste joyeux et encourageant ✨."""
)

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0

# Sidebar pour les réglages
with st.sidebar:
    st.header("⚙️ Paramètres")
    total_q = st.slider("Nombre de questions", 1, 20, 10)
    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

st.markdown(f'<div class="fixed-score">⚡ {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- CHARGEMENT ---
if not st.session_state.cours_texte:
    photo = st.camera_input("📸 Prends ton cours en photo")
    if photo and st.button("🚀 GÉNÉRER LE QUIZZ"):
        with st.spinner("Lecture magique..."):
            img = Image.open(photo).convert("RGB")
            res = model.generate_content(["Extrais le texte de ce cours.", img])
            st.session_state.cours_texte = res.text
            # Première question
            q = model.generate_content(f"Cours: {st.session_state.cours_texte}. Pose une question QCM (A, B, C).")
            st.session_state.messages.append({"role": "assistant", "content": q.text})
            st.rerun()

# --- AFFICHAGE DU QUIZZ ---
if st.session_state.cours_texte and st.session_state.nb_q < total_q:
    # Barre de progression
    progress = st.session_state.nb_q / total_q
    st.progress(progress, text=f"Progression : {st.session_state.nb_q}/{total_q}")

    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and st.button("🔊 Écouter", key=f"snd_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

    # Boutons de réponse (Uniquement pour le dernier message de l'IA)
    if st.session_state.messages[-1]["role"] == "assistant":
        st.write("---")
        c1, c2, c3 = st.columns(3)
        choix = None
        if c1.button("🅰️", use_container_width=True): choix = "A"
        if c2.button("🅱️", use_container_width=True): choix = "B"
        if c3.button("🅲", use_container_width=True): choix = "C"

        if choix:
            st.session_state.nb_q += 1
            with st.spinner("Vérification..."):
                prompt = f"Cours: {st.session_state.cours_texte}. Anaïs a choisi {choix}. Juste ou Faux ? Si juste, dis BRAVO. Pose la question QCM suivante."
                res = model.generate_content(prompt)
                
                if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                    st.balloons()
                    st.session_state.xp += 20
                
                st.session_state.messages.append({"role": "user", "content": f"Je choisis la {choix}"})
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                
                if st.session_state.xp >= 200:
                    st.snow() # Récompense visuelle
                
                st.rerun()

if st.session_state.nb_q >= total_q:
    st.success(f"🏆 Bravo Anaïs ! Tu as terminé tes {total_q} questions et gagné {st.session_state.xp} XP !")
