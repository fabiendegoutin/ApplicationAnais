import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# Configuration
st.set_page_config(page_title="Le Coach Magique d'Anaïs 🌟", layout="centered")

# Style CSS
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
    st.error("Clé API manquante.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False

def obtenir_badge(xp):
    if xp >= 500: return "🏆 Maître des Leçons"
    if xp >= 300: return "💎 Expert en Herbe"
    if xp >= 100: return "🌟 Apprenti Brillant"
    return "🌱 Débutant Motivé"

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    prenom = st.text_input("Prénom :", value="Anaïs")
    st.subheader(f"Rang : {obtenir_badge(st.session_state.xp)}")
    if st.button("🔄 Reset"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

# --- INTERFACE ---
st.title(f"🌟 Le Coach de {prenom}")
st.write(f"⭐ **{st.session_state.xp} XP** — Badge : {obtenir_badge(st.session_state.xp)}")
st.progress(min((st.session_state.xp % 100) / 100, 1.0))

# --- ÉTAPE 1 : CHARGEMENT ET EXTRACTION (UNE SEULE FOIS) ---
if st.session_state.cours_texte is None:
    fichiers = st.file_uploader("📸 Dépose les photos de tes leçons :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    if fichiers:
        if st.button("🧠 Mémoriser le cours"):
            with st.spinner("Je lis ton cours..."):
                photos = [Image.open(f).convert("RGB") for f in fichiers]
                prompt_extract = "Tu es un assistant pédagogique. Analyse ces images et extrais-en tout le contenu de manière structurée pour pouvoir poser des questions ensuite. Ne réponds que le contenu du cours, rien d'autre."
                try:
                    res = model.generate_content([prompt_extract] + photos)
                    st.session_state.cours_texte = res.text
                    st.success("C'est bon ! J'ai tout appris. On commence ?")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
else:
    st.info("✅ Cours mémorisé. Je suis prêt !")

# --- ÉTAPE 2 : LOGIQUE DU QUIZ ---
col1, col2 = st.columns(2)
with col1:
    # --- ÉTAPE 2 : LOGIQUE DU QUIZ AUTOMATISÉE ---
if st.session_state.cours_texte:
    st.info("✅ Le cours est en mémoire. Prête pour un défi ?")
    
    if st.button("🚀 LANCER UNE QUESTION"):
        st.session_state.messages = [] # On vide pour une nouvelle question
        with st.spinner("Je prépare ta question..."):
            prompt_q = f"Basé sur ce cours : '{st.session_state.cours_texte}', pose une seule question QCM (A, B, C) courte à {prenom} (6ème, TDAH). Sois très encourageant et utilise des emojis."
            try:
                res = model.generate_content(prompt_q)
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                st.session_state.attente_reponse = True
                st.rerun() # On force l'affichage de la question
            except Exception as e:
                st.error(f"Zut, petit souci technique : {e}")

    else:
        # Si le texte n'est pas encore extrait, on propose de le faire
        if fichiers:
            if st.button("🧠 ÉTAPE 1 : Apprendre ma leçon"):
                with st.spinner("Lecture des photos..."):
                    photos = [Image.open(f).convert("RGB") for f in fichiers]
                    prompt_extract = "Analyse ces images et extrais tout le contenu pédagogique. Ne réponds que le texte."
                    res = model.generate_content([prompt_extract] + photos)
                    st.session_state.cours_texte = res.text
                    st.success("C'est bon ! Appuie maintenant sur Lancer !")
                    st.rerun()
    else:
        st.warning("Commence par ajouter une photo de ta leçon en haut ! 📸")

with col2:
    if st.button("🏁 RÉSUMÉ"):
        st.balloons()
        st.info(f"Bravo {prenom} ! Tu as gagné {st.session_state.xp} XP aujourd'hui.")

# --- AFFICHAGE CHAT ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🌟" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and st.button("🔊 Écouter", key=f"snd_{i}"):
            tts = gTTS(text=msg["content"], lang='fr')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format="audio/mp3", autoplay=True)

# --- ZONE DE RÉPONSE ---
if st.session_state.attente_reponse:
    st.write("---")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A"): choix = "A"
    if c2.button("B"): choix = "B"
    if c3.button("C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Ma réponse est la {choix}"})
        st.session_state.attente_reponse = False
        
        with st.spinner("Vérification..."):
            prompt_v = f"""Cours : {st.session_state.cours_texte}
            Question posée : {st.session_state.messages[-2]['content']}
            Réponse d'Anaïs : {choix}
            Directives : Si juste, félicite chaudement (+ confettis). Si faux, explique avec douceur sans la dévaloriser. 
            Ensuite, propose une NOUVELLE question QCM (A, B, C)."""
            
            res = model.generate_content(prompt_v)
            if "bravo" in res.text.lower() or "juste" in res.text.lower() or "correct" in res.text.lower():
                st.session_state.xp += 20
                st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            st.session_state.attente_reponse = True
            st.rerun()

