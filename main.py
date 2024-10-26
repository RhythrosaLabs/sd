import streamlit as st
import requests
from PIL import Image, ImageOps
from io import BytesIO
import base64
import time
import os
from streamlit_drawable_canvas import st_canvas

# Set page configuration
st.set_page_config(
    page_title="Stability AI App",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Create the directory for saving generated images if it doesn't exist
if not os.path.exists("generated_images"):
    os.makedirs("generated_images")

# Initialize session state for current image
if 'current_image' not in st.session_state:
    st.session_state['current_image'] = None

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

    /* Canvas and tools layout */
    .canvas-container {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
    }
    .canvas-column {
        flex: 3;
        margin-right: 1rem;
    }
    .tools-column {
        flex: 1;
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
def display_image(response, save_prefix="generated_image"):
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type')
        if content_type and 'application/json' in content_type:
            data = response.json()
            if 'artifacts' in data:
                artifacts = data['artifacts']
                img_data = base64.b64decode(artifacts[0]['base64'])
                img = Image.open(BytesIO(img_data))
                # Update session state
                st.session_state['current_image'] = img
                # Save the image
                img_filename = f"{save_prefix}_{int(time.time())}.png"
                img.save(os.path.join("generated_images", img_filename))
        else:
            img = Image.open(BytesIO(response.content))
            # Update session state
            st.session_state['current_image'] = img
            # Save the image
            img_filename = f"{save_prefix}_{int(time.time())}.png"
            img.save(os.path.join("generated_images", img_filename))
    else:
        try:
            st.error(f"Error: {response.status_code} - {response.json().get('message', response.text)}")
        except:
            st.error(f"Error: {response.status_code} - {response.text}")

def display_video(response, save_prefix="generated_video"):
    if response.status_code == 200:
        video_bytes = response.content
        st.video(video_bytes)
        # Save the video
        video_filename = f"{save_prefix}_{int(time.time())}.mp4"
        with open(os.path.join("generated_images", video_filename), "wb") as f:
            f.write(video_bytes)
    else:
        try:
            st.error(f"Error: {response.status_code} - {response.json().get('message', response.text)}")
        except:
            st.error(f"Error: {response.status_code} - {response.text}")

def display_3d_model(response, save_prefix="generated_model"):
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
        # Save the model
        model_filename = f"{save_prefix}_{int(time.time())}.glb"
        with open(os.path.join("generated_images", model_filename), "wb") as f:
            f.write(glb_data)
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

# Main Interface
st.title("🖌️ Stability AI Image Editor")

# Top section with prompt and upload button
st.markdown("## Enter your prompt and upload an image (optional)")
col1, col2 = st.columns([3, 1])

with col1:
    prompt = st.text_area("Prompt", key="prompt_main", help="Describe the image you want to generate.")
    negative_prompt = st.text_area("Negative Prompt", key="negative_prompt_main", help="Describe what you don't want in the image.")
    generate_button = st.button("Generate Image", key="generate_button_main")
with col2:
    uploaded_image = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"], key="uploaded_image_main")
    if uploaded_image:
        init_image = Image.open(uploaded_image)
        st.session_state['current_image'] = init_image

if generate_button:
    with st.spinner("Generating image..."):
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": 0,
            "output_format": "png",
            "model": "stable-diffusion-3.5-large",
            "steps": 50,
            "sampler": "K_EULER",
            "cfg_scale": 7.0,
            "samples": 1,
        }
        if st.session_state['current_image']:
            data["strength"] = 0.5
            data["mode"] = "image-to-image"
            buffered = BytesIO()
            st.session_state['current_image'].save(buffered, format="PNG")
            files = {
                "image": buffered.getvalue(),
            }
        else:
            files = {"none": ""}
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            files=files,
            data=data,
        )
    display_image(response)
    st.success("Image generated and loaded into the canvas!")

# Main canvas and tools
st.markdown("---")
st.markdown("## Edit your image")
canvas_col, tools_col = st.columns([3, 1])

