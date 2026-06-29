# 📄 Resume Review AI

An intelligent, interactive web application that reviews resumes, scores them, identifies gaps, and suggests tailored improvements. Powered by **Google Gemini 2.5 Flash**, the **Google Agent Development Kit (ADK)**, and **Streamlit**.

---

## 📷 Screenshots

### 1. Main Dashboard (Paste/Type Resume)
<!-- MOCKUP PLACEHOLDER: Paste/Type Tab -->
![Dashboard Mockup](https://raw.githubusercontent.com/username/repository/main/assets/dashboard_preview.png)

### 2. Camera Input (Gemini Vision OCR)
<!-- MOCKUP PLACEHOLDER: Camera Capture Tab -->
![Camera Input Mockup](https://raw.githubusercontent.com/username/repository/main/assets/camera_preview.png)

---

## ✨ Features

* **双 Input Methods:** Paste or type resume text directly, or snap a photo of a physical resume using your webcam.
* **Instant OCR Extraction:** Real-time text extraction from photos using Gemini Vision models, automatically populating the editor.
* **Resume Quality Scoring:** Receives an overall rating out of 10 points.
* **Tailored Role Analysis:** Contextualized evaluation based on the target role (Data Analyst, Web Developer, AI/ML Engineer, Software Engineer).
* **Strengths & Weaknesses:** Detailed assessment of what is working well and what needs improvement.
* **Role-Specific Skill Mapping:** Highlights missing technical and soft skills required for the target job role.
* **Actionable Recommendations:** Provides step-by-step guidance on structural and content enhancements.
* **AI Summary Rewrite:** Generates an ATS-optimized, high-impact professional summary to replace your current one.

---

## 🛠️ Technologies Used

* **Frontend & UI:** [Streamlit](https://streamlit.io/) (with responsive glassmorphism dark-mode styles)
* **AI Orchestration:** [Google Agent Development Kit (ADK)](https://github.com/google/generative-ai-python)
* **Large Language Models:** [Google Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) (via `google-genai`)
* **Environment Management:** `python-dotenv`
* **Dependency & Package Manager:** `uv` (ultra-fast package installer)

---

## 🗂️ Project Structure

```text
Resume agent/
│
├── app.py              # Streamlit Web UI (Tab-based design & session management)
├── agent.py            # Google ADK agent definition & Vision OCR integration
├── requirements.txt    # Python dependencies list
├── .env.example        # Environment variables configuration template
└── README.md           # This project documentation
```

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
* Python 3.10 or higher installed.
* A Gemini API key. You can get one for free at [Google AI Studio](https://aistudio.google.com/app/apikey).

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd "Resume agent"
```

### 3. Initialize & Install Dependencies (Using `uv` - Recommended)
If you have `uv` installed:
```bash
# Create virtual environment and install packages
uv venv --python 3.11
uv pip install -r requirements.txt
```

If using standard `pip`:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Duplicate `.env.example` as `.env` and fill in your Gemini API key:
```bash
cp .env.example .env   # On Windows: copy .env.example .env
```
Open `.env` and configure:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 5. Launch the Application
Start the Streamlit development server:
```bash
uv run streamlit run app.py
```
Open your browser and navigate to **`http://localhost:8501`** to run the app.

---

## 🧠 Architecture Overview

```text
┌───────────────────────┐
│ Streamlit UI (app.py) │ ◄── (User Inputs candidate, role, and text/photo)
└──────────┬────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  agent.py                                    │
│  ├─ extract_text_from_image() (Vision OCR)   │ ◄── Gemini 2.5 Flash
│  └─ review_resume() (ADK Workflow Runner)     │ ◄── Google ADK + Gemini 2.5 Flash
└──────────────────────────────────────────────┘
```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.
