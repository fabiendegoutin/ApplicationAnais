import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# Configuration pour mobile
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# Design adapté aux enfants (gros boutons et couleurs vives)
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; background-color: #FFC107; color: black; border: none; font-weight: bold; }
    .stChatMessage { border-radius: 15px; font-size: 1.1rem; border: 1px solid #E0E0E0; }
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    </style>
""", unsafe_allow_html=True)

# Connexion sécurisée à l'API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Correction du nom du modèle pour éviter l'erreur 404
model = genai.GenerativeModel('models/gemini-1.5-flash')

# --- INITIALISATION DES DONNÉES ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "stock_photos" not in st.session_state: st.session_state.stock_photos = []

# --- INTERFACE ---
st.title("🌟 Mon Coach Magique")
st.subheader(f"⭐ Score d'Anaïs : {st.session_state.xp} XP")

# Zone d'upload
st.write("---")
st.write("📸 **Prends en photo tes leçons :**")
fichiers = st.file_uploader("", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# Traitement immédiat des photos pour Android
if fichiers:
    photos_traitees = []
    for f in fichiers:
        img = Image.open(f).convert("RGB")
        img.thumbnail((1024, 1024)) # Optimisation poids pour mobile
        photos_traitees.append(img)
    st.session_state.stock_photos = photos_traitees
    st.success(f"✅ {len(st.session_state.stock_photos)} page(s) enregistrée(s) !")

# Bouton de lancement du Quiz
if st.session_state.stock_photos:
    if st.button("🚀 PRÊTE POUR LE DÉFI ?"):
        st.session_state.messages = [] # On vide le chat précédent
        with st.spinner("Je lis tes leçons..."):
            try:
                # Prompt initial optimisé
                prompt = (
                    "Tu es le coach bienveillant d'Anaïs (6ème, TDAH). "
                    "Regarde ces photos de cours. Pose une seule question en QCM (A, B ou C). "
                    "Sois très encourageant. Saute une ligne entre chaque option."
                )
                response = model.generate_content([prompt] + st.session_state.stock_photos)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur d'analyse : {e}")

# --- AFFICHAGE DU CHAT ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "👤" if msg["role"] == "user" else "🌟"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        # Lecture audio pour aider à la concentration
        if msg["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

# --- GESTION DES RÉPONSES ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    reponse_enfant = st.chat_input("Ta réponse (A, B ou C)...")
    
    if reponse_enfant:
        st.session_state.messages.append({"role": "user", "content": reponse_enfant})
        
        with st.spinner("Vérification en cours..."):
            try:
                # Instruction spécifique pour gérer l'erreur de manière pédagogique
                instruction = (
                    f"Anaïs a répondu '{reponse_enfant}'. "
                    "Vérifie par rapport aux photos de cours. "
                    "1. Si c'est juste : Félicite-la chaleureusement (+20 XP !) et donne un petit complément d'info fun. "
                    "2. Si c'est faux : Ne sois pas négatif. Donne la bonne réponse gentiment et explique-la simplement à partir du cours. "
                    "Ensuite, pose la question suivante."
                )
                
                res = model.generate_content([instruction] + st.session_state.stock_photos)
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                
                # Système de récompense visuelle
                feedback_lower = res.text.lower()
                mots_cles_succes = ["bravo", "juste", "exact", "super", "félicitations", "correct"]
                
                if any(mot in feedback_lower for mot in mots_cles_succes):
                    st.balloons()
                    st.session_state.xp += 20
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Oups, une petite erreur : {e}")
