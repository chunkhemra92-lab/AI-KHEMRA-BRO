import asyncio
import base64
import datetime
import hashlib
import hmac
import json
import re
import random
import secrets
import shutil
import sqlite3
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import edge_tts
import extra_streamlit_components as stx
import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
from google import genai
from google.genai import types
from faster_whisper import WhisperModel

APP_VERSION = "6.7.3"

st.set_page_config(page_title='AI KHEMRA BRO', page_icon='🎬', layout='wide', initial_sidebar_state='collapsed')

st.markdown('''
<style>
:root{
  --bg:#080d15;
  --panel:#111827;
  --panel2:#182438;
  --text:#f8fafc;
  --muted:#9ca3af;
  --cyan:#38bdf8;
  --ocean:#0284c7;
  --ocean2:#22d3ee;
  --pink:#38bdf8;
}
.stApp{background:var(--bg);color:var(--text)}
.block-container{max-width:1180px;padding-top:.55rem;padding-bottom:3rem}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],#MainMenu,footer{display:none!important}

.hero{
  border:2px solid var(--ocean2);border-radius:24px;padding:34px 18px;
  text-align:center;background:linear-gradient(145deg,#17171d,#0b1018);
  box-shadow:0 0 24px rgba(34,211,238,.24);margin:0 0 18px;
}
.hero h1{font-size:44px;margin:0 0 8px;font-weight:900;white-space:nowrap;line-height:1.05}
.hero p{margin:0;color:#23c8ef;font-weight:800;letter-spacing:1.5px}
.section-title{font-size:30px;font-weight:900;margin:22px 0 10px}
.ok{background:#073d31;border:1px solid #10b981;border-radius:14px;padding:13px 15px;margin:10px 0}
.side-ok{background:#073d31;border:1px solid #10b981;border-radius:12px;padding:12px;margin:10px 0}
.stButton>button{
  width:100%;min-height:48px;border:0;border-radius:11px;color:white;
  font-weight:850;font-size:15px;background:linear-gradient(90deg,#0284c7,#22d3ee)
}
.stButton>button:hover,.stDownloadButton>button:hover{
  filter:brightness(1.08);transform:translateY(-1px);border-color:#a5f3fc!important;
}
.stDownloadButton>button{width:100%;min-height:46px;border:0!important;border-radius:11px!important;font-weight:850!important;color:white!important;background:linear-gradient(90deg,#0284c7,#22d3ee)!important;box-shadow:0 6px 18px rgba(2,132,199,.22)!important}
.st-key-generate_srt, .st-key-generate_srt > div, .st-key-generate_srt button{width:100%!important;max-width:100%!important;display:block!important;box-sizing:border-box!important}
div[data-testid="stFileUploader"]{background:#eef2f7;border-radius:12px;padding:8px}
/* Compact main-video upload panel: scoped so music and backup uploads retain their own controls. */
.st-key-main_video_upload_panel [data-testid="stFileUploader"]{
  margin:0!important;padding:0!important;background:transparent!important;max-width:100%!important;overflow:hidden!important;
}
.st-key-main_video_upload_panel [data-testid="stFileUploaderDropzone"]{
  min-height:94px!important;padding:11px 12px!important;border:1.5px dashed #22d3ee!important;
  border-radius:14px!important;background:linear-gradient(145deg,#102238,#0d1728)!important;overflow:hidden!important;
}
.st-key-main_video_upload_panel [data-testid="stFileUploaderDropzone"] *{
  max-width:100%!important;min-width:0!important;overflow-wrap:anywhere!important;word-break:break-word!important;
}
.st-key-main_video_upload_panel [data-testid="stFileUploaderDropzone"] button{
  min-height:36px!important;padding:7px 12px!important;font-size:13px!important;line-height:1.2!important;
  border-radius:9px!important;white-space:normal!important;
}
.st-key-main_video_upload_panel [data-testid="stFileUploaderDropzone"] small,
.st-key-main_video_upload_panel [data-testid="stFileUploaderDropzone"] span{
  font-size:12px!important;line-height:1.35!important;text-align:center!important;
}
.st-key-main_video_upload_panel .upload-note{
  margin:0 0 7px;color:#c9f7ff;font-size:13px;font-weight:800;line-height:1.35;overflow-wrap:anywhere;
}
.st-key-main_video_upload_panel .upload-note strong{color:#67e8f9}

div[data-testid="stTextArea"] textarea{
  background:#182438!important;color:#fff!important;border:1px solid #8290a4!important;
  border-radius:10px!important;font-size:16px!important;line-height:1.65!important;
  font-family:"Noto Sans Khmer","Khmer OS System",Arial,sans-serif!important
}
/* Beautiful mobile tab menu: all 4 tabs stay fully visible. */
div[data-baseweb="tab-list"]{
  gap:8px!important;
  background:#0f1726!important;
  border:1px solid #263349!important;
  border-radius:14px!important;
  padding:7px!important;
  overflow:visible!important;
}
button[data-baseweb="tab"]{
  background:#151f31!important;
  border:1px solid #2b3950!important;
  border-radius:10px!important;
  padding:11px 13px!important;
  min-height:46px!important;
  color:#aeb8c7!important;
  font-weight:800!important;
  justify-content:center!important;
  white-space:normal!important;
  text-align:center!important;
  line-height:1.2!important;
}
button[data-baseweb="tab"][aria-selected="true"]{
  background:linear-gradient(90deg,#0284c7,#22d3ee)!important;
  border-color:#67e8f9!important;
  color:white!important;
  box-shadow:0 5px 16px rgba(2,132,199,.28)!important;
}
.clear-wrap .stButton>button{
  background:linear-gradient(90deg,#0369a1,#22d3ee);color:#ffffff;font-weight:900
}

/* One stable professional menu button: white 3-line icon on black. */
.st-key-api_menu_container{
  position:fixed!important;top:7px!important;left:7px!important;
  z-index:1000000!important;width:44px!important;
}
.st-key-api_menu_container button{
  width:44px!important;height:40px!important;min-height:40px!important;
  padding:0!important;border-radius:11px!important;background:#050505!important;
  border:1px solid #3f3f46!important;box-shadow:0 3px 12px rgba(0,0,0,.45)!important;
  color:#fff!important;font-size:25px!important;font-weight:900!important;
  line-height:1!important;white-space:nowrap!important;overflow:hidden!important;
}
.st-key-api_menu_container button:hover{
  background:#111!important;border-color:#fff!important
}
div[data-baseweb="popover"]{
  z-index:1000001!important;
}
div[data-baseweb="popover"] [data-testid="stVerticalBlock"]{
  min-width:min(88vw,390px);
}

/* Discreet owner trigger. It looks like a decorative UI element. */
.st-key-owner_trigger_container{
  position:fixed!important;top:8px!important;right:8px!important;
  z-index:1000000!important;width:42px!important;
}
.st-key-owner_trigger_container button{
  width:42px!important;height:38px!important;min-height:38px!important;
  padding:0!important;border-radius:12px!important;
  background:rgba(8,13,21,.82)!important;border:1px solid #203247!important;
  color:#38bdf8!important;font-size:19px!important;line-height:1!important;
  box-shadow:0 3px 14px rgba(0,0,0,.38)!important;
}
.st-key-owner_trigger_container button:hover{
  background:#0f172a!important;border-color:#22d3ee!important;
}

@media(max-width:700px){
  .block-container{padding-left:.55rem!important;padding-right:.55rem!important;padding-top:.35rem!important}
  .hero{padding:28px 8px 24px!important;border-radius:18px!important;margin-bottom:14px!important}
  .hero h1{font-size:clamp(28px,9vw,42px)!important;letter-spacing:-1px!important}
  .hero p{font-size:clamp(9px,2.7vw,12px)!important;letter-spacing:.8px!important;line-height:1.35!important}
  .section-title{font-size:26px}
  div[data-baseweb="tab-list"]{
    display:grid!important;
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
    width:100%!important;
    gap:7px!important;
    padding:7px!important;
  }
  button[data-baseweb="tab"]{
    width:100%!important;
    min-width:0!important;
    padding:10px 5px!important;
    min-height:50px!important;
    font-size:12px!important;
  }
  button[data-baseweb="tab"] p{
    white-space:normal!important;
    overflow:visible!important;
    text-overflow:clip!important;
    text-align:center!important;
    line-height:1.25!important;
  }
  .st-key-api_menu_container{top:5px!important;left:5px!important;width:42px!important}
  .st-key-api_menu_container button{
    width:42px!important;height:38px!important;min-height:38px!important
  }
}

/* One locked split control: a single 100% bar divided 50% / 50%. */
html, body, [data-testid="stAppViewContainer"], .stApp{
  overflow-x:hidden!important;
  width:100%!important;
  max-width:100vw!important;
}
.block-container{
  width:100%!important;
  max-width:1180px!important;
  box-sizing:border-box!important;
  overflow-x:hidden!important;
}
.st-key-srt_actions{
  width:100%!important;
  max-width:100%!important;
  overflow:hidden!important;
  margin:8px 0 0!important;
  padding:0!important;
  border-radius:13px!important;
  background:#0ea5e9!important;
  box-sizing:border-box!important;
}
.st-key-srt_actions div[data-testid="stHorizontalBlock"]{
  display:grid!important;
  grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
  column-gap:1px!important;
  row-gap:0!important;
  width:100%!important;
  max-width:100%!important;
  min-width:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
  align-items:stretch!important;
  box-sizing:border-box!important;
}
.st-key-srt_actions div[data-testid="column"],
.st-key-srt_actions div[data-testid="stColumn"]{
  flex:none!important;
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
  box-sizing:border-box!important;
}
.st-key-srt_actions div[data-testid="column"] > div,
.st-key-srt_actions div[data-testid="stColumn"] > div,
.st-key-srt_actions .stButton,
.st-key-srt_actions .stDownloadButton{
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
  height:100%!important;
  margin:0!important;
  padding:0!important;
  box-sizing:border-box!important;
}
.st-key-srt_actions button{
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
  min-height:52px!important;
  height:52px!important;
  margin:0!important;
  padding:5px 3px!important;
  border:0!important;
  border-radius:0!important;
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
  line-height:1.05!important;
  font-size:clamp(10px,3vw,16px)!important;
  box-sizing:border-box!important;
  background:linear-gradient(90deg,#0284c7,#22d3ee)!important;
}
.st-key-srt_actions div[data-testid="column"]:first-child button,
.st-key-srt_actions div[data-testid="stColumn"]:first-child button{
  border-radius:12px 0 0 12px!important;
}
.st-key-srt_actions div[data-testid="column"]:last-child button,
.st-key-srt_actions div[data-testid="stColumn"]:last-child button{
  border-radius:0 12px 12px 0!important;
}
@media(max-width:430px){
  [data-testid="stMainBlockContainer"], .block-container{
    width:100%!important;
    max-width:100%!important;
    min-width:0!important;
    overflow-x:hidden!important;
  }
  .st-key-srt_actions{
    width:100%!important;
    max-width:100%!important;
    min-width:0!important;
  }
  .st-key-srt_actions button{
    height:48px!important;
    min-height:48px!important;
    font-size:11px!important;
    padding:4px 2px!important;
  }
}
@media (orientation:landscape) and (max-height:600px){
  .st-key-srt_actions button{height:46px!important;min-height:46px!important;font-size:12px!important}
}


/* ───────────── Login screen v3.0 — mobile layout matching the approved sample ───────────── */
.st-key-public_login_wrap{
  width:min(100%,760px)!important;
  margin:0 auto!important;
}
.st-key-public_login_wrap [data-testid="stMarkdownContainer"] h3{
  color:#ffc400!important;
  font-size:clamp(28px,7vw,43px)!important;
  font-weight:950!important;
  margin:18px 0 12px!important;
  line-height:1.2!important;
}
.st-key-customer_login_box{
  border:1px solid #1f2937!important;
  border-radius:16px!important;
  padding:18px 20px 16px!important;
  background:rgba(7,12,20,.42)!important;
}
.st-key-customer_login_box label,
.st-key-customer_login_box label p{
  color:#ffb000!important;
  font-weight:850!important;
  font-size:17px!important;
}
.st-key-customer_login_box input{
  min-height:58px!important;
  border-radius:12px!important;
  background:#f3f4f6!important;
  color:#20242e!important;
  border:1px solid #d1d5db!important;
  font-size:18px!important;
}
.st-key-customer_login_box input::placeholder{
  color:#8b8f99!important;
  opacity:1!important;
}
.st-key-customer_login_box [data-testid="stFormSubmitButton"] button{
  min-height:58px!important;
  margin-top:10px!important;
  border-radius:12px!important;
  border:1px solid #ffd84d!important;
  background:linear-gradient(90deg,#ffab00 0%,#ffd600 100%)!important;
  color:#ffffff!important;
  font-weight:950!important;
  font-size:18px!important;
  text-shadow:0 1px 2px rgba(0,0,0,.28)!important;
  box-shadow:0 8px 22px rgba(255,179,0,.20)!important;
}
.st-key-customer_login_box [data-testid="stFormSubmitButton"] button p{
  color:#ffffff!important;
  font-weight:950!important;
}
.social-split{
  width:100%;
  display:grid;
  grid-template-columns:minmax(0,1fr) minmax(0,1fr);
  gap:1px;
  padding:7px;
  margin:12px 0 0;
  border:2px solid #f5b400;
  border-radius:16px;
  overflow:hidden;
  background:#f5b400;
  box-sizing:border-box;
}
.social-split a{
  min-width:0;
  min-height:76px;
  display:flex;
  align-items:center;
  justify-content:center;
  gap:12px;
  color:#fff!important;
  text-decoration:none!important;
  font-size:clamp(16px,4vw,25px);
  font-weight:900;
  line-height:1;
  box-sizing:border-box;
  -webkit-tap-highlight-color:transparent;
}
.social-split a:first-child{
  border-radius:10px 0 0 10px;
  background:linear-gradient(135deg,#1265e8,#2f8df5);
}
.social-split a:last-child{
  border-radius:0 10px 10px 0;
  background:linear-gradient(135deg,#1aaee8,#36c9ef);
}
.social-split a:active{filter:brightness(.92);transform:scale(.995)}
.social-icon{
  width:42px;height:42px;flex:0 0 42px;
  display:inline-flex;align-items:center;justify-content:center;
  border-radius:50%;background:#fff;color:#1877f2;
  font-size:29px;font-weight:950;font-family:Arial,sans-serif;
}
.social-split a:last-child .social-icon{
  color:#229ed9;font-size:24px;transform:rotate(-8deg);
}
.login-help{
  margin:20px 2px 0;
  color:#a7adb7;
  font-size:clamp(15px,3.8vw,20px);
  line-height:1.65;
}
.login-help strong{color:#ffc400}
@media(max-width:700px){
  .st-key-public_login_wrap{width:100%!important}
  .st-key-customer_login_box{padding:16px 14px 14px!important}
  .social-split{padding:5px;border-radius:14px}
  .social-split a{min-height:64px;gap:8px}
  .social-icon{width:37px;height:37px;flex-basis:37px;font-size:25px}
}
	
/* ───────────── Universal mobile resilience patch ───────────── */
/* This layer protects 320 px–wide phones, modern notched devices, and
   landscape keyboards without changing the desktop workspace. */
*, *::before, *::after{box-sizing:border-box}
html{
  width:100%;max-width:100%;overflow-x:hidden;
  -webkit-text-size-adjust:100%;text-size-adjust:100%;
  -webkit-tap-highlight-color:transparent;
}
body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp{
  width:100%;max-width:100%;min-width:0;overflow-x:hidden;
}
[data-testid="stMainBlockContainer"], .block-container{
  min-width:0;max-width:100%;
  padding-bottom:max(2.5rem, env(safe-area-inset-bottom));
}
button, input, textarea, select{font:inherit}
button, a, [role="button"]{touch-action:manipulation}
[data-testid="stAudio"] audio,
[data-testid="stVideo"] video,
[data-testid="stFileUploader"],
[data-testid="stFileUploaderDropzone"],
[data-testid="stTextArea"],
[data-testid="stTextInput"],
[data-testid="stSelectbox"],
[data-testid="stDownloadButton"],
.stButton{width:100%;max-width:100%;min-width:0}
[data-testid="stAudio"] audio,
[data-testid="stVideo"] video{display:block;max-width:100%;height:auto}

@media (max-width:700px){
  /* Keep content clear of the fixed menu controls and the phone safe areas. */
  [data-testid="stMainBlockContainer"], .block-container{
    padding-top:max(.45rem, env(safe-area-inset-top))!important;
    padding-right:max(.7rem, env(safe-area-inset-right))!important;
    padding-bottom:max(2.8rem, env(safe-area-inset-bottom))!important;
    padding-left:max(.7rem, env(safe-area-inset-left))!important;
  }
  .hero{
    margin-top:44px!important;
    padding:22px 10px 20px!important;
    border-radius:16px!important;
  }
  .hero h1{
    white-space:normal!important;
    overflow-wrap:anywhere!important;
    font-size:clamp(25px,8.5vw,38px)!important;
    line-height:1.12!important;
  }
  .hero p{overflow-wrap:anywhere!important;word-break:normal!important}
  .section-title{
    font-size:clamp(21px,6.5vw,27px)!important;
    line-height:1.25!important;
    overflow-wrap:anywhere!important;
  }
  h1{font-size:clamp(25px,8vw,34px)!important;line-height:1.2!important}
  h2{font-size:clamp(21px,6.5vw,28px)!important;line-height:1.25!important}
  h3{font-size:clamp(18px,5.5vw,23px)!important;line-height:1.3!important}
  p, li, [data-testid="stMarkdownContainer"]{overflow-wrap:anywhere}

  /* Large, native-feeling controls prevent iOS browser zoom and missed taps. */
  .stButton > button, .stDownloadButton > button,
  [data-testid="stFormSubmitButton"] > button{
    width:100%!important;min-height:48px!important;
    padding:11px 12px!important;font-size:16px!important;
    line-height:1.25!important;white-space:normal!important;
    overflow-wrap:anywhere!important;
  }
  div[data-testid="stTextArea"] textarea,
  div[data-testid="stTextInput"] input,
  div[data-baseweb="base-input"] input,
  div[data-baseweb="select"] > div{
    font-size:16px!important; /* prevents automatic iOS zoom on focus */
    min-height:48px!important;max-width:100%!important;
  }
  div[data-testid="stTextArea"] textarea{
    min-height:150px!important;line-height:1.6!important;
  }
  [data-testid="stFileUploaderDropzone"]{
    min-height:142px!important;padding:14px 10px!important;
  }
  [data-testid="stFileUploaderDropzone"] button{
    min-height:44px!important;font-size:15px!important;
  }

  /* Four workflow tabs remain visible without horizontal clipping. */
  div[data-baseweb="tab-list"]{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
    gap:6px!important;padding:6px!important;
    max-width:100%!important;
  }
  button[data-baseweb="tab"]{
    width:100%!important;min-width:0!important;min-height:54px!important;
    padding:8px 4px!important;font-size:12px!important;
  }
  button[data-baseweb="tab"] p,
  button[data-baseweb="tab"] div{
    min-width:0!important;white-space:normal!important;
    overflow-wrap:anywhere!important;word-break:normal!important;
    text-align:center!important;
  }
  [data-baseweb="tab-highlight"]{display:none!important}

  /* Popover settings never exceed the visible width of a handset. */
  div[data-baseweb="popover"]{
    max-width:calc(100vw - 14px)!important;
  }
  div[data-baseweb="popover"] [data-testid="stVerticalBlock"]{
    width:min(92vw,390px)!important;min-width:0!important;max-width:92vw!important;
  }
  .st-key-api_menu_container{left:max(5px, env(safe-area-inset-left))!important}
  .st-key-owner_trigger_container{right:max(5px, env(safe-area-inset-right))!important}

  /* Wide utility components scroll inside themselves instead of moving the page. */
  [data-testid="stDataFrame"], [data-testid="stTable"],
  [data-testid="stCodeBlock"], [data-testid="stJson"]{
    max-width:100%!important;overflow-x:auto!important;
    -webkit-overflow-scrolling:touch;
  }
}

@media (max-width:380px){
  [data-testid="stMainBlockContainer"], .block-container{
    padding-right:.5rem!important;padding-left:.5rem!important;
  }
  .hero{margin-top:42px!important;padding:18px 7px!important}
  .hero h1{font-size:clamp(23px,8vw,30px)!important}
  .hero p{font-size:10px!important;letter-spacing:.45px!important}
  .section-title{font-size:21px!important}
  div[data-baseweb="tab-list"]{gap:5px!important;padding:5px!important}
  button[data-baseweb="tab"]{min-height:52px!important;font-size:11px!important}
  .stButton > button, .stDownloadButton > button{font-size:15px!important}
}

/* Calm progress card: status stays readable without jumping percentage/time text. */
.khemra-wait-card{
  display:flex;align-items:center;gap:12px;margin:12px 0 7px;padding:14px 16px;
  border:1px solid rgba(34,211,238,.34);border-radius:16px;
  background:linear-gradient(135deg,rgba(8,132,199,.16),rgba(17,24,39,.88));
  box-shadow:0 8px 22px rgba(0,0,0,.16);
}
.khemra-wait-orb{
  width:11px;height:11px;flex:none;border-radius:50%;background:#22d3ee;
  box-shadow:0 0 0 0 rgba(34,211,238,.6);animation:khemraPulse 1.7s ease-out infinite;
}
.khemra-wait-title{font-size:16px;font-weight:850;color:#f8fafc;line-height:1.3}
.khemra-wait-copy{margin-top:2px;font-size:13px;color:#b7c7d9;line-height:1.45}
@keyframes khemraPulse{0%{box-shadow:0 0 0 0 rgba(34,211,238,.55)}70%{box-shadow:0 0 0 10px rgba(34,211,238,0)}100%{box-shadow:0 0 0 0 rgba(34,211,238,0)}}
@media (max-width:768px){
  .khemra-wait-card{padding:12px 13px;border-radius:14px}
  .khemra-wait-title{font-size:15px}.khemra-wait-copy{font-size:12px}
}

/* Action identity: translation uses a calm brain pulse; voice controls remain simple. */
.st-key-translate_btn button,.st-key-analyze_thoughts button{
  background:linear-gradient(100deg,#7c3aed,#a855f7,#6366f1)!important;
  box-shadow:0 8px 20px rgba(139,92,246,.28)!important;
}
.st-key-generate_audio button,.st-key-srt_to_speech_btn button,.st-key-plain_voice_btn button{
  background:linear-gradient(100deg,#0369a1,#0891b2,#22d3ee)!important;
}
.st-key-translate_btn button::before{content:'🧠';display:inline-block;margin-right:8px;animation:brainPulse 1.9s ease-in-out infinite;transform-origin:50% 60%}
.brain-pulse{display:inline-block;animation:brainPulse 1.9s ease-in-out infinite;transform-origin:50% 60%}
@keyframes brainPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.16) rotate(-4deg)}}

@media (orientation:landscape) and (max-height:600px) and (max-width:950px){
  [data-testid="stMainBlockContainer"], .block-container{
    padding-top:.35rem!important;padding-bottom:1.2rem!important;
  }
  .hero{margin-top:40px!important;padding:14px 10px!important}
  .hero h1{font-size:26px!important}
  .hero p{font-size:10px!important}
  button[data-baseweb="tab"]{min-height:44px!important}
  .stButton > button, .stDownloadButton > button{min-height:44px!important}
}
</style>
''', unsafe_allow_html=True)

