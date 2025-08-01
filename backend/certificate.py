import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from typing import Dict, List, Optional
from fastapi import FastAPI
from reportlab.lib import colors
import datetime
from backend.logger import get_logger
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pdfrw import PdfReader, PdfWriter, PageMerge
import json

# I'm importing the logger so can use it throughout this file.
logger = get_logger()

class CertificateGenerator:
    def __init__(self, template_path: str = r'./'):
        self.template_path = template_path
        self.output_dir = "../generated_certificates"
        os.makedirs(self.output_dir, exist_ok=True)
        # Register custom fonts from config
        config_path = os.path.join(os.path.dirname(__file__), 'certificate_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            for font in config.get('custom_fonts', []):
                try:
                    font_file = os.path.join(os.path.dirname(__file__), font['file'])
                    pdfmetrics.registerFont(TTFont(font['name'], font_file))
                except Exception as e:
                    logger.error(f"Failed to register font {font['name']}: {e}")
    
    def parse_excel_csv(self, excel_path: str) -> List[Dict]:
        """Parse Excel or CSV file and return list of student records."""
        try:
            logger.info(f"Attempting to parse file: {excel_path}")
            
            # Check if file exists and get basic info
            if not os.path.exists(excel_path):
                raise FileNotFoundError(f"File not found: {excel_path}")
            
            file_size = os.path.getsize(excel_path)
            logger.info(f"File size: {file_size} bytes")
            
            # Determine file type and read accordingly
            if excel_path.lower().endswith('.csv'):
                logger.info("Reading as CSV file")
                df = pd.read_csv(excel_path)
            else:
                logger.info("Reading as Excel file")
                # For Excel files, try different engines if one fails
                try:
                    df = pd.read_excel(excel_path, engine='openpyxl')
                except Exception as openpyxl_error:
                    logger.error(f"Failed with openpyxl engine: {openpyxl_error}")
                    try:
                        df = pd.read_excel(excel_path, engine='xlrd')
                    except Exception as xlrd_error:
                        logger.error(f"Failed with xlrd engine: {xlrd_error}")
                        # If it's truly corrupted, raise a clear error
                        raise ValueError(f"Cannot read Excel file. File may be corrupted. Original errors: openpyxl: {openpyxl_error}, xlrd: {xlrd_error}")
            
            logger.info(f"Successfully read file with {len(df)} rows and {len(df.columns)} columns")
            
            # Normalize column names (handle variations and formatting)
            df.columns = [col.lower().replace(" ", "_").strip() for col in df.columns]
            column_mapping = {
                'name': ['name', 'student_name', 'full_name'],
                'email': ['email', 'email_id', 'email_address'],
                'year_of_study': ['year_of_study', 'year', 'academic_year'],
                'branch': ['branch', 'department', 'course']
            }
            normalized_columns = {}
            for standard_name, variations in column_mapping.items():
                for col in df.columns:
                    if col in [v.lower().replace(" ", "_").strip() for v in variations]:
                        normalized_columns[col] = standard_name
                        break
            df = df.rename(columns=normalized_columns)
            
            # Validate required columns
            required_cols = ['name', 'email', 'year_of_study', 'branch']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}. Accepted variations: {column_mapping}")
            
            # Convert to list of dictionaries
            students = df[required_cols].to_dict('records')
            
            # Clean data
            for student in students:
                for key, value in student.items():
                    if pd.isna(value):
                        student[key] = ""
                    else:
                        student[key] = str(value).strip()
            
            logger.info(f"Successfully parsed {len(students)} student records")
            return students
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {e}")
            raise
    
    def generate_certificate_pdf(self, student_data: Dict, output_path: str) -> str:
        """Generate a certificate PDF for a single student."""
        try:
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=18,
                spaceAfter=20,
                alignment=TA_CENTER
            )
            
            content_style = ParagraphStyle(
                'CustomContent',
                parent=styles['Normal'],
                fontSize=14,
                spaceAfter=15,
                alignment=TA_CENTER
            )
            
            # Certificate content
            story.append(Spacer(1, 50))
            story.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
            story.append(Spacer(1, 30))
            
            story.append(Paragraph("This is to certify that", content_style))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph(f"<b>{student_data['name']}</b>", subtitle_style))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph(
                f"has successfully completed the seminar on AI/ML <b>{student_data['branch']}</b>",
                content_style
            ))
            story.append(Spacer(1, 15))
            
            story.append(Paragraph(
                f"in the year <b>{student_data['year_of_study']}</b>",
                content_style
            ))
            story.append(Spacer(1, 40))
            
            story.append(Paragraph("Congratulations on this achievement!", content_style))
            story.append(Spacer(1, 60))
            
            # Signature section
            story.append(Paragraph("_____________________", content_style))
            story.append(Paragraph("Authorized Signature", content_style))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Certificate generated for {student_data['name']}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating certificate for {student_data['name']}: {e}")
            raise
    
    def generate_all_certificates(self, students: List[Dict]) -> List[str]:
        """Generate certificates for all students."""
        generated_files = []
        
        for i, student in enumerate(students):
            try:
                # Create filename
                safe_name = "".join(c for c in student['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"certificate_{safe_name}_{i+1}.pdf"
                output_path = os.path.join(self.output_dir, filename)
                
                # Generate certificate
                self.generate_certificate_pdf(student, output_path)
                generated_files.append(output_path)
                
            except Exception as e:
                logger.error(f"Failed to generate certificate for student {i+1}: {e}")
                continue
        
        return generated_files
    
    def generate_all_certificates_with_config(self, students: List[Dict]) -> List[str]:
        """Generate certificates for all students using configuration-based layout."""
        generated_files = []
        
        for i, student in enumerate(students):
            try:
                # Create filename
                safe_name = "".join(c for c in student['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"certificate_{safe_name}_{i+1}.pdf"
                output_path = os.path.join(self.output_dir, filename)
                
                # Generate certificate using config
                self.generate_certificate_with_config(student, output_path)
                generated_files.append(output_path)
                
            except Exception as e:
                logger.error(f"Failed to generate config-based certificate for student {i+1}: {e}")
                continue
        
        return generated_files
    
    def generate_certificate_with_config(self, student_data: Dict, output_path: str, config_path: Optional[str] = None) -> str:
        """Generate a certificate PDF using the configuration file for layout and styling."""
        try:
            # Load configuration
            if config_path is None:
                config_path = os.path.join(os.path.dirname(__file__), 'certificate_config.json')
            
            if not os.path.exists(config_path):
                logger.warning(f"Config file not found: {config_path}, falling back to default method")
                return self.generate_certificate_pdf(student_data, output_path)
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Create canvas for PDF
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from pdfrw import PdfReader, PdfWriter, PageMerge
            
            temp_pdf_path = output_path + ".temp.pdf"
            c = canvas.Canvas(temp_pdf_path, pagesize=A4)
            
            # Register any additional custom fonts (they're already registered in __init__)
            for font in config.get('custom_fonts', []):
                try:
                    font_file = os.path.join(os.path.dirname(__file__), font['file'])
                    if os.path.exists(font_file):
                        pdfmetrics.registerFont(TTFont(font['name'], font_file))
                except Exception as e:
                    logger.warning(f"Could not register font {font['name']}: {e}")
            
            # Draw title if configured
            title_cfg = config.get("title", {})
            if title_cfg.get("x") and title_cfg.get("y"):
                try:
                    c.setFont(title_cfg.get("font", "Helvetica-Bold"), title_cfg.get("size", 24))
                except:
                    logger.warning(f"Font {title_cfg.get('font')} not available, using Helvetica-Bold")
                    c.setFont("Helvetica-Bold", title_cfg.get("size", 24))
                
                c.setFillColor(title_cfg.get("color", "#000000"))
                c.drawCentredString(title_cfg.get("x", 300), title_cfg.get("y", 500), "CERTIFICATE OF COMPLETION")
            
            # Draw each configured field
            fields_config = config.get("fields", {})
            for field_name, field_cfg in fields_config.items():
                value = student_data.get(field_name, "")
                if value and field_cfg.get("x") and field_cfg.get("y"):
                    try:
                        c.setFont(field_cfg.get("font", "Helvetica"), field_cfg.get("size", 14))
                    except:
                        logger.warning(f"Font {field_cfg.get('font')} not available, using Helvetica")
                        c.setFont("Helvetica", field_cfg.get("size", 14))
                    
                    c.setFillColor(field_cfg.get("color", "#000000"))
                    c.drawCentredString(field_cfg.get("x", 300), field_cfg.get("y", 400), str(value))
            
            c.save()
            
            # Try to merge with template if available
            template_path = config.get("template_path", "template.pdf")
            if template_path and os.path.exists(template_path):
                try:
                    template_pdf = PdfReader(template_path)
                    overlay_pdf = PdfReader(temp_pdf_path)
                    
                    if (hasattr(template_pdf, "pages") and isinstance(template_pdf.pages, list) and template_pdf.pages and
                        hasattr(overlay_pdf, "pages") and isinstance(overlay_pdf.pages, list) and overlay_pdf.pages):
                        
                        for page, overlay_page in zip(template_pdf.pages, overlay_pdf.pages):
                            merger = PageMerge(page)
                            merger.add(overlay_page).render()
                        
                        PdfWriter(output_path, trailer=template_pdf).write()
                        os.remove(temp_pdf_path)
                    else:
                        os.rename(temp_pdf_path, output_path)
                except Exception as merge_err:
                    logger.warning(f"Template merge failed: {merge_err}, using overlay only")
                    os.rename(temp_pdf_path, output_path)
            else:
                os.rename(temp_pdf_path, output_path)
            
            logger.info(f"Config-based certificate generated for {student_data['name']}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating config-based certificate for {student_data['name']}: {e}")
            raise

app = FastAPI()
