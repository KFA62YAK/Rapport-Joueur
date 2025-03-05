import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
            excel_data = pd.ExcelFile(uploaded_file)
            required_sheets = {"CSV", "Vidéo", "Poste", "Constante"}
            missing_sheets = required_sheets - set(excel_data.sheet_names)
            if missing_sheets:
                st.error(f"Le fichier Excel doit contenir les feuilles suivantes : {', '.join(required_sheets)}. Feuilles manquantes : {', '.join(missing_sheets)}")
                return None, None, None, None
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

# Fonctions pour l'onglet GPS

def get_text_color_from_image(image_path):
    """Détermine si le texte doit être blanc ou noir en fonction de la luminosité du background."""
    with Image.open(image_path) as img:
        img = img.convert("L")
        brightness = sum(img.getdata()) / len(img.getdata())
        return "255,255,255" if brightness < 128 else "0,0,0"

def filter_duration(player_data, min_duration=3900):
    """Filtre les données des joueurs selon la durée minimale."""
    return player_data[player_data["Durée"] >= min_duration]

def add_data_table_to_pdf(pdf, data):
    """Ajoute un tableau des données utilisées à la dernière page du PDF."""
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, "Tableau des données utilisées", ln=True, align="C")
    pdf.ln(5)
    headers = list(data.columns)
    for header in headers:
        pdf.cell(40, 10, header, border=1, align="C")
    pdf.ln()
    for _, row in data.iterrows():
        for cell in row:
            pdf.cell(40, 10, str(cell), border=1, align="C")
        pdf.ln()

def generate_report_with_background(selected_graphs, player_name, constants, player_data, positions, module, background_image):
    """Génère un rapport PDF en mode paysage avec les graphiques sélectionnés et un arrière-plan personnalisé."""
    temp_pdf_path = None
    try:
        temp_pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{player_name}.pdf").name
        pdf = FPDF(orientation="L", unit="mm", format="A4")
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
            x_offsets = [10, 155]
            for i, graph in enumerate(graph_pair):
                if module == "Pôle Féminin":
                    fig = plot_feminine_graph(graph, player_name, constants, player_data, positions)
                else:
                    fig = plot_masculine_graph(graph, player_name, constants, player_data, positions)
                if fig:
                    fig.update_layout(xaxis_tickangle=45)
                    temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                    # Utilisation de write_image (nécessite l'installation de kaleido)
                    fig.write_image(temp_image, scale=2, width=800, height=600)
                    pdf.image(temp_image, x=x_offsets[i], y=60, w=135)
                    os.remove(temp_image)
        add_data_table_to_pdf(pdf, player_data)
        pdf.output(temp_pdf_path)
        return temp_pdf_path
    except Exception as e:
        st.error(f"Erreur lors de la génération du rapport PDF : {e}")
        return None

def display_selected_graphs(selected_graphs, player_name, constants, player_data, positions, module):
    """Affiche les graphiques sélectionnés de manière interactive en utilisant Plotly."""
    for graph in selected_graphs:
        st.subheader(f"Graphique : {graph}")
        if module == "Pôle Féminin":
            fig = plot_feminine_graph(graph, player_name, constants, player_data, positions)
        else:
            fig = plot_masculine_graph(graph, player_name, constants, player_data, positions)
        if fig:
            fig.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig)
        else:
            st.error(f"Graphique {graph} non disponible.")

# -------- Onglet principal --------

