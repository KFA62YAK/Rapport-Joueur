import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from fpdf import FPDF
import tempfile
from PIL import Image, ImageFile
import base64
import io
import zipfile

# Permettre à PIL de charger des images tronquées
ImageFile.LOAD_TRUNCATED_IMAGES = True

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

def load_folder():
    """
    Charge un dossier compressé (ZIP) contenant :
      - Un fichier Excel (avec les feuilles 'CSV', 'Vidéo', 'Poste', 'Constante')
      - Un dossier "Trombi" avec les images des joueurs.
    Le dossier est extrait dans un répertoire temporaire persistant et le chemin
    de ce répertoire (base_folder) est renvoyé.
    """
    uploaded_zip = st.file_uploader("Charger un dossier compressé (ZIP) contenant l'Excel et le dossier Trombi", type=["zip"])
    if uploaded_zip is not None:
        try:
            base_folder = tempfile.mkdtemp()
            zip_path = os.path.join(base_folder, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getvalue())
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(base_folder)
            excel_file_path = None
            for root, dirs, files in os.walk(base_folder):
                for file in files:
                    if file.lower().endswith((".xls", ".xlsx", ".xlsm")):
                        excel_file_path = os.path.join(root, file)
                        break
                if excel_file_path:
                    break
            if excel_file_path is None:
                st.error("Aucun fichier Excel trouvé dans le dossier compressé.")
                return None, None, None, None, None
            excel_data = pd.ExcelFile(excel_file_path)
            required_sheets = {"CSV", "Vidéo", "Poste", "Constante"}
            missing_sheets = required_sheets - set(excel_data.sheet_names)
            if missing_sheets:
                st.error(
                    f"Le fichier Excel doit contenir les feuilles suivantes : {', '.join(required_sheets)}. "
                    f"Feuilles manquantes : {', '.join(missing_sheets)}"
                )
                return None, None, None, None, None
            data = excel_data.parse("CSV")
            video_data = excel_data.parse("Vidéo")
            positions = excel_data.parse("Poste")
            constante_data = excel_data.parse("Constante")
            return data, video_data, positions, constante_data, base_folder
        except Exception as e:
            st.error(f"Erreur lors du chargement du dossier : {e}")
            return None, None, None, None, None
    else:
        st.info("Veuillez charger un dossier compressé (ZIP) pour continuer.")
    return None, None, None, None, None

def get_text_color_from_image(image_path):
    """Détermine si le texte doit être blanc ou noir en fonction de la luminosité de l'image d'arrière-plan."""
    with Image.open(image_path) as img:
        img = img.convert("L")
        brightness = sum(img.getdata()) / len(img.getdata())
        return "255,255,255" if brightness < 128 else "0,0,0"

def get_dominant_color_from_region(bg_image_path, x_mm, y_mm, w_mm, h_mm, page_width_mm=297, page_height_mm=210):
    """
    Extrait la couleur dominante de la zone de l'image d'arrière-plan correspondant à
    la zone définie par (x_mm, y_mm, w_mm, h_mm) en mm, en supposant que l'image est
    étirée sur une page de dimensions page_width_mm x page_height_mm.
    La couleur est retournée sous la forme (R, G, B, 255).
    """
    from PIL import Image
    with Image.open(bg_image_path) as img:
        bg_width, bg_height = img.size
        left = int((x_mm / page_width_mm) * bg_width)
        top = int((y_mm / page_height_mm) * bg_height)
        region_width = int((w_mm / page_width_mm) * bg_width)
        region_height = int((h_mm / page_height_mm) * bg_height)
        region = img.crop((left, top, left + region_width, top + region_height)).convert("RGB")
        small_region = region.resize((50, 50))
        colors = small_region.getcolors(50 * 50)
        if colors:
            dominant_color = max(colors, key=lambda item: item[0])[1]
            return (dominant_color[0], dominant_color[1], dominant_color[2], 255)
    return (255, 255, 255, 255)

