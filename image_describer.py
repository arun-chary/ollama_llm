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

import json
import tempfile  # For creating temporary files
from pathlib import Path  # For handling file paths
import ollama  # For AI interaction
import streamlit as st  # For Web UI
import os  # Standard library for OS interactions


def extract_tags_and_confidence(description, model_name):
    """Use the selected model to extract short tags and a confidence label."""
    extraction_prompt = (
        "From the following image description, extract 5 short keywords or object names "
        "that best describe the image. Return a JSON object with exactly two keys: "
        "'tags' (a list of short strings) and 'confidence' (one of 'high', 'medium', or 'low')."
        f"\nDescription: {description}"
    )

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": extraction_prompt}],
        )
        content = response["message"]["content"].strip()

        try:
            data = json.loads(content)
            tags = data.get("tags", [])
            confidence = str(data.get("confidence", "medium")).lower()
        except Exception:
            tags = [item.strip() for item in content.split(",") if item.strip()]
            confidence = "medium"
    except Exception:
        tags = []
        confidence = "medium"

    return tags[:5], confidence


st.title("Image Describer!")

# Create a file uploader widget.
# accept_multiple_files=True allows the user to select more than one image at a time.
# type=[...] restricts uploads to image formats.

uploaded_files = st.file_uploader(
    "Choose an image",
    accept_multiple_files=True,
    type=["jpg", "jpeg", "png"]
)

prompt_type = st.selectbox(
    "Prompt type",
    ["Describe", "Short caption", "List objects", "Analyze mood"],
    index=0,
)

model_choice = st.selectbox(
    "Model to use",
    ["llava:7b", "llava", "llava:latest"],
    index=2,
)

prompt_templates = {
    "Describe": "Describe this image in one short paragraph.",
    "Short caption": "Write a short caption for this image.",
    "List objects": "List the main objects visible in this image.",
    "Analyze mood": "Describe the mood and atmosphere of this image.",
}

question = prompt_templates[prompt_type]

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

    output_path = Path(__file__).resolve().parent / "image_descriptions.txt"
    output_path.parent.mkdir(exist_ok=True)

    for uploaded_file in uploaded_files:
        st.subheader(uploaded_file.name)
        st.image(uploaded_file, caption="Uploaded Image", width=600)

        suffix = Path(uploaded_file.name).suffix or ".jpg"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name

        try:
            models_to_try = [model_choice]

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
                    description = response["message"]["content"]
                    st.markdown(description)
                    st.caption(f"Model used: {model_name}")

                    tags, confidence = extract_tags_and_confidence(description, model_name)
                    st.subheader("Tags")
                    st.write(", ".join(tags) if tags else "No tags extracted")
                    st.caption(f"Confidence: {confidence.upper()}")

                    with output_path.open("a", encoding="utf-8") as fh:
                        fh.write(f"File: {uploaded_file.name}\n")
                        fh.write(f"Prompt type: {prompt_type}\n")
                        fh.write(f"Model used: {model_name}\n")
                        fh.write(f"Prompt: {question}\n")
                        fh.write("Description:\n")
                        fh.write(f"{description}\n")
                        fh.write("Tags: " + (", ".join(tags) if tags else "No tags extracted") + "\n")
                        fh.write(f"Confidence: {confidence}\n")
                        fh.write("-" * 40 + "\n")

                    st.caption(f"Saved to {output_path}")
                    break
                except Exception as exc:
                    last_error = exc
                    if "not found" not in str(exc).lower():
                        raise
            else:
                raise RuntimeError(
                    f"The selected model '{model_choice}' could not be used. Make sure it is installed with 'ollama pull {model_choice}'."
                ) from last_error
        except Exception as e:
            st.error(f"Could not describe the image: {e}")
