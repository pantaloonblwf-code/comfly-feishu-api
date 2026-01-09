import os
import requests
import base64
import io
from PIL import Image
from flask import Flask, request, jsonify

app = Flask(__name__)

API_URL = "https://ai.comfly.chat/v1/images/generations"
API_KEY = os.getenv("COMFLY_API_KEY")  # 安全：从环境变量读取

def generate_single(prompt, ref_img_pil, aspect_ratio, quality):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    if quality in ("2K", "4K"):
        payload = {
            "model": "nano-banana-2",
            "prompt": prompt,
            "response_format": "url",
            "aspect_ratio": aspect_ratio,
            "image_size": quality
        }
    else:
        payload = {
            "model": "nano-banana",
            "prompt": prompt,
            "response_format": "url",
            "aspect_ratio": aspect_ratio
        }
    
    if ref_img_pil:
        buffer = io.BytesIO()
        ref_img_pil.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        payload["image"] = [f"data:image/png;base64,{img_str}"]
    
    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=120)
        if resp.status_code == 200:
            return resp.json()["data"][0]["url"]
        else:
            return f"ERROR_{resp.status_code}"
    except Exception as e:
        return f"EXCEPTION_{str(e)}"

@app.route('/batch-generate', methods=['POST'])
def batch_generate():
    data = request.json
    base_prompt = data.get("base_prompt", "")
    specific_prompts = data.get("specific_prompts", [])
    aspect_ratio = data.get("aspect_ratio", "1:1")
    quality = data.get("quality", "1K")
    ref_image_url = data.get("ref_image_url")

    ref_pil = None
    if ref_image_url and ref_image_url.startswith("http"):
        try:
            img_data = requests.get(ref_image_url, timeout=10).content
            ref_pil = Image.open(io.BytesIO(img_data))
        except:
            pass

    results = []
    for i in range(5):
        sp = specific_prompts[i] if i < len(specific_prompts) else ""
        if not sp.strip():
            results.append("")
            continue
        full_prompt = f"{base_prompt} {sp}".strip()
        url = generate_single(full_prompt, ref_pil, aspect_ratio, quality)
        results.append(url)
    
    return jsonify({
        "result_1": results[0],
        "result_2": results[1],
        "result_3": results[2],
        "result_4": results[3],
        "result_5": results[4]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
