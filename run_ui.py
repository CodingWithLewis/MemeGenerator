import streamlit as st

from main import create_upload_file

st.markdown('''
# Meme Generator

Generate memes using AI! Upload an image and add text to it.
''')
col1, col2 = st.columns(2)

with col1:
    st.subheader("Create Meme")
    with st.form("meme_form"):
        news_article = st.text_input("News Article")
        meme_image = st.file_uploader('Upload an image. This will be used to caption.', accept_multiple_files=False, type=['png', 'jpg', 'jpeg'])

        submit = st.form_submit_button("Generate Meme!")

with col2:
    log_area = st.empty()

if submit:
    if meme_image is None:
        st.error("Please upload an image!")
        st.stop()
    bytes_data = meme_image.getvalue()
    image_path = create_upload_file(bytes_data, news_article, log_area)
    st.image(str(image_path.absolute()))

