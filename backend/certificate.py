import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from typing import Dict, List
import logging
from fastapi import FastAPI
from reportlab.lib import colors
from pdfrw import PdfReader, PdfWriter, PageMerge
import json

logger = logging.getLogger(__name__)

class CertificateGenerator:
    def __init__(self, template_path: str = ''):
        self.template_path = template_path
        self.output_dir = "../generated_certificates"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def parse_excel(self, excel_path: str) -> List[Dict]:
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
    
    def load_config(self, config_path: str = "certificate_config.json") -> dict:
        """Load certificate layout config from JSON file."""
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

    def preview_certificate(self, student_data: Dict, config: dict, output_path: str) -> str:
        """Generate a preview certificate using config settings."""
        try:
            template_path = config.get("template_path", self.template_path or "template.pdf")
            template_pdf = PdfReader(template_path)
            temp_pdf_path = output_path + ".temp.pdf"
            c = canvas.Canvas(temp_pdf_path, pagesize=A4)
            # Draw title
            title_cfg = config.get("title", {})
            c.setFont(title_cfg.get("font", "Helvetica-Bold"), title_cfg.get("size", 24))
            c.setFillColor(title_cfg.get("color", "#000000"))
            c.drawCentredString(title_cfg.get("x", 300), title_cfg.get("y", 500), "CERTIFICATE OF COMPLETION")
            # Draw fields
            for field, cfg in config.get("fields", {}).items():
                value = student_data.get(field, "")
                c.setFont(cfg.get("font", "Helvetica"), cfg.get("size", 14))
                c.setFillColor(cfg.get("color", "#000000"))
                c.drawCentredString(cfg.get("x", 300), cfg.get("y", 400), value)
            c.save()
            overlay_pdf = PdfReader(temp_pdf_path)
            for page, overlay_page in zip(template_pdf.pages, overlay_pdf.pages):
                merger = PageMerge(page)
                merger.add(overlay_page).render()
            PdfWriter(output_path, trailer=template_pdf).write()
            os.remove(temp_pdf_path)
            logger.info(f"Preview certificate generated for {student_data['name']}")
            return output_path
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            raise

    def generate_certificate_pdf(self, student_data: Dict, output_path: str, config_path: str = "certificate_config.json") -> str:
        """Generate a certificate PDF for a single student using config layout."""
        try:
            config = self.load_config(config_path)
            return self.preview_certificate(student_data, config, output_path)
        except Exception as e:
            logger.error(f"Error generating certificate for {student_data['name']}: {e}")
            raise

    def generate_all_certificates(self, students: List[Dict], config_path: str = "certificate_config.json") -> List[str]:
        """Generate certificates for all students using config layout."""
        generated_files = []
        config = self.load_config(config_path)
        for i, student in enumerate(students):
            try:
                safe_name = "".join(c for c in student['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"certificate_{safe_name}_{i+1}.pdf"
                output_path = os.path.join(self.output_dir, filename)
                self.preview_certificate(student, config, output_path)
                generated_files.append(output_path)
            except Exception as e:
                logger.error(f"Failed to generate certificate for student {i+1}: {e}")
                continue
        return generated_files

app = FastAPI()
