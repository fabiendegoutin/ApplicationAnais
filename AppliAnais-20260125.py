import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# Style pour fixer les éléments importants en haut
st.markdown("""
    <style>
    .fixed-xp { position: fixed; top: 10px; right: 10px; background: #FF69B4; color: white; padding: 10px 20px; border-radius: 20px; z-index: 1000; font-weight: bold; border: 2px solid white; }
    div[data-testid="stHorizontalBlock"] button { height: 3.5em !important; border-radius: 15px !important; font-size: 1.1em !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API avec le nom de modèle STABLE
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash') # <--- CORRECTION ICI

if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0

st.markdown(f'<div class="fixed-xp">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- ÉTAPE 1 : CHARGEMENT ---
if not st.session_state.cours_texte:
    # On remet la caméra ET l'import de fichier
    photo = st.camera_input("📸 Prends ton cours")
    if not photo:
        photo = st.file_uploader("📂 Ou choisis une photo", type=['jpg', 'png'])

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Lecture du cours..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((500, 500))
                # Appel API corrigé
                res = model.generate_content(["Extrais le texte de ce cours.", img])
                st.session_state.cours_texte = res.text
                st.rerun()
        except Exception as e:
            st.error(f"Oups ! Google ne répond pas. Réessaie dans 10s. (Erreur: {e})")

# --- ÉTAPE 2 : LE QUIZZ (Ordre inversé pour le confort) ---
elif st.session_state.nb_q < 10:
    # Génération de la question si besoin
    if not st.session_state.messages:
        with st.spinner("Préparation de la question..."):
            q = model.generate_content(f"Cours : {st.session_state.cours_texte}. Pose une question QCM (A, B, C) simple.")
            st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
            st.rerun()

    st.write(f"Question {st.session_state.nb_q} / 10")
    st.progress(st.session_state.nb_q / 10)

    # Boutons de réponse en haut
    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        st.session_state.nb_q += 1
        try:
            with st.spinner("Vérification..."):
                prompt = f"Cours : {st.session_state.cours_texte}. Réponse : {rep}. Dis BRAVO si juste, sinon explique. Puis nouvelle question."
                res = model.generate_content(prompt)
                if "BRAVO" in res.text.upper():
                    st.balloons()
                    st.session_state.xp += 20
                st.session_state.messages.insert(0, {"role": "user", "content": f"Choix {rep}"})
                st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
                st.rerun()
        except:
            st.warning("IA fatiguée... Attends 5 secondes.")

    st.write("---")
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and st.button("🔊", key=f"v_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)
