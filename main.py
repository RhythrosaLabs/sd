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
api_key = st.sidebar.text_input("Enter your Stability AI API Key", type="password")

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Text-to-Image", "Image-to-Image", "Image-to-Image Masking",
    "Image Upscaling", "Image Editing", "Image Control",
    "Video Generation", "3D Generation"
])

with st.sidebar:
    st.header("User Account")
    if st.button("View Account Details"):
        response = requests.get(
            "https://api.stability.ai/v1/user/account",
            headers=headers,
        )
        if response.status_code == 200:
            account_info = response.json()
            st.json(account_info)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")

    if st.button("View Account Balance"):
        response = requests.get(
            "https://api.stability.ai/v1/user/balance",
            headers=headers,
        )
        if response.status_code == 200:
            balance_info = response.json()
            st.json(balance_info)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")

with tab1:
    st.header("Text-to-Image Generation")
    engines = get_engines()
    engine_id = st.selectbox("Select Engine", engines)
    prompt = st.text_area("Prompt")
    height = st.number_input("Height", value=512, step=64)
    width = st.number_input("Width", value=512, step=64)
    cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0)
    sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL",
                                       "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL",
                                       "K_HEUN", "K_LMS"])
    samples = st.number_input("Samples", min_value=1, max_value=10, value=1)
    steps = st.number_input("Steps", min_value=10, max_value=50, value=30)
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0)
    style_preset = st.selectbox(
        "Style Preset",
        ["None", "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art", "enhance",
         "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound", "neon-punk", "origami",
         "photographic", "pixel-art", "tile-texture"]
    )
    generate_button = st.button("Generate Image")

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

with tab2:
    st.header("Image-to-Image Generation with Prompt")
    engines = get_engines()
    engine_id = st.selectbox("Select Engine", engines)
    init_image_file = st.file_uploader("Upload Initial Image", type=["png", "jpg", "jpeg", "webp"])
    if init_image_file:
        init_image = Image.open(init_image_file)
        st.image(init_image, caption="Initial Image")
    prompt = st.text_area("Prompt")
    image_strength = st.slider("Image Strength", min_value=0.0, max_value=1.0, value=0.35)
    cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0)
    sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL",
                                       "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL",
                                       "K_HEUN", "K_LMS"])
    samples = st.number_input("Samples", min_value=1, max_value=10, value=1)
    steps = st.number_input("Steps", min_value=10, max_value=50, value=30)
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0)
    style_preset = st.selectbox(
        "Style Preset",
        ["None", "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art", "enhance",
         "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound", "neon-punk", "origami",
         "photographic", "pixel-art", "tile-texture"]
    )
    generate_button = st.button("Generate Image")

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

with tab3:
    st.header("Image-to-Image Generation with Mask")
    engines = get_engines()
    engine_id = st.selectbox("Select Engine", engines)
    init_image_file = st.file_uploader("Upload Initial Image", type=["png", "jpg", "jpeg", "webp"])
    mask_image_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"])
    if init_image_file:
        init_image = Image.open(init_image_file)
        st.image(init_image, caption="Initial Image")
    if mask_image_file:
        mask_image = Image.open(mask_image_file)
        st.image(mask_image, caption="Mask Image")
    prompt = st.text_area("Prompt")
    mask_source = st.selectbox("Mask Source", ["MASK_IMAGE_WHITE", "MASK_IMAGE_BLACK", "INIT_IMAGE_ALPHA"])
    cfg_scale = st.slider("CFG Scale", min_value=0.0, max_value=35.0, value=7.0)
    sampler = st.selectbox("Sampler", ["DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL",
                                       "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL",
                                       "K_HEUN", "K_LMS"])
    samples = st.number_input("Samples", min_value=1, max_value=10, value=1)
    steps = st.number_input("Steps", min_value=10, max_value=50, value=30)
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967295, value=0)
    style_preset = st.selectbox(
        "Style Preset",
        ["None", "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art", "enhance",
         "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound", "neon-punk", "origami",
         "photographic", "pixel-art", "tile-texture"]
    )
    generate_button = st.button("Generate Image")

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

with tab4:
    st.header("Image Upscaling")
    upscale_type = st.selectbox("Select Upscaler", ["Fast", "Conservative", "Creative"])
    image_file = st.file_uploader("Upload Image to Upscale", type=["png", "jpg", "jpeg", "webp"])
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Original Image")

    if upscale_type == "Fast":
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"])
        upscale_button = st.button("Upscale Image")
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
        prompt = st.text_area("Prompt")
        negative_prompt = st.text_area("Negative Prompt")
        seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0)
        creativity = st.slider("Creativity", min_value=0.2, max_value=0.5, value=0.35)
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"])
        upscale_button = st.button("Upscale Image")
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
        prompt = st.text_area("Prompt")
        negative_prompt = st.text_area("Negative Prompt")
        seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0)
        creativity = st.slider("Creativity", min_value=0.0, max_value=0.35, value=0.3)
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"])
        upscale_button = st.button("Start Upscaling")
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

