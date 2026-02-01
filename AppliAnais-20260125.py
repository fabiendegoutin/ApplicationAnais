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
    .stChatMessage { border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    
    /* Alignement de l'audio à droite */
    .audio-container { display: flex; justify-content: space-between; align-items: center; }
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

# --- SIDEBAR (Options et Ballons) ---
with st.sidebar:
    st.header("⚙️ Options")
    prenom = st.text_input("Prénom :", value="Anaïs")
    # Retour de l'option des ballons
    activer_ballons = st.toggle("Activer les ballons 🎈", value=True)
    st.write("---")
    if st.button("🗑️ Recommencer"):
        st.session_state.cours_texte = None
        st.session_state.messages = []
        st.rerun()

# --- INTERFACE ---
st.title(f"✨ Le Coach d'Anaïs")
st.write(f"🚀 **Score : {st.session_state.xp} XP**")

fichiers = st.file_uploader("📸 Photos de la leçon :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# --- MÉMORISATION ---
if fichiers and st.session_state.cours_texte is None:
    if st.button("🧠 Étape 1 : Mémoriser le cours"):
        with st.spinner("Analyse des images..."):
            photos = [Image.open(f).convert("RGB") for f in fichiers]
            for p in photos: p.thumbnail((1024, 1024))
            contenu = ["Extrais tout le texte de ces images. Sois précis."] + photos
            res = model.generate_content(contenu)
            st.session_state.cours_texte = res.text
            st.success("✅ Cours mémorisé !")

# --- LANCER UNE QUESTION ---
if st.button("🚀 LANCER UNE QUESTION"):
    if st.session_state.cours_texte is None:
        st.warning("Mémorise d'abord ton cours ! 🧠")
    else:
        st.session_state.messages = []
        prompt = f"""Cours : {st.session_state.cours_texte}. 
        Pose une question QCM courte.
        RÈGLES :
        - Saute une ligne vide entre chaque option A, B et C.
        - Ne fais aucune introduction."""
        res = model.generate_content(prompt)
        st.session_state.messages.append({"role": "assistant", "content": res.text})
        st.session_state.attente_reponse = True
        st.rerun()

# --- AFFICHAGE CHAT AVEC AUDIO À DROITE ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "🌈" if msg["role"] == "assistant" else "⭐"
    with st.chat_message(msg["role"], avatar=avatar):
        col_txt, col_audio = st.columns([0.85, 0.15])
        with col_txt:
            st.markdown(msg["content"])
        with col_audio:
            if msg["role"] == "assistant":
                if st.button("🔊", key=f"audio_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

# --- RÉPONSES ---
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
            
            CONSIGNES :
            1. Si juste : commence par 'BRAVO'.
            2. Si faux : commence par 'ZUT'. Explique la bonne réponse en 2 phrases MAXIMUM.
            3. INTERDIT : Ne dis jamais 'Le texte dit que' ou 'D'après le texte'. Parle directement du sujet.
            4. Pose ensuite une nouvelle question QCM (A, B, C) bien aérée."""
            
            res = model.generate_content(prompt_v)
            txt = res.text
            
            # Gestion des ballons
            nettoyage_txt = txt.strip().upper()
            if nettoyage_txt.startswith("BRAVO") or "BRAVO" in nettoyage_txt[:10]:
                st.session_state.xp += 20
                if activer_ballons:
                    st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            st.session_state.attente_reponse = True
            st.rerun()
