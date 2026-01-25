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
    .stButton>button { border-radius: 25px; font-weight: bold; width: 100%; }
    .upload-container { background-color: #f9f9f9; padding: 20px; border-radius: 15px; border: 2px dashed #FFC107; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

# ==============================
# INITIALISATION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Coucou Anaïs ! 👋 Prends en photo ton cours pour commencer le défi ! ✨"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False
if "images_data" not in st.session_state: st.session_state.images_data = []

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown(f"### ⭐ {st.session_state.xp} XP")
    if st.button("🗑️ Recommencer"):
        st.session_state.clear()
        st.rerun()

# ==============================
# ZONE CENTRALE : TÉLÉCHARGEMENT
# ==============================
st.title("🌟 Mon Coach Magique")

with st.container():
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    # L'option "Camera" apparaît sur Samsung quand on clique sur "Browse files" 
    # si le type est bien restreint aux images.
    uploaded_files = st.file_uploader(
        "📸 Prends une photo ou choisis une image", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
    
    if st.button("🚀 LANCER LE DÉFI QCM", type="primary"):
        if uploaded_files:
            st.session_state.quiz_en_cours = True
            st.session_state.messages = [{"role": "assistant", "content": "C'est parti ! J'analyse tes documents... ⏳"}] 
            st.session_state.first_run = True 
            # Sauvegarde des images en session pour ne pas les perdre
            st.session_state.images_data = [f.getvalue() for f in uploaded_files]
            st.session_state.mimes = [f.type for f in uploaded_files]
        else:
            st.warning("Il me faut une photo de ton cours ! 😊")
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ZONE DE CHAT
# ==============================
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=("👤" if message["role"] == "user" else "🌟")):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{hash(message['content'])}"):
                audio_data = text_to_speech(message["content"])
                st.audio(audio_data, format="audio/mp3", autoplay=True)

# ==============================
# LOGIQUE DU COACH
# ==============================

if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Je lis ton cours très attentivement..."):
            # PROMPT RENFORCÉ POUR LE FOCUS
            prompt_init = """Tu es le coach scolaire d'Anaïs (6ème). 
            CONSIGNE STRICTE : Pose une question QCM (A, B, C) basée UNIQUEMENT sur les informations présentes dans les images fournies. 
            Ne pose pas de question de culture générale hors du document. 
            Saute une ligne entre chaque option A, B et C.
            Sois très encourageant !"""
            
            contenu = [prompt_init]
            for i in range(len(st.session_state.images_data)):
                contenu.append(types.Part.from_bytes(data=st.session_state.images_data[i], mime_type=st.session_state.mimes[i]))
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=contenu)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.session_state.first_run = False
            st.rerun()

if prompt := st.chat_input("Ta réponse (A, B, C)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant", avatar="🌟"):
        # On redonne les images dans le contexte pour que Gemini garde le focus
        instruction = f"""Anaïs a répondu : '{prompt}'. 
        1. Vérifie par rapport au document fourni en photo. 
        2. Félicite-la et explique si besoin.
        3. Pose le prochain QCM (A, B, C) basé EXCLUSIVEMENT sur les images.
        Sauts de ligne entre A, B et C."""
        
        # On envoie les images + l'historique pour garder le focus
        historique = [instruction]
        for i in range(len(st.session_state.images_data)):
            historique.append(types.Part.from_bytes(data=st.session_state.images_data[i], mime_type=st.session_state.mimes[i]))
        
        # On ajoute les derniers échanges de texte
        for msg in st.session_state.messages[-3:]: 
            historique.append(msg["content"])

        response = client.models.generate_content(model="gemini-2.0-flash", contents=historique)
        
        if any(word in response.text.lower() for word in ["bravo", "super", "génial", "juste"]):
            st.balloons()
            st.session_state.xp += 20
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()
