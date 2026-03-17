"""
styles.py
---------
Complete UI design system — Dark Glassmorphism Edition.
Deep dark navy · Glowing accents · 3D effects · Smooth animations
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CSS CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

_FONT = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
"""

_VARS = """
:root {
  --primary:       #7c3aed;
  --primary-light: #a78bfa;
  --primary-soft:  rgba(124,58,237,0.18);
  --primary-glow:  rgba(124,58,237,0.45);
  --violet:        #8b5cf6;
  --cyan:          #22d3ee;
  --success:       #4ade80;
  --warning:       #fbbf24;
  --danger:        #f87171;
  --text-1:        #f1f5f9;
  --text-2:        #94a3b8;
  --text-3:        #475569;
  --glass-bg:      rgba(15, 22, 45, 0.78);
  --glass-border:  rgba(255, 255, 255, 0.07);
  --glass-border-bright: rgba(255, 255, 255, 0.12);
  --glass-blur:    24px;
  --glass-shadow:  0 8px 32px rgba(0,0,0,0.45), 0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06);
  --glass-shadow-hover: 0 20px 60px rgba(0,0,0,0.55), 0 6px 20px rgba(124,58,237,0.25), inset 0 1px 0 rgba(255,255,255,0.08);
  --radius-card:   20px;
  --radius-btn:    12px;
  --ease:          cubic-bezier(0.4, 0, 0.2, 1);
  --transition:    all 0.30s cubic-bezier(0.4, 0, 0.2, 1);
  --nav-active-bg: rgba(124, 58, 237, 0.22);
  --nav-hover-bg:  rgba(124, 58, 237, 0.10);
}
"""

_RESET = """
html, body, [data-testid="stApp"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* App background — deep dark with glowing radial blobs */
[data-testid="stApp"] {
  background:
    radial-gradient(ellipse at 15%  8%,  rgba(124,58,237,0.22)  0%, transparent 50%),
    radial-gradient(ellipse at 85% 90%,  rgba(139,92,246,0.18)  0%, transparent 50%),
    radial-gradient(ellipse at 55% 42%,  rgba(34,211,238,0.10)  0%, transparent 45%),
    radial-gradient(ellipse at 10% 80%,  rgba(124,58,237,0.10)  0%, transparent 40%),
    linear-gradient(150deg, #06080f 0%, #080c18 40%, #0a0618 75%, #06080f 100%) !important;
  min-height: 100vh !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background: transparent !important;
}

/* Page entrance animation */
[data-testid="stMainBlockContainer"] {
  animation: pageEntrance 0.42s var(--ease) both !important;
}

/* Global text colour fix */
[data-testid="stMainBlockContainer"] p,
[data-testid="stMainBlockContainer"] span,
[data-testid="stMainBlockContainer"] li {
  color: var(--text-1) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
::-webkit-scrollbar-thumb {
  background: rgba(124,58,237,0.35);
  border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(124,58,237,0.6); }
"""

_KEYFRAMES = """
@keyframes pageEntrance {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0);    }
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(22px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0)    scale(1);    }
}
@keyframes fadeInLeft {
  from { opacity: 0; transform: translateX(-18px); }
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
  0%, 100% { box-shadow: 0 0 20px rgba(124,58,237,0.3); }
  50%       { box-shadow: 0 0 50px rgba(124,58,237,0.65); }
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
@keyframes glow {
  0%, 100% { box-shadow: 0 0 15px rgba(124,58,237,0.4); }
  50%       { box-shadow: 0 0 35px rgba(124,58,237,0.75), 0 0 60px rgba(139,92,246,0.3); }
}
@keyframes navPulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.7; }
}
"""

