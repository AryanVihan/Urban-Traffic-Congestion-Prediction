"""
styles.py
---------
Complete UI design system for the Traffic Intelligence Dashboard.
Glassmorphism · 3D effects · Light theme · Animations
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CSS CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

_FONT = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
"""

_VARS = """
:root {
  --primary:       #6366f1;
  --primary-soft:  rgba(99,102,241,0.12);
  --primary-glow:  rgba(99,102,241,0.28);
  --violet:        #8b5cf6;
  --cyan:          #06b6d4;
  --success:       #22c55e;
  --warning:       #f59e0b;
  --danger:        #ef4444;
  --text-1:        #1e293b;
  --text-2:        #475569;
  --text-3:        #94a3b8;
  --glass-bg:      rgba(255,255,255,0.72);
  --glass-border:  rgba(255,255,255,0.60);
  --glass-blur:    22px;
  --glass-shadow:  0 8px 32px rgba(99,102,241,0.13), 0 2px 8px rgba(0,0,0,0.06);
  --glass-shadow-hover: 0 24px 64px rgba(99,102,241,0.22), 0 6px 20px rgba(0,0,0,0.09);
  --radius-card:   20px;
  --radius-btn:    12px;
  --ease:          cubic-bezier(0.4, 0, 0.2, 1);
  --transition:    all 0.32s cubic-bezier(0.4, 0, 0.2, 1);
}
"""

_RESET = """
html, body, [data-testid="stApp"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* App background — animated gradient */
[data-testid="stApp"] {
  background:
    radial-gradient(ellipse at 20% 10%, rgba(99,102,241,0.12) 0%, transparent 55%),
    radial-gradient(ellipse at 80% 85%, rgba(139,92,246,0.10) 0%, transparent 55%),
    radial-gradient(ellipse at 60% 40%, rgba(6,182,212,0.07) 0%, transparent 50%),
    linear-gradient(145deg, #eef2ff 0%, #f5f0ff 40%, #f0f9ff 75%, #f8faff 100%) !important;
  min-height: 100vh !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background: transparent !important;
}

/* Page entrance animation */
[data-testid="stMainBlockContainer"] {
  animation: pageEntrance 0.45s var(--ease) both !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(99,102,241,0.3);
  border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.5); }
"""

_KEYFRAMES = """
@keyframes pageEntrance {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0);    }
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(24px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0)    scale(1);    }
}
@keyframes fadeInLeft {
  from { opacity: 0; transform: translateX(-20px); }
  to   { opacity: 1; transform: translateX(0);     }
}
@keyframes float {
  0%, 100% { transform: translateY(0px);  }
  50%       { transform: translateY(-7px); }
}
@keyframes shimmer {
  0%   { background-position: -400% center; }
  100% { background-position:  400% center; }
}
@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 20px rgba(99,102,241,0.2); }
  50%       { box-shadow: 0 0 40px rgba(99,102,241,0.45); }
}
@keyframes spin360 {
  to { transform: rotate(360deg); }
}
@keyframes tabSlide {
  from { transform: scaleX(0); }
  to   { transform: scaleX(1); }
}
@keyframes cardPop {
  0%   { transform: scale(0.93); opacity: 0; }
  70%  { transform: scale(1.02);             }
  100% { transform: scale(1);    opacity: 1; }
}
@keyframes gradientShift {
  0%   { background-position: 0%   50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0%   50%; }
}
"""

