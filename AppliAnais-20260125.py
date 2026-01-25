import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# ==============================
# CONFIGURATION & STYLE
# ==============================
st.set_page_config(page_title="Coach Magique d'Anaïs 🌟", page_icon="🌈", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 18px; }
    .stChatMessage { border-radius: 15px; margin-bottom: 15px; border: 1px solid #ddd; }
    .stButton>button { border-radius: 30px; height: 60px !important; font-size: 20px !important; width: 100%; }
    .stFileUploader section { background-color: #fff9e6; border: 2px dashed #ffc107; border-radius: 20px; padding: 20px; }
    </style>
""", unsafe_allow_html=True)

# Initialisation du modèle avec le nom complet pour éviter l'erreur NotFound
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Utilisation du nom de modèle explicite
MODEL_NAME = 'models/gemini-1.5-flash'
model = genai.GenerativeModel(model_name=MODEL_NAME)

# ==============================
# MÉMOIRE DE LA SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Coucou Anaïs ! 👋 Prends en photo tes leçons et on commence !"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False
if "mes_photos" not in st.session_state: st.session_state.mes_photos = []

# ==============================
# INTERFACE D'ACCUEIL
# ==============================
st.markdown("<h1 style='text-align: center;'>🌟 Mon Coach Magique</h1>", unsafe_allow_html=True)

if not st.session_state.quiz_en_cours:
    st.write(f"### ⭐ Score d'Anaïs : {st.session_state.xp} XP")
    
    fichiers = st.file_uploader(
        "📸 PRENDS TES PHOTOS ICI", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )
    
    if fichiers:
        # Optimisation des images pour éviter de saturer l'envoi
        st.session_state.mes_photos = []
        for f in fichiers:
            img = Image.open(f)
            if img.mode != 'RGB': img = img.convert('RGB')
            st.session_state.mes_photos.append(img)
            
        st.success(f"✅ {len(fichiers)} page(s) prête(s) !")
        
        if st.button("🚀 LANCER LE QUIZ", type="primary"):
            st.session_state.quiz_en_cours = True
            st.session_state.first_run = True
            st.rerun()

# ==============================
# ZONE DU QUIZ
# ==============================
if st.session_state.quiz_en_cours:
    for i, msg in enumerate(st.session_state.messages):
        avatar = "👤" if msg["role"] == "user" else "🌟"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"btn_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

    if prompt := st.chat_input("Ta réponse (A, B ou C)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# ==============================
# LOGIQUE IA (CORRECTION NOTFOUND)
# ==============================
if st.session_state.quiz_en_cours:
    if st.session_state.first_run or st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant", avatar="🌟"):
            with st.spinner("Je regarde tes photos... ✨"):
                try:
                    if st.session_state.first_run:
                        consigne = "Tu es le coach d'Anaïs (6ème). Analyse ces photos. Pose la 1ère question QCM (A, B, C) basée UNIQUEMENT sur ces documents. Saute une ligne entre A, B et C."
                        st.session_state.first_run = False
                    else:
                        rep = st.session_state.messages[-1]["content"]
                        consigne = f"Anaïs a répondu '{rep}'. Vérifie sur les photos. Félicite-la et pose le prochain QCM basé sur les photos. Saute des lignes."
                    
                    # Construction du contenu robuste
                    contenu_final = [consigne] + st.session_state.mes_photos
                    
                    # Appel au modèle
                    response = model.generate_content(contenu_final)
                    
                    if any(w in response.text.lower() for w in ["bravo", "super", "juste"]):
                        st.balloons()
                        st.session_state.xp += 20
                    
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Désolé Anaïs, j'ai eu un petit bug : {e}")