PISITH='km-KH-PisethNeural'
SREYMOM='km-KH-SreymomNeural'
VOICE_PROFILES={
# Warm, natural profiles. Large pitch boosts make Khmer Neural voices thin/airy,
# so age differences use mostly rate and only a very small pitch movement.
'BOY':{'voice':PISITH,'rate':'+4%','pitch':'+2Hz','volume':'+5%'},
'GIRL':{'voice':SREYMOM,'rate':'+4%','pitch':'+3Hz','volume':'+5%'},
'M_YOUNG':{'voice':PISITH,'rate':'+1%','pitch':'+0Hz','volume':'+6%'},
'F_YOUNG':{'voice':SREYMOM,'rate':'+1%','pitch':'+1Hz','volume':'+6%'},
'M_ADULT':{'voice':PISITH,'rate':'-3%','pitch':'-3Hz','volume':'+7%'},
'F_ADULT':{'voice':SREYMOM,'rate':'-2%','pitch':'-1Hz','volume':'+7%'},
'M_OLD':{'voice':PISITH,'rate':'-11%','pitch':'-8Hz','volume':'+8%'},
'F_OLD':{'voice':SREYMOM,'rate':'-10%','pitch':'-6Hz','volume':'+8%'},
# Thought voices stay close to normal speech level, but use a gentler pace and
# warmer tone.  This keeps them intimate and attractive without becoming weak,
# hollow, whispery, or artificially echoing.
'M_THINK':{'voice':PISITH,'rate':'-2%','pitch':'+0Hz','volume':'+0%'},
'F_THINK':{'voice':SREYMOM,'rate':'-2%','pitch':'+1Hz','volume':'+0%'},
'NARRATOR_M':{'voice':PISITH,'rate':'-7%','pitch':'-6Hz','volume':'+8%'},
'NARRATOR_F':{'voice':SREYMOM,'rate':'-6%','pitch':'-4Hz','volume':'+8%'},
# Backward-compatible labels for older SRT files.
'M':{'voice':PISITH,'rate':'+0%','pitch':'+0Hz','volume':'+0%'},
'F':{'voice':SREYMOM,'rate':'+0%','pitch':'+0Hz','volume':'+0%'},
'OLD_M':{'voice':PISITH,'rate':'-8%','pitch':'-5Hz','volume':'+8%'},
'OLD_F':{'voice':SREYMOM,'rate':'-8%','pitch':'-3Hz','volume':'+8%'}
}

# Natural-dubbing controls. Very long fades and forced gaps make every short
# subtitle audibly dip. Keep only click protection and leave normal breathing
# space to the original timestamps.
VOICE_FADE_IN_SECONDS = 0.010
VOICE_FADE_OUT_SECONDS = 0.018
MIN_VOICE_GAP_MS = 0
# Consecutive subtitle fragments from the same speaker are synthesized as one
# phrase when the visible gap is tiny, preventing the voice from restarting its
# intonation at every subtitle boundary.
CONTINUATION_GAP_MS = 260
# Thought voices remain clearly audible at 60% of the matching ordinary voice
# (a 40% reduction). This is applied once per thought cue and retained after
# mastering for a thought-only clip.
THOUGHT_VOICE_GAIN = 0.60
# Do not accelerate Khmer Neural speech. Natural pacing is more important than
# forcing a long sentence into a short subtitle timestamp.
MAX_TEMPO_SPEED = 1.00
# A very slow, low-range leveler aligns whole phrases without pumping individual
# syllables or flattening a character's intended emotion.
FINAL_LEVELER_FILTER = 'dynaudnorm=f=1600:g=3:p=0.96:m=1.12:n=1:c=1:b=1:o=0.92'

# Optional background-music ducking. These defaults favor smooth dialogue over
# aggressive pumping, and can be adjusted per audio job in the mobile UI.
DUCKING_DEFAULTS = {
    'enabled': True,
    'music_gain': 0.42,
    'threshold': 0.050,
    'ratio': 8.0,
    'attack_ms': 40,
    'release_ms': 700,
    'knee': 4.0,
    'music_fade_in_seconds': 0.70,
    'music_fade_out_seconds': 1.20,
}
BACKGROUND_MUSIC_MAX_MB = 30
VIDEO_MAX_MB = 100
VIDEO_MAX_DURATION_SECONDS = 10 * 60

# The four canonical tags requested for Khmer dubbing output.
CANONICAL_SRT_TAGS = ("M", "F", "M_THINK", "F_THINK")
TAG_ALIASES = {
    "M": "M", "M_ADULT": "M", "M_YOUNG": "M", "M_OLD": "M", "BOY": "M", "OLD_M": "M", "NARRATOR_M": "M",
    "F": "F", "F_ADULT": "F", "F_YOUNG": "F", "F_OLD": "F", "GIRL": "F", "OLD_F": "F", "NARRATOR_F": "F",
    "M_THINK": "M_THINK", "F_THINK": "F_THINK",
}
NON_KHMER_SCRIPT_RE = re.compile(
    r"[A-Za-z\u00C0-\u024F\u0E00-\u0E7F\u3040-\u30FF\u3100-\u312F\u3130-\uD7AF"
    r"\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]"
)

# Production Gemini text/multimodal models. Labels are only for the mobile UI;
# the exact API identifier is always sent to the Gemini SDK.
GEMINI_MODEL_OPTIONS = (
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
)
# Fast Mode reduces network round trips by grouping more short subtitle cues per
# Gemini request. Standard Mode remains more conservative for unusually dense SRTs.
FAST_TRANSLATION_BATCH_SIZE = 60
STANDARD_TRANSLATION_BATCH_SIZE = 50

GEMINI_MODEL_LABELS = {
    "gemini-3.7-flash": "🔥 gemini-3.7-flash — Best quality",
    "gemini-3.6-flash": "⚡ gemini-3.6-flash — Fast and balanced",
    "gemini-3.5-flash": "🚀 gemini-3.5-flash — Standard",
    "gemini-3.5-flash-lite": "💡 gemini-3.5-flash-lite — Efficient and fast",
    "gemini-3.1-flash-lite": "✨ gemini-3.1-flash-lite — Very fast",
    "gemini-3.1-pro-preview": "🧠 gemini-3.1-pro-preview — Deep review",
}
TARGET_LANGUAGE_OPTIONS = (
    "Khmer (ខ្មែរ)", "English", "Chinese (中文)", "Korean (한국어)", "Vietnamese (Tiếng Việt)",
)
# Each selectable target has a matching male/female Edge voice.  This keeps the
# generated SRT and its MP3 in the same language rather than sending non-Khmer
# text to a Khmer-only voice.
TARGET_LANGUAGE_SETTINGS = {
    "Khmer (ខ្មែរ)": {"name": "Khmer", "sample": "ខ្មែរ", "male_voice": PISITH, "female_voice": SREYMOM, "khmer_only": True},
    "English": {"name": "English", "sample": "English", "male_voice": "en-US-GuyNeural", "female_voice": "en-US-JennyNeural", "khmer_only": False},
    "Chinese (中文)": {"name": "Simplified Chinese", "sample": "中文", "male_voice": "zh-CN-YunxiNeural", "female_voice": "zh-CN-XiaoxiaoNeural", "khmer_only": False},
    "Korean (한국어)": {"name": "Korean", "sample": "한국어", "male_voice": "ko-KR-InJoonNeural", "female_voice": "ko-KR-SunHiNeural", "khmer_only": False},
    "Vietnamese (Tiếng Việt)": {"name": "Vietnamese", "sample": "Tiếng Việt", "male_voice": "vi-VN-NamMinhNeural", "female_voice": "vi-VN-HoaiMyNeural", "khmer_only": False},
}
TRANSLATION_STYLE_OPTIONS = (
    "👤 បកប្រែធម្មតា (Standard)",
    "⚡ ស៊ីចង្វាក់មាត់ (Lipsync)",
    "🤣 បែបកំប្លែង (Comedy)",
    "👔 ផ្លូវការ (Formal)",
)
TRANSLATION_STYLE_GUIDANCE = {
    "👤 បកប្រែធម្មតា (Standard)": "Use balanced, natural Cambodian movie dialogue. Preserve the source emotion and speakability.",
    "⚡ ស៊ីចង្វាក់មាត់ (Lipsync)": "Prioritize short, speakable Khmer phrasing that fits the visible timing and likely mouth movement. Preserve meaning; never omit a key reaction, negation, name, or number.",
    "🤣 បែបកំប្លែង (Comedy)": "Preserve humor, playful timing, teasing, and wordplay with natural Khmer comedy. Do not invent jokes or vulgarity absent from the source.",
    "👔 ផ្លូវការ (Formal)": "Use respectful, polished Khmer suitable for formal scenes, officials, elders, news, and ceremonial speech. Keep dialogue natural, not stiff.",
}

# Keep historical stored option values stable while rendering every setting in English.
TARGET_LANGUAGE_LABELS = {
    "Khmer (ខ្មែរ)": "Khmer",
    "English": "English",
    "Chinese (中文)": "Chinese (Simplified)",
    "Korean (한국어)": "Korean",
    "Vietnamese (Tiếng Việt)": "Vietnamese",
}
TRANSLATION_STYLE_LABELS = {
    "👤 បកប្រែធម្មតា (Standard)": "👤 Standard",
    "⚡ ស៊ីចង្វាក់មាត់ (Lipsync)": "⚡ Lipsync",
    "🤣 បែបកំប្លែង (Comedy)": "🤣 Comedy",
    "👔 ផ្លូវការ (Formal)": "👔 Formal",
}
SOURCE_LANGUAGE_LABELS = {
    "Auto-detect (ចិន/កូរ៉េ/វៀតណាម/អង់គ្លេស)": "Auto-detect (Chinese, Korean, Vietnamese, English)",
    "Chinese (中文)": "Chinese (Simplified)",
    "Korean (한국어)": "Korean",
    "Vietnamese (Tiếng Việt)": "Vietnamese",
    "English": "English",
}
WORKFLOW_MODE_LABELS = {
    "⚡ Khmer SRT ស្វ័យប្រវត្តិ": "⚡ Automatic Khmer SRT",
    "🎙️ Khmer SRT + MP3 តែម្តង": "🎙️ Khmer SRT + MP3",
    "📝 Source SRT only": "📝 Source SRT only",
}
PROCESSING_MODE_LABELS = {
    "⚡ លឿន (ណែនាំ)": "⚡ Fast (Recommended)",
    "🎚️ សំឡេងច្បាស់ (យឺតជាង)": "🎚️ Higher accuracy (Slower)",
}


def normalize_voice_tag(tag):
    """Return one of the four approved Khmer dubbing tags."""
    return TAG_ALIASES.get(str(tag or "M").upper().strip(), "M")


def contains_non_khmer_script(text):
    """Reject Chinese, Korean, Thai, Vietnamese/English Latin text in Khmer output."""
    return bool(NON_KHMER_SCRIPT_RE.search(str(text or "")))


def normalized_target_language(target_language):
    """Return a supported target language, safely migrating old saved settings."""
    value = str(target_language or "")
    return value if value in TARGET_LANGUAGE_SETTINGS else "Khmer (ខ្មែរ)"


def target_language_settings(target_language):
    return TARGET_LANGUAGE_SETTINGS[normalized_target_language(target_language)]


def is_valid_target_dialogue(text, target_language):
    """Keep strict Khmer-script protection while accepting valid multilingual output."""
    dialogue = str(text or "").strip()
    if not dialogue:
        return False
    settings = target_language_settings(target_language)
    return not settings["khmer_only"] or not contains_non_khmer_script(dialogue)


def voice_profile_for_target_language(tag, target_language):
    """Use the selected language's matching male/female voice with the role's gentle tuning."""
    canonical_tag = normalize_voice_tag(tag)
    profile = dict(VOICE_PROFILES.get(canonical_tag, VOICE_PROFILES["M"]))
    settings = target_language_settings(target_language)
    profile["voice"] = settings["female_voice"] if canonical_tag.startswith("F") else settings["male_voice"]
    return profile


def target_language_prompt_rules(target_language):
    """Return Khmer-specific rules by default and concise equivalent rules for other targets."""
    selected = normalized_target_language(target_language)
    if selected == "Khmer (ខ្មែរ)":
        return KHMER_DUBBING_RULES
    language_name = target_language_settings(selected)["name"]
    return f"""
ROLE: You are an Expert Subtitler & Dubbing Translator. Translate the dialogue into natural spoken {language_name} only, never word-for-word or bookishly.

RULE 1 — NATURAL SPOKEN LANGUAGE: Use authentic everyday {language_name} dialogue and natural emotional delivery appropriate to the scene.
RULE 2 — MATCH THE ACTOR: Keep pronouns, forms of address, age, rank, relationship, and speaker identity consistent.
RULE 3 — EMOTIONAL DEPTH: Preserve anger, humour, grief, romance, sarcasm, fear, idioms, and implied meaning naturally.
RULE 4 — SUBTITLE TIMING: Preserve every ID and timestamp. Keep each cue short, clear, natural to speak, and within its available timing without deleting meaning.
RULE 5 — AUDIO TAGS: Output exactly one tag for every cue: [M], [F], [M_THINK], or [F_THINK]. Use THINK only for an unheard internal thought; it must be intimate, never hollow, reverberant, or echoing.
RULE 6 — {language_name.upper()}-ONLY AND SAFE OUTPUT: The dialogue text must use {language_name} only, without source-language leftovers, notes, or brackets. Keep it suitable for a general audience while preserving the scene's emotion and meaning. Return one JSON object for every supplied ID in the same order.
""".strip()


KHMER_DUBBING_RULES = """
ROLE: You are an Expert Subtitler & Dubbing Translator. Translate Chinese, Korean,
Vietnamese, or English dialogue into standard Cambodian Khmer only. The final Khmer
must sound like real spoken movie dialogue, not a literal or book-style translation.

RULE 1 — NATURAL SPOKEN KHMER: Never translate word-for-word. Use natural daily
Cambodian speech and use emotional particles such as ណា, ណ៎, ហ្មង, តើ, អញ្ចឹង,
វើយ, ហាស, ចា៎, ចុះ only where the scene genuinely calls for them.

RULE 2 — MATCH THE ACTOR: Match pronouns and forms of address to age, rank,
relationship, and context. Use forms such as បង/អូន, ឯង/អញ, ខ្ញុំ/លោក,
ពួកម៉ាក, and សម្លាញ់ only when appropriate. Keep each character consistent.

RULE 3 — EMOTIONAL DEPTH: Preserve anger, humour, grief, romance, sarcasm, fear,
and wordplay. Rewrite naturally in Khmer so the same intended emotion is heard.

RULE 4 — SUBTITLE TIMING: Preserve every ID and timestamp exactly. Keep each line
short, clear, and speakable in its allotted time; shorten through natural Khmer
rewriting, never by deleting meaning, names, negation, numbers, reactions, or replies.
Write one comfortable spoken idea per cue, with ordinary punctuation only where a
real speaker pauses. When the same actor continues across close subtitle cues, write
the later cue as a natural continuation; do not end every screen-only fragment with
Khmer full stop. Use one ellipsis (…) only for a meaningful hesitation or held
thought, never repeatedly or as artificial padding. Do not make the Khmer voice rush,
drag, flatten its tone, or jump between artificial highs and lows.

RULE 5 — AUDIO TAGS: Output exactly one tag for every cue. Only [M] for male dialogue,
[F] for female dialogue, [M_THINK] for male internal thought, and [F_THINK] for female
internal thought are allowed. Do not use any other tag. Use THINK only when it is truly an
unheard internal monologue or thought voice, never just because an actor speaks quietly. A
THINK line must be soft and intimate, but not whispered, hollow, reverberant, or echoing.

RULE 6 — KHMER-ONLY AND FACEBOOK-SAFE OUTPUT: The text field must contain Khmer script only.
Never leave Chinese, Korean, Thai, Vietnamese, English, romanization, translator notes,
or brackets inside the dialogue. Keep all dialogue suitable for a general Facebook audience:
preserve anger, threat, mockery, and emotion, but naturally replace profanity, sexual insults,
hateful language, degrading slurs, and unnecessarily graphic wording with clean spoken Khmer.
Never invent an insult not present in the source. Return one JSON object for every supplied ID
in the same order.
""".strip()


SIX_RULE_TRANSLATION_BRAIN = """MANDATORY SIX-RULE TRANSLATION BRAIN — perform this silent quality check for EVERY cue before returning JSON.

1. NATURAL SPOKEN LANGUAGE: Reject word-for-word, book-like, or robotic phrasing. Write the way a real person would naturally speak in the target language.
2. ACTOR VOICE AND RELATIONSHIP: Check pronouns, rank, age, relationship, respect, and character continuity against nearby cues. Do not randomly change how characters address each other.
3. EMOTIONAL DEPTH: Preserve the original emotional purpose—anger, comedy, fear, grief, warmth, mockery, romance, urgency, or surprise—without inventing new plot facts.
4. SUBTITLE CLARITY AND TIMING: Keep the supplied ID and timestamp locked. Make one concise, complete, speakable idea that fits MAX_WORDS; never remove a name, negation, number, command, reply, or audible reaction merely to shorten it.
5. AUDIO TAG: Return exactly one canonical tag for every cue: M, F, M_THINK, or F_THINK. Use M/F for audible dialogue. Use THINK only when characters cannot hear the line because it is a genuine internal thought. Never use an invalid tag or leave the tag blank.
6. TARGET-LANGUAGE-ONLY OUTPUT: Return only the selected target language in text, with no source-language characters, explanations, brackets, or translator notes. Keep wording broadly suitable for general audiences.

If any rule fails, rewrite the cue silently before returning it. Return JSON only; never explain your decisions.
""".strip()


SPEAKER_TAG_PROMPT = """You are an audiovisual speaker-tagging editor for film subtitles.
The video and fixed-timestamp transcript cues are supplied. Identify the person who is ACTUALLY speaking at each timestamp from audible voice, lip movement, scene context, and continuity across nearby cues.

Return JSON only. Return one object for every supplied ID, in the same order:
[{"id": 1, "tag": "M"}]

Only these exact tags are allowed:
- M: male dialogue spoken aloud.
- F: female dialogue spoken aloud.
- M_THINK: male inner thought that other characters cannot hear.
- F_THINK: female inner thought that other characters cannot hear.

Rules:
- Never tag every cue M by default. Decide M or F from the real active speaker whenever the video/audio provides evidence.
- Use THINK only for clear internal monologue, voice-over thought, or an unheard thought. A quiet, distant, crying, muffled, or off-screen spoken line is still ordinary M or F dialogue.
- Keep the same speaking character on a consistent M or F tag across adjacent cues until the real speaker changes.
- Do not tag the character merely visible on screen if another person is speaking off-camera.
- Do not translate, shorten, rewrite, or return dialogue text. Return only id and tag for every cue.
- Never change cue ID, cue order, start time, or end time.
""".strip()


def translation_style_guidance(translation_style, target_language="Khmer (ខ្មែរ)"):
    """Return a safe style instruction that matches the selected output language."""
    guidance = TRANSLATION_STYLE_GUIDANCE.get(
        str(translation_style or ""),
        TRANSLATION_STYLE_GUIDANCE["👤 បកប្រែធម្មតា (Standard)"],
    )
    if normalized_target_language(target_language) == "Khmer (ខ្មែរ)":
        return guidance
    return guidance.replace("Cambodian movie dialogue", "target-language movie dialogue").replace("Khmer phrasing", "target-language phrasing").replace("Khmer comedy", "target-language comedy")


def build_multilingual_translation_prompt(cue_lines, source_language="Auto-detect", previous_context="", translation_style="👤 បកប្រែធម្មតា (Standard)", target_language="Khmer (ខ្មែរ)"):
    selected_target = normalized_target_language(target_language)
    settings = target_language_settings(selected_target)
    return f"""
{target_language_prompt_rules(selected_target)}

{SIX_RULE_TRANSLATION_BRAIN}

SOURCE LANGUAGE: {source_language}. If Auto-detect is selected, identify the source
language from each SOURCE line before translating.

TARGET LANGUAGE: {settings['name']} ({selected_target})
SELECTED TRANSLATION STYLE: {translation_style}
STYLE INSTRUCTION: {translation_style_guidance(translation_style, selected_target)}

RECENT CONTINUITY CONTEXT:
{previous_context or '(none)'}

Return JSON only, with this exact schema:
[{{"id": 1, "tag": "M", "text": "{settings['sample']}"}}]

CUES:
{cue_lines}
""".strip()