_SIDEBAR = """
/* ── Sidebar shell ── */
[data-testid="stSidebar"] {
  background:
    linear-gradient(170deg,
      rgba(6, 8, 20, 0.97) 0%,
      rgba(10, 6, 24, 0.97) 100%) !important;
  backdrop-filter: blur(28px) saturate(1.4) !important;
  -webkit-backdrop-filter: blur(28px) saturate(1.4) !important;
  border-right: 1px solid rgba(124,58,237,0.18) !important;
  box-shadow: 4px 0 50px rgba(0,0,0,0.5), 2px 0 20px rgba(124,58,237,0.08) !important;
}
[data-testid="stSidebarContent"] {
  background: transparent !important;
  padding: 0.9rem 0.85rem !important;
}

/* Sidebar headings */
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  background: linear-gradient(135deg, var(--primary-light), var(--cyan)) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  font-weight: 800 !important;
}

/* Sidebar text */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small {
  color: var(--text-2) !important;
}

/* ── Navigation radio — complete overhaul ── */

/* Hide the default radio circles */
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
  display: none !important;
}

/* Container gap */
[data-testid="stSidebar"] [data-testid="stRadio"] > div > div {
  gap: 2px !important;
  padding: 4px 0 !important;
}

/* Each nav item label */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  border-radius: 11px !important;
  padding: 9px 12px 9px 14px !important;
  margin-bottom: 1px !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  color: var(--text-2) !important;
  transition: var(--transition) !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  gap: 9px !important;
  border-left: 2.5px solid transparent !important;
  position: relative !important;
  letter-spacing: 0.01em !important;
  user-select: none !important;
}

/* Hover state */
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background: var(--nav-hover-bg) !important;
  color: var(--primary-light) !important;
  border-left-color: rgba(124,58,237,0.45) !important;
  transform: translateX(3px) !important;
}

/* Active / selected state — glowing gradient fill */
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
  background: linear-gradient(90deg,
    rgba(124,58,237,0.28) 0%,
    rgba(139,92,246,0.14) 60%,
    transparent 100%) !important;
  color: #c4b5fd !important;
  font-weight: 700 !important;
  border-left-color: var(--violet) !important;
  box-shadow:
    0 0 20px rgba(124,58,237,0.15),
    inset 0 0 30px rgba(124,58,237,0.06) !important;
  letter-spacing: 0.015em !important;
}

/* Active item right-side glow dot */
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked)::after {
  content: '' !important;
  position: absolute !important;
  right: 12px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  width: 6px !important;
  height: 6px !important;
  border-radius: 50% !important;
  background: var(--violet) !important;
  box-shadow: 0 0 8px var(--violet), 0 0 16px rgba(139,92,246,0.6) !important;
  animation: navPulse 2.5s ease-in-out infinite !important;
}

/* Sidebar divider */
[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,0.06) !important;
  margin: 10px 0 !important;
}
"""

_METRICS = """
/* ── Metric cards ── */
[data-testid="stMetric"] {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) !important;
  border: 1px solid var(--glass-border-bright) !important;
  border-radius: var(--radius-card) !important;
  padding: 1.3rem 1.5rem !important;
  box-shadow: var(--glass-shadow) !important;
  transform: perspective(700px) translateZ(2px) !important;
  transition: var(--transition) !important;
  animation: cardPop 0.45s var(--ease) both !important;
}
[data-testid="stMetric"]:hover {
  transform: perspective(700px) translateZ(14px) translateY(-5px) !important;
  box-shadow: var(--glass-shadow-hover) !important;
  border-color: rgba(124,58,237,0.3) !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.85rem !important;
  font-weight: 800 !important;
  color: var(--primary-light) !important;
  letter-spacing: -0.03em !important;
  line-height: 1.1 !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.72rem !important;
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
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%) !important;
  color: #f3f0ff !important;
  border: 1px solid rgba(167,139,250,0.25) !important;
  border-radius: var(--radius-btn) !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  letter-spacing: 0.02em !important;
  padding: 0.6rem 1.4rem !important;
  box-shadow:
    0 4px 20px rgba(124,58,237,0.50),
    0 1px 0 rgba(255,255,255,0.12) inset !important;
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
  background: linear-gradient(135deg, rgba(255,255,255,0.12) 0%, transparent 55%) !important;
  border-radius: inherit !important;
  pointer-events: none !important;
}
[data-testid="stButton"] > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
  transform: perspective(400px) translateZ(6px) translateY(-2px) !important;
  box-shadow:
    0 12px 35px rgba(124,58,237,0.65),
    0 1px 0 rgba(255,255,255,0.15) inset !important;
  border-color: rgba(167,139,250,0.4) !important;
}
[data-testid="stButton"] > button:active,
[data-testid="stFormSubmitButton"] > button:active {
  transform: perspective(400px) translateZ(0) scale(0.98) !important;
}
"""

