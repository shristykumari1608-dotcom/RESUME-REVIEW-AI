# app.py
# Main Streamlit application for Resume Review AI.
# Run with:  uv run streamlit run app.py
#
# Features:
#   - Paste / type resume text
#   - Capture resume photo with camera → Gemini Vision OCR → auto-fill text
#   - AI agent review with structured results

import streamlit as st
from agent import review_resume, extract_text_from_image

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Resume Review AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* ── Hero ─────────────────────────────────────────────────────────── */
.hero { text-align: center; padding: 2.5rem 1rem 1.2rem; }
.hero h1 {
    font-size: 2.8rem; font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.4rem;
}
.hero p { color: #cbd5e1; font-size: 1.05rem; }

/* ── Glass card ───────────────────────────────────────────────────── */
.glass-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem;
    backdrop-filter: blur(12px);
}

/* ── Camera hint box ──────────────────────────────────────────────── */
.camera-hint {
    background: rgba(96,165,250,0.08);
    border: 1px dashed rgba(96,165,250,0.4);
    border-radius: 12px; padding: 1rem 1.2rem;
    color: #93c5fd; font-size: 0.9rem; margin-bottom: 1rem;
    text-align: center;
}

/* ── Extracted text preview ───────────────────────────────────────── */
.extracted-label {
    color: #34d399; font-weight: 600; font-size: 0.9rem;
    margin-bottom: 0.4rem; display: flex; align-items: center; gap: 6px;
}

/* ── Section heading ──────────────────────────────────────────────── */
.section-heading {
    font-size: 1.15rem; font-weight: 600; color: #a78bfa;
    margin-bottom: 0.75rem;
    border-left: 4px solid #a78bfa; padding-left: 0.75rem;
}

