import streamlit as st
import pandas as pd
import re
import os
import io
import docx
import base64
import phonenumbers
from PIL import Image
from pdfminer.high_level import extract_text

def extract_name(text, file_name):
    """
    Extract name from text using regular expression
    """
    name = None
    file_name_without_extension = os.path.splitext(os.path.basename(file_name))[0]

    # 1st Priority Condition: Name extraction from file name if "CV" word is at the start of the file name
    if file_name_without_extension.startswith('CV'):
        # Remove "CV", special characters, and numbers; add spaces before the 2nd, 3rd, and 4th capital letters
        cleaned_name = re.sub('[^a-zA-Z]', '', file_name_without_extension[2:])
        name = re.sub('(?<!\n)([A-Z][a-z]*)([A-Z][a-z]*)([A-Z][a-z]*)?', r'\1 \2 \3', cleaned_name).strip()

    # 2nd Priority Condition: Name extraction from file name if "Rozee" word is at the start of the file name
    elif file_name_without_extension.startswith('Rozee'):
        # Split the file name by '-' characters
        name_parts = file_name_without_extension.split('-')

        # Look for the last two parts that have at least one alphabetical character
        for i in range(len(name_parts) - 1, -1, -1):
            if re.search('[a-zA-Z]', name_parts[i]):
                last_name = name_parts[i]
                if i > 0 and re.search('[a-zA-Z]', name_parts[i - 1]):
                    first_name = name_parts[i - 1]
                    first_name = first_name.title()
                    last_name = last_name.title()
                    name = f"{first_name} {last_name}"
                    break

        name = re.sub('[^a-zA-Z ]', '', name).strip()

    # 3rd Priority Condition: Name extraction from file name if "Resume" word is at the start of the file name
    elif file_name_without_extension.startswith('Resume'):
        # Remove "Resume", special characters, and numbers; add spaces before the 2nd, 3rd, and 4th capital letters
        cleaned_name = re.sub('[^a-zA-Z]', '', file_name_without_extension[6:])
        name = re.sub('(?<!\n)([A-Z][a-z]*)([A-Z][a-z]*)([A-Z][a-z]*)?', r'\1 \2 \3', cleaned_name).strip()

    # 4th Priority Condition: Name extraction from file name if "Resumes" or "CV" word is not at the start of the file name
    elif not file_name_without_extension.startswith(('Resume', 'CV', 'Updated', 'RESUME', 'updated')):
        # Remove "Resumes", "CV", special characters, and numbers; capitalize the first letter of first and last name
        cleaned_name = re.sub('[^a-zA-Z]', ' ', file_name_without_extension).strip()
        cleaned_name = ' '.join([word.capitalize() for word in cleaned_name.split() if word not in ('CV', 'Updated', 'Resume', 'RESUME', 'updated',)])
        name = cleaned_name

    return name

if not os.path.exists("tmp"):
    os.makedirs("tmp")

def extract_resume_info(file):
    """
    Extract name, email, phone number, file name, and qualification from resume file
    """
    # Extract name from file name
    name = os.path.splitext(file.name)[0]
    name = extract_name(name, file.name)

    # Save uploaded file to a temporary file
    with open(f"tmp/{file.name}", "wb") as f:
        f.write(file.read())

    # Extract text from temporary file
    if file.type == 'application/pdf':
        text = extract_text(f"tmp/{file.name}")
    elif file.type in ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'):
        doc = docx.Document(io.BytesIO(file.read()))
        text = '\n'.join([para.text for para in doc.paragraphs])
    else:
        text = ''

    # Delete temporary file
    os.remove(f"tmp/{file.name}")

    email = extract_email(text)
    phone = extract_phone_number(text)
    file_name = file.name

    # If name is not found in the file name, extract name from the resume text
    if not name:
        name = extract_name(text, file_name)

    # Extract qualification from resume text
    qualification = None
    if re.search(r'\bDigital Marketer\b', text) and re.search(r'\bFB Ads\b', text):
        qualification = "Digital Marketer, Fb Ads"
    elif re.search(r'\bDigital Marketing\b', text):
        qualification = "Digital Marketing"
    elif re.search(r'\bDigital Marketer\b', text):
        qualification = "Digital Marketer"
    elif re.search(r'\bFb Ads\b', text):
        qualification = "Fb Ads"
    elif re.search(r'\bSEO\b', text):
        qualification = "SEO"
    elif re.search(r'\bAdvertisement\b', text):
        qualification = "Advertisement"
    elif re.search(r'\bPPC\b', text):
        qualification = "PPC"
    elif re.search(r'\bPPC Fb Ads\b', text):
        qualification = "PPC Fb Ads"
    else:
        qualification = "None"

    return {"Name": name, "Email": email, "Phone": phone, "File Name": file_name, "Qualification": qualification}

