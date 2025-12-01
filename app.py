import streamlit as st
from fpdf import FPDF
import io
import os
import tempfile
from pypdf import PdfWriter, PdfReader
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import uuid
import requests # Pour parler à Gumroad

# --- CONFIGURATION ---
st.set_page_config(page_title="GermanFlatMate Pro", page_icon="🇩🇪", layout="centered")

# --- CONFIGURATION GUMROAD (A REMPLIR) ---
# Le "Permalink" est la fin de votre URL Gumroad. 
# Si votre lien est https://gumroad.com/l/azerty, alors le permalink est "azerty"
GUMROAD_PRODUCT_PERMALINK = "germanflatmatepremium" 

# Le Token que vous avez généré dans Settings > Advanced
# Dans un vrai projet, on cache ça dans st.secrets, mais pour démarrer mettez le ici.
GUMROAD_ACCESS_TOKEN = "ULLfWW0d140WMJ2QO5T0x5PB3wySSKfzlyhDVkuOjNo" 

# --- FONCTION DE VÉRIFICATION DE LICENCE (MODE DEBUG) ---
def verify_license(key):
    """Version temporaire pour afficher les erreurs à l'écran"""
    
    # Nettoyage de la clé (enlève les espaces invisibles avant/après)
    clean_key = key.strip()
    
    st.info(f"⏳ Vérification de la clé : {clean_key}...")
    st.info(f"🔗 Produit visé : {GUMROAD_PRODUCT_PERMALINK}")
    
    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_permalink": GUMROAD_PRODUCT_PERMALINK,
                "license_key": clean_key,
                "increment_uses_count": "false"
            },
            # On retire l'espace éventuel dans le token aussi
            headers={"Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN.strip()}"}
        )
        
        data = response.json()
        
        # --- LE MOUCHARD : AFFICHER LA RÉPONSE DE GUMROAD ---
        st.write("🔴 RÉPONSE BRUTE DE GUMROAD (Lisez ceci) :")
        st.json(data)
        # ----------------------------------------------------
        
        if data.get("success") and not data.get("purchase", {}).get("refunded"):
            return True
        else:
            return False
            
    except Exception as e:
        st.error(f"Erreur technique de connexion : {e}")
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

# --- SIDEBAR (MONÉTISATION VIA GUMROAD) ---
with st.sidebar:
    st.header("💎 Premium Access")
    st.write("Unlock the watermark-free & editable version for **€9.90**.")
    
    # LIEN VERS VOTRE PAGE GUMROAD
    gumroad_link = f"https://gumroad.com/l/{GUMROAD_PRODUCT_PERMALINK}"
    st.markdown(f"[👉 **Purchase License Key**]({gumroad_link})") 
    
    st.write("---")
    input_code = st.text_input("Enter License Key (from email):").strip()
    
    if st.button("Verify Key"):
        if verify_license(input_code):
            st.session_state.is_premium = True
            st.success("✅ License Valid! Premium Unlocked.")
        else:
            st.error("❌ Invalid License Key.")
            st.session_state.is_premium = False
            
    if st.session_state.is_premium:
        st.success("You are in Premium Mode")

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
            # Compression
            max_width = 1600
            if image.width > max_width:
                ratio = max_width / float(image.width)
                new_height = int((float(image.height) * float(ratio)))
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            img_pdf = FPDF(); img_pdf.add_page()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                image.save(tmp_file.name, format='JPEG', quality=75, optimize=True)
                tmp_path = tmp_file.name

            try:
                img_pdf.image(tmp_path, x=10, y=10, w=190)
            finally:
                if os.path.exists(tmp_path): os.unlink(tmp_path)
            
            apply_watermark_diagonal(img_pdf)
            return PdfReader(io.BytesIO(bytes(img_pdf.output())))
        except Exception: return None

# --- DICTIONNAIRES ---
jobs_mapping = {
    "Software Engineer": "Softwareentwickler", "Student": "Student", "Project Manager": "Projektmanager",
    "Data Scientist": "Data Scientist", "Marketing Manager": "Marketing Manager", "Consultant": "Unternehmensberater",
    "Teacher": "Lehrer", "Doctor (Medical)": "Arzt", "Nurse": "Krankenpfleger", "Architect": "Architekt",
    "Designer": "Designer", "Sales Manager": "Vertriebsleiter", "Accountant": "Buchhalter",
    "Engineer (General)": "Ingenieur", "Researcher": "Forscher", "Other": "Other"
}
german_mapping = {"Single": "Ledig", "Married": "Verheiratet", "Partnership": "Lebensgemeinschaft", "Yes": "Ja", "No": "Nein"}

