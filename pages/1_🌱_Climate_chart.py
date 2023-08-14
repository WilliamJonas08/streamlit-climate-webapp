import streamlit as st
import requests
import csv
import os
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Climate Chart", page_icon="🌱")
if 'language' not in st.session_state.keys():
    st.session_state['language'] = 'FR' # Manual initialization

with open('style/climate_chart.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


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

def clean_data(df):
    # Choice data status within 'Archivé', 'Valide générique', 'Refusé', 'En brouillon','Valide spécifique', 'En discussion', 'Supprimé'
    df = df[df["Statut_de_l'élément"]=='Valide générique']

    df['Nom_base_français'] = df['Nom_base_français'].apply(lambda f : f.replace('""""','').replace('"""','').replace('\t',''))     # Weird strings
    df['Type_poste'] = df['Type_poste'].fillna('--Not applicable--')

    # Removing some duplicated names
    df.loc[df.cat2=='Produits animaux','Nom_base_français'] = df.loc[df.cat2=='Produits animaux','Nom_base_français'].apply(lambda f: f.lower().replace(' de ', ' ').capitalize())

    # Lacks of translations
    df['Nom_base_anglais'] = df['Nom_base_anglais'].fillna(df['Nom_base_français'])
    df['Unité_anglais'] = df['Unité_anglais'].fillna(df['Unité_français'])
    return df

def no_data_warning(message='No data to display with the selected filters'):
    st.warning(message)

def init_page_data():
    if not os.path.isfile('data.csv'):
        print('Making request')
        with st.spinner('Requesting for remote data ...'):
            load_remote_data()
    else:
        print('Loading saved data')
    #print(json.dumps(data, indent=4))  # Analyzing response output

    with st.spinner('Reading data ...'):
        df = pd.read_csv('data.csv')    # selected useful cols = ['Nom_base_français', 'Type_poste', 'Nom_poste_français', 'Code_de_la_catégorie', 'Localisation_géographique', 'Total_poste_non_décomposé','Unité_français', 'Incertitude', 'Contributeur', 'Source']

    return df

def plot_all_data(df):

    # FILTERS
    input_data = df.copy()
    categories_selected = []
    current_cat = None
    with st.sidebar:
        with st.container():
            st.header('All data filters')
            with st.expander("**Categories**"):
                for cat_id in range(nb_categories):

                        if (input_data['nb_cat'].min()>cat_id) :   #& (current_cat!="Select an option")
                            # Still sub categories to choose
                            if (input_data['nb_cat'].min()-1==cat_id) & (input_data['nb_cat'].max()-1==cat_id):   #& input_data['nb_cat'].max()==cat_id
                                current_cat = st.multiselect(f'Category - level {cat_id}',options=input_data[f'cat{cat_id}'].unique(), default=input_data[f'cat{cat_id}'].unique(), key=cat_id)
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
            
            st.write('Other filters')
            with st.expander("**Localisation**"):
                scale = st.multiselect('',options=input_data['Localisation_géographique'].unique(), default=input_data[f'Localisation_géographique'].unique(), key="scale")
                input_data=input_data[input_data['Localisation_géographique'].isin(scale)]
                if input_data.shape[0]==0:
                    no_data_warning()
        
            with st.expander("**Type**"):
                type = st.multiselect('',options=input_data['Type_poste'].unique(), default=input_data[f'Type_poste'].unique(), key="type")
                input_data=input_data[input_data['Type_poste'].isin(type)]
                if input_data.shape[0]==0:
                    no_data_warning()

    # PLOT
    # if st.session_state['tab'] == 'all_data':
    language_suffix = 'français' if st.session_state['language']=='FR' else 'anglais'
    x_feature = f"Nom_base_{language_suffix}"
    y_feature = "Total_poste_non_décomposé"

    # Fix some particular use cases (eg planes with different number of passengers)
    # if input_data.groupby([x_feature])[last_cat_level].nunique()>0: 
    #     # Same product name in multiple categories
    #     # We update the product name for a better plot
    #     input_data[x_feature] = input_data.apply(lambda f: f[x_feature]+'_'+f[last_cat_level], axis=0)

    # Crop items names if too long to don't affect the display
    size_item_name = 40

    input_data['x_feature_croped'] = input_data[x_feature].apply(lambda f: f[:size_item_name])
    input_data = input_data.sort_values(y_feature, ascending=False)

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

def plot_diet_chart(df):

    st.write('#### Impact carbone des aliments selon le régime alimentaire')

    mapping_animals_dic={
        'boeuf':['Boeuf','Génisse','Taurillon','Vache','Veau'],
        'chèvre' : ['Chèvre','Chevrette','Chevreau'],
        'mouton' : ['Brebis', 'Agneau'],
        'porc' : ['Porc','Truie'],
        'poisson' : ['Porc','Truie'],
        'poulet' : ['Poulet','Dinde'],
    }
    list_milk = ['Lait 1er âge', 'Lait 2e âge', 'Lait concentré non sucré',
        'Lait concentré sucré', 'Lait de brebis', 'Lait de chèvre',
            'Lait de croissance infantile',
        'Lait de vache', 'Lait demi-écrémé', 'Lait emprésuré aromatisé',
        'Lait en poudre', 'Lait entier',
        'Lait fermenté ou spécialité laitière type yaourt',
        'Lait fermenté à boire', 'Lait gélifié aromatisé', 'Lait écrémé']
    LIST_VEGAN = ['Tofu', 'Haricots verts', 'Noix', 'Soja']
    LIST_VEGGE = ['Lait vache', 'Lait chèvre', 'Lait brebis', 'Oeuf', *list_milk]
    LIST_CARNIVORE = [k.capitalize() for k in mapping_animals_dic.keys()]
    list_animals_raw_products=['Oeuf', 'Lait vache', 'Lait chèvre', 'Lait brebis', 'Laine']

    with st.expander('Vegan dishes'):
        list_vegan = st.multiselect('', options=LIST_VEGAN, default=LIST_VEGAN, key="vegan")
    with st.expander('Vegge dishes'):
        list_vege = st.multiselect('', options=LIST_VEGGE, default=LIST_VEGGE, key="vegge")
    with st.expander('Carnivore dishes'):
        list_carnivore = st.multiselect('', options=LIST_CARNIVORE, default=LIST_CARNIVORE, key="carnivore")

    def matching(key, str):
        try:
            key = key.lower()
            str = str.lower()
        except:
            print(str, key)
        return (key==str) #or (key+' ' in str)

    def map_meat_fn(str):
        if str in list_animals_raw_products:
            return str.lower()

        for key in mapping_animals_dic.keys():
            for sub_key in mapping_animals_dic[key]: 
                if sub_key.lower() in str.lower():
                    # if key=='boeuf' and ('lait' in str.lower()):
                    #     return 'vache laitière'
                    # else:
                        return key

    def map_vege_fn(str):

        if 'lait' in str.lower():
            return 'lait'
        else:
            return str

    def map_vegan_fn(str):

        if 'noix' in str.lower():
            return 'noix'
        else:
            return str

    df.loc[:, 'name_mapped'] = df.loc[:, 'Nom_base_français']
    df.loc[df.cat2=='Produits animaux','Nom_base_français'] = df.loc[df.cat2=='Produits animaux','Nom_base_français'].apply(lambda f: f.lower().replace(' de ', ' ').capitalize())
    df.loc[df.cat2=='Produits animaux', 'name_mapped'] = df.loc[df.cat2=='Produits animaux', 'Nom_base_français'].apply(lambda f: map_meat_fn(f))
    df = df.loc[~df.name_mapped.isna()]

    mask_vege = df['Nom_base_français'].apply(lambda f: sum([matching(key,f) for key in list_vege])).astype(bool)
    mask_vegan = df['Nom_base_français'].apply(lambda f: sum([matching(key,f) for key in list_vegan])).astype(bool)
    mask_carnivore = df['name_mapped'].apply(lambda f: sum([matching(key,f) for key in list_carnivore])).astype(bool)

    df.loc[mask_vege,'name_mapped'] = df.loc[mask_vege,'Nom_base_français'].apply(lambda f: map_vege_fn(f))
    df.loc[mask_vegan,'name_mapped'] = df.loc[mask_vegan,'Nom_base_français'].apply(lambda f: map_vegan_fn(f))
    df = df.loc[~df.name_mapped.isna()]
    df.loc[:,'name_mapped'] = df.loc[:,'name_mapped'].apply(lambda f: f.lower().capitalize())

    df.loc[: ,'cat_plot'] = 'carnivore'
    df.loc[mask_vege,'cat_plot'] = 'vegetarian'
    df.loc[mask_vegan,'cat_plot'] = 'vegan'

    df = df.loc[ mask_carnivore | mask_vege | mask_vegan]

    with st.container():
        if df.shape[0]>2:
    
            input_data = df.copy()
            input_data = input_data.groupby(['cat_plot', "name_mapped"])["Total_poste_non_décomposé"].mean().reset_index()
            input_data = input_data.sort_values("Total_poste_non_décomposé", ascending=False)

            fig = px.bar(
                input_data, 
                x="name_mapped",
                y="Total_poste_non_décomposé",
                title='',
                color='cat_plot',
                labels={
                    "name_mapped":'Aliment',
                    "Total_poste_non_décomposé": 'kgCO2e/kg', #f"{'<br>'.join(df[f'Unité_français'].unique())}",
                    'cat_plot':'Diet'
                })

            st.plotly_chart(fig, use_container_width=True)
        else: 
            # When all categories are not unselected
            no_data_warning()

    with st.container():

        st.write('#### Key metrics')
        if df.shape[0]>2:

            input_data = df.groupby(['cat_plot', "name_mapped"])["Total_poste_non_décomposé"].mean().reset_index()

            def find_element_index(element, my_list):
                try:
                    index = my_list.index(element)
                except:
                    index = 0
                return index

            aliment1 = input_data.iloc[0].name_mapped
            aliment2 = input_data.iloc[1].name_mapped
            col1, col2 = st.columns(2)
            with col1:
                aliment1 = st.selectbox('Aliment A', options=[item for item in input_data.name_mapped.unique() if item != aliment2], index=find_element_index('Beauf',[item for item in input_data.name_mapped.unique() if item != aliment2]))
                v1_value = input_data.query("name_mapped==@aliment1")['Total_poste_non_décomposé'].values[0]
                st.write(f'{v1_value.round(1)} kgCO2e/kg')
            with col2:
                aliment2 = st.selectbox('Aliment B', options=[item for item in input_data.name_mapped.unique() if item != aliment1], index=find_element_index('Tofu',[item for item in input_data.name_mapped.unique() if item != aliment1]))
                v2_value = input_data.query("name_mapped==@aliment2")['Total_poste_non_décomposé'].values[0]
                st.write(f'{v2_value.round(1)} kgCO2e/kg')

            # input_data = input_data.set_index("name_mapped").loc[[aliment1,aliment2]]
            difference = (v1_value-v2_value)/min(v1_value,v2_value)

            mk = f"""
                <div style="display: flex; justify-content: center; margin-top:1.5rem;">
                    <div style="border: 2px solid #ccc; padding: 1rem 1.5rem 1rem 1.5rem; border-radius: 10px;">
                        <p style="margin:0;">
                            <strong style="font-size: 1.5rem; text-align: left;">{aliment1}</strong>  émet <br>
                        </p>
                        <div>
                            <span style="color: {'red' if difference >0 else 'green'}; font-size: 2.5rem;">
                                {'+' if difference >0 else ''} {difference.round(1)}
                            </span>
                            <div style="font-size: 0.5rem; text-align: center; margin=0;">
                                &nbsp;&nbsp;fois {'plus' if difference >0 else 'moins'} de CO2
                            </div>
                        </div>
                        <p style="text-align: right;margin:0;">
                            que  <strong style="font-size: 1.5rem;">{aliment2}</strong>
                        </p>
                    </div>
                </div>
            """
            st.markdown(body=mk, unsafe_allow_html=True)
        else: 
            no_data_warning('Not enought data with the selected filters (at least 2 dishes are required)')

st.write("# Visualisation d'impacts carbone")

df = init_page_data()

# Preprocessing / Cleaning
pattern = ' > '
max_sub_cat = max(df['Code_de_la_catégorie'].apply(lambda f: len(f.split(pattern))))
for i in range(max_sub_cat):
    df[f'cat{i}'] = df['Code_de_la_catégorie'].apply(lambda f: f.split(pattern)[i] if len(f.split(pattern))>i else None)
df['nb_cat'] = df['Code_de_la_catégorie'].apply(lambda f: len(f.split(pattern)))
nb_categories = df['nb_cat'].max()

df = clean_data(df)

all_data, meat = st.tabs(["📈 All data", "🍖 Why you should eat more meat"])

with all_data:
    st.session_state['tab'] = 'all_data'
    plot_all_data(df)

with meat:
    st.session_state['tab'] = 'meat'
    plot_diet_chart(df)




# Data selection by user

# continuous_value = st.slider('Value',0,100,3)
# cat0 = st.sidebar.multiselect('Category',df['cat0'].unique())
# cat0 = st.sidebar.selectbox('Category',df['cat0'].unique())


