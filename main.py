import streamlit as st
import replicate
import os
from dotenv import load_dotenv

# Load environment variables from .env if available
load_dotenv()

# Title and Sidebar Setup
st.set_page_config(page_title="Replicate Model Explorer")
st.title("Replicate Model Explorer")

# Sidebar for API Key Input and Model Link
st.sidebar.title("Configuration")
api_key = st.sidebar.text_input("Enter your Replicate API Key", type="password")

# Verify API Key and Initialize Client
if api_key:
    replicate_client = replicate.Client(api_token=api_key)
    st.sidebar.success("API Key is set!", icon="✅")
else:
    st.sidebar.warning("Please enter your API key to proceed.")

# Sidebar Model URL Input
model_url = st.sidebar.text_input("Paste Replicate Model Link (e.g., 'stability-ai/stable-diffusion:latest')")

# Sidebar Parameters for Text/Image Adjustments
st.sidebar.subheader("Model Parameters")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.5)
top_p = st.sidebar.slider("Top P", 0.0, 1.0, 0.9)
max_length = st.sidebar.slider("Max Length", 16, 512, 128)

# Model Interaction Section
st.write("### Model Interaction")
if model_url and api_key:
    try:
        # Extract model info
        model_name = model_url.split("/")[-1]  # Extracts the model ID
        model = replicate_client.models.get(model_name)
        version = model.versions.list()[0]  # Get latest version

        # Display model info
        st.write(f"**Model:** {model_name}")
        st.write(model.description)

        # Input Prompt
        prompt = st.text_area("Enter your prompt:")

        # Run Model and Display Results
        if st.button("Generate"):
            with st.spinner("Generating..."):
                try:
                    # Define parameters based on input
                    inputs = {
                        "prompt": prompt,
                        "temperature": temperature,
                        "top_p": top_p,
                        "max_length": max_length,
                    }

                    # Run the model prediction
                    output = version.predict(**inputs)

                    # Display output based on type
                    if isinstance(output, str) and output.startswith("http"):
                        st.image(output, caption="Generated Image")
                    elif isinstance(output, list) and any(isinstance(i, dict) for i in output):
                        st.video(output[0]["url"])
                    elif isinstance(output, str):
                        st.write(output)
                    else:
                        st.json(output)
                except Exception as e:
                    st.error(f"Error during model execution: {e}")
    except Exception as e:
        st.error("Invalid model link or parameters. Please verify your inputs.")
else:
    st.info("Please enter a model URL and your API key.")

# Favorites Section: Saving and Loading Model Settings
st.sidebar.title("Favorites")
favorite_name = st.sidebar.text_input("Favorite Name")
save_favorite = st.sidebar.button("Save Favorite Settings")
if save_favorite and favorite_name:
    if "favorites" not in st.session_state:
        st.session_state["favorites"] = []
    st.session_state["favorites"].append({"name": favorite_name, "url": model_url, "params": inputs})
    st.sidebar.success(f"Favorite '{favorite_name}' saved!")

# Export Favorites as JSON
if st.sidebar.button("Export Favorites as JSON"):
    import json
    with open("favorites.json", "w") as f:
        json.dump(st.session_state.get("favorites", []), f)
    st.sidebar.success("Favorites exported as favorites.json")

# Load a Favorite
if st.sidebar.checkbox("Load Favorite"):
    favorites = st.session_state.get("favorites", [])
    if favorites:
        selected_favorite = st.sidebar.selectbox("Select a Favorite", [fav["name"] for fav in favorites])
        favorite_data = next((fav for fav in favorites if fav["name"] == selected_favorite), None)
        if favorite_data:
            model_url = favorite_data["url"]
            inputs = favorite_data["params"]
            st.sidebar.info(f"Loaded settings for '{selected_favorite}'")
