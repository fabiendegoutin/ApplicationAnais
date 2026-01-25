import streamlit as st
from google import genai  # Utilisation de la nouvelle bibliothèque
from PIL import Image
from datetime import datetime

# --- 1. CONFIGURATION DE L'IA ---
API_KEY = st.secrets["GEMINI_API_KEY"]

# Nouvelle méthode pour initialiser Gemini (SDK 2.0)
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-1.5-flash" 

# --- 2. INITIALISATION DE LA MÉMOIRE (Session State) ---
if 'xp' not in st.session_state:
    st.session_state.xp = 0
if 'badges' not in st.session_state:
    st.session_state.badges = []
if 'historique' not in st.session_state:
    st.session_state.historique = []
if 'dernier_quiz' not in st.session_state:
    st.session_state.dernier_quiz = None

def ajouter_xp(montant):
    st.session_state.xp += montant
    if st.session_state.xp >= 100 and "🚀 Apprenti" not in st.session_state.badges:
        st.session_state.badges.append("🚀 Apprenti")
    if st.session_state.xp >= 300 and "👑 Champion" not in st.session_state.badges:
        st.session_state.badges.append("👑 Champion")

# --- 3. INTERFACE ET STYLE ---
st.set_page_config(page_title="Mon Coach Magique", page_icon="🎓")

with st.sidebar:
    st.title("🏆 Mon Score")
    st.metric(label="Total XP", value=f"{st.session_state.xp} pts")
    
    st.subheader("🏅 Mes Badges")
    for b in st.session_state.badges:
        st.success(b)
        
    st.divider()
    st.subheader("📜 Historique")
    if not st.session_state.historique:
        st.write("Aucun chapitre validé pour le moment.")
    else:
        for item in st.session_state.historique:
            st.info(f"✅ {item['titre']}\n\n*{item['date']}*")

    st.divider()
    st.subheader("⚙️ Réglages")
    niveau = st.selectbox("Niveau", ["Primaire", "Collège", "Lycée"])
    mode_tdah = st.checkbox("Aide au Focus (TDAH)", value=True)
    mode_confiance = st.checkbox("Encouragement +", value=True)

# --- 4. CŒUR DE L'APPLICATION ---
st.title("🌟 Ton Assistant d'Étude")
st.write("Transforme tes photos de cours en un défi amusant !")

uploaded_files = st.file_uploader(
    "Prends tes photos de cours ici :", 
    type=['png', 'jpg', 'jpeg'], 
    accept_multiple_files=True,
    help="Tu peux prendre plusieurs photos à la suite !"
)

if uploaded_files:
    st.image([Image.open(f) for f in uploaded_files], width=100)
    chapitre_nom = st.text_input("Comment s'appelle ce chapitre ? (ex: Les Volcans)", "Mon Cours")

    if st.button("Lancer le défi ! ✨"):
        with st.spinner("Je lis ton cours avec attention..."):
            images = [Image.open(f) for f in uploaded_files]
            
            prompt = f"""
            Tu es un coach bienveillant pour un enfant ({niveau}). 
            Analyse ces photos.
            Crée 3 questions courtes et ludiques.
            
            CONSIGNES :
            - {"TDAH : Utilise des phrases ultra-courtes et des emojis." if mode_tdah else ""}
            - {"CONFIANCE : Commence par dire à l'enfant que son cours est intéressant. En cas d'erreur, donne un indice." if mode_confiance else ""}
            - Donne les solutions cachées à la fin.
            """
            
            try:
                # Nouvelle syntaxe pour générer le contenu avec des images
                # On envoie une liste contenant le texte et les objets images
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=[prompt] + images
                )
                
                st.session_state.dernier_quiz = response.text
                ajouter_xp(20) 
                st.rerun()
            except Exception as e:
                st.error(f"Oups ! Une petite erreur : {e}")

# Affichage du quiz
if st.session_state.dernier_quiz:
    st.markdown("---")
    st.markdown(st.session_state.dernier_quiz)
    
    if st.button("J'ai terminé le défi ! 🏁"):
        date_jour = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.session_state.historique.append({"titre": chapitre_nom, "date": date_jour})
        ajouter_xp(50)
        st.session_state.dernier_quiz = None
        st.balloons()
        st.success("Bravo Anaïs ! +50 XP !")
        st.rerun()