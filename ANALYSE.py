import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os


# Chargement du fichier CSV
uploaded_file = st.file_uploader("Choisissez un fichier CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Lecture du CSV en utilisant la 3ème ligne comme en-tête
        df = pd.read_csv(uploaded_file, skiprows=2, header=0, encoding="utf-8", low_memory=False)
        
        # Vérification de la présence des colonnes nécessaires
        if "Time" in df.columns and "HR (bpm)" in df.columns:
            # Conversion de la colonne Time en datetime et calcul du temps écoulé en minutes
            df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
            df["Elapsed Minutes"] = (df["Time"] - df["Time"].min()).dt.total_seconds() / 60
            
            # Création du graphique complet
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["Elapsed Minutes"],
                y=df["HR (bpm)"],
                mode="lines",
                name="HR (bpm)"
            ))
            # Ici, on définit le hovermode à "x unified" pour conserver l'étiquette unifiée
            fig.update_layout(
                title="Fréquence cardiaque en fonction du temps",
                xaxis_title="Temps (minutes)",
                yaxis_title="HR (bpm)",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("Sélectionnez manuellement la plage de l'axe X en indiquant le début et la fin (en minutes) :")
            
            # Deux colonnes pour la saisie manuelle
            col1, col2 = st.columns(2)
            with col1:
                x_min_manual = st.number_input(
                    "Début de la plage (minutes)",
                    value=float(df["Elapsed Minutes"].min()),
                    min_value=float(df["Elapsed Minutes"].min()),
                    max_value=float(df["Elapsed Minutes"].max()),
                    step=0.1,
                    format="%.2f"
                )
            with col2:
                x_max_manual = st.number_input(
                    "Fin de la plage (minutes)",
                    value=float(df["Elapsed Minutes"].max()),
                    min_value=float(df["Elapsed Minutes"].min()),
                    max_value=float(df["Elapsed Minutes"].max()),
                    step=0.1,
                    format="%.2f"
                )
            
            if x_max_manual < x_min_manual:
                st.error("La valeur de fin doit être supérieure à la valeur de début.")
            else:
                # Filtrage des données en fonction de la plage saisie
                df_selected = df[(df["Elapsed Minutes"] >= x_min_manual) & (df["Elapsed Minutes"] <= x_max_manual)]
                
                st.write(f"**Plage sélectionnée :** {x_min_manual:.2f} - {x_max_manual:.2f} minutes")
                
                if not df_selected.empty:
                    hr_max = df_selected["HR (bpm)"].max()
                    hr_mean = df_selected["HR (bpm)"].mean()
                    hr_min = df_selected["HR (bpm)"].min()
                    hr_max_time = df_selected[df_selected["HR (bpm)"] == hr_max]["Elapsed Minutes"].values[0]
                    
                    # Récupération des HR à 1, 2, 3 et 5 minutes après HR max
                    time_offsets = [1, 2, 3, 5]
                    hr_differences = {}
                    hr_values = []
                    
                    for offset in time_offsets:
                        hr_time = hr_max_time + offset
                        nearest_hr = df.iloc[(df["Elapsed Minutes"] - hr_time).abs().argsort()[:1]]["HR (bpm)"].values[0]
                        hr_differences[offset] = hr_max - nearest_hr
                        
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**HR Maximum :** {hr_max:.2f}")
                        st.write(f"**HR Moyenne :** {hr_mean:.2f}")
                        st.write(f"**HR Minimum :** {hr_min:.2f}")
                    
                    with col2:
                        recovery_data = pd.DataFrame({
                            "Δ Récupération": ["1 min", "2 min", "3 min", "5 min"],
                            "Différence avec HR max": list(hr_differences.values())
                        })
                        recovery_data = recovery_data.dropna(axis=1, how='all')  # Suppression des colonnes vides
                        recovery_data = recovery_data.iloc[:, :2]  # Forcer le tableau à n'avoir que deux colonnes
                        st.dataframe(recovery_data.set_index("Δ Récupération"))
                else:
                    st.write("Aucune donnée dans la plage sélectionnée.")
        else:
            st.error("Les colonnes 'Time' et 'HR (bpm)' ne sont pas présentes dans le fichier.")
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
