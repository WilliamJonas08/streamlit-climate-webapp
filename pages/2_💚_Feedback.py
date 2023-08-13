# Inspired from https://www.youtube.com/watch?v=FOULV9Xij_8
# Form Submit : https://formsubmit.co/

import streamlit as st  # pip install streamlit

with open('style/feedback.css') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


st.write("# :mailbox: Get In Touch With Me!")
st.write("Any feedback will be appreciated 💚")

contact_form = """
<form action="26393e880afb441edff4c4baaa47e867" method="POST">
     <input type="hidden" name="_captcha" value="false">
     <input type="text" name="name" placeholder="Your name" required>
     <input type="email" name="email" placeholder="Your email" required>
     <textarea name="message" placeholder="Your feedback here"></textarea>
     <button type="submit">Send</button>
</form>
"""

st.markdown(contact_form, unsafe_allow_html=True)

with st.container():
    st.markdown(f"If the form above doesn't work, you can try with this (secured) link: https://formsubmit.co/el/nabolo")