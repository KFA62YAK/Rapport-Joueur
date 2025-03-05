import streamlit as st
import time
import os


def main():
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    
    if st.session_state.page == "home":
        show_home()
    elif st.session_state.page == "analyse":
        show_analyse()
    elif st.session_state.page == "comparaison":
        show_comparaison()
    elif st.session_state.page == "HRR":
        show_HRR()

def show_home():
    st.markdown("<h1>⚽ Pôle Liévin</h1>", unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        .stButton>button {
            font-size: 50px !important;
            font-weight: bold !important;
            padding: 40px !important;
            width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📈 Analyse GPS/Vidéo", use_container_width=True):
            st.session_state.page = "analyse"
            st.rerun()
        elif st.button("🫀 Analyse FC", use_container_width=True):
            st.session_state.page = "HRR"
            st.rerun()
    with col2:
        if st.button("🪪 Comparaison joueur", use_container_width=True):
            st.session_state.page = "comparaison"
            st.rerun()

def show_HRR():
    st.markdown("<h1>🫀 Analyse FC</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        if st.button("🪪 Comparaison joueur", use_container_width=True):
            st.session_state.page = "comparaison"
            st.rerun()
        if st.button("📈 Analyse GPS/Vidéo", use_container_width=True):
            st.session_state.page = "analyse"
            st.rerun()
    with col2:
        time.sleep(1)
        script_path = os.path.join(os.path.dirname(__file__), "ANALYSE.py")
        if os.path.exists(script_path):
            try:
                with open(script_path, "r", encoding="utf-8") as file:
                    code = file.read()
                exec(code, globals())
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du script : {e}")
        else:
            st.error(f"Le fichier spécifié n'existe pas : {script_path}")
                
def show_analyse():
    st.markdown("<h1>📈 Analyse GPS/Vidéo</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        if st.button("🪪 Comparaison joueur", use_container_width=True):
            st.session_state.page = "comparaison"
            st.rerun()
        if st.button("🫀 Analyse FC", use_container_width=True):
            st.session_state.page = "HRR"
            st.rerun()
    with col2:
        time.sleep(1)
        script_path = os.path.join(os.path.dirname(__file__), "INVENT.py")
        if os.path.exists(script_path):
            try:
                with open(script_path, "r", encoding="utf-8") as file:
                    code = file.read()
                exec(code, globals())
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du script : {e}")
        else:
            st.error(f"Le fichier spécifié n'existe pas : {script_path}")
    
def show_comparaison():
    st.markdown("<h1>🪪 Comparaison Joueur</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        if st.button("📈 Analyse GPS/Vidéo", use_container_width=True):
            st.session_state.page = "analyse"
            st.rerun()
        if st.button("🫀 Analyse FC", use_container_width=True):
            st.session_state.page = "HRR"
            st.rerun()
    with col2:
        script_path = os.path.join(os.path.dirname(__file__), "essaiCompa.py")
        if os.path.exists(script_path):
            try:
                with open(script_path, "r", encoding="utf-8") as file:
                    code = file.read()
                exec(code, globals())
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du script : {e}")
        else:
            st.error(f"Le fichier spécifié n'existe pas : {script_path}")

if __name__ == "__main__":
    main()
