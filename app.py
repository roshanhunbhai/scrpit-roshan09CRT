import os
import asyncio
import urllib.parse
import requests
from flask import Flask, render_template_string, request, send_file
import edge_tts
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

app = Flask(__name__)

# Classic Mobile & Web Responsive Dashboard Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Video Creator Studio</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent-color: #38bdf8;
            --btn-color: #0284c7;
            --text-color: #f8fafc;
        }
        body {
            font-family: 'Segoe UI', Inter, system-ui, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 15px;
        }
        .app-container {
            max-width: 750px;
            margin: 10px auto;
            background: var(--card-bg);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            border: 1px solid #334155;
        }
        .header {
            text-align: center;
            border-bottom: 1px solid #334155;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .header h1 {
            color: var(--accent-color);
            font-size: 24px;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .header p {
            color: #94a3b8;
            font-size: 13px;
            margin-top: 5px;
        }
        .section-title {
            font-weight: 600;
            color: #cbd5e1;
            margin-top: 18px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }
        textarea, select {
            width: 100%;
            padding: 12px;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 10px;
            color: white;
            box-sizing: border-box;
            font-size: 14px;
            outline: none;
            transition: 0.3s;
        }
        textarea:focus, select:focus {
            border-color: var(--accent-color);
        }
        textarea { height: 100px; resize: vertical; }
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        @media (max-width: 500px) {
            .grid-2 { grid-template-columns: 1fr; }
        }
        .btn-generate {
            width: 100%;
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: white;
            border: none;
            padding: 16px;
            margin-top: 25px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(2, 132, 199, 0.4);
            transition: 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .btn-generate:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(2, 132, 199, 0.6);
        }
        .badge {
            background: #10b981;
            color: black;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header">
            <h1><i class="fa-solid fa-wand-magic-sparkles"></i> AI Studio Creator</h1>
            <p>Generate Shorts, Tax Videos & Bubu Dudu Animations in seconds</p>
        </div>

        <form action="/generate" method="post">
            
            <div class="section-title">
                <i class="fa-solid fa-pen-to-square"></i> 1. Script / Story Input (1 line per scene)
            </div>
            <textarea name="script" required placeholder="Line 1: Tax bachana chahte hain? Yeh simple tips dekhein.&#10;Line 2: Section 80C me invest karke aap 1.5 Lakh tak bacha sakte hain."></textarea>

            <div class="grid-2">
                <div>
                    <div class="section-title"><i class="fa-solid fa-clapperboard"></i> 2. Category / Preset</div>
                    <select name="category">
                        <option value="tax">📊 Tax & Finance Explainer</option>
                        <option value="bubududu">🧸 Bubu Dudu Cute Animation</option>
                        <option value="shorts">⚡ YouTube Shorts / Reels</option>
                        <option value="horror">👻 Horror / Thriller Story</option>
                    </select>
                </div>
                <div>
                    <div class="section-title"><i class="fa-solid fa-microphone"></i> 3. AI Voiceover</div>
                    <select name="voice">
                        <option value="hi-IN-SwaraNeural">Female Voice (Swara - Hindi)</option>
                        <option value="hi-IN-MadhurNeural">Male Voice (Madhur - Hindi)</option>
                    </select>
                </div>
            </div>

            <div class="grid-2">
                <div>
                    <div class="section-title"><i class="fa-solid fa-mobile-screen"></i> 4. Video Ratio</div>
                    <select name="aspect_ratio">
                        <option value="vertical">9:16 (Shorts / Reels)</option>
                        <option value="landscape">16:9 (YouTube Horizontal)</option>
                    </select>
                </div>
                <div>
                    <div class="section-title"><i class="fa-solid fa-palette"></i> 5. Custom Style (Optional)</div>
                    <select name="art_style">
                        <option value="3d pixar animation style, highly detailed, vibrant colors">3D Pixar Animated</option>
                        <option value="2d clean corporate vector illustration animation">2D Corporate Explainer</option>
                        <option value="retro vintage comic art style, highly detailed">Retro Comic Style</option>
                    </select>
                </div>
            </div>

            <button type="submit" class="btn-generate">
                <i class="fa-solid fa-bolt"></i> Generate & Download Video
            </button>
        </form>
    </div>
</body>
</html>
"""

async def generate_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def create_image(prompt, aspect_ratio, output_path):
    width, height = (720, 1280) if aspect_ratio == "vertical" else (1280, 720)
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    res = requests.get(url, timeout=30)
    if res.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(res.content)
        return True
    return False

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        script_raw = request.form.get('script', '')
        category = request.form.get('category', 'tax')
        voice = request.form.get('voice', 'hi-IN-SwaraNeural')
        aspect_ratio = request.form.get('aspect_ratio', 'vertical')
        art_style = request.form.get('art_style', '')

        lines = [line.strip() for line in script_raw.split('\n') if line.strip()]
        if not lines:
            return "Script empty hai!", 400

        # Category Specific Style Addons
        category_prompts = {
            "tax": "professional 2d corporate character explaining finance and tax savings",
            "bubududu": "cute white bear and brown bear cartoon characters Bubu Dudu style, fluffy romantic",
            "shorts": "vibrant eye catching dynamic cartoon scene",
            "horror": "dark creepy horror atmosphere animated character"
        }
        
        base_style = category_prompts.get(category, "")
        final_art_prompt = f"{base_style}, {art_style}"

        clips = []

        for idx, line in enumerate(lines):
            audio_path = f"audio_{idx}.mp3"
            image_path = f"img_{idx}.jpg"

            # Safe Async TTS Generation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate_tts(line, voice, audio_path))
            loop.close()

            # Dynamic Image Prompting
            full_prompt = f"{line}, {final_art_prompt}"
            create_image(full_prompt, aspect_ratio, image_path)

            # Audio-Visual Syncing
            audio = AudioFileClip(audio_path)
            img_clip = ImageClip(image_path).with_duration(audio.duration).with_audio(audio)
            clips.append(img_clip)

        output_video = "studio_rendered_video.mp4"
        final_video = concatenate_videoclips(clips, method="compose")
        final_video.write_videofile(output_video, fps=24, codec='libx264', audio_codec='aac')

        return send_file(output_video, as_attachment=True)

    except Exception as e:
        return f"<h3>Render Error Log:</h3><p>{str(e)}</p>", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