/* ── Score badge ──────────────────────────────────────────────────── */
.score-badge {
    display: inline-block; font-size: 3rem; font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

/* ── Bullet items ─────────────────────────────────────────────────── */
.review-item {
    background: rgba(255,255,255,0.06); border-radius: 8px;
    padding: 0.5rem 0.9rem; margin-bottom: 0.45rem;
    color: #e2e8f0; font-size: 0.95rem; border-left: 3px solid #60a5fa;
}

/* ── Summary box ──────────────────────────────────────────────────── */
.summary-box {
    background: rgba(167,139,250,0.1);
    border: 1px solid rgba(167,139,250,0.35);
    border-radius: 12px; padding: 1.2rem 1.5rem;
    color: #e2e8f0; font-size: 0.97rem; line-height: 1.7; font-style: italic;
}

/* ── Tab overrides ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.04);
    border-radius: 12px; padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; color: #94a3b8 !important;
    font-weight: 500; padding: 0.5rem 1.4rem;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #7c3aed, #3b82f6) !important;
    color: white !important;
}

/* ── Streamlit widgets ────────────────────────────────────────────── */
.stTextInput > label, .stSelectbox > label, .stTextArea > label {
    color: #cbd5e1 !important; font-weight: 500;
}
.stButton > button {
    background: linear-gradient(90deg, #a78bfa, #60a5fa) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; padding: 0.65rem 2.5rem !important;
    font-size: 1rem !important; font-weight: 600 !important;
    width: 100% !important; transition: opacity 0.2s ease !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

hr { border-color: rgba(255,255,255,0.1) !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
# We use session state so that OCR-extracted text persists after the
# camera widget re-renders (Streamlit reruns on every interaction).

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "ocr_done" not in st.session_state:
    st.session_state.ocr_done = False
if "ocr_image_id" not in st.session_state:
    st.session_state.ocr_image_id = None   # track which photo was OCR'd

# ---------------------------------------------------------------------------
# Hero Header
# ---------------------------------------------------------------------------

st.markdown("""
<div class="hero">
    <h1>📄 Resume Review AI</h1>
    <p>Get instant AI-powered feedback — type your resume or snap a photo with your camera.</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# Candidate Info  (always visible, above the tabs)
# ---------------------------------------------------------------------------

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    candidate_name = st.text_input(
        "👤 Candidate Name",
        placeholder="e.g. Jane Doe",
        help="Enter your full name as it appears on your resume.",
    )

with col2:
    job_role = st.selectbox(
        "💼 Target Job Role",
        options=["Data Analyst", "Web Developer", "AI/ML Engineer", "Software Engineer"],
        help="Select the role you are applying for.",
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Input Tabs – Paste Text  |  Camera Capture
# ---------------------------------------------------------------------------

tab_paste, tab_camera = st.tabs(["✏️  Paste / Type Resume", "📷  Camera Capture"])

# ── TAB 1 : Paste / Type ──────────────────────────────────────────────────

with tab_paste:
    st.markdown("Paste the full text of your resume below, or type it directly.")

    typed_text = st.text_area(
        "📋 Resume Text",
        value=st.session_state.resume_text,  # pre-fill if camera OCR already ran
        height=320,
        placeholder=(
            "Paste your complete resume here…\n\n"
            "Include: Contact Info · Summary · Experience · Education · Skills"
        ),
        key="paste_text_area",
        help="Copy and paste all text from your resume into this box.",
    )
    # Keep session state in sync when user edits manually
    st.session_state.resume_text = typed_text

# ── TAB 2 : Camera ────────────────────────────────────────────────────────

with tab_camera:
    st.markdown(
        '<div class="camera-hint">'
        '📸 Point your camera at your resume and click <b>Take Photo</b>. '
        'Gemini Vision will automatically read and extract all the text for you.'
        '</div>',
        unsafe_allow_html=True,
    )

    # Streamlit's built-in camera widget
    camera_photo = st.camera_input(
        label="📷 Take a photo of your resume",
        key="camera_widget",
        help="Hold the resume flat and make sure it is well-lit for best results.",
    )

    if camera_photo is not None:
        # Only re-run OCR if a NEW photo was taken (avoid repeat API calls)
        photo_id = hash(camera_photo.getvalue())

        if photo_id != st.session_state.ocr_image_id:
            st.session_state.ocr_image_id = photo_id
            st.session_state.ocr_done = False  # reset flag for new photo

        if not st.session_state.ocr_done:
            with st.spinner("🔍 Gemini Vision is reading your resume… please wait."):
                try:
                    image_bytes = camera_photo.getvalue()
                    extracted = extract_text_from_image(
                        image_bytes=image_bytes,
                        mime_type="image/jpeg",
                    )
                    st.session_state.resume_text = extracted
                    st.session_state.ocr_done = True

                except ValueError as ve:
                    st.error(f"🔑 Configuration Error: {ve}")
                    st.info(
                        "Add your API key to `.env`:\n```\nGOOGLE_API_KEY=your_key\n```"
                    )
                except Exception as e:
                    st.error(f"❌ OCR failed: {e}")

        # Show the extracted text (editable — user can correct mistakes)
        if st.session_state.ocr_done and st.session_state.resume_text:
            st.success("✅ Text extracted successfully! Review and edit below if needed.")
            corrected = st.text_area(
                "📝 Extracted Resume Text (editable)",
                value=st.session_state.resume_text,
                height=280,
                key="camera_text_area",
                help="Gemini Vision extracted this text. Correct any OCR errors before reviewing.",
            )
            # Sync edits back to session state
            st.session_state.resume_text = corrected

    else:
        # Camera not triggered yet — remind user what to do
        if st.session_state.resume_text and st.session_state.ocr_done:
            st.info("✅ Text already captured from camera. Switch to **✏️ Paste / Type** tab to review it.")

# ---------------------------------------------------------------------------
# Review Button  (always visible below both tabs)
# ---------------------------------------------------------------------------

st.markdown("---")
review_button = st.button("🔍 Review Resume", use_container_width=True, key="review_btn")

# ---------------------------------------------------------------------------
# Helper – Parse Agent Response into Sections
# ---------------------------------------------------------------------------

def parse_review(raw_text: str) -> dict:
    """
    Parses the structured agent response into a dictionary of sections.
    """
    sections = {
        "score": "",
        "strengths": [],
        "weaknesses": [],
        "missing_technical": [],
        "missing_soft": [],
        "recommendations": [],
        "summary": "",
    }

    markers = [
        ("**SCORE:**",                        "score"),
        ("**STRENGTHS:**",                    "strengths"),
        ("**WEAKNESSES:**",                   "weaknesses"),
        ("**MISSING TECHNICAL SKILLS:**",     "missing_technical"),
        ("**MISSING SOFT SKILLS:**",          "missing_soft"),
        ("**IMPROVEMENT RECOMMENDATIONS:**",  "recommendations"),
        ("**IMPROVED PROFESSIONAL SUMMARY:**","summary"),
    ]

    lines = raw_text.splitlines()
    current_key = None

    for line in lines:
        stripped = line.strip()
        matched = False

        for marker, key in markers:
            if marker in stripped:
                current_key = key
                inline = stripped.replace(marker, "").strip()
                if inline and key == "score":
                    sections["score"] = inline
                elif inline and key == "summary":
                    sections["summary"] = inline
                matched = True
                break

        if matched:
            continue

        if current_key and stripped:
            if current_key in ("strengths","weaknesses","missing_technical",
                               "missing_soft","recommendations"):
                item = stripped.lstrip("-•* ").strip()
                if item:
                    sections[current_key].append(item)
            elif current_key == "summary":
                sections["summary"] += (" " + stripped) if sections["summary"] else stripped
            elif current_key == "score" and not sections["score"]:
                sections["score"] = stripped

    return sections


def render_bullets(items: list, color: str = "#60a5fa"):
    for item in items:
        st.markdown(
            f'<div class="review-item" style="border-left-color:{color};">{item}</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Review Logic
# ---------------------------------------------------------------------------

if review_button:

    # ── Validation ────────────────────────────────────────────────────────
    errors = []
    if not candidate_name.strip():
        errors.append("⚠️ Please enter the **Candidate Name**.")
    if not st.session_state.resume_text.strip():
        errors.append(
            "⚠️ Resume text is empty. Paste your resume in the **✏️ Paste** tab "
            "or take a photo in the **📷 Camera** tab."
        )

    if errors:
        for err in errors:
            st.error(err)
        st.stop()

    # ── Call Agent ────────────────────────────────────────────────────────
    st.divider()
    with st.spinner("🤖 AI Agent is reviewing your resume… This may take a few seconds."):
        try:
            raw_review = review_resume(
                candidate_name.strip(),
                job_role,
                st.session_state.resume_text.strip(),
            )
        except ValueError as ve:
            st.error(f"🔑 Configuration Error: {ve}")
            st.info(
                "Create a `.env` file in the project folder with:\n"
                "```\nGOOGLE_API_KEY=your_api_key_here\n```"
            )
            st.stop()
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {e}")
            st.stop()

    # ── Parse & Render Results ────────────────────────────────────────────
    parsed = parse_review(raw_review)

    st.markdown(
        f"### 📊 Resume Review Results for **{candidate_name}** — *{job_role}*"
    )
    st.divider()

    # Score
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">🏆 Overall Score</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="score-badge">{parsed["score"] or "N/A"}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Strengths & Weaknesses
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">✅ Strengths</div>', unsafe_allow_html=True)
        render_bullets(parsed["strengths"], "#34d399") if parsed["strengths"] else st.caption("None identified.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">❌ Weaknesses</div>', unsafe_allow_html=True)
        render_bullets(parsed["weaknesses"], "#f87171") if parsed["weaknesses"] else st.caption("None identified.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Missing Skills
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">🛠️ Missing Technical Skills</div>', unsafe_allow_html=True)
        render_bullets(parsed["missing_technical"], "#f59e0b") if parsed["missing_technical"] else st.caption("None found.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">🤝 Missing Soft Skills</div>', unsafe_allow_html=True)
        render_bullets(parsed["missing_soft"], "#c084fc") if parsed["missing_soft"] else st.caption("None found.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Recommendations
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">💡 Improvement Recommendations</div>', unsafe_allow_html=True)
    render_bullets(parsed["recommendations"], "#60a5fa") if parsed["recommendations"] else st.caption("No recommendations.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Improved Summary
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">✨ Improved Professional Summary</div>', unsafe_allow_html=True)
    if parsed["summary"]:
        st.markdown(f'<div class="summary-box">{parsed["summary"]}</div>', unsafe_allow_html=True)
    else:
        st.caption("No improved summary generated.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Raw output (debugging)
    with st.expander("🔎 View Raw Agent Response"):
        st.text(raw_review)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    '<p style="text-align:center; color:#64748b; font-size:0.85rem;">'
    "Resume Review AI · Powered by Google Gemini Vision &amp; ADK"
    "</p>",
    unsafe_allow_html=True,
)