# === INPUTS ===
st.subheader("1️⃣ Personal Details")
col1, col2 = st.columns(2)
with col1:
    full_name = st.text_input("Full Name", placeholder="Jean Dupont")
    selected_job = st.selectbox("Profession", list(jobs_mapping.keys()))
    custom_job = ""
    if selected_job == "Other": custom_job = st.text_input("Profession in German", placeholder="Bäcker")
    move_in_date = st.date_input("Desired Move-in Date")
with col2:
    income = st.number_input("Net Monthly Income (€)", min_value=0, value=2500)
    family_status = st.selectbox("Marital Status", ["Single", "Married", "Partnership"])
    st.caption("Includes you, partner, and kids.")
    people_count = st.number_input("Total people", min_value=1, value=1)

st.subheader("2️⃣ Legal Questions")
c1, c2 = st.columns(2)
with c1:
    smoker = st.radio("Smoker?", ["No", "Yes"], horizontal=True)
    pets = st.radio("Pets?", ["No", "Yes"], horizontal=True)
with c2:
    insolvency = st.radio("Insolvency?", ["No", "Yes"], horizontal=True)
    eviction = st.radio("Evictions?", ["No", "Yes"], horizontal=True)

st.subheader("3️⃣ Documents")
no_schufa_mode = st.checkbox("I am new to Germany (No SCHUFA).")
u_income = st.file_uploader("Proof of Income", type=["pdf", "jpg", "png"], accept_multiple_files=True)
u_id = st.file_uploader("ID Copy", type=["pdf", "jpg", "png"], accept_multiple_files=True)
u_schufa = None
if not no_schufa_mode:
    u_schufa = st.file_uploader("SCHUFA", type=["pdf", "jpg", "png"], accept_multiple_files=True)

st.subheader("4️⃣ Signature")
st.caption("Please sign below (required):")
canvas_result = st_canvas(stroke_width=2, stroke_color="#000000", background_color="#ffffff", height=150, width=400, drawing_mode="freedraw", key="canvas")

st.markdown("---")
agree_terms = st.checkbox("I confirm that all provided information is true. GermanFlatMate is a tool and assumes no liability for the accuracy of the generated documents.")

generate_click = st.button("🚀 GENERATE APPLICATION PACKAGE", type="primary")

