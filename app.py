import cv2
import numpy as np
import pandas as pd
from pyzbar.pyzbar import decode
import requests
from bs4 import BeautifulSoup
import streamlit as st

st.title("Real-time Skeniranje i Scraping QR Kodova sa Računa")
st.write("Umeri kameru ka QR kodu sa fiskalnog računa.")

if "scanned_url" not in st.session_state:
  st.session_state.scanned_url = None

camera_image = st.camera_input("Uključi kameru")

if camera_image is not None:
  bytes_data = camera_image.getvalue()
  np_arr = np.frombuffer(
      bytes_data, np.pybytes if hasattr(np, "pybytes") else np.uint8  # type: ignore
  )
  frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

  decoded_objects = decode(frame)

  if decoded_objects:
    for obj in decoded_objects:
      qr_data = obj.data.decode("utf-8")

      if qr_data.startswith("http://") or qr_data.startswith("https://"):
        if st.session_state.scanned_url != qr_data:
          st.session_state.scanned_url = qr_data
          st.success(
              f"Uspešno detektovan link: [Otvori link]({qr_data})"
          )
      else:
        st.warning(f"Sadržaj QR koda nije URL: {qr_data}")
  else:
    st.info("QR kod nije pronađen u kadru. Pomerite kameru bliže.")

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
