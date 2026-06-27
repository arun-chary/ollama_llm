# ollama_llm
This repo is to create ollama llm projects

Project: Image Reader
---------------------

Project Description

This project is a Streamlit-based image analysis web app that uses a local Ollama AI model to describe uploaded images. It allows users to upload one or more images from their computer, choose a prompt style, select an Ollama model, and receive AI-generated descriptions directly in the browser.

The app is designed for experimentation and learning with local AI models. It provides a simple interface where users can:

1. Upload images in JPG, JPEG, or PNG format
2. Choose different prompt types such as description, short caption, object listing, or mood analysis
3. Select an Ollama model such as llava:7b, llava, or llava:latest
4. View the generated description for each image
5. Extract simple tags and a confidence label from the generated description
6. Save the results into a text file for later review

The application uses Streamlit for the frontend and Ollama for local image understanding. It creates a temporary file from each uploaded image, sends it to the selected model, and displays the response in the app. It also saves the output to a file named image_descriptions.txt in the project folder.

This project is useful for:

1. Learning how to build AI-powered web apps
2. Testing different prompt styles
3. Comparing local models for image understanding
4. Exploring image captioning and image analysis workflows

Features

1. Upload multiple images at once
2. Select prompt type from a dropdown
3. Choose the Ollama model to use
4. View image descriptions in the browser
5. Extract keywords/tags from the description
6. Assign a simple confidence label
7. Save results to a text file
8. Basic UI controls such as theme selection, max-image slider, start button, and clear button

Requirements

Python
Streamlit
Ollama
A local Ollama model such as llava


How to Run?

1. Install the required packages:
2. pip install streamlit ollama
3. Pull a model with Ollama:
4. ollama pull llava:latest
5. Run the app: streamlit run image_describer.py
