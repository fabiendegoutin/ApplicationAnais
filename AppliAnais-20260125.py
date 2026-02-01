import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach Magique d'Anaïs 🌟", layout="centered")

# Design
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; font-weight: bold; }
    .stChatMessage { border-radius: 15px; border: 1px solid #E0E0E0; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- FONCTION DE COMPRESSION (Économise les tokens) ---
def preparer_image(image_upload):
    img = Image.open(image_upload).convert("RGB")
    # On réduit la taille pour que ce soit moins lourd (max 1024px)
    img.thumbnail((1024, 1024))
    return img

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False

# --- INTERFACE ---
st.title(f"🌟 Le Coach Magique")
st.write(f"⭐ **{st.session_state.xp} XP**")

fichiers = st.file_uploader("📸 Dépose tes photos :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if st.button("🚀 LANCER UNE QUESTION"):
    if not fichiers and not st.session_state.cours_texte:
        st.warning("Ajoute une photo d'abord ! 📸")
    else:
        try:
            with st.spinner("Analyse du cours (cela peut prendre 10s)..."):
                if st.session_state.cours_texte is None:
                    # On compresse chaque image avant l'envoi
                    images_preparees = [preparer_image(f) for f in fichiers]
                    prompt_extract = "Extrais tout le texte de ce cours. Sois précis."
                    res_extract = model.generate_content([prompt_extract] + images_preparees)
                    st.session_state.cours_texte = res_extract.text
                
                # Question
                st.session_state.messages = []
                prompt_q = f"Cours : {st.session_state.cours_texte}. Pose une question QCM courte (A, B, C) à Anaïs (TDAH). Encourage-la."
                res_q = model.generate_content(prompt_q)
                st.session_state.messages.append({"role": "assistant", "content": res_q.text})
                st.session_state.attente_reponse = True
                st.rerun()
                
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
                st.error("⚠️ Trop de demandes d'un coup ! Attends 30 secondes, l'IA reprend son souffle.")
            else:
                st.error(f"Erreur : {e}")

# --- AFFICHAGE ET RÉPONSES ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.attente_reponse:
    cA, cB, cC = st.columns(3)
    choix = None
    if cA.button("🅰️ A"): choix = "A"
    if cB.button("🅱️ B"): choix = "B"
    if cC.button("🅲 C"): choix = "C"

    if choix:
        try:
            st.session_state.messages.append({"role": "user", "content": f"Choix {choix}"})
            st.session_state.attente_reponse = False
            with st.spinner("Vérification..."):
                prompt_v = f"Cours: {st.session_state.cours_texte}. Elle a choisi {choix}. Valide et donne une nouvelle question QCM."
                res_coach = model.generate_content(prompt_v)
                st.session_state.messages.append({"role": "assistant", "content": res_coach.text})
                st.session_state.attente_reponse = True
                st.rerun()
        except Exception as e:
            st.error("L'IA est fatiguée, réessaie dans un instant.")