_SIDEBAR = """
/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background:
    linear-gradient(160deg,
      rgba(238,242,255,0.92) 0%,
      rgba(245,240,255,0.90) 100%) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(1.6) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(1.6) !important;
  border-right: 1px solid var(--glass-border) !important;
  box-shadow: 4px 0 40px rgba(99,102,241,0.10) !important;
}
[data-testid="stSidebarContent"] {
  background: transparent !important;
  padding: 1rem 1.1rem !important;
}

/* Sidebar headings */
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
  background: linear-gradient(135deg, var(--primary), var(--violet)) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  font-weight: 800 !important;
}

/* Sidebar captions */
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stCaption {
  color: var(--text-2) !important;
  font-size: 0.76rem !important;
}

/* Radio nav in sidebar */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  border-radius: 10px !important;
  padding: 9px 14px !important;
  margin-bottom: 3px !important;
  font-weight: 500 !important;
  font-size: 0.88rem !important;
  color: var(--text-1) !important;
  transition: var(--transition) !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background: rgba(99,102,241,0.10) !important;
  transform: translateX(4px) !important;
  color: var(--primary) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
  background: linear-gradient(90deg, rgba(99,102,241,0.15), rgba(139,92,246,0.10)) !important;
  color: var(--primary) !important;
  font-weight: 700 !important;
  box-shadow: inset 3px 0 0 var(--primary) !important;
}
"""

_METRICS = """
/* ── Metric cards ── */
[data-testid="stMetric"] {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-card) !important;
  padding: 1.3rem 1.5rem !important;
  box-shadow: var(--glass-shadow), inset 0 1px 0 rgba(255,255,255,0.9) !important;
  transform: perspective(700px) translateZ(2px) !important;
  transition: var(--transition) !important;
  animation: cardPop 0.45s var(--ease) both !important;
}
[data-testid="stMetric"]:hover {
  transform: perspective(700px) translateZ(12px) translateY(-5px) !important;
  box-shadow: var(--glass-shadow-hover), inset 0 1px 0 rgba(255,255,255,0.9) !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.9rem !important;
  font-weight: 800 !important;
  color: var(--primary) !important;
  letter-spacing: -0.03em !important;
  line-height: 1.1 !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.73rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.10em !important;
  color: var(--text-2) !important;
}
[data-testid="stMetricDelta"] {
  font-size: 0.82rem !important;
  font-weight: 600 !important;
}
"""

_BUTTONS = """
/* ── Buttons ── */
[data-testid="stButton"] > button,
[data-testid="stFormSubmitButton"] > button {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--radius-btn) !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  letter-spacing: 0.02em !important;
  padding: 0.6rem 1.4rem !important;
  box-shadow:
    0 4px 15px rgba(99,102,241,0.35),
    0 1px 0 rgba(255,255,255,0.2) inset !important;
  transform: perspective(400px) translateZ(0) !important;
  transition: var(--transition) !important;
  position: relative !important;
  overflow: hidden !important;
}
[data-testid="stButton"] > button::after,
[data-testid="stFormSubmitButton"] > button::after {
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background: linear-gradient(135deg, rgba(255,255,255,0.18) 0%, transparent 60%) !important;
  border-radius: inherit !important;
  pointer-events: none !important;
}
[data-testid="stButton"] > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
  transform: perspective(400px) translateZ(6px) translateY(-2px) !important;
  box-shadow:
    0 10px 28px rgba(99,102,241,0.50),
    0 1px 0 rgba(255,255,255,0.2) inset !important;
}
[data-testid="stButton"] > button:active,
[data-testid="stFormSubmitButton"] > button:active {
  transform: perspective(400px) translateZ(0) translateY(0) scale(0.98) !important;
}
"""

_TABS = """
/* ── Tabs ── */
[data-testid="stTabs"] {
  background: rgba(255,255,255,0.55) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
  border-radius: 14px !important;
  border: 1px solid var(--glass-border) !important;
  padding: 6px !important;
  box-shadow: 0 2px 12px rgba(99,102,241,0.08) !important;
  overflow: hidden !important;
}
[data-testid="stTab"] {
  border-radius: 10px !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  color: var(--text-2) !important;
  transition: var(--transition) !important;
  position: relative !important;
  border: none !important;
  background: transparent !important;
}
[data-testid="stTab"]:hover {
  color: var(--primary) !important;
  background: rgba(99,102,241,0.07) !important;
}
[data-testid="stTab"][aria-selected="true"] {
  background: rgba(255,255,255,0.95) !important;
  color: var(--primary) !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 10px rgba(99,102,241,0.18) !important;
}
[data-testid="stTab"][aria-selected="true"]::after {
  content: '' !important;
  position: absolute !important;
  bottom: 0 !important; left: 12% !important;
  width: 76% !important; height: 2.5px !important;
  background: linear-gradient(90deg, var(--primary), var(--violet)) !important;
  border-radius: 2px 2px 0 0 !important;
  animation: tabSlide 0.25s var(--ease) forwards !important;
}
"""

