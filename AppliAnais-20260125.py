import streamlit as st
import google.generativeai as genai
from PIL import Image
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# LE MODÈLE DÉTECTÉ SUR VOTRE COMPTE :
MODEL_NAME = 'models/gemini-2.5-flash'
model = genai.GenerativeModel(MODEL_NAME)

if "xp" not in st.session_state: st.session_state.xp = 0
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "messages" not in st.session_state: st.session_state.messages = []

st.sidebar.metric("XP 🚀", st.session_state.xp)
st.title("✨ Le Coach d'Anaïs")

# --- 1. LECTURE DU COURS ---
if not st.session_state.cours_texte:
    photo = st.camera_input("📸 Prends ton cours")
    if not photo:
        photo = st.file_uploader("📂 Ou choisis une photo", type=['jpg', 'png'])

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Analyse avec Gemini 2.5..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((600, 600))
                
                # Appel API avec le nouveau modèle
                res = model.generate_content(["Extrais le texte de ce cours de 6ème.", img])
                if res.text:
                    st.session_state.cours_texte = res.text
                    st.success("Cours chargé avec succès !")
                    st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- 2. LE QUIZZ ---
elif len(st.session_state.messages) < 10:
    if not st.session_state.messages:
        with st.spinner("Génération de la question..."):
            q = model.generate_content(f"Cours : {st.session_state.cours_texte}. Pose un QCM (A, B, C).")
            st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
            st.rerun()

    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        try:
            with st.spinner("Vérification..."):
                prompt = f"Cours : {st.session_state.cours_texte}. Réponse : {rep}. Dis si c'est juste, puis nouvelle question."
                res = model.generate_content(prompt)
                if "BRAVO" in res.text.upper() or "JUSTE" in res.text.upper():
                    st.session_state.xp += 20
                    st.balloons()
                st.session_state.messages.insert(0, {"role": "user", "content": f"Choix {rep}"})
                st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
                st.rerun()
        except Exception as e:
            st.warning("IA très sollicitée, attends 3 secondes...")
            time.sleep(3)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
