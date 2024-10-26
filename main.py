import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO
import base64
import time

# Set page configuration
st.set_page_config(
    page_title="Stability AI App",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    /* Hide Streamlit header and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom font and background */
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #f0f2f6;
    }

    /* Button styling */
    .stButton>button {
        color: white;
        background-color: #6c63ff;
        border-radius: 8px;
        height: 3em;
        width: 100%;
        font-size: 16px;
    }

    /* Tabs styling */
    .stTabs [role="tab"] {
        padding: 1rem;
        font-size: 16px;
        font-weight: 600;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #6c63ff;
        color: white;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6 {
        color: white;
    }
    [data-testid="stSidebar"] label {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar for API Key and User Account
st.sidebar.title("🔑 API Configuration")
api_key = st.sidebar.text_input(
    "Enter your Stability AI API Key",
    type="password",
    key="api_key",
    help="Get your API key from https://platform.stability.ai/",
)

if not api_key:
    st.sidebar.warning("Please enter your API key to continue.")
    st.stop()

headers = {
    "Authorization": f"Bearer {api_key}",
}

# Sidebar - User Account
st.sidebar.markdown("---")
st.sidebar.header("👤 User Account")

if st.sidebar.button("View Account Details", key="account_details"):
    with st.spinner("Fetching account details..."):
        response = requests.get(
            "https://api.stability.ai/v1/user/account",
            headers=headers,
        )
    if response.status_code == 200:
        account_info = response.json()
        st.sidebar.success("Account Details:")
        st.sidebar.json(account_info)
    else:
        st.sidebar.error(f"Error: {response.status_code} - {response.text}")

if st.sidebar.button("View Account Balance", key="account_balance"):
    with st.spinner("Fetching account balance..."):
        response = requests.get(
            "https://api.stability.ai/v1/user/balance",
            headers=headers,
        )
    if response.status_code == 200:
        balance_info = response.json()
        st.sidebar.success(f"💰 Credits: {balance_info['credits']}")
    else:
        st.sidebar.error(f"Error: {response.status_code} - {response.text}")

# Helper Functions
def get_engines():
    response = requests.get(
        "https://api.stability.ai/v1/engines/list",
        headers=headers,
    )
    if response.status_code == 200:
        engines = response.json()
        return [engine["id"] for engine in engines]
    else:
        st.error("Failed to fetch engines.")
        return []

def display_image(response):
    if response.status_code == 200:
        if 'artifacts' in response.json():
            artifacts = response.json()['artifacts']
            cols = st.columns(len(artifacts))
            for idx, artifact in enumerate(artifacts):
                img_data = base64.b64decode(artifact['base64'])
                img = Image.open(BytesIO(img_data))
                cols[idx].image(img)
        else:
            img = Image.open(BytesIO(response.content))
            st.image(img)
    else:
        try:
            st.error(f"Error: {response.status_code} - {response.json().get('message', response.text)}")
        except:
            st.error(f"Error: {response.status_code} - {response.text}")

def display_video(response):
    if response.status_code == 200:
        video_bytes = response.content
        st.video(video_bytes)
    else:
        try:
            st.error(f"Error: {response.status_code} - {response.json().get('message', response.text)}")
        except:
            st.error(f"Error: {response.status_code} - {response.text}")

def display_3d_model(response):
    if response.status_code == 200:
        glb_data = response.content
        b64_glb = base64.b64encode(glb_data).decode("utf-8")
        st.components.v1.html(
            f"""
            <model-viewer src="data:model/gltf-binary;base64,{b64_glb}"
                          style="width: 100%; height: 600px;"
                          autoplay
                          camera-controls
                          ar>
            </model-viewer>
            <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
            """,
            height=600,
        )
    else:
        try:
            st.error(f"Error: {response.status_code} - {response.json().get('message', response.text)}")
        except:
            st.error(f"Error: {response.status_code} - {response.text}")

def start_polling(generation_id, result_url, accept_header):
    max_retries = 30
    retry_delay = 10  # seconds
    for attempt in range(max_retries):
        time.sleep(retry_delay)
        result_response = requests.get(
            result_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": accept_header,
            },
        )
        if result_response.status_code == 200:
            return result_response
        elif result_response.status_code == 202:
            st.info(f"Generation in progress... ({attempt + 1}/{max_retries})")
            continue
        else:
            st.error(f"Error: {result_response.status_code} - {result_response.text}")
            break
    st.error("Generation timed out.")
    return None

# Main Tabs
tab_titles = [
    "🖼️ Image Generation & Editing",
    "🎞️ Video Generation",
    "🔷 3D Generation",
]
tabs = st.tabs(tab_titles)

# 🖼️ Image Generation & Editing Tab
with tabs[0]:
    st.header("🖼️ Image Generation & Editing")

    # Sub-tabs for different functionalities
    image_subtabs = st.tabs(["Text-to-Image", "Image-to-Image", "Image Masking", "Image Upscaling", "Image Editing", "Image Control"])

    # Text-to-Image Sub-tab
    with image_subtabs[0]:
        st.subheader("🎨 Text-to-Image Generation")
        with st.expander("Generation Settings", expanded=True):
            engines = get_engines()
            engine_id = st.selectbox("Select Engine", engines, key="tti_engine")
            prompt = st.text_area("Prompt", key="tti_prompt", help="Describe the image you want to generate.")
            negative_prompt = st.text_area("Negative Prompt", key="tti_negative_prompt", help="Describe what you don't want in the image.")
            col1, col2 = st.columns(2)
            with col1:
                height = st.number_input("Height", value=512, step=64, key="tti_height")
                cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0, key="tti_cfg_scale", help="How closely the image should adhere to the prompt.")
                samples = st.number_input("Samples", min_value=1, max_value=4, value=1, key="tti_samples", help="Number of images to generate.")
            with col2:
                width = st.number_input("Width", value=512, step=64, key="tti_width")
                steps = st.number_input("Steps", min_value=10, max_value=150, value=30, key="tti_steps", help="Number of diffusion steps.")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0, key="tti_seed")
            sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL", "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL", "K_HEUN", "K_LMS"], key="tti_sampler")
            style_preset = st.selectbox(
                "Style Preset",
                ["None", "3D Model", "Analog Film", "Anime", "Cinematic", "Comic Book", "Digital Art", "Enhance",
                 "Fantasy Art", "Isometric", "Line Art", "Low Poly", "Modeling Compound", "Neon Punk", "Origami",
                 "Photographic", "Pixel Art", "Tile Texture"],
                key="tti_style_preset"
            )

        generate_button = st.button("Generate Image", key="tti_generate")

        if generate_button:
            with st.spinner("Generating image..."):
                json_body = {
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": cfg_scale,
                    "height": height,
                    "width": width,
                    "sampler": sampler,
                    "samples": samples,
                    "steps": steps,
                    "seed": seed,
                }
                if negative_prompt:
                    json_body["text_prompts"].append({"text": negative_prompt, "weight": -1})
                if style_preset != "None":
                    json_body["style_preset"] = style_preset.lower().replace(" ", "-")
                response = requests.post(
                    f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=json_body,
                )
            display_image(response)

    # Image-to-Image Sub-tab
    with image_subtabs[1]:
        st.subheader("🖼️ Image-to-Image Generation")
        with st.expander("Upload and Settings", expanded=True):
            engines = get_engines()
            engine_id = st.selectbox("Select Engine", engines, key="iti_engine")
            init_image_file = st.file_uploader("Upload Initial Image", type=["png", "jpg", "jpeg", "webp"], key="iti_init_image", help="Upload the image you want to use as a base.")
            if init_image_file:
                init_image = Image.open(init_image_file)
                st.image(init_image, caption="Initial Image", use_column_width=True)
            prompt = st.text_area("Prompt", key="iti_prompt", help="Describe the changes you want to make to the image.")
            negative_prompt = st.text_area("Negative Prompt", key="iti_negative_prompt", help="Describe what you don't want in the image.")
            image_strength = st.slider("Image Strength", min_value=0.0, max_value=1.0, value=0.35, key="iti_image_strength", help="How much influence the initial image has on the final result.")
            cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0, key="iti_cfg_scale")
            steps = st.number_input("Steps", min_value=10, max_value=150, value=30, key="iti_steps")
            seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0, key="iti_seed")
            sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL", "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL", "K_HEUN", "K_LMS"], key="iti_sampler")
            style_preset = st.selectbox(
                "Style Preset",
                ["None", "3D Model", "Analog Film", "Anime", "Cinematic", "Comic Book", "Digital Art", "Enhance",
                 "Fantasy Art", "Isometric", "Line Art", "Low Poly", "Modeling Compound", "Neon Punk", "Origami",
                 "Photographic", "Pixel Art", "Tile Texture"],
                key="iti_style_preset"
            )

        generate_button = st.button("Generate Image", key="iti_generate")

        if generate_button and init_image_file:
            with st.spinner("Generating image..."):
                files = {
                    "init_image": init_image_file.getvalue(),
                }
                data = {
                    "text_prompts[0][text]": prompt,
                    "image_strength": image_strength,
                    "cfg_scale": cfg_scale,
                    "sampler": sampler,
                    "steps": steps,
                    "seed": seed,
                    "init_image_mode": "IMAGE_STRENGTH",
                }
                if negative_prompt:
                    data["text_prompts[1][text]"] = negative_prompt
                    data["text_prompts[1][weight]"] = -1
                if style_preset != "None":
                    data["style_preset"] = style_preset.lower().replace(" ", "-")
                response = requests.post(
                    f"https://api.stability.ai/v1/generation/{engine_id}/image-to-image",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
                    files=files,
                    data=data,
                )
            display_image(response)

    # Image Masking Sub-tab
    with image_subtabs[2]:
        st.subheader("✂️ Image Masking")
        with st.expander("Upload Images and Settings", expanded=True):
            engines = get_engines()
            engine_id = st.selectbox("Select Engine", engines, key="mask_engine")
            init_image_file = st.file_uploader("Upload Initial Image", type=["png", "jpg", "jpeg", "webp"], key="mask_init_image", help="Upload the image you want to modify.")
            mask_image_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"], key="mask_mask_image", help="Upload the mask image indicating areas to modify.")
            if init_image_file and mask_image_file:
                col1, col2 = st.columns(2)
                with col1:
                    init_image = Image.open(init_image_file)
                    st.image(init_image, caption="Initial Image", use_column_width=True)
                with col2:
                    mask_image = Image.open(mask_image_file)
                    st.image(mask_image, caption="Mask Image", use_column_width=True)
            prompt = st.text_area("Prompt", key="mask_prompt", help="Describe the modifications you want to make.")
            negative_prompt = st.text_area("Negative Prompt", key="mask_negative_prompt", help="Describe what you don't want in the image.")
            mask_source = st.selectbox("Mask Source", ["MASK_IMAGE_WHITE", "MASK_IMAGE_BLACK", "INIT_IMAGE_ALPHA"], key="mask_source", help="Define how the mask is interpreted.")
            cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0, key="mask_cfg_scale")
            steps = st.number_input("Steps", min_value=10, max_value=150, value=30, key="mask_steps")
            seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0, key="mask_seed")
            sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL", "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL", "K_HEUN", "K_LMS"], key="mask_sampler")
            style_preset = st.selectbox(
                "Style Preset",
                ["None", "3D Model", "Analog Film", "Anime", "Cinematic", "Comic Book", "Digital Art", "Enhance",
                 "Fantasy Art", "Isometric", "Line Art", "Low Poly", "Modeling Compound", "Neon Punk", "Origami",
                 "Photographic", "Pixel Art", "Tile Texture"],
                key="mask_style_preset"
            )

        generate_button = st.button("Generate Image", key="mask_generate")

        if generate_button and init_image_file and mask_image_file:
            with st.spinner("Generating image..."):
                files = {
                    "init_image": init_image_file.getvalue(),
                    "mask_image": mask_image_file.getvalue(),
                }
                data = {
                    "text_prompts[0][text]": prompt,
                    "mask_source": mask_source,
                    "cfg_scale": cfg_scale,
                    "sampler": sampler,
                    "steps": steps,
                    "seed": seed,
                }
                if negative_prompt:
                    data["text_prompts[1][text]"] = negative_prompt
                    data["text_prompts[1][weight]"] = -1
                if style_preset != "None":
                    data["style_preset"] = style_preset.lower().replace(" ", "-")
                response = requests.post(
                    f"https://api.stability.ai/v1/generation/{engine_id}/image-to-image/masking",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
                    files=files,
                    data=data,
                )
            display_image(response)

    # Image Upscaling Sub-tab
    with image_subtabs[3]:
        st.subheader("📈 Image Upscaling")
        with st.expander("Upscaling Options", expanded=True):
            upscale_type = st.selectbox("Select Upscaler", ["Fast", "Conservative", "Creative"], key="upscale_type")
            image_file = st.file_uploader("Upload Image to Upscale", type=["png", "jpg", "jpeg", "webp"], key="upscale_image")
            if image_file:
                image = Image.open(image_file)
                st.image(image, caption="Original Image", use_column_width=True)
            if upscale_type == "Fast":
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="fast_output_format")
                upscale_button = st.button("Upscale Image", key="fast_upscale_button")
                if upscale_button and image_file:
                    with st.spinner("Upscaling image..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/upscale/fast",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)
            elif upscale_type == "Conservative":
                prompt = st.text_area("Prompt", key="conservative_prompt")
                negative_prompt = st.text_area("Negative Prompt", key="conservative_negative_prompt")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="conservative_seed")
                creativity = st.slider("Creativity", min_value=0.2, max_value=0.5, value=0.35, key="conservative_creativity")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="conservative_output_format")
                upscale_button = st.button("Upscale Image", key="conservative_upscale_button")
                if upscale_button and image_file:
                    with st.spinner("Upscaling image..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "seed": seed,
                            "creativity": creativity,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/upscale/conservative",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)
            elif upscale_type == "Creative":
                prompt = st.text_area("Prompt", key="creative_prompt")
                negative_prompt = st.text_area("Negative Prompt", key="creative_negative_prompt")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="creative_seed")
                creativity = st.slider("Creativity", min_value=0.0, max_value=0.35, value=0.3, key="creative_creativity")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="creative_output_format")
                upscale_button = st.button("Start Upscaling", key="creative_upscale_button")
                if upscale_button and image_file:
                    with st.spinner("Upscaling image..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "seed": seed,
                            "creativity": creativity,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/upscale/creative",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                            },
                            files=files,
                            data=data,
                        )
                    if response.status_code == 200:
                        generation_id = response.json().get("id")
                        st.write(f"Generation ID: {generation_id}")
                        st.write("Fetching upscaled image...")
                        result_response = start_polling(
                            generation_id,
                            f"https://api.stability.ai/v2beta/stable-image/upscale/creative/result/{generation_id}",
                            accept_header="image/*"
                        )
                        if result_response:
                            display_image(result_response)
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")

    # Image Editing Sub-tab
    with image_subtabs[4]:
        st.subheader("🛠️ Image Editing")
        with st.expander("Editing Options", expanded=True):
            edit_type = st.selectbox(
                "Select Edit Type",
                ["Inpaint", "Outpaint", "Erase", "Search and Replace", "Search and Recolor", "Remove Background"],
                key="edit_type"
            )
            image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"], key="edit_image")
            if image_file:
                image = Image.open(image_file)
                st.image(image, caption="Original Image", use_column_width=True)

            if edit_type == "Inpaint":
                prompt = st.text_area("Prompt", key="inpaint_prompt")
                negative_prompt = st.text_area("Negative Prompt", key="inpaint_negative_prompt")
                mask_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"], key="inpaint_mask")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="inpaint_seed")
                grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=100, value=5, key="inpaint_grow_mask")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="inpaint_output_format")
                inpaint_button = st.button("Inpaint", key="inpaint_button")

                if inpaint_button and image_file and mask_file:
                    with st.spinner("Inpainting image..."):
                        files = {
                            "image": image_file.getvalue(),
                            "mask": mask_file.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "seed": seed,
                            "grow_mask": grow_mask,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/edit/inpaint",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)

            elif edit_type == "Outpaint":
                prompt = st.text_area("Prompt", key="outpaint_prompt")
                negative_prompt = st.text_area("Negative Prompt", key="outpaint_negative_prompt")
                left = st.number_input("Left Expansion (pixels)", min_value=0, max_value=2000, value=0, key="outpaint_left")
                right = st.number_input("Right Expansion (pixels)", min_value=0, max_value=2000, value=0, key="outpaint_right")
                up = st.number_input("Up Expansion (pixels)", min_value=0, max_value=2000, value=0, key="outpaint_up")
                down = st.number_input("Down Expansion (pixels)", min_value=0, max_value=2000, value=0, key="outpaint_down")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="outpaint_seed")
                creativity = st.slider("Creativity", min_value=0.0, max_value=1.0, value=0.5, key="outpaint_creativity")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="outpaint_output_format")
                outpaint_button = st.button("Outpaint", key="outpaint_button")

                if outpaint_button and image_file:
                    with st.spinner("Outpainting image..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "left": left,
                            "right": right,
                            "up": up,
                            "down": down,
                            "creativity": creativity,
                            "seed": seed,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/edit/outpaint",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)

            elif edit_type == "Erase":
                mask_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"], key="erase_mask")
                grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=20, value=5, key="erase_grow_mask")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="erase_seed")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="erase_output_format")
                erase_button = st.button("Erase", key="erase_button")

                if erase_button and image_file and mask_file:
                    with st.spinner("Erasing image..."):
                        files = {
                            "image": image_file.getvalue(),
                            "mask": mask_file.getvalue(),
                        }
                        data = {
                            "grow_mask": grow_mask,
                            "seed": seed,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/edit/erase",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)

            elif edit_type == "Search and Replace":
                prompt = st.text_area("Prompt", key="search_replace_prompt")
                search_prompt = st.text_input("Search Prompt", key="search_replace_search_prompt")
                negative_prompt = st.text_area("Negative Prompt", key="search_replace_negative_prompt")
                grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=20, value=3, key="search_replace_grow_mask")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="search_replace_seed")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="search_replace_output_format")
                replace_button = st.button("Search and Replace", key="search_replace_button")

                if replace_button and image_file:
                    with st.spinner("Processing image..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "search_prompt": search_prompt,
                            "negative_prompt": negative_prompt,
                            "grow_mask": grow_mask,
                            "seed": seed,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/edit/search-and-replace",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)

            elif edit_type == "Search and Recolor":
                prompt = st.text_area("Prompt", key="search_recolor_prompt")
                select_prompt = st.text_input("Select Prompt", key="search_recolor_select_prompt")
                negative_prompt = st.text_area("Negative Prompt", key="search_recolor_negative_prompt")
                grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=20, value=3, key="search_recolor_grow_mask")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="search_recolor_seed")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="search_recolor_output_format")
                recolor_button = st.button("Search and Recolor", key="search_recolor_button")

                if recolor_button and image_file:
                    with st.spinner("Processing image..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "select_prompt": select_prompt,
                            "negative_prompt": negative_prompt,
                            "grow_mask": grow_mask,
                            "seed": seed,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/edit/search-and-recolor",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)

            elif edit_type == "Remove Background":
                output_format = st.selectbox("Output Format", ["png", "webp"], key="remove_bg_output_format")
                remove_bg_button = st.button("Remove Background", key="remove_bg_button")

                if remove_bg_button and image_file:
                    with st.spinner("Removing background..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/edit/remove-background",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)

    # Image Control Sub-tab
    with image_subtabs[5]:
        st.subheader("🖌️ Image Control")
        with st.expander("Control Options", expanded=True):
            control_type = st.selectbox("Select Control Type", ["Sketch", "Structure", "Style"], key="control_type")
            image_file = st.file_uploader("Upload Control Image", type=["png", "jpg", "jpeg", "webp"], key="control_image")
            if image_file:
                image = Image.open(image_file)
                st.image(image, caption="Control Image", use_column_width=True)

            prompt = st.text_area("Prompt", key="control_prompt")
            negative_prompt = st.text_area("Negative Prompt", key="control_negative_prompt")
            seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="control_seed")
            output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="control_output_format")

            if control_type == "Sketch":
                control_strength = st.slider("Control Strength", min_value=0.0, max_value=1.0, value=0.7, key="sketch_control_strength")
                control_button = st.button("Generate Image", key="sketch_control_button")

                if control_button and image_file:
                    with st.spinner("Generating image..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "control_strength": control_strength,
                            "negative_prompt": negative_prompt,
                            "seed": seed,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/control/sketch",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)

            elif control_type == "Structure":
                control_strength = st.slider("Control Strength", min_value=0.0, max_value=1.0, value=0.7, key="structure_control_strength")
                control_button = st.button("Generate Image", key="structure_control_button")

                if control_button and image_file:
                    with st.spinner("Generating image..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "control_strength": control_strength,
                            "negative_prompt": negative_prompt,
                            "seed": seed,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/control/structure",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)

            elif control_type == "Style":
                fidelity = st.slider("Fidelity", min_value=0.0, max_value=1.0, value=0.5, key="style_fidelity")
                aspect_ratio = st.selectbox("Aspect Ratio", ["1:1", "16:9", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"], key="style_aspect_ratio")
                control_button = st.button("Generate Image", key="style_control_button")

                if control_button and image_file:
                    with st.spinner("Generating image..."):
                        files = {
                            "image": image_file.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "fidelity": fidelity,
                            "aspect_ratio": aspect_ratio,
                            "negative_prompt": negative_prompt,
                            "seed": seed,
                            "output_format": output_format,
                        }
                        response = requests.post(
                            "https://api.stability.ai/v2beta/stable-image/control/style",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Accept": "image/*",
                            },
                            files=files,
                            data=data,
                        )
                    display_image(response)

# 🎞️ Video Generation Tab
with tabs[1]:
    st.header("🎞️ Video Generation")
    video_subtabs = st.tabs(["Text-to-Animation", "Image-to-Video"])

    # Text-to-Animation Sub-tab
    with video_subtabs[0]:
        st.subheader("📝 Text-to-Animation")
        with st.expander("Animation Settings", expanded=True):
            engines = get_engines()
            engine_id = st.selectbox("Select Engine", engines, key="tta_engine")
            prompt = st.text_area("Prompt", key="tta_prompt", help="Describe the animation you want to generate.")
            negative_prompt = st.text_area("Negative Prompt", key="tta_negative_prompt", help="Describe what you don't want in the animation.")
            cfg_scale = st.number_input("CFG Scale", min_value=0.0, max_value=35.0, value=7.0, key="tta_cfg_scale")
            steps = st.number_input("Steps", min_value=10, max_value=50, value=30, key="tta_steps")
            seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0, key="tta_seed")
            samples = st.number_input("Samples", min_value=1, max_value=4, value=1, key="tta_samples")
            sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL", "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL", "K_HEUN", "K_LMS"], key="tta_sampler")

        generate_button = st.button("Generate Animation", key="tta_generate")

        if generate_button:
            with st.spinner("Generating animation..."):
                json_body = {
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": cfg_scale,
                    "steps": steps,
                    "seed": seed,
                    "samples": samples,
                    "sampler": sampler,
                }
                if negative_prompt:
                    json_body["text_prompts"].append({"text": negative_prompt, "weight": -1})
                response = requests.post(
                    f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=json_body,
                )
            display_image(response)

    # Image-to-Video Sub-tab
    with video_subtabs[1]:
        st.subheader("🖼️ Image-to-Video")
        with st.expander("Video Generation Settings", expanded=True):
            image_file = st.file_uploader("Upload Initial Image", type=["png", "jpg", "jpeg"], key="video_image")
            if image_file:
                image = Image.open(image_file)
                st.image(image, caption="Initial Image", use_column_width=True)
            cfg_scale = st.number_input("CFG Scale", min_value=0.0, max_value=10.0, value=1.8, key="video_cfg_scale")
            motion_bucket_id = st.number_input("Motion Bucket ID", min_value=1, max_value=255, value=127, key="video_motion_bucket")
            seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="video_seed")
        video_button = st.button("Generate Video", key="video_button")

        if video_button and image_file:
            with st.spinner("Generating video..."):
                files = {
                    "image": image_file.getvalue(),
                }
                data = {
                    "cfg_scale": cfg_scale,
                    "motion_bucket_id": motion_bucket_id,
                    "seed": seed,
                }
                response = requests.post(
                    "https://api.stability.ai/v2beta/image-to-video",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
                    files=files,
                    data=data,
                )
            if response.status_code == 200:
                generation_id = response.json().get("id")
                st.write(f"Generation ID: {generation_id}")
                st.write("Fetching video...")
                result_response = start_polling(
                    generation_id,
                    f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}",
                    accept_header="video/*"
                )
                if result_response:
                    display_video(result_response)
            else:
                st.error(f"Error: {response.status_code} - {response.text}")

# 🔷 3D Generation Tab
with tabs[2]:
    st.header("🔷 3D Model Generation")
    with st.expander("3D Model Generation Settings", expanded=True):
        image_file = st.file_uploader("Upload Image for 3D Model", type=["png", "jpg", "jpeg", "webp"], key="3d_image")
        if image_file:
            image = Image.open(image_file)
            st.image(image, caption="Input Image", use_column_width=True)
        texture_resolution = st.selectbox("Texture Resolution", [512, 1024, 2048], key="3d_texture_resolution")
        foreground_ratio = st.slider("Foreground Ratio", min_value=0.1, max_value=1.0, value=0.85, key="3d_foreground_ratio")
        remesh = st.selectbox("Remesh", ["none", "quad", "triangle"], key="3d_remesh")
        vertex_count = st.number_input("Vertex Count (-1 for default)", min_value=-1, max_value=20000, value=-1, key="3d_vertex_count")
    model_button = st.button("Generate 3D Model", key="3d_model_button")

    if model_button and image_file:
        with st.spinner("Generating 3D model..."):
            files = {
                "image": image_file.getvalue(),
            }
            data = {
                "texture_resolution": texture_resolution,
                "foreground_ratio": foreground_ratio,
                "remesh": remesh,
                "vertex_count": vertex_count,
            }
            response = requests.post(
                "https://api.stability.ai/v2beta/3d/stable-fast-3d",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                files=files,
                data=data,
            )
        display_3d_model(response)
