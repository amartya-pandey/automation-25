import streamlit as st
import json
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pdfrw import PdfReader, PdfWriter, PageMerge
from PIL import Image
from pdf2image import convert_from_path
import tempfile
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

CONFIG_PATH = "certificate_config.json"

# Hi! I'm loading the config file here. If it doesn't exist, I'll use a default config for 
# Here is sample data. can change these values to match config fields.
SAMPLE_DATA = {
    "name": "Sample Name",
    "branch": "Sample Branch",
    "year_of_study": "2025"
}

# Let's load config if it exists, or use a default one if it doesn't.
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
else:
    config = {
        "fields": {
            "name": {"x": 300, "y": 450, "font": "Helvetica-Bold", "size": 18, "color": "#000000"},
            "branch": {"x": 300, "y": 420, "font": "Helvetica", "size": 14, "color": "#000000"},
            "year_of_study": {"x": 300, "y": 400, "font": "Helvetica", "size": 14, "color": "#000000"}
        },
        "title": {"x": 300, "y": 500, "font": "Helvetica-Bold", "size": 24, "color": "#000000"},
        "template_path": "frontend/template.pdf"
    }

st.title("Certificate Config Editor")
st.write("Here can edit the field positions, font, and color for certificates. I'll help preview changes in real time.")

col1, col2 = st.columns([1, 1])

CUSTOM_FONTS = [
    ("Helvetica", None),
    ("Helvetica-Bold", None),
    ("Helvetica-Oblique", None),
    ("Times-Roman", None),
    ("Times-Bold", None),
    ("Times-Italic", None),
    ("Courier", None),
    ("Courier-Bold", None),
    ("FrunchySage", None)
]

with col1:
    st.write("## Edit Certificate La")
    config["template_path"] = st.text_input("Template PDF Path", value=config.get("template_path", "template.pdf"))
    st.subheader("Title Settings")
    title_cfg = config.get("title", {})
    title_cfg["x"] = st.number_input("Title X Position", value=title_cfg.get("x", 300))
    title_cfg["y"] = st.number_input("Title Y Position", value=title_cfg.get("y", 500))
    font_options = [f[0] for f in CUSTOM_FONTS]
    title_cfg["font"] = st.selectbox("Title Font", options=font_options, index=font_options.index(title_cfg.get("font", "Helvetica-Bold")) if title_cfg.get("font", "Helvetica-Bold") in font_options else 0)
    title_cfg["size"] = st.number_input("Title Font Size", value=title_cfg.get("size", 24))
    title_cfg["color"] = st.color_picker("Title Color", value=title_cfg.get("color", "#000000"))
    config["title"] = title_cfg
    st.subheader("Field Settings")
    for field in config["fields"]:
        st.markdown(f"**{field.replace('_', ' ').title()}**")
        cfg = config["fields"][field]
        col_x, col_y = st.columns(2)
        with col_x:
            cfg["x"] = st.slider(f"{field} X Position (slider)", 0, 600, value=cfg.get("x", 300), key=f"{field}_x_slider")
            cfg["x"] = st.number_input(f"{field} X Position (number)", value=cfg["x"], key=f"{field}_x_num")
        with col_y:
            cfg["y"] = st.slider(f"{field} Y Position (slider)", 0, 850, value=cfg.get("y", 400), key=f"{field}_y_slider")
            cfg["y"] = st.number_input(f"{field} Y Position (number)", value=cfg["y"], key=f"{field}_y_num")
        cfg["font"] = st.selectbox(f"{field} Font", options=font_options, index=font_options.index(cfg.get("font", "Helvetica")) if cfg.get("font", "Helvetica") in font_options else 0, key=f"{field}_font")
        cfg["size"] = st.number_input(f"{field} Font Size", value=cfg.get("size", 14), key=f"{field}_size")
        cfg["color"] = st.color_picker(f"{field} Color", value=cfg.get("color", "#000000"), key=f"{field}_color")
        config["fields"][field] = cfg
    if st.button("Save Config"):
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        st.success("I've saved config!")
    st.write("Edit the config and see the preview on the right.")

# Inject custom CSS for selected fonts
font_css = "\n".join([css for name, css in CUSTOM_FONTS if css and (config["title"]["font"] == name or any(f["font"] == name for f in config["fields"].values()))])
if font_css:
    st.markdown(f"<style>{font_css}</style>", unsafe_allow_html=True)

