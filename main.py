import asyncio
import edge_tts
import requests
import urllib.parse
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# 1. Aapki Kahani / Script
SCRIPT_SCENES = [
    {"text": "Ek chhote se gaon me ek udas ladka rehta tha.", "emotion": "sad cartoon boy sitting alone under a tree, Pixar style 3d render"},
    {"text": "Achanak use ek magical sparkling khazana mila aur woh bohot khush ho gaya!", "emotion": "happy excited cartoon boy discovering a glowing treasure box, Pixar style 3d render"},
    {"text": "Usne apne dost ke sath khushi se dance kiya.", "emotion": "two joyful cartoon friends celebrating together, colorful background, 3d animation style"}
]

VOICE = "hi-IN-SwaraNeural"  # Hindi AI Voice

async def generate_voice(text, filename):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)

def generate_image(prompt, filename):
    # Free AI Image Generator (Pollinations.ai)
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)

def create_cartoon_story_video():
    clips = []
    
    for idx, scene in enumerate(SCRIPT_SCENES):
        print(f"Processing Scene {idx+1}...")
        
        audio_file = f"voice_{idx}.mp3"
        image_file = f"scene_{idx}.jpg"
        
        # Voiceover & Image generation
        asyncio.run(generate_voice(scene["text"], audio_file))
        generate_image(scene["emotion"], image_file)
        
        # Audio & Image merge
        audio = AudioFileClip(audio_file)
        image_clip = ImageClip(image_file).set_duration(audio.duration).set_audio(audio)
        clips.append(image_clip)
        
    # All scenes combined into final video
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile("cartoon_story_video.mp4", fps=24, codec='libx264', audio_codec='aac')
    print("Full Cartoon Video Created Successfully!")

# Run Script
create_cartoon_story_video()