_TABS = """
/* ── Tabs ── */
[data-testid="stTabs"] {
  background: rgba(15, 22, 45, 0.60) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border-radius: 14px !important;
  border: 1px solid var(--glass-border-bright) !important;
  padding: 5px !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.35) !important;
  overflow: hidden !important;
}
[data-testid="stTab"] {
  border-radius: 10px !important;
  font-weight: 500 !important;
  font-size: 0.84rem !important;
  color: var(--text-2) !important;
  transition: var(--transition) !important;
  position: relative !important;
  border: none !important;
  background: transparent !important;
}
[data-testid="stTab"]:hover {
  color: var(--primary-light) !important;
  background: rgba(124,58,237,0.10) !important;
}
[data-testid="stTab"][aria-selected="true"] {
  background: rgba(124,58,237,0.22) !important;
  color: #c4b5fd !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 14px rgba(124,58,237,0.25) !important;
  border: 1px solid rgba(124,58,237,0.25) !important;
}
[data-testid="stTab"][aria-selected="true"]::after {
  content: '' !important;
  position: absolute !important;
  bottom: 0 !important; left: 12% !important;
  width: 76% !important; height: 2px !important;
  background: linear-gradient(90deg, var(--primary-light), var(--cyan)) !important;
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
  border: 1px solid var(--glass-border-bright) !important;
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
  background: rgba(10, 14, 30, 0.75) !important;
  border: 1.5px solid rgba(124,58,237,0.22) !important;
  border-radius: 10px !important;
  color: var(--text-1) !important;
  font-family: 'Inter', sans-serif !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--primary-light) !important;
  box-shadow: 0 0 0 3px rgba(124,58,237,0.25) !important;
  outline: none !important;
  background: rgba(15, 22, 45, 0.90) !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
  background: rgba(10, 14, 30, 0.75) !important;
  border: 1.5px solid rgba(124,58,237,0.22) !important;
  border-radius: 10px !important;
  color: var(--text-1) !important;
  transition: border-color 0.2s ease !important;
}
[data-testid="stSelectbox"] > div > div:hover {
  border-color: var(--primary-light) !important;
}

/* ── Sliders ── */
[data-testid="stSlider"] [data-testid="stSliderThumb"] {
  background: var(--primary-light) !important;
  box-shadow: 0 0 10px rgba(124,58,237,0.6) !important;
}
[data-testid="stSliderThumbValue"] {
  background: var(--primary) !important;
  color: #f3f0ff !important;
  border-radius: 6px !important;
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  padding: 2px 7px !important;
  box-shadow: 0 2px 10px rgba(124,58,237,0.55) !important;
}

/* ── Checkboxes ── */
[data-testid="stCheckbox"] label {
  color: var(--text-1) !important;
  font-weight: 500 !important;
}
[data-testid="stCheckbox"] input[type="checkbox"] {
  accent-color: var(--primary-light) !important;
  width: 16px !important; height: 16px !important;
  cursor: pointer !important;
}

/* ── Widget labels ── */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p {
  font-weight: 600 !important;
  font-size: 0.82rem !important;
  color: var(--text-2) !important;
  letter-spacing: 0.01em !important;
}

/* Dropdown popup */
[data-baseweb="popover"] ul,
[data-baseweb="menu"] {
  background: rgba(12, 16, 35, 0.97) !important;
  border: 1px solid rgba(124,58,237,0.25) !important;
  backdrop-filter: blur(20px) !important;
}
[data-baseweb="menu"] li:hover {
  background: rgba(124,58,237,0.18) !important;
}
"""