with tab5:
    st.header("Stable Image Editing")
    edit_type = st.selectbox("Select Edit Type", ["Inpaint", "Outpaint", "Erase", "Search and Replace", "Search and Recolor", "Remove Background"])
    image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"])
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Original Image")

    if edit_type == "Inpaint":
        prompt = st.text_area("Prompt")
        negative_prompt = st.text_area("Negative Prompt")
        mask_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"])
        seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0)
        grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=100, value=5)
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"])
        inpaint_button = st.button("Inpaint")

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
        prompt = st.text_area("Prompt")
        negative_prompt = st.text_area("Negative Prompt")
        left = st.number_input("Left Expansion (pixels)", min_value=0, max_value=2000, value=0)
        right = st.number_input("Right Expansion (pixels)", min_value=0, max_value=2000, value=0)
        up = st.number_input("Up Expansion (pixels)", min_value=0, max_value=2000, value=0)
        down = st.number_input("Down Expansion (pixels)", min_value=0, max_value=2000, value=0)
        seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0)
        creativity = st.slider("Creativity", min_value=0.0, max_value=1.0, value=0.5)
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"])
        outpaint_button = st.button("Outpaint")

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
        mask_file = st.file_uploader("Upload Mask Image", type=["png", "jpg", "jpeg", "webp"])
        grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=20, value=5)
        seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0)
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"])
        erase_button = st.button("Erase")

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
        prompt = st.text_area("Prompt")
        search_prompt = st.text_input("Search Prompt")
        negative_prompt = st.text_area("Negative Prompt")
        grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=20, value=3)
        seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0)
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"])
        replace_button = st.button("Search and Replace")

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
        prompt = st.text_area("Prompt")
        select_prompt = st.text_input("Select Prompt")
        negative_prompt = st.text_area("Negative Prompt")
        grow_mask = st.number_input("Grow Mask (pixels)", min_value=0, max_value=20, value=3)
        seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0)
        output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"])
        recolor_button = st.button("Search and Recolor")

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
        output_format = st.selectbox("Output Format", ["png", "webp"])
        remove_bg_button = st.button("Remove Background")

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

with tab6:
    st.header("Image Control")
    control_type = st.selectbox("Select Control Type", ["Sketch", "Structure", "Style"])
    image_file = st.file_uploader("Upload Control Image", type=["png", "jpg", "jpeg", "webp"])
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Control Image")

    prompt = st.text_area("Prompt")
    negative_prompt = st.text_area("Negative Prompt")
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0)
    output_format = st.selectbox("Output Format", ["png", "jpeg", "webp"])

    if control_type == "Sketch":
        control_strength = st.slider("Control Strength", min_value=0.0, max_value=1.0, value=0.7)
        control_button = st.button("Generate Image")

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
        control_strength = st.slider("Control Strength", min_value=0.0, max_value=1.0, value=0.7)
        control_button = st.button("Generate Image")

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
        fidelity = st.slider("Fidelity", min_value=0.0, max_value=1.0, value=0.5)
        aspect_ratio = st.selectbox("Aspect Ratio", ["1:1", "16:9", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"])
        control_button = st.button("Generate Image")

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

with tab7:
    st.header("Image to Video Generation")
    image_file = st.file_uploader("Upload Initial Image", type=["png", "jpg", "jpeg"])
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Initial Image")
    cfg_scale = st.number_input("CFG Scale", min_value=0.0, max_value=10.0, value=1.8)
    motion_bucket_id = st.number_input("Motion Bucket ID", min_value=1, max_value=255, value=127)
    seed = st.number_input("Seed (0 for random)", min_value=0, max_value=4294967294, value=0)
    video_button = st.button("Generate Video")

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

with tab8:
    st.header("3D Model Generation")
    image_file = st.file_uploader("Upload Image for 3D Model", type=["png", "jpg", "jpeg", "webp"])
    if image_file:
        image = Image.open(image_file)
        st.image(image, caption="Input Image")
    texture_resolution = st.selectbox("Texture Resolution", [512, 1024, 2048])
    foreground_ratio = st.slider("Foreground Ratio", min_value=0.1, max_value=1.0, value=0.85)
    remesh = st.selectbox("Remesh", ["none", "quad", "triangle"])
    vertex_count = st.number_input("Vertex Count (-1 for default)", min_value=-1, max_value=20000, value=-1)
    model_button = st.button("Generate 3D Model")

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
