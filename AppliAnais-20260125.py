import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# Configuration pour mobile
st.set_page_config(page_title="Le Coach Magique 🌟", layout="centered")

# Design personnalisé pour Anaïs (TDAH-friendly)
st.markdown("""
    <style>
    /* Gros boutons colorés pour les réponses */
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; font-weight: bold; border: none; }
    
    /* Couleurs spécifiques pour les choix QCM */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50; color: white; } /* Vert */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3; color: white; } /* Bleu */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0; color: white; } /* Violet */
    
    /* Style des bulles de chat */
    .stChatMessage { border-radius: 15px; font-size: 1.1rem; border: 1px solid #E0E0E0; }
    
    /* Bouton lancer et terminer */
    button[kind="secondary"] { background-color: #FFC107; color: black; }
    </style>
""", unsafe_allow_html=True)

# Connexion à l'API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "stock_photos" not in st.session_state: st.session_state.stock_photos = []
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    prenom = st.text_input("Prénom de l'élève :", value="Anaïs")
    if st.button("🔄 Réinitialiser la séance"):
        st.session_state.xp = 0
        st.session_state.messages = []
        st.session_state.stock_photos = []
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title(f"🌟 Le Coach de {prenom}")
st.subheader(f"⭐ Score actuel : {st.session_state.xp} XP")

# Zone de capture
st.write("---")
fichiers = st.file_uploader("📸 Dépose ou prends tes leçons en photo :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if fichiers:
    photos_traitees = []
    for f in fichiers:
        img = Image.open(f).convert("RGB")
        img.thumbnail((1024, 1024))
        photos_traitees.append(img)
    st.session_state.stock_photos = photos_traitees
    st.success(f"✅ {len(st.session_state.stock_photos)} page(s) enregistrée(s) !")

# Boutons d'action
col_action1, col_action2 = st.columns(2)
with col_action1:
    btn_lancer = st.button(f"🚀 LANCER LE DÉFI")
with col_action2:
    btn_fin = st.button("🏁 VOIR MON RÉSUMÉ")

# --- LOGIQUE DE
