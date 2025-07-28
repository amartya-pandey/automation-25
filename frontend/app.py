import streamlit as st
import requests
import pandas as pd
import time
import os
from typing import Optional

# Page configuration
st.set_page_config(
    page_title="Auto-Certy - Certificate Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL
API_BASE_URL = "http://localhost:8000"

def upload_files(excel_file, template_file=None):
    """Upload files to the backend."""
    try:
        files = {"excel_file": (excel_file.name, excel_file, "application/octet-stream")}
        if template_file:
            files["template_file"] = (template_file.name, template_file, "application/pdf")
        
        response = requests.post(f"{API_BASE_URL}/upload-files", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error uploading files: {e}")
        return None

def start_processing(task_id, email_config):
    """Start the certificate processing."""
    try:
        data = {
            "task_id": task_id,
            "sender_email": email_config["sender_email"],
            "sender_password": email_config["sender_password"],
            "email_subject": email_config["email_subject"],
            "email_body": email_config["email_body"],
            "smtp_server": email_config["smtp_server"],
            "smtp_port": email_config["smtp_port"]
        }
        
        response = requests.post(f"{API_BASE_URL}/process-certificates", data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error starting processing: {e}")
        return None

def get_status(task_id):
    """Get processing status."""
    try:
        response = requests.get(f"{API_BASE_URL}/status/{task_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting status: {e}")
        return None

def cleanup_task(task_id):
    """Clean up task files."""
    try:
        response = requests.delete(f"{API_BASE_URL}/cleanup/{task_id}")
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error cleaning up: {e}")
        return False

def main():
    st.title("🎓 Auto-Certy")
    st.markdown("### Automated College Certificate Generator & Mailer")
    
    # Check backend connection
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code != 200:
            st.error("⚠️ Backend server is not responding. Please ensure the FastAPI server is running on port 8000.")
            st.stop()
    except:
        st.error("⚠️ Cannot connect to backend server. Please ensure the FastAPI server is running on port 8000.")
        st.stop()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Upload & Process", "View Status", "Help"])
    
    if page == "Upload & Process":
        upload_and_process_page()
    elif page == "View Status":
        view_status_page()
    else:
        help_page()

def upload_and_process_page():
    st.header("📤 Upload Files & Configure Email")

    with st.form("upload_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Student Data")
            excel_file = st.file_uploader(
                "Upload Excel or CSV file with student data",
                type=['xlsx', 'xls', 'csv'],
                help="File should contain columns: Name, Email, Year of Study, Branch"
            )
            df = None
            if excel_file:
                try:
                    if excel_file.name.lower().endswith('.csv'):
                        df = pd.read_csv(excel_file)
                    else:
                        df = pd.read_excel(excel_file)
                    st.success(f"✅ File loaded: {len(df)} records found")
                    with st.expander("Preview Data"):
                        st.dataframe(df.head())
                    expected_cols = ['name', 'email', 'year_of_study', 'branch']
                    df_cols_lower = [col.lower().strip() for col in df.columns]
                    missing_info = []
                    for col in expected_cols:
                        variations = {
                            'name': ['name', 'student_name', 'full_name'],
                            'email': ['email', 'email_id', 'email_address'],
                            'year_of_study': ['year_of_study', 'year', 'academic_year'],
                            'branch': ['branch', 'department', 'course']
                        }
                        if not any(var in df_cols_lower for var in variations[col]):
                            missing_info.append(f"No column found for '{col}'. Expected variations: {', '.join(variations[col])}")
                    if missing_info:
                        st.warning("⚠️ Column validation issues:")
                        for issue in missing_info:
                            st.write(f"- {issue}")
                    else:
                        st.success("✅ All required columns found!")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
        with col2:
            st.subheader("📄 Certificate Template (Optional)")
            template_file = st.file_uploader(
                "Upload certificate template (PDF)",
                type=['pdf'],
                help="Optional: Upload a PDF template. If not provided, a default template will be used."
            )
            if template_file:
                st.success("✅ Template file uploaded")
            else:
                st.info("ℹ️ Using default certificate template")
        st.header("📧 Email Configuration")
        with st.expander("Email Settings", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                sender_email = st.text_input(
                    "Sender Email Address",
                    placeholder="your-email@gmail.com",
                    help="Email address that will send the certificates"
                )
                sender_password = st.text_input(
                    "Email Password",
                    type="password",
                    help="For Gmail, use App Password instead of regular password"
                )
                smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
                smtp_port = st.number_input("SMTP Port", value=587)
            with col2:
                email_subject = st.text_input(
                    "Email Subject",
                    value="Your Certificate",
                    help="Subject line for the certificate emails"
                )
                email_body = st.text_area(
                    "Email Body Template",
                    value="Dear {name},\n\nCongratulations! Please find your certificate for {branch} ({year_of_study}) attached.\n\nBest regards,\nCertificate Team",
                    help="Use {name}, {branch}, {year_of_study} as placeholders",
                    height=150
                )
        st.header("🚀 Start Processing")
        submit_btn = st.form_submit_button("Generate & Send Certificates")
        if submit_btn:
            if not excel_file:
                st.error("Please upload an Excel or CSV file")
                return
            if not sender_email or not sender_password:
                st.error("Please provide email credentials")
                return
            # Reset file pointers before upload
            if excel_file:
                excel_file.seek(0)
            if template_file:
                template_file.seek(0)
            with st.spinner("Uploading files..."):
                upload_result = upload_files(excel_file, template_file)
                if upload_result:
                    task_id = upload_result['task_id']
                    st.success(f"Files uploaded successfully! Task ID: {task_id}")
                    st.session_state['current_task_id'] = task_id
                    email_config = {
                        "sender_email": sender_email,
                        "sender_password": sender_password,
                        "email_subject": email_subject,
                        "email_body": email_body,
                        "smtp_server": smtp_server,
                        "smtp_port": smtp_port
                    }
                    with st.spinner("Starting certificate generation..."):
                        process_result = start_processing(task_id, email_config)
                        if process_result:
                            st.success("Processing started! Check the status in the 'View Status' page.")
                            st.info(f"Task ID: {task_id}")
                            time.sleep(2)
                            st.rerun()

def view_status_page():
    st.header("📊 Processing Status")
    
    # Task ID input
    task_id = st.text_input(
        "Task ID",
        value=st.session_state.get('current_task_id', ''),
        help="Enter the Task ID from the upload process"
    )
    
    if task_id:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("🔄 Refresh Status", use_container_width=True):
                pass  # Just refresh the page
        
        with col2:
            auto_refresh = st.checkbox("Auto-refresh", value=True)
        
        with col3:
            if st.button("🗑️ Cleanup", use_container_width=True):
                if cleanup_task(task_id):
                    st.success("Task cleaned up successfully!")
                    if 'current_task_id' in st.session_state:
                        del st.session_state['current_task_id']
        
        # Get and display status
        status_data = get_status(task_id)
        
        if status_data:
            status = status_data['status']
            message = status_data['message']
            processed = status_data.get('processed_count', 0)
            total = status_data.get('total_count', 0)
            
            # Status indicator
            if status == "completed":
                st.success(f"✅ {message}")
            elif status == "error":
                st.error(f"❌ {message}")
            elif status == "processing":
                st.info(f"⏳ {message}")
            else:
                st.info(f"📋 {message}")
            
            # Progress bar
            if total > 0:
                progress = processed / total
                st.progress(progress)
                st.write(f"Progress: {processed}/{total} ({progress:.1%})")
            
            # Detailed results
            if 'results' in status_data and status_data['results']:
                results = status_data['results']
                
                st.subheader("📈 Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Students", results['total'])
                with col2:
                    st.metric("Successful", results['success_count'])
                with col3:
                    st.metric("Failed", results['failure_count'])
                
                # Successful emails
                if results['successful']:
                    with st.expander(f"✅ Successful Emails ({len(results['successful'])})"):
                        for student in results['successful']:
                            st.write(f"• {student['name']} - {student['email']}")
                
                # Failed emails
                if results['failed']:
                    with st.expander(f"❌ Failed Emails ({len(results['failed'])})"):
                        for student in results['failed']:
                            st.write(f"• {student['name']} - {student['email']}: {student.get('error', 'Unknown error')}")
        
        # Auto-refresh
        if auto_refresh and status_data and status_data['status'] == 'processing':
            time.sleep(3)
            st.rerun()

def help_page():
    st.header("📖 Help & Instructions")
    
    st.markdown("""
    ## How to Use Auto-Certy
    
    ### 1. Prepare Your Data File
    Your Excel (.xlsx, .xls) or CSV (.csv) file should contain the following columns (case-insensitive):
    - **Name** (or Student_Name, Full_Name)
    - **Email** (or Email_ID, Email_Address)  
    - **Year_of_Study** (or Year, Academic_Year)
    - **Branch** (or Department, Course)
    
    ### 2. Email Configuration
    - **Gmail Users**: Use App Password instead of regular password
      - Go to Google Account Settings → Security → App passwords
      - Generate a new app password for this application
    - **Other Email Providers**: Use your regular SMTP settings
    
    ### 3. Certificate Template
    - Upload a PDF template (optional)
    - If no template is provided, a default certificate will be generated
    - Templates should be designed to accommodate variable text
    
    ### 4. Processing Steps
    1. Upload your Excel/CSV file and optional template
    2. Configure email settings
    3. Click "Generate & Send Certificates"
    4. Monitor progress in the "View Status" page
    5. Clean up completed tasks when done
    
    ### 5. Troubleshooting
    - **Backend Connection Error**: Ensure FastAPI server is running (`uvicorn main:app --reload`)
    - **Email Authentication Error**: Check email credentials and app password
    - **File Format Error**: Ensure file is .xlsx, .xls, or .csv format
    - **Column Not Found**: Check that your Excel columns match expected names
    
    ### 6. Security Notes
    - Email passwords are not stored permanently
    - Generated certificates are cleaned up after processing
    - Use app passwords for better security
    """)
    
    st.subheader("📋 Sample File Format")
    sample_data = {
        'Name': ['John Doe', 'Jane Smith', 'Mike Johnson'],
        'Email': ['john@example.com', 'jane@example.com', 'mike@example.com'],
        'Year_of_Study': ['2023', '2024', '2023'],
        'Branch': ['Computer Science', 'Mechanical Engineering', 'Electrical Engineering']
    }
    st.dataframe(pd.DataFrame(sample_data))

# Initialize session state
if 'current_task_id' not in st.session_state:
    st.session_state['current_task_id'] = ''

if __name__ == "__main__":
    main()
