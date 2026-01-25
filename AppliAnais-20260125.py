import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# ==============================
# CONFIGURATION
# ==============================
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", page_icon="🌈")

# Utilisation de la version STABLE du SDK
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Utilisation de gemini-1.5-flash (ultra stable pour l'analyse d'images)
model = genai.GenerativeModel('gemini-1.5-flash')

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
    st.session_state.messages = [{"role": "assistant", "content": "Coucou Anaïs ! 👋 Envoie tes photos et je lirai tout pour toi ! ✨"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False
if "images_pil" not in st.session_state: st.session_state.images_pil = []

# ==============================
# INTERFACE PHOTO
# ==============================
st.title("🌟 Mon Coach Magique")

if not st.session_state.quiz_en_cours:
    uploaded_files = st.file_uploader("📸 Ajoute tes photos de cours", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if uploaded_files:
        # On convertit les fichiers en vraies images PIL pour Gemini
        st.session_state.images_pil = [Image.open(f) for f in uploaded_files]
        st.success(f"✅ {len(uploaded_files)} photo(s) reçue(s) !")
        
        if st.button("🚀 LANCER LE QUIZ"):
            st.session_state.quiz_en_cours = True
            st.session_state.first_run = True
            st.rerun()

# ==============================
# ZONE DE CHAT
# ==============================
if st.session_state.quiz_en_cours:
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar=("👤" if message["role"] == "user" else "🌟")):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"voc_{i}"):
                    audio_fp = text_to_speech(message["content"])
                    if audio_fp: st.audio(audio_fp, format="audio/mp3", autoplay=True)

# ==============================
# LOGIQUE DE RÉPONSE (FOCUS IMAGE)
# ==============================
def obtenir_reponse(consigne_texte):
    # On envoie TOUJOURS les images PIL avec le texte pour forcer le focus
    contenu_a_envoyer = [consigne_texte] + st.session_state.images_pil
    response = model.generate_content(contenu_a_envoyer)
    return response.text

if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.spinner("Je lis tes photos..."):
        prompt = "Tu es le coach d'Anaïs (6ème). Pose une question QCM (A, B, C) basée UNIQUEMENT sur ces photos. Saute une ligne entre chaque choix."
        reponse_coach = obtenir_reponse(prompt)
        st.session_state.messages.append({"role": "assistant", "content": reponse_coach})
        st.session_state.first_run = False
        st.rerun()

if prompt_user := st.chat_input("Ta réponse..."):
    st.session_state.messages.append({"role": "user", "content": prompt_user})
    with st.spinner("Je vérifie sur tes photos..."):
        instruction = f"Anaïs a répondu '{prompt_user}'. Vérifie dans les photos. Félicite-la et pose le prochain QCM basé sur les photos."
        reponse_coach = obtenir_reponse(instruction)
        
        if any(w in reponse_coach.lower() for w in ["bravo", "juste", "super"]):
            st.balloons()
            st.session_state.xp += 20
        
        st.session_state.messages.append({"role": "assistant", "content": reponse_coach})
        st.rerun()
