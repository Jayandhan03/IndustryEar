import streamlit as st
from src.agent import agent

st.set_page_config(
    page_title="AI Solopreneur News",
    page_icon="📰",
    layout="centered",
)

st.title("📰 AI Solopreneur News Agent")
st.caption("Latest stories on solo founders using AI to build millions")

query = st.text_input(
    "Enter news topic",
    value="How solo entrepreneurs use AI to become multimillionaires",
)

if st.button("Generate News 🚀"):

    with st.spinner("Searching the web and summarizing..."):
        result = agent(topic=query)   # ✅ this is already a STRING

    if result and isinstance(result, str):
        st.success("Done")
        st.markdown(result)
    else:
        st.warning("No summary generated.")
