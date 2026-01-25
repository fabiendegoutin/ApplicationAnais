import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io

# ==============================
# CONFIGURATION & DESIGN
# ==============================
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", page_icon="🌈", layout="centered")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #f0f2f6; }
    .stButton>button { border-radius: 25px; font-weight: bold; width: 100%; height: 50px; }
    .upload-container { background-color: #f9f9f9; padding: 20px; border-radius: 15px; border: 2px dashed #FFC107; margin-bottom: 20px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# Initialisation du client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='fr')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None

# ==============================
# INITIALISATION SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Coucou Anaïs ! 👋 Prends ton cours en photo et on commence ! ✨"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False
if "images_data" not in st.session_state: st.session_state.images_data = []

# ==============================
# ZONE CENTRALE : PHOTO
# ==============================
st.title("🌟 Mon Coach Magique")

with st.container():
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    
    # Version améliorée pour Huawei/Samsung : On utilise st.camera_input pour le direct 
    # ou st.file_uploader pour la galerie.
    mode_photo = st.radio("Comment veux-tu envoyer ton cours ?", ["Appareil Photo 📸", "Galerie d'images 🖼️"], horizontal=True)
    
    source_files = []
    if mode_photo == "Appareil Photo 📸":
        cam_file = st.camera_input("Prends la photo de ton cours")
        if cam_file: source_files = [cam_file]
    else:
        uploaded_files = st.file_uploader("Choisis tes images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        if uploaded_files: source_files = uploaded_files
    
    if st.button("🚀 LANCER LE DÉFI", type="primary"):
        if source_files:
            st.session_state.quiz_en_cours = True
            st.session_state.messages = [{"role": "assistant", "content": "C'est parti Anaïs ! J'analyse tes photos... ⏳"}] 
            st.session_state.first_run = True 
            st.session_state.images_data = [{"data": f.getvalue(), "mime": f.type} for f in source_files]
            st.rerun()
        else:
            st.warning("N'oublie pas de prendre une photo ! 😊")
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ZONE DE CHAT
# ==============================
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=("👤" if message["role"] == "user" else "🌟")):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{hash(message['content'])}"):
                audio_fp = text_to_speech(message["content"])
                if audio_fp:
                    st.audio(audio_fp, format="audio/mp3", autoplay=True)

# ==============================
# LOGIQUE GEMINI
# ==============================

def generer_reponse(prompt_systeme):
    contenu = [prompt_systeme]
    # On force l'envoi des images à CHAQUE fois pour ne jamais perdre le contexte du cours
    for img in st.session_state.images_data:
        contenu.append(types.Part.from_bytes(data=img["data"], mime_type=img["mime"]))
    
    # On ajoute les 4 derniers messages pour la fluidité du chat
    for msg in st.session_state.messages[-4:]:
        contenu.append(msg["content"])
        
    return client.models.generate_content(model="gemini-2.0-flash", contents=contenu)

if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Je lis ton cours..."):
            instr = "Tu es le coach d'Anaïs (6ème). Pose la 1ère question QCM (A, B, C) basée UNIQUEMENT sur les photos. Saute une ligne entre A, B et C."
            res = generer_reponse(instr)
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            st.session_state.first_run = False
            st.rerun()

if prompt := st.chat_input("Ta réponse (A, B ou C)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Attends, je regarde..."):
            instr_rep = f"Anaïs a répondu '{prompt}'. Vérifie sur les photos. Félicite-la, explique le cours s'il y a une erreur, puis pose le prochain QCM (A, B, C) basé sur les photos. Saute des lignes."
            res = generer_reponse(instr_rep)
            
            if any(w in res.text.lower() for w in ["bravo", "super", "juste", "génial"]):
                st.balloons()
                st.session_state.xp += 20
                
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            st.rerun()
