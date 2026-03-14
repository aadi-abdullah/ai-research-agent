import streamlit as st
from agents.search_agent import run_search_agent
from chains.summarizer import summarize
from agents.report_agent import generate_report
from utils.pdf_exporter import export_pdf
import tempfile
import os
import time
from config import GOOGLE_API_KEY, TAVILY_API_KEY
import base64
from datetime import datetime

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Enhanced CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');

    /* ── Design Tokens ── */
    :root {
        --bg:        #0e0f11;
        --surface:   #141618;
        --surface2:  #1c1e22;
        --border:    #2a2d33;
        --border2:   #3a3d45;
        --text:      #e8e9ec;
        --muted:     #7a7f8c;
        --amber:     #f5a623;
        --amber-dim: #c4831c;
        --amber-glow:rgba(245,166,35,0.12);
        --green:     #4ade80;
        --red:       #f87171;
        --radius:    4px;
        --radius-lg: 8px;
    }

    /* ── Global Reset ── */
    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif !important;
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }

    /* hide default Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 2.5rem 3rem 4rem !important; max-width: 1300px; }

    /* ── Noise-texture overlay (atmosphere) ── */
    .main::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
        pointer-events: none;
        z-index: 0;
        opacity: 0.35;
    }

    /* ── Hero Header ── */
    .hero {
        position: relative;
        text-align: center;
        padding: 3.5rem 1rem 2rem;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -60px; left: 50%;
        transform: translateX(-50%);
        width: 520px; height: 320px;
        background: radial-gradient(ellipse at center, rgba(245,166,35,0.14) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-eyebrow {
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: var(--amber);
        margin-bottom: 0.9rem;
    }
    .hero-title {
        font-size: 3.6rem;
        font-weight: 800;
        line-height: 1.05;
        letter-spacing: -0.03em;
        color: var(--text);
        margin: 0 0 0.6rem;
    }
    .hero-title span { color: var(--amber); }
    .hero-sub {
        font-family: 'Lora', serif;
        font-style: italic;
        font-size: 1.05rem;
        color: var(--muted);
        margin: 0;
    }

    /* ── Thin amber rule ── */
    .amber-rule {
        width: 56px; height: 2px;
        background: var(--amber);
        margin: 2.2rem auto;
        border-radius: 2px;
    }

    /* ── Status / Feature Cards ── */
    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.25rem 1rem 1.1rem;
        text-align: center;
        transition: border-color 0.25s, box-shadow 0.25s;
        position: relative;
        overflow: hidden;
    }
    .card::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, var(--amber-glow) 0%, transparent 60%);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .card:hover { border-color: var(--amber-dim); box-shadow: 0 0 0 1px var(--amber-dim); }
    .card:hover::after { opacity: 1; }
    .card-icon {
        font-size: 1.6rem;
        margin-bottom: 0.45rem;
        display: block;
        line-height: 1;
    }
    .card-title {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--muted);
        margin-bottom: 0.5rem;
    }

    /* ── Badges ── */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        font-family: 'DM Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        padding: 0.3rem 0.65rem;
        border-radius: 2px;
        font-weight: 500;
    }
    .badge-green { background: rgba(74,222,128,0.1); color: var(--green); border: 1px solid rgba(74,222,128,0.25); }
    .badge-red   { background: rgba(248,113,113,0.1); color: var(--red);   border: 1px solid rgba(248,113,113,0.25); }
    .badge-amber { background: var(--amber-glow);     color: var(--amber); border: 1px solid rgba(245,166,35,0.3); }

    /* ── Search Box ── */
    .search-wrap {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.8rem 1.8rem 1.5rem;
        margin-bottom: 1.8rem;
        position: relative;
    }
    .search-wrap::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 3px;
        background: linear-gradient(90deg, var(--amber), var(--amber-dim), transparent);
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    }
    .search-label {
        font-family: 'DM Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--amber);
        margin-bottom: 0.7rem;
        display: block;
    }

    /* Override Streamlit input */
    .stTextInput > div > div > input {
        background: var(--surface2) !important;
        border: 1px solid var(--border2) !important;
        border-radius: var(--radius) !important;
        color: var(--text) !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 1rem !important;
        padding: 0.75rem 1.1rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--amber) !important;
        box-shadow: 0 0 0 3px var(--amber-glow) !important;
    }
    .stTextInput > div > div > input::placeholder { color: var(--muted) !important; }

    /* ── Primary Button ── */
    .stButton > button {
        background: var(--amber) !important;
        color: #0e0f11 !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        border: none !important;
        border-radius: var(--radius) !important;
        padding: 0.78rem 1.6rem !important;
        transition: background 0.2s, transform 0.15s, box-shadow 0.2s !important;
        width: 100%;
    }
    .stButton > button:hover {
        background: #f7b84a !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(245,166,35,0.35) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    /* ── Download Button ── */
    .stDownloadButton > button {
        background: transparent !important;
        color: var(--amber) !important;
        border: 1px solid var(--amber) !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em !important;
        border-radius: var(--radius) !important;
        transition: background 0.2s, box-shadow 0.2s !important;
    }
    .stDownloadButton > button:hover {
        background: var(--amber-glow) !important;
        box-shadow: 0 0 16px rgba(245,166,35,0.2) !important;
    }

    /* ── Progress Bar ── */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--amber-dim), var(--amber)) !important;
        border-radius: 2px !important;
    }
    .stProgress > div > div {
        background: var(--border) !important;
        border-radius: 2px !important;
        height: 5px !important;
    }

    /* ── Step Status Banner ── */
    .step-banner {
        display: flex;
        align-items: center;
        gap: 0.9rem;
        padding: 0.9rem 1.2rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 3px solid var(--amber);
        border-radius: var(--radius);
        margin: 0.6rem 0;
        font-size: 0.92rem;
    }
    .step-banner.success {
        border-left-color: var(--green);
        background: rgba(74,222,128,0.04);
    }
    .step-num {
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        color: var(--amber);
        background: var(--amber-glow);
        border: 1px solid rgba(245,166,35,0.3);
        padding: 0.15rem 0.45rem;
        border-radius: 2px;
        white-space: nowrap;
    }

    /* ── Metric Cards ── */
    .metric-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.4rem 1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--amber), transparent);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: var(--amber);
        line-height: 1;
        margin-bottom: 0.35rem;
    }
    .metric-label {
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--muted);
    }

    /* ── Section Heading ── */
    .section-heading {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2.2rem 0 1.1rem;
    }
    .section-heading-text {
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--text);
    }
    .section-heading-line {
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    /* ── Source Items ── */
    .source-item {
        padding: 0.6rem 0.85rem;
        border-left: 2px solid var(--amber);
        background: var(--surface);
        border-radius: 0 var(--radius) var(--radius) 0;
        margin: 0.45rem 0;
        font-family: 'DM Mono', monospace;
        font-size: 0.78rem;
        color: var(--muted);
        border-top: 1px solid var(--border);
        border-right: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
    }
    .source-item a { color: var(--amber) !important; text-decoration: none; }
    .source-item a:hover { text-decoration: underline; }
    .source-num {
        color: var(--muted);
        font-size: 0.65rem;
        margin-bottom: 0.2rem;
    }

    /* ── Report Container ── */
    .report-container {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 2.2rem 2.5rem;
        margin: 0.8rem 0;
        position: relative;
        overflow: hidden;
    }
    .report-container::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 3px;
        background: linear-gradient(90deg, var(--amber), var(--amber-dim), transparent);
    }

    /* ── Markdown in report ── */
    .report-container h1, .report-container h2, .report-container h3 {
        font-family: 'Syne', sans-serif !important;
        color: var(--text) !important;
        border-bottom: 1px solid var(--border);
        padding-bottom: 0.4rem;
    }
    .report-container p {
        font-family: 'Lora', serif;
        font-size: 0.97rem;
        line-height: 1.75;
        color: #c8cad0;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.04em !important;
        color: var(--text) !important;
    }
    .streamlit-expanderContent {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius) var(--radius) !important;
    }

    /* ── Spinner ── */
    .stSpinner > div > div { border-top-color: var(--amber) !important; }

    /* ── Alert / Error ── */
    .stAlert {
        background: var(--surface) !important;
        border-radius: var(--radius) !important;
        border: 1px solid var(--border2) !important;
        font-family: 'Syne', sans-serif !important;
    }

    /* ── Info box ── */
    .stInfo {
        background: var(--amber-glow) !important;
        border: 1px solid rgba(245,166,35,0.25) !important;
        border-radius: var(--radius) !important;
        color: var(--amber) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface) !important;
        border-radius: var(--radius) var(--radius) 0 0 !important;
        border: 1px solid var(--border) !important;
        border-bottom: none !important;
        gap: 0 !important;
        padding: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--muted) !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.06em !important;
        border-radius: 0 !important;
        padding: 0.7rem 1.4rem !important;
        border-bottom: 2px solid transparent !important;
        transition: color 0.2s, border-color 0.2s !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--amber) !important;
        border-bottom: 2px solid var(--amber) !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text) !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-lg) var(--radius-lg) !important;
        padding: 1.5rem 1.2rem !important;
    }

    /* ── Footer ── */
    .footer {
        text-align: center;
        padding: 2.5rem 1rem 1rem;
        color: var(--muted);
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        border-top: 1px solid var(--border);
        margin-top: 4rem;
        line-height: 2;
    }
    .footer-dot { color: var(--amber); margin: 0 0.4rem; }

    /* ── Animations ── */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .fade-up { animation: fadeUp 0.45s ease both; }
    .delay-1 { animation-delay: 0.08s; }
    .delay-2 { animation-delay: 0.16s; }
    .delay-3 { animation-delay: 0.24s; }
    .delay-4 { animation-delay: 0.32s; }

    @keyframes pulse-amber {
        0%, 100% { box-shadow: 0 0 0 0 rgba(245,166,35,0.4); }
        50%       { box-shadow: 0 0 0 8px rgba(245,166,35,0); }
    }
    .pulse { animation: pulse-amber 2.2s infinite; }
