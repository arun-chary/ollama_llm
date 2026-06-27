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

from PIL import Image
import json
import re
import tempfile  # For creating temporary files
from pathlib import Path  # For handling file paths
import ollama  # For AI interaction
import streamlit as st  # For Web UI
import os  # Standard library for OS interactions


def parse_extraction_output(content):
    """Try to parse the model output as JSON or structured text."""
    content = content.strip()

    # Try direct JSON parse first.
    try:
        data = json.loads(content)
        return data
    except Exception:
        pass

    # Try to extract a JSON object from inside noisy text.
    match = re.search(r"\{.*\}", content, re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            return data
        except Exception:
            pass

    # Fallback: look for a confidence word and comma-separated tags.
    confidence = "medium"
    if re.search(r"\bhigh\b", content, re.I):
        confidence = "high"
    elif re.search(r"\blow\b", content, re.I):
        confidence = "low"

    tags = []
    if "tags" in content.lower():
        tag_match = re.search(r"tags\s*[:=]\s*\[([^\]]+)\]", content, re.I)
        if tag_match:
            tags = [t.strip().strip('"\'') for t in tag_match.group(1).split(",") if t.strip()]
    if not tags:
        # Take the first comma-separated line as tags
        first_line = content.splitlines()[0]
        tags = [item.strip() for item in first_line.split(",") if item.strip()]

    return {"tags": tags, "confidence": confidence}


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
        data = parse_extraction_output(content)
        tags = data.get("tags", []) if isinstance(data, dict) else []
        confidence = str(data.get("confidence", "medium")).lower() if isinstance(data, dict) else "medium"
    except Exception:
        tags = []
        confidence = "medium"

    return tags[:5], confidence


st.set_page_config(page_title="Image Describer", page_icon="🖼️", layout="wide")
st.title("Image Describer!")

st.sidebar.header("Controls")
st.info("Upload one or more images, choose your settings, and click Start analysis.")

if theme_choice := st.sidebar.selectbox(
    "Theme",
    ["Default", "Dark", "Light"],
    index=0,
    key="theme_choice",
):
    if theme_choice == "Dark":
        st.markdown(
            "<style>body{background-color:#0e1117;color:white;} .stApp{background-color:#0e1117;} .stMarkdown, .stTextInput, .stSelectbox, .stSlider, .stButton>button{color:white;}</style>",
            unsafe_allow_html=True,
        )
    elif theme_choice == "Light":
        st.markdown(
            "<style>body{background-color:white;color:#111;} .stApp{background-color:white;} .stMarkdown, .stTextInput, .stSelectbox, .stSlider, .stButton>button{color:#111;}</style>",
            unsafe_allow_html=True,
        )

# Create a file uploader widget.
# accept_multiple_files=True allows the user to select more than one image at a time.
# type=[...] restricts uploads to image formats.

uploaded_files = st.file_uploader(
    "Choose an image",
    accept_multiple_files=True,
    type=["jpg", "jpeg", "png"],
    key="uploaded_files",
)

prompt_type = st.sidebar.selectbox(
    "Prompt type",
    ["Describe", "Short caption", "List objects", "Analyze mood"],
    index=0,
    key="prompt_type",
)

model_choice = st.sidebar.selectbox(
    "Model to use",
    ["llava:7b", "llava", "llava:latest"],
    index=2,
    key="model_choice",
)

max_items = st.sidebar.slider("Max images to process at once", 1, 5, 3, key="max_items")

submit_button = st.sidebar.button("Start analysis", key="submit_button")
clear_button = st.sidebar.button("Clear all", key="clear_button")

prompt_templates = {
    "Describe": "Describe this image in one short paragraph.",
    "Short caption": "Write a short caption for this image.",
    "List objects": "List the main objects visible in this image.",
    "Analyze mood": "Describe the mood and atmosphere of this image.",
}

question = prompt_templates[prompt_type]

if clear_button:
    st.session_state.pop("prompt_type", None)
    st.session_state.pop("model_choice", None)
    st.session_state.pop("theme_choice", None)
    st.session_state.pop("max_items", None)
    st.session_state.pop("submit_button", None)
    st.session_state.pop("clear_button", None)
    st.rerun()

# Print the list of uploaded file objects to the terminal for debugging.
print(uploaded_files)

if uploaded_files and submit_button:
    st.write(f"Uploaded {len(uploaded_files)} image(s)")

    output_path = Path(__file__).resolve().parent / "image_descriptions.txt"
    output_path.parent.mkdir(exist_ok=True)

    for uploaded_file in uploaded_files[:max_items]:
        st.subheader(uploaded_file.name)
        st.image(uploaded_file, caption="Uploaded Image", width=600)

        suffix = Path(uploaded_file.name).suffix or ".jpg"

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name

            try:
                Image.open(temp_path).verify()
            except Exception:
                st.error("Uploaded file is not a valid image or is corrupted.")
                continue

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
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