_EXPANDERS = """
/* ── Expanders ── */
[data-testid="stExpander"] {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  border: 1px solid var(--glass-border-bright) !important;
  border-radius: 16px !important;
  overflow: hidden !important;
  box-shadow: var(--glass-shadow) !important;
  transition: var(--transition) !important;
  margin-bottom: 0.6rem !important;
}
[data-testid="stExpander"]:hover {
  box-shadow: var(--glass-shadow-hover) !important;
  transform: translateY(-1px) !important;
  border-color: rgba(124,58,237,0.22) !important;
}
[data-testid="stExpander"] details summary {
  font-weight: 600 !important;
  color: var(--text-1) !important;
  padding: 0.85rem 1.1rem !important;
  font-family: 'Inter', sans-serif !important;
  transition: background 0.2s ease !important;
}
[data-testid="stExpander"] details summary:hover {
  background: rgba(124,58,237,0.08) !important;
}
[data-testid="stExpanderDetails"] {
  border-top: 1px solid var(--glass-border-bright) !important;
  padding: 1rem 1.1rem !important;
}
"""

_DATAFRAMES = """
/* ── Dataframes ── */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(124,58,237,0.18) !important;
  border-radius: 16px !important;
  overflow: hidden !important;
  box-shadow: var(--glass-shadow) !important;
  background: rgba(10, 14, 30, 0.70) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  animation: fadeInUp 0.4s var(--ease) both !important;
}
"""

_ALERTS = """
/* ── Alerts ── */
[data-testid="stAlert"] {
  background: rgba(15, 22, 45, 0.80) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border-radius: 14px !important;
  border-left-width: 4px !important;
  box-shadow: var(--glass-shadow) !important;
  animation: fadeInUp 0.35s var(--ease) both !important;
}
[data-testid="stAlert"] p {
  color: var(--text-1) !important;
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
    rgba(124,58,237,0.35) 20%,
    rgba(139,92,246,0.35) 50%,
    rgba(124,58,237,0.35) 80%,
    transparent) !important;
  margin: 1.4rem 0 !important;
}
"""

_HEADINGS = """
/* ── Page-level headings ── */
[data-testid="stMainBlockContainer"] h1 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 900 !important;
  font-size: 2.0rem !important;
  letter-spacing: -0.03em !important;
  background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 40%, #22d3ee 100%) !important;
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
  font-size: 1.15rem !important;
  letter-spacing: -0.01em !important;
}
[data-testid="stMainBlockContainer"] h3 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  color: var(--text-2) !important;
  font-size: 0.98rem !important;
}

/* Charts glass wrap */
[data-testid="stArrowVegaLiteChart"],
[data-testid="stPlotlyChart"] {
  background: rgba(10, 14, 30, 0.65) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid var(--glass-border-bright) !important;
  border-radius: 18px !important;
  padding: 10px !important;
  box-shadow: var(--glass-shadow) !important;
  overflow: hidden !important;
  animation: fadeInUp 0.45s var(--ease) both !important;
}
"""

_SPINNER = """
/* ── Spinner ── */
[data-testid="stSpinner"] > div {
  border-top-color: var(--primary-light) !important;
}
[data-testid="stSpinner"] {
  color: var(--text-2) !important;
}
"""

_NAV_GROUPS = """
/* ── Sidebar nav group section labels (rendered via st.markdown) ── */
.nav-group-label {
  font-size: 0.60rem !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.14em !important;
  padding: 14px 14px 4px !important;
  display: block !important;
  pointer-events: none !important;
  opacity: 0.65 !important;
}
"""