_FORMS = """
/* ── Forms ── */
[data-testid="stForm"] {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 24px !important;
  padding: 1.8rem !important;
  box-shadow: var(--glass-shadow) !important;
  animation: fadeInUp 0.4s var(--ease) both !important;
}
"""

_INPUTS = """
/* ── Text inputs / textareas ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
  background: rgba(255,255,255,0.85) !important;
  border: 1.5px solid rgba(99,102,241,0.22) !important;
  border-radius: 10px !important;
  color: var(--text-1) !important;
  font-family: 'Inter', sans-serif !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px var(--primary-soft) !important;
  outline: none !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
  background: rgba(255,255,255,0.85) !important;
  border: 1.5px solid rgba(99,102,241,0.22) !important;
  border-radius: 10px !important;
  transition: border-color 0.2s ease !important;
}
[data-testid="stSelectbox"] > div > div:hover {
  border-color: var(--primary) !important;
}

/* ── Sliders ── */
[data-testid="stSliderThumbValue"] {
  background: var(--primary) !important;
  color: #fff !important;
  border-radius: 6px !important;
  font-size: 0.74rem !important;
  font-weight: 600 !important;
  padding: 2px 7px !important;
  box-shadow: 0 2px 8px rgba(99,102,241,0.4) !important;
}

/* ── Checkboxes ── */
[data-testid="stCheckbox"] label {
  color: var(--text-1) !important;
  font-weight: 500 !important;
}
[data-testid="stCheckbox"] input[type="checkbox"] {
  accent-color: var(--primary) !important;
  width: 16px !important; height: 16px !important;
  cursor: pointer !important;
}

/* ── Widget labels ── */
[data-testid="stWidgetLabel"] {
  font-weight: 600 !important;
  font-size: 0.82rem !important;
  color: var(--text-1) !important;
  letter-spacing: 0.01em !important;
}
"""

_EXPANDERS = """
/* ── Expanders ── */
[data-testid="stExpander"] {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 16px !important;
  overflow: hidden !important;
  box-shadow: 0 2px 16px rgba(99,102,241,0.08) !important;
  transition: var(--transition) !important;
  margin-bottom: 0.6rem !important;
}
[data-testid="stExpander"]:hover {
  box-shadow: 0 6px 28px rgba(99,102,241,0.14) !important;
  transform: translateY(-1px) !important;
}
[data-testid="stExpander"] details summary {
  font-weight: 600 !important;
  color: var(--text-1) !important;
  padding: 0.85rem 1.1rem !important;
  font-family: 'Inter', sans-serif !important;
  transition: background 0.2s ease !important;
}
[data-testid="stExpander"] details summary:hover {
  background: rgba(99,102,241,0.06) !important;
}
[data-testid="stExpanderDetails"] {
  border-top: 1px solid var(--glass-border) !important;
  padding: 1rem 1.1rem !important;
}
"""

_DATAFRAMES = """
/* ── Dataframes ── */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(99,102,241,0.15) !important;
  border-radius: 16px !important;
  overflow: hidden !important;
  box-shadow: 0 3px 16px rgba(99,102,241,0.07) !important;
  background: rgba(255,255,255,0.7) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
  animation: fadeInUp 0.4s var(--ease) both !important;
}
"""

