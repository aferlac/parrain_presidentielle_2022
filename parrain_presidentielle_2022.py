#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import folium
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import folium_static

st.set_page_config(page_title=' Parrainages - Présidentielle 2022 ', page_icon=None, layout='centered', initial_sidebar_state='auto')
st.title('Parrainages - Présidentielle 2022')

# Récupération des données du conseil constitutionnel
@st.cache
def extract(lien):
    return(pd.read_csv(lien, sep=';'))
df = extract("https://presidentielle2022.conseil-constitutionnel.fr/telechargement/parrainagestotal.csv")

# Construction du df_parrain = nombre de parrainage par candidat
@st.cache
def total_parrain(df):
    candidat, parrainage = [], []
    parrainage = []
    for i in df['Candidat'].unique():
        candidat.append(i)
        parrainage.append(df['Candidat'][df['Candidat']==i].count())
    df_parrain = pd.DataFrame({
        'candidat' : candidat,
        'nombre parrainage' : parrainage,
    })
    df_parrain['limite']=500
    df_parrain=df_parrain.sort_values(by='nombre parrainage',ascending=False)
    return(df_parrain)
df_parrain = total_parrain(df)

# Construction du df_occurence = nombre de parrainage par candidat, département et date de publication
@st.cache
def occurence(df):
    candidat, departement, nombre, date = [], [], [], []
    for c in df['Candidat'].unique():
        for d in df['Département'][(df['Candidat']==c)].unique():
            n=0
            for j in df['Date de publication'].unique():   
                n+=len(df[(df['Candidat']==c) & (df['Département']==d) & (df['Date de publication']==j)])
                candidat.append(c)
                departement.append(d)
                nombre.append(n)
                date.append(j)
    df_occurence = pd.DataFrame({
    'Candidats':candidat,
    'Département':departement,
    'Date':date,    
    'Parrainage':nombre,
    })
    df_occurence['Limite']=500
    return(df_occurence)
df_occurence = occurence(df)

liste_candidats = df['Candidat'].unique()
liste_candidats.sort()

liste_depart= df_occurence['Département'].unique()
liste_depart.sort()

Choix_graphe = st.radio(label='Choisissez un graphe',
                        options=['Nombre de parrainages validés',
                                 'Origine géographique des parrainages',
                                 'Evolution des parrainages',
                                 'Par département',
                                 'Par candidat'])

if Choix_graphe=='Nombre de parrainages validés':
    # Graphe du nombre de parrainage par candidat
    fig = px.bar(df_parrain, 
             x='candidat', 
             y='nombre parrainage',
            title='Nombre de parrainages publiés le '+str(df_occurence['Date'].max()),
             orientation='v',
             range_y=[0,600],
             width=800,
            height=600,
            hover_data={'candidat':False, 'nombre parrainage':True},
             labels=None,
            )
    fig.add_trace(trace=go.Scatter(x=df_parrain['candidat'], y=df_parrain['limite'],  mode='lines',showlegend=False,hoverinfo='none'))
    st.write(fig)


elif Choix_graphe=='Origine géographique des parrainages':
    Choix_candidat = st.selectbox(label='Sélectionnez un candidat (menu déroulant ou saisir le nom)',options=liste_candidats)
    # création de la carte OpenStreetMap de la France
    map = folium.Map([46.9, 3.1], zoom_start=5)
    # ajout des contours des communes
    folium.Choropleth(geo_data=r'contour-des-departements.geojson', 
                    name="départements", 
                    data=df_occurence[df_occurence['Candidats']==Choix_candidat], 
                    columns=['Département','Parrainage'], 
                    key_on='feature.properties.nom', 
                    fill_color="YlGnBu",
                    nan_fill_opacity=0,
                    bins=[1, 5, 10, 20, 30, 50, 70,100], 
                    fill_opacity=1, 
                    line_weight=0.4,
                    ).add_to(map)
    # Ajout du contrôle des couches
    folium.LayerControl().add_to(map)

    # Affichage du parrain et du nombre de parrainage
    st.write(str(df_parrain[df_parrain['candidat']==Choix_candidat]['nombre parrainage'].tolist()[0])+' parrainages')

    # Affichage de la carte dans Streamlit
    folium_static(map)

