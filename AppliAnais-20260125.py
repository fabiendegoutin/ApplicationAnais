import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach Magique d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    /* Boutons de réponse colorés */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 3em; border: none; width: 100%; }
    /* Bouton flottant "+" en haut à gauche */
    .stDeployButton { display:none; }
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

# --- BARRE LATÉRALE (OPTIONS) ---
with st.sidebar:
    st.header("⚙️ Réglages")
    # Option d'arrêt des ballons
    activer_ballons = st.toggle("Activer les ballons 🎈", value=True)
    st.write("---")
    # Bouton "+" pour reprendre un autre QCM
    if st.button("➕ Ajouter une autre leçon"):
        st.session_state.cours_texte = None
        st.session_state.messages = []
        st.rerun()

# --- INTERFACE ---
st.title(f"✨ Le Coach d'Anaïs")
st.write(f"🚀 **Score : {st.session_state.xp} XP**")

# Le chargeur de fichiers reste visible pour ajouter des photos
fichiers = st.file_uploader("📸 Dépose tes photos ici :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# --- LANCEMENT DIRECT ---
if st.button("🚀 LANCER UNE QUESTION"):
    if not fichiers and st.session_state.cours_texte is None:
        st.warning("Ajoute une photo d'abord ! 📸")
    else:
        with st.spinner("Je prépare tes questions..."):
            # Si le texte n'est pas encore extrait, on le fait automatiquement ici
            if st.session_state.cours_texte is None:
                photos = [Image.open(f).convert("RGB") for f in fichiers]
                for p in photos: p.thumbnail((1024, 1024))
                res_ocr = model.generate_content(["Extrais tout le texte de ces images."] + photos)
                st.session_state.cours_texte = res_ocr.text
            
            # Génération de la question
            st.session_state.messages = []
            prompt = f"""Cours : {st.session_state.cours_texte}. 
            Pose une question QCM courte. Saute une ligne vide entre chaque option A, B et C."""
            res = model.generate_content(prompt)
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            st.session_state.attente_reponse = True
            st.rerun()

# --- CHAT ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "🌈" if msg["role"] == "assistant" else "⭐"
    with st.chat_message(msg["role"], avatar=avatar):
        c_txt, c_aud = st.columns([0.88, 0.12])
        with c_txt:
            st.markdown(msg["content"])
        with c_aud:
            if msg["role"] == "assistant":
                if st.button("🔊", key=f"audio_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

# --- ZONE RÉPONSE ---
if st.session_state.attente_reponse:
    st.write("---")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A"): choix = "A"
    if c2.button("B"): choix = "B"
    if c3.button("C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Je choisis la {choix}"})
        st.session_state.attente_reponse = False
        with st.spinner("Vérification..."):
            prompt_v = f"""Cours : {st.session_state.cours_texte}
            Question : {st.session_state.messages[-2]['content']}
            Réponse choisie : {choix}
            - Si juste : commence par 'BRAVO'.
            - Si faux : commence par 'ZUT'. Explique en 2 phrases MAX (sans dire 'le texte dit').
            - Pose ensuite une nouvelle question QCM. Saute une ligne entre A, B et C."""
            
            res = model.generate_content(prompt_v)
            txt = res.text
            
            if "BRAVO" in txt.strip().upper()[:10]:
                st.session_state.xp += 20
                if activer_ballons:
                    st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            st.session_state.attente_reponse = True
            st.rerun()