_ALERTS = """
/* ── Alerts / info boxes ── */
[data-testid="stAlert"] {
  background: rgba(255,255,255,0.70) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
  border-radius: 14px !important;
  border-left-width: 4px !important;
  box-shadow: 0 2px 12px rgba(99,102,241,0.08) !important;
  animation: fadeInUp 0.35s var(--ease) both !important;
}
"""

_DIVIDERS = """
/* ── Dividers ── */
hr,
[data-testid="stMarkdown"] hr {
  border: none !important;
  height: 1px !important;
  background: linear-gradient(90deg,
    transparent,
    rgba(99,102,241,0.25) 20%,
    rgba(139,92,246,0.25) 50%,
    rgba(99,102,241,0.25) 80%,
    transparent) !important;
  margin: 1.4rem 0 !important;
}
"""

_HEADINGS = """
/* ── Page-level headings ── */
[data-testid="stMainBlockContainer"] h1 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 900 !important;
  font-size: 2.1rem !important;
  letter-spacing: -0.03em !important;
  background: linear-gradient(135deg,
    var(--primary) 0%, var(--violet) 50%, var(--cyan) 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  line-height: 1.15 !important;
  margin-bottom: 0.2rem !important;
}
[data-testid="stMainBlockContainer"] h2 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 700 !important;
  color: var(--text-1) !important;
  font-size: 1.2rem !important;
  letter-spacing: -0.01em !important;
}
[data-testid="stMainBlockContainer"] h3 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  color: var(--text-2) !important;
  font-size: 1rem !important;
}

/* Bar charts / generic Streamlit charts */
[data-testid="stArrowVegaLiteChart"],
[data-testid="stPlotlyChart"] {
  background: rgba(255,255,255,0.65) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 18px !important;
  padding: 12px !important;
  box-shadow: 0 4px 20px rgba(99,102,241,0.08) !important;
  overflow: hidden !important;
  animation: fadeInUp 0.45s var(--ease) both !important;
}
"""

_SPINNER = """
/* ── Spinner ── */
[data-testid="stSpinner"] > div {
  border-top-color: var(--primary) !important;
}
"""

# Concat all CSS
ALL_CSS = "\n".join([
    _FONT, _VARS, _RESET, _KEYFRAMES, _SIDEBAR, _METRICS, _BUTTONS,
    _TABS, _FORMS, _INPUTS, _EXPANDERS, _DATAFRAMES, _ALERTS,
    _DIVIDERS, _HEADINGS, _SPINNER,
])


