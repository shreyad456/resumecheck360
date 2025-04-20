import fitz # PyMuPDF
import spacy
from flask import Flask, render_template, request
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load the spaCy NLP mo
nlp = spacy.load("en_core_web_sm")

def extract_text(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def calculate_match_score(resume_text, jd_text):
    resume_doc = nlp(resume_text)
    jd_doc = nlp(jd_text)
    return resume_doc.similarity(jd_doc)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    resume_file = request.files['resume']
    jd_file = request.files['jd']

    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
    jd_path = os.path.join(app.config['UPLOAD_FOLDER'], jd_file.filename)

    resume_file.save(resume_path)
    jd_file.save(jd_path)

    resume_text = extract_text(resume_path)
    jd_text = extract_text(jd_path)

    score = calculate_match_score(resume_text, jd_text)
    score_percent = round(score * 100, 2)

    return render_template('index.html', score=score_percent)


from flask import jsonify

@app.route('/check', methods=['POST'])
def check():
    data = request.get_json()
    
    resume_text = data.get("resume", "")
    jd_text = data.get("job_description", "")

    score = calculate_match_score(resume_text, jd_text)
    score_percent = round(score * 100, 2)

    return jsonify({
        "message": "Match Score Calculated",
        "score": f"{score_percent}%",
        "resume": resume_text,
        "job_description": jd_text
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

























