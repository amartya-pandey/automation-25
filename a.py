import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
from datetime import datetime
from transformers import pipeline
import easyocr
import numpy as np
import cv2
import io
import zipfile
import re
from typing import List, Tuple

# Page config
st.set_page_config(
    page_title="Simple OCR Certificate Generator", 
    layout="centered"
)

st.title("🎓 Simple OCR Certificate Generator")
st.markdown("*Extract names and generate certificates easily*")

# Load models with better error handling
@st.cache_resource
def load_ner_model():
    """Load Hugging Face NER model with error handling"""
    try:
        return pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)
    except Exception as e:
        st.error(f"Failed to load NER model: {str(e)}")
        return None

@st.cache_resource 
def load_ocr_model():
    """Load EasyOCR model with error handling"""
    try:
        # EasyOCR will download models on first run, 'en' for English
        return easyocr.Reader(['en'], gpu=False) 
    except Exception as e:
        st.error(f"Failed to load OCR model: {str(e)}")
        return None

# Initialize models
ner_pipeline = load_ner_model()
ocr_reader = load_ocr_model()

def extract_names_with_ner(text: str, min_score: float = 0.8) -> List[str]:
    """Simple NER-based name extraction"""
    if not ner_pipeline or not text.strip():
        return []
    
    try:
        results = ner_pipeline(text)
        names = []
        
        for entity in results:
            if entity["entity_group"] == "PER" and entity["score"] >= min_score:
                name = entity["word"].replace(' ##', '').strip()
                # Clean up the name
                name = re.sub(r'[^\w\s]', '', name)
                name = ' '.join([word.capitalize() for word in name.split() if word.isalpha()])
                
                if len(name) > 2 and name not in names:
                    names.append(name)
        
        return names
    except Exception as e:
        st.warning(f"NER processing failed: {str(e)}")
        return []

def is_probable_name(line: str, min_words: int = 2, max_words: int = 4) -> bool:
    """Improved heuristic name detection with stricter rules."""
    line = line.strip()
    if not line:
        return False

    words = line.split()

    # Check word count
    if not (min_words <= len(words) <= max_words):
        return False

    # Check if all words start with a capital letter and contain mostly letters
    for word in words:
        if not word.isalpha() or not word[0].isupper():
            return False

    # Filter out common phrases or non-name patterns
    common_non_name_phrases = {
        'this certificate', 'is hereby presented to', 'for successful completion',
        'date of issue', 'signature of', 'program director', 'has successfully',
        'award', 'presented by', 'congratulations', 'achieved', 'hereby certifies'
    }
    if any(phrase in line.lower() for phrase in common_non_name_phrases):
        return False
        
    # Heuristic to check if the line contains a number (often not part of a name)
    if any(char.isdigit() for char in line):
        return False

    return True

def simple_preprocess_image(pil_image: Image.Image) -> np.ndarray:
    """Enhanced image preprocessing for better OCR results."""
    try:
        # Convert to grayscale
        img = np.array(pil_image.convert("L"))

        # Simple resize if image is too small (e.g., width < 800)
        height, width = img.shape
        if width < 800:
            scale = 800 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

        # Apply adaptive thresholding for better text separation
        # This helps in images with uneven lighting
        img = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Optional: Apply a median blur to remove noise, especially speckles
        # Be cautious not to blur too much, which can degrade character edges
        img = cv2.medianBlur(img, 3) # Use a small kernel size like 3

        return img
    except Exception as e:
        st.warning(f"Image preprocessing failed: {str(e)}. Falling back to basic grayscale.")
        return np.array(pil_image.convert("L"))

@st.cache_data
def run_simple_ocr(_pil_image, _ocr_reader_inst, _ner_pipeline_inst, confidence_threshold: float = 0.8) -> Tuple[str, List[str]]:
    """Simplified OCR processing with better error handling and refined name extraction."""
    
    if not _ocr_reader_inst:
        return "", []
    
    try:
        # Preprocess image
        processed_img = simple_preprocess_image(_pil_image)
        
        # Run OCR with basic settings
        ocr_results = _ocr_reader_inst.readtext(processed_img)
        
        if not ocr_results:
            return "No text detected", []
        
        # Extract text from results
        extracted_text_lines = []
        for result in ocr_results:
            if len(result) >= 2:  # Make sure result has text
                text_part = result[1] if isinstance(result[1], str) else str(result[1])
                extracted_text_lines.append(text_part.strip())
        
        extracted_text = " ".join(extracted_text_lines)
        
        if not extracted_text:
            return "No readable text found", []
        
        # Extract names using NER
        ner_names = extract_names_with_ner(extracted_text, min_score=confidence_threshold)
        
        # Extract names using heuristics from lines
        heuristic_names = []
        
        for line in extracted_text_lines: # Iterate through individual lines from OCR
            cleaned_line = re.sub(r'[^\w\s]', '', line).strip() # Initial clean for heuristics
            if is_probable_name(cleaned_line):
                # Ensure each word is capitalized and then join
                formatted_name = ' '.join(word.capitalize() for word in cleaned_line.split() if word.isalpha())
                if formatted_name and len(formatted_name) > 2 and formatted_name not in heuristic_names:
                    heuristic_names.append(formatted_name)
        
        # Combine all found names, remove duplicates, and sort
        all_names = list(set(ner_names + heuristic_names))
        all_names.sort()
        
        return extracted_text, all_names
        
    except Exception as e:
        error_msg = f"OCR processing failed: {str(e)}"
        st.error(error_msg)
        return error_msg, []