# ─────────────────────────────────────────────────────────────────────────────
#  HTML COMPONENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def inject_styles() -> None:
    """Call once, immediately after st.set_page_config()."""
    import streamlit as st
    st.markdown(f"<style>{ALL_CSS}</style>", unsafe_allow_html=True)
    # Background decorative orbs (fixed, pointer-events: none)
    st.markdown("""
    <div style="
      position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden;">
      <div style="
        position:absolute;width:600px;height:600px;border-radius:50%;
        background:radial-gradient(circle,rgba(99,102,241,0.10) 0%,transparent 70%);
        top:-180px;left:-180px;animation:float 9s ease-in-out infinite;"></div>
      <div style="
        position:absolute;width:500px;height:500px;border-radius:50%;
        background:radial-gradient(circle,rgba(139,92,246,0.09) 0%,transparent 70%);
        bottom:-150px;right:-150px;animation:float 11s ease-in-out infinite reverse;"></div>
      <div style="
        position:absolute;width:350px;height:350px;border-radius:50%;
        background:radial-gradient(circle,rgba(6,182,212,0.07) 0%,transparent 70%);
        top:40%;left:55%;animation:float 13s ease-in-out infinite 2s;"></div>
    </div>""", unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = "",
                tag: str = "h1") -> str:
    """
    Glassmorphism hero header for each page.
    Returns raw HTML — pass to st.markdown(..., unsafe_allow_html=True).
    """
    sub_html = (
        f"<p style='margin:6px 0 0;font-size:0.95rem;font-weight:400;"
        f"color:#475569;letter-spacing:0.01em'>{subtitle}</p>"
        if subtitle else ""
    )
    return f"""
<div style="
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border: 1px solid rgba(255,255,255,0.65);
  border-radius: 24px;
  padding: 28px 32px;
  margin-bottom: 20px;
  box-shadow: 0 8px 40px rgba(99,102,241,0.13), inset 0 1px 0 rgba(255,255,255,1);
  animation: fadeInUp 0.45s cubic-bezier(0.4,0,0.2,1) both;
  display: flex;
  align-items: center;
  gap: 18px;
  position: relative;
  overflow: hidden;
">
  <!-- shimmer strip -->
  <div style="
    position:absolute;inset:0;
    background:linear-gradient(105deg,transparent 35%,rgba(255,255,255,0.35) 50%,transparent 65%);
    background-size:200% 100%;
    animation:shimmer 3.5s ease-in-out infinite;
    pointer-events:none;border-radius:inherit;"></div>
  <!-- icon -->
  <div style="
    font-size:2.6rem;line-height:1;
    filter:drop-shadow(0 4px 12px rgba(99,102,241,0.25));
    animation:float 5s ease-in-out infinite;
    flex-shrink:0;">{icon}</div>
  <!-- text -->
  <div>
    <{tag} style="
      margin:0;
      font-family:'Inter',sans-serif;
      font-weight:900;
      font-size:1.9rem;
      letter-spacing:-0.03em;
      line-height:1.1;
      background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#06b6d4 100%);
      -webkit-background-clip:text;
      -webkit-text-fill-color:transparent;
      background-clip:text;">{title}</{tag}>
    {sub_html}
  </div>
</div>"""


def metric_row(metrics: list) -> str:
    """
    Render a row of glassmorphism KPI cards.
    metrics: list of dicts with keys: icon, value, label, color (optional)
    """
    cards = []
    delays = [0, 0.07, 0.14, 0.21, 0.28]
    for i, m in enumerate(metrics):
        col = m.get("color", "#6366f1")
        delay = delays[i] if i < len(delays) else 0
        cards.append(f"""
<div style="
  flex:1;min-width:140px;
  background:rgba(255,255,255,0.72);
  backdrop-filter:blur(18px);
  -webkit-backdrop-filter:blur(18px);
  border:1px solid rgba(255,255,255,0.65);
  border-radius:20px;
  padding:22px 20px 18px;
  box-shadow:0 8px 32px rgba(99,102,241,0.12),inset 0 1px 0 rgba(255,255,255,1);
  transform:perspective(700px) translateZ(2px);
  transition:all 0.32s cubic-bezier(0.4,0,0.2,1);
  animation:cardPop 0.45s cubic-bezier(0.4,0,0.2,1) {delay}s both;
  cursor:default;position:relative;overflow:hidden;"
  onmouseover="this.style.transform='perspective(700px) translateZ(14px) translateY(-5px)';
               this.style.boxShadow='0 24px 60px rgba(99,102,241,0.22),inset 0 1px 0 rgba(255,255,255,1)'"
  onmouseout="this.style.transform='perspective(700px) translateZ(2px)';
              this.style.boxShadow='0 8px 32px rgba(99,102,241,0.12),inset 0 1px 0 rgba(255,255,255,1)'">
  <!-- top accent bar -->
  <div style="
    position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,{col},{col}aa,transparent);
    border-radius:20px 20px 0 0;"></div>
  <div style="font-size:1.6rem;margin-bottom:8px;
    filter:drop-shadow(0 3px 8px {col}44);">{m['icon']}</div>
  <div style="
    font-size:1.75rem;font-weight:800;
    color:{col};letter-spacing:-0.03em;line-height:1.1;
    font-family:'Inter',sans-serif;">{m['value']}</div>
  <div style="
    font-size:0.70rem;font-weight:700;
    text-transform:uppercase;letter-spacing:0.10em;
    color:#64748b;margin-top:5px;
    font-family:'Inter',sans-serif;">{m['label']}</div>
</div>""")
    inner = "\n".join(cards)
    return f"""
<div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:12px;">
  {inner}
</div>"""


