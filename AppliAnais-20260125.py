import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach Magique d'Anaïs 🌟", layout="centered")

# Design adapté (plus doux et visuel)
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; font-weight: bold; border: none; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50; color: white; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3; color: white; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0; color: white; }
    .stChatMessage { border-radius: 15px; font-size: 1.1rem; border: 1px solid #E0E0E0; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- INITIALISATION DES VARIABLES ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False

def obtenir_badge(xp):
    if xp >= 500: return "🏆 Maître des Leçons"
    if xp >= 300: return "💎 Expert en Herbe"
    if xp >= 100: return "🌟 Apprenti Brillant"
    return "🌱 Débutant Motivé"

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    prenom = st.text_input("Prénom :", value="Anaïs")
    st.subheader(f"Rang : {obtenir_badge(st.session_state.xp)}")
    if st.button("🔄 Recommencer à zéro"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title(f"🌟 Le Coach de {prenom}")
st.write(f"⭐ **{st.session_state.xp} XP** — Objectif : {((st.session_state.xp // 100) + 1) * 100} XP")
st.progress(min((st.session_state.xp % 100) / 100, 1.0))

# Chargement des photos
fichiers = st.file_uploader("📸 Dépose les photos de tes leçons :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

st.write("---")

# --- LOGIQUE DU BOUTON MAGIQUE ---
if st.button("🚀 LANCER UNE QUESTION"):
    if not fichiers and not st.session_state.cours_texte:
        st.warning("Oups ! Ajoute d'abord une photo de ton cours en haut. 📸")
    else:
        with st.spinner("Je prépare ton défi..."):
            # Étape 1 : Si on n'a pas encore extrait le texte des photos
            if st.session_state.cours_texte is None:
                photos = [Image.open(f).convert("RGB") for f in fichiers]
                prompt_extract = "Analyse ces images de cours et extrais tout le contenu texte de manière détaillée. Ne réponds que le contenu du cours."
                res_extract = model.generate_content([prompt_extract] + photos)
                st.session_state.cours_texte = res_extract.text
            
            # Étape 2 : Poser la question à partir du texte (économise les tokens !)
            st.session_state.messages = [] # On nettoie l'écran pour la nouvelle question
            prompt_q = f"Basé sur ce cours : '{st.session_state.cours_texte}', pose une seule question QCM (A, B, C) courte à {prenom} (6ème, TDAH). Sois très encourageant avec des emojis."
            res_q = model.generate_content(prompt_q)
            
            st.session_state.messages.append({"role": "assistant", "content": res_q.text})
            st.session_state.attente_reponse = True
            st.rerun()

# --- AFFICHAGE DE LA DISCUSSION ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "🌟" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

# --- ZONE DE RÉPONSE (BOUTONS) ---
if st.session_state.attente_reponse:
    st.write(f"### Ta réponse {prenom} :")
    cA, cB, cC = st.columns(3)
    choix = None
    if cA.button("🅰️ A"): choix = "A"
    if cB.button("🅱️ B"): choix = "B"
    if cC.button("🅲 C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Je choisis la {choix}"})
        st.session_state.attente_reponse = False # On bloque les boutons pendant le calcul
        
        with st.spinner("Vérification..."):
            prompt_v = f"""Cours de référence : {st.session_state.cours_texte}
            Dernière question : {st.session_state.messages[-2]['content']}
            Réponse d'Anaïs : {choix}
            
            Instructions : 
            1. Si c'est juste : Félicite-la avec enthousiasme.
            2. Si c'est faux : Explique la bonne réponse avec beaucoup de douceur.
            3. Propose IMMÉDIATEMENT une nouvelle question QCM (A, B, C) différente."""
            
            res_coach = model.generate_content(prompt_v)
            reponse_texte = res_coach.text
            
            # Bonus XP si c'est gagné
            if any(w in reponse_texte.lower() for w in ["bravo", "juste", "exact", "correct", "félicitations"]):
                st.session_state.xp += 20
                st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": reponse_texte})
            st.session_state.attente_reponse = True # On rouvre les boutons pour la suite
            st.rerun()
