import streamlit as st
import requests
import csv
import os
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Climate Chart", page_icon="🌱")

with open('style/climate_chart.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.session_state['language'] = 'EN' # Manual initialization

def load_remote_data():
    # Load data from ADEME API
    base_url = "https://data.ademe.fr/data-fair/api/v1/datasets/base-carboner/"
    # api_key = "API key"

    # headers = {
    #     "Authorization": f"Bearer {api_key}"
    # }

    response_schema = requests.get(base_url+'safe-schema').json()   # , headers=headers
    columns = [el['key'] for el in response_schema]

    
    # Get number of items in the db
    response = requests.get(base_url+'lines')
    if response.status_code == 200:
        data = response.json()
        # print(f'Number of items in the db: {data["total"]}')
    else:
        print("Erreur lors de la requête :", response.status_code)
    nb_items = data["total"]

    # Request all the lines of the dataset
    nb_items_received=0
    batch_size = 1000
    url_suffix = f'lines?size={batch_size}'
    mode = 'w'
    while nb_items_received <nb_items:
        print(f'Request {nb_items_received//batch_size} / {(nb_items//batch_size)+1}')
        if nb_items_received>0:
            url_suffix = data['next'].split('/')[-1]
            mode = 'a'

        response = requests.get(base_url+url_suffix)

        if response.status_code == 200:
            data = response.json()
            nb_items_received += batch_size
        else:
            print("Erreur lors de la requête :", response.status_code)

        # Write response data into csv file
        with open('data.csv', mode=mode, newline='') as csvfile:
            csvwriter = csv.writer(csvfile)

            # Écrire les en-têtes
            if mode=='w':
                headers= columns
                csvwriter.writerow(headers)

            # Écrire les lignes de données
            for row in data['results']:
                row_values = [row.get(key, None) for key in headers]
                csvwriter.writerow(row_values)

def no_data_warning():
    st.warning('No data to display with the selected filters')

st.write("# Visualisation d'impacts carbone")

if not os.path.isfile('data.csv'):
    print('Making request')
    with st.spinner('Requesting for remote data ...'):
        load_remote_data()
else:
    print('Loading saved data')
#print(json.dumps(data, indent=4))  # Analyzing response output

with st.spinner('Reading data ...'):
    df = pd.read_csv('data.csv')    # selected useful cols = ['Nom_base_français', 'Type_poste', 'Nom_poste_français', 'Code_de_la_catégorie', 'Localisation_géographique', 'Total_poste_non_décomposé','Unité_français', 'Incertitude', 'Contributeur', 'Source']

# Preprocessing / Cleaning

pattern = ' > '
max_sub_cat = max(df['Code_de_la_catégorie'].apply(lambda f: len(f.split(pattern))))
for i in range(max_sub_cat):
    df[f'cat{i}'] = df['Code_de_la_catégorie'].apply(lambda f: f.split(pattern)[i] if len(f.split(pattern))>i else None)
df['nb_cat'] = df['Code_de_la_catégorie'].apply(lambda f: len(f.split('>')))
nb_categories = df['nb_cat'].max()

df['Nom_base_français'] = df['Nom_base_français'].apply(lambda f : f.replace('""""','').replace('"""','').replace('\t',''))     # Weird strings
df['Type_poste'] = df['Type_poste'].fillna('--Not applicable--')

# Data selection by user

# continuous_value = st.slider('Value',0,100,3)
# cat0 = st.sidebar.multiselect('Category',df['cat0'].unique())
# cat0 = st.sidebar.selectbox('Category',df['cat0'].unique())

input_data = df.copy()
categories_selected = []
current_cat = None
with st.sidebar:
    with st.expander("**Localisation filter**"):
        scale = st.multiselect('',options=input_data['Localisation_géographique'].unique(), default=input_data[f'Localisation_géographique'].unique())
        input_data=input_data[input_data['Localisation_géographique'].isin(scale)]
        if input_data.shape[0]==0:
            no_data_warning()
    
    with st.expander("**Type filter**"):
        type = st.multiselect('',options=input_data['Type_poste'].unique(), default=input_data[f'Type_poste'].unique())
        input_data=input_data[input_data['Type_poste'].isin(type)]
        if input_data.shape[0]==0:
            no_data_warning()

    with st.expander("**Categories filter**"):
        for cat_id in range(nb_categories):

                if (input_data['nb_cat'].min()>cat_id) :   #& (current_cat!="Select an option")
                    # Still sub categories to choose
                    if (input_data['nb_cat'].min()-1==cat_id) & (input_data['nb_cat'].max()-1==cat_id):   #& input_data['nb_cat'].max()==cat_id
                        current_cat = st.multiselect(f'Category - level {cat_id}',options=input_data[f'cat{cat_id}'].unique(), default=input_data[f'cat{cat_id}'].unique())
                        input_data = input_data[input_data[f'cat{cat_id}'].isin(current_cat)]

                        if input_data.shape[0]>0:
                            categories_selected.append(current_cat)
                            last_cat_level = f'cat{cat_id}'
                            title = pattern.join(input_data['Code_de_la_catégorie'].unique()[0].split(pattern)[:cat_id])
                        else:
                            no_data_warning()

                    elif input_data['nb_cat'].min()-1>=cat_id :
                        current_cat = st.selectbox(f'Category - level {cat_id}',options=input_data[f'cat{cat_id}'].unique())    #options = ["Select an option",  *input_data[f'cat{cat_id}'].unique()]
                        input_data = input_data[input_data[f'cat{cat_id}']==current_cat]

                        if input_data.shape[0]>0:
                            categories_selected.append(current_cat)
                            title = input_data['Code_de_la_catégorie'].unique()[0]
                            last_cat_level = f'cat{cat_id}'
                        else: 
                            no_data_warning()
    
# Plot

language_suffix = 'français' if st.session_state['language']=='FR' else 'anglais'
x_feature = f"Nom_base_{language_suffix}"
y_feature = "Total_poste_non_décomposé"

# Fix some particular use cases
# if input_data.groupby([x_feature])[last_cat_level].nunique()>0: 
#     # Same product name in multiple categories
#     # We update the product name for a better plot
#     input_data[x_feature] = input_data.apply(lambda f: f[x_feature]+'_'+f[last_cat_level], axis=0)

# Crop items names if too long to don't affect the display
size_item_name = 40
input_data['x_feature_croped'] = input_data[x_feature].apply(lambda f: f[:size_item_name])
x_feature2 = 'x_feature_croped'

if input_data.shape[0]>0:
    fig = px.bar(
        input_data, 
        x=x_feature2, 
        y=y_feature,
        title=title,
        color=input_data[last_cat_level],
        hover_data=[x_feature],
        labels={
            x_feature2:'Nom du produit/service',
            y_feature:f"{'<br>'.join(input_data[f'Unité_{language_suffix}'].unique())}",
            last_cat_level : 'Categories'
        },
        barmode='group')
    fig.update_layout(
        height= 600,
        width= 800,
    )

    st.plotly_chart(fig, use_container_width=True)
else: 
    # When all last subcategories are not unselected
    no_data_warning()