TRANSLATE_PROMPT = """You are an expert Khmer movie subtitler, Chinese-drama translator, dubbing script writer, and character-continuity editor.
The supplied cue IDs and Whisper timestamps are authoritative and MUST NOT be changed.
Use the uploaded video to identify the actual speaker, voice source, age, gender, social rank, relationship, narration, and inner thought.

Return a JSON array only. Each object must contain exactly:
{"id": integer, "tag": string, "text": string}

Allowed tags:
BOY, GIRL, M_YOUNG, F_YOUNG, M_ADULT, F_ADULT, M_OLD, F_OLD, M_THINK, F_THINK, NARRATOR_M, NARRATOR_F

SPEAKER AND CHARACTER RULES:
- Assign the tag to the person who is actually speaking, not merely the person visible on screen.
- Dialogue from a distant, off-camera, quiet, echoing, or partially covered speaker is still real dialogue. Translate it normally and completely; never shorten or omit it merely because the speaker sounds far away.
- Do not change meaning, pronouns, or speaker identity because a voice is louder, quieter, nearer, farther, muffled, or reverberant.
- Keep each recurring character on a consistent gender/age/role tag across nearby cues. Never switch a character's label merely because the emotion, volume, camera angle, or speaking style changes.
- Before assigning a new tag, compare with the preceding and following cues. Change the tag only when the actual speaker changes or clear video/audio evidence proves a different age/gender/role.
- Use BOY/GIRL for children, M_YOUNG/F_YOUNG for teenagers or young adults, M_ADULT/F_ADULT for ordinary adults, and M_OLD/F_OLD for elderly speakers.
- Choose age from the actual voice and visible character context; do not guess an elderly or child label from clothing alone.
- Use M_THINK or F_THINK only for an unheard inner thought or internal monologue.
- Use NARRATOR tags only for true off-screen narration, not for a character's thought.
- Use BOY/GIRL and M_OLD/F_OLD only when age is clearly supported; otherwise prefer M_YOUNG/F_YOUNG or M_ADULT/F_ADULT.

PROFESSIONAL KHMER TRANSLATION RULES:
- Translate into smooth, natural spoken Khmer that Cambodian people actually use in everyday conversation and movie dialogue.
- Never translate word-for-word. First understand the whole meaning, situation, relationship, and emotion, then rewrite it naturally in Khmer.
- Avoid formal, book-like, bureaucratic, robotic, dry, or machine-translated Khmer unless the character and scene truly require formal speech.
- Prefer short, familiar, easy-to-understand Khmer expressions. The sentence should sound natural when spoken aloud, not merely look grammatically correct in writing.
- Preserve the original meaning, intention, emotion, humor, threat, sarcasm, romance, fear, grief, status, and relationship.
- You may reorder wording inside the same cue and replace unnatural literal phrases with familiar Khmer speech, but you MUST preserve every audible idea, response, interjection, negation, name, number, command, and emotional particle. Never invent information or change the meaning.
- Do NOT delete short words, filler sounds, reactions, repeated words, names, negations, or tiny replies when they are audible in the source. Translate natural reactions such as 嗯, 啊, 哦, 喂, 哎, 好, 不, 是, 什么 into suitable spoken Khmer such as អឺ, អា៎, អូ, ហេ៎, អុញ, បាន, ទេ, មែន, អី—according to context.
- Use conversational sentence order and natural responses such as “អញ្ចឹងមែន?”, “បានហើយ”, “មិនអីទេ”, “តើមានរឿងអី?”, or similar only when they accurately match the source meaning and scene.
- Choose pronouns and forms of address that fit age, gender, rank, relationship, and scene context, such as: បង/អូន, ខ្ញុំ/លោក, ឯង/អញ, ពួកម៉ាក, សម្លាញ់, លោកគ្រូ, សិស្ស, ព្រះអង្គ, អធិរាជ, ម្ចាស់, មេទ័ព, លោកតា, លោកយាយ.
- Use natural Khmer emotion particles only when suitable, for example: ណា, ណ៎, ចា៎, ចុះ, អញ្ចឹង, ហ្នឹង, មែនទេ, វើយ, ហ្មង, ហាស, អូហ៍.
- FACEBOOK-SAFE LANGUAGE MODE IS ALWAYS ON: do not output profanity, obscene expressions, sexual insults, degrading slurs, hateful language, direct humiliation, or unnecessarily graphic wording.
- When the source contains rude or offensive speech, keep the intention and emotion but replace it with a clean, natural Khmer expression suitable for a general Facebook audience. For example, use context-appropriate clean phrases such as «មនុស្សអាក្រក់», «ឈប់និយាយទៅ», «កុំធ្វើបែបនេះ», «គួរឱ្យខឹងមែន», or «ចេញទៅ» instead of reproducing vulgar wording.
- Do not sanitize so aggressively that the plot meaning disappears. Preserve whether the speaker is angry, threatening, mocking, shocked, or rejecting someone, but express it without offensive vocabulary.
- Never create insults that were not present in the source. Never target protected characteristics, disability, appearance, family members, or private sexual matters.
- Do not overuse slang, insults, or particles. Match the actor's personality and the scene while keeping the wording clean enough for a broad Facebook audience.
- For historical, cultivation, martial-arts, palace, fantasy, or modern-drama terms, choose Khmer wording that viewers understand while keeping names and ranks consistent.
- If a source phrase contains an idiom, joke, hidden meaning, or wordplay, recreate the intended effect naturally in Khmer instead of translating the literal words.
- Do not leave Chinese characters, pinyin, English explanation, translator notes, or brackets inside the Khmer dialogue.

EMOTION AND DUBBING RULES:
- Write each line so that Khmer AI speech sounds smooth, emotional, and easy to pronounce.
- Use punctuation naturally to guide pauses, breathing, and rising/falling intonation, but avoid excessive punctuation.
- Use one full stop for a normal statement, `?` only for a real question, and `!` only for a real emotional outburst. Do not add repeated punctuation or artificial ellipses; they make Khmer TTS jump or sound flat.
- Keep one natural spoken idea in each cue, with a gentle pause only where a real speaker would breathe.
- Make angry lines firm, sad lines gentle, romantic lines warm, fearful lines urgent, and comic lines lively.
- Avoid awkward repeated words, robotic phrasing, and long formal constructions.

KHMER DUBBING QUALITY RULES:
- Translate as if you are writing dialogue for a professional Khmer TV dubbing studio.
- Every sentence must sound like a real Cambodian person speaking naturally.
- Prefer intended meaning and emotion over literal wording.
- Rewrite sentence structure whenever necessary so it flows naturally in Khmer.
- Keep emotion and character continuity flowing from one subtitle to the next.
- Never produce robotic, dry, textbook, or machine-translated Khmer.
- Use familiar daily Khmer expressions only when they fit the character and situation.
- If the source is emotional, make the Khmer line emotionally convincing without changing its meaning.
- Avoid repeating the same words in consecutive subtitles unless the repetition is intentional.
- If a direct translation sounds unnatural, reshape it into natural Khmer conversation.
- Make every subtitle easy for Khmer AI voices to pronounce with natural rhythm and breathing.
- The final dialogue should sound as if it was originally written and performed in Khmer.
- Before returning each subtitle, silently ask: “Would a Cambodian naturally say this in a real conversation or movie?” If not, rewrite it.

STRICT TIMING AND SUBTITLE LENGTH RULES:
- The supplied start and end timestamp of every cue is locked. Never move dialogue earlier or later, never borrow time from another cue, and never merge or split cues.
- Each cue includes MAX_WORDS. The Khmer text MUST stay at or below that word limit so the generated voice can finish inside its own timestamp.
- Start speaking at the cue start and finish before the cue end. Do not let one character's voice overlap the next cue unless the original timestamps themselves overlap.
- Shorten only by choosing concise natural Khmer wording; never delete a meaning-bearing word, negation, name, number, command, response, or audible reaction.
- Cut and reshape the translation so it fits the subtitle time and can be spoken comfortably before the cue ends.
- Prefer one short, clear, natural spoken sentence per cue.
- Keep the complete meaning and emotional force. Never remove an audible word merely because it is short, repeated, a filler, a reaction, or difficult to fit. Use concise Khmer wording while preserving it.
- Do not make a line unnaturally incomplete merely to shorten it; choose a shorter natural Khmer expression instead.
- Never merge, split, omit, summarize away, or renumber cues. Every supplied cue must contain spoken Khmer text unless the source cue is truly silent/non-speech.

MANDATORY NO-SKIP RULES:
- Translate 100% of the audible speech in every cue, including one-word replies and tiny sounds.
- Never return an empty text value for a cue containing speech.
- Preserve negatives such as “not/no/don’t”, names, numbers, titles, greetings, calls, sighs, surprise, agreement, disagreement, and repeated emphasis.
- Do not summarize two clauses into one if that removes information.
- If the source is very short, return a correspondingly short Khmer utterance rather than deleting it.
- Recheck each cue against SOURCE before output: every audible element must be represented in Khmer.
- Final safety check for every cue: remove or rewrite any vulgar, obscene, hateful, sexually insulting, or degrading word into clean natural Khmer while preserving the scene's meaning and emotion.
- Final timing check for every cue: wording must be speakable within that cue's exact duration without rushing, dragging, starting early, or finishing late.

OUTPUT RULES:
- Return exactly one object for every supplied cue ID, in the same order.
- Every text value must be fluent Khmer suitable for professional movie subtitles and dubbing.
- JSON only. No markdown fences, headings, comments, or explanation.
"""

ANALYZE_PROMPT = """You are a Chinese-drama Khmer dubbing continuity editor.
Review the supplied fixed-timestamp cues using the video context.
Return a JSON array only with exactly:
{"id": integer, "tag": string, "text": string}

Allowed tags:
BOY, GIRL, M_YOUNG, F_YOUNG, M_ADULT, F_ADULT, M_OLD, F_OLD, M_THINK, F_THINK, NARRATOR_M, NARRATOR_F

Rules:
- Return exactly one object per cue ID in the same order.
- Do not alter timestamps, cue count, or cue order.
- Keep recurring character identity and tag consistent across nearby cues.
- Ordinary audible dialogue must use the correct age-and-gender label, even when calm, soft, sad, angry, or whispering.
- Use THINK only for unheard internal monologue; use NARRATOR only for true narration.
- Use BOY/GIRL and M_OLD/F_OLD only when age is clearly supported; use M_YOUNG/F_YOUNG for young speakers and M_ADULT/F_ADULT for adults.
- Rewrite Khmer into fluent, natural everyday Cambodian dialogue suitable for professional movie dubbing; never use stiff word-for-word or book-like phrasing.
- Read each Khmer line as spoken dialogue: if a Cambodian would not normally say it that way, rewrite it using shorter and more familiar wording.
- Respect each cue's MAX_WORDS strictly so dubbing can play at a normal pace.
- Preserve every spoken meaning, including short replies, particles, hesitation sounds, repeated words, names, negations, and small expressions. Never delete a cue or omit a spoken word merely to shorten it; shorten only by natural Khmer rephrasing without information loss.
- JSON only. No explanations or markdown.
"""

API_COOKIE_NAME = "ai_khemra_bro_private_api"
SETTINGS_COOKIE_NAME = "ai_khemra_bro_private_settings"
LEGACY_COOKIE_SECRET = "AI-KHEMRA-BRO-PERSISTENT-PRIVATE-COOKIE-v1-2026"

try:
    configured_cookie_secret = str(st.secrets.get("COOKIE_SECRET", "")).strip()
except Exception:
    configured_cookie_secret = ""

# New encryption uses the private Streamlit secret when supplied.  The legacy
# cipher remains read-only so a later security upgrade never makes existing
# encrypted customer API keys unreadable.  PREVIOUS_COOKIE_SECRETS supports
# a deliberate secret rotation without losing already saved browser keys.
try:
    configured_previous_cookie_secrets = str(
        st.secrets.get("PREVIOUS_COOKIE_SECRETS", "")
    ).strip()
except Exception:
    configured_previous_cookie_secrets = ""

COOKIE_SECRET_CONFIGURED = bool(configured_cookie_secret)
primary_cookie_secret = configured_cookie_secret or LEGACY_COOKIE_SECRET
previous_cookie_secrets = [
    secret.strip()
    for secret in configured_previous_cookie_secrets.replace(",", "\n").splitlines()
    if secret.strip()
]
cipher_secrets = []
for secret in [primary_cookie_secret, *previous_cookie_secrets, LEGACY_COOKIE_SECRET]:
    if secret and secret not in cipher_secrets:
        cipher_secrets.append(secret)
api_ciphers = [
    Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest()))
    for secret in cipher_secrets
]
api_cipher = api_ciphers[0]
cookie_manager = stx.CookieManager(key="ai_khemra_private_cookie_manager")


def _clean_api_keys(api_keys_text):
    """Normalize and deduplicate user keys without logging their values."""
    keys = []
    seen = set()
    for raw_key in str(api_keys_text or "").replace(",", "\n").splitlines():
        key = raw_key.strip()
        if key and key not in seen:
            keys.append(key)
            seen.add(key)
    return "\n".join(keys)


def load_secret_gemini_api_keys():
    """Read optional app-level fallback keys from Streamlit Secrets, never from GitHub."""
    try:
        return _clean_api_keys(st.secrets.get("GEMINI_API_KEYS", ""))
    except Exception:
        return ""


def encrypt_api_keys(api_keys_text):
    cleaned = _clean_api_keys(api_keys_text)
    if not cleaned:
        return ""
    return api_cipher.encrypt(cleaned.encode("utf-8")).decode("utf-8")


def decrypt_api_keys(cookie_value):
    """Read current keys and legacy-encrypted keys without exposing their values."""
    if not cookie_value:
        return ""
    encrypted = str(cookie_value).encode("utf-8")
    for cipher in api_ciphers:
        try:
            return cipher.decrypt(encrypted).decode("utf-8")
        except (InvalidToken, ValueError, TypeError):
            continue
    return ""


def _current_customer_code():
    """Return the authenticated customer's normalized access code."""
    try:
        return normalize_access_code(st.session_state.get("customer_code", ""))
    except Exception:
        return str(st.session_state.get("customer_code", "") or "").strip().upper()


def _load_api_keys_from_account():
    """Load encrypted API keys from the persistent customer account database."""
    code = _current_customer_code()
    if not code:
        return ""
    try:
        with license_connection() as connection:
            row = connection.execute(
                "SELECT saved_api_keys_encrypted FROM licenses "
                "WHERE access_code_hash=? OR access_code_display=?",
                (_hash_code(code), code),
            ).fetchone()
        if not row:
            return ""
        return decrypt_api_keys(row["saved_api_keys_encrypted"] or "")
    except Exception:
        return ""


def _save_api_keys_to_account(api_keys_text):
    """Save encrypted API keys against the signed-in account, not only Safari."""
    code = _current_customer_code()
    if not code:
        return False
    cleaned = _clean_api_keys(api_keys_text)
    encrypted = encrypt_api_keys(cleaned) if cleaned else ""
    try:
        with license_connection() as connection:
            cursor = connection.execute(
                "UPDATE licenses SET saved_api_keys_encrypted=? "
                "WHERE access_code_hash=? OR access_code_display=?",
                (encrypted, _hash_code(code), code),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                return False
            connection.commit()
        return True
    except Exception:
        return False


def load_private_api_keys():
    """Load the encrypted personal key from this browser only.

    API keys are intentionally not read from the shared license record, so two
    phones using different (or even the same) access code never receive each
    other's personal key.
    """
    try:
        return decrypt_api_keys(cookie_manager.get(API_COOKIE_NAME))
    except Exception:
        return ""


def save_private_api_keys(api_keys_text):
    """Keep a customer's personal API key in this browser's encrypted cookie only."""
    cleaned = _clean_api_keys(api_keys_text)
    try:
        if cleaned:
            cookie_manager.set(
                API_COOKIE_NAME,
                encrypt_api_keys(cleaned),
                expires_at=datetime.datetime.now() + datetime.timedelta(days=7300),
                key="save_private_api_cookie",
            )
        else:
            cookie_manager.delete(API_COOKIE_NAME, key="delete_private_api_cookie")
        return True
    except Exception:
        return False


def delete_private_api_keys():
    """Delete only this browser's saved API key when the user explicitly requests it."""
    try:
        cookie_manager.delete(API_COOKIE_NAME, key="delete_private_api_cookie_explicit")
    except Exception:
        pass


def _validate_translation_preferences(payload, owner_code):
    """Validate a stored Settings payload before allowing it into Streamlit state."""
    owner = normalize_access_code(owner_code)
    saved = dict(payload or {})
    if normalize_access_code(saved.get("owner", "")) != owner:
        return {}
    model = str(saved.get("model_selector", ""))
    target = str(saved.get("target_language", ""))
    style = str(saved.get("translation_style", ""))
    if model not in GEMINI_MODEL_OPTIONS or target not in TARGET_LANGUAGE_OPTIONS or style not in TRANSLATION_STYLE_OPTIONS:
        return {}
    return {"model_selector": model, "target_language": target, "translation_style": style}


def _load_translation_preferences_from_account(owner_code):
    """Fallback for browsers that block a cookie write; data is keyed to one customer."""
    owner = normalize_access_code(owner_code)
    if not owner:
        return {}
    try:
        with license_connection() as connection:
            row = connection.execute(
                "SELECT saved_translation_preferences_encrypted FROM licenses "
                "WHERE access_code_hash=? OR access_code_display=?",
                (_hash_code(owner), owner),
            ).fetchone()
        payload = decrypt_api_keys(row["saved_translation_preferences_encrypted"] or "") if row else ""
        return _validate_translation_preferences(json.loads(payload) if payload else {}, owner)
    except Exception:
        return {}


def _save_translation_preferences_to_account(owner_code, payload):
    """Persist safe settings so Save succeeds even when a mobile cookie is blocked."""
    owner = normalize_access_code(owner_code)
    if not owner:
        return False
    try:
        encrypted = encrypt_api_keys(json.dumps(payload, ensure_ascii=False))
        with license_connection() as connection:
            cursor = connection.execute(
                "UPDATE licenses SET saved_translation_preferences_encrypted=? "
                "WHERE access_code_hash=? OR access_code_display=?",
                (encrypted, _hash_code(owner), owner),
            )
            connection.commit()
        return cursor.rowcount == 1
    except Exception:
        return False


def load_private_translation_preferences(owner_code):
    """Load settings from the browser first, then use the same customer's encrypted fallback."""
    owner = normalize_access_code(owner_code)
    try:
        encrypted = cookie_manager.get(SETTINGS_COOKIE_NAME)
        payload = decrypt_api_keys(encrypted) if encrypted else ""
        saved = _validate_translation_preferences(json.loads(payload) if payload else {}, owner)
        if saved:
            return saved
    except Exception:
        pass
    return _load_translation_preferences_from_account(owner)


def save_private_translation_preferences(owner_code, model_selector, target_language, translation_style):
    """Save validated Settings privately; browser cookie is optional, account fallback is reliable."""
    owner = normalize_access_code(owner_code)
    model = str(model_selector or "")
    target = str(target_language or "")
    style = str(translation_style or "")
    payload = _validate_translation_preferences({
        "owner": owner, "model_selector": model,
        "target_language": target, "translation_style": style,
    }, owner)
    if not payload:
        return False
    account_saved = _save_translation_preferences_to_account(owner, {"owner": owner, **payload})
    cookie_saved = False
    try:
        cookie_manager.set(
            SETTINGS_COOKIE_NAME,
            encrypt_api_keys(json.dumps({"owner": owner, **payload}, ensure_ascii=False)),
            expires_at=datetime.datetime.now() + datetime.timedelta(days=7300),
            key="save_private_translation_preferences",
        )
        cookie_saved = True
    except Exception:
        pass
    # Settings are already validated and live in this private Streamlit session.
    # A cookie/account write is attempted for persistence, but a mobile browser
    # must never be blocked from using its selected model/style if that write is
    # acknowledged asynchronously by the cookie component.
    return True


def api_keys_changed():
    save_private_api_keys(st.session_state.get("api_keys_manager", ""))


def clear_private_user_session(delete_saved_api=False):
    """Clear only the current browser's work without exposing or retaining another user's data."""
    if delete_saved_api:
        delete_private_api_keys()
    st.session_state.pop("api_keys_manager", None)
    st.session_state.pop("private_preferences_owner", None)
    for state_key, default_value in {
        "srt_text": "",
        "pending_srt": "",
        "audio_bytes": None,
        "pending_editor_update": None,
        "audio_job_pending": None,
        "source_srt_text": "",
        "translated_srt_preview": "",
        "speech_tab_audio_bytes": None,
        "text_tab_audio_bytes": None,
        "source_video_stem": "khmer_story",
        "mp3_download_name": "khmer_story_dubbed",
        "mp3_filename_widget": "khmer_story_dubbed",
        "project_temp_files": [],
        "ducking_profiles": {},
        "background_music_paths": {},
        "background_music_signatures": {},
        "background_music_upload_versions": {},
    }.items():
        st.session_state[state_key] = default_value


def _new_project_workspace():
    """Create a private workspace for this Streamlit browser session only."""
    session_id = uuid.uuid4().hex
    workspace = Path(tempfile.gettempdir()) / "ai_khemra_bro_sessions" / session_id
    workspace.mkdir(parents=True, exist_ok=True)
    return session_id, workspace


def _ensure_project_workspace():
    session_id = st.session_state.get("project_session_id")
    workspace_value = st.session_state.get("project_workspace")
    if not session_id or not workspace_value:
        session_id, workspace = _new_project_workspace()
        st.session_state.project_session_id = session_id
        st.session_state.project_workspace = str(workspace)
        return workspace
    workspace = Path(workspace_value)
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _reset_project_workspace():
    """Delete and recreate only the current user's workspace."""
    old_value = st.session_state.get("project_workspace")
    if old_value:
        shutil.rmtree(old_value, ignore_errors=True)
    session_id, workspace = _new_project_workspace()
    st.session_state.project_session_id = session_id
    st.session_state.project_workspace = str(workspace)
    return workspace


def bind_workspace_to_customer(access_code):
    """Keep temporary work private when a different customer signs in on this browser."""
    owner = normalize_access_code(access_code)
    previous_owner = st.session_state.get("private_workspace_owner", "")
    if previous_owner and previous_owner != owner:
        clear_private_user_session(delete_saved_api=False)
        _reset_project_workspace()
        st.session_state.video_uploader_version = st.session_state.get("video_uploader_version", 0) + 1
    st.session_state.private_workspace_owner = owner
    return _ensure_project_workspace()


@st.cache_resource(show_spinner=False)
def load_whisper_model():
    # Base + int8 is selected so it can run on Streamlit Community Cloud CPU.
    return WhisperModel("base", device="cpu", compute_type="int8")

for key,value in {
    'srt_text':'',
    'pending_srt':'',
    'audio_bytes':None,
    'pending_editor_update':None,
    'source_video_stem':'khmer_story',
    'mp3_download_name':'khmer_story_dubbed',
    'video_uploader_version':0,
    'project_temp_files':[],
    'project_session_id':'',
    'project_workspace':'',
    'private_workspace_owner':'',
    'mp3_filename_widget':'khmer_story_dubbed',
    'source_srt_text':'',
    'translated_srt_preview':'',
    'speech_tab_audio_bytes':None,
    'text_tab_audio_bytes':None,
    'ducking_profiles':{},
    'background_music_paths':{},
    'background_music_signatures':{},
    'background_music_upload_versions':{},
}.items():
    if key not in st.session_state:
        st.session_state[key]=value

_ensure_project_workspace()

def clean_srt(text):
    text=re.sub(r'^```(?:srt)?\s*','',text.strip(),flags=re.I)
    return re.sub(r'\s*```$','',text).strip()

def safe_download_stem(value, fallback='khmer_story_dubbed'):
    """Create a safe, user-editable filename without changing the audio data."""
    name = Path(str(value or '')).stem.strip()
    name = re.sub(r'[\\/:*?"<>|]+', '_', name)
    name = re.sub(r'\s+', ' ', name).strip(' ._-')
    return (name or fallback)[:100]

def save_upload(uploaded_file):
    """Save a supported upload atomically inside this user's private workspace."""
    allowed_suffixes = {".mp4", ".mov", ".mkv", ".webm"}
    suffix = Path(getattr(uploaded_file, "name", "")).suffix.lower() or ".mp4"
    if suffix not in allowed_suffixes:
        raise ValueError("Unsupported video format. Please use MP4, MOV, MKV, or WEBM.")
    workspace = _ensure_project_workspace()
    destination = workspace / f"upload_{uuid.uuid4().hex}{suffix}"
    try:
        uploaded_file.seek(0)
        with destination.open("wb") as temp:
            shutil.copyfileobj(uploaded_file, temp, length=4 * 1024 * 1024)
            temp.flush()
        if not destination.exists() or destination.stat().st_size == 0:
            raise RuntimeError("The uploaded video is empty or incomplete.")
        return destination
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"Could not save the uploaded video: {exc}") from exc

def validate_video_duration(video_path):
    """Reject videos longer than the supported ten-minute workflow before ASR/Gemini work starts."""
    seconds = probe_audio_duration(video_path)
    if seconds > VIDEO_MAX_DURATION_SECONDS:
        raise ValueError("Videos must be 10 minutes or shorter. Please trim the video and try again.")
    return seconds


def save_background_music_upload(uploaded_file):
    """Save one customer-owned music track inside the private session workspace."""
    allowed_suffixes = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}
    suffix = Path(getattr(uploaded_file, 'name', '')).suffix.lower() or '.mp3'
    if suffix not in allowed_suffixes:
        raise ValueError('Background music must be MP3, WAV, M4A, AAC, or OGG.')
    size = int(getattr(uploaded_file, 'size', 0) or 0)
    if size <= 0 or size > BACKGROUND_MUSIC_MAX_MB * 1024 * 1024:
        raise ValueError(f'Background music must be smaller than {BACKGROUND_MUSIC_MAX_MB} MB.')
    workspace = _ensure_project_workspace()
    destination = workspace / f'music_{uuid.uuid4().hex}{suffix}'
    try:
        uploaded_file.seek(0)
        with destination.open('wb') as temp:
            shutil.copyfileobj(uploaded_file, temp, length=4 * 1024 * 1024)
            temp.flush()
        if not destination.exists() or destination.stat().st_size < 256:
            raise RuntimeError('The uploaded music file is empty or incomplete.')
        return destination
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f'Could not save the uploaded music file: {exc}') from exc


