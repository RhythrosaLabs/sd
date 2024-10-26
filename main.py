# app.py

import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO
import base64
import time

st.set_page_config(layout="wide")

# Sidebar for API Key
st.sidebar.title("API Configuration")
api_key = st.sidebar.text_input("Enter your Stability AI API Key", type="password", key="api_key")

if not api_key:
    st.warning("Please enter your API key to continue.")
    st.stop()

headers = {
    "Authorization": f"Bearer {api_key}",
}

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
            for artifact in artifacts:
                img_data = base64.b64decode(artifact['base64'])
                img = Image.open(BytesIO(img_data))
                st.image(img)
        else:
            img = Image.open(BytesIO(response.content))
            st.image(img)
    else:
        try:
            st.error(f"Error: {response.status_code} - {response.json()}")
        except:
            st.error(f"Error: {response.status_code} - {response.text}")

def display_video(response):
    if response.status_code == 200:
        video_bytes = response.content
        st.video(video_bytes)
    else:
        try:
            st.error(f"Error: {response.status_code} - {response.json()}")
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
            st.error(f"Error: {response.status_code} - {response.json()}")
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
    "Text-to-Image", "Image-to-Image", "Image-to-Image Masking",
    "Image Upscaling", "Image Editing", "Image Control",
    "Video Generation", "3D Generation"
]
tabs = st.tabs(tab_titles)

# Sidebar - User Account
with st.sidebar:
    st.header("User Account")
    if st.button("View Account Details", key="account_details"):
        response = requests.get(
            "https://api.stability.ai/v1/user/account",
            headers=headers,
        )
        if response.status_code == 200:
            account_info = response.json()
            st.json(account_info)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")

    if st.button("View Account Balance", key="account_balance"):
        response = requests.get(
            "https://api.stability.ai/v1/user/balance",
            headers=headers,
        )
        if response.status_code == 200:
            balance_info = response.json()
            st.json(balance_info)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")

# Text-to-Image Tab
with tabs[0]:
    st.header("Text-to-Image Generation")
    engines = get_engines()
    engine_id = st.selectbox("Select Engine", engines, key="tti_engine")
    prompt = st.text_area("Prompt", key="tti_prompt")
    height = st.number_input("Height", value=512, step=64, key="tti_height")
    width = st.number_input("Width", value=512, step=64, key="tti_width")
    cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0, key="tti_cfg_scale")
    sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL",
                                       "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL",
                                       "K_HEUN", "K_LMS"], key="tti_sampler")
    samples = st.number_input("Samples", min_value=1, max_value=10, value=1, key="tti_samples")
    steps = st.number_input("Steps", min_value=10, max_value=50, value=30, key="tti_steps")
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0, key="tti_seed")
    style_preset = st.selectbox(
        "Style Preset",
        ["None", "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art", "enhance",
         "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound", "neon-punk", "origami",
         "photographic", "pixel-art", "tile-texture"],
        key="tti_style_preset"
    )
    generate_button = st.button("Generate Image", key="tti_generate")

    if generate_button:
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
        if style_preset != "None":
            json_body["style_preset"] = style_preset
        response = requests.post(
            f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=json_body,
        )
        display_image(response)

# Image-to-Image Tab
with tabs[1]:
    st.header("Image-to-Image Generation with Prompt")
    engines = get_engines()
    engine_id = st.selectbox("Select Engine", engines, key="iti_engine")
    init_image_file = st.file_uploader("Upload Initial Image", type=["png", "jpg", "jpeg", "webp"], key="iti_init_image")
    if init_image_file:
        init_image = Image.open(init_image_file)
        st.image(init_image, caption="Initial Image")
    prompt = st.text_area("Prompt", key="iti_prompt")
    image_strength = st.slider("Image Strength", min_value=0.0, max_value=1.0, value=0.35, key="iti_image_strength")
    cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0, key="iti_cfg_scale")
    sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL",
                                       "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL",
                                       "K_HEUN", "K_LMS"], key="iti_sampler")
    samples = st.number_input("Samples", min_value=1, max_value=10, value=1, key="iti_samples")
    steps = st.number_input("Steps", min_value=10, max_value=50, value=30, key="iti_steps")
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0, key="iti_seed")
    style_preset = st.selectbox(
        "Style Preset",
        ["None", "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art", "enhance",
         "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound", "neon-punk", "origami",
         "photographic", "pixel-art", "tile-texture"],
        key="iti_style_preset"
    )
    generate_button = st.button("Generate Image", key="iti_generate")

    if generate_button and init_image_file:
        files = {
            "init_image": init_image_file.getvalue(),
        }
        data = {
            "text_prompts[0][text]": prompt,
            "image_strength": image_strength,
            "cfg_scale": cfg_scale,
            "sampler": sampler,
            "samples": samples,
            "steps": steps,
            "seed": seed,
            "init_image_mode": "IMAGE_STRENGTH",
        }
        if style_preset != "None":
            data["style_preset"] = style_preset
        response = requests.post(
            f"https://api.stability.ai/v1/generation/{engine_id}/image-to-image",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            files=files,
            data=data,
        )
        display_image(response)

