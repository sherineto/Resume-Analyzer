import streamlit as st
import pandas as pd
import re
import base64
import phonenumbers
from PIL import Image
from pdfminer.high_level import extract_text

def extract_name(text):
    """
    Extract name from text using regular expression
    """
    name = None
    patterns = [
        r"([A-Z][a-z]+ [A-Z][a-z]+)",  # Firstname Lastname
        r"([A-Z][a-z]+ [A-Z].)",  # Firstname L.
        r"([A-Z]. [A-Z][a-z]+ [A-Z][a-z]+)",  # F. Lastname
        r"([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)",  # Firstname Middlename Lastname
        r"([A-Z][a-z]+ [A-Z][a-z]+-[A-Z][a-z]+)",  # Firstname Lastname-Lastname
        r"([A-Z][a-z]+-[A-Z][a-z]+ [A-Z][a-z]+)",  # Firstname-Lastname Lastname
        r"([A-Z]. [A-Z][a-z]+ [A-Z]. [A-Z][a-z]+)",  # F. M. Lastname
    ]
    for pattern in patterns:
        result = re.search(pattern, text)
        if result:
            name = result.group(1)
            break
    return name

def extract_email(text):
    """
    Extract email address from text using regular expression
    """
    email = None
    pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
    matches = re.findall(pattern, text)
    if matches:
        email = matches[0].lower()
    return email

def extract_phone_number(text):
    """
    Extract phone number from text using phonenumbers library
    """
    phone = None
    for match in phonenumbers.PhoneNumberMatcher(text, "PK"):
        phone_number = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
        if phone_number.startswith("+92"):
            phone = phone_number
            break
    return phone

def extract_resume_info(file):
    """
    Extract name, email, and phone number from resume file
    """
    text = extract_text(file)
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone_number(text)
    return {"Name": name, "Email": email, "Phone": phone}

def main():
    st.title("Nutrifactor Resume Analyzer")
    col1, col2 = st.columns([1, 3])
    with col1:
        img = Image.open('./images/Nutrifactor.jpg')
        img = img.resize((250, 250))
        st.image(img)
    with col2:
        st.write("Upload resumes in PDF format to extract name, email, and phone number.")

        uploaded_files = st.file_uploader("Choose a PDF file", accept_multiple_files=True)

    if uploaded_files:
        resume_list = []
        num_files = len(uploaded_files)
        with st.empty():
            for i, file in enumerate(uploaded_files):
                info = extract_resume_info(file)
                resume_list.append(info)
                progress = (i + 1) / num_files
                progress_bar = st.progress(progress)
                status_text = f"Processed {i + 1} out of {num_files} files ({progress:.0%})"
                status_text += " " * (st.session_state.status_text_width - len(status_text))
                st.session_state.status_text_width = len(status_text)
                status = st.text(status_text)
                progress_bar.progress(progress)
                status.text(status_text)

        st.write("All files processed!")
        df = pd.DataFrame(resume_list)
        # Make column headers bold using HTML tags
        df_html = df.style.set_table_styles([{"selector": "th", "props": [("font-weight", "bold")]}]).render()
        st.write(df_html, unsafe_allow_html=True)

        # Create download link for CSV
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="resume_info.csv">Download CSV file</a>'
        st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    st.session_state.status_text_width = 0
    main()