# Concat all CSS
ALL_CSS = "\n".join([
    _FONT, _VARS, _RESET, _KEYFRAMES, _SIDEBAR, _METRICS, _BUTTONS,
    _TABS, _FORMS, _INPUTS, _EXPANDERS, _DATAFRAMES, _ALERTS,
    _DIVIDERS, _HEADINGS, _SPINNER, _NAV_GROUPS,
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
    <div style="position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden;">
      <div style="
        position:absolute;width:700px;height:700px;border-radius:50%;
        background:radial-gradient(circle,rgba(124,58,237,0.14) 0%,transparent 70%);
        top:-200px;left:-200px;animation:float 10s ease-in-out infinite;"></div>
      <div style="
        position:absolute;width:550px;height:550px;border-radius:50%;
        background:radial-gradient(circle,rgba(139,92,246,0.11) 0%,transparent 70%);
        bottom:-180px;right:-180px;animation:float 12s ease-in-out infinite reverse;"></div>
      <div style="
        position:absolute;width:400px;height:400px;border-radius:50%;
        background:radial-gradient(circle,rgba(34,211,238,0.08) 0%,transparent 70%);
        top:38%;left:52%;animation:float 14s ease-in-out infinite 3s;"></div>
      <div style="
        position:absolute;width:300px;height:300px;border-radius:50%;
        background:radial-gradient(circle,rgba(124,58,237,0.09) 0%,transparent 70%);
        top:70%;left:10%;animation:float 9s ease-in-out infinite 1.5s;"></div>
    </div>""", unsafe_allow_html=True)


def sidebar_brand() -> str:
    """Brand logo + title block for the sidebar top."""
    return """
<div style="text-align:center;padding:20px 0 12px;">
  <div style="
    font-size:2.8rem;line-height:1;
    filter:drop-shadow(0 0 18px rgba(124,58,237,0.7)) drop-shadow(0 4px 8px rgba(0,0,0,0.4));
    animation:float 5s ease-in-out infinite;
    margin-bottom:10px;">🚦</div>
  <div style="
    font-size:1.05rem;font-weight:900;letter-spacing:-0.01em;
    background:linear-gradient(135deg,#a78bfa,#7c3aed,#22d3ee);
    background-size:200% auto;
    animation:shimmer 4s linear infinite;
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    background-clip:text;">Traffic Intelligence</div>
  <div style="
    font-size:0.68rem;color:rgba(148,163,184,0.55);font-weight:600;margin-top:3px;
    letter-spacing:0.10em;text-transform:uppercase;">Urban Congestion AI · MCP</div>
</div>"""


def nav_group_label(text: str, color: str = "#7c3aed") -> str:
    """Render a navigation section header in the sidebar."""
    return (
        f"<div class='nav-group-label' style='color:{color}'>{text}</div>"
    )


def page_header(icon: str, title: str, subtitle: str = "",
                tag: str = "h1") -> str:
    """Glassmorphism hero header — dark edition."""
    sub_html = (
        f"<p style='margin:6px 0 0;font-size:0.93rem;font-weight:400;"
        f"color:#94a3b8;letter-spacing:0.01em'>{subtitle}</p>"
        if subtitle else ""
    )
    return f"""
<div style="
  background: rgba(15, 22, 45, 0.80);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  border-top: 1px solid rgba(167,139,250,0.18);
  border-radius: 24px;
  padding: 26px 30px;
  margin-bottom: 20px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.45), 0 0 60px rgba(124,58,237,0.10), inset 0 1px 0 rgba(255,255,255,0.06);
  animation: fadeInUp 0.42s cubic-bezier(0.4,0,0.2,1) both;
  display: flex;
  align-items: center;
  gap: 18px;
  position: relative;
  overflow: hidden;
">
  <!-- shimmer strip -->
  <div style="
    position:absolute;inset:0;
    background:linear-gradient(105deg,transparent 35%,rgba(167,139,250,0.08) 50%,transparent 65%);
    background-size:200% 100%;
    animation:shimmer 4s ease-in-out infinite;
    pointer-events:none;border-radius:inherit;"></div>
  <!-- bottom glow line -->
  <div style="
    position:absolute;bottom:0;left:10%;right:10%;height:1px;
    background:linear-gradient(90deg,transparent,rgba(124,58,237,0.5),rgba(34,211,238,0.3),transparent);
    border-radius:0 0 24px 24px;"></div>
  <!-- icon -->
  <div style="
    font-size:2.5rem;line-height:1;
    filter:drop-shadow(0 0 16px rgba(124,58,237,0.6)) drop-shadow(0 4px 8px rgba(0,0,0,0.3));
    animation:float 5s ease-in-out infinite;
    flex-shrink:0;">{icon}</div>
  <!-- text -->
  <div>
    <{tag} style="
      margin:0;
      font-family:'Inter',sans-serif;
      font-weight:900;
      font-size:1.85rem;
      letter-spacing:-0.03em;
      line-height:1.1;
      background:linear-gradient(135deg,#a78bfa 0%,#7c3aed 40%,#22d3ee 100%);
      -webkit-background-clip:text;
      -webkit-text-fill-color:transparent;
      background-clip:text;">{title}</{tag}>
    {sub_html}
  </div>
</div>"""


def metric_row(metrics: list) -> str:
    """Row of dark glassmorphism KPI cards with 3D hover."""
    cards = []
    delays = [0, 0.07, 0.14, 0.21, 0.28]
    for i, m in enumerate(metrics):
        col   = m.get("color", "#a78bfa")
        delay = delays[i] if i < len(delays) else 0
        cards.append(f"""
<div style="
  flex:1;min-width:130px;
  background:rgba(15,22,45,0.82);
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
  border:1px solid rgba(255,255,255,0.07);
  border-top:1px solid rgba(255,255,255,0.10);
  border-radius:20px;
  padding:20px 18px 16px;
  box-shadow:0 8px 32px rgba(0,0,0,0.40),inset 0 1px 0 rgba(255,255,255,0.05);
  transform:perspective(700px) translateZ(2px);
  transition:all 0.30s cubic-bezier(0.4,0,0.2,1);
  animation:cardPop 0.45s cubic-bezier(0.4,0,0.2,1) {delay}s both;
  cursor:default;position:relative;overflow:hidden;"
  onmouseover="this.style.transform='perspective(700px) translateZ(16px) translateY(-6px)';
               this.style.boxShadow='0 24px 60px rgba(0,0,0,0.55),0 0 30px {col}33,inset 0 1px 0 rgba(255,255,255,0.07)';
               this.style.borderColor='rgba(255,255,255,0.13)'"
  onmouseout="this.style.transform='perspective(700px) translateZ(2px)';
              this.style.boxShadow='0 8px 32px rgba(0,0,0,0.40),inset 0 1px 0 rgba(255,255,255,0.05)';
              this.style.borderColor='rgba(255,255,255,0.07)'">
  <!-- top accent bar -->
  <div style="
    position:absolute;top:0;left:0;right:0;height:2.5px;
    background:linear-gradient(90deg,{col},{col}88,transparent);
    border-radius:20px 20px 0 0;"></div>
  <!-- subtle glow background -->
  <div style="
    position:absolute;bottom:-20px;right:-20px;width:80px;height:80px;border-radius:50%;
    background:radial-gradient(circle,{col}18 0%,transparent 70%);
    pointer-events:none;"></div>
  <div style="font-size:1.5rem;margin-bottom:8px;
    filter:drop-shadow(0 0 8px {col}66);">{m['icon']}</div>
  <div style="
    font-size:1.70rem;font-weight:800;
    color:{col};letter-spacing:-0.03em;line-height:1.1;
    font-family:'Inter',sans-serif;
    text-shadow:0 0 20px {col}44;">{m['value']}</div>
  <div style="
    font-size:0.68rem;font-weight:700;
    text-transform:uppercase;letter-spacing:0.10em;
    color:#475569;margin-top:5px;
    font-family:'Inter',sans-serif;">{m['label']}</div>
</div>""")
    inner = "\n".join(cards)
    return f"""
<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px;">
  {inner}
</div>"""


def glass_section(title: str, icon: str = "") -> str:
    """Dark glass section subheader pill."""
    prefix = f"<span style='margin-right:8px;font-size:1.05rem'>{icon}</span>" if icon else ""
    return f"""
<div style="
  background:rgba(15,22,45,0.75);
  backdrop-filter:blur(14px);
  -webkit-backdrop-filter:blur(14px);
  border:1px solid rgba(124,58,237,0.22);
  border-radius:12px;
  padding:10px 16px;
  margin:14px 0 10px;
  display:inline-flex;align-items:center;
  box-shadow:0 4px 16px rgba(0,0,0,0.3),0 0 20px rgba(124,58,237,0.10);
  animation:fadeInLeft 0.32s cubic-bezier(0.4,0,0.2,1) both;">
  {prefix}
  <span style="
    font-family:'Inter',sans-serif;
    font-size:1.0rem;font-weight:700;
    color:#e2e8f0;letter-spacing:-0.01em;">{title}</span>
</div>"""


def glass_badge(text: str, color: str = "#a78bfa") -> str:
    """Small glowing pill badge."""
    return (
        f"<span style='display:inline-block;background:{color}20;color:{color};"
        f"border:1px solid {color}40;border-radius:99px;padding:3px 12px;"
        f"font-size:0.75rem;font-weight:700;letter-spacing:0.04em;"
        f"text-shadow:0 0 10px {color}55;"
        f"font-family:Inter,sans-serif'>{text}</span>"
    )


def congestion_banner(label: str, confidence: float,
                      inference_ms: float, impact: str) -> str:
    """Large dark-glass result banner for the Predict page."""
    col_map = {
        "Low":    ("#4ade80", "rgba(74,222,128,0.12)",  "rgba(74,222,128,0.35)"),
        "Medium": ("#fbbf24", "rgba(251,191,36,0.12)",  "rgba(251,191,36,0.35)"),
        "High":   ("#fb923c", "rgba(251,146,60,0.12)",  "rgba(251,146,60,0.35)"),
        "Severe": ("#f87171", "rgba(248,113,113,0.12)", "rgba(248,113,113,0.35)"),
    }
    emoji_map = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Severe": "🔴"}
    col, bg, glow = col_map.get(label, ("#a78bfa", "rgba(167,139,250,0.12)", "rgba(167,139,250,0.35)"))
    emoji = emoji_map.get(label, "⚪")
    return f"""
<div style="
  background:{bg};
  border:1.5px solid {col}55;
  border-radius:24px;
  padding:32px 24px;
  text-align:center;
  margin-bottom:20px;
  box-shadow:0 12px 50px rgba(0,0,0,0.5),0 0 60px {glow},inset 0 1px 0 rgba(255,255,255,0.06);
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
  animation:cardPop 0.5s cubic-bezier(0.4,0,0.2,1) both;
  position:relative;overflow:hidden;">
  <div style="
    position:absolute;inset:0;
    background:linear-gradient(105deg,transparent 35%,{col}10 50%,transparent 65%);
    background-size:200% 100%;
    animation:shimmer 3s ease-in-out infinite;
    pointer-events:none;border-radius:inherit;"></div>
  <div style="font-size:54px;line-height:1;margin-bottom:12px;
    filter:drop-shadow(0 0 20px {col}) drop-shadow(0 4px 10px rgba(0,0,0,0.4));
    animation:float 4s ease-in-out infinite;">{emoji}</div>
  <div style="font-size:2.1rem;font-weight:900;color:{col};
    font-family:Inter,sans-serif;letter-spacing:-0.03em;
    text-shadow:0 0 30px {col}66;">{label} Congestion</div>
  <div style="margin-top:12px;font-size:0.93rem;color:#94a3b8;">
    Confidence <strong style="color:{col};text-shadow:0 0 10px {col}44">{confidence}%</strong>
    &nbsp;·&nbsp;
    Inference <strong style="color:{col};text-shadow:0 0 10px {col}44">{inference_ms} ms</strong>
  </div>
  <div style="margin-top:8px;font-size:0.88rem;color:#64748b;font-style:italic">
    {impact}</div>
</div>"""