</style>
""", unsafe_allow_html=True)

# ── Initialize session state ──────────────────────────────────────────────────
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False
if 'sources_count' not in st.session_state:
    st.session_state.sources_count = 0

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero fade-up">
    <div class="hero-eyebrow">// Built by Abdullah Shafique &nbsp;·&nbsp; AI Engineer</div>
    <h1 class="hero-title">AI Research <span>Agent</span></h1>
    <p class="hero-sub">Powered by Google Gemini · Real-time web synthesis · Professional reports</p>
    <div style="margin-top:1.2rem;display:flex;justify-content:center;gap:0.6rem;flex-wrap:wrap;">
        <a href="https://www.linkedin.com/in/aadi-abdullah" target="_blank"
           style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.08em;
                  padding:0.3rem 0.8rem;border-radius:2px;text-decoration:none;
                  background:rgba(245,166,35,0.1);color:#f5a623;
                  border:1px solid rgba(245,166,35,0.3);">in / aadi-abdullah
        </a>
        <a href="https://github.com/aadi-abdullah" target="_blank"
           style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.08em;
                  padding:0.3rem 0.8rem;border-radius:2px;text-decoration:none;
                  background:rgba(245,166,35,0.1);color:#f5a623;
                  border:1px solid rgba(245,166,35,0.3);">github / aadi-abdullah
        </a>
        <span style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.08em;
                     padding:0.3rem 0.8rem;border-radius:2px;
                     background:rgba(74,222,128,0.08);color:#4ade80;
                     border:1px solid rgba(74,222,128,0.2);">Open Source
        </span>
    </div>
</div>
<div class="amber-rule"></div>
""", unsafe_allow_html=True)

