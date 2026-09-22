# 📄 Resume Review Agent

A beginner-friendly single-agent AI application built with **CrewAI + Streamlit + Groq**.

The application compares a candidate's resume against a target job description and produces a structured review with actionable improvement suggestions.

## ✨ Features

* Upload a resume as PDF
* Paste resume text directly
* Paste a target job description
* Extract PDF text using `pypdf`
* Compare resume information against job requirements
* Identify:

  * Match Summary
  * Skills Found
  * Missing Requirements
  * Unclear / Not Demonstrated
  * Experience Gaps
  * Education / Qualification Gaps
  * Resume Improvements
  * Keywords to Consider
  * Priority Action Plan
* Uses exactly:

  * 1 CrewAI Agent
  * 1 CrewAI Task
  * 1 Crew
* Uses Groq as the LLM provider
* Uses `openai/gpt-oss-120b`
* Uses Streamlit Secrets for API key management
* Does not permanently store resumes or job descriptions
* Includes basic error handling

---

## 🏗️ Architecture

```text
Resume PDF / Text
       │
       ▼
Resume Text Extraction
       │
       ├───────────────┐
       │               │
       ▼               ▼
Resume Text      Job Description
       │               │
       └───────┬───────┘
               ▼
       CrewAI Resume Agent
               │
               ▼
          One Task
               │
               ▼
       Groq GPT-OSS 120B
               │
               ▼
        Structured Review
               │
               ▼
          Streamlit UI
```

---

## 📁 Project Structure

```text
resume-review-agent/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── .streamlit/
    └── secrets.toml.example
```

---

## 🛠️ Technologies

* Python 3.11
* Streamlit
* CrewAI
* Groq
* pypdf

---

## 🔑 Groq API Key

Create a Groq API key and configure it through Streamlit Secrets.

The application expects:

```toml
GROQ_API_KEY = "your_api_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

Never place your real API key directly inside `app.py`.

Never upload a real `secrets.toml` file to GitHub.

---

## 💻 Run Locally

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Enter the project folder

```bash
cd resume-review-agent
```

### 3. Create a virtual environment

Windows:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Create Streamlit secrets

Create:

```text
.streamlit/secrets.toml
```

Add:

```toml
GROQ_API_KEY = "your_groq_api_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

### 6. Run the application

```bash
streamlit run app.py
```

The application should open in your browser.

---

## ☁️ Deploy to Streamlit Community Cloud

1. Push the project to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new application.
4. Select your GitHub repository.
5. Select `app.py` as the main file.
6. Configure Python to use **Python 3.11**.
7. Add the following secrets:

```toml
GROQ_API_KEY = "your_groq_api_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

8. Deploy the application.

Do not put the API key into GitHub.

---

## 🔒 Privacy

The application does not intentionally save uploaded resumes or job descriptions to a database or permanent application storage.

The supplied resume and job description are sent to the configured Groq LLM provider so that the AI review can be generated.

Do not submit confidential information unless you are comfortable sending it to the configured AI provider.

---

## ⚠️ Accuracy Rule

The Resume Review Agent must not invent information.

If a qualification is not explicitly supported by the supplied resume, it should not be presented as a confirmed skill or experience.

For example:

Incorrect:

> The candidate has no Python experience.

Correct:

> Python experience is not demonstrated in the supplied resume.

The application distinguishes between:

* Demonstrated
* Not Demonstrated
* Unknown

---

## 🚀 Future Improvements

Possible future additions include:

* DOCX support
* Resume section extraction
* Downloadable review reports
* Resume rewriting
* Multiple job descriptions
* Job-specific resume customization
* ATS-oriented keyword analysis
* Resume version history
* Authentication

These features are intentionally not included in the beginner version.

---

## 📚 Learning Goal

This project demonstrates how to build a simple AI agent application using:

```text
Streamlit
     +
CrewAI
     +
Groq
     +
PDF extraction
```

The project is intentionally kept small so beginners can understand how an AI agent receives information, processes it through an LLM, and returns a useful structured result.
