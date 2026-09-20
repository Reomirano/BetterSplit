import streamlit as st
from PIL import Image
import numpy as np
import cv2
from pyzbar.pyzbar import decode
import requests

st.title("Fiskalni QR čitač – Poreska uprava")

uploaded = st.file_uploader("Ubaci sliku fiskalnog QR koda", type=["png", "jpg", "jpeg"])

def read_qr(image):
    try:
        decoded = decode(image)
        if not decoded:
            return None
        return decoded[0].data.decode("utf-8")
    except:
        return None

def fetch_pu(url):
    try:
        r = requests.get(url, timeout=10)
        if "application/json" not in r.headers.get("Content-Type", ""):
            return None
        return r.json()
    except:
        return None

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Učitana slika", use_column_width=True)

    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    qr_text = read_qr(img_cv)

    if not qr_text:
        st.error("QR kod nije moguće očitati.")
    else:
        st.success("QR kod očitan.")
        st.write(qr_text)

        if "http" not in qr_text:
            st.error("QR kod ne sadrži validan PU URL.")
        else:
            st.info("Povlačim podatke sa Poreske uprave...")
            data = fetch_pu(qr_text)

            if not data:
                st.error("PU nije vratila JSON podatke.")
            else:
                items = data.get("items", [])
                if not items:
                    st.warning("PU nije vratila artikle.")
                else:
                    st.success("Artikli učitani.")
                    table = [
                        {
                            "Naziv": item.get("name", ""),
                            "Količina": item.get("quantity", ""),
                            "Cena": item.get("price", "")
                        }
                        for item in items
                    ]
                    st.table(table)
