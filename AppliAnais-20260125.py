import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# Configuration
st.set_page_config(page_title="Le Coach Magique 🌟", layout="centered")

# Design optimisé : gros boutons pour les réponses
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; background-color: #FFC107; color: black; border: none; font-weight: bold; }
    .stChatMessage { border-radius: 15px; font-size: 1.1rem; border: 1px solid #E0E0E0; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50; color: white; } /* Bouton A */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3; color: white; } /* Bouton B */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0; color: white; } /* Bouton C */
    </style>
""", unsafe_allow_html=True)

# API Setup
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

# --- BARRE LATÉRALE (Paramètres) ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    prenom = st.text_input("Prénom de l'élève :", value="Anaïs")
    if st.button("Réinitialiser tout"):
        st.session_state.clear()
        st.rerun()

# --- INTERFACE ---
st.title(f"🌟 Le Coach de {prenom}")
st.subheader(f"⭐ Score : {st.session_state.xp} XP")

st.write("---")
fichiers = st.file_uploader("📸 Prends tes leçons en photo :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if fichiers:
    photos = [Image.open(f).convert("RGB") for f in fichiers]
    for p in photos: p.thumbnail((1024, 1024))
    st.session_state.stock_photos = photos
    st.success(f"✅ {len(photos)} page(s) prête(s) !")

# Lancement du Quiz
if st.session_state.stock_photos and not st.session_state.messages:
    if st.button(f"🚀 C'EST PARTI {prenom.upper()} !"):
        with st.spinner("Je prépare ton défi..."):
            prompt = f"""Tu es le coach d'IA de {prenom} (classe de 6ème, profil TDAH). 
            Analyse ces photos de cours et pose une seule question QCM.
            IMPORTANT : 
            1. Présente les choix sous la forme :
               A) [Choix 1]
               
               B) [Choix 2]
               
               C) [Choix 3]
            2. Saute bien une ligne entre chaque choix pour que ce soit aéré.
            3. Sois super encourageant !"""
            try:
                res = model.generate_content([prompt] + st.session_state.stock_photos)
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                st.session_state.attente_reponse = True
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- AFFICHAGE DU CHAT ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "👤" if msg["role"] == "user" else "🌟"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

# --- ZONE DE RÉPONSE (BOUTONS QCM) ---
if st.session_state.get("attente_reponse"):
    st.write("### Ta réponse :")
    colA, colB, colC = st.columns(3)
    choix = None
    
    with colA: 
        if st.button("🅰️ A"): choix = "A"
    with colB: 
        if st.button("🅱️ B"): choix = "B"
    with colC: 
        if st.button("🅲 C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Ma réponse est la {choix}"})
        st.session_state.attente_reponse = False
        
        with st.spinner("Vérification..."):
            instruction = f"""{prenom} a choisi la réponse {choix}.
            1. Vérifie sur les photos.
            2. Si c'est juste : Félicite-la chaleureusement (+20 XP).
            3. Si c'est faux : Donne la bonne réponse gentiment et explique-la simplement.
            4. Pose la question suivante en sautant une ligne entre les choix A, B et C."""
            
            try:
                res = model.generate_content([instruction] + st.session_state.stock_photos)
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                st.session_state.attente_reponse = True
                
                if any(w in res.text.lower() for w in ["bravo", "juste", "exact", "correct", "super"]):
                    st.balloons()
                    st.session_state.xp += 20
                st.rerun()
            except Exception as e:
                st.error(f"Oups : {e}")

# Bouton de résumé final
if st.session_state.messages:
    if st.button("🏁 J'ai fini pour aujourd'hui !"):
        st.balloons()
        st.success(f"### 🎉 Bravo {prenom} !\nTu as gagné {st.session_state.xp} XP au total. Tu peux être fière de toi !")