def main():
    data, video_data, positions, constante_data = load_excel()
    st.write("Le fichier Excel doit contenir les feuilles 'CSV', 'Vidéo', 'Poste', et 'Constante'.")
    if data is not None and video_data is not None and positions is not None and constante_data is not None:
        tab1, tab2 = st.tabs(["GPS", "Vidéo"])
        
        # Onglet GPS
        with tab1:
            col1, col2 = st.columns([0.5, 0.5])
            with col1:
                selected_player = st.selectbox("Sélectionner un joueur/joueuse", data["Joueur"].drop_duplicates().tolist())
            with col2:
                module = st.selectbox("Choisir le module d'analyse", ["Pôle Féminin", "Pôle Masculin"])
            background_file = st.file_uploader("Télécharger un fichier d'arrière-plan (PNG)", type=["png"])
            background_image = None
            if background_file is not None:
                background_image = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                with open(background_image, "wb") as f:
                    f.write(background_file.getvalue())
            if selected_player:
                st.write(f"Graphiques pour {selected_player} ({module}):")
                if module == "Pôle Féminin":
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
                    constants = get_feminine_constants(constante_data)
                else:
                    general_graphs = [
                        "Distance",
                        "Distance > 16km/h",
                        "Distance > 20km/h",
                        "TopSpeed",
                        "Nb Acc/Dec > 2m/s²",
                        "Nb Acc/Dec > 4m/s²",
                        "Diagramme empilé"
                    ]
                    per_min_graphs = [
                        "Dist/min",
                        "Distance>20kmh/min",
                        "Distance>16kmh/min",
                        "Nb Acc/Dec > 2m/s²/min",
                        "Nb Acc/Dec > 4m/s²/min"
                    ]
                    constants = get_masculine_constants(constante_data)
                    
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
                selected_graphs = selected_general_graphs + selected_per_min_graphs
                filter_matches = st.checkbox("Afficher les matchs < 3900 secondes", value=False)
                player_data = data[data["Joueur"] == selected_player]
                if not filter_matches:
                    player_data = filter_duration(player_data)
                if player_data.empty:
                    st.warning("Aucune donnée à afficher après le filtrage.")
                else:
                    if selected_graphs:
                        st.write("**Graphiques sélectionnés :**")
                        display_selected_graphs(selected_graphs, selected_player, constants, player_data, positions, module)
                    if st.button("Générer le rapport PDF"):
                        temp_pdf_path = generate_report_with_background(
                            selected_graphs, selected_player, constants, player_data, positions, module, background_image
                        )
                        if temp_pdf_path:
                            with open(temp_pdf_path, "rb") as pdf_file:
                                st.download_button("Télécharger le rapport PDF", data=pdf_file, file_name=f"rapport_{selected_player}.pdf")
                        if temp_pdf_path and os.path.exists(temp_pdf_path):
                            os.remove(temp_pdf_path)
                        if background_image and os.path.exists(background_image):
                            os.remove(background_image)
        
        # Onglet Vidéo
        with tab2:
            st.header("Vidéo")
            from scipy.ndimage import gaussian_filter  # si nécessaire
            col1, col2 = st.columns(2)
            with col1:
                player_name_video = st.selectbox("Sélectionnez un joueur", options=video_data["Joueur"].dropna().unique())
            with col2:
                session_name = st.selectbox("Sélectionnez une session", options=video_data["Session Title"].unique())
            if player_name_video and session_name:
                player_video_data = video_data[(video_data["Joueur"] == player_name_video) & (video_data["Session Title"] == session_name)]
                if player_video_data.empty:
                    st.warning("Aucune donnée disponible pour ce joueur et cette session.")
                else:
                    module_video = st.selectbox("Choisir le module d'analyse", options=["Carte de chaleur", "Analyse vidéo"])
                    if module_video == "Carte de chaleur":
                        try:
                            x_raw = player_video_data.iloc[0]["X"]
                            y_raw = player_video_data.iloc[0]["Y"]
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
                            if len(x_coords) != len(y_coords):
                                st.error(f"Les longueurs des coordonnées X ({len(x_coords)}) et Y ({len(y_coords)}) ne correspondent pas.")
                                x_coords, y_coords = [], []
                            heatmap = np.zeros((945, 612))
                            influence_radius = 1
                            sigma = influence_radius / (105 / 945)
                            for x, y in zip(x_coords, y_coords):
                                x_pixel = int((x / 105) * 945)
                                y_pixel = int((y / 68) * 612)
                                x_range = np.arange(945)
                                y_range = np.arange(612)
                                X, Y = np.meshgrid(x_range, y_range)
                                gauss = np.exp(-(((X - x_pixel) ** 2) + ((Y - y_pixel) ** 2)) / (2 * sigma**2))
                                heatmap += gauss.T
                            heatmap /= np.max(heatmap)
                            
                            # Création de la carte de chaleur avec Plotly
                            x_axis = np.linspace(0, 105, 945)
                            y_axis = np.linspace(0, 68, 612)
                            fig = go.Figure()
                            fig.add_trace(go.Heatmap(
                                z=heatmap.T,
                                x=x_axis,
                                y=y_axis,
                                colorscale="RdBu",
                                zmin=0.01,
                                opacity=0.8,
                                showscale=False
                            ))
                            
                            # Ajout des formes pour dessiner le terrain
                            shapes = []
                            # Limites du terrain
                            shapes.append(dict(type="line", x0=0, y0=0, x1=0, y1=68, line=dict(color="black", width=2)))
                            shapes.append(dict(type="line", x0=0, y0=68, x1=105, y1=68, line=dict(color="black", width=2)))
                            shapes.append(dict(type="line", x0=105, y0=68, x1=105, y1=0, line=dict(color="black", width=2)))
                            shapes.append(dict(type="line", x0=105, y0=0, x1=0, y1=0, line=dict(color="black", width=2)))
                            # Ligne médiane
                            shapes.append(dict(type="line", x0=52.5, y0=0, x1=52.5, y1=68, line=dict(color="black", width=2, dash="dash")))
                            # Surfaces de réparation
                            shapes.append(dict(type="line", x0=0, y0=20.15, x1=16.5, y1=20.15, line=dict(color="black", width=2)))
                            shapes.append(dict(type="line", x0=16.5, y0=20.15, x1=16.5, y1=47.85, line=dict(color="black", width=2)))
                            shapes.append(dict(type="line", x0=16.5, y0=47.85, x1=0, y1=47.85, line=dict(color="black", width=2)))
                            shapes.append(dict(type="line", x0=105, y0=20.15, x1=88.5, y1=20.15, line=dict(color="black", width=2)))
                            shapes.append(dict(type="line", x0=88.5, y0=20.15, x1=88.5, y1=47.85, line=dict(color="black", width=2)))
                            shapes.append(dict(type="line", x0=88.5, y0=47.85, x1=105, y1=47.85, line=dict(color="black", width=2)))
                            # Cercle central
                            shapes.append(dict(type="circle", xref="x", yref="y", x0=52.5-9.15, y0=34-9.15, x1=52.5+9.15, y1=34+9.15, line=dict(color="black", width=2)))
                            # Buts étendus
                            shapes.append(dict(type="line", x0=-4, y0=30.34, x1=-4, y1=37.66, line=dict(color="black", width=3)))
                            shapes.append(dict(type="line", x0=0, y0=30.34, x1=-4, y1=30.34, line=dict(color="black", width=3)))
                            shapes.append(dict(type="line", x0=0, y0=37.66, x1=-4, y1=37.66, line=dict(color="black", width=3)))
                            shapes.append(dict(type="line", x0=105, y0=30.34, x1=109, y1=30.34, line=dict(color="black", width=3)))
                            shapes.append(dict(type="line", x0=109, y0=30.34, x1=109, y1=37.66, line=dict(color="black", width=3)))
                            shapes.append(dict(type="line", x0=105, y0=37.66, x1=109, y1=37.66, line=dict(color="black", width=3)))
                            
                            fig.update_layout(
                                shapes=shapes,
                                xaxis=dict(range=[-6, 111], showgrid=False, zeroline=False, visible=False),
                                yaxis=dict(range=[-5, 73], showgrid=False, zeroline=False, visible=False),
                                margin=dict(l=0, r=0, t=0, b=0)
                            )
                            st.plotly_chart(fig)
                        except Exception as e:
                            st.error(f"Erreur lors de la génération de la carte de chaleur : {e}")
                    if module_video == "Analyse vidéo":
                        try:
                            if video_data is None or positions is None or constante_data is None:
                                st.error("Les données vidéo, postes ou constantes ne sont pas disponibles. Veuillez charger un fichier Excel valide.")
                            else:
                                joueur = st.selectbox("Sélectionnez un joueur", video_data["Joueur"].dropna().unique())
                                donnees_filtrees = video_data[video_data["Joueur"] == joueur]
                                if donnees_filtrees.empty:
                                    st.warning(f"Aucune donnée disponible pour le joueur sélectionné : {joueur}.")
                                else:
                                    poste_joueur = positions[positions["Joueur"] == joueur]["Poste"].iloc[0] if not positions.empty else "Poste inconnu"
                                    constante_value = None
                                    if poste_joueur in constante_data.columns:
                                        constante_row = constante_data[constante_data.iloc[:, 0] == "Ballons touchés"]
                                        if not constante_row.empty:
                                            constante_value = constante_row[poste_joueur].values[0]
                                    sessions = donnees_filtrees["Session Title"].tolist()
                                    ballons_touches = donnees_filtrees["Ballons touchés"].tolist()
                                    st.subheader(f"Évolution des ballons touchés pour {joueur}")
                                    fig = px.line(x=sessions, y=ballons_touches, markers=True, 
                                                  labels={"x": "Session Title", "y": "Ballons touchés"},
                                                  title=f"Ballons touchés - {joueur}")
                                    if constante_value is not None:
                                        fig.add_hline(y=constante_value, line_dash="dash", line_color="red", 
                                                      annotation_text=f"Constante ({poste_joueur})", annotation_position="bottom right")
                                    st.plotly_chart(fig)
                        except Exception as e:
                            st.error(f"Erreur lors de la génération du graphique : {e}")
    else:
        st.warning("Veuillez charger un fichier Excel pour continuer.")

if __name__ == "__main__":
    main()