def normalized_ducking_config(config=None):
    """Clamp browser-provided controls to smooth, safe FFmpeg ducking values."""
    raw = dict(DUCKING_DEFAULTS)
    raw.update(dict(config or {}))
    return {
        'enabled': bool(raw.get('enabled', True)),
        'music_gain': min(0.70, max(0.10, float(raw.get('music_gain', 0.42)))),
        'threshold': min(0.20, max(0.010, float(raw.get('threshold', 0.050)))),
        'ratio': min(12.0, max(2.0, float(raw.get('ratio', 8.0)))),
        'attack_ms': int(min(180, max(15, int(raw.get('attack_ms', 40))))),
        'release_ms': int(min(1600, max(250, int(raw.get('release_ms', 700))))),
        'knee': min(8.0, max(1.0, float(raw.get('knee', 4.0)))),
        'music_fade_in_seconds': float(DUCKING_DEFAULTS['music_fade_in_seconds']),
        'music_fade_out_seconds': float(DUCKING_DEFAULTS['music_fade_out_seconds']),
    }


def render_audio_ducking_controls(context_key):
    """Render one mobile-safe music uploader and return its private path + settings."""
    profiles = dict(st.session_state.get('ducking_profiles', {}))
    stored = normalized_ducking_config(profiles.get(context_key))
    versions = dict(st.session_state.get('background_music_upload_versions', {}))
    version = int(versions.get(context_key, 0))
    paths = dict(st.session_state.get('background_music_paths', {}))
    signatures = dict(st.session_state.get('background_music_signatures', {}))

    with st.expander('🎵 Background Music & Auto Ducking', expanded=False):
        st.caption('Music lowers smoothly while dialogue is present and returns naturally afterward.')
        upload = st.file_uploader(
            'Background Music (MP3/WAV/M4A/AAC/OGG)',
            type=['mp3', 'wav', 'm4a', 'aac', 'ogg'],
            key=f'background_music_{context_key}_{version}',
            label_visibility='collapsed',
        )
        if upload is not None:
            signature = f'{getattr(upload, "name", "music")}:{getattr(upload, "size", 0)}'
            current = Path(paths.get(context_key, '')) if paths.get(context_key) else None
            if signature != signatures.get(context_key) or not current or not current.exists():
                current = save_background_music_upload(upload)
                paths[context_key] = str(current)
                signatures[context_key] = signature
                st.session_state.project_temp_files.append(str(current))
                st.session_state.background_music_paths = paths
                st.session_state.background_music_signatures = signatures
        music_path = Path(paths[context_key]) if paths.get(context_key) else None
        if music_path and music_path.exists():
            st.caption(f'✅ Music selected: {music_path.name}')
        else:
            st.caption('Without music, the app creates a normal voice-only MP3.')

        enabled = st.toggle(
            '🎚️ Enable Auto Ducking', value=stored['enabled'],
            disabled=not (music_path and music_path.exists()), key=f'ducking_enabled_{context_key}',
        )
        c1, c2 = st.columns(2, gap='small')
        with c1:
            music_gain = st.slider('Music Level', 0.10, 0.70, stored['music_gain'], 0.01,
                                   key=f'ducking_gain_{context_key}')
            ratio = st.slider('Ducking Strength', 2.0, 12.0, stored['ratio'], 0.5,
                              key=f'ducking_ratio_{context_key}')
        with c2:
            attack_ms = st.slider('Music Fade Down', 15, 180, stored['attack_ms'], 5,
                                  key=f'ducking_attack_{context_key}')
            release_ms = st.slider('Music Fade Up', 250, 1600, stored['release_ms'], 50,
                                   key=f'ducking_release_{context_key}')
        current_config = normalized_ducking_config({
            'enabled': enabled,
            'music_gain': music_gain,
            'ratio': ratio,
            'attack_ms': attack_ms,
            'release_ms': release_ms,
        })
        profiles[context_key] = current_config
        st.session_state.ducking_profiles = profiles
        return (music_path if music_path and music_path.exists() else None), current_config


