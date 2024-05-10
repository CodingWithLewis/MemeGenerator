import streamlit as st

from video import get_news_meme

st.markdown("""
# Meme Generator

Generate memes using AI! Upload an image and add text to it.
""")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Create Meme")
    with st.form("meme_form"):
        news_article = st.text_input("News Article")
        meme_image = st.file_uploader(
            "Upload an image. This will be used to caption.",
            accept_multiple_files=False,
            type=["png", "jpg", "jpeg"],
        )

        submit = st.form_submit_button("Generate Meme!")
with col2:
    st.subheader("Meme will show up here")

if submit:
    if meme_image is None:
        st.error("Please upload an image!")
        st.stop()
    bytes_data = meme_image.getvalue()
    with st.status("Starting...", state="running") as status:
        meme_caption = get_news_meme(news_article, meme_image.getvalue())
        status.write("Finished!")
    with col2:
        st.text_area(str(meme_caption))

st.divider()
with st.container():
    st.write("Data retrieval powered by:")
    st.image(
        "https://www.enterprisetimes.co.uk/wp-content/uploads/2044/05/Bright-Data-Logo-Copy.png",
        width=200,
    )
