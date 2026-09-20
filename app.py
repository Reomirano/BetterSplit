import streamlit as st
import cv2
from pyzxing import BarCodeReader
from PIL import Image
import requests

st.title("Fiskalni QR čitač – Poreska uprava")

uploaded = st.file_uploader("Ubaci sliku fiskalnog QR koda", type=["png", "jpg", "jpeg"])

def extract_qr_data(image_path):
    reader = BarCodeReader()
    result = reader.decode(image_path)
    if not result:
        return None
    return result[0]['parsed']

def fetch_pu_data(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

if uploaded:
    img = Image.open(uploaded)
    img.save("temp_qr.png")
    st.image(img, caption="Učitana slika", use_column_width=True)

    qr_text = extract_qr_data("temp_qr.png")

    if not qr_text:
        st.error("QR kod nije pronađen.")
    else:
        st.success("QR kod uspešno očitan.")
        st.write("Sadržaj QR koda:", qr_text)

        if "http" not in qr_text:
            st.error("QR kod ne sadrži validan PU URL.")
        else:
            st.info("Povlačim podatke sa Poreske uprave...")
            data = fetch_pu_data(qr_text)

            if "error" in data:
                st.error("Greška pri komunikaciji sa PU: " + data["error"])
            else:
                items = data.get("items", [])
                if not items:
                    st.warning("PU nije vratila artikle.")
                else:
                    st.success("Podaci uspešno preuzeti.")
                    table = [
                        {"Naziv": i.get("name", ""), "Količina": i.get("quantity", ""), "Cena": i.get("price", "")}
                        for i in items
                    ]
                    st.table(table)