def seconds_to_srt(value):
    total_ms = max(0, int(round(float(value) * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def optimize_video_for_processing(source_path, output_path):
    """Create a small 480p proxy to reduce server RAM, disk and Gemini upload size."""
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(source_path),
            "-map", "0:v:0", "-map", "0:a:0?",
            "-vf", "scale='min(480,iw)':-2,fps=12",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "32",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ac", "1", "-ar", "16000", "-b:a", "32k",
            "-movflags", "+faststart",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        timeout=900,
    )
    if result.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(result.stderr[-1200:] or "Could not optimize the video.")
    return output_path


def extract_audio(video_path, audio_path, fast_mode=True):
    """Extract a small Whisper-ready mono track with bounded logs and clear errors."""
    base = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", str(video_path)]
    if fast_mode:
        command = base + ["-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio_path)]
    else:
        # Clear mode helps unusually noisy recordings but takes longer than fast mode.
        audio_filter = (
            "highpass=f=70,lowpass=f=7800,afftdn=nf=-28:tn=1,"
            "dynaudnorm=f=250:g=9:p=0.95:m=12,"
            "acompressor=threshold=-30dB:ratio=2.2:attack=12:release=180:makeup=1.35,"
            "alimiter=limit=0.97"
        )
        command = base + [
            "-vn", "-ac", "1", "-ar", "16000", "-af", audio_filter,
            "-c:a", "flac", "-compression_level", "5", str(audio_path),
        ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired as exc:
        audio_path.unlink(missing_ok=True)
        raise RuntimeError("Audio extraction took too long. Try a shorter or smaller video.") from exc
    except FileNotFoundError as exc:
        raise RuntimeError("The server does not have FFmpeg required for video processing.") from exc
    if result.returncode != 0 or not audio_path.exists() or audio_path.stat().st_size < 1024:
        audio_path.unlink(missing_ok=True)
        raise RuntimeError(result.stderr[-1200:] or "Could not extract audio from the video.")


def _standardize_whisper_segments(segments):
    """Split ASR output into readable, timing-accurate subtitle cues."""
    cues = []
    max_duration = 5.5
    max_chars = 34
    punctuation = set("。！？!?；;，,")

    def emit(words):
        if not words:
            return
        text = "".join((getattr(w, "word", "") or "") for w in words).strip()
        if not text:
            return
        start = max(0.0, float(getattr(words[0], "start", 0.0) or 0.0))
        end = max(start + 0.20, float(getattr(words[-1], "end", start + 0.20) or start + 0.20))
        cues.append({"id": len(cues) + 1, "start": start, "end": end, "source": text})

    for segment in segments:
        words = [w for w in (getattr(segment, "words", None) or []) if (getattr(w, "word", "") or "").strip()]
        if not words:
            text = (getattr(segment, "text", "") or "").strip()
            if text:
                start = max(0.0, float(segment.start))
                end = max(start + 0.20, float(segment.end))
                cues.append({"id": len(cues) + 1, "start": start, "end": end, "source": text})
            continue

        current = []
        for word in words:
            if current:
                gap = max(0.0, float(word.start or 0.0) - float(current[-1].end or 0.0))
                duration = float(current[-1].end or 0.0) - float(current[0].start or 0.0)
                chars = len("".join((getattr(w, "word", "") or "") for w in current))
                if gap >= 0.55 or duration >= max_duration or chars >= max_chars:
                    emit(current)
                    current = []
            current.append(word)
            token = (getattr(word, "word", "") or "").strip()
            duration = float(word.end or 0.0) - float(current[0].start or 0.0)
            if token and token[-1] in punctuation and duration >= 0.65:
                emit(current)
                current = []
        emit(current)

    # Remove only tiny accidental overlaps; never push a cue far from the speech.
    previous_end = 0.0
    for cue in cues:
        if cue["start"] < previous_end and previous_end - cue["start"] <= 0.12:
            cue["start"] = previous_end
        if cue["end"] <= cue["start"]:
            cue["end"] = cue["start"] + 0.25
        previous_end = cue["end"]
    for index, cue in enumerate(cues, 1):
        cue["id"] = index
    return cues


def transcribe_with_whisper(wav_path, fast_mode=True):
    model = load_whisper_model()
    # Fast mode keeps word timestamps and context but avoids expensive wide beam search.
    beam_size = 3 if fast_mode else 5
    best_of = 1 if fast_mode else 3
    segments, _ = model.transcribe(
        str(wav_path),
        language=None,  # Auto-detect Chinese, Korean, Vietnamese, or English speech.
        beam_size=beam_size,
        best_of=best_of,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 220,
            "min_speech_duration_ms": 45,
            "speech_pad_ms": 380,
        },
        condition_on_previous_text=True,
        word_timestamps=True,
        no_speech_threshold=0.65,
        log_prob_threshold=-1.5,
        compression_ratio_threshold=2.6,
    )
    cues = _standardize_whisper_segments(list(segments))
    if not cues:
        raise RuntimeError("Whisper did not detect dialogue in this video.")
    return cues


def upload_for_context(client, video_path):
    """Upload optional analysis context with a finite wait, never an indefinite hang."""
    uploaded = client.files.upload(file=str(video_path))
    deadline = time.monotonic() + 180
    while True:
        state = str(getattr(getattr(uploaded, "state", None), "name", "") or "").upper()
        if state != "PROCESSING":
            break
        if time.monotonic() >= deadline:
            raise RuntimeError("Gemini took too long to prepare the video. Try again or refine the SRT without video context.")
        time.sleep(2)
        uploaded = client.files.get(name=uploaded.name)
    if state in {"FAILED", "ERROR"}:
        raise RuntimeError("Gemini could not read this video.")
    if state == "PROCESSING":
        raise RuntimeError("Gemini did not finish preparing the video.")
    return uploaded


def parse_json_array(raw_text):
    import json
    cleaned = (raw_text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    left, right = cleaned.find("["), cleaned.rfind("]")
    if left == -1 or right == -1 or right <= left:
        raise ValueError("AI did not return valid JSON.")
    value = json.loads(cleaned[left:right + 1])
    if not isinstance(value, list):
        raise ValueError("AI JSON output is not a list.")
    return value


def cue_word_limit(start, end):
    """Khmer spoken-word budget that fits normal dialogue speed."""
    duration = max(0.35, float(end) - float(start))
    # Keep dialogue at a comfortable spoken pace. The translation prompt must
    # rephrase naturally rather than rush the generated Khmer voice.
    return max(2, min(20, int(duration * 2.7 + 1.0)))


def khmer_word_count(text):
    return len([part for part in re.split(r"\s+", (text or "").strip()) if part])


def contains_cjk(text):
    return bool(re.search(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]", text or ""))


def normalize_dialogue(text):
    text = re.sub(r"```|<[^>]+>", "", str(text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _error_message(exc):
    return str(exc or "").upper()


def is_quota_error(exc):
    message = _error_message(exc)
    return any(token in message for token in (
        "429", "RESOURCE_EXHAUSTED", "QUOTA", "RATE LIMIT"
    ))


def is_invalid_key_error(exc):
    message = _error_message(exc)
    return any(token in message for token in (
        "API_KEY_INVALID", "INVALID API KEY", "API KEY NOT VALID", "PERMISSION_DENIED",
        "KEY_REPORTED_AS_LEAKED", "REPORTED AS LEAKED"
    ))


def is_model_unavailable_error(exc):
    message = _error_message(exc)
    return "404" in message or "NOT_FOUND" in message or "MODEL NOT FOUND" in message


def is_transient_gemini_error(exc):
    message = _error_message(exc)
    return any(token in message for token in (
        "408", "500", "502", "503", "504", "UNAVAILABLE", "TIMEOUT",
        "DEADLINE_EXCEEDED", "CONNECTION RESET", "CONNECTION ABORTED", "INTERNAL"
    ))


def is_structured_output_error(exc):
    message = _error_message(exc)
    return "JSON" in message or "AI did not return" in str(exc or "")


def is_retryable_model_error(exc):
    """Errors for which trying a different supported model may be useful."""
    return (
        is_quota_error(exc)
        or is_model_unavailable_error(exc)
        or is_transient_gemini_error(exc)
        or is_structured_output_error(exc)
    )


def gemini_generate_with_retry(client, model_name, contents, attempts=2):
    """Return JSON-only Gemini output with a small, bounded transient retry budget."""
    last_error = None
    # The official SDK already retries transient failures. This wrapper adds at
    # most one extra retry and never repeatedly waits on quota or invalid-key errors.
    attempts = max(1, min(2, int(attempts)))
    config = types.GenerateContentConfig(response_mime_type="application/json")
    for attempt in range(attempts):
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            last_error = exc
            if (
                is_quota_error(exc)
                or is_invalid_key_error(exc)
                or is_model_unavailable_error(exc)
                or not is_transient_gemini_error(exc)
                or attempt >= attempts - 1
            ):
                raise
            # Add small jitter so simultaneous mobile requests do not retry together.
            delay = min(4.0, 0.8 * (2 ** attempt)) + random.uniform(0.0, 0.35)
            time.sleep(delay)
    raise last_error


def translation_needs_repair(cue, item):
    """Reject missing, non-Khmer, or clearly overlong dubbing lines."""
    if not item:
        return True
    dialogue = normalize_dialogue(item.get("text"))
    if not dialogue or contains_non_khmer_script(dialogue):
        return True
    # A tiny tolerance avoids needless API calls for Khmer tokenization quirks.
    return khmer_word_count(dialogue) > cue_word_limit(cue["start"], cue["end"]) + 2


def repair_translation_items(client, model_name, uploaded_video, cues, items):
    """Retry only missing or still-Chinese cues until every cue is usable Khmer."""
    by_id = {cue["id"]: cue for cue in cues}
    for _attempt in range(3):
        bad_ids = [
            cue["id"] for cue in cues
            if translation_needs_repair(cue, items.get(cue["id"]))
        ]
        if not bad_ids:
            return items
        for offset in range(0, len(bad_ids), 12):
            group = [by_id[i] for i in bad_ids[offset:offset + 12]]
            payload = "\n".join(
                f'ID={cue["id"]} | MAX_WORDS={cue_word_limit(cue["start"], cue["end"])} | SOURCE={cue["source"]}'
                for cue in group
            )
            prompt = TRANSLATE_PROMPT + "\nIMPORTANT: These cues failed before. Translate EVERY audible word, tiny response, negation, name, number, filler, and emotional reaction fully into natural Khmer. Never omit or summarize any element. Never copy Chinese characters.\n\nCUES:\n" + payload
            contents = [uploaded_video, prompt] if uploaded_video is not None else [prompt]
            response = gemini_generate_with_retry(client, model_name, contents)
            for row in parse_json_array(response.text or ""):
                try:
                    cue_id = int(row.get("id"))
                except (TypeError, ValueError, AttributeError):
                    continue
                if cue_id not in by_id:
                    continue
                tag = str(row.get("tag", "M")).upper().strip()
                if tag not in VOICE_PROFILES:
                    tag = items.get(cue_id, {}).get("tag", "M")
                dialogue = normalize_dialogue(row.get("text"))
                if dialogue and not contains_cjk(dialogue):
                    items[cue_id] = {"tag": tag, "text": dialogue}
    bad_ids = [
        cue["id"] for cue in cues
        if translation_needs_repair(cue, items.get(cue["id"]))
    ]
    if bad_ids:
        raise RuntimeError(f"AI did not complete the translation. Problem cue IDs: {bad_ids[:20]}")
    return items


def refine_translated_cues(client, model_name, uploaded_video, cues, translated):
    """Second pass for stable character tags and short normal-speed dialogue."""
    refined = {}
    batch_size = 35
    for offset in range(0, len(cues), batch_size):
        batch = cues[offset:offset + batch_size]
        lines = []
        for cue in batch:
            item = translated[cue["id"]]
            lines.append(
                f'ID={cue["id"]} | TIME={seconds_to_srt(cue["start"])} --> '
                f'{seconds_to_srt(cue["end"])} | MAX_WORDS={cue_word_limit(cue["start"], cue["end"])} '
                f'| CURRENT_TAG={item["tag"]} | SOURCE={cue["source"]} | KHMER={item["text"]}'
            )
        response = gemini_generate_with_retry(
            client, model_name,
            [uploaded_video, ANALYZE_PROMPT + "\n\nCUES:\n" + "\n".join(lines)],
        )
        for item in parse_json_array(response.text or ""):
            try:
                cue_id = int(item.get("id"))
            except (TypeError, ValueError, AttributeError):
                continue
            tag = str(item.get("tag", "M")).upper().strip()
            if tag not in VOICE_PROFILES:
                tag = translated.get(cue_id, {}).get("tag", "M")
            dialogue = str(item.get("text", "")).strip()
            if dialogue:
                refined[cue_id] = {"tag": tag, "text": dialogue}

    for cue in cues:
        refined.setdefault(cue["id"], translated[cue["id"]])
    return refined


def classify_speaker_tags_from_video(client, model_name, uploaded_video, cues, translated):
    """Use actual video/audio context to assign the four canonical dubbing tags.

    Translation stays on the fast text path.  This focused second pass only returns
    tags, so it cannot alter subtitle wording, IDs, or fixed timestamps.  If the
    optional multimodal service is unavailable, the already-valid translation is
    preserved rather than failing the entire customer job.
    """
    if uploaded_video is None:
        return translated
    tagged = {cue_id: dict(item) for cue_id, item in translated.items()}
    for offset in range(0, len(cues), 32):
        batch = cues[offset:offset + 32]
        payload = "\n".join(
            f'ID={cue["id"]} | TIME={seconds_to_srt(cue["start"])} --> '
            f'{seconds_to_srt(cue["end"])} | SOURCE={cue["source"]}'
            for cue in batch
        )
        response = gemini_generate_with_retry(
            client, model_name, [uploaded_video, SPEAKER_TAG_PROMPT + "\n\nCUES:\n" + payload]
        )
        allowed_ids = {cue["id"] for cue in batch}
        for row in parse_json_array(response.text or ""):
            try:
                cue_id = int(row.get("id"))
            except (TypeError, ValueError, AttributeError):
                continue
            if cue_id in allowed_ids and cue_id in tagged:
                tagged[cue_id]["tag"] = normalize_voice_tag(row.get("tag", tagged[cue_id].get("tag", "M")))
    return tagged


def translate_cues(client, model_name, uploaded_video, cues):
    """Translate in sequential batches while carrying recent character context."""
    result_by_id = {}
    batch_size = 24
    context_size = 6

    for offset in range(0, len(cues), batch_size):
        batch = cues[offset:offset + batch_size]

        previous_context = []
        for previous in cues[max(0, offset - context_size):offset]:
            translated = result_by_id.get(previous["id"])
            if translated:
                previous_context.append(
                    f'ID={previous["id"]} | TAG={translated["tag"]} '
                    f'| SOURCE={previous["source"]} | KHMER={translated["text"]}'
                )

        cue_lines = "\n".join(
            f"ID={cue['id']} | {seconds_to_srt(cue['start'])} --> "
            f"{seconds_to_srt(cue['end'])} | MAX_WORDS={cue_word_limit(cue['start'], cue['end'])} "
            f"| SOURCE={cue['source']}"
            for cue in batch
        )

        context_block = ""
        if previous_context:
            context_block = (
                "\n\nRECENT CONTINUITY CONTEXT (reference only; do not return these IDs):\n"
                + "\n".join(previous_context)
            )

        prompt = (
            TRANSLATE_PROMPT
            + context_block
            + "\n\nNEW CUES TO RETURN:\n"
            + cue_lines
        )
        response = gemini_generate_with_retry(
            client, model_name, [uploaded_video, prompt]
        )
        items = parse_json_array(response.text or "")
        for item in items:
            try:
                cue_id = int(item.get("id"))
            except (TypeError, ValueError, AttributeError):
                continue
            if cue_id not in {cue["id"] for cue in batch}:
                continue
            tag = str(item.get("tag", "M")).upper().strip()
            if tag not in VOICE_PROFILES:
                tag = "M_ADULT"
            translated = normalize_dialogue(item.get("text", ""))
            if translated:
                result_by_id[cue_id] = {"tag": tag, "text": translated}

    return repair_translation_items(
        client, model_name, uploaded_video, cues, result_by_id
    )


def assert_srt_timing_integrity(source_cues, output_srt):
    """Verify that translation never renumbers or moves locked subtitle timings."""
    rendered = srt_to_structured_cues(output_srt)
    expected = [
        (int(cue["id"]), int(round(float(cue["start"]) * 1000)), int(round(float(cue["end"]) * 1000)))
        for cue in source_cues
    ]
    actual = [(int(cue["id"]), int(cue["start_ms"]), int(cue["end_ms"])) for cue in rendered]
    if actual != expected:
        raise RuntimeError("SRT timing or cue IDs changed. Please translate again.")


def build_srt(cues, translated):
    """Build SRT with the four canonical voice tags and Khmer-only dialogue."""
    blocks = []
    for cue in cues:
        item = translated[cue["id"]]
        dialogue = normalize_dialogue(item.get("text", ""))
        if not dialogue or contains_non_khmer_script(dialogue):
            raise RuntimeError(f"Cue {cue['id']} is not valid Khmer-only output.")
        tag = normalize_voice_tag(item.get("tag", "M"))
        blocks.append(
            f'{cue["id"]}\n'
            f'{seconds_to_srt(cue["start"])} --> {seconds_to_srt(cue["end"])}\n'
            f'[{tag}] {dialogue}'
        )
    return "\n\n".join(blocks)


def friendly_ai_error(exc, key_count=1):
    if is_quota_error(exc):
        if key_count > 1:
            return (
                "All configured Gemini API keys have reached their usage quota. "
                "Wait for quota recovery or add an API key from another Google Cloud project in ☰ Settings."
            )
        return (
            "This Gemini API key has reached its usage quota (429). "
            "Wait for quota recovery or add a key from another Google Cloud project in ☰ Settings."
        )
    if is_invalid_key_error(exc):
        return "This Gemini API key is invalid or unauthorized. Add a new key and click Save."
    # Never show URLs or API-key-shaped values from a provider error in the UI.
    message = re.sub(r"https?://\\S+", "", str(exc or ""))
    message = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_API_KEY]", message)
    return f"AI could not complete the translation: {message[:280]}"


# ---------------------------------------------------------------------------
# v5.5 resilient SRT workflow
# ---------------------------------------------------------------------------
def build_source_srt(cues):
    """Build a standards-compliant source-language SRT from Whisper cues.

    This is always available even when Gemini has no quota, so the user never
    loses the transcription work and can still download or translate it later.
    """
    blocks = []
    for index, cue in enumerate(cues, start=1):
        text = normalize_dialogue(cue.get("source", ""))
        if not text:
            continue
        blocks.append(
            f"{index}\n{seconds_to_srt(cue['start'])} --> {seconds_to_srt(cue['end'])}\n{text}"
        )
    return "\n\n".join(blocks).strip()


def transcribe_video_to_source_srt(video_path, fast_mode=True):
    """FFmpeg + Whisper only. Auto-detects source speech and needs no Gemini key."""
    with tempfile.TemporaryDirectory() as folder:
        audio_path = Path(folder) / ("audio_16k.wav" if fast_mode else "audio_16k.flac")
        extract_audio(Path(video_path), audio_path, fast_mode=fast_mode)
        cues = transcribe_with_whisper(audio_path, fast_mode=fast_mode)
        source_srt = build_source_srt(cues)
        if not source_srt or "-->" not in source_srt:
            raise RuntimeError("Could not create a Source SRT from the video.")
        return cues, source_srt

# ---------------------------------------------------------------------------
# v5.4 reliable Khmer SRT pipeline
# ---------------------------------------------------------------------------
def _candidate_gemini_models(selected_model):
    """Use a short list of current stable text models to avoid repeated 404 delays."""
    ordered = [
        str(selected_model or "").strip(),
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
    ]
    result = []
    for name in ordered:
        name = str(name or "").strip()
        if name and name not in result:
            result.append(name)
    return result


def _normalized_api_key_list(api_keys):
    if isinstance(api_keys, str):
        api_keys = [api_keys]
    return [key for key in _clean_api_keys("\n".join(map(str, api_keys or []))).splitlines() if key]


def _translate_batch_text_only(client, model_name, batch, previous_context="", source_language="Auto-detect", translation_style="👤 បកប្រែធម្មតា (Standard)", target_language="Khmer (ខ្មែរ)"):
    """Translate source cues to the selected language without uploading video to the AI service."""
    cue_lines = "\n".join(
        f'ID={cue["id"]} | TIME={seconds_to_srt(cue["start"])} --> '
        f'{seconds_to_srt(cue["end"])} | MAX_WORDS={cue_word_limit(cue["start"], cue["end"])} '
        f'| SOURCE={cue["source"]}'
        for cue in batch
    )
    prompt = build_multilingual_translation_prompt(cue_lines, source_language, previous_context, translation_style, target_language)
    response = gemini_generate_with_retry(client, model_name, [prompt], attempts=3)
    rows = parse_json_array(response.text or "")
    allowed_ids = {cue["id"] for cue in batch}
    parsed = {}
    for row in rows:
        try:
            cue_id = int(row.get("id"))
        except (TypeError, ValueError, AttributeError):
            continue
        if cue_id not in allowed_ids:
            continue
        raw_tag = str(row.get("tag", "")).upper().strip()
        dialogue = normalize_dialogue(row.get("text", ""))
        # Do not silently turn an invalid/blank AI tag into [M].  Reject the row
        # so the bounded repair request has to return one of the four promised tags.
        if raw_tag in CANONICAL_SRT_TAGS and is_valid_target_dialogue(dialogue, target_language):
            parsed[cue_id] = {"tag": raw_tag, "text": dialogue}
    return parsed


def translate_cues_text_only(client, model_name, cues, source_language="Auto-detect", translation_style="👤 បកប្រែធម្មតា (Standard)", target_language="Khmer (ខ្មែរ)", fast_mode=True):
    """Multilingual translation with continuity context, targeted repair, and safe Fast Mode batching."""
    translated = {}
    # Fewer Gemini calls improve throughput without changing the prompt, tags,
    # locked timestamps, or targeted repair safeguards. Standard Mode stays more
    # conservative for dense subtitle files.
    batch_size = FAST_TRANSLATION_BATCH_SIZE if fast_mode else STANDARD_TRANSLATION_BATCH_SIZE
    for offset in range(0, len(cues), batch_size):
        batch = cues[offset:offset + batch_size]
        context_rows = []
        for cue in cues[max(0, offset - 5):offset]:
            item = translated.get(cue["id"])
            if item:
                context_rows.append(
                    f'ID={cue["id"]} TAG={item["tag"]} SOURCE={cue["source"]} TARGET={item["text"]}'
                )
        parsed = _translate_batch_text_only(
            client, model_name, batch, "\n".join(context_rows), source_language, translation_style, target_language
        )
        translated.update(parsed)

        missing = [cue for cue in batch if cue["id"] not in translated]
        if missing:
            repaired = _translate_batch_text_only(
                client, model_name, missing, source_language=source_language,
                translation_style=translation_style, target_language=target_language
            )
            translated.update(repaired)

        still_missing = [cue["id"] for cue in batch if cue["id"] not in translated]
        if still_missing:
            raise RuntimeError(
                "AI did not return enough SRT cue lines: "
                + ", ".join(map(str, still_missing[:20]))
            )
    return translated


def video_to_srt(video_path, api_keys, model, prepared_cues=None, source_language="Auto-detect", translation_style="👤 បកប្រែធម្មតា (Standard)", target_language="Khmer (ខ្មែរ)", fast_mode=True):
    """
    Reliable v6.6.5 path:
    FFmpeg -> Whisper timestamps -> text-only Gemini translation -> selected-language SRT.
    When prepared_cues are supplied, Whisper is not run a second time.
    """
    api_keys = _normalized_api_key_list(api_keys)
    if not api_keys:
        raise ValueError("No Gemini API key is available.")

    if prepared_cues is None:
        with tempfile.TemporaryDirectory() as folder:
            audio_path = Path(folder) / "audio_16k.wav"
            extract_audio(Path(video_path), audio_path, fast_mode=True)
            cues = transcribe_with_whisper(audio_path)
    else:
        cues = prepared_cues
    if not cues:
        raise RuntimeError("Whisper did not detect speech in this video.")

    last_error = None
    for api_key_value in api_keys:
        try:
            client = genai.Client(api_key=api_key_value)
        except Exception as exc:
            last_error = exc
            continue
        for model_name in _candidate_gemini_models(model):
            try:
                translated = translate_cues_text_only(
                    client, model_name, cues, source_language, translation_style,
                    target_language, fast_mode=fast_mode,
                )
                # Fast text translation preserves throughput. A focused video pass then
                # assigns M/F/THINK from the actual active speaker without touching text
                # or timestamps. If optional video context fails, keep the translated SRT.
                try:
                    video_context = upload_for_context(client, video_path)
                    translated = classify_speaker_tags_from_video(client, model_name, video_context, cues, translated)
                except Exception:
                    pass
                result = build_srt(cues, translated)
                assert_srt_timing_integrity(cues, result)
                if not result.strip() or "-->" not in result:
                    raise RuntimeError("Could not create an SRT in the selected target language.")
                return result
            except Exception as exc:
                last_error = exc
                # An invalid key cannot be repaired by trying more models; move to the next key.
                if is_invalid_key_error(exc):
                    break
                if is_retryable_model_error(exc):
                    continue
                raise RuntimeError(friendly_ai_error(exc, len(api_keys))) from exc

    raise RuntimeError(friendly_ai_error(last_error, len(api_keys)))


def translate_srt_to_khmer(srt_text, api_keys, model, source_language="Auto-detect", translation_style="👤 បកប្រែធម្មតា (Standard)", target_language="Khmer (ខ្មែរ)", fast_mode=True):
    """Translate an imported SRT into the selected target language."""
    api_keys = _normalized_api_key_list(api_keys)
    if not api_keys:
        raise ValueError("No Gemini API key is available.")
    source_cues = srt_to_structured_cues(srt_text)
    if not source_cues:
        raise ValueError("The SRT is invalid or has no text to translate.")
    cues = [
        {
            "id": cue["id"],
            "start": cue["start_ms"] / 1000.0,
            "end": cue["end_ms"] / 1000.0,
            "source": cue["text"],
        }
        for cue in source_cues
    ]
    last_error = None
    for api_key_value in api_keys:
        try:
            client = genai.Client(api_key=api_key_value)
        except Exception as exc:
            last_error = exc
            continue
        for model_name in _candidate_gemini_models(model):
            try:
                translated = translate_cues_text_only(
                    client, model_name, cues, source_language, translation_style,
                    target_language, fast_mode=fast_mode,
                )
                result = build_srt(cues, translated)
                assert_srt_timing_integrity(cues, result)
                return result
            except Exception as exc:
                last_error = exc
                if is_invalid_key_error(exc):
                    break
                if is_retryable_model_error(exc):
                    continue
                raise RuntimeError(friendly_ai_error(exc, len(api_keys))) from exc
    raise RuntimeError(friendly_ai_error(last_error, len(api_keys)))


def srt_to_structured_cues(srt_text):
    parsed = parse_srt(srt_text)
    return [
        {
            "id": cue["id"],
            "start_ms": cue["start"],
            "end_ms": cue["end"],
            "tag": cue["tag"],
            "text": cue["text"],
        }
        for cue in parsed
    ]


def ms_to_srt(value):
    return seconds_to_srt(value / 1000.0)


def analyze_inner_thoughts(srt_text, api_keys, selected_model, video_path=None):
    """Improve tags and phrasing with the same safe key/model fallback as translation."""
    cues = srt_to_structured_cues(srt_text)
    if not cues:
        raise ValueError("No valid SRT was found.")
    api_keys = _normalized_api_key_list(api_keys)
    if not api_keys:
        raise ValueError("No Gemini API key is available.")

    last_error = None
    for api_key_value in api_keys:
        try:
            client = genai.Client(api_key=api_key_value)
            context = upload_for_context(client, video_path) if video_path else None
        except Exception as exc:
            last_error = exc
            continue
        for model_name in _candidate_gemini_models(selected_model):
            updated = {}
            try:
                for offset in range(0, len(cues), 35):
                    batch = cues[offset:offset + 35]
                    payload = "\n".join(
                        f'ID={cue["id"]} | TIME={ms_to_srt(cue["start_ms"])} --> {ms_to_srt(cue["end_ms"])} '
                        f'| MAX_WORDS={cue_word_limit(cue["start_ms"] / 1000.0, cue["end_ms"] / 1000.0)} '
                        f'| TAG={cue["tag"]} | TEXT={cue["text"]}'
                        for cue in batch
                    )
                    contents = [ANALYZE_PROMPT + "\n\nCUES:\n" + payload]
                    if context is not None:
                        contents.insert(0, context)
                    response = gemini_generate_with_retry(client, model_name, contents)
                    for item in parse_json_array(response.text or ""):
                        try:
                            cue_id = int(item.get("id"))
                        except (TypeError, ValueError, AttributeError):
                            continue
                        tag = normalize_voice_tag(item.get("tag", "M"))
                        dialogue = str(item.get("text", "")).strip()
                        if dialogue:
                            updated[cue_id] = {"tag": tag, "text": dialogue}
                blocks = []
                for cue in cues:
                    item = updated.get(cue["id"], {"tag": cue["tag"], "text": cue["text"]})
                    tag = normalize_voice_tag(item.get("tag", "M"))
                    blocks.append(
                        f'{cue["id"]}\n{ms_to_srt(cue["start_ms"])} --> {ms_to_srt(cue["end_ms"])}\n'
                        f'[{tag}] {item["text"]}'
                    )
                return "\n\n".join(blocks)
            except Exception as exc:
                last_error = exc
                if is_invalid_key_error(exc):
                    break
                if is_retryable_model_error(exc):
                    continue
                raise RuntimeError(friendly_ai_error(exc, len(api_keys))) from exc
    raise RuntimeError(friendly_ai_error(last_error, len(api_keys)))

def parse_srt(srt_text):
    time_re=re.compile(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})')
    tag_re=re.compile(r'^\[(BOY|GIRL|M_YOUNG|F_YOUNG|M_ADULT|F_ADULT|M_OLD|F_OLD|M_THINK|F_THINK|NARRATOR_M|NARRATOR_F|M|F|OLD_M|OLD_F)\]\s*',re.I)
    def to_ms(v):
        h,m,s,ms=map(int,v); return ((h*60+m)*60+s)*1000+ms
    cues=[]
    for block_index, block in enumerate(re.split(r'\n\s*\n',srt_text.strip()), start=1):
        lines=[x.strip() for x in block.splitlines() if x.strip()]
        idx=next((i for i,x in enumerate(lines) if '-->' in x),None)
        if idx is None or idx+1>=len(lines):
            continue
        match=time_re.search(lines[idx])
        if not match:
            raise ValueError(f"Invalid SRT timestamp in block {block_index}.")
        cue_id = block_index
        if idx > 0 and lines[0].isdigit():
            cue_id = int(lines[0])
        dialogue=' '.join(lines[idx+1:]).strip(); tag_match=tag_re.match(dialogue)
        tag=tag_match.group(1).upper() if tag_match else 'M'
        if tag_match:
            dialogue=dialogue[tag_match.end():].strip()
        if dialogue:
            start_ms=to_ms(match.groups()[:4]); end_ms=to_ms(match.groups()[4:])
            if end_ms <= start_ms:
                raise ValueError(f"The SRT end timestamp must be later than the start timestamp in cue {cue_id}.")
            cues.append({'id': cue_id, 'start':start_ms,'end':end_ms,'tag':tag,'text':dialogue})
    return cues


def coalesce_continuation_cues(cues):
    """Join close consecutive fragments spoken by the same Khmer voice.

    Subtitle lines are often split only for reading on screen.  Sending each
    fragment separately to TTS makes the engine restart its melody every time.
    Joining only close, same-tag fragments preserves one connected spoken phrase
    while different speakers and deliberate pauses remain separate.
    """
    grouped = []
    for cue in cues:
        if (
            grouped
            and grouped[-1]['tag'] == cue['tag']
            and int(cue['start']) - int(grouped[-1]['source_end']) <= CONTINUATION_GAP_MS
        ):
            previous = grouped[-1]
            # A Khmer full stop at a screen-only subtitle break causes an
            # artificial falling tone. Keep question/exclamation marks intact.
            previous['parts'][-1] = previous['parts'][-1].rstrip().rstrip('។').rstrip()
            previous['parts'].append(cue['text'].strip())
            previous['end'] = cue['end']
            previous['source_end'] = cue['end']
        else:
            grouped.append({
                'start': cue['start'], 'end': cue['end'], 'source_end': cue['end'],
                'tag': cue['tag'], 'parts': [cue['text'].strip()],
            })
    return [
        {'start': group['start'], 'end': group['end'], 'tag': group['tag'],
         'text': ' '.join(part for part in group['parts'] if part).strip()}
        for group in grouped
    ]


def run_async(coro):
    loop=asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop); return loop.run_until_complete(coro)
    finally:
        loop.close(); asyncio.set_event_loop(None)

def prepare_tts_text(text):
    """Prepare conversational Khmer for smoother Edge-TTS rhythm and intonation."""
    clean = normalize_dialogue(text)
    # Treat (...), ... and repeated ellipses as one intentional natural hesitation.
    # The Unicode ellipsis is left in the text so Edge TTS can make a gentle pause.
    clean = re.sub(r"\(\s*(?:\.{3,}|…)\s*\)", "…", clean)
    clean = re.sub(r"\.{3,}", "…", clean)
    clean = re.sub(r"…{2,}", "…", clean)
    clean = re.sub(r"\s+([,!?។…])", r"\1", clean)
    clean = re.sub(r"([,!?។]){2,}", r"\1", clean)
    clean = re.sub(r"\s*…\s*", " … ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    # A final Khmer full stop gives declarative lines a gentle natural fall.
    if clean and clean[-1] not in "!?។…":
        clean += "។"
    return clean


async def synthesize(text, profile, output_path):
    clean_text = prepare_tts_text(text)
    if not clean_text:
        raise ValueError('The SRT contains an empty line.')
    last_error = None
    attempts = [
        profile,
        {**profile, 'rate': '+0%', 'pitch': '+0Hz', 'volume': '+0%'},
        {'voice': profile.get('voice', PISITH), 'rate': '+0%', 'pitch': '+0Hz', 'volume': '+0%'},
    ]
    for current in attempts:
        try:
            await edge_tts.Communicate(
                text=clean_text, voice=current['voice'], rate=current['rate'],
                pitch=current['pitch'], volume=current['volume']
            ).save(str(output_path))
            if output_path.exists() and output_path.stat().st_size > 500:
                return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.8)
    raise RuntimeError(f'Edge TTS did not return audio: {last_error or "unknown error"}')

def character_voice_filters(tag):
    """Subtle per-role tone shaping so age/role labels do not all sound identical."""
    mapping = {
        # Canonical speakers are gently aligned before the master stage.  This
        # only offsets speaker-to-speaker rendering differences; it does not
        # normalize individual words or erase a character's emotion.
        'M': ['volume=1.00'],
        'F': ['volume=0.94'],
        'BOY': ['equalizer=f=180:t=q:w=1.0:g=-0.8', 'equalizer=f=2900:t=q:w=1.0:g=1.0'],
        'GIRL': ['equalizer=f=180:t=q:w=1.0:g=-1.0', 'equalizer=f=3000:t=q:w=1.0:g=1.0'],
        'M_YOUNG': ['equalizer=f=190:t=q:w=1.0:g=0.7', 'equalizer=f=2500:t=q:w=1.0:g=0.5'],
        'F_YOUNG': ['equalizer=f=220:t=q:w=1.0:g=0.4', 'equalizer=f=2600:t=q:w=1.0:g=0.6'],
        'M_ADULT': ['equalizer=f=170:t=q:w=1.0:g=1.6', 'equalizer=f=3200:t=q:w=1.0:g=-0.4'],
        'F_ADULT': ['equalizer=f=220:t=q:w=1.0:g=0.9', 'equalizer=f=3000:t=q:w=1.0:g=0.2'],
        'M_OLD': ['equalizer=f=140:t=q:w=1.0:g=2.2', 'equalizer=f=2600:t=q:w=1.0:g=-1.0', 'lowpass=f=7200:p=2'],
        'F_OLD': ['equalizer=f=180:t=q:w=1.0:g=1.7', 'equalizer=f=2800:t=q:w=1.0:g=-0.8', 'lowpass=f=7400:p=2'],
        'M_THINK': [
            # Inner thought remains intelligible yet clearly below ordinary male dialogue.
            'equalizer=f=190:t=q:w=1.0:g=0.4', 'equalizer=f=3000:t=q:w=1.0:g=-0.35',
            'lowpass=f=7400:p=2', f'volume={THOUGHT_VOICE_GAIN:.3f}'
        ],
        'F_THINK': [
            # Normal female dialogue is aligned to 0.94, so 0.564 is exactly 60% of it.
            'equalizer=f=230:t=q:w=1.0:g=0.3', 'equalizer=f=3200:t=q:w=1.0:g=-0.35',
            'lowpass=f=7400:p=2', f'volume={0.94 * THOUGHT_VOICE_GAIN:.3f}'
        ],
        'NARRATOR_M': ['equalizer=f=150:t=q:w=1.0:g=2.0', 'equalizer=f=2200:t=q:w=1.0:g=0.8'],
        'NARRATOR_F': ['equalizer=f=200:t=q:w=1.0:g=1.3', 'equalizer=f=2300:t=q:w=1.0:g=0.7'],
    }
    return mapping.get(tag, [])


def voice_tone_filters(tag):
    """Return the common gentle cleanup chain used by every generated MP3."""
    canonical_tag = normalize_voice_tag(tag)
    return [
        # Keep the TTS tone open. Excessive equalizers/compressors can make Khmer
        # consonants dull or cause each short cue to sound like a separate recording.
        'highpass=f=75:p=2',
        'lowpass=f=7600:p=2',
        'equalizer=f=4300:t=q:w=1.0:g=-1.2',
        'equalizer=f=6200:t=q:w=0.9:g=-1.8',
        *character_voice_filters(canonical_tag),
    ]


def append_audio_master_filters(filters, voice_label, total_seconds=None, music_input_index=None, ducking_config=None, post_master_gain=1.0):
    """Master voice alone or mix it with a smoothly ducked private music track."""
    config = normalized_ducking_config(ducking_config)
    master_label = voice_label
    use_ducking = music_input_index is not None and config['enabled']
    if use_ducking:
        total = max(0.35, float(total_seconds or 0.35))
        fade_out = min(config['music_fade_out_seconds'], max(0.10, total * 0.35))
        fade_out_start = max(0.0, total - fade_out)
        # A filter label can be consumed only once, so split the voice into a
        # detector branch and a clean branch for the final music+voice mix.
        filters.append(f'{voice_label}asplit=2[voice_sidechain][voice_mix]')
        filters.append(
            f'[{music_input_index}:a]asetpts=PTS-STARTPTS,'
            f'volume={config["music_gain"]:.3f},'
            f'apad=whole_dur={total:.3f},atrim=0:{total:.3f},'
            f'afade=t=in:st=0:d={config["music_fade_in_seconds"]:.3f},'
            f'afade=t=out:st={fade_out_start:.3f}:d={fade_out:.3f}[music]'
        )
        filters.append(
            f'[music][voice_sidechain]sidechaincompress='
            f'threshold={config["threshold"]:.3f}:ratio={config["ratio"]:.2f}:'
            f'attack={config["attack_ms"]}:release={config["release_ms"]}:'
            f'makeup=1:knee={config["knee"]:.2f}:detection=rms:mix=1[music_ducked]'
        )
        filters.append(
            '[music_ducked][voice_mix]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[mix_raw]'
        )
        master_label = '[mix_raw]'

    ending = ''
    if total_seconds is not None:
        total = max(0.35, float(total_seconds))
        ending = f',apad=whole_dur={total:.3f},atrim=0:{total:.3f}'
    post_master_gain = min(1.0, max(0.05, float(post_master_gain)))
    post_level = f',volume={post_master_gain:.3f}' if post_master_gain < 0.999 else ''
    filters.append(
        master_label
        + FINAL_LEVELER_FILTER + ','
          'alimiter=limit=0.95:attack=30:release=520,'
          'loudnorm=I=-18:TP=-2.0:LRA=8'
        + post_level + ending + '[out]'
    )


def probe_audio_duration(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-500:] or "FFprobe failed.")
    return max(0.01, float(result.stdout.strip()))


def atempo_chain(speed):
    """Build a valid FFmpeg atempo chain for speed factors above 1."""
    factors = []
    remaining = max(1.0, float(speed))
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    if remaining > 1.001:
        factors.append(remaining)
    return ",".join(f"atempo={value:.5f}" for value in factors)


def create_mp3(srt_text, progress_callback=None, background_music_path=None, ducking_config=None, target_language="Khmer (ខ្មែរ)"):
    """
    Create one synchronized MP3 in the selected target language.

    v3.0 rules:
    - Every voice starts at the original SRT start timestamp.
    - A clip is fitted inside the time available before the next cue.
    - Generated voices never overlap or compete with one another.
    - Breathy high frequencies are reduced without making speech muddy.
    - Loudness is mastered once at the end instead of aggressively per clip.
    """
    cues = parse_srt(srt_text)
    if not cues:
        raise ValueError('No valid SRT with timestamps was found.')

    selected_target = normalized_target_language(target_language)
    invalid_rows = [
        i + 1 for i, cue in enumerate(cues)
        if not is_valid_target_dialogue(cue['text'], selected_target)
    ]
    if invalid_rows:
        raise ValueError(
            f'SRT does not match the selected target language in cue(s): {invalid_rows[:20]}. '
            'Translate the SRT again before creating MP3.'
        )
    for cue in cues:
        cue['tag'] = normalize_voice_tag(cue.get('tag', 'M'))
    render_cues = coalesce_continuation_cues(cues)

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        clips = [None] * len(render_cues)
        clip_durations = [0.0] * len(render_cues)
        total_cues = len(render_cues)

        if progress_callback:
            progress_callback(2, "Preparing character voices…")

        def create_voice_clip(index, cue):
            clip = root / f'clip_{index:04d}.mp3'
            profile = voice_profile_for_target_language(cue['tag'], selected_target)
            run_async(synthesize(cue['text'], profile, clip))
            return index, clip, probe_audio_duration(clip)

        # A small pool makes Edge-TTS much faster while avoiding excessive requests.
        workers = min(3, total_cues)
        completed = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(create_voice_clip, index, cue) for index, cue in enumerate(render_cues)]
            for future in as_completed(futures):
                index, clip, duration = future.result()
                clips[index] = clip
                clip_durations[index] = duration
                completed += 1
                if progress_callback:
                    percent = 5 + int((completed / total_cues) * 82)
                    progress_callback(
                        min(percent, 87),
                        f"Creating voices {completed}/{total_cues}…",
                    )

        config = normalized_ducking_config(ducking_config)
        music_path = Path(background_music_path) if background_music_path else None
        use_ducking = bool(
            music_path and music_path.exists() and music_path.is_file() and config['enabled']
        )
        command = ['ffmpeg', '-y']
        for clip in clips:
            command.extend(['-i', str(clip)])
        music_input_index = None
        if use_ducking:
            music_input_index = len(clips)
            command.extend(['-stream_loop', '-1', '-i', str(music_path)])

        filters = []
        labels = []
        final_end_ms = 0
        previous_voice_end_ms = 0

        for index, cue in enumerate(render_cues):
            start_ms = max(0, int(cue['start']))
            cue_end_ms = max(start_ms + 250, int(cue['end']))

            audio_seconds = clip_durations[index]

            # Never chop a Khmer sentence or force it to rush.  When an SRT cue is
            # shorter than the natural Neural voice, continue that cue in sequence
            # instead of cutting its final words; the next speaker begins after a
            # tiny 24 ms hand-off that prevents overlap but still feels connected.
            render_start_ms = start_ms if index == 0 else max(start_ms, previous_voice_end_ms - 24)
            trim_seconds = audio_seconds

            # Short fades remove digital clicks without audibly shrinking phrases.
            fade_in = min(VOICE_FADE_IN_SECONDS, max(0.006, trim_seconds * 0.012))
            fade_out = min(VOICE_FADE_OUT_SECONDS, max(0.010, trim_seconds * 0.018))
            fade_out_start = max(0.01, trim_seconds - fade_out)

            label = f'a{index}'
            parts = [f'[{index}:a]asetpts=PTS-STARTPTS']

            # Apply the same gentle speech-cleanup chain to every cue.
            parts.extend([
                *voice_tone_filters(cue.get('tag', 'M')),
                f'atrim=0:{trim_seconds:.3f}',
                'asetpts=PTS-STARTPTS',
                f'afade=t=in:st=0:d={fade_in:.3f}',
                f'afade=t=out:st={fade_out_start:.3f}:d={fade_out:.3f}',
                f'adelay={render_start_ms}|{render_start_ms}[{label}]',
            ])

            filters.append(','.join(parts).replace('],', ']'))
            labels.append(f'[{label}]')
            previous_voice_end_ms = render_start_ms + int(trim_seconds * 1000)
            final_end_ms = max(final_end_ms, previous_voice_end_ms, cue_end_ms)

        total = (final_end_ms + 350) / 1000.0

        # Mix voices first, then optionally duck the music with the voice signal.
        # The same slow final master is applied in both paths, so no-music output
        # remains compatible with previous versions.
        filters.append(
            ''.join(labels)
            + f'amix=inputs={len(labels)}:duration=longest:dropout_transition=0:normalize=0[voice_raw]'
        )
        all_thought = bool(render_cues) and all(
            cue.get('tag') in {'M_THINK', 'F_THINK'} for cue in render_cues
        )
        append_audio_master_filters(
            filters, '[voice_raw]', total_seconds=total,
            music_input_index=music_input_index, ducking_config=config,
            post_master_gain=THOUGHT_VOICE_GAIN if all_thought else 1.0,
        )

        output = root / 'khmer_dubbed.mp3'
        command.extend([
            '-filter_complex', ';'.join(filters),
            '-map', '[out]',
            '-c:a', 'libmp3lame',
            '-ac', '2',
            '-ar', '48000',
            '-b:a', '192k',
            str(output),
        ])

        if progress_callback:
            progress_callback(
                92,
                "Mixing voices and automatically ducking music…"
                if use_ducking else "Combining all voices into one MP3…",
            )

        result = subprocess.run(command, capture_output=True, text=True, timeout=900)
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-2200:] or 'FFmpeg failed.')
        if not output.exists() or output.stat().st_size < 1000:
            raise RuntimeError('MP3 was created but does not contain enough audio.')

        if progress_callback:
            progress_callback(100, "MP3 created successfully")
        return output.read_bytes()


