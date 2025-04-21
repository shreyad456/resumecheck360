import fitz  # PyMuPDF
import spacy
from flask import Flask, render_template, request, send_file
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


def extract_keywords(text):
    doc = nlp(text)
    keywords = set()
    for chunk in doc.noun_chunks:
        if len(chunk.text.strip()) > 2:
            keywords.add(chunk.text.strip().lower())
    return list(keywords)


def find_matched_keywords(resume_text, jd_keywords):
    resume_text_lower = resume_text.lower()
    matched = [kw for kw in jd_keywords if kw in resume_text_lower]
    return matched


def generate_suggestions(resume_text):
    suggestions = []

    if resume_text.count("experience") < 2:
        suggestions.append("You could highlight more of your work experience.")

    if "skills" not in resume_text.lower():
        suggestions.append("Consider adding a skills section to showcase your abilities.")

    if "%" not in resume_text and any(word in resume_text.lower() for word in ["increased", "improved", "reduced"]):
        suggestions.append("Include measurable achievements, like percentages or numbers.")

    if not any(verb in resume_text.lower() for verb in ["managed", "led", "developed", "implemented"]):
        suggestions.append("Use strong action verbs to describe your experience.")

    if len(resume_text.split()) < 150:
        suggestions.append("Your resume is quite short. Consider adding more content.")

    if not suggestions:
        suggestions.append("Your resume looks good! No major issues detected.")

    return suggestions


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files or 'job_description' not in request.files:
        return "Missing files! Please upload both Resume and Job Description."

    resume_file = request.files['resume']
    jd_file = request.files['job_description']

    if resume_file.filename == "" or jd_file.filename == "":
        return "Files were not selected! Please upload both files."

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
    jd_path = os.path.join(app.config['UPLOAD_FOLDER'], jd_file.filename)

    resume_file.save(resume_path)
    jd_file.save(jd_path)

    resume_text = extract_text(resume_path)
    jd_text = extract_text(jd_path)

    score = calculate_match_score(resume_text, jd_text)
    score_percent = round(score * 100, 2)

    jd_keywords = extract_keywords(jd_text)
    matched_keywords = find_matched_keywords(resume_text, jd_keywords)

    suggestions = generate_suggestions(resume_text)

    return render_template(
        'index.html',
        match_score=score_percent,
        matched_keywords=matched_keywords,
        suggestion=", ".join(suggestions)
    )


@app.route('/download-report')
def download_report():
    match_score = request.args.get('score', 'N/A')
    keywords = request.args.get('keywords', '')

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, "ResumeCheck360 Report")

    p.setFont("Helvetica", 12)
    p.drawString(100, height - 130, f"Match Score: {match_score}%")

    p.drawString(100, height - 160, "Matched Keywords:")
    for i, word in enumerate(keywords.split(','), start=1):
        p.drawString(120, height - 160 - (i * 20), f"- {word.strip()}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='ResumeCheck360_Report.pdf', mimetype='application/pdf')


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)










