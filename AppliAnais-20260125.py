import streamlit as st
import google.generativeai as genai  # Utilisation de la version STABLE
from PIL import Image
from datetime import datetime

# --- 1. CONFIGURATION ---
# Récupération de la clé depuis les "Secrets" de Streamlit Cloud
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "VOTRE_CLE_API"

# Initialisation SANS v1beta ou v1
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. INITIALISATION MÉMOIRE ---
if 'xp' not in st.session_state:
    st.session_state.xp = 0
if 'dernier_quiz' not in st.session_state:
    st.session_state.dernier_quiz = None

# --- 3. INTERFACE ---
st.set_page_config(page_title="Coach Anaïs", page_icon="🎓")

st.title("🌟 Le Coach Magique d'Anaïs")
st.write(f"### Score : {st.session_state.xp} XP")

uploaded_files = st.file_uploader("Prends tes leçons en photo :", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    processed_images = []
    for f in uploaded_files:
        img = Image.open(f)
        img.thumbnail((800, 800)) # Réduction pour éviter les erreurs de quota
        processed_images.append(img)
    
    st.image(processed_images, width=150)

    if st.button("Lancer le défi ! ✨"):
        with st.spinner("L'IA prépare tes questions..."):
            prompt = "Tu es un coach scolaire. Crée un quiz de 3 questions courtes à partir de ces photos. Donne les solutions à la fin."
            try:
                # Syntaxe de la bibliothèque stable
                response = model.generate_content([prompt] + processed_images)
                st.session_state.dernier_quiz = response.text
                st.rerun()
            except Exception as e:
                st.error(f"Erreur technique : {e}")

if st.session_state.dernier_quiz:
    st.markdown("---")
    st.markdown(st.session_state.dernier_quiz)
    if st.button("J'ai fini ! 🏁"):
        st.session_state.xp += 50
        st.session_state.dernier_quiz = None
        st.balloons()
        st.rerun()
