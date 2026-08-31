import os
import requests
import asyncio
import edge_tts
from flask import Flask, request, render_template_string, send_file
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Video Creator</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; display: flex; justify-content: center; }
        .card { background: #1e293b; padding: 25px; border-radius: 12px; width: 100%; max-width: 500px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
        h1 { font-size: 24px; color: #38bdf8; text-align: center; margin-bottom: 20px; }
        label { display: block; margin-top: 15px; font-weight: bold; }
        input, select, button { width: 100%; padding: 12px; margin-top: 8px; border-radius: 8px; border: 1px solid #334155; box-sizing: border-box; background: #0f172a; color: #fff; }
        button { background: #0284c7; color: white; font-weight: bold; border: none; margin-top: 20px; cursor: pointer; }
        .res { margin-top: 20px; padding: 15px; background: #0f172a; border-radius: 8px; border-left: 4px solid #38bdf8; }
        video { width: 100%; border-radius: 8px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎬 AI Video Generator</h1>
        <form method="POST">
            <label>ਵੀਡੀਓ ਦਾ ਟੌਪਿਕ ਲਿਖੋ:</label>
            <input type="text" name="topic" placeholder="e.g. 3 Morning Habits, Nature facts" required>
            <label>ਭਾਸ਼ਾ (Voice Language):</label>
            <select name="lang">
                <option value="pa-IN">ਪੰਜਾਬੀ (Punjabi)</option>
                <option value="hi-IN">हिंदी (Hindi)</option>
                <option value="en-US">English</option>
            </select>
            <button type="submit">ਵੀਡੀਓ ਤਿਆਰ ਕਰੋ 🚀</button>
        </form>

        {% if video_url %}
        <div class="res">
            <h3>✅ ਤੁਹਾਡੀ ਵੀਡੀਓ ਤਿਆਰ ਹੈ!</h3>
            <p><strong>ਸਕ੍ਰਿਪਟ:</strong> {{ script_text }}</p>
            <video controls autoplay>
                <source src="{{ video_url }}" type="video/mp4">
            </video>
            <a href="{{ video_url }}" download><button>ਵੀਡੀਓ ਡਾਊਨਲੋਡ ਕਰੋ 📥</button></a>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

async def create_voice(text, filename, lang="pa-IN"):
    voice = "pa-IN-OjasNeural" if lang == "pa-IN" else ("hi-IN-SwaraNeural" if lang == "hi-IN" else "en-US-ChristopherNeural")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

def get_pexels_video(query):
    if not PEXELS_API_KEY:
        return None
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
    headers = {"Authorization": PEXELS_API_KEY}
    r = requests.get(url, headers=headers).json()
    if "videos" in r and len(r["videos"]) > 0:
        return r["videos"][0]["video_files"][0]["link"]
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form.get("topic")
        lang = request.form.get("lang", "pa-IN")
        
        # 1. ਸਕ੍ਰਿਪਟ ਬਣਾਓ
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"Write a very short 15-second viral video script about '{topic}' in {lang}. Output only the spoken script text, no brackets or scene titles."
        response = model.generate_content(prompt)
        script_text = response.text.strip()
        
        # 2. ਆਡੀਓ ਬਣਾਓ
        audio_file = "voice.mp3"
        asyncio.run(create_voice(script_text, audio_file, lang))
        
        # 3. ਵੀਡੀਓ ਕਲਿੱਪ ਡਾਊਨਲੋਡ ਕਰੋ
        video_url = get_pexels_video(topic)
        if not video_url:
            video_url = get_pexels_video("nature")
            
        r = requests.get(video_url)
        with open("clip.mp4", "wb") as f:
            f.write(r.content)
            
        # 4. ਵੀਡੀਓ ਅਤੇ ਆਡੀਓ ਮਿਲਾਓ
        audio_clip = AudioFileClip(audio_file)
        video_clip = VideoFileClip("clip.mp4").subclip(0, min(15, audio_clip.duration))
        video_clip = video_clip.set_audio(audio_clip)
        
        final_file = "static/final_video.mp4"
        os.makedirs("static", exist_ok=True)
        video_clip.write_videofile(final_file, codec="libx264", audio_codec="aac", fps=24)
        
        return render_template_string(HTML_TEMPLATE, video_url="/static/final_video.mp4", script_text=script_text)

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

