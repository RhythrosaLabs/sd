import streamlit as st
import requests
import replicate
import json
import os

# Initialize session state to store favorites and API key
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = []

# Sidebar for API key input
st.sidebar.title("Configuration")
api_key = st.sidebar.text_input("Enter your Replicate API Key", type="password")

# Verify and initialize Replicate client if API key is provided
if api_key:
    replicate_client = replicate.Client(api_token=api_key)

# Sidebar File Management Section
st.sidebar.title("File Management")
uploaded_files = st.sidebar.file_uploader("Upload Files", accept_multiple_files=True)
st.sidebar.write("Uploaded Files:")
for file in uploaded_files:
    st.sidebar.write(file.name)

# Sidebar to Save Favorite Models
st.sidebar.title("Favorites")
model_name_input = st.sidebar.text_input("Favorite Model Name", help="Name this model setup")
save_favorite = st.sidebar.button("Save Current Model Settings")

# Step 1: App Title and Model URL Input
st.title("Replicate Model Explorer")
model_url = st.text_input("Paste Replicate model reference link (e.g., 'replicate/black-forest-labs/flux-1.1-pro')")

# Step 2: Extract Model Name and Parameters
if api_key and model_url:
    try:
        # Extract model information
        model_name = model_url.split("replicate.com/")[-1]
        model = replicate_client.models.get(model_name)
        version = model.versions.list()[0]  # Get the latest version of the model

        # Display model description and parameters
        st.write(f"### Model: {model_name}")
        st.write(model.description)

        # Step 3: Dynamic Parameter Input Generation
        st.write("### Model Parameters")
        inputs = {}
        for param, details in version["schema"]["properties"].items():
            param_type = details["type"]
            default = details.get("default", None)
            description = details.get("description", "")

            # Generate input fields based on parameter type
            if param_type == "string":
                inputs[param] = st.text_input(param, value=default, help=description)
            elif param_type == "number":
                inputs[param] = st.number_input(param, value=default, help=description)
            elif param_type == "boolean":
                inputs[param] = st.checkbox(param, value=default, help=description)
            elif param_type == "array":
                inputs[param] = st.text_area(param, help=description)
            else:
                st.write(f"Parameter {param} has an unsupported type: {param_type}")

        # Save Favorite Model Settings if Button Clicked
        if save_favorite and model_name_input:
            favorite = {"model_name": model_name, "settings": inputs}
            st.session_state['favorites'].append(favorite)
            st.sidebar.success(f"Saved settings for model: {model_name_input}")

        # Step 4: Run Model and Display Results
        if st.button("Run Model"):
            with st.spinner("Generating..."):
                try:
                    output = version.predict(**inputs)
                    # Display based on output type
                    if isinstance(output, str) and output.startswith("http"):
                        st.image(output, caption="Generated Image")
                    elif isinstance(output, list) and any(isinstance(i, dict) for i in output):
                        st.video(output[0]["url"])
                    elif isinstance(output, str):
                        st.write(output)
                    else:
                        st.json(output)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        # Export Favorite Models as JSON
        if st.sidebar.button("Export Favorites as JSON"):
            with open("favorites.json", "w") as f:
                json.dump(st.session_state['favorites'], f)
            st.sidebar.success("Favorites exported as favorites.json")

    except Exception as e:
        st.error("Invalid model link or parameters. Please try again.")
else:
    st.info("Please enter a valid API key in the sidebar to begin.")
