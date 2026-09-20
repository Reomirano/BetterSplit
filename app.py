import cv2
import numpy as np
import pandas as pd
from pyzbar.pyzbar import decode
import requests
from bs4 import BeautifulSoup
import streamlit as st

st.set_page_config(
    page_title="BetterSplit & Fiskalni Skener", page_icon="🧾", layout="wide"
)

st.title("BetterSplit — Upravljanje troškovima i fiskalnim računima")

# Kreiranje tabova da sve bude na jednom mestu
tab1, tab2 = st.tabs(
    ["Mreža troškova (BetterSplit)", "Skeniranje fiskalnog računa"]
)

with tab1:
  st.header("Podela troškova i IPS QR")
  st.write("Ovde stoji tvoja originalna logika za deljenje troškova...")
  # Ovde ide tvoj postojeći kod za deljenje troškova i IPS generisanje

with tab2:
  st.header("Skeniranje fiskalnog QR koda")
  st.write(
      "U slikaj fiskalni račun ili otpremi fotografiju da automatski"
      " preuzmemo podatke sa Poreske uprave."
  )

  # Dajemo obe opcije: slikanje kamerom i upload fajla radi sigurnosti
  opcija = st.radio(
      "Izaberi način unosa:", ["Uslikaj kamerom", "Otpremi sliku sa uređaja"]
  )

  qr_data = None

  if opcija == "Uslikaj kamerom":
    camera_image = st.camera_input("Umeri kameru ka QR kodu sa računa")
    if camera_image is not None:
      bytes_data = camera_image.getvalue()
      np_arr = np.frombuffer(bytes_data, np.uint8)
      frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
      decoded_objects = decode(frame)
      if decoded_objects:
        qr_data = decoded_objects[0].data.decode("utf-8")

  else:
    uploaded_file = st.file_uploader(
        "Izaberi sliku računa", type=["png", "jpg", "jpeg"]
    )
    if uploaded_file is not None:
      file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
      opencv_image = cv2.imdecode(file_bytes, 1.de)  # type: ignore
      # Ako koristimo cv2 imdecode za uploadovan fajl:
      opencv_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
      decoded_objects = decode(opencv_image)
      if decoded_objects:
        qr_data = decoded_objects[0].data.decode("utf-8")

  # Ako je QR kod uspešno iščitan i predstavlja validan link ka SUF-u
  if qr_data:
    if qr_data.startswith("http"):
      st.success(f"Uspešno prepoznat link: {qr_data}")

      with st.spinner("Skidamo podatke sa Poreske uprave..."):
        try:
          headers = {
              "User-Agent": (
                  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              )
          }
          response = requests.get(qr_data, headers=headers, timeout=10)

          if response.status_code == 200:
            tables = pd.read_html(response.text)
            if tables:
              st.subheader("Stavke sa fiskalnog računa:")
              for df in tables:
                st.dataframe(df)
            else:
              st.info(
                  "Stranica je učitana, ali struktura tabela nije standardna."
              )
          else:
            st.error(f"Greška pri pristupu sajtu: {response.status_code}")
        except Exception as e:
          st.error(f"Došlo je do greške u parsiranju: {e}")
    else:
      st.warning(f"Sadržaj koda nije link: {qr_data}")
