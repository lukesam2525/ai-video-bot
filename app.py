import os
from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Generator</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 30px auto; padding: 20px; background: #0f172a; color: #fff; }
        .card { background: #1e293b; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        h2 { text-align: center; color: #38bdf8; margin-top: 0; }
        input, select, button { width: 100%; padding: 12px; margin-top: 10px; border-radius: 8px; border: 1px solid #334155; box-sizing: border-box; font-size: 16px; }
        input, select { background: #0f172a; color: #fff; }
        button { background: #0284c7; color: white; font-weight: bold; border: none; cursor: pointer; margin-top: 20px; }
        button:hover { background: #0369a1; }
        #output { margin-top: 20px; padding: 15px; background: #0f172a; border-radius: 8px; white-space: pre-wrap; display: none; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚀 AI Video Script Generator</h2>
        <label>ਟੌਪਿਕ ਜਾਂ ਆਈਡੀਆ ਲਿਖੋ:</label>
        <input type="text" id="topic" placeholder="ਜਿਵੇਂ: Top 5 Skincare Tips, Fun Facts...">
        
        <label style="margin-top:15px; display:block;">ਪਲੇਟਫਾਰਮ ਚੁਣੋ:</label>
        <select id="platform">
            <option value="YouTube Shorts / Reels">Shorts / Reels (60s)</option>
            <option value="Long YouTube Video">Long YouTube Video</option>
            <option value="Blog / Article Idea">Blog / Article Content</option>
        </select>
        
        <button onclick="generateScript()" id="btn">ਜਨਰੇਟ ਕਰੋ ✨</button>
        <div id="output"></div>
    </div>

    <script>
        async function generateScript() {
            const topic = document.getElementById('topic').value;
            const platform = document.getElementById('platform').value;
            const btn = document.getElementById('btn');
            const output = document.getElementById('output');
            
            if (!topic) {
                alert('ਕਿਰਪਾ ਕਰਕੇ ਕੋਈ ਟੌਪਿਕ ਲਿਖੋ!');
                return;
            }
            
            btn.innerText = 'ਲਿਖ ਰਿਹਾ ਹੈ... ਕਿਰਪਾ ਕਰਕੇ ਉਡੀਕ ਕਰੋ...';
            btn.disabled = true;
            output.style.display = 'none';
            
            try {
                const res = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({topic, platform})
                });
                const data = await res.json();
                output.style.display = 'block';
                output.innerText = data.result || 'ਕੋਈ ਗੜਬੜ ਹੋ ਗਈ: ' + (data.error || 'ਅਣਜਾਣ ਗਲਤੀ');
            } catch (err) {
                output.style.display = 'block';
                output.innerText = 'ਗਲਤੀ ਆਈ: ' + err.message;
            }
            
            btn.innerText = 'ਜਨਰੇਟ ਕਰੋ ✨';
            btn.disabled = false;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json or {}
    topic = data.get('topic', '')
    platform = data.get('platform', 'Shorts / Reels')
    
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Create an engaging, viral video script or outline for {platform} on the topic: '{topic}'. Include Hook, Main Body Points, Visual Scenes suggestions, and Call to Action."
        response = model.generate_content(prompt)
        return jsonify({'result': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
