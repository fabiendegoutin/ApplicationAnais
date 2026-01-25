import streamlit as st
from openai import OpenAI
from PIL import Image
from datetime import datetime
import io
import base64

# ==============================
# CONFIG STREAMLIT (TOUJOURS EN PREMIER)
# ==============================
st.set_page_config(page_title="Mon Coach Magique", page_icon="🎓")

# ==============================
# CONFIGURATION OPENAI
# ==============================
# Dans Streamlit Cloud > Settings > Secrets :
# OPENAI_API_KEY = "ta_cle"
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

MODEL_ID = "gpt-4o"  # vision + texte (le plus stable)

# ==============================
# SESSION STATE
# ==============================
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "badges" not in st.session_state:
    st.session_state.badges = []
if "historique" not in st.session_state:
    st.session_state.historique = []
if "dernier_quiz" not in st.session_state:
    st.session_state.dernier_quiz = None
if "chapitre_nom" not in st.session_state:
    st.session_state.chapitre_nom = "Mon Cours"

def ajouter_xp(montant):
    st.session_state.xp += montant
    if st.session_state.xp >= 100 and "🚀 Apprenti" not in st.session_state.badges:
        st.session_state.badges.append("🚀 Apprenti")
    if st.session_state.xp >= 300 and "👑 Champion" not in st.session_state.badges:
        st.session_state.badges.append("👑 Champion")

# ==============================
# OUTILS
# ==============================
def image_to_base64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode()

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.title("🏆 Mon Score")
    st.metric("Total XP", f"{st.session_state.xp} pts")

    st.subheader("🏅 Mes Badges")
    if not st.session_state.badges:
        st.write("Encore aucun badge 🌱")
    for b in st.session_state.badges:
        st.success(b)

    st.divider()
    st.subheader("📜 Historique")
    if not st.session_state.historique:
        st.write("Aucun chapitre validé.")
    else:
        for item in st.session_state.historique:
            st.info(f"✅ {item['titre']}\n\n*{item['date']}*")

    st.divider()
    st.subheader("⚙️ Réglages")
    niveau = st.selectbox("Niveau", ["Primaire", "Collège", "Lycée"])
    mode_tdah = st.checkbox("Aide au Focus (TDAH)", value=True)
    mode_confiance = st.checkbox("Encouragement +", value=True)

# ==============================
# INTERFACE PRINCIPALE
# ==============================
st.title("🌟 Ton Assistant d'Étude")
st.write("Transforme tes photos de cours en un défi amusant !")

uploaded_files = st.file_uploader(
    "Prends tes photos de cours ici 📸",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    images = []
    for f in uploaded_files:
        img = Image.open(f)
        img.thumbnail((1024, 1024))
        images.append(img)

    st.image(images, width=120)

    st.session_state.chapitre_nom = st.text_input(
        "Comment s'appelle ce chapitre ?",
        st.session_state.chapitre_nom
    )

    if st.button("Lancer le défi ✨"):
        with st.spinner("Je lis ton cours avec attention..."):
            prompt = f"""
Tu es un coach bienveillant pour un enfant ({niveau}).
À partir des photos de cours, crée 3 questions courtes et ludiques.

RÈGLES IMPORTANTES :
- {"Utilise des phrases très courtes et des emojis." if mode_tdah else ""}
- {"Commence par valoriser le cours. En cas d'erreur, donne un indice doux." if mode_confiance else ""}
- Ne dis jamais que c'est faux brutalement
- Termine par les solutions
"""

            content = [{"type": "text", "text": prompt}]

            for img in images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_to_base64(img)}"
                    }
                })

            try:
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[{"role": "user", "content": content}],
                )

                st.session_state.dernier_quiz = response.choices[0].message.content
                ajouter_xp(20)
                st.rerun()

            except Exception:
                st.error(e)
                #st.error("Oups 😕 Il y a eu un petit souci. Réessaie tranquillement.")

# ==============================
# AFFICHAGE DU QUIZ
# ==============================
if st.session_state.dernier_quiz:
    st.markdown("---")
    st.markdown(st.session_state.dernier_quiz)

    if st.button("J'ai terminé le défi 🏁"):
        st.session_state.historique.append({
            "titre": st.session_state.chapitre_nom,
            "date": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        ajouter_xp(50)
        st.session_state.dernier_quiz = None
        st.balloons()
        st.success("Bravo 🌟 Tu peux être fière de toi ! +50 XP")
        st.rerun()