# === GENERATION ===
if generate_click:
    if not full_name:
        st.error("⚠️ Please enter your full name.")
    elif canvas_result.image_data is None:
        st.error("⚠️ Please sign the document.")
    elif not agree_terms:
        st.error("⚠️ You must confirm that the information is true to proceed.")
    else:
        job_de = custom_job if (selected_job == "Other" and custom_job) else jobs_mapping.get(selected_job, "Angestellter")
        
        class PDF(FPDF):
            def header(self):
                self.set_fill_color(0, 51, 102)
                self.rect(0, 0, 210, 30, 'F')
                self.set_text_color(255, 255, 255); self.set_font('Helvetica', 'B', 20); self.set_y(10)
                self.cell(0, 10, 'Bewerbungsmappe', ln=True, align='C'); self.ln(20)
                apply_watermark_diagonal(self)

        pdf = PDF(); pdf.add_page()
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", '', 11)
        pdf.multi_cell(0, 6, f"Sehr geehrte Damen und Herren,\n\nhiermit bewerbe ich mich ({full_name}) verbindlich fuer die Wohnung. Anbei finden Sie meine vollstaendigen Unterlagen.", align='L')
        pdf.ln(5)
        
        pdf.set_text_color(0, 51, 102); pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 8, "1. Angaben zur Person (Personal Details)", ln=1)
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", '', 11)
        def add_row(l, v):
            pdf.set_font("Helvetica", 'B', 11); pdf.cell(80, 7, l, border=0)
            pdf.set_font("Helvetica", '', 11); pdf.cell(0, 7, str(v), ln=1, border=0)
        
        add_row("Name:", full_name); add_row("Beruf:", job_de)
        add_row("Nettoeinkommen:", f"{income} EUR / Monat"); add_row("Familienstand:", german_mapping[family_status])
        add_row("Einziehende Personen:", str(people_count)); add_row("Einzugstermin:", move_in_date.strftime("%d.%m.%Y"))
        pdf.ln(5)
        
        pdf.set_text_color(0, 51, 102); pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 8, "2. Weitere Angaben (Legal Declarations)", ln=1)
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", '', 11)
        add_row("Raucher:", german_mapping[smoker]); add_row("Haustiere:", german_mapping[pets])
        add_row("Insolvenzverfahren:", german_mapping[insolvency]); add_row("Mietschulden:", german_mapping[eviction])
        pdf.ln(10)
        
        pdf.set_font("Helvetica", '', 10); pdf.multi_cell(0, 5, "Ich bestaetige, dass die oben gemachten Angaben wahrheitsgemaess sind."); pdf.ln(5)
        
        if canvas_result.image_data is not None:
            sign_img = Image.fromarray(canvas_result.image_data.astype('uint8'))
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_sign:
                sign_img.save(tmp_sign.name, format="PNG")
                tmp_sign_path = tmp_sign.name
            try:
                pdf.image(tmp_sign_path, x=10, w=50)
            finally:
                if os.path.exists(tmp_sign_path): os.unlink(tmp_sign_path)
            pdf.cell(0, 5, "Unterschrift", ln=1)
        
        master = bytes(pdf.output())
        merger = PdfWriter(); merger.append(io.BytesIO(master))
        
        if no_schufa_mode:
            p2 = FPDF(); p2.add_page()
            p2.set_fill_color(0, 51, 102); p2.rect(0, 0, 210, 30, 'F')
            p2.set_text_color(255, 255, 255); p2.set_font("Helvetica", 'B', 20); p2.set_y(10)
            p2.cell(0, 10, 'Bonitaet (Credit Score)', ln=True, align='C'); p2.ln(25)
            apply_watermark_diagonal(p2)
            p2.set_text_color(0, 0, 0); p2.set_font("Helvetica", '', 12)
            p2.multi_cell(0, 7, f"Da ich neu in Deutschland bin, habe ich noch keine SCHUFA.\nAnbei meine Einkommensnachweise.\n\n{full_name}")
            merger.append(io.BytesIO(bytes(p2.output())))
        
        def add_files(files):
            if files:
                for f in files:
                    p = convert_to_pdf_bytes(f)
                    if p: merger.append(p)
        add_files(u_income)
        if not no_schufa_mode: add_files(u_schufa)
        add_files(u_id)
        
        if not st.session_state.is_premium:
            owner_pwd = str(uuid.uuid4())
            merger.encrypt("", owner_pwd)

        buf = io.BytesIO(); merger.write(buf)
        st.session_state.final_pdf_bytes = buf.getvalue()
        st.session_state.pdf_generated = True
        st.session_state.email_context = {"name": full_name}
        st.balloons()

# === RESULTATS ===
if st.session_state.pdf_generated:
    st.markdown("---")
    
    if not st.session_state.is_premium:
        st.warning("⚠️ **DEMO MODE:** Your PDF is locked and watermarked. Buy Premium to remove restrictions.")
    else:
        st.success("✅ **PREMIUM MODE:** Clean & Unlocked PDF generated!")
        
    clean_name = st.session_state.email_context["name"].replace(" ", "_")
    
    st.download_button(
        label="⬇️ Download PDF (Bewerbungsmappe)",
        data=st.session_state.final_pdf_bytes,
        file_name=f"Bewerbung_{clean_name}.pdf",
        mime="application/pdf"
    )

    st.markdown("""
    <div class="arrow-box">
        👇 WAIT! DON'T CLOSE YET! 👇<br>
        Scroll down to get your Email Text
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📧 Step 2: Send the Email")
    
    st.info("""
    **🇬🇧 English Translation:**
    "Dear Sir/Madam, Thank you for the opportunity to apply. I am very interested. 
    Attached is my complete dossier (Self-disclosure, Income proof, ID). 
    Sincerely, [Your Name]"
    """)

    st.markdown('<p class="step-header">1. Copy Subject Line (Betreff)</p>', unsafe_allow_html=True)
    st.code(f"Bewerbung für die Wohnung - {st.session_state.email_context['name']}", language="text")

    st.markdown('<p class="step-header">2. Copy Message Body</p>', unsafe_allow_html=True)
    email_body = f"""Sehr geehrte Damen und Herren,

vielen Dank für die Möglichkeit, mich für diese Wohnung zu bewerben.
Ich habe großes Interesse an dem Objekt.

Im Anhang finden Sie meine vollständige Bewerbungsmappe (als einzelne PDF-Datei), inklusive:
- Mieterselbstauskunft
- Einkommensnachweise
- Identitätsnachweis

Für Rückfragen stehe ich Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen,
{st.session_state.email_context['name']}"""
    st.code(email_body, language="text")



