import base64
import hashlib
import time
from pathlib import Path

import streamlit as st

from cv_generator import generate_pdf
from llm_service import extract_structured_cv, get_next_question, transcribe_audio
from schema import CVSchema

st.set_page_config(page_title="NTT DATA CV Dashboard", layout="wide")

LOGO_CANDIDATES = [
    Path("assets/ntt_data_logo.png"),
    Path("assets/NTT_Logo.png"),
    Path("assets/ntt_logo.png"),
    Path("assets/logo.png"),
]


def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --bg-soft: #f7fbff;
            --panel: rgba(255, 255, 255, 0.82);
            --panel-strong: rgba(255, 255, 255, 0.96);
            --line: rgba(125, 150, 182, 0.13);
            --ink: #0b1324;
            --muted: #4d6078;
            --brand: #0074c8;
            --brand-soft: rgba(0, 116, 200, 0.1);
            --accent: #14c7b0;
            --accent-soft: rgba(20, 199, 176, 0.14);
            --success: #16a34a;
            --shadow: 0 30px 80px rgba(7, 20, 42, 0.09);
        }
        .stApp {
            background:
                radial-gradient(circle at 0% 0%, rgba(0, 116, 200, 0.1), transparent 20%),
                radial-gradient(circle at 100% 0%, rgba(20, 199, 176, 0.08), transparent 18%),
                linear-gradient(180deg, #ffffff 0%, #f7fbff 50%, #f2f8ff 100%);
        }
        header[data-testid="stHeader"] {
            display: none;
        }
        div[data-testid="stToolbar"] {
            display: none;
        }
        div[data-testid="stDecoration"] {
            display: none;
        }
        div[data-testid="stAppViewContainer"] {
            padding-top: 0 !important;
        }
        .stApp::before {
            content: "";
            position: fixed;
            inset: -20% -10% auto auto;
            width: 300px;
            height: 300px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(37, 99, 235, 0.08) 0%, rgba(37, 99, 235, 0) 70%);
            pointer-events: none;
            z-index: 0;
        }
        .stApp::after {
            content: "";
            position: fixed;
            inset: auto auto -14% -10%;
            width: 320px;
            height: 320px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(15, 118, 110, 0.09) 0%, rgba(15, 118, 110, 0) 72%);
            pointer-events: none;
            z-index: 0;
        }
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 2rem;
            max-width: 1380px;
            position: relative;
            z-index: 1;
        }
        .dashboard-card {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 251, 255, 0.92) 55%, rgba(240, 255, 251, 0.84) 100%);
            border: 1px solid var(--line);
            border-radius: 30px;
            padding: 1.45rem 1.5rem;
            box-shadow: 0 16px 36px rgba(7, 20, 42, 0.06);
            margin-bottom: 1rem;
        }
        .topbar-shell {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.95rem 1.4rem;
            margin-bottom: 0.7rem;
            background: linear-gradient(90deg, #0a72c8 0%, #1583d8 58%, #1f96e8 100%);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 24px;
            box-shadow: 0 16px 36px rgba(0, 88, 153, 0.14);
        }
        .topbar-left {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            flex: 0 0 auto;
        }
        .topbar-center {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 0;
            text-align: center;
        }
        .topbar-spacer {
            flex: 0 0 178px;
        }
        .topbar-logo-wrap {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.5rem 0.7rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.96);
            box-shadow: 0 12px 26px rgba(7, 20, 42, 0.12);
        }
        .topbar-logo-wrap .hero-logo {
            width: 178px;
        }
        .topbar-title {
            font-size: 1.18rem;
            font-weight: 800;
            letter-spacing: 0.01em;
            text-align: center;
        }
        .topbar-title .topbar-title-soft {
            color: #ffffff;
        }
        .topbar-title .topbar-title-accent {
            color: #d8f1ff;
        }
        .topbar-subtitle {
            color: rgba(255, 255, 255);
            font-size: 0.9rem;
            margin-top: 0.14rem;
            margin-left: 25px;
            text-align: center;
        }
        .hero-shell {
            position: relative;
            overflow: hidden;
            padding: 2rem 2rem 1.8rem 2rem;
            background:
                radial-gradient(circle at 88% 18%, rgba(17, 185, 164, 0.26), transparent 20%),
                radial-gradient(circle at 12% 78%, rgba(0, 116, 200, 0.18), transparent 24%),
                linear-gradient(135deg, #07142a 0%, #081a38 42%, #0d2750 100%);
        }
        .hero-shell::before {
            content: "";
            position: absolute;
            width: 300px;
            height: 300px;
            top: -110px;
            right: -80px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(37, 99, 235, 0.18) 0%, rgba(37, 99, 235, 0) 72%);
        }
        .hero-shell::after {
            content: "";
            position: absolute;
            inset: 0;
            background-image: linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
            background-size: 30px 30px;
            opacity: 0.26;
            pointer-events: none;
        }
        .hero-content {
            position: relative;
            z-index: 1;
        }
        .hero-logo {
            width: 250px;
            max-width: 100%;
            height: auto;
            display: block;
        }
        .hero-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.42rem 0.78rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #f4fbff;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            margin-bottom: 0.85rem;
        }
        .hero-title {
            max-width: 900px;
            font-size: 3.15rem;
            line-height: 1.04;
            font-weight: 700;
            color: transparent;
            background: linear-gradient(90deg, #ffffff 0%, #cfe8ff 34%, #7edfe0 62%, #ffffff 100%);
            background-size: 220% 100%;
            background-position: 0% 50%;
            -webkit-background-clip: text;
            background-clip: text;
            margin-bottom: 0.9rem;
            letter-spacing: -0.03em;
        }
        .hero-title .hero-title-soft {
            color: #ffffff;
            background: none;
            -webkit-text-fill-color: #ffffff;
        }
        .hero-title .hero-title-tail {
            color: transparent;
            background: linear-gradient(90deg, #b8e3ff 0%, #59c6ff 46%, #1d97e8 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-title .hero-title-accent {
            color: transparent;
            background: linear-gradient(90deg, #b8e3ff 0%, #59c6ff 46%, #1d97e8 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-copy {
            color: rgba(247, 251, 255, 0.94);
            margin-bottom: 1.1rem;
            max-width: 820px;
            font-size: 1.05rem;
            line-height: 1.74;
        }
        .hero-copy .hero-copy-soft {
            color: rgba(255, 255, 255, 0.96);
        }
        .hero-copy .hero-copy-accent {
            color: #8bd4ff;
            font-weight: 600;
        }
        .hero-meta {
            display: flex;
            gap: 0.72rem;
            flex-wrap: wrap;
        }
        .hero-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 0.92rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.09);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #f3f8fe;
            font-size: 0.84rem;
            font-weight: 700;
        }
        .metric-card {
            position: relative;
            overflow: hidden;
            min-height: 128px;
            background: linear-gradient(155deg, rgba(255,255,255,0.98), rgba(240,248,255,0.9)) !important;
        }
        .metric-card::before {
            content: "";
            position: absolute;
            width: 74px;
            height: 74px;
            border-radius: 999px;
            right: -16px;
            top: -16px;
            background: linear-gradient(135deg, rgba(8, 26, 56, 0.22), rgba(13, 39, 80, 0.34));
        }
        .metric-card::after {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, #0074c8, #14c7b0);
        }
        .metric-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.32rem 0.68rem;
            border-radius: 999px;
            background: rgba(0, 116, 200, 0.08);
            color: var(--brand);
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.85rem;
        }
        .metric-value {
            color: var(--ink);
            font-size: 2.12rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.22rem;
        }
        .metric-subtle {
            color: var(--muted);
            font-size: 0.92rem;
        }
        .app-loader-shell {
            min-height: 72vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .app-loader-card {
            width: min(520px, 92vw);
            text-align: center;
            padding: 2rem 2.2rem;
            border-radius: 28px;
            border: 1px solid rgba(125, 150, 182, 0.16);
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.97), rgba(240, 249, 255, 0.9));
            box-shadow: 0 24px 56px rgba(12, 35, 64, 0.1);
        }
        .app-loader-spinner {
            width: 56px;
            height: 56px;
            margin: 0 auto 1rem auto;
            border-radius: 999px;
            border: 4px solid rgba(0, 116, 200, 0.14);
            border-top-color: #0074c8;
            border-right-color: #11b9a4;
            animation: loaderSpin 0.9s linear infinite;
        }
        .app-loader-title {
            color: #0f172a;
            font-size: 1.18rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .app-loader-copy {
            color: #587089;
            font-size: 0.97rem;
            line-height: 1.65;
        }
        .section-title {
            color: var(--ink);
            font-size: 1.22rem;
            font-weight: 800;
            margin-bottom: 0.28rem;
        }
        .section-copy {
            color: var(--muted);
            margin-bottom: 0.4rem;
        }
        .panel-banner {
            margin-bottom: 0.8rem;
        }
        .panel-tag {
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.82rem;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(0, 116, 200, 0.1), rgba(20, 199, 176, 0.1));
            color: #066799;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.55rem;
        }
        .workspace-divider-wrap {
            height: 100%;
            min-height: 72vh;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none;
        }
        .workspace-divider {
            width: 4px;
            height: 96%;
            border-radius: 999px;
            background: linear-gradient(
                180deg,
                rgba(7, 100, 170, 0.2) 0%,
                rgba(7, 100, 170, 0.72) 22%,
                rgba(16, 176, 160, 0.78) 50%,
                rgba(7, 100, 170, 0.72) 78%,
                rgba(7, 100, 170, 0.2) 100%
            );
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.72), 0 0 0 2px rgba(8, 108, 184, 0.16), 0 10px 28px rgba(8, 108, 184, 0.26);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--line) !important;
            border-radius: 24px !important;
            background: linear-gradient(155deg, rgba(255,255,255,0.9), rgba(244,250,255,0.82)) !important;
            box-shadow: var(--shadow) !important;
        }
        div[data-testid="stChatMessage"] {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(240, 248, 255, 0.84));
            border: 1px solid rgba(125, 150, 182, 0.14);
            border-radius: 22px;
            padding: 0.24rem 0.35rem;
            box-shadow: 0 16px 36px rgba(12, 35, 64, 0.05);
            margin-bottom: 0.55rem;
        }
        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
            line-height: 1.65;
        }
        div[data-testid="stForm"] {
            margin-top: 1rem;
            padding: 0.45rem 0.5rem;
            border-radius: 28px;
            border: 1px solid rgba(125, 150, 182, 0.16);
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(239, 248, 255, 0.88));
            box-shadow: 0 12px 28px rgba(12, 35, 64, 0.06);
        }
        div[data-testid="stForm"] div[data-baseweb="input"] > div {
            min-height: 3.25rem;
            border-radius: 20px !important;
            border: 0 !important;
            background: rgba(255, 255, 255, 0.55) !important;
            box-shadow: none !important;
        }
        div[data-testid="stForm"] div[data-baseweb="input"] input {
            font-size: 0.98rem !important;
            padding-left: 0.2rem !important;
        }
        div[data-testid="stForm"] div[data-testid="stAudioInput"] {
            display: flex;
            align-items: stretch;
            height: 100%;
        }
        div[data-testid="stForm"] div[data-testid="stAudioInput"] > div {
            width: 100%;
        }
        div[data-testid="stForm"] div[data-testid="stAudioInput"] audio,
        div[data-testid="stForm"] div[data-testid="stAudioInput"] small,
        div[data-testid="stForm"] div[data-testid="stAudioInput"] p {
            display: none !important;
        }
        div[data-testid="stForm"] div[data-testid="stAudioInput"] button {
            min-height: 3.25rem !important;
            width: 100% !important;
            border-radius: 20px !important;
            border: 0 !important;
            background: linear-gradient(135deg, #0074c8 0%, #11b9a4 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 16px 30px rgba(0, 116, 200, 0.2);
            font-size: 0 !important;
        }
        div[data-testid="stForm"] div[data-testid="stAudioInput"] button svg {
            color: #ffffff !important;
            fill: #ffffff !important;
        }
        div[data-testid="stForm"] div[data-testid="stAudioInput"] button:disabled {
            background: linear-gradient(145deg, #c6d1dd, #b8c5d3) !important;
            color: #f8fbff !important;
            box-shadow: none !important;
        }
        div[data-testid="stForm"] div[data-baseweb="input"] input:disabled {
            color: #7b8798 !important;
            -webkit-text-fill-color: #7b8798 !important;
            cursor: not-allowed !important;
        }
        div[data-testid="stForm"] div[data-baseweb="input"] > div:has(input:disabled) {
            background: linear-gradient(145deg, rgba(236, 241, 247, 0.95), rgba(227, 234, 243, 0.92)) !important;
            border: 1px solid rgba(125, 150, 182, 0.18) !important;
            opacity: 0.82;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
            min-height: 3.25rem;
            border-radius: 20px !important;
            background: linear-gradient(135deg, #0074c8 0%, #11b9a4 100%) !important;
            border: 0 !important;
            color: #ffffff !important;
            box-shadow: 0 16px 30px rgba(0, 116, 200, 0.2);
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-1px);
            box-shadow: 0 20px 34px rgba(0, 116, 200, 0.24);
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"]:nth-of-type(1) button,
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"]:last-of-type button {
            font-size: 0 !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"]:nth-of-type(1) button::before {
            content: "🎤";
            font-size: 1rem;
            font-weight: 700;
            color: #ffffff;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"]:last-of-type button::before {
            content: "->";
            font-size: 1rem;
            font-weight: 700;
            color: #ffffff;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:disabled,
        div[data-testid="stButton"] button:disabled {
            background: linear-gradient(145deg, #c6d1dd, #b8c5d3) !important;
            border: 0 !important;
            color: #f8fbff !important;
            box-shadow: none !important;
            opacity: 0.85;
            cursor: not-allowed !important;
            transform: none !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"]:nth-of-type(1) button::before {
            content: "\\01F3A4";
            font-size: 1.2rem;
            font-weight: 700;
            color: #ffffff;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"]:last-of-type button::before {
            content: "\\2192";
            font-size: 1.2rem;
            font-weight: 700;
            color: #ffffff;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
            width: 3rem !important;
            min-width: 3rem !important;
            min-height: 3rem !important;
            height: 3rem !important;
            padding: 0 !important;
            border-radius: 999px !important;
            border: 1px solid rgba(125, 150, 182, 0.2) !important;
            background: rgba(255, 255, 255, 0.96) !important;
            color: #36506f !important;
            box-shadow: 0 10px 24px rgba(12, 35, 64, 0.08) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 28px rgba(12, 35, 64, 0.12) !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button p {
            font-size: 0 !important;
            line-height: 0 !important;
        }
        div[data-testid="stForm"] [data-testid="column"]:nth-of-type(2) div[data-testid="stFormSubmitButton"] button::before {
            content: "\\01F3A4";
            font-size: 1.05rem;
            font-weight: 700;
            color: #36506f;
        }
        div[data-testid="stForm"] [data-testid="column"]:nth-of-type(3) div[data-testid="stFormSubmitButton"] button {
            border: 0 !important;
            background: linear-gradient(135deg, #0074c8 0%, #11b9a4 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 14px 28px rgba(0, 116, 200, 0.2) !important;
        }
        div[data-testid="stForm"] [data-testid="column"]:nth-of-type(3) div[data-testid="stFormSubmitButton"] button:hover {
            box-shadow: 0 18px 32px rgba(0, 116, 200, 0.24) !important;
        }
        div[data-testid="stForm"] [data-testid="column"]:nth-of-type(3) div[data-testid="stFormSubmitButton"] button::before {
            content: "\\2191";
            font-size: 1.2rem;
            font-weight: 700;
            color: #ffffff;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:disabled::before {
            color: #f8fbff !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button::before {
            content: none !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button p {
            font-size: 1.15rem !important;
            line-height: 1 !important;
            margin: 0 !important;
            font-weight: 700 !important;
            color: inherit !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"]:last-of-type button {
            border: 0 !important;
            background: linear-gradient(135deg, #0074c8 0%, #11b9a4 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 14px 28px rgba(0, 116, 200, 0.2) !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"]:last-of-type button:hover {
            box-shadow: 0 18px 32px rgba(0, 116, 200, 0.24) !important;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            border-radius: 18px !important;
            border-color: rgba(125, 150, 182, 0.2) !important;
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(243, 250, 255, 0.88)) !important;
            box-shadow: none !important;
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {
            color: var(--ink) !important;
        }
        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button {
            border-radius: 16px;
            min-height: 3rem;
            font-weight: 700;
            border: 1px solid rgba(125, 150, 182, 0.18);
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(240, 250, 255, 0.88));
            color: var(--ink);
            box-shadow: 0 14px 28px rgba(12, 35, 64, 0.06);
        }
        div[data-testid="stButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            border-color: rgba(0, 116, 200, 0.22);
            color: var(--ink);
            transform: translateY(-1px);
        }
        div[data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(135deg, #0a72c8 0%, #1f8ad8 100%);
            border: 1px solid #0a72c8;
            color: #ffffff;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background: linear-gradient(135deg, #0862ae 0%, #1778c4 100%);
            border-color: #0862ae;
            color: #ffffff;
        }
        @media (max-width: 900px) {
            .topbar-shell,
            .topbar-left {
                flex-direction: column;
                align-items: flex-start;
            }
            .topbar-shell {
                justify-content: flex-start;
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
            .topbar-center {
                position: static;
                transform: none;
                width: 100%;
                justify-content: flex-start;
                margin-top: 0.6rem;
            }
            .topbar-title {
                text-align: left;
            }
            .topbar-subtitle {
                text-align: left;
            }
            .topbar-spacer {
                display: none;
            }
            .hero-title {
                font-size: 2.35rem;
            }
            .workspace-divider-wrap {
                display: none;
            }
        }
        @keyframes loaderSpin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    # Persist the conversation, preview, file output, and UI flags across Streamlit reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_text" not in st.session_state:
        st.session_state.conversation_text = ""
    if "structured_cv" not in st.session_state:
        st.session_state.structured_cv = None
    if "preview_error" not in st.session_state:
        st.session_state.preview_error = ""
    if "generated_cv_path" not in st.session_state:
        st.session_state.generated_cv_path = ""
    if "generated_cv_name" not in st.session_state:
        st.session_state.generated_cv_name = "cv.pdf"
    if "composer_text" not in st.session_state:
        st.session_state.composer_text = ""
    if "pending_clear_composer" not in st.session_state:
        st.session_state.pending_clear_composer = False
    if "profile_photo_bytes" not in st.session_state:
        st.session_state.profile_photo_bytes = b""
    if "profile_photo_name" not in st.session_state:
        st.session_state.profile_photo_name = ""
    if "photo_offer_made" not in st.session_state:
        st.session_state.photo_offer_made = False
    if "last_audio_fingerprint" not in st.session_state:
        st.session_state.last_audio_fingerprint = ""
    if "latest_transcript" not in st.session_state:
        st.session_state.latest_transcript = ""
    if "pending_transcript_fill" not in st.session_state:
        st.session_state.pending_transcript_fill = ""
    if "show_mic_panel" not in st.session_state:
        st.session_state.show_mic_panel = False
    if "audio_notice" not in st.session_state:
        st.session_state.audio_notice = ""
    if "is_processing_reply" not in st.session_state:
        st.session_state.is_processing_reply = False
    if "pending_user_reply" not in st.session_state:
        st.session_state.pending_user_reply = ""
    if "chat_error" not in st.session_state:
        st.session_state.chat_error = ""
    if "ui_bootstrapped" not in st.session_state:
        st.session_state.ui_bootstrapped = False
    if not st.session_state.messages:
        # Seed the conversation once so the user lands on the first interview question.
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "Hi! I will help you to create your CV in NTT Data Format.\n\nWhat is your full name?",
            }
        )


def build_conversation_text(messages):
    # The extractor only needs the user's answers, not the assistant prompts.
    user_lines = [f"User: {msg['content']}" for msg in messages if msg["role"] == "user"]
    return "\n".join(user_lines)


def sync_preview():
    # Rebuild the structured CV preview from the latest conversation snapshot.
    conversation_text = build_conversation_text(st.session_state.messages)
    st.session_state.conversation_text = conversation_text

    if not conversation_text.strip():
        st.session_state.structured_cv = None
        st.session_state.preview_error = ""
        return

    try:
        extracted = extract_structured_cv(conversation_text)
        st.session_state.structured_cv = CVSchema.model_validate(extracted).model_dump()
        st.session_state.preview_error = ""
    except Exception as exc:
        st.session_state.preview_error = str(exc)


def process_user_reply(user_text):
    # Commit the user's message and store the user text in session state message,
    #  ask the model for the next question, then refresh the preview.
    cleaned = user_text.strip()
    if not cleaned:
        return

    st.session_state.messages.append({"role": "user", "content": cleaned})
    next_question = get_next_question(
        st.session_state.messages,
        has_profile_photo=bool(st.session_state.profile_photo_bytes),
        photo_offer_made=st.session_state.photo_offer_made,
    )
    st.session_state.messages.append({"role": "assistant", "content": next_question})
    if "photo" in next_question.lower():
        st.session_state.photo_offer_made = True
    sync_preview()


def queue_user_reply(user_text):
    # Queue the reply first so the composer can lock while the LLM call happens on the next rerun.
    # stroring the user text in temporary session state to avoid issues with Streamlit's form handling and stale closures.
    cleaned = user_text.strip()
    if not cleaned:
        return

    st.session_state.pending_user_reply = cleaned
    st.session_state.is_processing_reply = True
    st.session_state.chat_error = ""


def generate_cv_file():
    # Validate the latest structured data before exporting the final PDF.
    sync_preview()
    structured = st.session_state.structured_cv or {}
    cv = CVSchema.model_validate(structured)
    safe_name = (cv.name or "candidate_cv").strip().replace(" ", "_")
    payload = cv.model_dump()
    payload["profile_photo_bytes"] = st.session_state.profile_photo_bytes
    output_path = generate_pdf(payload, f"{safe_name}.pdf")
    st.session_state.generated_cv_path = output_path
    st.session_state.generated_cv_name = f"{safe_name}.pdf"


def calculate_completion(cv_data):
    if not cv_data:
        return 0

    checks = [
        bool(cv_data.get("name")),
        bool(cv_data.get("title")),
        bool(cv_data.get("total_it_experience")),
        bool(cv_data.get("summary")),
        bool(cv_data.get("skills")),
        bool(cv_data.get("experience")),
        bool(cv_data.get("education")),
        bool(cv_data.get("achievements")),
    ]
    return int(sum(checks) / len(checks) * 100)


def render_metric_card(label, value):
    st.metric(label, value)


def render_list(items, empty_message):
    if not items:
        st.caption(empty_message)
        return

    for item in items:
        st.write(f"- {item}")


@st.cache_data(show_spinner=False)
def get_brand_logo_markup():
    for logo_path in LOGO_CANDIDATES:
        if logo_path.exists():
            # Inline the local logo as base64 so the hero works without any extra asset hosting.
            suffix = logo_path.suffix.lower().lstrip(".") or "png"
            encoded = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
            return f'<img class="hero-logo" src="data:image/{suffix};base64,{encoded}" alt="NTT DATA logo" />'

    return """
        <svg class="hero-logo" viewBox="0 0 560 120" xmlns="http://www.w3.org/2000/svg" aria-label="NTT DATA logo" role="img">
            <g fill="none" stroke="#0080C9" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="54" cy="60" r="38"/>
                <circle cx="54" cy="24" r="15"/>
                <path d="M26 70c0-18 13-31 30-31 16 0 27 11 27 25 0 16-12 28-29 28-16 0-28-10-28-22"/>
            </g>
            <g fill="#0A6EBD">
                <text x="112" y="78" font-family="Arial Black, Arial, Helvetica, sans-serif" font-size="60" font-weight="900" letter-spacing="-3">NTT</text>
                <text x="250" y="78" font-family="Arial Black, Arial, Helvetica, sans-serif" font-size="60" font-weight="900" letter-spacing="-3">DATA</text>
            </g>
        </svg>
    """


init_state()

if st.session_state.pending_transcript_fill and not st.session_state.is_processing_reply:
    # Fill the chat draft on the next rerun so the transcript appears inside the composer.
    st.session_state.composer_text = st.session_state.pending_transcript_fill
    st.session_state.pending_transcript_fill = ""

if st.session_state.pending_clear_composer and not st.session_state.is_processing_reply:
    st.session_state.composer_text = ""
    st.session_state.pending_clear_composer = False

structured_cv = st.session_state.structured_cv or {}
completion = calculate_completion(structured_cv)
user_responses = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
experience_items = len(structured_cv.get("experience", []))
skills_count = len(structured_cv.get("skills", []))

metric_cols = st.columns(4)
with metric_cols[0]:
    render_metric_card("Profile completion", f"{completion}%")
with metric_cols[1]:
    render_metric_card("User responses", user_responses)
with metric_cols[2]:
    render_metric_card("Skills captured", skills_count)
with metric_cols[3]:
    render_metric_card("Experience items", experience_items)

left_col, right_col = st.columns([1.35, 1], gap="large")

with left_col:
    with st.container(border=True):
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if st.session_state.show_mic_panel:
        with st.container(border=True):
            mic_header_cols = st.columns([0.82, 0.18], gap="small")
            with mic_header_cols[0]:
                st.markdown("**Microphone**")
                st.caption("Click the mic icon to open this panel, record your response, then send the transcript into the chat.")
            with mic_header_cols[1]:
                if st.button("Close Mic", use_container_width=True, disabled=st.session_state.is_processing_reply):
                    st.session_state.show_mic_panel = False
                    st.rerun()

            if hasattr(st, "audio_input"):
                recorded_audio_panel = st.audio_input(
                    "Record a spoken answer",
                    label_visibility="collapsed",
                    disabled=st.session_state.is_processing_reply,
                )
                if recorded_audio_panel is not None:
                    audio_bytes = recorded_audio_panel.getvalue()
                    fingerprint = hashlib.sha256(audio_bytes).hexdigest() if audio_bytes else ""
                    if fingerprint and fingerprint != st.session_state.last_audio_fingerprint:
                        with st.spinner("Transcribing your audio..."):
                            try:
                                transcript = transcribe_audio(audio_bytes, recorded_audio_panel.name or "speech.wav")
                                st.session_state.last_audio_fingerprint = fingerprint
                                if transcript:
                                    st.session_state.latest_transcript = transcript
                                else:
                                    st.session_state.latest_transcript = ""
                                    st.session_state.audio_notice = "No clear speech was detected. Please try recording again."
                                st.rerun()
                            except Exception as exc:
                                st.session_state.latest_transcript = ""
                                st.session_state.audio_notice = ""
                                st.error(f"Speech-to-text failed: {exc}")
            else:
                st.info("This Streamlit version does not support `st.audio_input`, so speech capture is unavailable.")

            if st.session_state.latest_transcript:
                st.text_area(
                    "Latest transcript",
                    value=st.session_state.latest_transcript,
                    height=100,
                    disabled=True,
                )
                if st.button("Use Transcript", use_container_width=True, disabled=st.session_state.is_processing_reply):
                    st.session_state.pending_transcript_fill = st.session_state.latest_transcript
                    st.session_state.latest_transcript = ""
                    st.session_state.show_mic_panel = False
                    st.rerun()

    if st.session_state.audio_notice:
        st.info(st.session_state.audio_notice)
        st.session_state.audio_notice = ""

    with st.form("chat_composer", clear_on_submit=False):
        composer_cols = st.columns([0.82, 0.09, 0.09], gap="small")

        with composer_cols[0]:
            typed_reply = st.text_input(
                "Message",
                key="composer_text",
                label_visibility="collapsed",
                placeholder="Type your answer here",
                disabled=st.session_state.is_processing_reply,
            )

        with composer_cols[1]:
            mic_clicked = st.form_submit_button(
                "\U0001F3A4",
                use_container_width=True,
                disabled=st.session_state.is_processing_reply,
            )

        with composer_cols[2]:
            send_clicked = st.form_submit_button(
                "\u27A4",
                use_container_width=True,
                disabled=st.session_state.is_processing_reply,
            )

    if mic_clicked:
        st.session_state.show_mic_panel = True
        st.rerun()

    if send_clicked and typed_reply.strip():
        queue_user_reply(typed_reply)
        st.session_state.pending_clear_composer = True
        st.session_state.latest_transcript = ""
        st.session_state.show_mic_panel = False
        st.rerun()

with right_col:
    uploaded_photo = st.file_uploader(
        "Upload profile photo",
        type=["png", "jpg", "jpeg"],
        help="Optional: upload a professional headshot to include in the final CV.",
        disabled=st.session_state.is_processing_reply,
    )
    if uploaded_photo is not None:
        st.session_state.profile_photo_bytes = uploaded_photo.getvalue()
        st.session_state.profile_photo_name = uploaded_photo.name or "profile_photo"
        st.session_state.photo_offer_made = True

    if st.session_state.profile_photo_bytes:
        photo_cols = st.columns([0.45, 0.55], gap="small")
        with photo_cols[0]:
            st.image(st.session_state.profile_photo_bytes, caption="Profile photo", use_container_width=True)
        with photo_cols[1]:
            st.caption(st.session_state.profile_photo_name or "Uploaded photo")
            if st.button("Remove Photo", use_container_width=True):
                st.session_state.profile_photo_bytes = b""
                st.session_state.profile_photo_name = ""
                st.rerun()

    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button("Refresh Preview", use_container_width=True):
            sync_preview()
    with action_cols[1]:
        if st.button("Generate CV", type="primary", use_container_width=True):
            try:
                generate_cv_file()
                st.success("CV generated successfully.")
            except Exception as exc:
                st.error(str(exc))

    structured_cv = st.session_state.structured_cv or {}

    if st.session_state.preview_error:
        st.warning(f"Preview refresh issue: {st.session_state.preview_error}")

    with st.container(border=True):
        st.subheader(structured_cv.get("name") or "Candidate name pending")
        st.caption(structured_cv.get("title") or "Current title pending")
        if structured_cv.get("total_it_experience"):
            st.caption(f"Total IT experience: {structured_cv.get('total_it_experience')}")
        if structured_cv.get("objectives"):
            st.write(f"**Career objective:** {structured_cv.get('objectives')}")
        st.write(structured_cv.get("summary") or "Summary will appear here as the conversation grows.")

    preview_cols = st.columns(2)
    with preview_cols[0]:
        with st.container(border=True):
            st.markdown("**Skills**")
            render_list(structured_cv.get("skills", []), "No skills extracted yet.")
        with st.container(border=True):
            st.markdown("**Achievements**")
            render_list(structured_cv.get("achievements", []), "No achievements extracted yet.")
    with preview_cols[1]:
        with st.container(border=True):
            st.markdown("**Education**")
            education_items = structured_cv.get("education", [])
            if education_items:
                for item in education_items:
                    if isinstance(item, dict):
                        values = [str(value) for value in item.values() if value]
                        st.write(f"- {' | '.join(values)}")
                    else:
                        st.write(f"- {item}")
            else:
                st.caption("No education details extracted yet.")
        with st.container(border=True):
            st.markdown("**Certifications**")
            render_list(structured_cv.get("certifications", []), "No certifications extracted yet.")

    with st.container(border=True):
        st.markdown("**Experience**")
        experience = structured_cv.get("experience", [])
        if experience:
            for item in experience:
                role = item.get("role") or "Role pending"
                company = item.get("company") or "Company pending"
                st.write(f"**{role}** at **{company}**")
                dates = " - ".join(filter(None, [item.get("start_date"), item.get("end_date")]))
                if dates:
                    st.caption(dates)
                for responsibility in item.get("responsibilities", item.get("bullets", [])):
                    st.write(f"- {responsibility}")
        else:
            st.caption("No experience entries extracted yet.")

    if st.session_state.generated_cv_path:
        with open(st.session_state.generated_cv_path, "rb") as generated_file:
            st.download_button(
                "Download CV",
                data=generated_file.read(),
                file_name=st.session_state.generated_cv_name,
                mime="application/pdf",
                use_container_width=True,
            )

if st.session_state.chat_error:
    st.error(f"Chat response failed: {st.session_state.chat_error}")

if st.session_state.is_processing_reply and st.session_state.pending_user_reply:
    try:
        # Run the LLM call after the form submit rerun so the chat stays disabled while work is in progress.
        with st.spinner("Assistant is preparing the next question..."):
            process_user_reply(st.session_state.pending_user_reply)
        st.session_state.pending_user_reply = ""
        st.session_state.is_processing_reply = False
        st.rerun()
    except Exception as exc:
        st.session_state.pending_user_reply = ""
        st.session_state.is_processing_reply = False
        st.session_state.chat_error = str(exc)
        st.rerun()