def extract_email(text):
    """
    Extract email address from text using regular expression
    """
    email = None
    pattern = r"[\w.-]+@[\w.-]+.\w+"
    matches = re.findall(pattern, text)
    if matches:
        email = matches[0].lower()
        if email.endswith("gmail.co"):
            email = email.replace("gmail.co", "gmail.com")
    return email

def extract_phone_number(text):
    """
    Extract phone number from text and format it to start with +92
    """
    phone = None
    for match in phonenumbers.PhoneNumberMatcher(text, "PK"):
        phone_number = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
        if phone_number.startswith("+92"):
            # If the number already starts with +92, use it as is
            phone = phone_number
        elif phone_number.startswith("0"):
            # If the number starts with 0, remove the 0 and add +92
            phone = "+92" + phone_number[1:]
        elif phone_number.startswith("92"):
            # If the number starts with 92, add a + before the 92
            phone = "+" + phone_number

        # If we've found a phone number, break out of the loop
        if phone is not None:
            break

    return phone

def create_resume_link(file_contents, file_name):
    file_b64 = base64.b64encode(file_contents).decode()
    href = f'<a href="data:application/pdf;base64,{file_b64}" target="_blank">View Resume</a>'
    return href

def main():
    st.title("Nutrifactor Resume Analyzer")
    col1, col2 = st.columns([1, 3])
    with col1:
        img = Image.open('./images/Nutrifactor.jpg')
        img = img.resize((250, 250))
        st.image(img)
    with col2:
        st.write("Upload resumes in PDF format to extract name, email, phone number, and qualification.")

        uploaded_files = st.file_uploader("Choose a file", type=['pdf', 'docx'], accept_multiple_files=True)

    if uploaded_files:
        resume_list = []
        num_files = len(uploaded_files)
        with st.empty():
            for i, file in enumerate(uploaded_files):
                _, file_ext = os.path.splitext(file.name)
                if file_ext not in ['.pdf', '.docx']:
                    st.write(f"Skipping file {file.name}. Invalid file extension.")
                    continue

                file_contents = file.getvalue()
                info = extract_resume_info(file)
                info["View Resume"] = create_resume_link(file_contents, file.name)
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
        df = pd.DataFrame(resume_list, columns=["Name", "Email", "Phone", "File Name", "Qualification"])
        # Define table style
        table_style = [{
            'selector': 'th',
            'props': [
                ('font-family', 'Arial'),
                ('font-size', '10pt')
            ]
        }, {
            'selector': 'td',
            'props': [
                ('font-family', 'Arial'),
                ('font-size', '10pt')
            ]
        }, {
            'selector': 'table',
            'props': [
                ('max-width', '500px')
            ]
        }]
        # Apply table style to Pandas DataFrame
        df_html = df.style.set_table_styles(table_style).render()

        # Display table with style
        st.write(df_html, unsafe_allow_html=True)

        # Create download link for CSV
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="resume_info.csv">Download CSV file</a>'
        st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    st.session_state.status_text_width = 0
    main()