def get_player_portrait(player_name, positions, base_folder, target_width_mm):
    """
    Ouvre l'image du joueur, la redimensionne pour que sa largeur soit target_width_mm,
    et retourne l'image redimensionnée ainsi que sa hauteur en mm.
    """
    import os
    from PIL import Image
    trombi_folder = os.path.join(base_folder, "Trombi")
    positions["Joueur_norm"] = positions["Joueur"].astype(str).str.strip().str.lower()
    selected_norm = str(player_name).strip().lower()
    player_row = positions[positions["Joueur_norm"] == selected_norm]
    if player_row.empty:
        return None, None
    file_name = player_row.iloc[0]["Trombi"]
    if not file_name:
        return None, None
    photo_path = os.path.join(trombi_folder, file_name)
    if not os.path.exists(photo_path):
        return None, None
    with Image.open(photo_path) as img:
        img = img.convert("RGBA")
        # Calculer la largeur en pixels correspondant à target_width_mm (en supposant 96 DPI)
        target_width_px = int(target_width_mm * (96 / 25.4))
        # Calculer le facteur de redimensionnement
        factor = target_width_px / img.width
        new_width = target_width_px
        new_height = int(img.height * factor)
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        # Convertir la hauteur en mm
        new_height_mm = new_height * 25.4 / 96
        return img_resized, new_height_mm

def generate_report_with_background(selected_graphs, player_name, constants, player_data, positions, module, background_image, base_folder):
    """
    Génère un rapport PDF en mode paysage avec :
      - Un arrière-plan personnalisé (si fourni)
      - Le titre et les infos du joueur
      - Un sommaire des graphiques
      - Le portrait du joueur inséré à un emplacement précis,
        aligné par le bas.
    
    Le portrait est redimensionné à la largeur target_width_mm, et son bord inférieur
    est aligné à bottom_y_mm (les valeurs sont modifiables).
    """
    from PFtest import plot_feminine_graph
    from PMtest import plot_masculine_graph
    from io import BytesIO
    import base64, tempfile, os
    from fpdf import FPDF

    # Paramètres pour le portrait
    target_width_mm = 60      # Largeur souhaitée pour le portrait (modifiable)
    bottom_y_mm = 65          # Coordonnée y (en mm) où doit se trouver le bas du portrait

    temp_pdf_path = None
    try:
        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.set_compression(False)
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
        pdf.cell(0, 10, "Sommaire :", align="C", ln=True)
        pdf.set_font("Arial", size=12)
        for idx, graph in enumerate(selected_graphs, start=1):
            pdf.cell(0, 8, f"{idx}. {graph}", align="C", ln=True)

        # Récupération et redimensionnement du portrait
        portrait_img, portrait_height_mm = get_player_portrait(player_name, positions, base_folder, target_width_mm)
        if portrait_img is not None:
            # Pour aligner le bas du portrait à bottom_y_mm, calculer la position y de l'image
            top_y_mm = bottom_y_mm - portrait_height_mm
            # Sauvegarder l'image redimensionnée dans un fichier temporaire
            buffer = BytesIO()
            portrait_img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            composite_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
            with open(composite_path, "wb") as f:
                f.write(img_bytes)
            # Insérer le portrait dans le PDF : x fixe (ici 230 mm), y calculé pour aligner le bas
            pdf.image(composite_path, x=230, y=top_y_mm, w=target_width_mm, type="PNG")
            os.remove(composite_path)
        else:
            st.error("Le portrait du joueur n'a pas pu être chargé.")

        pdf.ln(10)

        # Insertion des graphiques (2 par page)
        graph_pairs = [selected_graphs[i:i+2] for i in range(0, len(selected_graphs), 2)]
        for graph_pair in graph_pairs:
            pdf.add_page()
            if background_image:
                pdf.image(background_image, x=0, y=0, w=297, h=210)
                r, g, b = map(int, text_color.split(","))
                pdf.set_text_color(r, g, b)
            x_offsets = [10, 155]
            for i, graph in enumerate(graph_pair):
                if module == "Pôle Féminin":
                    fig = plot_feminine_graph(graph, player_name, constants, player_data, positions)
                else:
                    fig = plot_masculine_graph(graph, player_name, constants, player_data, positions)
                if fig:
                    fig.update_layout(xaxis_tickangle=45)
                    temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                    fig.write_image(temp_image, scale=2, width=800, height=600)
                    pdf.image(temp_image, x=x_offsets[i], y=60, w=135, type="PNG")
                    os.remove(temp_image)
                else:
                    st.error(f"Graphique {graph} non disponible.")
        
        temp_pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{player_name}.pdf").name
        pdf.output(temp_pdf_path)
        st.write("PDF généré :", temp_pdf_path)
        return temp_pdf_path
    except Exception as e:
        st.error(f"Erreur lors de la génération du rapport PDF : {e}")
        return None

