import os
import re

import streamlit as st
from pypdf import PdfReader
from crewai import Agent, Task, Crew, Process, LLM


# ============================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Resume Review Agent",
    page_icon="📄",
    layout="wide",
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_pdf_text(uploaded_file):
    """
    Extract text from a PDF using pypdf.

    Returns:
        str: Extracted text
    Raises:
        ValueError: If the PDF cannot be read or contains no text.
    """

    try:
        reader = PdfReader(uploaded_file)

        if not reader.pages:
            raise ValueError("The PDF does not contain any pages.")

        extracted_pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                extracted_pages.append(text)

        extracted_text = "\n\n".join(extracted_pages).strip()

        if not extracted_text:
            raise ValueError(
                "No readable text was found in the PDF. "
                "The file may be scanned/image-based."
            )

        return extracted_text

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            "The PDF could not be read. Please check that it is a valid PDF file."
        ) from exc


def clean_text(text):
    """
    Clean excessive whitespace while preserving readable text.
    """

    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def get_groq_settings():
    """
    Read Groq configuration from Streamlit secrets.

    Required:
        GROQ_API_KEY

    Optional:
        GROQ_MODEL

    Returns:
        tuple[str, str]
    """

    try:
        api_key = st.secrets["GROQ_API_KEY"]

        model = st.secrets.get(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

    except Exception as exc:
        raise ValueError(
            "GROQ_API_KEY is missing from Streamlit secrets."
        ) from exc

    if not api_key or not str(api_key).strip():
        raise ValueError(
            "GROQ_API_KEY is empty. Please add a valid Groq API key."
        )

    return str(api_key).strip(), str(model).strip()


def build_resume_review_crew(resume_text, job_description):
    """
    Create exactly:
        1 CrewAI Agent
        1 CrewAI Task
        1 Crew
    """

    api_key, model_name = get_groq_settings()

    # CrewAI uses LiteLLM-style provider/model notation.
    # Groq's actual model ID is openai/gpt-oss-120b.
    crewai_model = f"groq/{model_name}"

    # Make the key available to LiteLLM/CrewAI.
    os.environ["GROQ_API_KEY"] = api_key

    llm = LLM(
        model=crewai_model,
        api_key=api_key,
        temperature=0.1,
        max_tokens=6000,
    )

    # ========================================================
    # EXACTLY ONE AGENT
    # ========================================================

    resume_reviewer = Agent(
        role="Resume Review Specialist",
        goal=(
            "Accurately compare a candidate's resume with a target job "
            "description and provide evidence-based, actionable resume "
            "improvement recommendations."
        ),
        backstory=(
            "You are a careful professional resume reviewer. "
            "You analyze resumes against job requirements without "
            "inventing information. You distinguish clearly between "
            "skills explicitly demonstrated in the resume, requirements "
            "that are missing, and requirements that cannot be determined "
            "from the provided information."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # ========================================================
    # EXACTLY ONE TASK
    # ========================================================

    review_task = Task(
        description=f"""
You must review a candidate's resume against a target job description.

========================
CANDIDATE RESUME
========================

{resume_text}

========================
TARGET JOB DESCRIPTION
========================

{job_description}

========================
STRICT ACCURACY RULE
========================

This is extremely important:

NEVER invent, assume, infer, or fabricate information about the candidate.

Only identify a qualification, skill, experience, project, certification,
achievement, education, employment history, technology, or responsibility
as PRESENT when it is explicitly supported by the supplied resume.

If the resume does not provide enough information to determine whether a
requirement is satisfied, classify it as:

"Unknown / Not Demonstrated"

Do NOT interpret silence as proof that the candidate lacks something.

For example:

- If Python is not mentioned, do not say "the candidate has no Python skills."
- Say "Python is not demonstrated in the supplied resume."
- If the job requires 3 years of experience but the resume does not provide
  enough information to determine the duration, say "Unknown / Not Demonstrated."
- Never create years of experience.
- Never create certifications.
- Never create projects.
- Never create job titles.
- Never create educational qualifications.

========================
REQUIRED REVIEW FORMAT
========================

Produce a professional review using exactly these sections:

## 1. Match Summary

Give a concise evidence-based summary of how the supplied resume relates
to the target job.

Do not give a fabricated numerical score.

## 2. Skills Found

List important skills from the job description that are explicitly
supported by the resume.

For each skill, briefly explain the resume evidence.

## 3. Missing Requirements

List important job requirements that are not explicitly demonstrated
in the resume.

Use wording such as:
"Not demonstrated in the supplied resume."

Do not claim that the candidate definitely lacks the skill.

## 4. Unclear / Not Demonstrated

List requirements where the resume does not provide enough information
to determine whether the candidate meets them.

## 5. Experience Gaps

Compare the experience requirements in the job description with the
experience explicitly documented in the resume.

Clearly distinguish:
- explicitly demonstrated
- not demonstrated
- unknown

## 6. Education / Qualification Gaps

Compare education, degrees, certifications, licenses, or other formal
qualifications.

Do not assume qualifications that are not explicitly stated.

## 7. Resume Improvements

Give specific recommendations for improving the resume.

Only recommend adding information if it is truthful and actually supported
by the candidate's real background.

Do not tell the candidate to falsely add a skill or qualification.

## 8. Keywords to Consider

Identify useful keywords and phrases from the job description that could
be considered for the resume ONLY if they accurately describe the
candidate's real experience.

Clearly warn against adding unsupported keywords.

## 9. Priority Action Plan

Provide a practical action plan with:

1. Highest-priority resume improvement
2. Second-priority improvement
3. Third-priority improvement
4. Optional improvement

========================
STYLE
========================

- Be concise but useful.
- Use bullet points where appropriate.
- Quote or paraphrase resume evidence when useful.
- Do not exaggerate.
- Do not make hiring decisions.
- Do not claim the candidate will or will not get the job.
- Do not fabricate a match percentage.
- Do not invent missing information.
- Keep recommendations actionable.

Your output must contain all nine required sections.
""",
        expected_output=(
            "A structured resume review containing all nine requested "
            "sections, based only on information explicitly present in "
            "the supplied resume and job description."
        ),
        agent=resume_reviewer,
    )

    # ========================================================
    # EXACTLY ONE CREW
    # ========================================================

    crew = Crew(
        agents=[resume_reviewer],
        tasks=[review_task],
        process=Process.sequential,
        verbose=False,
    )

    return crew


def run_review(resume_text, job_description):
    """
    Run the single-agent CrewAI workflow.
    """

    crew = build_resume_review_crew(
        resume_text=resume_text,
        job_description=job_description,
    )

    result = crew.kickoff()

    return str(result)


def display_review(review_text):
    """
    Display the generated review.

    The agent is instructed to return Markdown, so Streamlit
    can render it directly.
    """

    st.markdown(review_text)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("📄 Resume Review Agent")

st.write(
    "Compare your resume with a target job description and receive "
    "an evidence-based review with practical improvement suggestions."
)

st.info(
    "🔒 Privacy notice: Your resume and job description are processed "
    "temporarily for this review and are not permanently stored by this "
    "application. The information is sent to the configured Groq LLM "
    "provider for analysis. Avoid submitting information you do not want "
    "to send to the configured provider."
)


# ============================================================
# RESUME INPUT
# ============================================================

st.header("1. Provide Your Resume")

resume_input_method = st.radio(
    "Choose how you want to provide your resume:",
    ["Upload PDF", "Paste Resume Text"],
    horizontal=True,
)


resume_text = ""


if resume_input_method == "Upload PDF":

    uploaded_resume = st.file_uploader(
        "Upload your resume as a PDF",
        type=["pdf"],
        help="Only PDF files are supported.",
    )

    if uploaded_resume is not None:

        try:
            resume_text = extract_pdf_text(uploaded_resume)
            resume_text = clean_text(resume_text)

            st.success(
                f"Resume extracted successfully "
                f"({len(resume_text):,} characters)."
            )

            with st.expander("Preview extracted resume text"):
                preview_length = 5000

                if len(resume_text) > preview_length:
                    st.text(
                        resume_text[:preview_length]
                        + "\n\n[Preview truncated]"
                    )
                else:
                    st.text(resume_text)

        except ValueError as error:
            st.error(str(error))

else:

    resume_text = st.text_area(
        "Paste your resume text here",
        height=350,
        placeholder=(
            "Paste the complete text of your resume here..."
        ),
    )

    resume_text = clean_text(resume_text)


# ============================================================
# JOB DESCRIPTION
# ============================================================

st.header("2. Provide the Target Job Description")

job_description = st.text_area(
    "Paste the job description here",
    height=350,
    placeholder=(
        "Paste the complete target job description here..."
    ),
)

job_description = clean_text(job_description)


# ============================================================
# REVIEW BUTTON
# ============================================================

st.divider()

review_button = st.button(
    "🔍 Review Resume",
    type="primary",
    use_container_width=True,
)


# ============================================================
# RUN APPLICATION
# ============================================================

if review_button:

    # --------------------------------------------------------
    # Validate inputs
    # --------------------------------------------------------

    if not resume_text:
        st.error(
            "Please upload a readable PDF or paste your resume text."
        )
        st.stop()

    if not job_description:
        st.error(
            "Please paste the target job description."
        )
        st.stop()

    # Prevent accidentally sending extremely large inputs.
    max_characters = 100000

    if len(resume_text) > max_characters:
        st.warning(
            "The resume text is unusually long. "
            "Please shorten it before submitting."
        )
        st.stop()

    if len(job_description) > max_characters:
        st.warning(
            "The job description is unusually long. "
            "Please shorten it before submitting."
        )
        st.stop()

    # --------------------------------------------------------
    # Run CrewAI
    # --------------------------------------------------------

    with st.spinner(
        "The Resume Review Agent is analyzing the resume..."
    ):

        try:

            review = run_review(
                resume_text=resume_text,
                job_description=job_description,
            )

            if not review.strip():
                st.error(
                    "The agent returned an empty review. "
                    "Please try again."
                )
                st.stop()

            st.success("Resume review completed.")

            st.header("📊 Resume Review")

            display_review(review)

        except ValueError as error:

            st.error(str(error))

        except Exception as error:

            error_message = str(error).lower()

            # ----------------------------------------------
            # Rate-limit errors
            # ----------------------------------------------

            if (
                "rate limit" in error_message
                or "429" in error_message
                or "too many requests" in error_message
            ):

                st.error(
                    "Groq rate limit reached. "
                    "Please wait a little while and try again."
                )

            # ----------------------------------------------
            # Authentication / API key errors
            # ----------------------------------------------

            elif (
                "401" in error_message
                or "authentication" in error_message
                or "invalid api key" in error_message
                or "api_key" in error_message
            ):

                st.error(
                    "The Groq API key could not be authenticated. "
                    "Please check your Streamlit secrets."
                )

            # ----------------------------------------------
            # Model errors
            # ----------------------------------------------

            elif (
                "model" in error_message
                and (
                    "not found" in error_message
                    or "does not exist" in error_message
                    or "unsupported" in error_message
                )
            ):

                st.error(
                    "The configured Groq model is unavailable. "
                    "Please check the GROQ_MODEL value in Streamlit secrets."
                )

            # ----------------------------------------------
            # Timeout / connection errors
            # ----------------------------------------------

            elif (
                "timeout" in error_message
                or "timed out" in error_message
                or "connection" in error_message
                or "connect" in error_message
            ):

                st.error(
                    "The connection to the AI service timed out. "
                    "Please wait a moment and try again."
                )

            # ----------------------------------------------
            # Generic safe error
            # ----------------------------------------------

            else:

                st.error(
                    "The resume review could not be completed. "
                    "Please check your inputs, API configuration, "
                    "and try again."
                )
