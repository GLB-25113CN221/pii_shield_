"""Visual layer for PII Shield India: one stylesheet plus the header markup.

Everything here is presentation only. Colours are defined once as CSS variables at the
top of the stylesheet, so the whole look can be re-tinted by editing a few lines.
"""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Mukta:wght@400;500;600;700&display=swap');

:root {
  color-scheme: light;
  --paper:   #F3F4F9;   /* page background */
  --surface: #FFFFFF;   /* cards, inputs */
  --tint:    #E9EBF7;   /* sidebar, disabled fields */
  --ink:     #14173A;   /* main text, redaction bars */
  --muted:   #4F5575;   /* secondary text (passes AA on paper and white) */
  --line:    #C7CBE3;   /* borders */
  --indigo:  #2B2FA0;   /* primary actions */
  --indigo-d:#1E2178;   /* primary hover */
  --marigold:#FFB400;   /* highlighter accent */
  --warn-bg: #FFF4CF;
  --ok:      #0B7A5C;
  --bad:     #B3261E;
  --display: 'Bricolage Grotesque','Mukta','Noto Sans Devanagari','Nirmala UI',system-ui,sans-serif;
  --body:    'Mukta','Noto Sans Devanagari','Nirmala UI','Segoe UI',system-ui,sans-serif;
}

/* ---------- Canvas ---------- */
.stApp { background: var(--paper) !important; color: var(--ink) !important; font-family: var(--body); }
.block-container { max-width: 1180px; padding-top: 1.6rem; padding-bottom: 4rem; }
header[data-testid="stHeader"] { background: transparent !important; }
hr { border: none !important; border-top: 1px solid var(--line) !important; margin: 2rem 0 1.2rem !important; }

/* Text that Streamlit would otherwise tint for dark mode */
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] p,
.stApp label, .stApp label p, .stApp label span {
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; opacity: 1 !important;
}
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p,
.stApp small {
  color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; opacity: 1 !important;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  font-family: var(--display); color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
  letter-spacing: -0.01em;
}
.stApp [data-testid="stWidgetLabel"] p, .stApp label p { font-weight: 600; font-size: 0.97rem; }