# I'm generating a real-time preview of certificate in the sidebar so can see changes instantly.
with st.sidebar:
    st.write("## Certificate Real-Time Preview")
    def generate_preview_pdf(config, sample_data, output_path):
        try:
            # Register custom fonts if present in config
            custom_fonts = config.get("custom_fonts", [])
            for font in custom_fonts:
                try:
                    font_file = os.path.join(os.path.dirname(__file__), font["file"])
                    if os.path.exists(font_file):
                        pdfmetrics.registerFont(TTFont(font["name"], font_file))
                        st.info(f"Successfully registered font: {font['name']}")
                    else:
                        st.error(f"Font file not found: {font_file}")
                except Exception as e:
                    st.error(f"Could not register font {font['name']}: {e}")
            
            # Also register FrunchySage if it's being used but not in config
            frunchy_font_path = os.path.join(os.path.dirname(__file__), "FrunchySage.ttf")
            if os.path.exists(frunchy_font_path):
                try:
                    pdfmetrics.registerFont(TTFont("FrunchySage", frunchy_font_path))
                except Exception as e:
                    st.warning(f"Could not register FrunchySage font: {e}")
            
            template_path = config.get("template_path", "template.pdf")
            temp_pdf_path = output_path + ".temp.pdf"
            c = canvas.Canvas(temp_pdf_path, pagesize=A4)
            # Here, I'm drawing the title and each field on the certificate preview using current settings.
            # I'll draw the title for here.
            title_cfg = config.get("title", {})
            try:
                c.setFont(title_cfg.get("font", "Helvetica-Bold"), title_cfg.get("size", 24))
            except:
                c.setFont("Helvetica-Bold", title_cfg.get("size", 24))
            c.setFillColor(title_cfg.get("color", "#000000"))
            c.drawCentredString(title_cfg.get("x", 300), title_cfg.get("y", 500), "CERTIFICATE OF COMPLETION")
            # Now I'll draw each field using settings.
            for field, cfg in config.get("fields", {}).items():
                value = SAMPLE_DATA.get(field, "")
                try:
                    c.setFont(cfg.get("font", "Helvetica"), cfg.get("size", 14))
                except:
                    c.setFont("Helvetica", cfg.get("size", 14))
                c.setFillColor(cfg.get("color", "#000000"))
                c.drawCentredString(cfg.get("x", 300), cfg.get("y", 400), value)
            c.save()
            # Let's try to merge overlay with the template PDF.
            try:
                template_pdf = PdfReader(template_path)
                overlay_pdf = PdfReader(temp_pdf_path)
                # I check that both PDFs have valid pages before merging.
                if (
                    hasattr(template_pdf, "pages") and isinstance(template_pdf.pages, list) and template_pdf.pages and
                    hasattr(overlay_pdf, "pages") and isinstance(overlay_pdf.pages, list) and overlay_pdf.pages
                ):
                    for page, overlay_page in zip(template_pdf.pages, overlay_pdf.pages):
                        merger = PageMerge(page)
                        merger.add(overlay_page).render()
                    PdfWriter(output_path, trailer=template_pdf).write()
                    os.remove(temp_pdf_path)
                else:
                    # If template is invalid, I'll just use the overlay.
                    os.rename(temp_pdf_path, output_path)
            except Exception as merge_err:
                # If template is missing or invalid, I'll just use the overlay.
                os.rename(temp_pdf_path, output_path)
            return True
        except Exception as e:
            st.error(f"Preview generation failed: {e}")
            return False
    # I'll generate a preview PDF and show it as an image for 
    with tempfile.TemporaryDirectory() as tmpdir:
        preview_pdf_path = os.path.join(tmpdir, "preview_certificate.pdf")
        if generate_preview_pdf(config, SAMPLE_DATA, preview_pdf_path):
            try:
                images = convert_from_path(preview_pdf_path, first_page=1, last_page=1)
                if images:
                    img = images[0]
                    max_width = 900
                    if img.width > max_width:
                        scale = max_width / img.width
                        new_size = (max_width, int(img.height * scale))
                        resample_method = getattr(getattr(Image, 'Resampling', Image), 'LANCZOS', getattr(Image, 'BICUBIC', 3))
                        img = img.resize(new_size, resample=resample_method)
                    st.image(img, caption="Certificate Preview", width=max_width)
            except Exception as e:
                st.error(f"Failed to render PDF preview: {e}")

# I'm resizing the preview image to fit nicely in the sidebar for 
# I'm injecting custom CSS to make the sidebar wider so preview is easier to see.
# I'm setting the sidebar width to 75% so have a big preview area.
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        min-width: 75vw !important;
        max-width: 75vw !important;
        width: 75vw !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
