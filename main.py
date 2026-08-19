import os
import asyncio
import urllib.parse
import requests
from flask import Flask, render_template_string, request, send_file
import edge_tts
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Tax Shorts Generator</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #f8fafc; margin:0; padding:20px; }
        .card { max-width: 600px; margin: 30px auto; background: #1e293b; padding: 25px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h2 { color: #38bdf8; text-align: center; margin-bottom: 20px; }
        label { font-weight: 600; display: block; margin-top: 15px; color: #94a3b8; }
        textarea, select { width: 100%; padding: 12px; margin-top: 6px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: white; box-sizing: border-box; }
        textarea { height: 120px; }
        button { width: 100%; background: #0284c7; color: white; border: none; padding: 15px; margin-top: 25px; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; transition: 0.3s; }
        button:hover { background: #0369a1; }
        .badge { background: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; float: right; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📊 AI Tax & Story Video Studio <span class="badge">40s Limit Active</span></h2>
        <form action="/generate" method="post">
            <label>1. Script / Tax Tips (3-4 Choti Lines Likhein):</label>
            <textarea name="script" required placeholder="Line 1: Tax bachana chahte hain? Yeh simple tip dekhein.&#10;Line 2: Section 80C me invest karke aap 1.5 Lakh tak tax bacha sakte hain.&#10;Line 3: Aaj hi apne financial planner se baat karein!"></textarea>

            <label>2. Voice Select Karein:</label>
            <select name="voice">
                <option value="hi-IN-SwaraNeural">Female Voice (Swara - Hindi)</option>
                <option value="hi-IN-MadhurNeural">Male Voice (Madhur - Hindi)</option>
            </select>

            <label>3. Visual Art Style:</label>
            <select name="art_style">
                <option value="2d cartoon explainer style character talking about money tax, clean corporate background">Tax Explainer (2D Cartoon)</option>
                <option value="3d pixar style professional accountant explaining finance with charts">3D Pixar Finance Style</option>
            </select>

            <button type="submit">🚀 Generate 40s Video</button>
        </form>
    </div>
</body>
</html>
"""

async def text_to_speech(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def create_image(prompt, output_path):
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
    res = requests.get(url)
    if res.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(res.content)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    script_raw = request.form.get('script', '')
    art_style = request.form.get('art_style', '')
    voice = request.form.get('voice', 'hi-IN-SwaraNeural')

    lines = [line.strip() for line in script_raw.split('\n') if line.strip()]
    if not lines:
        return "Script khali hai!", 400

    clips = []
    total_duration = 0
    MAX_DURATION = 45.0  # Safe limit for 40 sec short video

    for idx, line in enumerate(lines):
        if total_duration >= MAX_DURATION:
            break

        audio_path = f"audio_{idx}.mp3"
        image_path = f"img_{idx}.jpg"
        
        # Audio & Image Generate
        asyncio.run(text_to_speech(line, voice, audio_path))
        full_prompt = f"{line}, {art_style}"
        create_image(full_prompt, image_path)
        
        audio = AudioFileClip(audio_path)
        img_clip = ImageClip(image_path).with_duration(audio.duration).with_audio(audio)
        
        clips.append(img_clip)
        total_duration += audio.duration

    output_video = "tax_short_video.mp4"
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(output_video, fps=24, codec='libx264', audio_codec='aac')

    return send_file(output_video, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