def create_single_voice_mp3(text, tag, background_music_path=None, ducking_config=None, target_language="Khmer (ខ្មែរ)"):
    """Create a polished standalone MP3 in the selected language with optional private music ducking."""
    canonical_tag = normalize_voice_tag(tag)
    selected_target = normalized_target_language(target_language)
    if not is_valid_target_dialogue(text, selected_target):
        raise ValueError("The text does not match the selected target language.")
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        raw = root / 'raw_edge_tts.mp3'
        output = root / 'khmer_voice.mp3'
        run_async(synthesize(text, voice_profile_for_target_language(canonical_tag, selected_target), raw))
        total = probe_audio_duration(raw)
        config = normalized_ducking_config(ducking_config)
        music_path = Path(background_music_path) if background_music_path else None
        use_ducking = bool(
            music_path and music_path.exists() and music_path.is_file() and config['enabled']
        )
        command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(raw)]
        music_input_index = None
        if use_ducking:
            music_input_index = 1
            command.extend(['-stream_loop', '-1', '-i', str(music_path)])
        filters = [
            '[0:a]asetpts=PTS-STARTPTS,'
            + ','.join(voice_tone_filters(canonical_tag))
            + '[voice_raw]'
        ]
        append_audio_master_filters(
            filters, '[voice_raw]', total_seconds=total,
            music_input_index=music_input_index, ducking_config=config,
            post_master_gain=THOUGHT_VOICE_GAIN if canonical_tag in {'M_THINK', 'F_THINK'} else 1.0,
        )
        command.extend([
            '-filter_complex', ';'.join(filters), '-map', '[out]',
            '-c:a', 'libmp3lame', '-ac', '2', '-ar', '48000', '-b:a', '192k', str(output),
        ])
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        if result.returncode != 0 or not output.exists() or output.stat().st_size < 1000:
            raise RuntimeError(result.stderr[-1600:] or 'Could not master the MP3 audio.')
        return output.read_bytes()


def render_thought_voice_guide():
    """Show a compact, practical guide wherever customers choose a voice tag."""
    with st.expander("📘 How to Use [M_THINK] and [F_THINK]", expanded=False):
        st.markdown(
            "Use **[M_THINK]** for a male character’s inner thought and "
            "**[F_THINK]** for a female character’s inner thought. "
            "Use these only when the character is thinking silently or cannot be heard by others in the scene."
        )
        st.markdown(
            "Put the tag at the beginning of the line and keep the phrase short and smooth. Do not use `_THINK` "
            "for dialogue spoken aloud. Inner-thought voices are softer, without echo or a hollow effect."
        )
        st.code(
            """3
00:00:06,250 --> 00:00:08,700
[M_THINK] ខ្ញុំមិនអាចប្រាប់អូនពីរឿងពិតឥឡូវនេះបានទេ។

4
00:00:09,050 --> 00:00:11,200
[F_THINK] សង្ឃឹមថាគាត់មិនលាក់រឿងសំខាន់ពីខ្ញុំទេ។""",
            language="srt",
        )
        st.caption("Tip: Give each cue enough time and avoid overly long phrases to keep TTS rhythm natural.")


# ─────────────────────────────────────────────────────────────────────────────
# PRIVATE CUSTOMER LOGIN + HIDDEN OWNER LICENSE MANAGEMENT
# This module adds security only. The original app UI/workflow below is unchanged.
# ─────────────────────────────────────────────────────────────────────────────
LICENSE_DB_PATH = Path(__file__).with_name("licenses.db")
SESSION_COOKIE_NAME = "ai_khemra_bro_customer_session"
LOGIN_COOKIE_NAME = "ai_khemra_bro_saved_login"
SESSION_IDLE_MINUTES = 30
LOGIN_WINDOW_MINUTES = 15
MAX_LOGIN_ATTEMPTS = 5
NEW_LICENSE_CARD_HOURS = 24


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(value=None):
    return (value or _utcnow()).isoformat(timespec="seconds")


def _parse_iso(value):
    parsed = datetime.datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def _secret(name, default=""):
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return str(default).strip()


def get_admin_username():
    return _secret("ADMIN_USERNAME", "KHEMRA")


def get_admin_password():
    # Works immediately even before Streamlit Secrets are configured.
    # For production, set ADMIN_PASSWORD in Streamlit Secrets to override this bootstrap value.
    return _secret("ADMIN_PASSWORD", "0719067125")


def license_connection():
    connection = sqlite3.connect(str(LICENSE_DB_PATH), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def _ensure_column(connection, table, column, definition):
    names = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
    if column not in names:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def initialize_license_database():
    with license_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                access_code_hash TEXT UNIQUE,
                access_code_display TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                last_login_at TEXT,
                login_count INTEGER NOT NULL DEFAULT 0,
                active_session_hash TEXT,
                active_session_last_seen TEXT,
                created_card_until TEXT
            )
            """
        )
        # Safe migration from older versions of the same app.
        _ensure_column(connection, "licenses", "access_code_hash", "TEXT")
        _ensure_column(connection, "licenses", "access_code_display", "TEXT")
        _ensure_column(connection, "licenses", "active_session_hash", "TEXT")
        _ensure_column(connection, "licenses", "active_session_last_seen", "TEXT")
        _ensure_column(connection, "licenses", "created_card_until", "TEXT")
        _ensure_column(connection, "licenses", "saved_api_keys_encrypted", "TEXT")
        _ensure_column(connection, "licenses", "saved_translation_preferences_encrypted", "TEXT")
        _ensure_column(connection, "licenses", "plan_label", "TEXT")
        old_columns = {row["name"] for row in connection.execute("PRAGMA table_info(licenses)")}
        if "access_code" in old_columns:
            rows = connection.execute(
                "SELECT id, access_code, access_code_hash, access_code_display FROM licenses"
            ).fetchall()
            for row in rows:
                raw = normalize_access_code(row["access_code"])
                if raw:
                    connection.execute(
                        "UPDATE licenses SET access_code_hash=COALESCE(access_code_hash, ?), "
                        "access_code_display=CASE WHEN access_code_display IS NULL OR access_code_display='' THEN ? ELSE access_code_display END "
                        "WHERE id=?",
                        (_hash_code(raw), raw, row["id"]),
                    )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_key TEXT NOT NULL,
                attempted_at TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_key_time ON login_attempts(attempt_key, attempted_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(event_at)")
        connection.commit()


def normalize_customer_name(value):
    return " ".join(str(value or "").strip().split())[:80]


def normalize_access_code(value):
    return re.sub(r"[^A-Z0-9-]", "", str(value or "").strip().upper())[:48]


def _hash_code(code):
    # Keep the original fallback stable so existing license hashes remain valid.
    # A dedicated LICENSE_PEPPER in Streamlit Secrets takes priority when configured.
    pepper = _secret("LICENSE_PEPPER", LEGACY_COOKIE_SECRET)
    return hmac.new(pepper.encode("utf-8"), code.encode("utf-8"), hashlib.sha256).hexdigest()


def _hash_session(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _audit(event_type, actor, details=""):
    with license_connection() as connection:
        connection.execute(
            "INSERT INTO audit_log(event_at,event_type,actor,details) VALUES(?,?,?,?)",
            (_iso(), str(event_type)[:60], str(actor)[:100], str(details)[:500]),
        )
        connection.commit()


def _attempt_key(name, code):
    return hashlib.sha256(f"{name.casefold()}|{_hash_code(code)}".encode("utf-8")).hexdigest()


def _login_blocked(attempt_key):
    cutoff = _iso(_utcnow() - datetime.timedelta(minutes=LOGIN_WINDOW_MINUTES))
    with license_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS c FROM login_attempts WHERE attempt_key=? AND attempted_at>=? AND success=0",
            (attempt_key, cutoff),
        ).fetchone()["c"]
    return count >= MAX_LOGIN_ATTEMPTS


def _record_login_attempt(attempt_key, success):
    with license_connection() as connection:
        connection.execute(
            "INSERT INTO login_attempts(attempt_key,attempted_at,success) VALUES(?,?,?)",
            (attempt_key, _iso(), 1 if success else 0),
        )
        # Keep the DB compact.
        cutoff = _iso(_utcnow() - datetime.timedelta(days=7))
        connection.execute("DELETE FROM login_attempts WHERE attempted_at < ?", (cutoff,))
        connection.commit()


def validate_manual_access_code(value):
    """Validate an owner-selected reusable access code."""
    code = normalize_access_code(value)
    if not code:
        raise ValueError("Enter the Access Code you want to assign.")
    if len(code) < 4 or len(code) > 64:
        raise ValueError("Access Code must be between 4 and 64 characters.")
    if not re.fullmatch(r"[A-Z0-9_-]+", code):
        raise ValueError("Access Code may use only A-Z, 0-9, hyphens, and underscores.")
    return code


def add_license(customer_name, access_code, duration_days, plan_label=""):
    name = normalize_customer_name(customer_name)
    if not name:
        raise ValueError("Enter the customer name.")

    days = int(duration_days)
    allowed_plans = {
        7: "7 Days",
        30: "1 Month",
        90: "3 Months",
        180: "6 Months",
        365: "1 Year",
    }
    if days not in allowed_plans:
        raise ValueError("Invalid plan duration.")

    plan = str(plan_label or allowed_plans[days]).strip()
    now = _utcnow()
    expires = now + datetime.timedelta(days=days)
    card_until = now + datetime.timedelta(hours=NEW_LICENSE_CARD_HOURS)
    code = validate_manual_access_code(access_code)

    with license_connection() as connection:
        duplicate = connection.execute(
            "SELECT 1 FROM licenses WHERE access_code_hash=? OR access_code_display=?",
            (_hash_code(code), code),
        ).fetchone()
        if duplicate:
            raise ValueError("This Access Code already exists. Choose a different code.")
        connection.execute(
            """
            INSERT INTO licenses
            (customer_name, access_code_hash, access_code_display, created_at, expires_at,
             is_active, created_card_until, plan_label)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                name,
                _hash_code(code),
                code,
                _iso(now),
                _iso(expires),
                _iso(card_until),
                plan,
            ),
        )
        connection.commit()

    _audit("license_created", get_admin_username(), f"{name}|{plan}|{days} days")
    return code, expires, card_until


def _session_cookie_get():
    try:
        encrypted = cookie_manager.get(SESSION_COOKIE_NAME)
        return decrypt_api_keys(encrypted) if encrypted else ""
    except Exception:
        return ""


def _session_cookie_set(token):
    try:
        cookie_manager.set(
            SESSION_COOKIE_NAME,
            encrypt_api_keys(token),
            expires_at=datetime.datetime.now() + datetime.timedelta(days=365),
            key="save_customer_session_cookie",
        )
    except Exception:
        pass


def _session_cookie_delete():
    try:
        cookie_manager.delete(SESSION_COOKIE_NAME, key="delete_customer_session_cookie")
    except Exception:
        pass


def _saved_login_get():
    """Return encrypted saved customer credentials for automatic login."""
    try:
        encrypted = cookie_manager.get(LOGIN_COOKIE_NAME)
        if not encrypted:
            return "", ""
        payload = decrypt_api_keys(encrypted)
        data = json.loads(payload)
        return str(data.get("name", "")), str(data.get("code", ""))
    except Exception:
        return "", ""


def _saved_login_set(name, code):
    """Remember this customer's login on this browser until explicit logout."""
    try:
        payload = json.dumps({"name": str(name or ""), "code": str(code or "")}, ensure_ascii=False)
        cookie_manager.set(
            LOGIN_COOKIE_NAME,
            encrypt_api_keys(payload),
            expires_at=datetime.datetime.now() + datetime.timedelta(days=3650),
            key="save_customer_login_cookie",
        )
    except Exception:
        pass


def _saved_login_delete():
    try:
        cookie_manager.delete(LOGIN_COOKIE_NAME, key="delete_customer_login_cookie")
    except Exception:
        pass


def validate_customer_login(customer_name, access_code, existing_token="", acquire_session=False):
    """Validate a customer license without binding it to a device or browser.

    A valid, active, unexpired access code may be used again after logout,
    browser close, phone restart, or from another phone. The customer name is
    kept for display but the access code is the authentication credential.
    """
    entered_name = normalize_customer_name(customer_name)
    code = normalize_access_code(access_code)
    if not code:
        return False, "Enter an Access Code.", None, ""

    attempt_key = _attempt_key(entered_name or "code-user", code)
    if acquire_session and _login_blocked(attempt_key):
        return False, f"Too many attempts. Please wait {LOGIN_WINDOW_MINUTES} minutes.", None, ""

    now = _utcnow()
    code_hash = _hash_code(code)
    failure_reason = ""
    fresh = None
    token = existing_token or secrets.token_urlsafe(32)

    with license_connection() as connection:
        row = connection.execute(
            "SELECT * FROM licenses WHERE access_code_hash=? OR access_code_display=?",
            (code_hash, code),
        ).fetchone()

        if row is None:
            failure_reason = "Invalid Access Code."
        elif not bool(row["is_active"]):
            failure_reason = "This Access Code has been disabled by the owner."
        elif now >= _parse_iso(row["expires_at"]):
            failure_reason = "Your plan has expired. Contact the owner to renew access."
        else:
            # No device lock and no single-session lock. A purchased code can
            # be reused after logout/close and can work on any phone/browser.
            if acquire_session:
                connection.execute(
                    """
                    UPDATE licenses
                    SET active_session_hash=NULL,
                        active_session_last_seen=NULL,
                        last_login_at=?,
                        login_count=login_count+1
                    WHERE id=?
                    """,
                    (_iso(now), row["id"]),
                )
            else:
                connection.execute(
                    "UPDATE licenses SET active_session_hash=NULL, active_session_last_seen=NULL WHERE id=?",
                    (row["id"],),
                )
            connection.commit()
            fresh = connection.execute("SELECT * FROM licenses WHERE id=?", (row["id"],)).fetchone()

    if acquire_session:
        _record_login_attempt(attempt_key, not bool(failure_reason))
    if failure_reason:
        return False, failure_reason, None, ""

    display_name = str(fresh["customer_name"] or entered_name or "Customer")
    if acquire_session:
        _audit("customer_login", display_name, "success|multi-device")
    return True, "", dict(fresh), token


def release_customer_session(access_code, token, actor="customer"):
    """Log out this browser only; never block reuse of the purchased code."""
    code = normalize_access_code(access_code)
    with license_connection() as connection:
        row = connection.execute(
            "SELECT id,customer_name FROM licenses WHERE access_code_hash=? OR access_code_display=?",
            (_hash_code(code), code),
        ).fetchone()
        if row:
            connection.execute(
                "UPDATE licenses SET active_session_hash=NULL, active_session_last_seen=NULL WHERE id=?",
                (row["id"],),
            )
            connection.commit()
            _audit("customer_logout", actor, row["customer_name"])


def license_rows(search_text=""):
    query = "SELECT * FROM licenses"
    params = []
    if search_text.strip():
        query += " WHERE customer_name LIKE ? OR access_code_display LIKE ?"
        needle = f"%{search_text.strip()}%"
        params = [needle, needle]
    query += " ORDER BY id DESC"
    with license_connection() as connection:
        return connection.execute(query, params).fetchall()


def update_license_status(license_id, active):
    with license_connection() as connection:
        connection.execute(
            "UPDATE licenses SET is_active=?, active_session_hash=NULL, active_session_last_seen=NULL WHERE id=?",
            (1 if active else 0, int(license_id)),
        )
        connection.commit()
    _audit("license_status", get_admin_username(), f"id={license_id}|active={bool(active)}")


def renew_license(license_id, extra_days, plan_label=""):
    allowed_plans = {
        7: "7 Days",
        30: "1 Month",
        90: "3 Months",
        180: "6 Months",
        365: "1 Year",
    }
    days = int(extra_days)
    if days not in allowed_plans:
        raise ValueError("Invalid renewal duration.")

    with license_connection() as connection:
        row = connection.execute(
            "SELECT expires_at,customer_name FROM licenses WHERE id=?",
            (int(license_id),),
        ).fetchone()
        if not row:
            raise ValueError("Customer not found.")

        now = _utcnow()
        current_expiry = _parse_iso(row["expires_at"])
        base = max(current_expiry, now)
        new_expiry = base + datetime.timedelta(days=days)
        plan = str(plan_label or allowed_plans[days]).strip()

        connection.execute(
            """
            UPDATE licenses
            SET expires_at=?, is_active=1, plan_label=?
            WHERE id=?
            """,
            (_iso(new_expiry), plan, int(license_id)),
        )
        connection.commit()

    _audit("license_renewed", get_admin_username(), f"{row['customer_name']}|{plan}|+{days}")


def disconnect_license(license_id):
    with license_connection() as connection:
        connection.execute(
            "UPDATE licenses SET active_session_hash=NULL,active_session_last_seen=NULL WHERE id=?",
            (int(license_id),),
        )
        connection.commit()
    _audit("session_disconnected", get_admin_username(), f"id={license_id}")


def delete_license(license_id):
    with license_connection() as connection:
        row = connection.execute("SELECT customer_name FROM licenses WHERE id=?", (int(license_id),)).fetchone()
        connection.execute("DELETE FROM licenses WHERE id=?", (int(license_id),))
        connection.commit()
    _audit("license_deleted", get_admin_username(), row["customer_name"] if row else str(license_id))


LICENSE_BACKUP_SCHEMA_VERSION = 1


