import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Main page",
    page_icon="🌍",
)

st.session_state['language'] = 'FR'

with open('README.md', 'r') as f:
    readme_line = f.readlines()
    for row in readme_line:
        st.markdown(row, unsafe_allow_html=True)

with st.sidebar:
    # with st.container():
    with st.expander("**Language**"):
        st.session_state['language'] = st.selectbox('',['FR','EN']) #Language

    # st.success("Select a demo above.")
    st.warning("Language feature not available for now (please accept french)")