def glass_section(title: str, icon: str = "") -> str:
    """A glass card section subheader."""
    prefix = f"<span style='margin-right:8px;font-size:1.1rem'>{icon}</span>" if icon else ""
    return f"""
<div style="
  background:rgba(255,255,255,0.55);
  backdrop-filter:blur(12px);
  -webkit-backdrop-filter:blur(12px);
  border:1px solid rgba(255,255,255,0.65);
  border-radius:14px;
  padding:12px 18px;
  margin:16px 0 10px;
  display:inline-flex;align-items:center;
  box-shadow:0 2px 12px rgba(99,102,241,0.08);
  animation:fadeInLeft 0.35s cubic-bezier(0.4,0,0.2,1) both;">
  {prefix}
  <span style="
    font-family:'Inter',sans-serif;
    font-size:1.05rem;font-weight:700;
    color:#1e293b;letter-spacing:-0.01em;">{title}</span>
</div>"""


def glass_badge(text: str, color: str = "#6366f1") -> str:
    """Small pill badge."""
    return (
        f"<span style='display:inline-block;background:{color}1a;color:{color};"
        f"border:1px solid {color}33;border-radius:99px;padding:3px 12px;"
        f"font-size:0.75rem;font-weight:700;letter-spacing:0.04em;"
        f"font-family:Inter,sans-serif'>{text}</span>"
    )


def congestion_banner(label: str, confidence: float,
                      inference_ms: float, impact: str) -> str:
    """Large result banner for the Predict page."""
    col_map = {
        "Low": ("#22c55e", "#f0fdf4"),
        "Medium": ("#f59e0b", "#fffbeb"),
        "High": ("#f97316", "#fff7ed"),
        "Severe": ("#ef4444", "#fef2f2"),
    }
    emoji_map = {"Low":"🟢","Medium":"🟡","High":"🟠","Severe":"🔴"}
    col, bg = col_map.get(label, ("#6366f1","#f0f4ff"))
    emoji = emoji_map.get(label, "⚪")
    return f"""
<div style="
  background:{bg};
  border:2px solid {col};
  border-radius:24px;
  padding:32px 24px;
  text-align:center;
  margin-bottom:20px;
  box-shadow:0 12px 48px {col}33,inset 0 1px 0 rgba(255,255,255,0.9);
  backdrop-filter:blur(16px);
  -webkit-backdrop-filter:blur(16px);
  animation:cardPop 0.5s cubic-bezier(0.4,0,0.2,1) both;
  position:relative;overflow:hidden;">
  <div style="
    position:absolute;inset:0;
    background:linear-gradient(105deg,transparent 35%,rgba(255,255,255,0.3) 50%,transparent 65%);
    background-size:200% 100%;
    animation:shimmer 2.5s ease-in-out infinite;
    pointer-events:none;border-radius:inherit;"></div>
  <div style="font-size:56px;line-height:1;margin-bottom:10px;
    animation:float 4s ease-in-out infinite;">{emoji}</div>
  <div style="font-size:2.2rem;font-weight:900;color:{col};
    font-family:Inter,sans-serif;letter-spacing:-0.03em;">{label} Congestion</div>
  <div style="margin-top:10px;font-size:0.95rem;color:#475569;">
    Confidence <strong style="color:{col}">{confidence}%</strong>
    &nbsp;·&nbsp;
    Inference <strong style="color:{col}">{inference_ms} ms</strong>
  </div>
  <div style="margin-top:8px;font-size:0.9rem;color:#374151;font-style:italic">
    {impact}</div>
</div>"""
