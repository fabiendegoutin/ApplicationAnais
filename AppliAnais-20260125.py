import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach Magique d'Anaïs 🌟", layout="centered")

# CSS pour le score Rose à droite et l'interface
st.markdown(f"""
    <style>
    .fixed-score {{
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #FF69B4;
        padding: 12px 20px;
        border-radius: 30px;
        font-weight: bold;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        z-index: 1000;
        color: white;
    }}
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {{ background-color: #4CAF50 !important; color: white !important; }}
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {{ background-color: #2196F3 !important; color: white !important; }}
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {{ background-color: #9C27B0 !important; color: white !important; }}
    .stButton>button {{ border-radius: 20px; font-weight: bold; height: 3em; width: 100%; }}
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- INITIALISATION ---
for key in ["xp", "messages", "cours_texte", "attente_reponse", "file_uploader_key"]:
    if key not in st.session_state:
        st.session_state.xp = 0
        st.session_state.messages = []
        st.session_state.cours_texte = None
        st.session_state.attente_reponse = False
        st.session_state.file_uploader_key = 0

# Score fixe visible
st.markdown(f'<div class="fixed-score">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Réglages")
    if st.button("➕ Nouvelle Leçon / Reset"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

st.title("✨ Le Coach d'Anaïs")

# Uploader avec clé pour reset les photos
fichiers = st.file_uploader("📸 Tes photos :", type=['jpg', 'png'], accept_multiple_files=True, key=f"up_{st.session_state.file_uploader_key}")

if st.button("🚀 LANCER LE QUIZZ"):
    if fichiers or st.session_state.cours_texte:
        with st.spinner("Je lis ton cours, Anaïs..."):
            if not st.session_state.cours_texte:
                # OPTIMISATION TOKENS : Redimensionnement et conversion texte unique
                imgs = [Image.open(f).convert("RGB") for f in fichiers]
                for img in imgs: img.thumbnail((1000, 1000))
                res = model.generate_content(["Extrais tout le texte de ces images.", *imgs])
                st.session_state.cours_texte = res.text
            
            prompt = f"Tu es le coach d'Anaïs (une fille). Savoir : {st.session_state.cours_texte}. Pose un QCM court (A, B, C) avec 2 lignes vides entre les choix. Ton joyeux, pas de 'selon le texte' !"
            q = model.generate_content(prompt)
            st.session_state.messages = [{"role": "assistant", "content": q.text}]
            st.session_state.attente_reponse = True
            st.rerun()

# --- AFFICHAGE MESSAGES ---
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"], avatar="🌈" if m["role"]=="assistant" else "⭐"):
        st.markdown(m["content"])
        if m["role"] == "assistant" and st.button("🔊", key=f"v_{i}"):
            tts = gTTS(text=m["content"].replace("A)", "Choix A,"), lang='fr')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format="audio/mp3", autoplay=True)

# --- ZONE RÉPONSE & SCROLL ---
if st.session_state.attente_reponse:
    st.write("---")
    c1, c2, c3 = st.columns(3)
    res_bouton = None
    if c1.button("A"): res_bouton = "A"
    if c2.button("B"): res_bouton = "B"
    if c3.button("C"): res_bouton = "C"

    if res_bouton:
        st.session_state.messages.append({"role": "user", "content": f"Choix {res_bouton}"})
        with st.spinner("Vérification..."):
            check_prompt = f"Savoir: {st.session_state.cours_texte}. La réponse {res_bouton} à la question '{st.session_state.messages[-2]['content']}' est-elle juste ? Réponds par OUI ou NON d'abord, puis explique courtement et pose une nouvelle question."
            v = model.generate_content(check_prompt)
            
            # Gestion des ballons immédiate
            if "OUI" in v.text.upper()[:10]:
                st.session_state.xp += 20
                st.balloons() # Déclenchement forcé
            
            st.session_state.messages.append({"role": "assistant", "content": v.text})
            # FORCER LE SCROLL EN BAS : On utilise un conteneur vide pour attirer le focus
            st.markdown('<div id="fin"></div>', unsafe_allow_html=True)
            st.rerun()
