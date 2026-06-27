# Title: Make a Image Describer page on Streamlit
#
# Description:
# This script integrates the 'Llava' image-understanding model into a Streamlit web app.
# It allows users to:
# 1. Upload one or multiple images via the browser.
# 2. Display the uploaded images.
# 3. Have the local AI describe each image automatically.
#
# IMPORTANT:
# Streamlit keeps uploaded files in RAM (memory), but Ollama expects a file PATH
# on the hard drive.
# In this specific file, we pass 'uploaded_file.name' to Ollama.
# We assume that the image you upload ALREADY exists in the same folder as this script.
# Since the file is on the disk, Ollama can find it using just the filename.
#
# Installation:
# pip install streamlit ollama
#
# How to run:
# streamlit run 9.py

import tempfile  # For creating temporary files
from pathlib import Path  # For handling file paths
import ollama  # For AI interaction
import streamlit as st  # For Web UI
import os  # Standard library for OS interactions


st.title("Image Describer!")

# Create a file uploader widget.
# accept_multiple_files=True allows the user to select more than one image at a time.
# type=[...] restricts uploads to image formats.

uploaded_files = st.file_uploader(
    "Choose an image",
    accept_multiple_files=True,
    type=["jpg", "jpeg", "png"]
)

question = st.text_input(
    "Ask a question about the uploaded image(s)",
    "Describe this image in one short paragraph."
)

# Print the list of uploaded file objects to the terminal for debugging.
print(uploaded_files)

# Check if the user has uploaded at least one file.
# if len(uploaded_files) != 0:
#     # Loop through each uploaded file.
#     for uploaded_file in uploaded_files:
#         # Debug prints
#         print(uploaded_file.name)
#         print(type(uploaded_file.name))

#         # Display the image on the webpage.
#         st.image(uploaded_file, caption='Uploaded Image.', width=True)

#         # Send the image to Llava for description.
#         # CRITICAL NOTE: 'uploaded_file.name' gives us the filename (e.g., "image.jpg").
#         # Because we are uploading a file that is ALREADY in our project folder,
#         # Ollama can find it by name. If you uploaded a file from a different folder,
#         # this would fail because Ollama wouldn't know the full path.

if uploaded_files:
    st.write(f"Uploaded {len(uploaded_files)} image(s)")

    for uploaded_file in uploaded_files:
        st.subheader(uploaded_file.name)
        st.image(uploaded_file, caption="Uploaded Image", width=600)

        suffix = Path(uploaded_file.name).suffix or ".jpg"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name

        try:
            models_to_try = ["llava:7b", "llava", "llava:latest"]

            last_error = None
            for model_name in models_to_try:
                try:
                    response = ollama.chat(
                        model=model_name,
                        messages=[
                            {
                                "role": "user",
                                "content": question,
                                "images": [temp_path],
                            }
                        ]
                    )
                    st.markdown(response["message"]["content"])
                    break
                except Exception as exc:
                    last_error = exc
                    if "not found" not in str(exc).lower():
                        raise
            else:
                raise RuntimeError(
                    "No compatible Ollama image model was found. Tried "
                    + ", ".join(models_to_try)
                    + ". Run 'ollama pull llava' or 'ollama pull llava:latest' first."
                ) from last_error
        except Exception as e:
            st.error(f"Could not describe the image: {e}")
