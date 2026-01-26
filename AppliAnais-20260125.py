import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# Configuration pour mobile
st.set_page_config(page_title="Le Coach Magique 🌟", layout="centered")

# Design personnalisé pour Anaïs (TDAH-friendly)
st.markdown("""
    <style>
    /* Gros boutons colorés pour les réponses */
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; font-weight: bold; border: none; }
    
    /* Couleurs spécifiques pour les choix QCM */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50; color: white; } /* Vert */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3; color: white; } /* Bleu */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0; color: white; } /* Violet */
    
    /* Style des bulles de chat */
    .stChatMessage { border-radius: 15px; font-size: 1.1rem; border: 1px solid #E0E0E0; }
    
    /* Bouton lancer et terminer */
    button[kind="secondary"] { background-color: #FFC107; color: black; }
    </style>
""", unsafe_allow_html=True)

# Connexion à l'API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
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
    if st.button("🔄 Réinitialiser la séance"):
        st.session_state.xp = 0
        st.session_state.messages = []
        st.session_state.stock_photos = []
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title(f"🌟 Le Coach de {prenom}")
st.subheader(f"⭐ Score actuel : {st.session_state.xp} XP")

# Zone de capture
st.write("---")
fichiers = st.file_uploader("📸 Dépose ou prends tes leçons en photo :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if fichiers:
    photos_traitees = []
    for f in fichiers:
        img = Image.open(f).convert("RGB")
        img.thumbnail((1024, 1024))
        photos_traitees.append(img)
    st.session_state.stock_photos = photos_traitees
    st.success(f"✅ {len(st.session_state.stock_photos)} page(s) enregistrée(s) !")

# Boutons d'action
col_action1, col_action2 = st.columns(2)
with col_action1:
    btn_lancer = st.button(f"🚀 LANCER LE DÉFI")
with col_action2:
    btn_fin = st.button("🏁 VOIR MON RÉSUMÉ")

# --- LOGIQUE DE GÉNÉRATION (Gestion Erreur 429) ---
def appeler_coach(prompt_complet):
    try:
        response = model.generate_content(prompt_complet)
        return response.text
    except Exception as e:
        if "429" in str(e):
            st.warning("🌟 Oups ! Le coach reprend son souffle (trop de questions d'un coup). Attends 30 petites secondes et réessaye !")
        else:
            st.error(f"Désolé, il y a un petit souci technique : {e}")
        return None

# Lancement
if btn_lancer and st.session_state.stock_photos:
    st.session_state.messages = []
    with st.spinner("Analyse de tes cours..."):
        prompt = f"""Tu es le coach d'IA de {prenom} (6ème, TDAH). 
        Analyse ces photos. Pose une seule question QCM.
        Mise en forme :
        A) [Option 1]
        
        B) [Option 2]
        
        C) [Option 3]
        Saute bien une ligne entre les options. Sois très encourageant !"""
        resultat = appeler_coach([prompt] + st.session_state.stock_photos)
        if resultat:
            st.session_state.messages.append({"role": "assistant", "content": resultat})
            st.session_state.attente_reponse = True

# Résumé final
if btn_fin:
    st.balloons()
    st.info(f"### 🎉 Bravo {prenom} !\nTu as terminé avec **{st.session_state.xp} XP**. Tu as bien travaillé !")
    st.stop()

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

# --- ZONE DE RÉPONSE CLICABLE ---
if st.session_state.attente_reponse:
    st.write(f"### À toi de jouer {prenom} :")
    cA, cB, cC = st.columns(3)
    choix = None
    with cA: 
        if st.button("🅰️ A"): choix = "A"
    with cB: 
        if st.button("🅱️ B"): choix = "B"
    with cC: 
        if st.button("🅲 C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Je choisis la réponse {choix}"})
        st.session_state.attente_reponse = False
        with st.spinner("Vérification..."):
            instruction = f"""{prenom} a répondu {choix}. 
            1. Vérifie sur les photos. 
            2. Si c'est juste : Félicite-la (+20 XP). 
            3. Si c'est faux : Donne la bonne réponse gentiment et explique-la simplement.
            4. Pose la question suivante (QCM A, B, C avec lignes sautées)."""
            
            reponse_coach = appeler_coach([instruction] + st.session_state.stock_photos)
            if reponse_coach:
                st.session_state.messages.append({"role": "assistant", "content": reponse_coach})
                st.session_state.attente_reponse = True
                
                # Feedback visuel
                if any(w in reponse_coach.lower() for w in ["bravo", "juste", "exact", "super", "correct"]):
                    st.balloons()
                    st.session_state.xp += 20
                st.rerun()
