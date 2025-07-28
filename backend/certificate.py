import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from PIL import Image as PILImage
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class CertificateGenerator:
    def __init__(self, template_path: str = None):
        self.template_path = template_path
        self.output_dir = "../generated_certificates"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def parse_excel(self, excel_path: str) -> List[Dict]:
        """Parse Excel file and return list of student records."""
        try:
            df = pd.read_excel(excel_path)
            
            # Normalize column names (handle variations)
            column_mapping = {
                'name': ['name', 'student_name', 'full_name'],
                'email': ['email', 'email_id', 'email_address'],
                'year_of_study': ['year_of_study', 'year', 'academic_year'],
                'branch': ['branch', 'department', 'course']
            }
            
            normalized_columns = {}
            for standard_name, variations in column_mapping.items():
                for col in df.columns:
                    if col.lower().strip() in [v.lower() for v in variations]:
                        normalized_columns[col] = standard_name
                        break
            
            df = df.rename(columns=normalized_columns)
            
            # Validate required columns
            required_cols = ['name', 'email', 'year_of_study', 'branch']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
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
                textColor='darkblue'
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
                f"has successfully completed the requirements for the degree in <b>{student_data['branch']}</b>",
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
