import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# --- 1. CONFIGURATION DE L'IA (Version Stable) ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "VOTRE_CLE_API_POUR_TEST_LOCAL"

# Initialisation avec la bibliothèque stable
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. INITIALISATION DE LA MÉMOIRE ---
if 'xp' not in st.session_state:
    st.session_state.xp = 0
if 'badges' not in st.session_state:
    st.session_state.badges = []
if 'dernier_quiz' not in st.session_state:
    st.session_state.dernier_quiz = None

def ajouter_xp(montant):
    st.session_state.xp += montant
    if st.session_state.xp >= 100 and "🚀 Apprenti" not in st.session_state.badges:
        st.session_state.badges.append("🚀 Apprenti")

# --- 3. INTERFACE ---
st.set_page_config(page_title="Le Coach d'Anaïs", page_icon="🎓")

with st.sidebar:
    st.title("🏆 Score :")
    st.metric(label="Total XP", value=f"{st.session_state.xp} pts")
    for b in st.session_state.badges:
        st.success(b)
    niveau = st.selectbox("Niveau", ["Primaire", "Collège", "Lycée"])
    mode_tdah = st.checkbox("Aide Focus (TDAH)", value=True)

st.title("🌟 Mon Coach Magique")

uploaded_files = st.file_uploader("Prends en photo ta leçon :", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    processed_images = []
    for f in uploaded_files:
        img = Image.open(f)
        img.thumbnail((800, 800)) # Taille optimisée pour éviter les erreurs
        processed_images.append(img)
    
    st.image(processed_images, width=150)
    chapitre_nom = st.text_input("Nom du chapitre :", "Ma leçon")

    if st.button("Lancer le défi ! ✨"):
        with st.spinner("L'IA analyse tes photos..."):
            prompt = f"Tu es un coach scolaire pour un enfant ({niveau}). Crée 3 questions courtes et ludiques sur ces photos. {'Utilise des emojis.' if mode_tdah else ''} Donne les solutions à la fin."
            
            try:
                # Syntaxe robuste : on envoie une liste avec le prompt et les images
                contenu = [prompt] + processed_images
                response = model.generate_content(contenu)
                st.session_state.dernier_quiz = response.text
                ajouter_xp(20)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

if st.session_state.dernier_quiz:
    st.markdown("---")
    st.markdown(st.session_state.dernier_quiz)
    
    if st.button("J'ai terminé ! 🏁"):
        ajouter_xp(50)
        st.session_state.dernier_quiz = None
        st.balloons()
        st.rerun()
