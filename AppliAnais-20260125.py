import streamlit as st
import google.generativeai as genai
from PIL import Image
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# SOLUTION : Utiliser le nom court sans préfixe
# Si 'gemini-1.5-flash' échoue, on essaiera 'gemini-pro'
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    model = genai.GenerativeModel('gemini-pro')

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
            with st.spinner("Analyse du cours..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((500, 500))
                # Appel API sans fioritures
                res = model.generate_content(["Extrais le texte de ce cours.", img])
                if res.text:
                    st.session_state.cours_texte = res.text
                    st.rerun()
        except Exception as e:
            # Si ça échoue encore, on affiche la liste des modèles pour comprendre
            st.error(f"Erreur : {e}")
            if "404" in str(e):
                st.write("Modèles disponibles sur ton compte :")
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                st.code(models)

# --- 2. LE QUIZZ ---
elif len(st.session_state.messages) < 10:
    if not st.session_state.messages:
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
            prompt = f"Cours : {st.session_state.cours_texte}. Réponse : {rep}. Dis si c'est juste, puis nouvelle question."
            res = model.generate_content(prompt)
            if "BRAVO" in res.text.upper() or "JUSTE" in res.text.upper():
                st.session_state.xp += 20
                st.balloons()
            st.session_state.messages.insert(0, {"role": "user", "content": f"Choix {rep}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()
        except:
            st.warning("Patiente 5 secondes...")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
