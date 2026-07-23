import streamlit as st

st.set_page_config(page_title="Continent Clicker", page_icon="🌍", layout="wide")

st.title("🌍 Continent Clicker")
st.caption("A mobile-friendly country-shape quiz. Choose a continent and tap the matching country.")
st.info("For the installable mobile version, open the game below in a new tab, then use your browser menu to **Install app** or **Add to Home Screen**.")
st.link_button("Open the installable game", "/app/static/mobile-game.html", type="primary")
st.iframe("/app/static/mobile-game.html", height=740)
