import streamlit as st
from google import genai
from PIL import Image
from datetime import datetime
import io

# --- 1. CONFIGURATION DE L'IA ---
# Sur Streamlit Cloud, on utilise les Secrets pour la sécurité
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "VOTRE_CLE_ICI_POUR_TEST_LOCAL"

# --- Modifier l'initialisation du client ---
client = genai.Client(
    api_key=API_KEY,
    http_options={'api_version': 'v1'} # On force la version stable v1 au lieu de v1beta
)

MODEL_ID = "gemini-3-flash-preview" # Ce modèle est le plus stable pour les comptes gratuits

# --- 2. INITIALISATION ---
if 'xp' not in st.session_state:
    st.session_state.xp = 0
if 'badges' not in st.session_state:
    st.session_state.badges = []
if 'historique' not in st.session_state:
    st.session_state.historique = []
if 'dernier_quiz' not in st.session_state:
    st.session_state.dernier_quiz = None

def ajouter_xp(montant):
    st.session_state.xp += montant
    if st.session_state.xp >= 100 and "🚀 Apprenti" not in st.session_state.badges:
        st.session_state.badges.append("🚀 Apprenti")
    if st.session_state.xp >= 300 and "👑 Champion" not in st.session_state.badges:
        st.session_state.badges.append("👑 Champion")

# --- 3. INTERFACE ---
st.set_page_config(page_title="Le Coach d'Anaïs", page_icon="🎓")

# CSS pour améliorer l'affichage sur petit écran
st.markdown("""<style> .stButton>button { width: 100%; border-radius: 20px; } </style>""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🏆 Score :")
    st.metric(label="Total XP", value=f"{st.session_state.xp} pts")
    st.subheader("🏅 Badges")
    for b in st.session_state.badges:
        st.success(b)
    
    st.divider()
    niveau = st.selectbox("Niveau", ["Primaire", "Collège", "Lycée"])
    mode_tdah = st.checkbox("Aide Focus (TDAH)", value=True)

st.title("🌟 Mon Coach Magique")

# Utilisation de l'appareil photo optimisée pour mobile
uploaded_files = st.file_uploader("Prends en photo ta leçon :", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    # On compresse les images pour éviter de saturer la mémoire du téléphone
    processed_images = []
    for f in uploaded_files:
        img = Image.open(f)
        img.thumbnail((1024, 1024)) # Redimensionne sans déformer
        processed_images.append(img)
    
    st.image(processed_images, width=150)
    chapitre_nom = st.text_input("Nom du chapitre :", "Ma leçon")

    if st.button("Lancer le défi ! ✨"):
        with st.spinner("L'IA analyse tes photos..."):
            prompt = f"Tu es un coach pour un enfant ({niveau}). Crée 3 questions courtes et ludiques sur ces photos. {'Utilise des emojis et phrases courtes.' if mode_tdah else ''} Donne les solutions à la fin."
            
            try:
                response = client.models.generate_content(model=MODEL_ID, contents=[prompt] + processed_images)
                st.session_state.dernier_quiz = response.text
                ajouter_xp(20)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

if st.session_state.dernier_quiz:
    st.markdown("---")
    st.markdown(st.session_state.dernier_quiz)
    
    if st.button("J'ai terminé ! 🏁"):
        st.session_state.historique.append({"titre": chapitre_nom, "date": datetime.now().strftime("%d/%m")})
        ajouter_xp(50)
        st.session_state.dernier_quiz = None
        st.balloons()
        st.rerun()