with canvas_col:
    st.subheader("🖼️ Canvas")
    canvas_mode = st.selectbox("Canvas Mode", ["Draw", "Modify"], key="canvas_mode")
    if canvas_mode == "Draw":
        stroke_width = st.slider("Stroke Width", 1, 25, 3)
        stroke_color = st.color_picker("Stroke Color", "#000000")
        bg_color = st.color_picker("Background Color", "#FFFFFF")
        realtime_update = st.checkbox("Update in Real Time", True)
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",  # Transparent fill
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color=bg_color,
            background_image=st.session_state['current_image'].convert("RGBA") if st.session_state['current_image'] else None,
            height=512,
            width=512,
            drawing_mode="freedraw",
            key="canvas",
            update_streamlit=realtime_update,
        )
        if canvas_result.image_data is not None:
            # Update the current image with the canvas content
            init_image = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            st.session_state['current_image'] = init_image
    else:
        if st.session_state['current_image']:
            st.image(st.session_state['current_image'], caption="Current Image", use_column_width=True)
        else:
            st.warning("Please draw or upload an image first.")

with tools_col:
    st.subheader("🛠️ Tools")
    tool = st.selectbox("Select Tool", ["Image Effects", "Image-to-Image", "Image-to-Video"])
    if tool == "Image Effects":
        effect_type = st.selectbox("Select Effect", ["Upscale", "Inpaint", "Outpaint", "Erase", "Search and Replace", "Search and Recolor", "Remove Background"], key="effect_type")
        if st.session_state['current_image'] is not None:
            if effect_type == "Upscale":
                upscale_type = st.selectbox("Upscale Type", ["Fast", "Conservative", "Creative"], key="upscale_type")
                if upscale_type == "Fast":
                    output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="output_format_upscale")
                    upscale_button = st.button("Upscale Image", key="upscale_button")
                    if upscale_button:
                        with st.spinner("Upscaling image..."):
                            buffered = BytesIO()
                            st.session_state['current_image'].save(buffered, format="PNG")
                            files = {
                                "image": buffered.getvalue(),
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
                            st.success("Image upscaled and loaded into the canvas!")
                else:
                    prompt_upscale = st.text_area("Upscale Prompt", key="upscale_prompt")
                    negative_prompt_upscale = st.text_area("Upscale Negative Prompt", key="upscale_negative_prompt")
                    seed_upscale = st.number_input("Upscale Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="upscale_seed")
                    creativity = st.slider("Creativity", min_value=0.0, max_value=0.5, value=0.3, key="creativity_upscale")
                    output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="output_format_upscale")
                    upscale_button = st.button("Upscale Image", key="upscale_button")
                    if upscale_button:
                        with st.spinner("Upscaling image..."):
                            buffered = BytesIO()
                            st.session_state['current_image'].save(buffered, format="PNG")
                            files = {
                                "image": buffered.getvalue(),
                            }
                            data = {
                                "prompt": prompt_upscale,
                                "negative_prompt": negative_prompt_upscale,
                                "seed": seed_upscale,
                                "creativity": creativity,
                                "output_format": output_format,
                            }
                            endpoint = "conservative" if upscale_type == "Conservative" else "creative"
                            response = requests.post(
                                f"https://api.stability.ai/v2beta/stable-image/upscale/{endpoint}",
                                headers={
                                    "Authorization": f"Bearer {api_key}",
                                },
                                files=files,
                                data=data,
                            )
                            if response.status_code == 200 and upscale_type == "Creative":
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
                                    st.success("Image upscaled and loaded into the canvas!")
                            else:
                                display_image(response)
                                st.success("Image upscaled and loaded into the canvas!")
            elif effect_type == "Inpaint":
                mask_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"], key="inpaint_mask")
                grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=100, value=5, key="grow_mask")
                prompt = st.text_area("Prompt", key="prompt_inpaint")
                negative_prompt = st.text_area("Negative Prompt", key="negative_prompt_inpaint")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="seed_inpaint")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="output_format_inpaint")
                inpaint_button = st.button("Inpaint Image", key="inpaint_button")
                if inpaint_button and mask_file:
                    with st.spinner("Inpainting image..."):
                        buffered = BytesIO()
                        st.session_state['current_image'].save(buffered, format="PNG")
                        files = {
                            "image": buffered.getvalue(),
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
                    st.success("Image inpainted and loaded into the canvas!")
            elif effect_type == "Outpaint":
                prompt = st.text_area("Prompt", key="prompt_outpaint")
                negative_prompt = st.text_area("Negative Prompt", key="negative_prompt_outpaint")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="seed_outpaint")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="output_format_outpaint")
                left = st.number_input("Left Expansion (pixels)", min_value=0, max_value=2000, value=0, key="left_expansion")
                right = st.number_input("Right Expansion (pixels)", min_value=0, max_value=2000, value=0, key="right_expansion")
                up = st.number_input("Up Expansion (pixels)", min_value=0, max_value=2000, value=0, key="up_expansion")
                down = st.number_input("Down Expansion (pixels)", min_value=0, max_value=2000, value=0, key="down_expansion")
                creativity = st.slider("Creativity", min_value=0.0, max_value=1.0, value=0.5, key="creativity_outpaint")
                outpaint_button = st.button("Outpaint Image", key="outpaint_button")
                if outpaint_button:
                    with st.spinner("Outpainting image..."):
                        buffered = BytesIO()
                        st.session_state['current_image'].save(buffered, format="PNG")
                        files = {
                            "image": buffered.getvalue(),
                        }
                        data = {
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "seed": seed,
                            "left": left,
                            "right": right,
                            "up": up,
                            "down": down,
                            "creativity": creativity,
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
                    st.success("Image outpainted and loaded into the canvas!")
            elif effect_type == "Erase":
                mask_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"], key="erase_mask")
                grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=20, value=5, key="erase_grow_mask")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="seed_erase")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="output_format_erase")
                erase_button = st.button("Erase", key="erase_button")
                if erase_button and mask_file:
                    with st.spinner("Erasing image..."):
                        buffered = BytesIO()
                        st.session_state['current_image'].save(buffered, format="PNG")
                        files = {
                            "image": buffered.getvalue(),
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
                    st.success("Image erased and loaded into the canvas!")
            elif effect_type == "Search and Replace":
                search_prompt = st.text_input("Search Prompt", key="search_replace_search_prompt")
                prompt = st.text_area("Replace Prompt", key="prompt_search_replace")
                negative_prompt = st.text_area("Negative Prompt", key="negative_prompt_search_replace")
                grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=20, value=3, key="search_replace_grow_mask")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="seed_search_replace")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="output_format_search_replace")
                replace_button = st.button("Search and Replace", key="search_replace_button")
                if replace_button:
                    with st.spinner("Processing image..."):
                        buffered = BytesIO()
                        st.session_state['current_image'].save(buffered, format="PNG")
                        files = {
                            "image": buffered.getvalue(),
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
                    st.success("Image processed and loaded into the canvas!")
            elif effect_type == "Search and Recolor":
                select_prompt = st.text_input("Select Prompt", key="search_recolor_select_prompt")
                prompt = st.text_area("Recolor Prompt", key="prompt_search_recolor")
                negative_prompt = st.text_area("Negative Prompt", key="negative_prompt_search_recolor")
                grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=20, value=3, key="search_recolor_grow_mask")
                seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="seed_search_recolor")
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="output_format_search_recolor")
                recolor_button = st.button("Search and Recolor", key="search_recolor_button")
                if recolor_button:
                    with st.spinner("Processing image..."):
                        buffered = BytesIO()
                        st.session_state['current_image'].save(buffered, format="PNG")
                        files = {
                            "image": buffered.getvalue(),
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
                    st.success("Image recolored and loaded into the canvas!")
            elif effect_type == "Remove Background":
                output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="output_format_remove_bg")
                remove_bg_button = st.button("Remove Background", key="remove_bg_button")
                if remove_bg_button:
                    with st.spinner("Removing background..."):
                        buffered = BytesIO()
                        st.session_state['current_image'].save(buffered, format="PNG")
                        files = {
                            "image": buffered.getvalue(),
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
                    st.success("Background removed and image loaded into the canvas!")
        else:
            st.warning("Please draw or upload an image first.")
    elif tool == "Image-to-Image":
        if st.session_state['current_image'] is not None:
            st.subheader("🖼️ Image-to-Image Generation")
            model_type = st.selectbox("Select Model", [
                "Stable Diffusion 3.5 Large", "Stable Diffusion 3.5 Large Turbo",
                "Stable Diffusion 3.0 Large", "Stable Diffusion 3.0 Large Turbo", "Stable Diffusion 3.0 Medium"
            ], key="model_type_iti")
            prompt = st.text_area("Prompt", key="prompt_iti", help="Describe the image you want to generate.")
            negative_prompt = st.text_area("Negative Prompt", key="negative_prompt_iti", help="Describe what you don't want in the image.")
            image_strength = st.slider("Image Strength", min_value=0.0, max_value=1.0, value=0.5, key="image_strength_iti")
            seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="seed_iti")
            output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="output_format_iti")
            steps = st.number_input("Steps", min_value=1, max_value=150, value=50, key="steps_iti")
            sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL", "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL", "K_HEUN", "K_LMS"], key="sampler_iti")
            cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0, key="cfg_scale_iti")
            samples = st.number_input("Samples", min_value=1, max_value=10, value=1, key="samples_iti")
            generate_button = st.button("Generate Image", key="generate_button_iti")
            if generate_button:
                with st.spinner("Generating image..."):
                    data = {
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "seed": seed,
                        "output_format": output_format,
                        "strength": image_strength,
                        "mode": "image-to-image",
                        "model": model_type.lower().replace(" ", "-"),
                        "steps": steps,
                        "sampler": sampler,
                        "cfg_scale": cfg_scale,
                        "samples": samples,
                    }
                    buffered = BytesIO()
                    st.session_state['current_image'].save(buffered, format="PNG")
                    files = {
                        "image": buffered.getvalue(),
                    }
                    response = requests.post(
                        "https://api.stability.ai/v2beta/stable-image/generate",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Accept": "application/json",
                        },
                        files=files,
                        data=data,
                    )
                    display_image(response)
                    st.success("Image generated and loaded into the canvas!")
        else:
            st.warning("Please draw or upload an image first.")
    elif tool == "Image-to-Video":
        st.subheader("🎞️ Image-to-Video")
        image_file = st.file_uploader("Upload Image for Video", type=["png", "jpg", "jpeg"], key="video_image")
        if image_file:
            image = Image.open(image_file)
            # Resize image to 768x768
            image = image.resize((768, 768))
            st.image(image, caption="Input Image (Resized to 768x768)", use_column_width=True)
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            files = {
                "image": buffered.getvalue(),
            }
            cfg_scale = st.number_input("CFG Scale", min_value=0.0, max_value=10.0, value=1.8, key="video_cfg_scale")
            motion_bucket_id = st.number_input("Motion Bucket ID", min_value=1, max_value=255, value=127, key="video_motion_bucket")
            seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="video_seed")
            video_button = st.button("Generate Video", key="video_button")
            if video_button:
                with st.spinner("Generating video..."):
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
        else:
            st.warning("Please upload an image for video generation.")

# Footer with file management
st.markdown("---")
st.header("📁 Your Generated Files")

# List all files in the 'generated_images' directory
files = os.listdir("generated_images")
images = [file for file in files if file.endswith(('.png', '.jpg', '.jpeg', '.webp'))]
videos = [file for file in files if file.endswith('.mp4')]
models = [file for file in files if file.endswith('.glb')]

if images:
    st.subheader("Images")
    cols = st.columns(4)
    for idx, img_file in enumerate(images):
        img_path = os.path.join("generated_images", img_file)
        img = Image.open(img_path)
        cols[idx % 4].image(img, caption=img_file)
else:
    st.write("No images found.")

if videos:
    st.subheader("Videos")
    for video_file in videos:
        video_path = os.path.join("generated_images", video_file)
        video_bytes = open(video_path, 'rb').read()
        st.video(video_bytes)
else:
    st.write("No videos found.")

if models:
    st.subheader("3D Models")
    for model_file in models:
        model_path = os.path.join("generated_images", model_file)
        glb_data = open(model_path, 'rb').read()
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
    st.write("No 3D models found.")
