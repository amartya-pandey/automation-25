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
        "template_path": "template.pdf"
    }

st.title("Certificate Config Editor")
st.write("Here can edit the field positions, font, and color for certificates. I'll help preview changes in real time.")

col1, col2 = st.columns([1, 1])

with col1:
    st.write("## Edit Certificate La")
    # can set template PDF path here.
    config["template_path"] = st.text_input("Template PDF Path", value=config.get("template_path", "template.pdf"))
    # Let's let edit the title settings.
    st.subheader("Title Settings")
    title_cfg = config.get("title", {})
    title_cfg["x"] = st.number_input("Title X Position", value=title_cfg.get("x", 300))
    title_cfg["y"] = st.number_input("Title Y Position", value=title_cfg.get("y", 500))
    title_cfg["font"] = st.text_input("Title Font", value=title_cfg.get("font", "Helvetica-Bold"))
    title_cfg["size"] = st.number_input("Title Font Size", value=title_cfg.get("size", 24))
    title_cfg["color"] = st.color_picker("Title Color", value=title_cfg.get("color", "#000000"))
    config["title"] = title_cfg
    # Now can edit each field's settings below.
    st.subheader("Field Settings")
    for field in config["fields"]:
        st.markdown(f"**{field.replace('_', ' ').title()}**")
        cfg = config["fields"][field]
        col_x, col_y = st.columns(2)
        with col_x:
            # Use these controls to move field horizontally.
            cfg["x"] = st.slider(f"{field} X Position (slider)", 0, 600, value=cfg.get("x", 300), key=f"{field}_x_slider")
            cfg["x"] = st.number_input(f"{field} X Position (number)", value=cfg["x"], key=f"{field}_x_num")
        with col_y:
            # Use these controls to move field vertically.
            cfg["y"] = st.slider(f"{field} Y Position (slider)", 0, 850, value=cfg.get("y", 400), key=f"{field}_y_slider")
            cfg["y"] = st.number_input(f"{field} Y Position (number)", value=cfg["y"], key=f"{field}_y_num")
        # Here can set the font, size, and color for this field.
        cfg["font"] = st.text_input(f"{field} Font", value=cfg.get("font", "Helvetica"), key=f"{field}_font")
        cfg["size"] = st.number_input(f"{field} Font Size", value=cfg.get("size", 14), key=f"{field}_size")
        cfg["color"] = st.color_picker(f"{field} Color", value=cfg.get("color", "#000000"), key=f"{field}_color")
        config["fields"][field] = cfg
    # When press this button, I'll save changes to the config file.
    if st.button("Save Config"):
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        st.success("I've saved config!")
    st.write("Edit the config and see the preview on the right.")

# I'm generating a real-time preview of certificate in the sidebar so can see changes instantly.
with st.sidebar:
    st.write("## Certificate Real-Time Preview")
    def generate_preview_pdf(config, sample_data, output_path):
        try:
            template_path = config.get("template_path", "template.pdf")
            temp_pdf_path = output_path + ".temp.pdf"
            c = canvas.Canvas(temp_pdf_path, pagesize=A4)
            # Here, I'm drawing the title and each field on the certificate preview using current settings.
            # I'll draw the title for here.
            title_cfg = config.get("title", {})
            c.setFont(title_cfg.get("font", "Helvetica-Bold"), title_cfg.get("size", 24))
            c.setFillColor(title_cfg.get("color", "#000000"))
            c.drawCentredString(title_cfg.get("x", 300), title_cfg.get("y", 500), "CERTIFICATE OF COMPLETION")
            # Now I'll draw each field using settings.
            for field, cfg in config.get("fields", {}).items():
                value = SAMPLE_DATA.get(field, "")
                c.setFont(cfg.get("font", "Helvetica"), cfg.get("size", 14))
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
