import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# Configuration
st.set_page_config(page_title="Le Coach Magique 🌟", layout="centered")

# Design et Couleurs
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; font-weight: bold; border: none; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50; color: white; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3; color: white; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0; color: white; }
    .stChatMessage { border-radius: 15px; font-size: 1.1rem; border: 1px solid #E0E0E0; }
    button[kind="secondary"] { background-color: #FFC107; color: black; }
    /* Barre de progression personnalisée */
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "stock_photos" not in st.session_state: st.session_state.stock_photos = []
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    prenom = st.text_input("Prénom de l'élève :", value="Anaïs")
    st.write("---")
    st.write(f"Niveau actuel : **{st.session_state.xp // 100 + 1}**")
    if st.button("🔄 Reset Séance"):
        st.session_state.xp = 0
        st.session_state.messages = []
        st.session_state.stock_photos = []
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title(f"🌟 Le Coach de {prenom}")

# Barre de progression vers le prochain niveau (tous les 100 XP)
prochain_palier = ((st.session_state.xp // 100) + 1) * 100
progression = (st.session_state.xp % 100) / 100
st.write(f"⭐ **{st.session_state.xp} XP** (Objectif : {prochain_palier} XP pour le prochain badge !)")
st.progress(progression)

st.write("---")
fichiers = st.file_uploader("📸 Photos de tes leçons :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if fichiers:
    photos = [Image.open(f).convert("RGB") for f in fichiers]
    for p in photos: p.thumbnail((1024, 1024))
    st.session_state.stock_photos = photos
    st.success(f"✅ {len(photos)} page(s) prête(s) !")

col_a1, col_a2 = st.columns(2)
with col_a1:
    btn_lancer = st.button(f"🚀 LANCER LE QUIZ")
with col_a2:
    btn_fin = st.button("🏁 VOIR MON RÉSUMÉ")

# --- FONCTIONS ---
def appeler_coach(contenu):
    try:
        response = model.generate_content(contenu)
        return response.text
    except Exception as e:
        if "429" in str(e):
            st.warning("🌟 Je reprends mon souffle... Attends 20 secondes !")
        else:
            st.error(f"Erreur : {e}")
        return None

def lire_audio(texte):
    # Langue française, slow=False pour une voix plus dynamique et rapide
    tts = gTTS(text=texte, lang='fr', slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

# --- LOGIQUE QUIZ ---
if btn_lancer and st.session_state.stock_photos:
    st.session_state.messages = []
    with st.spinner("Je lis tes notes..."):
        prompt = f"Tu es le coach d'IA de {prenom} (6ème, TDAH). Pose une question QCM aérée (A, B, C) basée sur les photos."
        res = appeler_coach([prompt] + st.session_state.stock_photos)
        if res:
            st.session_state.messages.append({"role": "assistant", "content": res})
            st.session_state.attente_reponse = True

if btn_fin:
    st.balloons()
    st.info(f"### 🎉 Super séance {prenom} !\nScore final : {st.session_state.xp} XP")
    st.stop()

# --- CHAT ET AUDIO ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "👤" if msg["role"] == "user" else "🌟"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{i}"):
                audio_fp = lire_audio(msg["content"])
                st.audio(audio_fp, format="audio/mp3", autoplay=True)

# --- ZONE DE RÉPONSE ---
if st.session_state.attente_reponse:
    st.write(f"### Ta réponse {prenom} :")
    cA, cB, cC = st.columns(3)
    choix = None
    with cA: 
        if st.button("🅰️ A"): choix = "A"
    with cB: 
        if st.button("🅱️ B"): choix = "B"
    with cC: 
        if st.button("🅲 C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Je choisis la {choix}"})
        st.session_state.attente_reponse = False
        with st.spinner("Vérification..."):
            historique = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            instruction = f"""Historique : {historique}
            {prenom} a répondu {choix}. 
            1. Vérifie sur les photos si c'est juste. 
            2. Explique pourquoi et félicite-la. 
            3. Pose la question suivante (QCM A, B, C avec lignes sautées)."""
            
            reponse_coach = appeler_coach([instruction] + st.session_state.stock_photos)
            if reponse_coach:
                st.session_state.messages.append({"role": "assistant", "content": reponse_coach})
                st.session_state.attente_reponse = True
                if any(w in reponse_coach.lower() for w in ["bravo", "juste", "exact", "correct"]):
                    st.balloons()
                    st.session_state.xp += 20
                st.rerun()
