import streamlit as st
import pandas as pd
from adbc_driver_postgresql import dbapi
from config import settings

st.title("Companies")

@st.cache_data
def load_data():
    with dbapi.connect(f'{settings.get_db_uri()}') as conn:
        data = pd.read_sql('SELECT name, location, description, link, created_at  FROM companies', conn)

    return data

data_load_state = st.text('Loading data...')
data = load_data()
data_load_state.text("Done! (using st.cache_data)")

st.write(data)
if st.button('Reload data'):
    load_data.clear()