def display_selected_graphs(selected_graphs, player_name, constants, player_data, positions, module):
    """
    Affiche les graphiques sélectionnés de manière interactive en utilisant Plotly.
    """
    from PFtest import plot_feminine_graph
    from PMtest import plot_masculine_graph

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

def display_player_photo(selected_player, positions, base_folder):
    """
    Récupère et affiche la photo du joueur à partir du dossier "Trombi" au format PNG.
    """
    if "Trombi" not in positions.columns:
        st.error("La colonne 'Trombi' n'existe pas dans la feuille Poste.")
        return
    selected_norm = str(selected_player).strip().lower()
    positions["Joueur_norm"] = positions["Joueur"].astype(str).str.strip().str.lower()
    player_row = positions[positions["Joueur_norm"] == selected_norm]
    if player_row.empty:
        st.warning("Aucune donnée de photo pour ce joueur.")
        return
    file_name = player_row.iloc[0]["Trombi"]
    if not file_name:
        st.warning("Aucune photo disponible pour ce joueur.")
        return
    image_path = os.path.join(base_folder, "Trombi", file_name)
    if not os.path.exists(image_path):
        st.error(f"Le fichier image n'existe pas : {image_path}")
        return
    try:
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier image: {e}")
        return
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    html = f'''
    <div style="text-align: center;">
        <img src="data:image/png;base64,{base64_image}" alt="Photo de {selected_player}" width="200">
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

def main():
    data, video_data, positions, constante_data, base_folder = load_folder()
    st.write("Le dossier compressé doit contenir un fichier Excel avec les feuilles 'CSV', 'Vidéo', 'Poste', et 'Constante'.")
    if data is not None and video_data is not None and positions is not None and constante_data is not None and base_folder is not None:
        tab1, tab2 = st.tabs(["GPS", "Vidéo"])
        
        # Onglet GPS
        with tab1:
            background_file = st.file_uploader("Télécharger un fichier d'arrière-plan (PNG)", type=["png"])
            background_image = None
            if background_file is not None:
                background_image = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                with open(background_image, "wb") as f:
                    f.write(background_file.getvalue())
            
            col1, col2 = st.columns([0.5, 0.5])
            with col1:
                module = st.selectbox("Choisir le module d'analyse", ["Pôle Féminin", "Pôle Masculin"])
                selected_player = st.selectbox("Sélectionner un joueur/joueuse", data["Joueur"].drop_duplicates().tolist())
            with col2:
                if selected_player:
                    display_player_photo(selected_player, positions, base_folder)
            
            debug_composite = st.checkbox("Afficher l'image composite (debug)", value=False)
            if selected_player and debug_composite:
                # Ici, on affiche simplement le portrait redimensionné avec alignement par le bas
                portrait_img, portrait_height_mm = get_player_portrait(selected_player, positions, base_folder, target_width_mm=60)
                if portrait_img is not None:
                    st.image(portrait_img, caption="Portrait du joueur redimensionné", width=200)
                else:
                    st.warning("Impossible de charger le portrait pour ce joueur.")
            
            if selected_player:
                st.write(f"Graphiques pour {selected_player} ({module}):")
                if module == "Pôle Féminin":
                    from PFtest import get_feminine_constants
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
                    from PMtest import get_masculine_constants
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
                    per_min_graphs = [
                        "Dist/min",
                        "Distance>20kmh/min",
                        "Distance>16kmh/min",
                        "Nb Acc/Dec > 2m/s²/min",
                        "Nb Acc/Dec > 4m/s²/min"
                    ]
    
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
                    def filter_duration(player_data, min_duration=3900):
                        return player_data[player_data["Durée"] >= min_duration]
                    player_data = filter_duration(player_data)
    
                if player_data.empty:
                    st.warning("Aucune donnée à afficher après le filtrage.")
                else:
                    if selected_graphs:
                        st.write("**Graphiques sélectionnés :**")
                        display_selected_graphs(selected_graphs, selected_player, constants, player_data, positions, module)
    
                    if st.button("Générer le rapport PDF"):
                        temp_pdf_path = generate_report_with_background(
                            selected_graphs, selected_player, constants, player_data, positions, module,
                            background_image, base_folder
                        )
                        if temp_pdf_path:
                            with open(temp_pdf_path, "rb") as pdf_file:
                                st.download_button(
                                    "Télécharger le rapport PDF", 
                                    data=pdf_file, 
                                    file_name=f"rapport_{selected_player}.pdf"
                                )
                        if temp_pdf_path and os.path.exists(temp_pdf_path):
                            os.remove(temp_pdf_path)
                        if background_image and os.path.exists(background_image):
                            os.remove(background_image)

        # Onglet Vidéo
        with tab2:
            st.header("Vidéo")
            from scipy.ndimage import gaussian_filter
            col1, col2 = st.columns(2)
            with col1:
                player_name_video = st.selectbox("Sélectionnez un joueur", options=video_data["Joueur"].dropna().unique())
            with col2:
                session_name = st.selectbox("Sélectionnez une session", options=video_data["Session Title"].unique())

            if player_name_video and session_name:
                player_video_data = video_data[
                    (video_data["Joueur"] == player_name_video) & 
                    (video_data["Session Title"] == session_name)
                ]
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
                                st.error(
                                    f"Les longueurs des coordonnées X ({len(x_coords)}) et Y ({len(y_coords)}) ne correspondent pas."
                                )
                                x_coords, y_coords = [], []
                            heatmap = np.zeros((945, 612))
                            influence_radius = 1
                            sigma = influence_radius / (105 / 945)
                            for x, y in zip(x_coords, y_coords):
                                x_pixel = int((x / 105) * 945)
                                y_pixel = int((y / 68) * 612)
                                if 0 <= x_pixel < 945 and 0 <= y_pixel < 612:
                                    heatmap[y_pixel, x_pixel] += 1
                            heatmap = gaussian_filter(heatmap, sigma=sigma)
                            if np.max(heatmap) > 0:
                                heatmap /= np.max(heatmap)
                            fig = go.Figure()
                            fig.add_trace(go.Heatmap(
                                z=heatmap.T,
                                x=np.linspace(0, 105, 945),
                                y=np.linspace(0, 68, 612),
                                colorscale=[(0, "white"), (0.5, "blue"), (1, "red")],
                                zmin=0,
                                opacity=0.8,
                                showscale=False
                            ))
                            shapes = [
                                dict(type="rect", x0=0, y0=0, x1=105, y1=68, line=dict(color="black", width=2)),
                                dict(type="line", x0=52.5, y0=0, x1=52.5, y1=68, line=dict(color="black", width=2, dash="dash")),
                                dict(type="circle", xref="x", yref="y", 
                                     x0=52.5-9.15, y0=34-9.15, x1=52.5+9.15, y1=34+9.15, 
                                     line=dict(color="black", width=2)),
                                dict(type="rect", x0=0, y0=13.84, x1=16.5, y1=54.16, line=dict(color="black", width=2)),
                                dict(type="rect", x0=88.5, y0=13.84, x1=105, y1=54.16, line=dict(color="black", width=2)),
                                dict(type="rect", x0=-2, y0=30.34, x1=0, y1=37.66, line=dict(color="black", width=3)),
                                dict(type="rect", x0=105, y0=30.34, x1=107, y1=37.66, line=dict(color="black", width=3)),
                                dict(type="rect", x0=0, y0=24.84, x1=5.5, y1=43.16, line=dict(color="black", width=2)),
                                dict(type="rect", x0=99.5, y0=24.84, x1=105, y1=43.16, line=dict(color="black", width=2)),
                                dict(type="circle", xref="x", yref="y", x0=11-0.4, y0=34-0.4, x1=11+0.4, y1=34+0.4, 
                                     line=dict(color="black", width=2)),
                                dict(type="circle", xref="x", yref="y", x0=94-0.4, y0=34-0.4, x1=94+0.4, y1=34+0.4, 
                                     line=dict(color="black", width=2))
                            ]
                            fig.update_layout(
                                shapes=shapes,
                                xaxis=dict(range=[0, 105], showgrid=False, zeroline=False, 
                                           showticklabels=False, visible=False, scaleanchor="y"),
                                yaxis=dict(range=[0, 68], showgrid=False, zeroline=False, 
                                           showticklabels=False, visible=False, scaleanchor="x"),
                                margin=dict(l=0, r=0, t=0, b=0)
                            )
                            st.plotly_chart(fig)
                        except Exception as e:
                            st.error(f"Erreur lors de la génération de la carte de chaleur : {e}")
    else:
        st.warning("Veuillez charger un dossier compressé (ZIP) pour continuer.")

if __name__ == "__main__":
    main()