# Image-to-Image Masking Tab
with tabs[2]:
    st.header("Image-to-Image Generation with Mask")
    engines = get_engines()
    engine_id = st.selectbox("Select Engine", engines, key="mask_engine")
    init_image_file = st.file_uploader("Upload Initial Image", type=["png", "jpg", "jpeg", "webp"], key="mask_init_image")
    mask_image_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"], key="mask_mask_image")
    if init_image_file:
        init_image = Image.open(init_image_file)
        st.image(init_image, caption="Initial Image")
    if mask_image_file:
        mask_image = Image.open(mask_image_file)
        st.image(mask_image, caption="Mask Image")
    prompt = st.text_area("Prompt", key="mask_prompt")
    mask_source = st.selectbox("Mask Source", ["MASK_IMAGE_WHITE", "MASK_IMAGE_BLACK", "INIT_IMAGE_ALPHA"], key="mask_source")
    cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0, key="mask_cfg_scale")
    sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL",
                                       "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL",
                                       "K_HEUN", "K_LMS"], key="mask_sampler")
    samples = st.number_input("Samples", min_value=1, max_value=10, value=1, key="mask_samples")
    steps = st.number_input("Steps", min_value=10, max_value=50, value=30, key="mask_steps")
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0, key="mask_seed")
    style_preset = st.selectbox(
        "Style Preset",
        ["None", "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art", "enhance",
         "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound", "neon-punk", "origami",
         "photographic", "pixel-art", "tile-texture"],
        key="mask_style_preset"
    )
    generate_button = st.button("Generate Image", key="mask_generate")

    if generate_button and init_image_file and mask_image_file:
        files = {
            "init_image": init_image_file.getvalue(),
            "mask_image": mask_image_file.getvalue(),
        }
        data = {
            "text_prompts[0][text]": prompt,
            "mask_source": mask_source,
            "cfg_scale": cfg_scale,
            "sampler": sampler,
            "samples": samples,
            "steps": steps,
            "seed": seed,
        }
        if style_preset != "None":
            data["style_preset"] = style_preset
        response = requests.post(
            f"https://api.stability.ai/v1/generation/{engine_id}/image-to-image/masking",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            files=files,
            data=data,
        )
        display_image(response)

# Image Upscaling Tab
with tabs[3]:
    st.header("Image Upscaling")
    upscale_type = st.selectbox("Select Upscaler", ["Fast", "Conservative", "Creative"], key="upscale_type")
    image_file = st.file_uploader("Upload Image to Upscale", type=["png", "jpg", "jpeg", "webp"], key="upscale_image")
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Original Image")
    if upscale_type == "Fast":
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="fast_output_format")
        upscale_button = st.button("Upscale Image", key="fast_upscale_button")
        if upscale_button and image_file:
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

# Image Editing Tab
with tabs[4]:
    st.header("Stable Image Editing")
    edit_type = st.selectbox("Select Edit Type", ["Inpaint", "Outpaint", "Erase", "Search and Replace", "Search and Recolor", "Remove Background"], key="edit_type")
    image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"], key="edit_image")
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Original Image")

    if edit_type == "Inpaint":
        prompt = st.text_area("Prompt", key="inpaint_prompt")
        negative_prompt = st.text_area("Negative Prompt", key="inpaint_negative_prompt")
        mask_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"], key="inpaint_mask")
        seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="inpaint_seed")
        grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=100, value=5, key="inpaint_grow_mask")
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="inpaint_output_format")
        inpaint_button = st.button("Inpaint", key="inpaint_button")

        if inpaint_button and image_file and mask_file:
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

# Image Control Tab
with tabs[5]:
    st.header("Image Control")
    control_type = st.selectbox("Select Control Type", ["Sketch", "Structure", "Style"], key="control_type")
    image_file = st.file_uploader("Upload Control Image", type=["png", "jpg", "jpeg", "webp"], key="control_image")
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Control Image")

    prompt = st.text_area("Prompt", key="control_prompt")
    negative_prompt = st.text_area("Negative Prompt", key="control_negative_prompt")
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="control_seed")
    output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"], key="control_output_format")

    if control_type == "Sketch":
        control_strength = st.slider("Control Strength", min_value=0.0, max_value=1.0, value=0.7, key="sketch_control_strength")
        control_button = st.button("Generate Image", key="sketch_control_button")

        if control_button and image_file:
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

# Video Generation Tab
with tabs[6]:
    st.header("Image to Video Generation")
    image_file = st.file_uploader("Upload Initial Image", type=["png", "jpg", "jpeg"], key="video_image")
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Initial Image")
    cfg_scale = st.number_input("CFG Scale", min_value=0.0, max_value=10.0, value=1.8, key="video_cfg_scale")
    motion_bucket_id = st.number_input("Motion Bucket ID", min_value=1, max_value=255, value=127, key="video_motion_bucket")
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0, key="video_seed")
    video_button = st.button("Generate Video", key="video_button")

    if video_button and image_file:
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

# 3D Generation Tab
with tabs[7]:
    st.header("3D Model Generation")
    image_file = st.file_uploader("Upload Image for 3D Model", type=["png", "jpg", "jpeg", "webp"], key="3d_image")
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Input Image")
    texture_resolution = st.selectbox("Texture Resolution", [512, 1024, 2048], key="3d_texture_resolution")
    foreground_ratio = st.slider("Foreground Ratio", min_value=0.1, max_value=1.0, value=0.85, key="3d_foreground_ratio")
    remesh = st.selectbox("Remesh", ["none", "quad", "triangle"], key="3d_remesh")
    vertex_count = st.number_input("Vertex Count (-1 for default)", min_value=-1, max_value=20000, value=-1, key="3d_vertex_count")
    model_button = st.button("Generate 3D Model", key="3d_model_button")

    if model_button and image_file:
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
