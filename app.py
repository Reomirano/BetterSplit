import streamlit as st
import cv2
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
from PIL import Image
import re

st.set_page_config(page_title="SUF Skener Računa", layout="centered")

# Inicijalizacija WeChat QR skenera unutar OpenCV-a (izuzetno lagan i precizan)
@st.cache_resource
def load_qr_detector():
    # WeChat QRdetektor zahteva dva mala modela koja dolaze uz opencv-contrib
    detector = cv2.wechat_qrcode_WeChatQRCode(
        "detect.prototxt", "detect.caffemodel",
        "sr_sr.prototxt", "sr_sr.caffemodel"
    )
    return detector

def extract_receipt_data(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = []
        item_rows = soup.find_all("div", class_=re.compile("row.*item.*", re.IGNORECASE)) 
        
        tables = soup.find_all("table")
        if tables:
            df_list = pd.read_html(str(tables[0]))
            if df_list:
                return df_list[0]
                
        for row in item_rows:
            name = row.find(class_=re.compile("name", re.IGNORECASE))
            qty = row.find(class_=re.compile("quantity", re.IGNORECASE))
            price = row.find(class_=re.compile("price", re.IGNORECASE))
            
            if name and price:
                items.append({
                    "Naziv": name.get_text(strip=True),
                    "Količina": qty.get_text(strip=True) if qty else "1",
                    "Iznos": price.get_text(strip=True)
                })
                
        if not items:
             st.warning("Uspelo je očitavanje linka, ali nismo pronašli artikle na stranici. HTML struktura Poreske uprave se možda promenila.")
             return pd.DataFrame()
             
        return pd.DataFrame(items)

    except Exception as e:
        st.error(f"Greška pri preuzimanju podataka sa sajta: {e}")
        return pd.DataFrame()

def process_image(image_file):
    image = Image.open(image_file)
    img_array = np.array(image)
    
    if len(img_array.shape) > 2 and img_array.shape[2] == 4:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
    img_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    with st.spinner("Skeniranje QR koda..."):
        # Pokušaj očitavanja preko OpenCV WeChat skenera
        detector = cv2.wechat_qrcode_WeChatQRCode()
        decoded_texts, points = detector.detectAndDecode(img_cv2)
        
    if not decoded_texts or decoded_texts[0] == "":
        st.error("QR kod nije pronađen ili je previše oštećen. Pokušaj sa boljim osvetljenjem.")
        return
        
    url = decoded_texts[0]
    st.success("QR Kod uspešno očitan!")
    st.info(f"Link: {url}")
    
    if "suf.purs.gov.rs" in url:
        with st.spinner("Preuzimanje podataka sa sajta Poreske uprave..."):
            df = extract_receipt_data(url)
            if not df.empty:
                st.subheader("Stavke sa računa")
                st.dataframe(df, use_container_width=True)
    else:
        st.warning("Očitani kod ne vodi na sajt Poreske uprave (suf.purs.gov.rs).")

st.title("🧾 SUF Skener Fiskalnih Računa")
st.write("Skeniraj ili otpremi sliku fiskalnog računa.")

tab1, tab2 = st.tabs(["📸 Kamera", "📁 Upload Slike"])

with tab1:
    camera_img = st.camera_input("Slikaj QR kod sa računa")
    if camera_img is not None:
        process_image(camera_img)

with tab2:
    uploaded_img = st.file_uploader("Otpremi sliku računa", type=['png', 'jpg', 'jpeg'])
    if uploaded_img is not None:
        process_image(uploaded_img)
