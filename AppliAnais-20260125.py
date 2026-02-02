import streamlit as st
import google.generativeai as genai
from PIL import Image
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- SYSTÈME DE SECOURS AUTOMATIQUE ---
@st.cache_resource
def get_working_model():
    # Liste de noms à tester par ordre de stabilité
    model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    for name in model_names:
        try:
            m = genai.GenerativeModel(name)
            # Test léger pour voir si le modèle répond
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return genai.GenerativeModel('gemini-1.5-flash') # Repli par défaut

model = get_working_model()

# --- INITIALISATION ---
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
                # Appel API
                res = model.generate_content(["Extrais le texte de ce cours.", img])
                if res.text:
                    st.session_state.cours_texte = res.text
                    st.rerun()
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")
            st.info("Vérifie que ta clé API est correcte dans les secrets Streamlit.")

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
            st.warning("IA occupée, réessaie dans 5 secondes.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
