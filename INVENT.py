import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PFtest import plot_feminine_graph, get_feminine_constants
from PMtest import plot_masculine_graph, get_masculine_constants
import os
from fpdf import FPDF
import tempfile
from PIL import Image

st.markdown(
    """
    <style>
    /* Centrer les onglets */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
    }

    /* Agrandir le texte des onglets */
    .stTabs [data-baseweb="tab"] {
        font-size: 20px !important;
        font-weight: bold !important;
        padding: 35px 100px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def load_excel(key="file_uploader_excel"):
    """Charge les données depuis un fichier Excel."""
    uploaded_file = st.file_uploader("Charger un fichier Excel", type=["xls", "xlsx", "xlsm"], key="file_uploader_excel")
    if uploaded_file is not None:
        try:
            # Charger le fichier Excel
            excel_data = pd.ExcelFile(uploaded_file)

            # Vérifier la présence des feuilles requises
            required_sheets = {"CSV", "Vidéo", "Poste", "Constante"}
            missing_sheets = required_sheets - set(excel_data.sheet_names)
            if missing_sheets:
                st.error(f"Le fichier Excel doit contenir les feuilles suivantes : {', '.join(required_sheets)}. "
                         f"Feuilles manquantes : {', '.join(missing_sheets)}")
                return None, None, None, None

            # Lire les données des feuilles
            data = excel_data.parse("CSV")
            video_data = excel_data.parse("Vidéo")
            positions = excel_data.parse("Poste")
            constante_data = excel_data.parse("Constante")

            return data, video_data, positions, constante_data

        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
    else:
        st.info("Veuillez charger un fichier Excel pour continuer.")
    return None, None, None, None

# Appel de la fonction principale dans le script
st.write("Le fichier Excel doit contenir les feuilles 'CSV', 'Vidéo', 'Poste', et 'Constante'.")
data, video_data, positions, constante_data = load_excel()

if data is not None and video_data is not None and positions is not None and constante_data is not None:
    # Ajouter des onglets pour naviguer entre les données
    tab1, tab2 = st.tabs(["GPS", "Vidéo"])

    with tab1:

        def get_text_color_from_image(image_path):
            """Détermine si le texte doit être blanc ou noir en fonction de la luminosité du background."""
            with Image.open(image_path) as img:
                img = img.convert("L")  # Convertir en niveaux de gris
                brightness = sum(img.getdata()) / len(img.getdata())  # Luminosité moyenne
                return "255,255,255" if brightness < 128 else "0,0,0"  # Blanc si sombre, sinon noir

        def filter_duration(player_data, min_duration=3900):
            """Filtre les données des joueurs selon la durée minimale."""
            return player_data[player_data["Durée"] >= min_duration]

        def add_data_table_to_pdf(pdf, data):
            """Ajoute un tableau des données utilisées à la dernière page du PDF."""
            pdf.add_page()
            pdf.set_font("Arial", size=10)

            # Ajouter un titre pour la table
            pdf.cell(0, 10, "Tableau des données utilisées", ln=True, align="C")
            pdf.ln(5)

            # Ajouter les en-têtes des colonnes
            headers = list(data.columns)
            for header in headers:
                pdf.cell(40, 10, header, border=1, align="C")
            pdf.ln()

            # Ajouter les lignes des données
            for _, row in data.iterrows():
                for cell in row:
                    pdf.cell(40, 10, str(cell), border=1, align="C")
                pdf.ln()

        def generate_report_with_background(selected_graphs, player_name, constants, player_data, positions, module, background_image):
            """Génère un rapport PDF en mode paysage avec les graphiques sélectionnés et un arrière-plan personnalisé."""
            temp_pdf_path = None  # Initialisation
            try:
                temp_pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{player_name}.pdf").name
                pdf = FPDF(orientation="L", unit="mm", format="A4")

                # Première page avec le titre et le sommaire
                pdf.add_page()
                if background_image:
                    pdf.image(background_image, x=0, y=0, w=297, h=210)
                    text_color = get_text_color_from_image(background_image)
                else:
                    text_color = "0,0,0"

                r, g, b = map(int, text_color.split(","))
                pdf.set_text_color(r, g, b)

                pdf.set_font("Arial", style="B", size=20)
                pdf.cell(0, 20, "Rapport de Performance en match", align="C", ln=True)
                pdf.set_font("Arial", size=16)
                position_row = positions[positions["Joueur"] == player_name]
                player_position = position_row.iloc[0]["Poste"] if not position_row.empty else "Non spécifié"
                pdf.cell(0, 10, f"{player_name} ({player_position})", align="C", ln=True)
                pdf.ln(5)

                # Ajouter le sommaire
                pdf.set_font("Arial", style="B", size=14)
                pdf.set_y(65)
                pdf.cell(0, 10, "Sommaire :", align="C", ln=True)
                pdf.set_font("Arial", size=12)
                for idx, graph in enumerate(selected_graphs, start=1):
                    pdf.cell(0, 8, f"{idx}. {graph}", align="C", ln=True)
                pdf.ln(10)

                graph_pairs = [selected_graphs[i:i+2] for i in range(0, len(selected_graphs), 2)]

                for graph_pair in graph_pairs:
                    pdf.add_page()
                    if background_image:
                        pdf.image(background_image, x=0, y=0, w=297, h=210)

                    # Générer les graphiques
                    x_offsets = [10, 155]  # Positions horizontales pour deux graphiques
                    for i, graph in enumerate(graph_pair):
                        if module == "Pôle Féminin":
                            fig = plot_feminine_graph(graph, player_name, constants, player_data, positions)
                        else:
                            fig = plot_masculine_graph(graph, player_name, constants, player_data, positions)

                        if fig:
                            temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                            fig.autofmt_xdate ()
                            fig.savefig(temp_image, bbox_inches="tight")
                            pdf.image(temp_image, x=x_offsets[i], y=60, w=135)  # Ajusté pour deux graphiques
                            os.remove(temp_image)

                pdf.output(temp_pdf_path)
                return temp_pdf_path
            except Exception as e:
                st.error(f"Erreur lors de la génération du rapport PDF : {e}")
                return None

        def display_selected_graphs(selected_graphs, player_name, constants, player_data, positions, module):
            """Affiche les graphiques sélectionnés de manière interactive."""
            for graph in selected_graphs:
                st.subheader(f"Graphique : {graph}")
                if module == "Pôle Féminin":
                    fig = plot_feminine_graph(graph, player_name, constants, player_data, positions)
                else:
                    fig = plot_masculine_graph(graph, player_name, constants, player_data, positions)

                if fig:
                    fig.autofmt_xdate ()
                    st.pyplot(fig)
                else:
                    st.error(f"Graphique {graph} non disponible.")

        def main():

            # Vérifier que les données sont chargées
            if data is not None:
                players = data["Joueur"].drop_duplicates().tolist()
                
                col1, col2 = st.columns([0.5, 0.5])
                with col1:
                    selected_player = st.selectbox("Sélectionner un joueur/joueuse", players)
                with col2:
                # Menu déroulant pour choisir le module
                    module = st.selectbox("Choisir le module d'analyse", ["Pôle Féminin", "Pôle Masculin"])



                # Télécharger un arrière-plan
                background_file = st.file_uploader("Télécharger un fichier d'arrière-plan (PNG)", type=["png"])
                background_image = None
                if background_file is not None:
                    background_image = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                    with open(background_image, "wb") as f:
                        f.write(background_file.getvalue())

                # Déterminer les constantes et les listes de graphiques appropriées
                if module == "Pôle Féminin":
                    constants = get_feminine_constants(constante_data)
                    general_graphs = [
                        "Distance",
                        "Distance>19km/h",
                        "Distance > 23km/h",
                        "TopSpeed",
                        "Accélérations > 2m/s²",
                        "Décélérations > 2m/s²",
                        "Diagramme empilé"
                    ]
                    per_min_graphs = [
                        "Dist/min",
                        "Distance>23kmh/min",
                        "Distance > 19kmh/min",
                        "Nb Accélération > 2m/s²/min",
                        "Nb Décélération > 2m/s²/min"
                    ]
                else:
                    constants = get_masculine_constants(constante_data)
                    general_graphs = [
                        "Distance",
                        "Distance > 16km/h",
                        "Distance > 20km/h",
                        "TopSpeed",
                        "Nb Acc/Dec > 2m/s²",
                        "Nb Acc/Dec > 4m/s²",
                        "Diagramme empilé"
                    ]

                    # Graphiques par minute
                    per_min_graphs = [
                        "Dist/min",
                        "Distance>20kmh/min",
                        "Distance>16kmh/min",
                        "Nb Acc/Dec > 2m/s²/min",
                        "Nb Acc/Dec > 4m/s²/min"
                    ]

                if selected_player:
                    st.write(f"Graphiques pour {selected_player} ({module}):")
                    col1, col2 = st.columns([0.5, 0.5])
                    with col1:
                        select_all_general = st.checkbox("Sélectionner tous les graphiques généraux")
                        selected_general_graphs = st.multiselect(
                            "Choisir les graphiques généraux", 
                            general_graphs, 
                            default=general_graphs if select_all_general else []
                        )
                    with col2:
                        select_all_per_min = st.checkbox("Sélectionner tous les graphiques par minute")
                        selected_per_min_graphs = st.multiselect(
                            "Choisir les graphiques par minute", 
                            per_min_graphs, 
                            default=per_min_graphs if select_all_per_min else []
                        )   

                    # Combiner les graphiques sélectionnés
                    selected_graphs = selected_general_graphs + selected_per_min_graphs

                    # Filtrer les données pour les matchs inférieurs à 3900 secondes
                    filter_matches = st.checkbox("Afficher les matchs < 3900 secondes", value=False)
                    player_data = data[data["Joueur"] == selected_player]
                    if not filter_matches:
                        player_data = filter_duration(player_data)

                    if player_data.empty:
                        st.warning("Aucune donnée à afficher après le filtrage.")
                    else:
                        # Afficher les graphiques interactifs
                        if selected_graphs:
                            st.write("**Graphiques sélectionnés :**")
                            display_selected_graphs(selected_graphs, selected_player, constants, player_data, positions, module)

                        # Ajouter un bouton pour générer un PDF
                        if st.button("Générer le rapport PDF"):
                            try:
                                temp_pdf_path = generate_report_with_background(
                                    selected_graphs, selected_player, constants, player_data, positions, module, background_image
                                )
                                if temp_pdf_path:
                                    with open(temp_pdf_path, "rb") as pdf_file:
                                        st.download_button("Télécharger le rapport PDF", data=pdf_file, file_name=f"rapport_{selected_player}.pdf")
                            finally:
                                if temp_pdf_path and os.path.exists(temp_pdf_path):
                                    os.remove(temp_pdf_path)
                                if background_image and os.path.exists(background_image):
                                    os.remove(background_image)
                else:
                    st.warning("Veuillez sélectionner un joueur avant de continuer.")
            else:
                st.warning("Veuillez charger un fichier Excel avant de continuer.")

        if __name__ == "__main__":
            main()


    with tab2:
        st.header("Vidéo")
        from scipy.ndimage import gaussian_filter

        # Créer des colonnes pour aligner les selectbox côte à côte
        col1, col2 = st.columns(2)

        # Placer les selectbox dans les colonnes
        with col1:
            player_name = st.selectbox(
                "Sélectionnez un joueur", 
                options=video_data["Joueur"].unique()
            )
        with col2:
            session_name = st.selectbox(
                "Sélectionnez une session", 
                options=video_data["Session Title"].unique()
            )

        if player_name and session_name:
            # Filtrer les données pour le joueur et la session sélectionnés
            player_data = video_data[(video_data["Joueur"] == player_name) & (video_data["Session Title"] == session_name)]

            if player_data.empty:
                st.warning("Aucune donnée disponible pour ce joueur et cette session.")
            else:
                # Menu déroulant pour choisir le module
                module = st.selectbox(
                    "Choisir le module d'analyse", 
                    options=["Carte de chaleur", "Analyse vidéo"]
                )

                if module == "Carte de chaleur":
                    try:
                        # Parser les colonnes X et Y
                        x_raw = player_data.iloc[0]["X"]
                        y_raw = player_data.iloc[0]["Y"]

                        if isinstance(x_raw, str):
                            x_coords = list(map(float, x_raw.split(";")))
                        elif isinstance(x_raw, (list, np.ndarray)):
                            x_coords = list(map(float, x_raw))
                        else:
                            x_coords = [float(x_raw)]

                        if isinstance(y_raw, str):
                            y_coords = list(map(float, y_raw.split(";")))
                        elif isinstance(y_raw, (list, np.ndarray)):
                            y_coords = list(map(float, y_raw))
                        else:
                            y_coords = [float(y_raw)]

                        # Vérifier si les longueurs correspondent
                        if len(x_coords) != len(y_coords):
                            st.error(
                                f"Les longueurs des coordonnées X ({len(x_coords)}) "
                                f"et Y ({len(y_coords)}) ne correspondent pas."
                            )
                            x_coords, y_coords = [], []

                        # Créer une carte de chaleur initiale vide
                        heatmap = np.zeros((945, 612))

                        # Taille de la zone d'influence
                        influence_radius = 1  # En mètres
                        sigma = influence_radius / (105 / 945)  # Convertir en pixels

                        # Ajouter l'influence de chaque point
                        for x, y in zip(x_coords, y_coords):
                            x_pixel = int((x / 105) * 945)  # Conversion des mètres en pixels
                            y_pixel = int((y / 68) * 612)  # Conversion des mètres en pixels

                            # Créer une matrice gaussienne centrée sur le point
                            x_range = np.arange(945)
                            y_range = np.arange(612)
                            X, Y = np.meshgrid(x_range, y_range)
                            gauss = np.exp(
                                -(((X - x_pixel) ** 2) + ((Y - y_pixel) ** 2)) / (2 * sigma**2)
                            )

                            # Ajouter cette influence au heatmap
                            heatmap += gauss.T

                        # Normaliser le heatmap
                        heatmap /= np.max(heatmap)

                        # Dessiner le terrain de football avec la carte de chaleur
                        fig, ax = plt.subplots(figsize=(12, 8))
                        ax.set_xlim(-6, 111)  # Longueur en mètres (plus d'espace pour les buts)
                        ax.set_ylim(-5, 73)  # Largeur en mètres (inclut un peu autour)

                        # Dimensions des buts
                        goal_width = 7.32  # Largeur des buts en mètres
                        goal_height_start = (68 - goal_width) / 2
                        goal_height_end = goal_height_start + goal_width

                        # Dessin des limites du terrain
                        ax.plot([0, 0, 105, 105, 0], [0, 68, 68, 0, 0], color="black", linewidth=2)

                        # Ligne médiane
                        ax.plot([52.5, 52.5], [0, 68], color="black", linewidth=2, linestyle="--")

                        # Surface de réparation (côtés gauche et droit)
                        ax.plot([0, 16.5, 16.5, 0], [20.15, 20.15, 47.85, 47.85], color="black", linewidth=2)
                        ax.plot([105, 88.5, 88.5, 105], [20.15, 20.15, 47.85, 47.85], color="black", linewidth=2)

                        # Point central et cercle central
                        ax.scatter(52.5, 34, color="black", s=50)
                        circle = plt.Circle((52.5, 34), 9.15, color="black", fill=False, linewidth=2)
                        ax.add_artist(circle)

                        # Dessiner les buts étendus derrière la ligne de terrain
                        ax.plot([-4, -4], [30.34, 37.66], color="black", linewidth=3)
                        ax.plot([0, -4], [30.34, 30.34], color="black", linewidth=3)
                        ax.plot([0, -4], [37.66, 37.66], color="black", linewidth=3)

                        ax.plot([105, 109], [30.34, 30.34], color="black", linewidth=3)
                        ax.plot([109, 109], [30.34, 37.66], color="black", linewidth=3)
                        ax.plot([105, 109], [37.66, 37.66], color="black", linewidth=3)

                        # Afficher la carte de chaleur avec des zones blanches pour l'absence d'activité
                        extent = [0, 105, 0, 68]
                        cmap = plt.cm.get_cmap("coolwarm")
                        cmap.set_under(color="white")  # Définit le blanc pour les zones sans activité
                        ax.imshow(heatmap.T, extent=extent, origin="lower", cmap=cmap, alpha=0.8, vmin=0.01)

                        # Retirer les axes
                        ax.axis("off")

                        st.pyplot(fig)
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du graphique : {e}")
                        
                if module == "Analyse vidéo":

                    try:
                        # Vérifier si les données vidéo, postes et constantes sont disponibles
                        if video_data is None or positions is None or constante_data is None:
                            st.error("Les données vidéo, postes ou constantes ne sont pas disponibles. Veuillez charger un fichier Excel valide.")
                        else:
                            # Sélectionner le joueur
                            joueur = st.selectbox("Sélectionnez un joueur", video_data["Joueur"].dropna().unique())

                            # Filtrer les données pour le joueur sélectionné
                            donnees_filtrees = video_data[video_data["Joueur"] == joueur]

                            if donnees_filtrees.empty:
                                st.warning(f"Aucune donnée disponible pour le joueur sélectionné : {joueur}.")
                            else:
                                # Récupérer le poste du joueur
                                poste_joueur = positions[positions["Joueur"] == joueur]["Poste"].iloc[0] if not positions.empty else "Poste inconnu"

                                # Récupérer la constante pour le poste et 'Ballons touchés'
                                constante_value = None
                                if poste_joueur in constante_data.columns:
                                    constante_row = constante_data[constante_data.iloc[:, 0] == "Ballons touchés"]
                                    if not constante_row.empty:
                                        constante_value = constante_row[poste_joueur].values[0]

                                # Préparer les données pour le graphique
                                sessions = donnees_filtrees["Session Title"].tolist()
                                ballons_touches = donnees_filtrees["Ballons touchés"].tolist()

                                # Tracer le graphique
                                st.subheader(f"Évolution des ballons touchés pour {joueur}")
                                fig, ax = plt.subplots(figsize=(10, 6))

                                # Graphique scatter relié
                                ax.plot(sessions, ballons_touches, marker="o", linestyle="-", color="blue", label="Ballons touchés")

                                # Ajouter une ligne constante si disponible
                                if constante_value is not None:
                                    ax.axhline(y=constante_value, color="red", linestyle="--", label=f"Constante ({poste_joueur})")

                                # Personnalisation du graphique
                                ax.set_title(f"Ballons touchés - {joueur}", fontsize=16)
                                ax.set_xlabel("Session Title", fontsize=12)
                                ax.set_ylabel("Ballons touchés", fontsize=12)
                                ax.tick_params(axis='x', rotation=45)
                                ax.grid(True, linestyle="--", alpha=0.7)
                                ax.legend()

                                # Afficher le graphique
                                st.pyplot(fig)
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du graphique : {e}")
        
