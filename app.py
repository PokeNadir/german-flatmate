import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF
import io
import os
import tempfile
from pypdf import PdfWriter, PdfReader
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import uuid
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="GermanFlatMate | German Rental Application Generator", page_icon="🇩🇪", layout="centered")

# ==========================================
# ZONE DE CONFIGURATION
# ==========================================
# IMPORTANT : Gumroad exige l'ID spécifique pour votre produit
GUMROAD_PRODUCT_ID = "8Dz3oaoMvtqcLt4Q6967JA=="

GUMROAD_ACCESS_TOKEN = "ULLfWW0d140WMJ2QO5T0x5PB3wySSKfzlyhDVkuOjNo" 
GA_ID = "G-F3PX9QD8EL" 
# ==========================================

# --- GOOGLE ANALYTICS (MÉTHODE INFAILLIBLE) ---
def inject_ga():
    ga_code = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{GA_ID}');
    </script>
    """
    components.html(ga_code, height=0, width=0)

inject_ga()

# --- FONCTION DE VÉRIFICATION DE LICENCE ---
def verify_license(key):
    """Vérifie la licence via l'API Gumroad avec l'ID produit"""
    clean_key = key.strip()
    
    # Backdoor pour vous (toujours utile pour tester sans payer)
    if clean_key == "BERLIN2025": 
        return True
        
    try:
        # CORRECTION : On utilise product_id comme demandé par l'erreur Gumroad
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_id": GUMROAD_PRODUCT_ID,  # <--- CHANGEMENT ICI
                "license_key": clean_key,
                "increment_uses_count": "false"
            },
            headers={"Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN.strip()}"}
        )
        data = response.json()
        
        # En cas d'erreur, on l'affiche pour le debug (vous pourrez retirer ça plus tard)
        if not data.get("success"):
            # On n'affiche le message technique que si ce n'est pas juste "clé invalide"
            if "license_key" not in data.get("message", ""):
                 st.warning(f"Note technique : {data.get('message')}")
        
        if data.get("success") and not data.get("purchase", {}).get("refunded"):
            return True
        else:
            return False
    except Exception:
        return False

# --- CSS ---
st.markdown("""
<style>
    .stButton>button {width: 100%; border-radius: 5px; font-weight: bold;}
    .step-header {font-weight: bold; font-size: 1.1em; margin-top: 15px; margin-bottom: 5px;}
    .arrow-box {
        text-align: center; background-color: #fff3cd; color: #856404;
        padding: 15px; border: 2px solid #ffeeba; border-radius: 10px;
        margin-top: 20px; margin-bottom: 20px; font-weight: bold; font-size: 1.2em;
    }
    .trust-box {
        background-color: #e8f4f8; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #3498db; margin-bottom: 20px; color: #2c3e50;
    }
    .impressum {font-size: 0.8em; color: #666;}
</style>
""", unsafe_allow_html=True)

# --- MEMOIRE ---
if 'pdf_generated' not in st.session_state: st.session_state.pdf_generated = False
if 'final_pdf_bytes' not in st.session_state: st.session_state.final_pdf_bytes = None
if 'email_context' not in st.session_state: st.session_state.email_context = {}
if 'is_premium' not in st.session_state: st.session_state.is_premium = False

# --- HEADER ---
st.title("🇩🇪 GermanFlatMate")
st.markdown("### The Ultimate Apartment Application Tool")

st.markdown("""
<div class="trust-box">
    <strong style="font-size:1.1em;">🔒 100% Private & Secure</strong><br>
    Your files are <strong>never saved</strong> on our systems. They are used once to generate your PDF and are <strong>permanently deleted</strong> the moment you close this tab.
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("💎 Premium Access")
    st.write("Unlock the watermark-free & editable version for **€2.90**.")
    
    # Lien d'achat (On garde le permalink pour l'URL humaine, c'est plus joli)
    st.markdown(f"[👉 **Purchase License Key**](https://germanflatmate.gumroad.com/l/premium)") 
    
    st.write("---")
    input_code = st.text_input("Enter License Key (from email):").strip()
    
    if st.button("Verify Key"):
        if verify_license(input_code):
            st.session_state.is_premium = True
            st.success("✅ License Valid!")
            st.rerun()
        else:
            st.error("❌ Invalid License Key.")
            st.session_state.is_premium = False
            
    if st.session_state.is_premium:
        st.success("Premium Active 🌟")

    st.write("---")
    st.markdown("### ⚖️ Legal & Contact")
    st.markdown("""
    <div class="impressum">
    <strong>Contact:</strong><br>
    info@germanflatmate.com<br><br>
    <strong>Impressum:</strong><br>
    GermanFlatMate is a service provided by the site operator.<br>
    Content responsibility acc. to § 5 TMG.<br>
    </div>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def apply_watermark_diagonal(pdf_obj):
    if not st.session_state.is_premium:
        pdf_obj.set_font("Helvetica", 'B', 40)
        pdf_obj.set_text_color(220, 220, 220)
        pdf_obj.rotate(45, 105, 148)
        text = "DEMO - GermanFlatMate.com"
        width = pdf_obj.get_string_width(text)
        x_start = (210 - width) / 2
        pdf_obj.text(x_start, 148, text)
        pdf_obj.rotate(0)

def convert_to_pdf_bytes(uploaded_file):
    if uploaded_file is None: return None
    if uploaded_file.type == "application/pdf":
        return PdfReader(uploaded_file)
    else:
        try:
            image = Image.open(uploaded_file)
            if image.mode in ("RGBA", "P"): image = image.convert("RGB")
            max_width = 1600
            if image.width > max_width:
                ratio = max_width / float(image.width)
                new_height = int((float(image.height) * float(ratio)))
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            img_pdf = FPDF(); img_pdf.add_page()
