import os
import requests
from flask import Flask, request, render_template_string
from gtts import gTTS
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Video Generator</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; display: flex; justify-content: center; }
        .card { background: #1e293b; padding: 25px; border-radius: 12px; width: 100%; max-width: 500px; }
        h1 { color: #38bdf8; text-align: center; }
        label { display: block; margin-top: 15px; font-weight: bold; }
        input, select, button { width: 100%; padding: 12px; margin-top: 8px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #fff; box-sizing: border-box; }
        button { background: #0284c7; font-weight: bold; border: none; margin-top: 20px; cursor: pointer; }
        .res { margin-top: 20px; padding: 15px; background: #0f172a; border-radius: 8px; border-left: 4px solid #38bdf8; }
        video { width: 100%; border-radius: 8px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎬 AI Video Generator</h1>
        <form method="POST">
            <label>ਵੀਡੀਓ ਦਾ ਟੌਪਿਕ ਲਿਖੋ:</label>
            <input type="text" name="topic" placeholder="e.g. Morning Motivation" required>
            <label>ਭਾਸ਼ਾ (Voice Language):</label>
            <select name="lang">
                <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="en">English</option>
            </select>
            <button type="submit">ਵੀਡੀਓ ਤਿਆਰ ਕਰੋ 🚀</button>
        </form>

        {% if video_url %}
        <div class="res">
            <h3>✅ ਵੀਡੀਓ ਤਿਆਰ ਹੈ!</h3>
            <p><strong>ਸਕ੍ਰਿਪਟ:</strong> {{ script_text }}</p>
            <video controls autoplay>
                <source src="{{ video_url }}" type="video/mp4">
            </video>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def create_voice(text, filename, lang="pa"):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(filename)

def get_pexels_video(query):
    if PEXELS_API_KEY:
        try:
            url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
            headers = {"Authorization": PEXELS_API_KEY}
            r = requests.get(url, headers=headers, timeout=10).json()
            if "videos" in r and len(r["videos"]) > 0:
                return r["videos"][0]["video_files"][0]["link"]
        except Exception:
            pass
    return "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form.get("topic", "Motivation")
        lang = request.form.get("lang", "pa")
        
        script_text = f"Top facts about {topic}. Work hard and stay focused on your goals every day."
        if GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
                prompt = f"Write a short, engaging 15-word video script about '{topic}' in language code '{lang}'. Do not use formatting or asterisks, only spoken plain text."
                res = model.generate_content(prompt)
                if res and res.text:
                    script_text = res.text.strip().replace("*", "")
            except Exception:
                pass
        
        audio_file = "voice.mp3"
        create_voice(script_text, audio_file, lang)
        
        video_url = get_pexels_video(topic)
        r = requests.get(video_url, timeout=15)
        with open("clip.mp4", "wb") as f:
            f.write(r.content)
            
        audio_clip = AudioFileClip(audio_file)
        video_clip = VideoFileClip("clip.mp4").subclip(0, min(10, max(3, audio_clip.duration)))
        video_clip = video_clip.set_audio(audio_clip)
        
        os.makedirs("static", exist_ok=True)
        final_file = "static/final_video.mp4"
        video_clip.write_videofile(final_file, codec="libx264", audio_codec="aac", fps=24, verbose=False, logger=None)
        
        return render_template_string(HTML_TEMPLATE, video_url="/static/final_video.mp4", script_text=script_text)

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
