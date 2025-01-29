import streamlit as st
import time
import os


def main():
    st.set_page_config(page_title="Pôle Liévin", page_icon="⚽", layout="wide")
    st.markdown(
        """
        <style>
        /* Agrandir les boutons */
        .stButton>button {
            font-size: 50px !important;  /* Taille du texte */
            font-weight: bold !important; /* Texte en gras */
            padding: 40px !important;  /* Espace interne du bouton */
            }
        </style>
        """,
        unsafe_allow_html=True
        )
    
    # Session state for animations
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    
    if st.session_state.page == "home":
        show_home()
    elif st.session_state.page == "analyse":
        show_analyse()
    elif st.session_state.page == "comparaison":
        show_comparaison()
        
def show_home():
    st.markdown("""<h1 style='text-align: center;'>⚽ Pôle Liévin</h1>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("📈 Analyse GPS/Vidéo", use_container_width=True):
            st.session_state.page = "analyse"
            st.rerun()
    with col2:
        if st.button("🪪 Comparaison joueur", use_container_width=True):
            st.session_state.page = "comparaison"
            st.rerun()
    
def show_analyse():
    st.markdown("""<h1 style='text-align: center;'>📈 Analyse GPS/Vidéo</h1>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        if st.button("🪪 Comparaison joueur", use_container_width=True):
            st.session_state.page = "comparaison"
            st.rerun()
    
    with col2:
        time.sleep(1)  # Simule un chargement
        
    
    # Chemin du fichier à exécuter
        script_path = os.path.join(os.path.dirname(__file__), "INVENT.py")

            # Vérification si le fichier existe
        if os.path.exists(script_path):

            try:
                # Lire le contenu du fichier avec un encodage explicite
                with open(script_path, "r", encoding="utf-8") as file:
                    code = file.read()

                # Exécuter le fichier dans le contexte Streamlit
                exec(code, globals())
            except UnicodeDecodeError as e:
                st.error(f"Erreur d'encodage : {e}. Essayez un autre encodage, comme 'latin-1'.")
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du script : {e}")
        else:
            st.error(f"Le fichier spécifié n'existe pas : {script_path}")
    
def show_comparaison():
    st.markdown("""<h1 style='text-align: center;'>🪪 Comparaison Joueur</h1>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        if st.button("📈 Analyse GPS/Vidéo", use_container_width=True):
            st.session_state.page = "analyse"
            st.rerun()
    
    with col2:

    # Chemin du fichier à exécuter
        script_path = os.path.join(os.path.dirname(__file__), "essaiCompa.py")


            # Vérification si le fichier existe
        if os.path.exists(script_path):

            try:
                # Lire le contenu du fichier avec un encodage explicite
                with open(script_path, "r", encoding="utf-8") as file:
                    code = file.read()

                # Exécuter le fichier dans le contexte Streamlit
                exec(code, globals())
            except UnicodeDecodeError as e:
                st.error(f"Erreur d'encodage : {e}. Essayez un autre encodage, comme 'latin-1'.")
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du script : {e}")
        else:
            st.error(f"Le fichier spécifié n'existe pas : {script_path}")
if __name__ == "__main__":
    main()
