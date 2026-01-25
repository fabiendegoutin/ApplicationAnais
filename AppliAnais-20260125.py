import streamlit as st
from google import genai
from google.genai import types

# ==============================
# CONFIGURATION & DESIGN
# ==============================
st.set_page_config(page_title="Mon Coach Magique", page_icon="🌈", layout="centered")

# Personnalisation visuelle pour mobile
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #f0f2f6; }
    .stButton>button { border-radius: 25px; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.05); }
    </style>
""", unsafe_allow_html=True)

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Oups ! La clé API est manquante dans les Secrets Streamlit.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==============================
# INITIALISATION DE LA SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Coucou championne ! Prête à devenir une star dans tes révisions ? Envoie-moi tes photos ! 📸✨"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False

# ==============================
# SIDEBAR (Espace Progression)
# ==============================
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🚀 Mon Espace</h1>", unsafe_allow_html=True)
    
    # Score stylisé
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FFEB3B, #FFC107); padding: 20px; border-radius: 15px; text-align: center; color: black; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);'>
            <h2 style='margin: 0;'>⭐ {st.session_state.xp} XP</h2>
            <p style='margin: 0; font-weight: bold;'>Tu es géniale !</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    uploaded_files = st.file_uploader("📥 Dépose tes photos ici", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if st.button("🚀 LANCER LE DÉFI QCM", use_container_width=True, type="primary"):
        if uploaded_files:
            st.session_state.quiz_en_cours = True
            st.session_state.messages = [] 
            st.session_state.first_run = True 
            st.rerun()
        else:
            st.warning("N'oublie pas les photos de ton cours ! 📸")

    if st.button("🗑️ Recommencer à zéro", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": "C'est reparti pour une nouvelle aventure ! 🎈"}]
        st.session_state.quiz_en_cours = False
        st.rerun()

# ==============================
# ZONE DE CHAT
# ==============================
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🌟"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            # Icône haut-parleur style mobile
            with st.expander("🔊 Écouter"):
                st.audio(f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=fr&q={message['content'].replace(' ', '+')}", format="audio/mp3")

# ==============================
# LOGIQUE DU COACH BIENVEILLANT
# ==============================

# 1. Déclenchement du Quiz
if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Je lis tes notes précieuses... 🧠✨"):
            prompt_init = """Tu es un coach scolaire ultra encourageant et positif. 
            Analyse ces images et pose la PREMIÈRE question d'un quiz.
            RÈGLES :
            - Toujours sous forme de QCM (A, B ou C).
            - Sois très enthousiaste, utilise des emojis.
            - Pose une seule question et attends.
            """
            
            contenu = [prompt_init]
            for f in uploaded_files:
                contenu.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type))
            
            try:
                response = client.models.generate_content(model="gemini-2.0-flash", contents=contenu)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.session_state.first_run = False
                st.rerun()
            except Exception as e:
                st.error(f"Oups ! {e}")

# 2. Saisie de la réponse
if prompt := st.chat_input("Tape A, B ou C ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# 3. Correction et Question suivante
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    user_reply = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Je vérifie... ✨"):
            instruction = f"""L'enfant a répondu : '{user_reply}'. 
            1. Félicite l'enfant quel que soit le résultat (sois très doux).
            2. Si c'est faux, explique avec beaucoup de bienveillance sans dire 'c'est mauvais'.
            3. Si c'est juste, célèbre sa réussite avec des emojis de fête.
            4. Pose ensuite la question suivante sous forme de QCM (A, B ou C).
            Une seule question à la fois.
            """
            
            historique = [msg["content"] for msg in st.session_state.messages]
            historique.append(instruction)
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=historique)
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.session_state.xp += 20 # Plus de points pour l'effort !
            st.rerun()
