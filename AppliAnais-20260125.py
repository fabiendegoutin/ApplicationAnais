import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION VISUELLE ---
st.set_page_config(page_title="Le Coach Magique d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    /* Boutons de réponse colorés */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; border: none; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; border: none; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; border: none; }
    
    /* Style général */
    .stButton>button { border-radius: 20px; font-weight: bold; }
    .stChatMessage { border-radius: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# Connexion API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False

def preparer_image(image_upload):
    img = Image.open(image_upload).convert("RGB")
    img.thumbnail((1024, 1024))
    return img

# --- INTERFACE ---
st.title(f"✨ Le Coach d'Anaïs")
st.write(f"🚀 **{st.session_state.xp} XP** — Tu es une championne !")

fichiers = st.file_uploader("📸 Dépose tes photos de cours :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# --- LOGIQUE DU BOUTON MAGIQUE ---
if st.button("🚀 LANCER UNE QUESTION"):
    if not fichiers and not st.session_state.cours_texte:
        st.warning("Ajoute une photo d'abord ! 📸")
    else:
        try:
            with st.spinner("Lecture du cours..."):
                if st.session_state.cours_texte is None:
                    images_preparees = [preparer_image(f) for f in fichiers]
                    prompt_extract = "Extrais tout le texte de ce cours de 6ème. Ne réponds que le texte brut."
                    res_extract = model.generate_content([prompt_extract] + images_preparees)
                    st.session_state.cours_texte = res_extract.text
                
                st.session_state.messages = []
                # PROMPT AMÉLIORÉ
                prompt_q = f"""Cours : {st.session_state.cours_texte}
                CONSIGNES STRICTES :
                - Pose une question QCM sur ce cours.
                - Format : Une option par ligne (A, B, C).
                - NE DIS RIEN AVANT LA QUESTION (Pas de 'Voici une question').
                - Termine par un petit mot d'encouragement pour Anaïs."""
                
                res_q = model.generate_content(prompt_q)
                st.session_state.messages.append({"role": "assistant", "content": res_q.text})
                st.session_state.attente_reponse = True
                st.rerun()
        except Exception as e:
            st.error(f"L'IA fait une pause, réessaie dans 20 secondes ! ({e})")

# --- CHAT ---
for i, msg in enumerate(st.session_state.messages):
    # Changement des icônes pour plus de peps
    icon = "🌈" if msg["role"] == "assistant" else "⭐"
    with st.chat_message(msg["role"], avatar=icon):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

# --- RÉPONSES ---
if st.session_state.attente_reponse:
    st.write("---")
    st.write("### Ta réponse :")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("🅰️ OPTION A"): choix = "A"
    if c2.button("🅱️ OPTION B"): choix = "B"
    if c3.button("🅲 OPTION C"): choix = "C"

    if choix:
        try:
            st.session_state.messages.append({"role": "user", "content": f"Je choisis la {choix}"})
            st.session_state.attente_reponse = False
            with st.spinner("Vérification..."):
                prompt_v = f"""Le cours : {st.session_state.cours_texte}
                Question : {st.session_state.messages[-2]['content']}
                Réponse choisie : {choix}
                DIRECTIVES :
                - Vérifie si c'est la bonne réponse par rapport au cours.
                - Si faux, explique pourquoi sans être sévère.
                - Pose ensuite une NOUVELLE question QCM (A, B, C) avec une option par ligne.
                - JAMAIS de phrases d'introduction type 'Voici la réponse'."""
                
                res_coach = model.generate_content(prompt_v)
                txt = res_coach.text
                
                if any(w in txt.lower() for w in ["bravo", "juste", "correct", "excellent"]):
                    st.session_state.xp += 20
                    st.balloons()
                
                st.session_state.messages.append({"role": "assistant", "content": txt})
                st.session_state.attente_reponse = True
                st.rerun()
        except:
            st.error("Petit souci de connexion, réessaie !")
