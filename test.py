import streamlit as st
import os

def get_file_extension(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension

def main():
    st.title("File Extension Extractor")

    uploaded_file = st.file_uploader("Upload a file", type=["txt", "csv", "xlsx", "pdf","docx"])

    if uploaded_file is not None:
        st.write("File Uploaded!")

        # Get and display the file extension
        file_extension = get_file_extension(uploaded_file.name)
        st.write(f"File Extension: {file_extension}")

if __name__ == "__main__":
    main()