import os
import asyncio
import urllib.parse
import requests
import time
from flask import Flask, render_template_string, request, send_file, jsonify
import edge_tts
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Studio Pro App</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg: #090a0f;
            --card: #141622;
            --accent: #ff2a5f;
            --accent-blue: #00f2fe;
            --border: #232738;
            --text: #ffffff;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding-bottom: 70px; }
        .app-header { background: #10121d; padding: 15px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }
        .app-header h1 { font-size: 18px; margin: 0; color: #fff; font-weight: 700; display: flex; align-items: center; gap: 8px; }
        
        .main-container { max-width: 500px; margin: 0 auto; padding: 15px; }

        /* Quick AI Tool Grid */
        .tools-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
        .tool-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 12px 5px; text-align: center; cursor: pointer; transition: 0.2s; }
        .tool-card i { font-size: 20px; color: var(--accent-blue); margin-bottom: 6px; display: block; }
        .tool-card span { font-size: 11px; color: #94a3b8; font-weight: 600; }
        .tool-card:active { transform: scale(0.95); }

        /* Input Form Elements */
        label { font-size: 13px; font-weight: 600; color: #cbd5e1; margin-top: 15px; display: flex; align-items: center; gap: 6px; }
        textarea, select { width: 100%; padding: 14px; background: var(--card); border: 1px solid var(--border); border-radius: 14px; color: #fff; font-size: 14px; margin-top: 6px; box-sizing: border-box; outline: none; }
        textarea { height: 85px; resize: none; }
        textarea:focus, select:focus { border-color: var(--accent); }

        /* Upload Ingredients Area */
        .upload-container { border: 2px dashed #334155; border-radius: 16px; padding: 18px; text-align: center; background: var(--card); margin-top: 8px; cursor: pointer; transition: 0.3s; }
        .upload-container:hover { border-color: var(--accent-blue); }
        .upload-container i { font-size: 32px; color: var(--accent-blue); }
        .upload-container p { font-size: 12px; color: #94a3b8; margin: 6px 0 0 0; }
        #image-preview-grid { display: flex; gap: 8px; justify-content: center; margin-top: 10px; flex-wrap: wrap; }
        .preview-img { width: 50px; height: 50px; border-radius: 8px; object-fit: cover; border: 1px solid var(--accent); }

        .btn-generate { width: 100%; background: linear-gradient(135deg, var(--accent), #e11d48); color: white; border: none; padding: 16px; margin-top: 20px; border-radius: 16px; font-weight: bold; font-size: 16px; cursor: pointer; box-shadow: 0 8px 25px rgba(255, 42, 95, 0.4); display: flex; align-items: center; justify-content: center; gap: 10px; }
        
        /* Video Player Section */
        #preview-section { display: none; margin-top: 20px; background: var(--card); padding: 15px; border-radius: 20px; border: 1px solid var(--border); text-align: center; }
        video { width: 100%; max-height: 380px; border-radius: 12px; background: #000; }
        .action-btns { display: flex; gap: 10px; margin-top: 15px; }
        .btn-dl { flex: 1; background: #10b981; color: white; padding: 12px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 14px; }
        .btn-del { flex: 1; background: #ef4444; color: white; padding: 12px; border-radius: 12px; border: none; font-weight: bold; cursor: pointer; font-size: 14px; }

        /* Bottom App Navigation Bar */
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: #10121d; border-top: 1px solid var(--border); display: flex; justify-content: space-around; padding: 10px 0; z-index: 1000; }
        .nav-item { text-align: center; color: #64748b; font-size: 10px; text-decoration: none; }
        .nav-item i { font-size: 18px; display: block; margin-bottom: 3px; }
        .nav-item.active { color: var(--accent); }

        #loading { display: none; text-align: center; margin-top: 20px; color: var(--accent-blue); font-weight: bold; }
    </style>
</head>
<body>

    <!-- Header Bar -->
    <div class="app-header">
        <h1><i class="fa-solid fa-wand-magic-sparkles" style="color:var(--accent)"></i> Studio AI App</h1>
        <span style="font-size: 11px; background: rgba(0,242,254,0.1); color: var(--accent-blue); padding: 4px 10px; border-radius: 20px; font-weight: bold;">v3.0 Ultra</span>
    </div>

    <div class="main-container">

        <!-- Top Tools Grid -->
        <div class="tools-grid">
            <div class="tool-card"><i class="fa-solid fa-plus-circle"></i><span>Create</span></div>
            <div class="tool-card"><i class="fa-solid fa-wand-magic"></i><span>Edit AI</span></div>
            <div class="tool-card"><i class="fa-solid fa-clapperboard"></i><span>Gen Video</span></div>
            <div class="tool-card"><i class="fa-solid fa-image"></i><span>Gen Image</span></div>
        </div>

        <form id="studioForm" enctype="multipart/form-data">
            
            <!-- Upload Ingredients -->
            <label><i class="fa-solid fa-upload" style="color:var(--accent-blue)"></i> Upload Photos / Ingredients (Optional)</label>
            <div class="upload-container" onclick="document.getElementById('images').click()">
                <i class="fa-solid fa-cloud-arrow-up"></i>
                <p id="upload-label">+ Add up to 3 custom photos (Or AI will generate automatically)</p>
                <div id="image-preview-grid"></div>
                <input type="file" id="images" name="images" multiple accept="image/*" style="display:none;" onchange="handleFileSelect(this)">
            </div>

            <!-- Script Input -->
            <label><i class="fa-solid fa-align-left" style="color:var(--accent)"></i> Video Story / Script Input</label>
            <textarea name="script" id="script" required placeholder="Line 1: Bubu aur Dudu market gaye.&#10;Line 2: Unhone mast ice-cream khayi."></textarea>

            <div style="display: flex; gap: 10px;">
                <div style="flex:1;">
                    <label><i class="fa-solid fa-microphone"></i> Voiceover</label>
                    <select name="voice">
                        <option value="hi-IN-SwaraNeural">Female (Swara)</option>
                        <option value="hi-IN-MadhurNeural">Male (Madhur)</option>
                    </select>
                </div>
                <div style="flex:1;">
                    <label><i class="fa-solid fa-palette"></i> Animation Theme</label>
                    <select name="category">
                        <option value="bubududu">🧸 Bubu Dudu Cute</option>
                        <option value="tax">📊 Tax Explainer</option>
                        <option value="shorts">⚡ YouTube Shorts</option>
                    </select>
                </div>
            </div>

            <button type="submit" class="btn-generate"><i class="fa-solid fa-bolt"></i> Render Studio Video</button>
        </form>

        <div id="loading"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><br><br>Generating Video... Please wait!</div>

        <!-- Inline Video Player -->
        <div id="preview-section">
            <h3 style="color:#10b981; margin: 0 0 10px 0; font-size:16px;">✨ Video Preview Ready!</h3>
            <video id="videoPlayer" controls autoplay></video>
            <div class="action-btns">
                <a id="downloadBtn" href="" download="studio_video.mp4" class="btn-dl"><i class="fa-solid fa-download"></i> Save Video</a>
                <button onclick="deleteVideo()" class="btn-del"><i class="fa-solid fa-trash"></i> Delete</button>
            </div>
        </div>
    </div>

    <!-- Mobile Navigation Bar -->
    <div class="bottom-nav">
        <a href="#" class="nav-item active"><i class="fa-solid fa-house"></i>Home</a>
        <a href="#" class="nav-item"><i class="fa-solid fa-compass"></i>Explore</a>
        <a href="#" class="nav-item"><i class="fa-solid fa-folder"></i>Projects</a>
        <a href="#" class="nav-item"><i class="fa-solid fa-user"></i>Profile</a>
    </div>

    <script>
        let currentVideoPath = "";

        function handleFileSelect(input) {
            const grid = document.getElementById('image-preview-grid');
            grid.innerHTML = '';
            if (input.files) {
                Array.from(input.files).forEach(file => {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'preview-img';
                        grid.appendChild(img);
                    }
                    reader.readAsDataURL(file);
                });
                document.getElementById('upload-label').innerText = `${input.files.length} Photo(s) Selected!`;
            }
        }

        document.getElementById('studioForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            document.getElementById('loading').style.display = 'block';
            document.getElementById('preview-section').style.display = 'none';

            const formData = new FormData(this);
            const response = await fetch('/generate', { method: 'POST', body: formData });
            const data = await response.json();

            document.getElementById('loading').style.display = 'none';

            if(data.status === 'success') {
                currentVideoPath = data.video_url;
                const player = document.getElementById('videoPlayer');
                player.src = data.video_url;
                document.getElementById('downloadBtn').href = data.video_url;
                document.getElementById('preview-section').style.display = 'block';
            } else {
                alert("Error: " + data.message);
            }
        });

        async function deleteVideo() {
            if(confirm("Video delete karein?")) {
                await fetch('/delete?file=' + currentVideoPath);
                document.getElementById('preview-section').style.display = 'none';
                alert("Deleted!");
            }
        }
    </script>
</body>
</html>
"""

async def generate_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def create_ai_image(prompt, output_path):
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&nologo=true"
    res = requests.get(url, timeout=30)
    if res.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(res.content)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        script_raw = request.form.get('script', '')
        category = request.form.get('category', 'bubududu')
        voice = request.form.get('voice', 'hi-IN-SwaraNeural')
        uploaded_files = request.files.getlist('images')

        lines = [line.strip() for line in script_raw.split('\n') if line.strip()]
        if not lines:
            return jsonify({'status': 'error', 'message': 'Script khali hai!'})

        os.makedirs('static', exist_ok=True)
        clips = []
        valid_uploads = [f for f in uploaded_files if f.filename != '']

        for idx, line in enumerate(lines):
            audio_path = f"audio_{idx}.mp3"
            image_path = f"img_{idx}.jpg"

            # Async TTS Voiceover
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate_tts(line, voice, audio_path))
            loop.close()

            # Image logic
            if valid_uploads and idx < len(valid_uploads):
                valid_uploads[idx].save(image_path)
            else:
                prompt = f"{line}, {category} cartoon style 3d"
                create_ai_image(prompt, image_path)

            audio = AudioFileClip(audio_path)
            img_clip = ImageClip(image_path).with_duration(audio.duration).with_audio(audio)
            clips.append(img_clip)

        timestamp = int(time.time())
        output_filename = f"static/video_{timestamp}.mp4"

        final_video = concatenate_videoclips(clips, method="compose")
        final_video.write_videofile(output_filename, fps=24, codec='libx264', audio_codec='aac')

        return jsonify({'status': 'success', 'video_url': f'/{output_filename}'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/static/<filename>')
def serve_video(filename):
    return send_file(f"static/{filename}", mimetype='video/mp4')

@app.route('/delete')
def delete_file():
    file_path = request.args.get('file', '').lstrip('/')
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'status': 'deleted'})
    return jsonify({'status': 'not found'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
