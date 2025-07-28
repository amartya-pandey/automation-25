import streamlit as st
import json
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pdfrw import PdfReader, PdfWriter, PageMerge
from PIL import Image
from pdf2image import convert_from_path
import tempfile

CONFIG_PATH = "certificate_config.json"

# Sample data - this should match the fields in your config
SAMPLE_DATA = {
    "name": "Sample Name",
    "branch": "Sample Branch",
    "year_of_study": "2025"
}

# Load config
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
        "template_path": "template.pdf"
    }

st.title("Certificate Config Editor")
st.write("Edit field positions, font, and color for your certificates.")

col1, col2 = st.columns([1, 1])

with col1:
    st.write("## Edit Certificate Layout")
    # Template path
    config["template_path"] = st.text_input("Template PDF Path", value=config.get("template_path", "template.pdf"))
    # Title settings
    st.subheader("Title Settings")
    title_cfg = config.get("title", {})
    title_cfg["x"] = st.number_input("Title X Position", value=title_cfg.get("x", 300))
    title_cfg["y"] = st.number_input("Title Y Position", value=title_cfg.get("y", 500))
    title_cfg["font"] = st.text_input("Title Font", value=title_cfg.get("font", "Helvetica-Bold"))
    title_cfg["size"] = st.number_input("Title Font Size", value=title_cfg.get("size", 24))
    title_cfg["color"] = st.color_picker("Title Color", value=title_cfg.get("color", "#000000"))
    config["title"] = title_cfg
    # Field settings
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
        cfg["font"] = st.text_input(f"{field} Font", value=cfg.get("font", "Helvetica"), key=f"{field}_font")
        cfg["size"] = st.number_input(f"{field} Font Size", value=cfg.get("size", 14), key=f"{field}_size")
        cfg["color"] = st.color_picker(f"{field} Color", value=cfg.get("color", "#000000"), key=f"{field}_color")
        config["fields"][field] = cfg
    if st.button("Save Config"):
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        st.success("Config saved!")
    st.write("Edit the config and see the preview on the right.")

# Move preview to sidebar for sticky visibility
with st.sidebar:
    st.write("## Certificate Real-Time Preview")
    def generate_preview_pdf(config, sample_data, output_path):
        try:
            template_path = config.get("template_path", "template.pdf")
            temp_pdf_path = output_path + ".temp.pdf"
            c = canvas.Canvas(temp_pdf_path, pagesize=A4)
            # Draw title
            title_cfg = config.get("title", {})
            c.setFont(title_cfg.get("font", "Helvetica-Bold"), title_cfg.get("size", 24))
            c.setFillColor(title_cfg.get("color", "#000000"))
            c.drawCentredString(title_cfg.get("x", 300), title_cfg.get("y", 500), "CERTIFICATE OF COMPLETION")
            # Draw fields
            for field, cfg in config.get("fields", {}).items():
                value = SAMPLE_DATA.get(field, "")
                c.setFont(cfg.get("font", "Helvetica"), cfg.get("size", 14))
                c.setFillColor(cfg.get("color", "#000000"))
                c.drawCentredString(cfg.get("x", 300), cfg.get("y", 400), f"{field.replace('_', ' ').title()}: {value}")
            c.save()
            # Try to merge with template PDF
            try:
                template_pdf = PdfReader(template_path)
                overlay_pdf = PdfReader(temp_pdf_path)
                if hasattr(template_pdf, 'pages') and hasattr(overlay_pdf, 'pages') and template_pdf.pages and overlay_pdf.pages:
                    for page, overlay_page in zip(template_pdf.pages, overlay_pdf.pages):
                        merger = PageMerge(page)
                        merger.add(overlay_page).render()
                    PdfWriter(output_path, trailer=template_pdf).write()
                    os.remove(temp_pdf_path)
                else:
                    # If template is invalid, just use overlay
                    os.rename(temp_pdf_path, output_path)
            except Exception as merge_err:
                # If template is missing or invalid, just use overlay
                os.rename(temp_pdf_path, output_path)
            return True
        except Exception as e:
            st.error(f"Preview generation failed: {e}")
            return False
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

# Inject custom CSS to set sidebar width to 75%
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        min-width: 60vw !important;
        max-width: 60vw !important;
        width: 60vw !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
