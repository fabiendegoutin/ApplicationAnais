import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ÉCRAN LARGE ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="wide")

st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 3em; font-weight: bold; width: 100%; }
    .stChatMessage { border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- CONNEXION IA ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Utilisation du modèle 1.5 Flash (le meilleur pour les photos mobiles)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- INITIALISATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "photos_data" not in st.session_state:
    st.session_state.photos_data = []

# --- INTERFACE PRINCIPALE ---
st.title("🌟 Le Coach Magique d'Anaïs")

# Zone de téléchargement
with st.expander("📸 CLIQUE ICI POUR AJOUTER TES PHOTOS", expanded=not st.session_state.photos_data):
    uploaded_files = st.file_uploader("Prends tes pages de cours en photo", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    
    if uploaded_files:
        # Stockage robuste : on transforme les photos en format compris par Google
        st.session_state.photos_data = []
        for f in uploaded_files:
            img = Image.open(f)
            # On réduit un peu la taille pour que ça passe mieux sur la connexion mobile
            img.thumbnail((1024, 1024))
            st.session_state.photos_data.append(img)
        st.success(f"✅ {len(uploaded_files)} page(s) prête(s) ! Tu peux fermer ce volet.")

# --- ZONE DE QUIZ ---
if st.session_state.photos_data:
    st.info(f"Score actuel : {st.session_state.xp} XP")
    
    # Bouton pour démarrer ou réinitialiser
    if st.button("🚀 LANCER LE DÉFI (QCM)"):
        st.session_state.messages = [] # On vide le chat pour recommencer
        
        with st.spinner("Analyse des photos en cours..."):
            prompt = "Tu es le coach d'Anaïs (6ème). Analyse ces photos de cours. Pose la 1ère question en QCM (A, B ou C). Sois très encourageant et saute une ligne entre les choix."
            try:
                # On envoie le texte + la liste d'images PIL
                response = model.generate_content([prompt] + st.session_state.photos_data)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur d'analyse : {e}")

    # Affichage du Chat
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar=("👤" if msg["role"] == "user" else "🌟")):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"audio_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

    # Entrée de la réponse
    if prompt_anais := st.chat_input("Ta réponse (A, B ou C)..."):
        st.session_state.messages.append({"role": "user", "content": prompt_anais})
        
        with st.spinner("Je vérifie..."):
            consigne = f"Anaïs a répondu '{prompt_anais}'. Vérifie sur les photos. Félicite-la et pose la question suivante en QCM."
            try:
                response = model.generate_content([consigne] + st.session_state.photos_data)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                if "bravo" in response.text.lower() or "super" in response.text.lower():
                    st.balloons()
                    st.session_state.xp += 20
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")
else:
    st.warning("👋 Coucou Anaïs ! Commence par ajouter les photos de ta leçon juste au-dessus.")
