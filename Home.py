import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Climate web app",
    page_icon="🌍",
)

st.session_state['language'] = 'FR'

st.write('# Welcome there !')

st.write('The sections you can explore are displayed on the left side bar of the screen.')

st.write("Don't forget to leave a feedback in the corresponding section about what you would have liked to find in such initiative 💚")


# If we want to include the README content inside the home page
# with open('README.md', 'r') as f:
#     readme_line = f.readlines()
#     for row in readme_line:
#         st.markdown(row, unsafe_allow_html=True)

with st.sidebar:
    with st.expander("**Language**"):
        language = st.selectbox('',['FR','EN']) #Language
        st.session_state['language'] = language
        # if language=='EN':
        #     st.success("Language switched to English")
        # elif language=='FR':
        #     st.success("Langue changée en Français")
    if language=='EN':
        st.warning("Language feature only available for product/services names (in climate chart section)")