import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner

st.title("Pravi Real-time Skeniranje QR Kodova")
st.write(
    "Umeri kameru ka QR kodu – skener će ga automatski uhvatiti čim se pojavi"
    " u kadru."
)

if "scanned_url" not in st.session_state:
  st.session_state.scanned_url = None

# Pravi live stream skener u pretraživaču
qr_code = qrcode_scanner(key="qrcode_scanner")

if qr_code:
  if qr_code.startswith("http://") or qr_code.startswith("https://"):
    if st.session_state.scanned_url != qr_code:
      st.session_state.scanned_url = qr_code
      st.success(f"Uspešno detektovan link iz kadra!")
  else:
    st.warning(f"Sadržaj QR koda nije URL: {qr_code}")

if st.session_state.scanned_url:
  st.subheader("Rezultati Scraping-a sa stranice:")
  url = st.session_state.scanned_url

  with st.spinner("Preuzimam i parsiram podatke sa linka..."):
    try:
      headers = {
          "User-Agent": (
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          )
      }
      response = requests.get(url, headers=headers, timeout=10)

      if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        tables = pd.read_html(response.text)

        if tables:
          st.write("Pronađene tabele na stranici:")
          for df in tables:
            st.dataframe(df)
        else:
          st.info(
              "Stranica je uspešno učitana, ali nisu pronađene standardne"
              " tabele."
          )
          paragraphs = [p.text for p in soup.find_all("p")]
          st.write(" ".join(paragraphs[:10]))
      else:
        st.error(f"Greška prilikom pristupa sajtu. Status kod: {response.status_code}")
    except Exception as e:
      st.error(f"Došlo je do greške tokom scraping-a: {e}")

  if st.button("Skeniraj novi kod"):
    st.session_state.scanned_url = None
    st.rerun()