elif Choix_graphe=='Evolution des parrainages':
    # Graphe de l'evolution des parrainages en fonction du temps.
    fig = px.bar(df_occurence, 
             x='Candidats', 
             y='Parrainage',
             animation_frame='Date',
            title='Parrainages validés',
             orientation='v',
             range_y=[0,600],
             width=800,
            height=600,
            hover_data={'Date':True, 'Candidats':False, 'Département':True, 'Parrainage':True},
             labels=None,
            )
    fig.add_trace(trace=go.Scatter(x=df_occurence['Candidats'], y=df_occurence['Limite'],  mode='lines',showlegend=False,hoverinfo='none'))
    st.write(fig)

elif Choix_graphe=='Par département':
    # Graphe des parrainages par département
    depart=st.selectbox(label='Sélectionnez un département (menu déroulant ou saisir le nom)',options=df_occurence['Département'].unique())
    df_departement=df_occurence[(df_occurence['Département']==depart) & (df_occurence['Date']==df_occurence['Date'].max())].sort_values(by='Parrainage',ascending=False)
    fig = px.bar(df_departement, 
                 x='Candidats', 
                 y='Parrainage',
                 title=depart+' : '+str(df_departement['Parrainage'].sum())+' parrainages',
                 orientation='v', 
                 width=800,
                 height=600,
                 hover_data={'Candidats':False, 'Parrainage':True},
                 labels=None,
                )
    if df_departement['Parrainage'].max()<=10:
        fig.update_yaxes(dtick=1)
    st.write(fig)

else:
    # Graphe des parrainages par candidat
    candidat= st.selectbox(label='Sélectionnez un candidat (menu déroulant ou saisir le nom)',options=liste_candidats)
    @st.cache
    def create_df_candidat(personne):
        df=df_occurence[(df_occurence['Candidats']==personne) & (df_occurence['Date']==df_occurence['Date'].max())].sort_values(by='Parrainage',ascending=False)
        df.drop(columns='Limite',inplace=True)
        df = df.set_index(np.arange(len(df))) 
        df['angle']=360/len(df)*df.index
        df['base']=40
        return(df)
    df_candidat=create_df_candidat(candidat)
    fig=px.bar_polar(data_frame=df_candidat,
                r=df_candidat['Parrainage'],
                theta=df_candidat['angle'],
                hover_data={'Date':False, 'Candidats':False, 'Département':True, 'Parrainage':True, 'angle':False, 'base':False},
                base=df_candidat['base'],
                barmode='relative',
                direction='clockwise',
                start_angle=90,
                title='Parrainages de '+candidat+' par département',
                width=800,
                height=600,
                )
    fig.update_layout(
        template=None,
        polar = dict(
            radialaxis = dict(range=[0, 100],
                            showticklabels=False,
                            ticks='',
                            gridwidth=0,
                            gridcolor='white',
                            ),
            angularaxis = dict(showticklabels=False,
                            ticks='',
                            gridwidth=0,
                            gridcolor='white',
                            ),
        ),
    )
    st.write(str(df_parrain[df_parrain['candidat']==candidat]['nombre parrainage'].tolist()[0])+' parrainages')
    st.write(fig)

st.write('---')
st.write('''Cette application a été construite sous Python avec les librairies Streamlit, Pandas, Plotly et Folium.\n
Les données des parrainages sont publiées par le conseil constitutionnel en open data chaque mardi et jeudi. https://presidentielle2022.conseil-constitutionnel.fr/les-parrainages/tous-les-parrainages-valides.html.\n
Merci à Grégoire David pour les coordonnées des contours des départements : https://france-geojson.gregoiredavid.fr/ \n
A. FERLAC - Février 2022.''')
st.write('---')