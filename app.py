import streamlit as st
import boto3
from io import BytesIO
from botocore.exceptions import ClientError
from PIL import Image


# AWS credentials
AWS_ACCESS_KEY_ID = "AKIA6ODU77IO5BEWVLND"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "us-east-1"

# S3 buckets
INPUT_S3_BUCKET_NAME = "documentinput"
OUTPUT_S3_BUCKET_NAME = "documentoutput"

# Initialize S3 clients
s3_input = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
s3_output = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

def upload_to_s3(file, source_lang, target_lang):
    uploaded_file_name = file.name
    uploaded_file_name = uploaded_file_name.replace(" ","_")
    file_name = f"{source_lang}|{target_lang}|{uploaded_file_name}"
    s3_input.upload_fileobj(file, INPUT_S3_BUCKET_NAME, file_name)
    return file_name

def download_from_s3(file_name):
    download_file_name = file_name
    download_file_name = download_file_name.replace(" ","_")
    try:
        obj = s3_output.get_object(Bucket=OUTPUT_S3_BUCKET_NAME, Key=download_file_name)
        return obj['Body'].read()
    except: 
        return None


def main():
    # Define image URL
    image_url = "rsz_qucoonlogo.png"

    # Display the image
    st.image(image_url)

    st.title("Document Translation System")
    
    # File upload
    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])
    
    if uploaded_file is not None:

        # Source language selection (Radio drop-down for French and English)
        source_lang = st.radio("Select source language:", ['French', 'English'])
        if source_lang == 'French':
            source_ext = 'fr'
        if source_lang == 'English':
            source_ext = 'en'
        # Target language selection (Radio drop-down for French and English)
        target_lang = st.radio("Select target language:", ['French', 'English'])
        if target_lang == 'French':
            target_ext = 'fr'
        if target_lang == 'English':
            target_ext = 'en'
        # Upload button
        if st.button("Translate and Upload to S3"):
            # Upload the document to S3
            file_name = upload_to_s3(uploaded_file, source_ext.lower(), target_ext.lower())
            st.success(f"Document '{file_name}' uploaded successfully!")

    # Download button
    #download_file_name = st.text_input("Enter the document name to download from S3:")
        download_file_name = f"{target_ext}{uploaded_file.name}"
        print(download_file_name)
        if st.button("Process Download"):
            downloaded_content = download_from_s3(download_file_name)
            print(downloaded_content)
            if downloaded_content is not None:
                    st.download_button(label="Download Processed Document", data=downloaded_content, file_name=download_file_name)
            else:
                st.error(f"Failed to download the document. Please reload the document and ensure it's not too large.")
            
if __name__ == "__main__":
    main()