# ── Status Cards ──────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

cards = [
    {
        "icon": "🤖",
        "title": "Gemini AI",
        "ok": bool(GOOGLE_API_KEY and GOOGLE_API_KEY.startswith("AIza")),
        "ok_label": "Active",
        "err_label": "Missing Key",
        "delay": "delay-1"
    },
    {
        "icon": "🔍",
        "title": "Tavily Search",
        "ok": bool(TAVILY_API_KEY and TAVILY_API_KEY.startswith("tvly")),
        "ok_label": "Active",
        "err_label": "Missing Key",
        "delay": "delay-2"
    },
    {
        "icon": "⚡",
        "title": "Rate Limit",
        "badge": True,
        "badge_label": "60 / min",
        "delay": "delay-3"
    },
    {
        "icon": "📄",
        "title": "PDF Export",
        "badge": True,
        "badge_label": "Ready",
        "delay": "delay-4"
    },
]

for col, card in zip([col1, col2, col3, col4], cards):
    with col:
        badge_html = ""
        if card.get("badge"):
            badge_html = f'<span class="badge badge-amber">{card["badge_label"]}</span>'
        elif card["ok"]:
            badge_html = f'<span class="badge badge-green">✓ {card["ok_label"]}</span>'
        else:
            badge_html = f'<span class="badge badge-red">✗ {card["err_label"]}</span>'

        st.markdown(f"""
        <div class="card fade-up {card['delay']}">
            <span class="card-icon">{card['icon']}</span>
            <div class="card-title">{card['title']}</div>
            {badge_html}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Search Box ────────────────────────────────────────────────────────────────
st.markdown('<div class="search-wrap fade-up">', unsafe_allow_html=True)
st.markdown('<span class="search-label">// Enter Research Query</span>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input(
        "Research question",
        value=st.session_state.query,
        placeholder="e.g., What are the latest breakthroughs in quantum computing?",
        label_visibility="collapsed"
    )
with col2:
    generate = st.button("🚀 Generate Report", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Example Questions ─────────────────────────────────────────────────────────
with st.expander("💡 Example Questions"):
    examples = [
        "What are the latest advances in renewable energy?",
        "How is AI being used in healthcare diagnosis?",
        "Recent breakthroughs in quantum computing",
        "Impact of remote work on productivity 2026",
        "Climate change solutions and innovations",
        "Future of electric vehicles technology",
        "Advances in CRISPR gene editing",
        "Space exploration missions 2026"
    ]
    cols = st.columns(4)
    for i, ex in enumerate(examples):
        with cols[i % 4]:
            if st.button(f"↗ {ex[:22]}…", key=f"ex_{i}", use_container_width=True):
                st.session_state.query = ex
                st.rerun()

# ── Main Research Logic ───────────────────────────────────────────────────────
if generate and query:
    if not GOOGLE_API_KEY or not GOOGLE_API_KEY.startswith("AIza"):
        st.error("⚠️ Please set up your Google Gemini API key in .env file")
    elif not TAVILY_API_KEY or not TAVILY_API_KEY.startswith("tvly"):
        st.error("⚠️ Please set up your Tavily API key in .env file")
    else:
        research_container = st.container()

        with research_container:
            st.markdown("""
            <div class="section-heading">
                <span class="section-heading-text">Research Process</span>
                <div class="section-heading-line"></div>
            </div>
            """, unsafe_allow_html=True)

            progress_bar = st.progress(0)
            status_text = st.empty()

            # Step 1 – Search
            status_text.markdown("""
            <div class="step-banner">
                <span class="step-num">STEP 01/03</span>
                🔍 &nbsp;Searching the web for relevant sources…
            </div>
            """, unsafe_allow_html=True)
            progress_bar.progress(25)

            try:
                with st.spinner("Gathering information from multiple sources…"):
                    results = run_search_agent(query)

                if not results or "results" not in results or len(results["results"]) == 0:
                    st.error("❌ No search results found. Try a different query.")
                else:
                    content = ""
                    sources = []
                    for r in results["results"]:
                        content += r.get("content", "") + "\n\n"
                        sources.append(r.get("url", "No URL"))

                    st.session_state.sources_count = len(sources)

                    # Step 2 – Summarize
                    status_text.markdown(f"""
                    <div class="step-banner">
                        <span class="step-num">STEP 02/03</span>
                        📚 &nbsp;Found {len(sources)} sources — analysing with Gemini AI…
                    </div>
                    """, unsafe_allow_html=True)
                    progress_bar.progress(50)

                    with st.spinner("Generating comprehensive summary with Gemini…"):
                        summary = summarize(content)

                    progress_bar.progress(75)

                    # Step 3 – Report
                    status_text.markdown("""
                    <div class="step-banner">
                        <span class="step-num">STEP 03/03</span>
                        📝 &nbsp;Composing final research report…
                    </div>
                    """, unsafe_allow_html=True)

                    report = generate_report(summary, sources)

                    progress_bar.progress(100)
                    status_text.markdown("""
                    <div class="step-banner success">
                        <span class="step-num" style="border-color:rgba(74,222,128,0.3);color:var(--green);background:rgba(74,222,128,0.08);">DONE</span>
                        ✅ &nbsp;Research report generated successfully.
                    </div>
                    """, unsafe_allow_html=True)

                    st.session_state.report_generated = True

                    # ── Metrics ──
                    st.markdown("<br>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{len(sources)}</div>
                            <div class="metric-label">Sources Analysed</div>
                        </div>""", unsafe_allow_html=True)
                    with c2:
                        words = len(report.split())
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{words:,}</div>
                            <div class="metric-label">Words Generated</div>
                        </div>""", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{datetime.now().strftime('%H:%M')}</div>
                            <div class="metric-label">Completed At</div>
                        </div>""", unsafe_allow_html=True)

                    # ── Report ──
                    st.markdown("""
                    <div class="section-heading" style="margin-top:2rem">
                        <span class="section-heading-text">Research Report</span>
                        <div class="section-heading-line"></div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="report-container">', unsafe_allow_html=True)
                    st.markdown(report)
                    st.markdown('</div>', unsafe_allow_html=True)

                    with st.expander(f"📚 All Sources ({len(sources)})"):
                        for i, source in enumerate(sources, 1):
                            st.markdown(f"{i}. [{source}]({source})")

                    # ── Download ──
                    st.markdown("""
                    <div class="section-heading" style="margin-top:2rem">
                        <span class="section-heading-text">Download</span>
                        <div class="section-heading-line"></div>
                    </div>
                    """, unsafe_allow_html=True)

                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c2:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            pdf_path = tmp.name

                        export_pdf(report, pdf_path)

                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()

                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"research_report_{query[:30].replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                        time.sleep(1)
                        try:
                            os.unlink(pdf_path)
                        except:
                            pass

            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                progress_bar.empty()

# ── Features Section ──────────────────────────────────────────────────────────
st.markdown("""
<div class="section-heading" style="margin-top:3rem">
    <span class="section-heading-text">Capabilities</span>
    <div class="section-heading-line"></div>
</div>
""", unsafe_allow_html=True)

features = [
    {"icon": "🤖", "title": "Gemini 2.0 Flash",   "desc": "State-of-the-art language model for analysis and synthesis"},
    {"icon": "🔍", "title": "Live Web Search",      "desc": "Real-time information retrieval via Tavily search API"},
    {"icon": "📊", "title": "Smart Summarisation",  "desc": "Multi-source distillation into structured insights"},
    {"icon": "📄", "title": "PDF Export",           "desc": "One-click professional report download"},
]

c1, c2, c3, c4 = st.columns(4)
for col, f, delay in zip([c1, c2, c3, c4], features, ["delay-1","delay-2","delay-3","delay-4"]):
    with col:
        st.markdown(f"""
        <div class="card fade-up {delay}" style="text-align:left;padding:1.5rem 1.3rem;">
            <span class="card-icon" style="font-size:1.4rem">{f['icon']}</span>
            <div class="card-title" style="margin-top:0.6rem">{f['title']}</div>
            <p style="font-size:0.8rem;color:var(--muted);margin:0;line-height:1.55;font-family:'DM Mono',monospace">{f['desc']}</p>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <div style="font-size:0.85rem;font-weight:700;color:#e8e9ec;margin-bottom:0.4rem;">
        Built by <span style="color:#f5a623;">Abdullah Shafique</span>
    </div>
    <div>
        AI Engineer &nbsp;·&nbsp; LangChain &nbsp;·&nbsp; LangGraph &nbsp;·&nbsp; FastAPI &nbsp;·&nbsp; Streamlit
    </div>
    <div style="margin-top:0.45rem;">
        <a href="https://www.linkedin.com/in/aadi-abdullah" target="_blank"
           style="color:#f5a623;text-decoration:none;margin:0 0.5rem;">LinkedIn</a>
        <span class="footer-dot">·</span>
        <a href="https://github.com/aadi-abdullah" target="_blank"
           style="color:#f5a623;text-decoration:none;margin:0 0.5rem;">GitHub</a>
        <span class="footer-dot">·</span>
        <a href="mailto:abdullahshafique2019@gmail.com"
           style="color:#f5a623;text-decoration:none;margin:0 0.5rem;">abdullahshafique2019@gmail.com</a>
    </div>
    <div style="margin-top:0.4rem;font-size:0.65rem">
        Gemini API &nbsp;·&nbsp; Tavily Search &nbsp;·&nbsp; 100% Open Source
    </div>
</div>
""", unsafe_allow_html=True)