/* ---------- Header ---------- */
.ps-hero {
  display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 2rem; align-items: center;
  background: var(--ink); border-radius: 22px; padding: 2.2rem 2.4rem; margin-bottom: 1.2rem;
  box-shadow: 0 18px 40px -22px rgba(20,23,58,.6);
}
.ps-hero, .ps-hero * { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
.ps-hero h1 {
  font-family: var(--display); font-weight: 800; font-size: clamp(2rem, 4.2vw, 3.2rem);
  line-height: 1.02; margin: 0 0 .8rem 0; padding: 0; letter-spacing: -0.02em;
}
.ps-hero p.ps-sub { font-size: 1.12rem; line-height: 1.5; margin: 0 0 1.2rem 0; max-width: 34em; color: #D9DCF5 !important; -webkit-text-fill-color: #D9DCF5 !important; }
.ps-chips { display: flex; flex-wrap: wrap; gap: .5rem; }
.ps-chip {
  font-size: .92rem; font-weight: 600; padding: .32rem .8rem; border-radius: 999px;
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.22);
}
.ps-chip::before { content: ""; display: inline-block; width: .5rem; height: .5rem; border-radius: 50%; background: var(--marigold); margin-right: .5rem; }

/* The memorable bit: a sample form whose private values get covered once on load */
.ps-doc {
  background: #FFFFFF; border-radius: 14px; padding: 1.1rem 1.3rem 1.2rem;
  box-shadow: 0 10px 28px -14px rgba(0,0,0,.55); transform: rotate(1.4deg);
}
.ps-doc, .ps-doc * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
.ps-doc-head { display: flex; justify-content: space-between; align-items: center; padding-bottom: .6rem; margin-bottom: .5rem; border-bottom: 2px solid var(--marigold); font-weight: 700; font-size: .95rem; }
.ps-doc-head span:last-child { font-weight: 600; font-size: .82rem; background: var(--warn-bg); padding: .12rem .55rem; border-radius: 999px; }
.ps-row { display: flex; align-items: baseline; gap: .8rem; padding: .42rem 0; font-size: 1.02rem; }
.ps-row .k { width: 4.6rem; flex: none; font-weight: 500; color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; }
.ps-row .v { position: relative; font-weight: 600; letter-spacing: .02em; white-space: nowrap; }
.ps-row .v::after {
  content: ""; position: absolute; left: -4px; right: -4px; top: -2px; bottom: -2px;
  background: var(--ink); border-radius: 3px; transform-origin: left center;
  animation: ps-cover .55s cubic-bezier(.65,0,.35,1) both; animation-delay: var(--d, .6s);
}
@keyframes ps-cover { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@media (prefers-reduced-motion: reduce) { .ps-row .v::after { animation: none; } }
@media (max-width: 860px) {
  .ps-hero { grid-template-columns: 1fr; padding: 1.5rem; }
  .ps-doc { transform: none; }
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] { background: var(--tint) !important; border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] .block-container, section[data-testid="stSidebar"] > div { padding-top: 1.6rem; }
.ps-loop { list-style: none; margin: .3rem 0 1rem 0; padding: 0 0 0 .2rem; }
.ps-loop li { position: relative; padding: .18rem 0 .18rem 1.5rem; font-weight: 600; font-size: .98rem; }
.ps-loop li::before { content: ""; position: absolute; left: .28rem; top: .62rem; width: .55rem; height: .55rem; border-radius: 50%; background: var(--indigo); }
.ps-loop li::after { content: ""; position: absolute; left: .52rem; top: 1.18rem; bottom: -.62rem; width: 2px; background: var(--line); }
.ps-loop li:last-child::after { display: none; }

/* ---------- Tabs (role selectors work across Streamlit versions) ---------- */
[role="tablist"] { gap: .2rem; border-bottom: 1px solid var(--line); }
.stApp [role="tab"], .stApp [role="tab"] *, .stApp [role="tab"] p {
  color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important;
  font-weight: 600 !important; font-size: 1.02rem !important; opacity: 1 !important; background: transparent !important;
}
.stApp [role="tab"][aria-selected="true"], .stApp [role="tab"][aria-selected="true"] *, .stApp [role="tab"][aria-selected="true"] p {
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; font-weight: 700 !important;
}
.stApp [role="tab"] { padding: .6rem 1.05rem !important; }
.stApp [role="tab"][aria-selected="true"] { box-shadow: inset 0 -4px 0 var(--marigold); border-radius: 6px 6px 0 0; }
.stApp [role="tab"]:hover, .stApp [role="tab"]:hover * { color: var(--indigo) !important; -webkit-text-fill-color: var(--indigo) !important; }
.stApp [role="tab"] > div[data-rac], div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none !important; }
.ps-intro { font-size: 1.05rem; color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; margin: .9rem 0 .4rem; max-width: 46em; }

/* ---------- Inputs ---------- */
div[data-baseweb="textarea"], div[data-baseweb="input"], div[data-baseweb="select"] > div {
  background: var(--surface) !important; border: 1.5px solid var(--line) !important; border-radius: 12px !important;
}
div[data-baseweb="textarea"]:focus-within, div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {
  border-color: var(--indigo) !important; box-shadow: 0 0 0 3px rgba(43,47,160,.18) !important;
}
.stApp textarea, .stApp input {
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
  background: transparent !important; caret-color: var(--indigo) !important; font-size: 1rem !important;
}
.stApp textarea::placeholder, .stApp input::placeholder { color: #6A7090 !important; -webkit-text-fill-color: #6A7090 !important; opacity: 1 !important; }
/* Read-only "Before / After" boxes */
.stApp textarea:disabled { background: var(--tint) !important; -webkit-text-fill-color: var(--ink) !important; color: var(--ink) !important; opacity: 1 !important; }
div[data-baseweb="textarea"]:has(textarea:disabled) { background: var(--tint) !important; }
div[data-baseweb="select"] * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
div[data-baseweb="select"] svg { fill: var(--ink) !important; }
/* Dropdown list renders in a portal outside .stApp */
div[data-baseweb="popover"] div[data-baseweb="menu"], div[data-baseweb="popover"] ul { background: var(--surface) !important; }
div[data-baseweb="popover"] li, div[data-baseweb="popover"] li * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
div[data-baseweb="popover"] li:hover, div[data-baseweb="popover"] li[aria-selected="true"] { background: var(--tint) !important; }

/* Checkbox (consent) becomes a clear, tappable panel */
.stApp [data-testid="stCheckbox"] {
  background: var(--surface); border: 1.5px solid var(--line); border-left: 5px solid var(--indigo);
  border-radius: 12px; padding: .8rem 1rem; margin: .2rem 0 .8rem;
}
.stApp [data-testid="stCheckbox"] span[data-baseweb="checkbox"] > div:first-child, .stApp [data-testid="stCheckbox"] label > span:first-child { border-color: var(--indigo) !important; }

/* Radio */
.stApp [data-testid="stRadio"] label, .stApp [data-testid="stRadio"] label * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }

/* ---------- File uploader (the previously invisible part) ---------- */
[data-testid="stFileUploaderDropzone"] {
  background: var(--surface) !important; border: 2px dashed #8A90CC !important; border-radius: 16px !important;
  padding: 1.3rem 1.4rem !important; transition: border-color .15s, background .15s;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--indigo) !important; background: #F7F8FF !important; }
[data-testid="stFileUploaderDropzone"] *, [data-testid="stFileUploaderDropzoneInstructions"] * {
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
}
[data-testid="stFileUploaderDropzone"] small { color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; }
[data-testid="stFileUploaderDropzone"] svg { fill: var(--indigo) !important; color: var(--indigo) !important; }
[data-testid="stFileUploaderDropzone"] button {
  background: var(--indigo) !important; border: 1.5px solid var(--indigo) !important; border-radius: 10px !important;
  opacity: 1 !important; box-shadow: none !important; padding: .5rem 1.1rem !important;
}
.stApp [data-testid="stFileUploaderDropzone"] button, .stApp [data-testid="stFileUploaderDropzone"] button *, .stApp [data-testid="stFileUploaderDropzone"] button p {
  color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-weight: 700 !important;
}
.stApp [data-testid="stFileUploaderDropzone"] button svg { fill: #FFFFFF !important; color: #FFFFFF !important; }
[data-testid="stFileUploaderDropzone"] button:hover { background: var(--indigo-d) !important; border-color: var(--indigo-d) !important; }
[data-testid="stFileUploaderFile"] { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: .3rem .6rem; margin-top: .4rem; }
[data-testid="stFileUploaderFile"] * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
[data-testid="stFileUploaderFile"] svg { fill: var(--ink) !important; }

/* ---------- Buttons ---------- */
.stApp .stButton > button, .stApp [data-testid="stFormSubmitButton"] button {
  background: var(--indigo) !important; border: 1.5px solid var(--indigo) !important; border-radius: 10px !important;
  padding: .55rem 1.3rem !important; opacity: 1 !important; transition: background .15s, transform .1s;
}
.stApp .stButton > button, .stApp .stButton > button *, .stApp [data-testid="stFormSubmitButton"] button, .stApp [data-testid="stFormSubmitButton"] button * {
  color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-weight: 700 !important;
}
.stApp .stButton > button:hover { background: var(--indigo-d) !important; border-color: var(--indigo-d) !important; }
.stApp .stButton > button:active { transform: translateY(1px); }
.stApp .stButton > button:disabled, .stApp .stButton > button:disabled * {
  background: #DADDEE !important; border-color: #C3C7E0 !important; color: #596080 !important; -webkit-text-fill-color: #596080 !important; opacity: 1 !important; cursor: not-allowed;
}
/* Downloads are outlined so the main action stays the loudest thing on screen */
.stApp .stDownloadButton > button {
  background: var(--surface) !important; border: 1.5px solid var(--indigo) !important; border-radius: 10px !important; opacity: 1 !important; padding: .5rem 1.2rem !important;
}
.stApp .stDownloadButton > button, .stApp .stDownloadButton > button * {
  color: var(--indigo) !important; -webkit-text-fill-color: var(--indigo) !important; font-weight: 700 !important;
}
.stApp .stDownloadButton > button:hover { background: var(--indigo) !important; }
.stApp .stDownloadButton > button:hover, .stApp .stDownloadButton > button:hover * { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
.stApp :focus-visible { outline: 3px solid var(--marigold) !important; outline-offset: 2px; }

/* ---------- Results ---------- */
[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: .9rem 1.1rem; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; font-weight: 600; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; font-family: var(--display); font-weight: 800; }
[data-testid="stExpander"] { background: var(--surface); border: 1px solid var(--line) !important; border-radius: 14px !important; overflow: hidden; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; font-weight: 700; }
[data-testid="stExpander"] summary:hover { background: var(--tint); }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
[data-testid="stCode"], [data-testid="stCode"] pre, [data-testid="stCode"] code { background: var(--tint) !important; color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; border-radius: 12px; }
[data-testid="stImageCaption"] { color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; }
[data-testid="stImage"] img { border-radius: 12px; border: 1px solid var(--line); }

/* ---------- Notices ---------- */
div[data-testid="stAlert"] { border-radius: 12px !important; border: 1px solid #E3C660 !important; border-left: 6px solid var(--marigold) !important; background: var(--warn-bg) !important; }
div[data-testid="stAlert"] *, div[data-testid="stAlert"] p { color: #2B2A12 !important; -webkit-text-fill-color: #2B2A12 !important; opacity: 1 !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) { background: #E6EBFF !important; border-color: #AEB8F0 !important; border-left-color: var(--indigo) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) { background: #FDE8E6 !important; border-color: #EDB1AC !important; border-left-color: var(--bad) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) * { color: #5C1410 !important; -webkit-text-fill-color: #5C1410 !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) { background: #E1F5EE !important; border-color: #9BD5C2 !important; border-left-color: var(--ok) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) * { color: #0A3D2E !important; -webkit-text-fill-color: #0A3D2E !important; }

.ps-foot { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 1rem 1.3rem; font-size: .98rem; }
.ps-foot * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
</style>
"""

HERO = (
    '<div class="ps-hero">'
    '<div>'
    '<h1>PII Shield India</h1>'
    '<p class="ps-sub">Find and cover Aadhaar numbers, PAN, phone numbers, names and addresses in text, '
    'images and documents, in Hindi and nine other Indian languages.</p>'
    '<div class="ps-chips">'
    '<span class="ps-chip">Runs on this machine</span>'
    '<span class="ps-chip">Audit log keeps no personal data</span>'
    '<span class="ps-chip">Exhibition build</span>'
    '</div></div>'
    '<div class="ps-doc" aria-hidden="true">'
    '<div class="ps-doc-head"><span>application_form.pdf</span><span>4 items covered</span></div>'
    '<div class="ps-row"><span class="k">नाम</span><span class="v" style="--d:.7s">राजेश कुमार</span></div>'
    '<div class="ps-row"><span class="k">Aadhaar</span><span class="v" style="--d:1.15s">2345 6789 4821</span></div>'
    '<div class="ps-row"><span class="k">PAN</span><span class="v" style="--d:1.6s">ABCPE1234F</span></div>'
    '<div class="ps-row"><span class="k">Phone</span><span class="v" style="--d:2.05s">+91 98765 43210</span></div>'
    '</div></div>'
)

AGENT_LOOP = (
    '<ul class="ps-loop">'
    '<li>Plan the next tool</li><li>Run it</li><li>Observe the result</li>'
    '<li>Reflect</li><li>Verify, or re-plan</li></ul>'
)


def apply_theme():
    """Inject the stylesheet and draw the header. Call once, right after set_page_config."""
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(HERO, unsafe_allow_html=True)


def intro(text):
    """One plain sentence under a tab title explaining what the tab does."""
    st.markdown(f'<p class="ps-intro">{text}</p>', unsafe_allow_html=True)
