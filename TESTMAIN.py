import streamlit as st
import pandas as pd
from PFtest import plot_feminine_graph, get_feminine_constants
from PMtest import plot_masculine_graph, get_masculine_constants
import matplotlib.pyplot as plt
import tempfile
import os
from fpdf import FPDF
from PIL import Image
os.system("streamlit run TESTMAIN.py")


def get_text_color_from_image(image_path):
    """Détermine si le texte doit être blanc ou noir en fonction de la luminosité du background."""
    with Image.open(image_path) as img:
        img = img.convert("L")  # Convertir en niveaux de gris
        brightness = sum(img.getdata()) / len(img.getdata())  # Luminosité moyenne
        return "255,255,255" if brightness < 128 else "0,0,0"  # Blanc si sombre, sinon noir

def load_excel():
    """Charge les données depuis un fichier Excel."""
    uploaded_file = st.file_uploader("Charger un fichier Excel", type=["xls", "xlsx", "xlsm"])
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            if "CSV" not in excel_data.sheet_names or "Poste" not in excel_data.sheet_names or "Constante" not in excel_data.sheet_names:
                st.error("Le fichier Excel doit contenir les feuilles 'CSV', 'Poste' et 'Constante'.")
                return None, None, None

            data = excel_data.parse("CSV")
            positions = excel_data.parse("Poste")
            constante_data = excel_data.parse("Constante")

            st.success("Fichier chargé avec succès")
            st.write("Aperçu des données chargées:")
            st.write(data.head())
            return data, positions, constante_data
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
    else:
        st.warning("Veuillez charger un fichier Excel.")
    return None, None, None

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
                    fig.savefig(temp_image, bbox_inches="tight")
                    pdf.image(temp_image, x=x_offsets[i], y=60, w=135)  # Ajusté pour deux graphiques
                    os.remove(temp_image)

        # Ajouter le tableau des données utilisées
        add_data_table_to_pdf(pdf, player_data)

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
            st.pyplot(fig)
        else:
            st.error(f"Graphique {graph} non disponible.")

def main():
    st.title("Editeur de rapport")

    # Charger les données
    data, positions, constante_data = load_excel()

    # Vérifier que les données sont chargées
    if data is not None:
        st.write("Données disponibles. Sélectionner un joueur:")
        players = data["Joueur"].drop_duplicates().tolist()
        selected_player = st.selectbox("Sélectionner un joueur/joueuse", players)

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
                "Diagramme empilé",
                "Tableau des données"
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

            # Cases à cocher pour sélectionner tous les graphiques
            select_all_general = st.checkbox("Sélectionner tous les graphiques généraux")
            select_all_per_min = st.checkbox("Sélectionner tous les graphiques par minute")

            # Menus pour sélectionner les graphiques généraux et par minute
            selected_general_graphs = st.multiselect(
                "Choisir les graphiques généraux", 
                general_graphs, 
                default=general_graphs if select_all_general else []
            )
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