def generate_simple_certificate(
    template: Image.Image, 
    name: str, 
    font_size: int, 
    x: int, 
    y: int, 
    font_color: str,
    add_date: bool = True
) -> Image.Image:
    """Simple certificate generation"""
    
    cert = template.copy().convert("RGB")
    draw = ImageDraw.Draw(cert)
    
    # Try to load a font, fallback to default
    try:
        # Use a more common default font if arial.ttf is not found on all systems
        font = ImageFont.truetype("arial.ttf", font_size) 
    except IOError:
        try:
            # Fallback to a common system font, or a bundled font if available
            font = ImageFont.truetype("LiberationSans-Regular.ttf", font_size) # Example common Linux font
        except IOError:
            font = ImageFont.load_default()
            # Try to make it bigger if possible
            if hasattr(font, 'font_variant'):
                try:
                    font = font.font_variant(size=font_size)
                except:
                    pass # Fallback to default size if font_variant fails
    
    # Draw the name
    draw.text((x, y), name, fill=font_color, font=font, anchor="mm")
    
    # Add date if requested
    if add_date:
        date_str = f"Date: {datetime.now().strftime('%B %d, %Y')}"
        try:
            date_font = ImageFont.truetype("arial.ttf", max(16, font_size // 3))
        except IOError:
            try:
                date_font = ImageFont.truetype("LiberationSans-Regular.ttf", max(16, font_size // 3))
            except IOError:
                date_font = font # Fallback to the main font if date font fails
        
        draw.text((x, y + font_size + 15), date_str, fill=font_color, font=date_font, anchor="mm")
    
    return cert

# --- Streamlit UI ---

st.subheader("📄 Step 1: Upload Certificate Template")
template_file = st.file_uploader(
    "Upload your certificate background image", 
    type=["jpg", "jpeg", "png"],
    help="This will be the background for your certificates"
)

st.subheader("📷 Step 2: Upload Image with Names")
uploaded_file = st.file_uploader(
    "Upload image containing names to extract", 
    type=["png", "jpg", "jpeg"],
    help="Upload a clear image with names you want to extract"
)

# Show settings
st.subheader("⚙️ Step 3: Configure Settings")
col1, col2 = st.columns(2)

with col1:
    font_size = st.slider("Font Size", 20, 100, 40)
    font_color = st.color_picker("Font Color", "#000000")

with col2:
    add_date = st.checkbox("Add Date to Certificate", value=True)
    confidence_threshold = st.slider("Name Detection Sensitivity", 0.5, 1.0, 0.8, 
                                     help="Higher = more strict detection for NER model")

# Process if both files are uploaded
if uploaded_file and template_file:
    
    # Check if models loaded
    if not ocr_reader:
        st.error("❌ OCR model failed to load. Please refresh the page.")
        st.stop()
    
    # Display uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", width=400)
    
    # Process the image
    st.subheader("🔍 Step 4: Extract Names")
    
    with st.spinner("Processing image and extracting names..."):
        # Pass confidence_threshold to run_simple_ocr
        extracted_text, found_names = run_simple_ocr(image, ocr_reader, ner_pipeline, confidence_threshold)
    
    # Show results
    st.write("**Extracted Text:**")
    st.text_area("", extracted_text, height=100, disabled=True)
    
    if found_names:
        st.success(f"✅ Found {len(found_names)} potential names!")
        
        st.write("**Detected Names:**")
        selected_names = st.multiselect(
            "Select names to generate certificates for:",
            found_names,
            default=found_names
        )
        
        if selected_names:
            # Position controls
            st.subheader("📍 Step 5: Position Text")
            template_preview = Image.open(template_file)
            template_width, template_height = template_preview.size
            
            col1, col2 = st.columns(2)
            with col1:
                x_pos = st.slider("Horizontal Position", 0, template_width, template_width // 2)
            with col2:
                y_pos = st.slider("Vertical Position", 0, template_height, template_height // 2)
            
            # Show preview
            st.write("**Preview:**")
            preview_cert = generate_simple_certificate(
                template_preview, selected_names[0], font_size, x_pos, y_pos, font_color, add_date
            )
            st.image(preview_cert, caption=f"Preview: {selected_names[0]}", width=500)
            
            # Generate all certificates
            st.subheader("🎓 Step 6: Generate Certificates")
            
            if st.button("Generate All Certificates", type="primary"):
                certificates = {}
                progress_bar = st.progress(0)
                
                for i, name in enumerate(selected_names):
                    # Generate certificate
                    template = Image.open(template_file)
                    cert = generate_simple_certificate(
                        template, name, font_size, x_pos, y_pos, font_color, add_date
                    )
                    
                    # Save to memory
                    img_bytes = io.BytesIO()
                    cert.save(img_bytes, format='PNG')
                    safe_name = re.sub(r'[^\w\s-]', '', name).replace(' ', '_')
                    certificates[f"{safe_name}_certificate.png"] = img_bytes.getvalue()
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(selected_names))
                
                st.success("✅ All certificates generated!")
                
                # Show generated certificates
                st.write("**Generated Certificates:**")
                # Displaying only first few or a sample to avoid UI clutter for many certs
                for i, (filename, cert_data) in enumerate(certificates.items()):
                    if i < 5: # Display max 5 certificates as preview
                        cert_img = Image.open(io.BytesIO(cert_data))
                        name_for_caption = filename.replace('_certificate.png', '').replace('_', ' ')
                        st.image(cert_img, caption=f"Certificate for {name_for_caption}", width=400)
                    else:
                        break # Stop displaying after 5
                if len(certificates) > 5:
                    st.info(f"And {len(certificates) - 5} more certificates generated. Download the ZIP file to see all.")

                # Create download ZIP
                if certificates:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for filename, cert_data in certificates.items():
                            zip_file.writestr(filename, cert_data)
                    
                    st.download_button(
                        label="📥 Download All Certificates (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"certificates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip"
                    )
        else:
            st.info("No names selected for certificate generation.")
    else:
        st.warning("⚠️ No names were detected in the image.")
        st.write("**Tips to improve detection:**")
        st.write("- Use a clearer, higher resolution image")
        st.write("- Ensure names are clearly visible and not handwritten")
        st.write("- Try lowering the 'Name Detection Sensitivity' slider (Step 3)")
        st.write("- Make sure the image contains actual names (not just random text)")

elif not uploaded_file or not template_file:
    st.info("👆 Please upload both files to get started!")

# Add manual name entry option
st.subheader("✍️ Alternative: Manual Name Entry")
st.write("If automatic detection doesn't work, you can manually enter names:")

manual_names_text = st.text_area(
    "Enter names (one per line):",
    placeholder="John Smith\nJane Doe\nMike Johnson",
    height=100
)

if manual_names_text and template_file:
    manual_names = [name.strip() for name in manual_names_text.split('\n') if name.strip()]
    
    if manual_names:
        st.write(f"**Manual names entered:** {len(manual_names)}")
        
        # Use same positioning controls
        template_preview = Image.open(template_file)
        template_width, template_height = template_preview.size
        
        col1, col2 = st.columns(2)
        with col1:
            manual_x = st.slider("Horizontal Position (Manual)", 0, template_width, template_width // 2, key="manual_x")
        with col2:
            manual_y = st.slider("Vertical Position (Manual)", 0, template_height, template_height // 2, key="manual_y")
        
        if st.button("Generate Certificates from Manual Names", type="primary"):
            manual_certificates = {}
            progress_bar = st.progress(0)
            
            for i, name in enumerate(manual_names):
                template = Image.open(template_file)
                cert = generate_simple_certificate(
                    template, name, font_size, manual_x, manual_y, font_color, add_date
                )
                
                img_bytes = io.BytesIO()
                cert.save(img_bytes, format='PNG')
                safe_name = re.sub(r'[^\w\s-]', '', name).replace(' ', '_')
                manual_certificates[f"{safe_name}_certificate.png"] = img_bytes.getvalue()
                
                progress_bar.progress((i + 1) / len(manual_names))
            
            st.success("✅ Manual certificates generated!")
            
            # Show generated certificates
            st.write("**Generated Certificates:**")
            for i, (filename, cert_data) in enumerate(manual_certificates.items()):
                if i < 5: # Display max 5 certificates as preview
                    cert_img = Image.open(io.BytesIO(cert_data))
                    name_for_caption = filename.replace('_certificate.png', '').replace('_', ' ')
                    st.image(cert_img, caption=f"Certificate for {name_for_caption}", width=400)
                else:
                    break # Stop displaying after 5
            if len(manual_certificates) > 5:
                st.info(f"And {len(manual_certificates) - 5} more certificates generated. Download the ZIP file to see all.")

            # Download option
            if manual_certificates:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, cert_data in manual_certificates.items():
                        zip_file.writestr(filename, cert_data)
                
                st.download_button(
                    label="📥 Download Manual Certificates (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"manual_certificates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )

st.markdown("---")
st.markdown("*Simple and reliable certificate generation*")