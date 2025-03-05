import os
import zipfile
import requests
import logging
import base64
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from transformers import pipeline  # Hugging Face AI Summarization

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Ensure 'uploads' directory exists
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def generate_ai_summary(text):
    """Generate AI-based summary using Hugging Face (Free)"""
    try:
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device=-1)  # ✅ Uses CPU
        summary = summarizer(text, max_length=200, min_length=50, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        logging.error(f"⚠ AI Summary Error: {str(e)}")
        return f"⚠ AI Summary Error: {str(e)}"

def extract_github_details(github_link):
    """Extracts technologies, implementation details, and key features from GitHub repository"""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logging.error("⚠ GitHub Token is missing!")
        return "⚠ GitHub Token is missing. Please add it to .env file."

    repo_api_url = github_link.replace("https://github.com/", "https://api.github.com/repos/")
    headers = {"Authorization": f"token {github_token}"}

    try:
        response = requests.get(repo_api_url, headers=headers, timeout=10)
        response.raise_for_status()
        repo_data = response.json()

        # Extracting only relevant details
        project_name = repo_data.get('name', 'N/A')
        tech_stack = repo_data.get('language', 'Unknown')
        
        # Extract README (Implementation Details)
        readme_api_url = repo_api_url + "/readme"
        readme_response = requests.get(readme_api_url, headers=headers, timeout=10)
        readme_content = ""
        if readme_response.status_code == 200:
            readme_content = base64.b64decode(readme_response.json().get("content", "")).decode("utf-8")

        # Preparing extracted text for AI summary
        extracted_text = f"Project Name: {project_name}\n"
        extracted_text += f"Technologies Used: {tech_stack}\n"
        extracted_text += f"README Content: {readme_content}\n"

        return extracted_text

    except requests.exceptions.RequestException as e:
        logging.error(f"⚠ GitHub API Error: {str(e)}")
        return f"⚠ Error fetching GitHub details: {str(e)}"

def extract_zip_contents(zip_file):
    """Extracts important files from ZIP (README, Code Files, Documentation)"""
    zip_path = os.path.join(app.config["UPLOAD_FOLDER"], zip_file.filename)
    zip_file.save(zip_path)
    extracted_text = ""

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(app.config["UPLOAD_FOLDER"])  # ✅ Extracts all files
            for file_name in zip_ref.namelist():
                if file_name.endswith((".txt", ".md", ".py", ".java", ".cpp", ".html", ".css", ".js")):
                    with zip_ref.open(file_name) as file:
                        content = file.read().decode("utf-8", errors="ignore").strip()
                        if content:
                            extracted_text += f"\n--- {file_name} ---\n{content}\n"
        
        os.remove(zip_path)  # Cleanup
        return extracted_text if extracted_text.strip() else "No relevant files found."

    except zipfile.BadZipFile:
        logging.error("⚠ Invalid ZIP file uploaded!")
        return "⚠ Invalid ZIP file. Please upload a valid archive."
    except Exception as e:
        logging.error(f"⚠ ZIP Extraction Error: {str(e)}")
        return f"⚠ ZIP Extraction Error: {str(e)}"

@app.route("/submit", methods=["POST"])
def submit_project():
    github_link = request.form.get("githubLink")
    zip_file = request.files.get("zipFile")

    extracted_text = ""

    # Extract from GitHub
    if github_link and "github.com" in github_link:
        extracted_text += extract_github_details(github_link)

    # Extract from ZIP file
    if zip_file:
        extracted_text += extract_zip_contents(zip_file)

    # ✅ Print extracted text before AI Summary (Debugging)
    print("\n📄 Extracted Text Before AI Summary:\n", extracted_text)

    # Generate AI summary
    ai_summary = generate_ai_summary(extracted_text) if extracted_text.strip() else "No project details found."

    return jsonify({"summary": ai_summary})

if __name__ == "__main__":
    logging.info("Starting Flask server on http://127.0.0.1:5000")
    app.run(debug=True)
