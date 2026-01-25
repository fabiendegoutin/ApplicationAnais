import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io

# ==============================
# CONFIGURATION & STYLE
# ==============================
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", page_icon="🌈", layout="centered")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #f0f2f6; }
    .stButton>button { border-radius: 25px; font-weight: bold; width: 100%; height: 50px; }
    .upload-section { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 2px solid #EEE; margin-bottom: 20px; }
    .status-box { padding: 10px; border-radius: 10px; background-color: #FFF9C4; text-align: center; font-weight: bold; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='fr')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# ==============================
# INITIALISATION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Coucou Anaïs ! 👋 Envoie-moi les photos de ton cours (même s'il y a plusieurs pages) et on commence ! ✨"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False
if "temp_photos" not in st.session_state: st.session_state.temp_photos = []

# ==============================
# BARRE LATÉRALE (SCORE)
# ==============================
with st.sidebar:
    st.markdown(f"## ⭐ {st.session_state.xp} Points XP")
    if st.button("🔄 Recommencer à zéro"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

# ==============================
# ZONE CENTRALE : LES PHOTOS
# ==============================
st.title("🌟 Mon Coach Magique")

if not st.session_state.quiz_en_cours:
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📸 Étape 1 : Ajoute tes photos")
    
    # On utilise le file_uploader classique car il permet le "multi-fichiers" 
    # et fonctionne généralement mieux pour plusieurs pages.
    uploaded_files = st.file_uploader(
        "Clique ici pour prendre des photos ou choisir des images", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True,
        help="Tu peux sélectionner plusieurs photos à la fois !"
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} photo(s) prête(s) !")
        # Aperçu rapide pour vérifier la netteté
        cols = st.columns(3)
        for idx, file in enumerate(uploaded_files):
            cols[idx % 3].image(file, use_container_width=True)

        if st.button("🚀 LANCER LE QUIZ", type="primary"):
            st.session_state.temp_photos = [{"data": f.getvalue(), "mime": f.type} for f in uploaded_files]
            st.session_state.quiz_en_cours = True
            st.session_state.first_run = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ZONE DE CHAT
# ==============================
if st.session_state.quiz_en_cours:
    # Rappel du cours actif
    st.markdown(f"<div class='status-box'>📖 Cours actuel : {len(st.session_state.temp_photos)} page(s)</div>", unsafe_allow_html=True)

    for i, message in enumerate(st.session_state.messages):
        avatar = "👤" if message["role"] == "user" else "🌟"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"voc_{i}"):
                    audio_fp = text_to_speech(message["content"])
                    if audio_fp: st.audio(audio_fp, format="audio/mp3", autoplay=True)

# ==============================
# LOGIQUE GEMINI (MULTI-IMAGES)
# ==============================
def interroger_gemini(consigne):
    contenu = [consigne]
    # On injecte TOUTES les photos stockées
    for img in st.session_state.temp_photos:
        contenu.append(types.Part.from_bytes(data=img["data"], mime_type=img["mime"]))
    # On ajoute l'historique récent
    for msg in st.session_state.messages[-5:]:
        contenu.append(msg["content"])
    return client.models.generate_content(model="gemini-2.0-flash", contents=contenu)

# Premier lancement
if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Je lis toutes tes pages de cours... 📖"):
            res = interroger_gemini("Tu es le coach d'Anaïs (6ème). Analyse TOUTES les photos reçues. Pose la 1ère question QCM (A, B, C) basée UNIQUEMENT sur ces documents. Saute une ligne entre A, B et C.")
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            st.session_state.first_run = False
            st.rerun()

# Réponse d'Anaïs
if prompt := st.chat_input("Ta réponse (A, B ou C)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Vérification... ✨"):
            res = interroger_gemini(f"Anaïs a répondu '{prompt}'. Vérifie dans les photos. Félicite-la (Bravo Anaïs !), explique si besoin, puis pose le prochain QCM basé sur les photos.")
            
            if any(w in res.text.lower() for w in ["bravo", "super", "juste", "génial"]):
                st.balloons()
                st.session_state.xp += 20
                
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            st.rerun()