def export_license_backup():
    """Export owner-controlled customer codes only; no customer or app API key is included."""
    columns = (
        "customer_name,access_code_display,created_at,expires_at,is_active,"
        "login_count,created_card_until,plan_label"
    )
    with license_connection() as connection:
        rows = connection.execute(f"SELECT {columns} FROM licenses ORDER BY id").fetchall()
    records = [dict(row) for row in rows if normalize_access_code(row["access_code_display"])]
    payload = {
        "schema_version": LICENSE_BACKUP_SCHEMA_VERSION,
        "created_at": _iso(),
        "record_count": len(records),
        "licenses": records,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def restore_license_backup(backup_bytes):
    """Import only missing Access Codes; existing codes are never overwritten or regenerated."""
    try:
        payload = json.loads(bytes(backup_bytes or b"").decode("utf-8-sig"))
    except Exception as exc:
        raise ValueError("Invalid backup JSON.") from exc
    if not isinstance(payload, dict) or int(payload.get("schema_version", 0)) != LICENSE_BACKUP_SCHEMA_VERSION:
        raise ValueError("Unsupported backup version.")
    records = payload.get("licenses")
    if not isinstance(records, list) or len(records) > 10000:
        raise ValueError("Backup does not contain a valid Access Code list.")

    imported = 0
    skipped = 0
    with license_connection() as connection:
        for record in records:
            if not isinstance(record, dict):
                skipped += 1
                continue
            try:
                code = validate_manual_access_code(record.get("access_code_display", ""))
                name = normalize_customer_name(record.get("customer_name", ""))
                if not name:
                    raise ValueError("empty name")
                duplicate = connection.execute(
                    "SELECT 1 FROM licenses WHERE access_code_hash=? OR access_code_display=?",
                    (_hash_code(code), code),
                ).fetchone()
                if duplicate:
                    skipped += 1
                    continue
                created_at = _iso(_parse_iso(record.get("created_at")))
                expires_at = _iso(_parse_iso(record.get("expires_at")))
                card_value = str(record.get("created_card_until") or "").strip()
                card_until = _iso(_parse_iso(card_value)) if card_value else None
                plan = str(record.get("plan_label") or "Member Plan").strip()[:80]
                login_count = max(0, min(int(record.get("login_count", 0)), 100000000))
                connection.execute(
                    """
                    INSERT INTO licenses
                    (customer_name,access_code_hash,access_code_display,created_at,expires_at,
                     is_active,login_count,created_card_until,plan_label)
                    VALUES (?,?,?,?,?,?,?,?,?)
                    """,
                    (name, _hash_code(code), code, created_at, expires_at,
                     1 if bool(record.get("is_active", True)) else 0, login_count, card_until, plan),
                )
                imported += 1
            except Exception:
                skipped += 1
        connection.commit()
    _audit("license_backup_restored", get_admin_username(), f"imported={imported}|skipped={skipped}")
    return {"imported": imported, "skipped": skipped}


def hidden_owner_trigger():
    if "owner_click_count" not in st.session_state:
        st.session_state.owner_click_count = 0
    if "admin_gate_visible" not in st.session_state:
        st.session_state.admin_gate_visible = False
    with st.container(key="owner_trigger_container"):
        clicked = st.button("✦", key="owner_trigger", help="AI KHEMRA BRO")
    if clicked:
        st.session_state.owner_click_count += 1
        if st.session_state.owner_click_count >= 5:
            st.session_state.owner_click_count = 0
            st.session_state.admin_gate_visible = True
            st.rerun()



def render_private_subscription_countdown(expiry_datetime, plan_label, customer_name="", access_code=""):
    """Render only the signed-in customer's stylish subscription summary card."""
    import streamlit.components.v1 as components

    expiry_iso = expiry_datetime.astimezone(datetime.timezone.utc).isoformat()
    safe_plan = re.sub(r"[^0-9A-Za-z\u1780-\u17FF .\-]", "", str(plan_label or "Member Plan"))
    safe_name = re.sub(r"[^0-9A-Za-z\u1780-\u17FF .\-]", "", str(customer_name or "Member"))
    safe_code = re.sub(r"[^0-9A-Za-z\-]", "", str(access_code or ""))

    components.html(
        f"""
        <div id="khbr-card" class="khbr-countdown-card" aria-label="Your subscription information">
          <div class="khbr-card-top"><span class="khbr-live-dot"></span><span>Your Account</span></div>
          <div class="khbr-name">👋 {safe_name or "Member"}</div>
          <div class="khbr-meta"><span>🏷️ {safe_plan or "Member Plan"}</span>{f'<span>• Code {safe_code}</span>' if safe_code else ''}</div>
          <div class="khbr-expiry-row"><span class="khbr-calendar">🗓️</span><span>Expires</span><strong id="khbr-expiry">Calculating…</strong></div>
          <div class="khbr-remaining"><strong id="khbr-days">—</strong><span>Days Left</span></div>
          <div id="khbr-detail" class="khbr-detail">Calculating…</div>
        </div>
        <style>
          html,body{{margin:0;padding:0;background:transparent;font-family:Arial,"Noto Sans Khmer",sans-serif}}
          .khbr-countdown-card{{
            min-height:246px; box-sizing:border-box; border-radius:22px; padding:17px 16px 15px;
            color:#f8fafc; border:2px solid #22d3ee; background:linear-gradient(145deg,#172236 0%,#0d1525 100%);
            box-shadow:0 0 0 1px rgba(34,211,238,.18),0 14px 30px rgba(2,8,23,.44); text-align:left;
          }}
          .khbr-card-top{{display:flex;align-items:center;gap:7px;color:#67e8f9;font-size:12px;font-weight:900;letter-spacing:.7px;text-transform:uppercase}}
          .khbr-live-dot{{width:8px;height:8px;border-radius:50%;background:#34d399;box-shadow:0 0 0 4px rgba(52,211,153,.12)}}
          .khbr-name{{font-size:clamp(22px,6.8vw,28px);line-height:1.2;font-weight:950;margin:12px 0 5px;overflow-wrap:anywhere}}
          .khbr-meta{{display:flex;flex-wrap:wrap;gap:5px;color:#cbd5e1;font-size:13px;font-weight:750;line-height:1.4}}
          .khbr-expiry-row{{display:grid;grid-template-columns:auto 1fr auto;gap:7px;align-items:center;margin-top:14px;padding:10px 11px;border-radius:12px;background:rgba(15,23,42,.72);border:1px solid rgba(148,163,184,.24);font-size:12px;color:#cbd5e1}}
          .khbr-calendar{{font-size:16px}} .khbr-expiry-row strong{{color:#fff;font-size:13px;white-space:nowrap}}
          .khbr-remaining{{display:flex;align-items:baseline;gap:9px;margin-top:13px}}
          .khbr-remaining strong{{font-size:clamp(36px,11vw,50px);line-height:1;color:#67e8f9;letter-spacing:-1px}}
          .khbr-remaining span{{font-size:17px;font-weight:950;color:#f8fafc}}
          .khbr-detail{{margin-top:5px;font-size:13px;font-weight:750;color:#94a3b8}}
          .khbr-countdown-card.is-expired{{border-color:#fb7185;box-shadow:0 0 0 1px rgba(251,113,133,.2),0 14px 30px rgba(2,8,23,.44)}}
          .khbr-countdown-card.is-expired .khbr-remaining strong{{color:#fda4af}}
          @media(max-width:360px){{.khbr-countdown-card{{padding:15px 13px;min-height:238px}}.khbr-expiry-row{{grid-template-columns:auto 1fr;}}.khbr-expiry-row strong{{grid-column:2;white-space:normal}}}}
        </style>
        <script>
          const end = new Date({expiry_iso!r});
          const cardNode = document.getElementById("khbr-card");
          const daysNode = document.getElementById("khbr-days");
          const detailNode = document.getElementById("khbr-detail");
          const expiryNode = document.getElementById("khbr-expiry");

          function two(n) {{ return String(n).padStart(2, "0"); }}

          function updateCountdown() {{
            const now = new Date();
            let ms = end.getTime() - now.getTime();

            expiryNode.textContent =
              "Expires: " +
              two(end.getDate()) + "/" +
              two(end.getMonth()+1) + "/" +
              end.getFullYear() + " " +
              two(end.getHours()) + ":" +
              two(end.getMinutes());

            const minute = 60 * 1000;
            const hour = 60 * minute;
            const day = 24 * hour;
            if (ms <= 0) {{
              cardNode.classList.add("is-expired");
              daysNode.textContent = "0";
              detailNode.textContent = "Plan expired";
              return;
            }}

            cardNode.classList.remove("is-expired");
            const days = Math.floor(ms / day);
            ms %= day;
            const hours = Math.floor(ms / hour);
            ms %= hour;
            const minutes = Math.floor(ms / minute);
            daysNode.textContent = String(days);
            detailNode.textContent = two(hours) + "h " + two(minutes) + "m remaining";
          }}

          updateCountdown();
          // Refresh only once per minute: the card remains calm and avoids jumping seconds.
          setInterval(updateCountdown, 60000);
        </script>
        """,
        height=258,
        scrolling=False,
    )

def public_login_screen():
    st.markdown(
        '<div class="hero"><h1>AI KHEMRA BRO</h1><p>PRIVATE CUSTOMER ACCESS</p></div>',
        unsafe_allow_html=True,
    )

    with st.container(key="public_login_wrap"):
        st.markdown("### 🔐 Customer Access")

        with st.container(key="customer_login_box"):
            with st.form("customer_login_form", clear_on_submit=False):
                name = st.text_input(
                    "Name (optional)",
                    placeholder="Leave blank if not needed",
                )
                code = st.text_input(
                    "Access Code",
                    placeholder="KHBR-XXXX-XXXX",
                    type="password",
                )
                submitted = st.form_submit_button(
                    "Open App",
                    use_container_width=True,
                )

        if submitted:
            existing = _session_cookie_get()
            ok, message, row, token = validate_customer_login(
                name,
                code,
                existing,
                acquire_session=True,
            )
            if ok:
                _session_cookie_set(token)
                _saved_login_set(row["customer_name"], row["access_code_display"])
                st.session_state.customer_authenticated = True
                st.session_state.customer_name = row["customer_name"]
                st.session_state.customer_code = row["access_code_display"]
                st.session_state.customer_session_token = token
                st.rerun()
            else:
                st.error(message)

        # Real clickable links: one locked 50% / 50% row on every phone size.
        st.markdown(
            """
            <div class="social-split">
              <a href="https://www.facebook.com/Khrmra?mibextid=wwXIfr&mibextid=wwXIfr" target="_blank" rel="noopener noreferrer"
                 aria-label="Open KHEMRA Facebook">
                <span class="social-icon">f</span>
                <span>Facebook</span>
              </a>
              <a href="https://t.me/+VC_6B66uwH5hMDE9" target="_blank" rel="noopener noreferrer"
                 aria-label="Open KHEMRA Telegram">
                <span class="social-icon">➤</span>
                <span>Telegram</span>
              </a>
            </div>
            <div class="login-help">
              Contact the owner to receive an <strong>Access Code</strong>
              for app access.
            </div>
            """,
            unsafe_allow_html=True,
        )


def _copy_card(name, code, expires_text):
    import html
    safe_name = html.escape(str(name))
    safe_code = html.escape(str(code))
    safe_expiry = html.escape(str(expires_text))
    payload = f"Name: {name}\nCode: {code}"
    safe_payload = payload.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    import streamlit.components.v1 as components
    components.html(
        f"""
        <div style="font-family:Arial,sans-serif;background:#0f172a;color:white;border:1px solid #22d3ee;border-radius:14px;padding:14px;margin:4px 0 10px">
          <div style="font-weight:800;margin-bottom:7px">Name: {safe_name}</div>
          <div style="font-weight:800;margin-bottom:7px">Code: {safe_code}</div>
          <div style="opacity:.8;margin-bottom:10px">Expires: {safe_expiry}</div>
          <button onclick="navigator.clipboard.writeText(`{safe_payload}`).then(()=>this.innerText='✅ COPIED')"
            style="width:100%;padding:11px;border:0;border-radius:9px;background:linear-gradient(90deg,#0284c7,#22d3ee);color:white;font-weight:900">COPY NAME + CODE</button>
        </div>
        """,
        height=176,
    )


def admin_dashboard():
    st.markdown('<div class="hero"><h1>AI KHEMRA BRO</h1><p>PRIVATE OWNER MANAGEMENT</p></div>', unsafe_allow_html=True)
    admin_password = get_admin_password()

    if not st.session_state.get("admin_authenticated", False):
        left, center, right = st.columns([1, 1.25, 1])
        with center:
            st.markdown("### 👑 Owner Access")
            with st.form("admin_login_form"):
                username = st.text_input("Username", autocomplete="off")
                password = st.text_input("Password", type="password", autocomplete="off")
                submitted = st.form_submit_button("Open Owner Dashboard", use_container_width=True)
            if submitted:
                name_ok = hmac.compare_digest(username.strip().casefold(), get_admin_username().casefold())
                pass_ok = hmac.compare_digest(password, admin_password)
                if name_ok and pass_ok:
                    st.session_state.admin_authenticated = True
                    st.session_state.admin_gate_visible = True
                    _audit("admin_login", username.strip(), "success")
                    st.rerun()
                else:
                    _audit("admin_login_failed", username.strip() or "unknown", "failed")
                    st.error("Incorrect username or password.")
            if st.button("← Back to Customer Login", key="close_admin_gate", use_container_width=True):
                st.session_state.admin_gate_visible = False
                st.session_state.owner_click_count = 0
                st.rerun()
        return

    top1, top2 = st.columns([4, 1])
    with top1:
        st.success("👑 Owner signed in")
    with top2:
        if st.button("Log out", key="admin_logout", use_container_width=True):
            _audit("admin_logout", get_admin_username(), "success")
            st.session_state.admin_authenticated = False
            st.session_state.admin_gate_visible = False
            st.session_state.owner_click_count = 0
            st.rerun()

    st.markdown("## 🛡️ API & Access Code Security")
    with st.expander("🔐 API Key Status & Access Code Backup", expanded=False):
        server_keys = [line for line in load_secret_gemini_api_keys().splitlines() if line]
        if server_keys:
            st.success(f"✅ App API keys available from Streamlit Secrets: {len(server_keys)}")
        else:
            st.warning("⚠️ No App API key found in Streamlit Secrets.")
        st.caption(
            "API key values are never shown or stored in the Owner dashboard. "
            "To change an App API key, update GEMINI_API_KEYS directly in Streamlit Secrets."
        )
        st.divider()
        st.markdown("#### 💾 Backup Access Code")
        st.caption(
            "Download a backup before an update or reboot. It contains names, Access Codes, plans, and expiry dates, "
            "but never API keys. Keep this file private and do not share it."
        )
        st.download_button(
            "⬇️ Download Access Code Backup", export_license_backup(),
            file_name="ai_khemra_access_code_backup.json", mime="application/json",
            key="download_license_backup", use_container_width=True,
        )
        restore_file = st.file_uploader(
            "Restore Backup (JSON)", type=["json"], key="restore_license_backup_file",
            help="Restore imports only codes that do not already exist. Existing codes are never overwritten or regenerated.",
        )
        if st.button("↥ Restore Missing Codes", key="restore_license_backup", disabled=restore_file is None, use_container_width=True):
            try:
                result = restore_license_backup(restore_file.getvalue())
                st.success(f"✅ Imported {result['imported']} code(s) • Skipped {result['skipped']} existing or invalid code(s)")
            except Exception as exc:
                st.error(f"❌ Restore failed: {exc}")

    st.markdown("## ➕ Create Customer")
    st.caption("The owner creates one Access Code for each customer. A code can be used on iPhone, Android, and different browsers without device locking.")
    with st.form("create_license_form", clear_on_submit=True):
        customer_name = st.text_input("Customer Name")
        manual_access_code = st.text_input(
            "Access Code to Assign",
            placeholder="e.g. KHBR-001 or VIP-2026-001",
            help="Use A-Z, 0-9, hyphens, and underscores. Codes are manual; there is no auto-generation.",
        )
        duration_label = st.selectbox("Duration", ["7 Days", "1 Month", "3 Months", "6 Months", "1 Year"])
        create_clicked = st.form_submit_button("✅ Save Access Code", use_container_width=True)
    if create_clicked:
        days = {"7 Days": 7, "1 Month": 30, "3 Months": 90, "6 Months": 180, "1 Year": 365}[duration_label]
        try:
            code, expires, card_until = add_license(customer_name, manual_access_code, days, duration_label)
            st.session_state.new_license_name = normalize_customer_name(customer_name)
            st.session_state.new_license_code = code
            st.session_state.new_license_expiry = _iso(expires)
            st.session_state.new_license_card_until = _iso(card_until)
        except Exception as exc:
            st.error(str(exc))

    card_until = st.session_state.get("new_license_card_until")
    if card_until and _utcnow() < _parse_iso(card_until):
        expiry_text = _parse_iso(st.session_state.new_license_expiry).astimezone().strftime("%Y-%m-%d %H:%M")
        _copy_card(st.session_state.new_license_name, st.session_state.new_license_code, expiry_text)

    st.markdown("## 👥 Customer Management")
    search = st.text_input("🔎 Search name or code", key="license_search")
    rows = license_rows(search)
    if not rows:
        st.info("No customers yet.")
    now = _utcnow()
    for row in rows:
        expiry = _parse_iso(row["expires_at"])
        expired = now >= expiry
        online = bool(row["active_session_hash"]) and row["active_session_last_seen"] and (now - _parse_iso(row["active_session_last_seen"])) <= datetime.timedelta(minutes=SESSION_IDLE_MINUTES)
        status = "Expired" if expired else "Disabled" if not row["is_active"] else "Online" if online else "Active"
        with st.expander(f"{row['customer_name']} • {row['access_code_display']} • {status}"):
            st.write(f"**Expires:** {expiry.astimezone().strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Logins:** {row['login_count']}")
            st.code(f"Name: {row['customer_name']}\nCode: {row['access_code_display']}", language=None)
            renew_cols = st.columns(5)
            renew_options = [
                ("+7 Days", 7, "7 Days"),
                ("+1 Month", 30, "1 Month"),
                ("+3 Months", 90, "3 Months"),
                ("+6 Months", 180, "6 Months"),
                ("+1 Year", 365, "1 Year"),
            ]
            for renew_col, (button_label, renew_days, plan_name) in zip(renew_cols, renew_options):
                with renew_col:
                    if st.button(
                        button_label,
                        key=f"renew_{renew_days}_{row['id']}",
                        use_container_width=True,
                    ):
                        renew_license(row["id"], renew_days, plan_name)
                        st.rerun()

            action_left, action_middle, action_right = st.columns(3)
            with action_left:
                label = "Disable" if row["is_active"] else "Enable"
                if st.button(label, key=f"toggle_{row['id']}", use_container_width=True):
                    update_license_status(row["id"], not bool(row["is_active"]))
                    st.rerun()
            with action_middle:
                if st.button("Clear Old Session", key=f"disconnect_{row['id']}", use_container_width=True):
                    disconnect_license(row["id"])
                    st.rerun()
            with action_right:
                if st.button("🗑️ Delete Legacy Database API Key", key=f"owner_delete_api_{row['id']}", use_container_width=True):
                    with license_connection() as connection:
                        connection.execute(
                            "UPDATE licenses SET saved_api_keys_encrypted='' WHERE id=?",
                            (int(row["id"]),),
                        )
                        connection.commit()
                    _audit(
                        "owner_deleted_customer_api_key",
                        get_admin_username(),
                        f"{row['customer_name']}|{row['access_code_display']}",
                    )
                    st.success("The legacy database API key was deleted. Customer browser API keys are never shown or affected.")
                    st.rerun()

            with st.expander("⚠️ Advanced Delete"):
                confirmation = st.text_input("Type DELETE to confirm", key=f"delete_confirm_{row['id']}")
                if st.button("Permanently Delete", key=f"delete_{row['id']}", disabled=confirmation != "DELETE", use_container_width=True):
                    delete_license(row["id"]); st.rerun()

    with st.expander("🧾 Audit Log"):
        with license_connection() as connection:
            logs = connection.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 100").fetchall()
        for log in logs:
            st.caption(f"{log['event_at']} • {log['event_type']} • {log['actor']} • {log['details']}")


initialize_license_database()
# Compatibility cleanup: remove historical device/session locks created by older versions.
with license_connection() as _lock_cleanup_connection:
    _lock_cleanup_connection.execute(
        "UPDATE licenses SET active_session_hash=NULL, active_session_last_seen=NULL"
    )
    _lock_cleanup_connection.commit()
hidden_owner_trigger()
if st.session_state.get("admin_gate_visible", False) or st.session_state.get("admin_authenticated", False):
    admin_dashboard()
    st.stop()

if not st.session_state.get("customer_authenticated", False):
    # Restore login automatically after refresh, phone restart, or app update.
    saved_name, saved_code = _saved_login_get()
    if saved_code:
        existing_token = _session_cookie_get()
        auto_ok, _, auto_row, auto_token = validate_customer_login(
            saved_name, saved_code, existing_token, acquire_session=False
        )
        if auto_ok:
            _session_cookie_set(auto_token)
            st.session_state.customer_authenticated = True
            st.session_state.customer_name = auto_row["customer_name"]
            st.session_state.customer_code = auto_row["access_code_display"]
            st.session_state.customer_session_token = auto_token
            st.rerun()
        else:
            _saved_login_delete()
            _session_cookie_delete()
    public_login_screen()
    st.stop()

current_token = st.session_state.get("customer_session_token") or _session_cookie_get()
login_ok, login_message, login_row, current_token = validate_customer_login(
    st.session_state.get("customer_name", ""),
    st.session_state.get("customer_code", ""),
    current_token,
    acquire_session=False,
)
if not login_ok:
    _session_cookie_delete()
    for key in ("customer_authenticated", "customer_name", "customer_code", "customer_session_token"):
        st.session_state.pop(key, None)
    st.error(login_message)
    st.rerun()

st.session_state.customer_session_token = current_token
bind_workspace_to_customer(login_row["access_code_display"])
st.caption(f"👤 Signed in as: {login_row['customer_name']}")

# Read this browser's saved key once per Streamlit session.
if "api_keys_manager" not in st.session_state:
    st.session_state.api_keys_manager = load_private_api_keys()

# Settings are private to this browser/customer, matching the encrypted API-key policy.
preferences_owner = normalize_access_code(login_row["access_code_display"])
if st.session_state.get("private_preferences_owner") != preferences_owner:
    saved_preferences = load_private_translation_preferences(preferences_owner)
    for preference_key in ("target_language", "translation_style", "model_selector"):
        if saved_preferences.get(preference_key):
            st.session_state[preference_key] = saved_preferences[preference_key]
    st.session_state.private_preferences_owner = preferences_owner

# Defaults are per user/session; no user's working data is shared with another.
for state_key, default_value in {
    "target_language": "Khmer (ខ្មែរ)",  # Legacy stored key; displayed as English.
    "source_language": "Auto-detect (ចិន/កូរ៉េ/វៀតណាម/អង់គ្លេស)",  # Legacy stored key; displayed as English.
    "workflow_mode": "⚡ Khmer SRT ស្វ័យប្រវត្តិ",  # Legacy stored key; displayed as English.
    "processing_mode": "⚡ លឿន (ណែនាំ)",  # Legacy stored key; displayed as English.
    "translation_style": "👤 បកប្រែធម្មតា (Standard)",  # Legacy stored key; displayed as English.
    "model_selector": "gemini-3.6-flash",
    "lite_mode": True,
    "api_saved_notice": False,
}.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value

# Migrate saved widget values from earlier releases so an app update never blocks login.
if st.session_state.get("translation_style") not in TRANSLATION_STYLE_OPTIONS:
    st.session_state.translation_style = "👤 បកប្រែធម្មតា (Standard)"
if st.session_state.get("model_selector") not in GEMINI_MODEL_OPTIONS:
    st.session_state.model_selector = "gemini-3.6-flash"
if st.session_state.get("target_language") not in TARGET_LANGUAGE_OPTIONS:
    st.session_state.target_language = "Khmer (ខ្មែរ)"
if st.session_state.get("plain_voice") and st.session_state.get("plain_voice") not in CANONICAL_SRT_TAGS:
    st.session_state.plain_voice = "M"

with st.container(key="api_menu_container"):
    with st.popover("☰", help="API keys and app settings"):
        st.markdown("### ⚙️ Gemini Model & API Keys")

        # Private subscription status for the current authenticated customer.
        private_expiry = _parse_iso(login_row["expires_at"]).astimezone()
        private_plan = str(dict(login_row).get("plan_label") or "Membership Plan")
        private_now = _utcnow()
        private_active = bool(login_row["is_active"]) and private_now < _parse_iso(login_row["expires_at"])

        st.markdown("#### 📅 Your Plan")
        render_private_subscription_countdown(
            private_expiry, private_plan, login_row["customer_name"], login_row["access_code_display"]
        )
        if not private_active:
            st.error("❌ Your plan has expired. Contact the owner to renew access.")

        st.divider()
        st.selectbox(
            "🤖 Gemini Model",
            GEMINI_MODEL_OPTIONS,
            key="model_selector",
            format_func=lambda item: GEMINI_MODEL_LABELS.get(item, item),
            help="Choose a translation model. The app automatically tries backup models if the selected model is unavailable.",
        )
        st.selectbox(
            "🎯 Target Language", TARGET_LANGUAGE_OPTIONS, key="target_language",
            format_func=lambda item: TARGET_LANGUAGE_LABELS.get(item, item),
            help="Choose the language for SRT and MP3 output. This preference is private to your Access Code.",
        )
        st.selectbox(
            "🎭 Translation Style",
            TRANSLATION_STYLE_OPTIONS,
            key="translation_style",
            format_func=lambda item: TRANSLATION_STYLE_LABELS.get(item, item),
            help="Standard uses natural dialogue; Lipsync prioritizes short timed phrases; Comedy preserves humour; Formal uses respectful language.",
        )

        with st.expander("⚙️ Additional Workflow Options", expanded=False):
            st.selectbox(
                "🗣️ Source Video / Subtitle Language",
                [
                    "Auto-detect (ចិន/កូរ៉េ/វៀតណាម/អង់គ្លេស)",
                    "Chinese (中文)", "Korean (한국어)",
                    "Vietnamese (Tiếng Việt)", "English",
                ],
                key="source_language",
                format_func=lambda item: SOURCE_LANGUAGE_LABELS.get(item, item),
            )
            st.selectbox(
                "🚀 Workflow",
                ["⚡ Khmer SRT ស្វ័យប្រវត្តិ", "🎙️ Khmer SRT + MP3 តែម្តង", "📝 Source SRT only"],
                key="workflow_mode",
                format_func=lambda item: WORKFLOW_MODE_LABELS.get(item, item),
                help="Select one workflow and the app will follow that workflow automatically.",
            )
            st.selectbox(
                "⚙️ Processing Mode",
                ["⚡ លឿន (ណែនាំ)", "🎚️ សំឡេងច្បាស់ (យឺតជាង)"],
                key="processing_mode",
                format_func=lambda item: PROCESSING_MODE_LABELS.get(item, item),
            )
            st.toggle("📶 4G Lite Mode", key="lite_mode")
            st.caption("Fast Mode uses quicker ASR and larger safe subtitle batches to reduce Gemini requests. It keeps the same Six-Rule Translation Brain, voice tags, and locked SRT timestamps.")

        # API management stays at the bottom of Settings so it never occupies
        # the main translation workspace.
        st.divider()
        st.markdown("#### 🔑 Gemini API Key")
        st.caption(
            "Your API keys are encrypted and stored with your account. "
            "You may enter multiple keys, one key per line."
        )
        st.text_area(
            "Gemini API Key",
            height=76,
            placeholder="AIza...",
            key="api_keys_manager",
            label_visibility="collapsed",
            help="If one key reaches its quota, the app automatically tries the next key.",
        )

        if st.button("💾 Save Settings & API Keys", key="save_api_keys", use_container_width=True):
            entered_keys = [
                line.strip()
                for line in st.session_state.api_keys_manager.splitlines()
                if line.strip()
            ]
            preferences_saved = save_private_translation_preferences(
                preferences_owner,
                st.session_state.model_selector,
                st.session_state.target_language,
                st.session_state.translation_style,
            )
            # Do not let a mobile placeholder such as "AIza..." overwrite a
            # real saved key or block the non-secret Settings save.
            real_api_keys = [key for key in entered_keys if key.startswith("AIza") and len(key) >= 20]
            keys_saved = True
            if real_api_keys:
                keys_saved = save_private_api_keys("\n".join(real_api_keys))
            if preferences_saved and keys_saved:
                st.session_state.api_saved_notice = True
                st.rerun()
            else:
                st.error("Settings could not be saved. Your existing API keys and settings remain unchanged. Please try again.")

        current_keys = [
            line.strip()
            for line in st.session_state.get("api_keys_manager", "").splitlines()
            if line.strip()
        ]
        if current_keys:
            st.success(f"✅ API keys ready: {len(current_keys)}")
        else:
            st.caption("No API key saved yet. You can still open and explore the app.")

        st.divider()
        if st.button("Log out", key="customer_logout", use_container_width=True):
            release_customer_session(st.session_state.get("customer_code", ""), current_token)
            _session_cookie_delete()
            clear_private_user_session()
            _reset_project_workspace()
            st.session_state.pop("private_workspace_owner", None)
            for key in ("customer_authenticated", "customer_name", "customer_code", "customer_session_token"):
                st.session_state.pop(key, None)
            st.rerun()

api_keys_text = st.session_state.get("api_keys_manager", "")
account_api_keys = [line.strip() for line in _clean_api_keys(api_keys_text).splitlines() if line.strip()]
secret_api_keys = [line.strip() for line in load_secret_gemini_api_keys().splitlines() if line.strip()]
# Customer keys take priority. Secrets provide a server-side fallback after a reboot or a lost browser cookie.
valid_api_keys = list(dict.fromkeys(account_api_keys + secret_api_keys))
api_key = valid_api_keys[0] if valid_api_keys else ""
translation_style = st.session_state.translation_style
target_language = normalized_target_language(st.session_state.target_language)
target_language_name = target_language_settings(target_language)["name"]
model = st.session_state.model_selector
lite_mode = st.session_state.lite_mode
source_language = st.session_state.source_language
workflow_mode = st.session_state.workflow_mode
fast_mode = st.session_state.processing_mode.startswith("⚡")
max_mb = 60 if lite_mode else VIDEO_MAX_MB

if not valid_api_keys:
    st.warning(f"🔐 No Gemini API key saved — add one in ☰ Settings to translate subtitles into {target_language_name}.")

st.markdown(
    '<div class="hero"><h1>AI KHEMRA BRO</h1><p>GLOBAL AI DUBBING & SUBTITLING WORKSTATION</p></div>',
    unsafe_allow_html=True,
)

tab_video, tab_translate, tab_srt_speech, tab_text_speech = st.tabs(
    ["🎬 Video → SRT", "📝 AI Subtitle Translator", "📜 SRT → Speech", "🎙️ Text → Speech"]
)

with tab_video:
    st.markdown(f'<div class="section-title">1️⃣ Generate Subtitles ({target_language_name})</div>', unsafe_allow_html=True)
    # Keep the customer workflow simple: ordinary dubbing uses the natural
    # voice pipeline directly, with no extra music or Ducking controls.
    video_music_path, video_ducking_config = None, None

    with st.container(key="main_video_upload_panel"):
        st.markdown(
            '<div class="upload-note">📹 <strong>Upload Video</strong> • MP4/MOV/MKV/WEBM • Max. 10 minutes • 100 MB</div>',
            unsafe_allow_html=True,
        )
        uploaded_video = st.file_uploader(
            "Choose a video (10 minutes or less)",
            type=["mp4", "mov", "mkv", "webm"],
            help="For a faster upload, use a 720p or 480p MP4 under 100 MB. The app extracts only 16 kHz mono audio for ASR to reduce memory use.",
            key=f"main_video_upload_{st.session_state.video_uploader_version}",
            label_visibility="collapsed",
        )

    if uploaded_video is not None:
        source_stem = safe_download_stem(Path(uploaded_video.name).stem, 'khmer_story')
        st.session_state.source_video_stem = source_stem
        if not st.session_state.get('mp3_download_name') or st.session_state.get('mp3_download_name') == 'khmer_story_dubbed':
            suggested_name = f"{source_stem}_khmer"
            st.session_state.mp3_download_name = suggested_name
            st.session_state.mp3_filename_widget = suggested_name

        # Keep the uploaded filename and file size private on-screen.
        # The file is still available internally for validation and processing.
        size_mb = uploaded_video.size / (1024 * 1024)

        if size_mb > max_mb:
            st.error(f"Please reduce the video size to under {max_mb} MB.")
        else:
            if not lite_mode and st.checkbox("▶️ Video Preview"):
                st.video(uploaded_video)

            st.caption(f"Workflow: {WORKFLOW_MODE_LABELS.get(workflow_mode, workflow_mode)} • Source: {SOURCE_LANGUAGE_LABELS.get(source_language, source_language)} • Mode: {'Fast' if fast_mode else 'Higher accuracy'}")
            if st.button("🚀 Start Selected Workflow", key="generate_srt", use_container_width=True):
                video_path = None
                progress_bar = st.progress(1)
                progress_text = st.empty()

                def show_waiting(title, copy):
                    progress_text.markdown(
                        f'<div class="khemra-wait-card"><span class="khemra-wait-orb"></span>'
                        f'<div><div class="khemra-wait-title">{title}</div>'
                        f'<div class="khemra-wait-copy">{copy}</div></div></div>',
                        unsafe_allow_html=True,
                    )

                started_at = time.time()
                try:
                    video_path = save_upload(uploaded_video)
                    st.session_state.project_temp_files.append(str(video_path))
                    duration_seconds = validate_video_duration(video_path)
                    show_waiting(
                        "Preparing audio from your video",
                        f"Duration: {int(duration_seconds // 60)} minutes {int(duration_seconds % 60)} seconds • Please wait and keep this page open.",
                    )

                    # Stage 1 always creates a source SRT first. Fast mode uses direct WAV extraction.
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(transcribe_video_to_source_srt, video_path, fast_mode)
                        while not future.done():
                            elapsed = time.time() - started_at
                            percent = min(58, max(2, int((elapsed / max(18.0, 14.0 + size_mb * 1.2)) * 58)))
                            progress_bar.progress(percent)
                            show_waiting("Recognizing speech", "AI is extracting dialogue from your video…")
                            time.sleep(0.35)
                        cues, source_srt = future.result()

                    st.session_state.source_srt_text = source_srt
                    generated_audio = None

                    if workflow_mode == "📝 Source SRT only":
                        generated_srt = source_srt
                        notice = "✅ Source SRT created successfully."
                    elif valid_api_keys:
                        progress_bar.progress(62)
                        show_waiting(f"Translating to {target_language_name}", "Preserving character emotion and speaking style…")
                        try:
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                future = executor.submit(
                                    video_to_srt, video_path, valid_api_keys, model, cues, source_language, translation_style, target_language, fast_mode
                                )
                                while not future.done():
                                    elapsed = time.time() - started_at
                                    percent = min(96, 62 + int((elapsed / max(32.0, 22.0 + size_mb * 1.6)) * 34))
                                    progress_bar.progress(percent)
                                    show_waiting(f"Translating to {target_language_name}", "Making dialogue natural and appropriate for each character…")
                                    time.sleep(0.4)
                                generated_srt = future.result()
                            notice = f"✅ {target_language_name} SRT created successfully."
                        except Exception as translation_exc:
                            # Never discard Whisper output when the translation service is unavailable.
                            generated_srt = source_srt
                            notice = (
                                "⚠️ Whisper created the Source SRT, but Gemini could not translate it. "
                                + friendly_ai_error(translation_exc, len(valid_api_keys))
                            )
                    else:
                        generated_srt = source_srt
                        notice = f"⚠️ Source SRT created. Add a Gemini API key in Settings to translate it into {target_language_name}."

                    if workflow_mode == "🎙️ Khmer SRT + MP3 តែម្តង" and generated_srt != source_srt:
                        def auto_audio_progress(percent, message):
                            progress_bar.progress(min(100, 96 + int(max(0, percent) * 0.04)))
                            show_waiting(f"Creating {target_language_name} voice", "Balancing speech for a smooth, natural result…")
                        try:
                            generated_audio = create_mp3(
                                generated_srt, progress_callback=auto_audio_progress,
                                background_music_path=video_music_path,
                                ducking_config=video_ducking_config,
                                target_language=target_language,
                            )
                            notice = f"✅ {target_language_name} SRT and MP3 created successfully."
                        except Exception as audio_exc:
                            notice += f" ⚠️ The SRT is ready, but MP3 creation failed: {audio_exc}"

                    st.session_state.srt_text = generated_srt
                    st.session_state.main_srt_editor = generated_srt
                    st.session_state.pending_srt = ""
                    st.session_state.audio_bytes = generated_audio
                    st.session_state.workflow_notice = notice
                    progress_bar.progress(100)
                    time.sleep(0.25)
                    progress_bar.empty()
                    progress_text.empty()
                    st.rerun()

                except Exception as exc:
                    progress_bar.empty()
                    progress_text.empty()
                    st.error(f"❌ Video processing failed: {exc}")
                finally:
                    if video_path is not None:
                        video_path.unlink(missing_ok=True)

    st.subheader("Generated SRT")
    workflow_notice = st.session_state.pop("workflow_notice", "")
    if workflow_notice:
        if workflow_notice.startswith("✅"):
            st.success(workflow_notice)
        else:
            st.warning(workflow_notice)
    st.caption("The SRT appears here automatically when processing reaches 100%. You can edit it before generating MP3.")

    pending_editor_update = st.session_state.pop("pending_editor_update", None)
    if pending_editor_update is not None:
        st.session_state.main_srt_editor = pending_editor_update
        st.session_state.srt_text = pending_editor_update

    if "main_srt_editor" not in st.session_state:
        st.session_state.main_srt_editor = st.session_state.srt_text

    st.text_area(
        "SRT Editor",
        height=360,
        label_visibility="collapsed",
        key="main_srt_editor",
    )
    st.session_state.srt_text = st.session_state.main_srt_editor

    # Keep both SRT action buttons on one row directly below the editor,
    # including portrait and landscape mobile screens.
    with st.container(key="srt_actions"):
        c1, c2 = st.columns([1, 1], gap=None)
        with c1:
            if st.button(
                "🧠 Refine SRT",
                key="analyze_thoughts",
                use_container_width=True,
            ):
                if not st.session_state.srt_text.strip():
                    st.warning("Please generate or paste an SRT first.")
                elif not api_key:
                    st.error("Open ☰ Settings, add an API key, and click Save.")
                else:
                    analysis_video_path = None
                    try:
                        if uploaded_video is not None:
                            analysis_video_path = save_upload(uploaded_video)
                        waiting = st.empty()
                        waiting.markdown(
                            '<div class="khemra-wait-card"><span class="khemra-wait-orb"></span>'
                            '<div><div class="khemra-wait-title">Refining SRT</div>'
                            '<div class="khemra-wait-copy">Preserving characters while refining voice tags and dialogue rhythm…</div>'
                            '</div></div>', unsafe_allow_html=True,
                        )
                        analyzed_srt = analyze_inner_thoughts(
                            st.session_state.srt_text,
                            valid_api_keys,
                            model,
                            analysis_video_path,
                        )
                        waiting.empty()
                        st.session_state.srt_text = analyzed_srt
                        st.session_state.pending_editor_update = analyzed_srt
                        st.session_state.audio_bytes = None
                        st.rerun()
                    except Exception as exc:
                        if 'waiting' in locals():
                            waiting.empty()
                        st.error(f"❌ {exc}")
                    finally:
                        if analysis_video_path is not None:
                            analysis_video_path.unlink(missing_ok=True)
        with c2:
            if st.session_state.srt_text:
                st.download_button(
                    "⬇️ Download SRT",
                    ("\ufeff" + st.session_state.srt_text).encode("utf-8"),
                    f"{safe_download_stem(st.session_state.get('source_video_stem'), 'khmer_story')}_subtitle.srt",
                    "application/x-subrip",
                    use_container_width=True,
                )
            else:
                st.button(
                    "⬇️ Download SRT",
                    disabled=True,
                    key="download_srt_disabled",
                    use_container_width=True,
                )

    st.markdown('<div class="section-title">2️⃣ AI Dubbing (Edge TTS Studio)</div>', unsafe_allow_html=True)
    

    # Before completion, show only the Generate button. After completion,
    # remove the progress/result messages and replace them with filename + Download.
    if not st.session_state.audio_bytes:
        generate_clicked = st.button(
            "🎙️ Generate MP3 Voice",
            key="generate_audio",
            use_container_width=False,
        )

        if generate_clicked:
            if not st.session_state.srt_text.strip():
                st.warning("Please generate or paste an SRT first.")
            else:
                progress_bar = st.progress(0)
                progress_text = st.empty()

                def update_audio_progress(percent, message):
                    progress_bar.progress(max(0, min(100, int(percent))))
                    progress_text.markdown(
                        '<div class="khemra-wait-card"><span class="khemra-wait-orb"></span>'
                        f'<div><div class="khemra-wait-title">Creating {target_language_name} voice</div>'
                        '<div class="khemra-wait-copy">Balancing the voice for smooth, non-overlapping speech…</div>'
                        '</div></div>',
                        unsafe_allow_html=True,
                    )

                try:
                    update_audio_progress(1, "Starting voice generation…")
                    st.session_state.audio_bytes = create_mp3(
                        st.session_state.srt_text,
                        progress_callback=update_audio_progress,
                        background_music_path=video_music_path,
                        ducking_config=video_ducking_config,
                        target_language=target_language,
                    )
                    # Clear the processing display immediately after completion.
                    progress_bar.empty()
                    progress_text.empty()
                    if not st.session_state.get("mp3_download_name"):
                        stem = st.session_state.get("source_video_stem", "khmer_story")
                        st.session_state.mp3_download_name = f"{stem}_khmer"
                    st.rerun()
                except Exception as exc:
                    progress_bar.empty()
                    progress_text.empty()
                    st.error(f"❌ MP3 generation failed: {exc}")
    else:
        if not st.session_state.get("mp3_filename_widget"):
            st.session_state.mp3_filename_widget = st.session_state.get(
                "mp3_download_name", "khmer_story_dubbed"
            )
        st.text_input(
            "✏️ MP3 File Name",
            key="mp3_filename_widget",
            placeholder="e.g. episode_1_khmer_dub",
            help="You can rename the file before downloading it.",
        )
        st.session_state.mp3_download_name = st.session_state.mp3_filename_widget
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
        download_stem = safe_download_stem(
            st.session_state.get("mp3_filename_widget"),
            fallback="khmer_story_dubbed",
        )
        st.download_button(
            "⬇️ Download MP3 Audio",
            st.session_state.audio_bytes,
            f"{download_stem}.mp3",
            "audio/mpeg",
            use_container_width=True,
        )

    def _clear_current_project():
        _reset_project_workspace()
        st.session_state.project_temp_files = []
        st.session_state.srt_text = ""
        st.session_state.pending_srt = ""
        st.session_state.audio_bytes = None
        st.session_state.audio_job_pending = False
        st.session_state.pending_editor_update = ""
        st.session_state.source_video_stem = "khmer_story"
        st.session_state.mp3_download_name = "khmer_story_dubbed"
        st.session_state.mp3_filename_widget = "khmer_story_dubbed"
        st.session_state.main_srt_editor = ""
        st.session_state.source_srt_text = ""
        st.session_state.speech_tab_audio_bytes = None
        st.session_state.text_tab_audio_bytes = None
        st.session_state.ducking_profiles = {}
        st.session_state.background_music_paths = {}
        st.session_state.background_music_signatures = {}
        old_music_versions = st.session_state.get("background_music_upload_versions", {})
        st.session_state.background_music_upload_versions = {
            key: int(value) + 1 for key, value in old_music_versions.items()
        }
        st.session_state.video_uploader_version = int(st.session_state.get("video_uploader_version", 0)) + 1

    st.markdown('<div class="clear-wrap">', unsafe_allow_html=True)
    st.button(
        "🗑️ Clear Video Project",
        key="clear_project",
        on_click=_clear_current_project,
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with tab_translate:
    st.header(f"AI Subtitle Translator → {target_language_name}")
    st.info(f"Paste a Chinese, Korean, Vietnamese, or English SRT. The app preserves original timestamps, translates to natural spoken {target_language_name}, and uses only [M], [F], [M_THINK], and [F_THINK].")
    st.caption(f"Source language selected in Settings: {SOURCE_LANGUAGE_LABELS.get(source_language, source_language)}")
    source_srt = st.text_area("Source SRT (Chinese / Korean / Vietnamese / English)", height=300, key="translator_source")
    if st.button(f"Translate SRT → {target_language_name}", key="translate_btn"):
        if not source_srt.strip():
            st.warning("Please paste a Source SRT first.")
        elif not valid_api_keys:
            st.error("Open ☰ Settings, add an API key, and click Save.")
        else:
            waiting = st.empty()
            try:
                waiting.markdown(
                    '<div class="khemra-wait-card"><span class="khemra-wait-orb"></span>'
                    f'<div><div class="khemra-wait-title">Translating to {target_language_name}</div>'
                    '<div class="khemra-wait-copy">Preserving emotion, pronouns, and each character’s speaking rhythm…</div>'
                    '</div></div>', unsafe_allow_html=True,
                )
                translated_srt = translate_srt_to_khmer(
                    source_srt, valid_api_keys, model, source_language,
                    translation_style, target_language, fast_mode=fast_mode,
                )
                waiting.empty()
                st.session_state.srt_text = translated_srt
                st.session_state.translated_srt_preview = translated_srt
                st.session_state.pending_editor_update = translated_srt
                st.success(f"✅ {target_language_name} SRT translated successfully with original timestamps preserved.")
            except Exception as exc:
                waiting.empty()
                st.error(f"❌ {exc}")
    if st.session_state.get("translated_srt_preview"):
        st.code(st.session_state.translated_srt_preview, language="srt")
        st.download_button(
            f"⬇️ Download {target_language_name} SRT",
            ("\ufeff" + st.session_state.translated_srt_preview).encode("utf-8"),
            "translated_subtitle.srt",
            "application/x-subrip",
            key="download_translated_srt",
            use_container_width=True,
        )

with tab_srt_speech:
    st.header("SRT → Speech")
    
    render_thought_voice_guide()
    srt_music_path, srt_ducking_config = None, None
    speech_srt = st.text_area(
        f"{target_language_name} SRT with [M] [F] [M_THINK] [F_THINK]",
        height=360,
        key="speech_srt_input",
    )
    if st.button("🎧 Create MP3", key="srt_to_speech_btn"):
        if not speech_srt.strip():
            st.warning(f"Please enter a {target_language_name} SRT.")
        else:
            waiting = st.empty()
            try:
                waiting.markdown(
                    '<div class="khemra-wait-card"><span class="khemra-wait-orb"></span>'
                    f'<div><div class="khemra-wait-title">Creating {target_language_name} voice</div>'
                    '<div class="khemra-wait-copy">Please wait while the app preserves natural speech rhythm…</div>'
                    '</div></div>', unsafe_allow_html=True,
                )
                st.session_state.speech_tab_audio_bytes = create_mp3(
                    speech_srt,
                    background_music_path=srt_music_path,
ducking_config=srt_ducking_config,
                        target_language=target_language,
                    )
                waiting.empty()
                st.success("✅ MP3 created successfully.")
            except Exception as exc:
                waiting.empty()
                st.error(f"❌ {exc}")
    if st.session_state.get("speech_tab_audio_bytes"):
        st.audio(st.session_state.speech_tab_audio_bytes, format="audio/mp3")
        st.download_button(
            "⬇️ Download MP3",
            st.session_state.speech_tab_audio_bytes,
            "srt_speech.mp3",
            "audio/mpeg",
            key="download_srt_speech_mp3",
            use_container_width=True,
        )

with tab_text_speech:
    st.header("Text → Speech")
    
    render_thought_voice_guide()
    text_music_path, text_ducking_config = None, None
    plain_text = st.text_area(f"{target_language_name} Text", height=260, key="plain_text_input")
    voice_choice = st.selectbox(
        "Voice",
        ["M", "F", "M_THINK", "F_THINK"],
        key="plain_voice",
    )
    if st.button("🔊 Generate Voice", key="plain_voice_btn"):
        if not plain_text.strip():
            st.warning(f"Please enter {target_language_name} text.")
        else:
            waiting = st.empty()
            try:
                waiting.markdown(
                    '<div class="khemra-wait-card"><span class="khemra-wait-orb"></span>'
                    '<div><div class="khemra-wait-title">Creating voice</div>'
                    '<div class="khemra-wait-copy">Preparing a soft, natural-sounding voice…</div>'
                    '</div></div>', unsafe_allow_html=True,
                )
                with tempfile.TemporaryDirectory() as folder:
                    output = Path(folder) / "speech.mp3"
                    st.session_state.text_tab_audio_bytes = create_single_voice_mp3(
                        plain_text.strip(), voice_choice,
                        background_music_path=text_music_path,
                        ducking_config=text_ducking_config,
                        target_language=target_language,
                    )
                waiting.empty()
                st.success("✅ Voice created successfully.")
            except Exception as exc:
                waiting.empty()
                st.error(f"❌ {exc}")
    if st.session_state.get("text_tab_audio_bytes"):
        st.audio(st.session_state.text_tab_audio_bytes, format="audio/mp3")
        st.download_button(
            "⬇️ Download MP3",
            st.session_state.text_tab_audio_bytes,
            "text_speech.mp3",
            "audio/mpeg",
            key="download_text_speech_mp3",
            use_container_width=True,
        )

st.caption("AI-KHEMRA-BRO v6.7.3 • English-first interface • Clear 40% Thought Voice • Mobile-first")
