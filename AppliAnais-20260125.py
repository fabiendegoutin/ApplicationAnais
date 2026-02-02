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
    .fixed-score {
        position: fixed; top: 70px; right: 20px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 10px 22px; border-radius: 50px;
        font-weight: 800; z-index: 9999;
        box-shadow: 0 4px 15px rgba(255, 105, 180, 0.4);
        border: 2px solid white;
    }
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 20px !important;
        height: 5em !important;
        font-size: 1.5em !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    /* Couleurs pour les boutons A, B, C */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name='models/gemini-2.0-flash',
    system_instruction="""Tu es le coach d'Anaïs (6ème). 
    Tu dois TOUJOURS poser des questions en format QCM avec 3 options : A, B et C.
    Ne pose JAMAIS de question ouverte. Sois joyeux et encourageant ✨."""
)

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0
if "recompense_prete" not in st.session_state: st.session_state.recompense_prete = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Réglages")
    total_q = st.slider("Nombre de questions", 1, 20, 10)
    if st.button("🔄 Nouveau cours / Reset"):
        st.session_state.clear()
        st.rerun()

st.markdown(f'<div class="fixed-score">⚡ {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- 1. CAPTURE DU COURS ---
if not st.session_state.cours_texte:
    st.write("### 📸 Étape 1 : Envoie ton cours")
    
    # Option Photo en direct
    img_cam = st.camera_input("Prends une photo")
    
    # Option Bibliothèque / Galerie
    img_file = st.file_uploader("Ou choisis une photo dans ta bibliothèque", type=['jpg', 'jpeg', 'png'])
    
    photo_active = img_cam if img_cam else img_file

    if photo_active and st.button("🚀 LANCER LE QUIZZ", use_container_width=True):
        try:
            with st.spinner("Je lis ton cours..."):
                img = Image.open(photo_active).convert("RGB")
                img.thumbnail((1024, 1024))
                res = model.generate_content(["Extrais le texte de ce cours pour une élève de 6ème.", img])
                st.session_state.cours_texte = res.text
                
                # Générer la 1ère question immédiatement
                q = model.generate_content(f"Cours: {st.session_state.cours_texte}. Pose une première question QCM (A, B, C) simple.")
                st.session_state.messages.append({"role": "assistant", "content": q.text})
                st.rerun()
        except exceptions.ResourceExhausted:
            st.error("Le coach se repose 30 secondes (limite API). 😊")

# --- 2. LE QUIZZ ---
elif st.session_state.nb_q < total_q:
    # Barre de progression visuelle
    progression = st.session_state.nb_q / total_q
    st.progress(progression, text=f"Question {st.session_state.nb_q}/{total_q}")

    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and st.button("🔊 Écouter", key=f"snd_{i}"):
                # Amélioration de la voix pour les choix
                clean = msg["content"].replace("A)", "Réponse A,").replace("B)", "Réponse B,").replace("C)", "Réponse C,")
                tts = gTTS(text=clean, lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

    # Boutons de réponse (uniquement après le dernier message de l'IA)
    if st.session_state.messages[-1]["role"] == "assistant":
        st.write("---")
        c1, c2, c3 = st.columns(3)
        choix = None
        if c1.button("🅰️", use_container_width=True): choix = "A"
        if c2.button("🅱️", use_container_width=True): choix = "B"
        if c3.button("🅲", use_container_width=True): choix = "C"

        if choix:
            st.session_state.nb_q += 1
            try:
                with st.spinner("Vérification..."):
                    prompt = f"Cours: {st.session_state.cours_texte}. Question: {st.session_state.messages[-1]['content']}. Anaïs a dit {choix}. Si juste dis BRAVO. Pose la question QCM suivante."
                    res = model.generate_content(prompt)
                    
                    if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                        st.balloons()
                        st.session_state.xp += 20
                        if st.session_state.xp % 200 == 0:
                            st.session_state.recompense_prete = True
                    
                    st.session_state.messages.append({"role": "user", "content": f"Je choisis la {choix}"})
                    st.session_state.messages.append({"role": "assistant", "content": res.text})
                    st.rerun()
            except exceptions.ResourceExhausted:
                st.error("Le coach a besoin d'une petite pause. Attends 20 secondes ! ☕")

# --- 3. RÉCOMPENSE & FIN ---
if st.session_state.recompense_prete:
    st.snow()
    st.success("### 🏆 GÉNIAL ! 200 XP ATTEINTS !")
    st.image(f"https://loremflickr.com/600/400/cute,animal?lock={st.session_state.xp}", caption="Ton cadeau magique ! ✨")
    if st.button("Merci ! Je continue 🚀"):
        st.session_state.recompense_prete = False
        st.rerun()

if st.session_state.nb_q >= total_q:
    st.balloons()
    st.info(f"🎯 Séance terminée ! Bravo Anaïs, tu as gagné {st.session_state.xp} XP !")
