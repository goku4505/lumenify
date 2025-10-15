#!/usr/bin/env python3
"""
LumoGen Voice Studio - Professional AI-Powered Text-to-Speech & Audio Transcription
Enhanced with Complete LumoGen Design System
"""

from flask import Flask, request, jsonify, send_file, session, Response
import os
import tempfile
import asyncio
import edge_tts
import threading
import uuid
from datetime import datetime, timedelta
import json
import re
import warnings
import socket

warnings.filterwarnings("ignore", category=UserWarning)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'lumogen-voice-studio-secret-key-2024')

# Global variables
VOICE_DATA = {}
LANGUAGE_VOICES = {}
TEMP_FILES = {}

# Recommended voices
RECOMMENDED_VOICES = [
    {'name': 'William', 'gender': 'Male', 'short_name': 'en-AU-WilliamNeural'},
    {'name': 'Natasha', 'gender': 'Female', 'short_name': 'en-AU-NatashaNeural'},
    {'name': 'Clara', 'gender': 'Female', 'short_name': 'en-CA-ClaraNeural'},
    {'name': 'Liam', 'gender': 'Male', 'short_name': 'en-CA-LiamNeural'},
    {'name': 'Ava', 'gender': 'Female', 'short_name': 'en-US-AvaNeural'},
    {'name': 'Andrew', 'gender': 'Male', 'short_name': 'en-US-AndrewNeural', 'best': True},
    {'name': 'Emma', 'gender': 'Female', 'short_name': 'en-US-EmmaNeural'},
    {'name': 'Brian', 'gender': 'Male', 'short_name': 'en-US-BrianNeural'}
]

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def get_fallback_voices():
    """Provide fallback voices when edge-tts is not available"""
    return {
        'English': [
            {
                'display_name': 'English Female - Jenny',
                'short_name': 'en-US-JennyNeural',
                'info': {'Locale': 'en-US', 'Gender': 'Female'},
                'language': 'English',
                'locale': 'en-US',
                'gender': 'Female'
            },
            {
                'display_name': 'English Male - Guy',
                'short_name': 'en-US-GuyNeural',
                'info': {'Locale': 'en-US', 'Gender': 'Male'},
                'language': 'English',
                'locale': 'en-US',
                'gender': 'Male'
            }
        ]
    }

async def load_voices():
    """Load all available voices from edge-tts"""
    global VOICE_DATA, LANGUAGE_VOICES
    
    if not check_internet_connection():
        print("Using fallback voices...")
        fallback = get_fallback_voices()
        LANGUAGE_VOICES = fallback
        VOICE_DATA = {v['display_name']: v for voices in fallback.values() for v in voices}
        return True
    
    try:
        voices = await edge_tts.list_voices()
        language_groups = {}
        all_voices = []
        
        for v in voices:
            try:
                locale = str(v.get('Locale', '')).strip()
                short_name = v.get('ShortName', '')
                friendly = v.get('FriendlyName', short_name)
                gender = v.get('Gender', 'Unknown')
                
                if not short_name:
                    continue
                
                lang_code = locale.split('-')[0] if locale else 'en'
                lang_names = {'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}
                language_name = lang_names.get(lang_code, f"{lang_code.upper()} Language")
                
                if language_name not in language_groups:
                    language_groups[language_name] = []
                
                display_name = f"{friendly} - {gender}"
                voice_data = {
                    'display_name': display_name,
                    'short_name': short_name,
                    'info': v,
                    'language': language_name,
                    'locale': locale,
                    'gender': gender
                }
                
                language_groups[language_name].append(voice_data)
                all_voices.append(voice_data)
                
            except Exception as e:
                continue
        
        LANGUAGE_VOICES = language_groups
        VOICE_DATA = {v['display_name']: v for v in all_voices}
        
        print(f"Loaded {len(all_voices)} voices across {len(language_groups)} languages")
        return True
        
    except Exception as e:
        print(f"Failed to load voices: {e}")
        fallback = get_fallback_voices()
        LANGUAGE_VOICES = fallback
        VOICE_DATA = {v['display_name']: v for voices in fallback.values() for v in voices}
        return True

def calculate_rate_parameter(speed):
    """Calculate proper rate parameter for edge-tts"""
    if speed == 1.0:
        return "+0%"
    percent = round((speed - 1.0) * 100)
    return f"+{percent}%" if percent > 0 else f"{percent}%"

def get_session_id():
    """Get or create session ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def cleanup_temp_files(session_id):
    """Clean up temporary files for a session"""
    if session_id in TEMP_FILES:
        for temp_file in TEMP_FILES[session_id]:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass
        del TEMP_FILES[session_id]

def find_voice_by_input(name):
    """Find voice by display name or short name"""
    if not name:
        return None
    
    if name in VOICE_DATA:
        return VOICE_DATA[name]
    
    for v in VOICE_DATA.values():
        if v.get('short_name') == name:
            return v
    
    return {'short_name': name}

# Load Faster Whisper
try:
    from faster_whisper import WhisperModel
    WHISPER_MODEL = WhisperModel("small", device="cpu", compute_type="int8")
except ImportError:
    WHISPER_MODEL = None

# Enhanced HTML Template with Complete LumoGen Design System
HTML_TEMPLATE = """<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no" />
  <title>LumoGen Voice Studio - Transform Ideas Into Professional Audio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
  <style>
    :root {
      /* Enhanced Color Palette from LumoGen */
      --primary-blue: #2563eb;
      --primary-green: #10b981;
      --gradient-primary: linear-gradient(135deg, #2563eb 0%, #10b981 100%);
      --gradient-secondary: linear-gradient(135deg, #1e40af 0%, #059669 100%);
      --gradient-accent: linear-gradient(135deg, #3b82f6 0%, #34d399 100%);
      
      /* Orange for content style buttons */
      --style-orange: #f97316;
      --style-orange-light: #fb923c;
      --style-orange-dark: #ea580c;
      
      /* Dark theme (default) */
      --bg-primary: #0a0a0f;
      --bg-secondary: #1a1a2e;
      --bg-tertiary: #16213e;
      --bg-card: #1e1e3f;
      --bg-glass: rgba(30, 30, 63, 0.8);
      --text-primary: #e8e8ff;
      --text-secondary: #b8b8d6;
      --text-muted: #8e8eb0;
      --border-subtle: rgba(37, 99, 235, 0.1);
      --border-medium: rgba(37, 99, 235, 0.2);
      --shadow-soft: 0 4px 20px rgba(37, 99, 235, 0.1);
      --shadow-medium: 0 8px 32px rgba(37, 99, 235, 0.2);
      --shadow-strong: 0 20px 50px rgba(37, 99, 235, 0.3);
      --radius: 20px;
      --mobile-padding: 20px;
      --touch-target: 48px;
    }

    [data-theme="light"] {
      /* Light theme colors */
      --bg-primary: #fafbff;
      --bg-secondary: #f4f5f9;
      --bg-tertiary: #e8eaf6;
      --bg-card: #ffffff;
      --bg-glass: rgba(255, 255, 255, 0.9);
      --text-primary: #1e293b;
      --text-secondary: #475569;
      --text-muted: #64748b;
      --border-subtle: rgba(37, 99, 235, 0.1);
      --border-medium: rgba(37, 99, 235, 0.2);
      --shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.08);
      --shadow-medium: 0 8px 32px rgba(0, 0, 0, 0.12);
      --shadow-strong: 0 20px 50px rgba(0, 0, 0, 0.15);
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      -webkit-tap-highlight-color: transparent;
    }
    
    body {
      font-family: 'Poppins', sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.6;
      min-height: 100vh;
      transition: all 0.3s ease;
      overflow-x: hidden;
    }
    
    /* Navigation */
    nav {
      position: fixed;
      top: 0;
      width: 100%;
      padding: 1rem 2rem;
      background: var(--bg-glass);
      backdrop-filter: blur(20px);
      z-index: 1000;
      transition: all 0.3s ease;
    }
    
    .nav-container {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .logo {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 1.8rem;
      font-weight: 800;
      color: var(--text-primary);
    }
    
    .logo i {
      font-size: 2rem;
      background: var(--gradient-primary);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }
    
    .nav-links {
      display: flex;
      gap: 2rem;
      align-items: center;
    }
    
    .nav-link {
      color: var(--text-secondary);
      text-decoration: none;
      font-weight: 500;
      transition: color 0.3s ease;
      position: relative;
    }
    
    .nav-link::after {
      content: '';
      position: absolute;
      bottom: -5px;
      left: 0;
      width: 0;
      height: 2px;
      background: var(--gradient-primary);
      transition: width 0.3s ease;
    }
    
    .nav-link:hover {
      color: var(--text-primary);
    }
    
    .nav-link:hover::after {
      width: 100%;
    }
    
    .theme-toggle {
      background: var(--bg-tertiary);
      border: none;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--text-primary);
      transition: all 0.3s ease;
    }
    
    .theme-toggle:hover {
      background: var(--border-medium);
      transform: rotate(180deg);
    }
    
    /* Main Container */
    .main-container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 80px 20px 40px;
    }
    
    /* Compact Hero Section */
    .hero {
      text-align: center;
      padding: 1.5rem 0;
      position: relative;
      overflow: hidden;
    }
    
    .hero::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: radial-gradient(circle at 50% 50%, rgba(37, 99, 235, 0.15) 0%, transparent 70%);
      z-index: -1;
    }
    
    .hero-content {
      max-width: 600px;
      margin: 0 auto;
      animation: fadeInUp 0.8s ease-out;
    }
    
    .hero-content h1 {
      font-size: clamp(1.8rem, 4vw, 2.5rem);
      font-weight: 900;
      line-height: 1.2;
      margin-bottom: 0.75rem;
      background: var(--gradient-primary);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }
    
    .hero-content p {
      font-size: 1rem;
      color: var(--text-secondary);
      margin-bottom: 1rem;
      line-height: 1.5;
      animation: fadeInUp 0.8s ease-out 0.2s backwards;
    }
    
    /* Grid Layout */
    .grid {
      display: grid;
      gap: 30px;
      grid-template-columns: 1fr;
    }
    
    @media (min-width: 1024px) {
      .grid {
        grid-template-columns: 400px 1fr;
      }
    }
    
    /* Cards */
    .card {
      background: var(--bg-card);
      border-radius: var(--radius);
      padding: 2rem;
      box-shadow: var(--shadow-soft);
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }
    
    .card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 5px;
      background: var(--gradient-primary);
    }
    
    .card:hover {
      transform: translateY(-10px);
      box-shadow: var(--shadow-strong);
    }
    
    /* Sections */
    .section {
      margin-bottom: 2rem;
    }
    
    .section-title {
      font-size: 1.5rem;
      font-weight: 700;
      margin-bottom: 1.5rem;
      color: var(--text-primary);
      position: relative;
      display: inline-block;
    }
    
    .section-title::after {
      content: '';
      position: absolute;
      bottom: -5px;
      left: 0;
      width: 50px;
      height: 3px;
      background: var(--gradient-primary);
      border-radius: 2px;
    }
    
    /* Forms */
    .form-group {
      margin-bottom: 1.5rem;
    }
    
    .form-label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 600;
      color: var(--text-primary);
    }
    
    .form-control {
      width: 100%;
      padding: 12px 16px;
      border: 2px solid var(--border-subtle);
      border-radius: 12px;
      background: var(--bg-tertiary);
      color: var(--text-primary);
      font-size: 16px;
      font-family: inherit;
      transition: all 0.3s ease;
      min-height: var(--touch-target);
    }
    
    .form-control:focus {
      outline: none;
      border-color: var(--primary-blue);
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    textarea.form-control {
      resize: vertical;
      min-height: 120px;
    }
    
    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 12px 24px;
      border: none;
      border-radius: 50px;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      margin-right: 0.5rem;
      margin-bottom: 0.5rem;
    }
    
    .btn-primary {
      background: var(--gradient-primary);
      color: white;
      box-shadow: var(--shadow-soft);
    }
    
    .btn-primary:hover {
      transform: translateY(-3px);
      box-shadow: var(--shadow-medium);
    }
    
    .btn-secondary {
      background: transparent;
      color: var(--text-primary);
      border: 2px solid var(--border-medium);
    }
    
    .btn-secondary:hover {
      background: var(--bg-tertiary);
      transform: translateY(-2px);
    }
    
    .btn-success {
      background: linear-gradient(135deg, var(--primary-green) 0%, #059669 100%);
      color: white;
    }
    
    .btn-download {
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      color: white;
    }
    
    .btn-transcribe {
      background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
      color: white;
    }
    
    /* Voice Recommendations */
    .voice-recommendations {
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);
      border: 2px solid var(--border-medium);
      border-radius: var(--radius);
      padding: 1.5rem;
      margin-bottom: 2rem;
    }
    
    .voice-recommendations h3 {
      margin: 0 0 1rem;
      font-size: 1.2rem;
      font-weight: 700;
      text-align: center;
      color: var(--text-primary);
    }
    
    .recommended-voices {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
    }
    
    @media (min-width: 768px) {
      .recommended-voices {
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
      }
    }
    
    .voice-chip {
      background: var(--bg-tertiary);
      border: 2px solid var(--border-subtle);
      border-radius: 12px;
      padding: 1rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      position: relative;
    }
    
    .voice-chip:hover {
      border-color: var(--primary-blue);
      transform: translateY(-2px);
      box-shadow: var(--shadow-soft);
    }
    
    .voice-chip.selected {
      background: var(--gradient-primary);
      color: white;
      border-color: var(--primary-blue);
    }
    
    .voice-chip.best::after {
      content: '👑';
      position: absolute;
      top: -8px;
      right: -8px;
      background: var(--style-orange);
      color: white;
      font-size: 14px;
      padding: 2px 6px;
      border-radius: 50%;
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .voice-name {
      font-weight: 700;
      margin-bottom: 0.25rem;
    }
    
    .voice-gender {
      font-size: 0.875rem;
      opacity: 0.8;
    }
    
    /* Audio Player */
    .audio-player {
      width: 100%;
      margin: 1.5rem 0;
      border-radius: 12px;
      height: 54px;
      background: var(--bg-tertiary);
    }
    
    .audio-actions {
      display: flex;
      gap: 1rem;
      margin: 1.5rem 0;
      flex-wrap: wrap;
    }
    
    /* Output */
    .output-content {
      background: var(--bg-tertiary);
      color: var(--text-secondary);
      padding: 1.5rem;
      border-radius: 12px;
      font-family: 'Courier New', monospace;
      font-size: 14px;
      line-height: 1.5;
      white-space: pre-wrap;
      max-height: 300px;
      overflow-y: auto;
      border: 1px solid var(--border-subtle);
    }
    
    /* File Upload */
    .file-upload {
      position: relative;
      width: 100%;
    }
    
    .file-upload-input {
      position: absolute;
      left: -9999px;
    }
    
    .file-upload-label {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 2rem;
      border: 2px dashed var(--border-medium);
      border-radius: 12px;
      background: var(--bg-tertiary);
      cursor: pointer;
      transition: all 0.3s ease;
      min-height: 100px;
      text-align: center;
    }
    
    .file-upload-label:hover {
      border-color: var(--primary-blue);
      background: rgba(37, 99, 235, 0.1);
    }
    
    .file-upload-label.has-file {
      border-color: var(--primary-green);
      background: rgba(16, 185, 129, 0.1);
      color: var(--primary-green);
    }
    
    /* Status Indicator */
    .status-indicator {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1.5rem;
      border-radius: 50px;
      font-size: 0.875rem;
      font-weight: 600;
      margin-bottom: 2rem;
      justify-content: center;
    }
    
    .status-indicator.online {
      background: rgba(16, 185, 129, 0.1);
      color: var(--primary-green);
      border: 2px solid rgba(16, 185, 129, 0.2);
    }
    
    .status-indicator.offline {
      background: rgba(239, 68, 68, 0.1);
      color: #ef4444;
      border: 2px solid rgba(239, 68, 68, 0.2);
    }
    
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
      animation: pulse 2s infinite;
    }
    
    /* Toast Notifications */
    .toast {
      position: fixed;
      top: 100px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--bg-card);
      border: 2px solid var(--border-medium);
      border-radius: 12px;
      padding: 1rem 1.5rem;
      box-shadow: var(--shadow-medium);
      z-index: 1000;
      opacity: 0;
      transition: all 0.3s ease;
      max-width: calc(100vw - 40px);
    }
    
    .toast.show {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
    
    .toast.success {
      border-color: var(--primary-green);
      background: rgba(16, 185, 129, 0.1);
      color: var(--primary-green);
    }
    
    .toast.error {
      border-color: #ef4444;
      background: rgba(239, 68, 68, 0.1);
      color: #ef4444;
    }
    
    /* Loading States */
    .loading {
      opacity: 0.7;
      pointer-events: none;
    }
    
    .loading-spinner {
      width: 20px;
      height: 20px;
      border: 2px solid transparent;
      border-top: 2px solid currentColor;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-right: 0.5rem;
    }
    
    /* Feature Grid */
    .feature-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1rem;
      margin: 2rem 0;
    }
    
    .feature-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1.5rem;
      background: var(--bg-tertiary);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      transition: all 0.3s ease;
    }
    
    .feature-item:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-soft);
    }
    
    .feature-icon {
      width: 48px;
      height: 48px;
      background: var(--gradient-primary);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1.25rem;
      flex-shrink: 0;
    }
    
    /* Animations */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(30px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    
    /* Utility Classes */
    .hidden {
      display: none;
    }
    
    .fade-in {
      animation: fadeInUp 0.8s ease-out;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
      .nav-links {
        display: none;
      }
      
      .main-container {
        padding: 70px 10px 20px;
      }
      
      .hero {
        padding: 1rem 0;
      }
      
      .btn {
        width: 100%;
        justify-content: center;
      }
      
      .audio-actions {
        flex-direction: column;
      }
    }
  </style>
</head>
<body>
  <!-- Navigation -->
  <nav>
    <div class="nav-container">
      <div class="logo">
        <i class="fas fa-microphone-alt"></i>
        <span>LumoGen Voice Studio</span>
      </div>
      <div class="nav-links">
        <a href="#voice-selection" class="nav-link">Voice Selection</a>
        <a href="#text-input" class="nav-link">Text Input</a>
        <a href="#audio-upload" class="nav-link">Audio Upload</a>
        <a href="#audio-player" class="nav-link">Audio Player</a>
        <button class="theme-toggle" id="theme-toggle">
          <i class="fas fa-moon" id="theme-icon"></i>
        </button>
      </div>
    </div>
  </nav>

  <!-- Main Container -->
  <div class="main-container">
    <!-- Compact Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>Transform Ideas Into Professional Audio</h1>
        <p>Create stunning voiceovers with AI-powered text-to-speech technology. Choose from hundreds of voices, multiple languages, and customize every detail.</p>
      </div>
    </section>

    <!-- Status Indicator -->
    <div id="statusIndicator" class="status-indicator">
      <div class="status-dot"></div>
      <span>Loading...</span>
    </div>

    <!-- Main Grid -->
    <div class="grid">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="card" id="voice-selection">
          <section class="section">
            <h2 class="section-title">Voice Selection</h2>
            
            <div class="form-group">
              <label class="form-label" for="voiceSearch">Search Voices</label>
              <input id="voiceSearch" class="form-control" placeholder="Search voices..." />
            </div>

            <div class="form-group">
              <label class="form-label" for="languageSelect">Language</label>
              <select id="languageSelect" class="form-control">
                <option>Loading...</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="genderSelect">Gender</label>
              <select id="genderSelect" class="form-control">
                <option value="All">All</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="voiceSelect">Available Voices</label>
              <select id="voiceSelect" class="form-control">
                <option>Loading...</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="speed">Speed</label>
              <input id="speed" type="number" class="form-control" value="1.0" min="0.5" max="2.0" step="0.1" />
            </div>

            <button id="refreshVoices" class="btn btn-secondary">
              <i class="fas fa-sync-alt"></i> Refresh Voices
            </button>
            
            <div class="voice-recommendations">
              <h3>✨ Recommended Voices</h3>
              <div class="recommended-voices" id="recommendedVoices">
                <!-- Populated by JS -->
              </div>
            </div>
          </section>
        </div>
      </aside>

      <!-- Main Panel -->
      <section class="main-panel">
        <!-- Text Input Section -->
        <div class="card" id="text-input">
          <div class="section">
            <h2 class="section-title">Text Input</h2>
            <div class="form-group">
              <label class="form-label" for="text">Enter Text</label>
              <textarea id="text" class="form-control" placeholder="Type your text here...">Welcome to LumoGen Voice Studio! This is a demonstration of our advanced text-to-speech technology.</textarea>
            </div>
            <button id="previewBtn" class="btn btn-secondary">
              <i class="fas fa-play"></i> Preview
            </button>
            <button id="generateBtn" class="btn btn-primary">
              <span class="btn-text">
                <i class="fas fa-magic"></i> Generate Audio
              </span>
            </button>
            <button id="cleanupBtn" class="btn btn-secondary">
              <i class="fas fa-broom"></i> Clean Up
            </button>
          </div>
        </div>

        <!-- Audio Upload Section -->
        <div class="card" id="audio-upload">
          <div class="section">
            <h2 class="section-title">Audio Upload</h2>
            <div class="form-group">
              <div class="file-upload">
                <input id="audioUpload" type="file" class="file-upload-input" accept="audio/*" />
                <label for="audioUpload" class="file-upload-label" id="uploadLabel">
                  <i class="fas fa-cloud-upload-alt" style="font-size: 2rem;"></i>
                  <span>Choose audio file or drag & drop</span>
                  <span style="font-size: 0.875rem; opacity: 0.7;">MP3, WAV, M4A supported</span>
                </label>
              </div>
            </div>
            <button id="transcribeUploadBtn" class="btn btn-success">
              <i class="fas fa-closed-captioning"></i> Transcribe Upload
            </button>
          </div>
        </div>

        <!-- Audio Player Section -->
        <div class="card" id="audio-player">
          <div class="section">
            <h2 class="section-title">Audio Player</h2>
            <audio id="player" class="audio-player" controls>
              Your browser doesn't support HTML audio.
            </audio>
            
            <div id="audioActions" class="audio-actions hidden">
              <button id="downloadAudioBtn" class="btn btn-download">
                <i class="fas fa-download"></i> Download Audio
              </button>
              <button id="transcribeAudioBtn" class="btn btn-transcribe">
                <i class="fas fa-closed-captioning"></i> Transcribe Audio
              </button>
            </div>
          </div>
        </div>

        <!-- Output Section -->
        <div class="card">
          <div class="section">
            <h2 class="section-title">Output</h2>
            <div id="output" class="output-content">🚀 LumoGen Voice Studio ready. Select a voice and enter text to begin creating professional audio.</div>
          </div>
        </div>

        <!-- Features Grid -->
        <div class="feature-grid">
          <div class="feature-item">
            <div class="feature-icon">
              <i class="fas fa-microphone"></i>
            </div>
            <div>
              <strong>High-Quality Voices</strong>
              <div style="font-size: 0.875rem; opacity: 0.8;">Natural-sounding AI voices</div>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <i class="fas fa-bolt"></i>
            </div>
            <div>
              <strong>Fast Processing</strong>
              <div style="font-size: 0.875rem; opacity: 0.8;">Generate audio in seconds</div>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <i class="fas fa-globe"></i>
            </div>
            <div>
              <strong>Multiple Languages</strong>
              <div style="font-size: 0.875rem; opacity: 0.8;">Support for 50+ languages</div>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <i class="fas fa-mobile-alt"></i>
            </div>
            <div>
              <strong>Mobile Optimized</strong>
              <div style="font-size: 0.875rem; opacity: 0.8;">Works on all devices</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="toast"></div>

<script>
const RECOMMENDED_VOICES = [
  { name: 'William', gender: 'Male', short_name: 'en-AU-WilliamNeural' },
  { name: 'Natasha', gender: 'Female', short_name: 'en-AU-NatashaNeural' },
  { name: 'Clara', gender: 'Female', short_name: 'en-CA-ClaraNeural' },
  { name: 'Liam', gender: 'Male', short_name: 'en-CA-LiamNeural' },
  { name: 'Ava', gender: 'Female', short_name: 'en-US-AvaNeural' },
  { name: 'Andrew', gender: 'Male', short_name: 'en-US-AndrewNeural', best: true },
  { name: 'Emma', gender: 'Female', short_name: 'en-US-EmmaNeural' },
  { name: 'Brian', gender: 'Male', short_name: 'en-US-BrianNeural' }
];

let isLoading = false;
let uploadedAudioFile = null;
let currentAudioUrl = null;
let currentAudioFilename = null;

// Theme Management
function toggleTheme() {
  const html = document.documentElement;
  const themeIcon = document.getElementById('theme-icon');
  
  if (html.getAttribute('data-theme') === 'dark') {
    html.setAttribute('data-theme', 'light');
    themeIcon.className = 'fas fa-sun';
    localStorage.setItem('theme', 'light');
  } else {
    html.setAttribute('data-theme', 'dark');
    themeIcon.className = 'fas fa-moon';
    localStorage.setItem('theme', 'dark');
  }
}

function initTheme() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const themeIcon = document.getElementById('theme-icon');
  
  if (saved === 'dark' || (!saved && prefersDark)) {
    document.documentElement.setAttribute('data-theme', 'dark');
    themeIcon.className = 'fas fa-moon';
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    themeIcon.className = 'fas fa-sun';
  }
}

// Toast Notifications
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = 'toast ' + type;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 4000);
}

// Loading States
function setLoading(loading) {
  isLoading = loading;
  document.body.classList.toggle('loading', loading);
}

function setButtonLoading(button, loading) {
  const btnText = button.querySelector('.btn-text') || button;

  if (loading) {
    const originalText = btnText.innerHTML;
    button.setAttribute('data-original-text', originalText);
    button.disabled = true;
    btnText.innerHTML = '<div class="loading-spinner"></div>Processing...';
  } else {
    const originalText = button.getAttribute('data-original-text');
    button.disabled = false;
    btnText.innerHTML = originalText;
  }
}

// Output Management
function updateOutput(message, type = 'info') {
  const output = document.getElementById('output');
  const timestamp = new Date().toLocaleTimeString();
  const prefix = type === 'error' ? '⛔' : type === 'success' ? '✅' : 'ℹ️';
  output.textContent = '[' + timestamp + '] ' + prefix + ' ' + message;
  
  if (type === 'error' || type === 'success') {
    showToast(message, type);
  }
}

// Voice Chip Creation
function createVoiceChip(voice) {
  const chip = document.createElement('div');
  chip.className = 'voice-chip' + (voice.best ? ' best' : '');
  chip.innerHTML = '<div class="voice-name">' + voice.name + '</div><div class="voice-gender">' + voice.gender + '</div>';
  
  chip.addEventListener('click', () => {
    document.querySelectorAll('.voice-chip').forEach(c => c.classList.remove('selected'));
    chip.classList.add('selected');
    
    const voiceSelect = document.getElementById('voiceSelect');
    for (let i = 0; i < voiceSelect.options.length; i++) {
      if (voiceSelect.options[i].dataset.shortName === voice.short_name) {
        voiceSelect.selectedIndex = i;
        break;
      }
    }
    
    updateOutput('Selected voice: ' + voice.name + ' (' + voice.gender + ')', 'success');
  });
  
  return chip;
}

function populateRecommendedVoices() {
  const container = document.getElementById('recommendedVoices');
  container.innerHTML = '';
  RECOMMENDED_VOICES.forEach(voice => {
    container.appendChild(createVoiceChip(voice));
  });
}

// Audio Actions
function showAudioActions() {
  const audioActions = document.getElementById('audioActions');
  audioActions.classList.remove('hidden');
}

function hideAudioActions() {
  const audioActions = document.getElementById('audioActions');
  audioActions.classList.add('hidden');
}

// API Functions
async function loadVoices() {
  setLoading(true);
  updateOutput('Loading voice database...');
  
  try {
    const response = await fetch('/api/voices');
    const data = await response.json();
    
    const languageSelect = document.getElementById('languageSelect');
    const statusIndicator = document.getElementById('statusIndicator');
    
    const statusClass = data.offline_mode ? 'offline' : 'online';
    const statusText = data.offline_mode ? 'Offline - Limited Voices' : 'Online - ' + data.total_voices + ' Voices';
    statusIndicator.className = 'status-indicator ' + statusClass;
    statusIndicator.querySelector('span').textContent = statusText;
    
    languageSelect.innerHTML = '<option value="All">All Languages</option>';
    const languages = data.languages || [];
    languages.sort().forEach(lang => {
      const option = document.createElement('option');
      option.value = lang;
      option.textContent = lang;
      languageSelect.appendChild(option);
    });
    
    if (languages.includes('English')) {
      languageSelect.value = 'English';
    }
    
    updateOutput('Loaded ' + data.total_voices + ' voices', 'success');
    await filterVoices();
    
  } catch (error) {
    updateOutput('Failed to load voices: ' + error.message, 'error');
  } finally {
    setLoading(false);
  }
}

async function filterVoices() {
  const query = document.getElementById('voiceSearch').value.trim();
  const gender = document.getElementById('genderSelect').value;
  const language = query ? 'All' : document.getElementById('languageSelect').value;

  try {
    const url = '/api/filter_voices?language=' + encodeURIComponent(language) + '&search=' + encodeURIComponent(query) + '&gender=' + encodeURIComponent(gender);
    const response = await fetch(url);
    const data = await response.json();

    const voiceSelect = document.getElementById('voiceSelect');
    voiceSelect.innerHTML = '';

    if (data.voices && data.voices.length > 0) {
      data.voices.forEach(voice => {
        const option = document.createElement('option');
        option.value = voice.short_name;
        option.textContent = voice.display_name + ' (' + voice.locale + ')';
        option.dataset.shortName = voice.short_name;
        voiceSelect.appendChild(option);
      });
      updateOutput('Found ' + data.voices.length + ' voices');
    } else {
      voiceSelect.innerHTML = '<option>No voices found</option>';
      updateOutput('No voices found', 'error');
    }

  } catch (error) {
    updateOutput('Filter failed: ' + error.message, 'error');
  }
}

async function previewVoice() {
  const text = document.getElementById('text').value.trim();
  const voice = document.getElementById('voiceSelect').value;
  const speed = parseFloat(document.getElementById('speed').value || '1.0');
  
  if (!text) {
    updateOutput('Please enter text to preview', 'error');
    return;
  }
  
  if (!voice) {
    updateOutput('Please select a voice', 'error');
    return;
  }
  
  setLoading(true);
  updateOutput('Generating preview...');
  
  try {
    const response = await fetch('/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        voice: voice,
        speed: speed,
        text: text.substring(0, 200)
      })
    });
    
    const data = await response.json();
    
    if (data.error) {
      updateOutput('Preview failed: ' + data.error, 'error');
      return;
    }
    
    const player = document.getElementById('player');
    player.src = data.audio_url;
    currentAudioUrl = data.audio_url;
    currentAudioFilename = 'preview.mp3';
    
    try {
      await player.play();
      updateOutput('Preview playing', 'success');
      showAudioActions();
    } catch {
      updateOutput('Preview ready (tap play)', 'success');
      showAudioActions();
    }
    
  } catch (error) {
    updateOutput('Preview failed: ' + error.message, 'error');
  } finally {
    setLoading(false);
  }
}

async function generateSpeech() {
  const text = document.getElementById('text').value.trim();
  const voice = document.getElementById('voiceSelect').value;
  const speed = parseFloat(document.getElementById('speed').value || '1.0');
  const generateBtn = document.getElementById('generateBtn');
  
  if (!text) {
    updateOutput('Please enter text', 'error');
    return;
  }
  
  if (!voice) {
    updateOutput('Please select a voice', 'error');
    return;
  }
  
  setButtonLoading(generateBtn, true);
  updateOutput('Generating audio...');
  
  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ voice: voice, speed: speed, text: text })
    });
    
    const data = await response.json();
    
    if (data.error) {
      updateOutput('Generation failed: ' + data.error, 'error');
      return;
    }
    
    const player = document.getElementById('player');
    player.src = data.audio_url;
    currentAudioUrl = data.audio_url;
    currentAudioFilename = data.filename;
    updateOutput('Audio generated: ' + data.filename, 'success');
    
    try {
      await player.play();
    } catch {
      // Autoplay blocked
    }
    
    showAudioActions();
    
  } catch (error) {
    updateOutput('Generation failed: ' + error.message, 'error');
  } finally {
    setButtonLoading(generateBtn, false);
  }
}

async function downloadAudio() {
  if (!currentAudioUrl) {
    updateOutput('No audio available to download', 'error');
    return;
  }
  
  try {
    const response = await fetch(currentAudioUrl);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentAudioFilename || 'audio.mp3';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    updateOutput('Downloaded: ' + currentAudioFilename, 'success');
  } catch (error) {
    updateOutput('Download failed: ' + error.message, 'error');
  }
}

async function transcribeAudio() {
  if (!currentAudioUrl) {
    updateOutput('No audio available to transcribe', 'error');
    return;
  }
  
  const transcribeAudioBtn = document.getElementById('transcribeAudioBtn');
  setButtonLoading(transcribeAudioBtn, true);
  updateOutput('Transcribing audio...');
  
  try {
    const response = await fetch(currentAudioUrl);
    const blob = await response.blob();
    
    const formData = new FormData();
    formData.append('audio', blob, currentAudioFilename);
    formData.append('model', 'small');
    formData.append('device', 'cpu');
    
    const transcribeResponse = await fetch('/api/transcribe_generated', {
      method: 'POST',
      body: formData
    });
    
    const data = await transcribeResponse.json();
    
    if (data.error) {
      updateOutput('Transcription failed: ' + data.error, 'error');
      return;
    }
    
    const transcript = data.transcript || data.full_text || 'Transcription completed';
    
    // Create and download transcript as txt file
    const txtBlob = new Blob([transcript], { type: 'text/plain' });
    const txtUrl = window.URL.createObjectURL(txtBlob);
    const a = document.createElement('a');
    a.href = txtUrl;
    a.download = 'transcript_' + Date.now() + '.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(txtUrl);
    
    updateOutput('Transcription completed and saved as txt file:\\n\\n' + transcript, 'success');
    
  } catch (error) {
    updateOutput('Transcription failed: ' + error.message, 'error');
  } finally {
    setButtonLoading(transcribeAudioBtn, false);
  }
}

async function transcribeUpload() {
  if (!uploadedAudioFile) {
    updateOutput('Please upload an audio file first', 'error');
    return;
  }
  
  const transcribeUploadBtn = document.getElementById('transcribeUploadBtn');
  setButtonLoading(transcribeUploadBtn, true);
  setLoading(true);
  updateOutput('Transcribing audio...');
  
  try {
    const formData = new FormData();
    formData.append('audio', uploadedAudioFile);
    formData.append('model', 'small');
    formData.append('device', 'cpu');
    
    const response = await fetch('/api/transcribe_upload', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (data.error) {
      updateOutput('Transcription failed: ' + data.error, 'error');
      return;
    }
    
    const transcript = data.transcript || data.full_text || 'Transcription completed';
    
    // Create and download transcript as txt file
    const txtBlob = new Blob([transcript], { type: 'text/plain' });
    const txtUrl = window.URL.createObjectURL(txtBlob);
    const a = document.createElement('a');
    a.href = txtUrl;
    a.download = 'transcript_upload_' + Date.now() + '.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(txtUrl);
    
    updateOutput('Transcription completed and saved as txt file:\\n\\n' + transcript, 'success');
    
  } catch (error) {
    updateOutput('Transcription failed: ' + error.message, 'error');
  } finally {
    setButtonLoading(transcribeUploadBtn, false);
    setLoading(false);
  }
}

async function cleanupSession() {
  setLoading(true);
  updateOutput('Cleaning up...');
  
  try {
    await fetch('/api/cleanup', { method: 'POST' });
    
    document.getElementById('player').src = '';
    document.querySelectorAll('.voice-chip').forEach(c => c.classList.remove('selected'));
    
    uploadedAudioFile = null;
    currentAudioUrl = null;
    currentAudioFilename = null;
    
    const uploadLabel = document.getElementById('uploadLabel');
    uploadLabel.innerHTML = '<i class="fas fa-cloud-upload-alt" style="font-size: 2rem;"></i><span>Choose audio file or drag & drop</span><span style="font-size: 0.875rem; opacity: 0.7;">MP3, WAV, M4A supported</span>';
    uploadLabel.classList.remove('has-file');
    
    hideAudioActions();
    updateOutput('Session cleaned up', 'success');
    
  } catch (error) {
    updateOutput('Cleanup failed: ' + error.message, 'error');
  } finally {
    setLoading(false);
  }
}

// File Upload Handler
function handleFileUpload() {
  const audioUpload = document.getElementById('audioUpload');
  const uploadLabel = document.getElementById('uploadLabel');
  
  audioUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      uploadedAudioFile = file;
      uploadLabel.innerHTML = '<i class="fas fa-check-circle" style="font-size: 2rem; color: var(--primary-green);"></i><span>' + file.name + '</span><span style="font-size: 0.875rem; opacity: 0.7;">(' + (file.size / 1024 / 1024).toFixed(1) + ' MB)</span>';
      uploadLabel.classList.add('has-file');
      updateOutput('File uploaded: ' + file.name, 'success');
    }
  });
  
  uploadLabel.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadLabel.style.borderColor = 'var(--primary-blue)';
  });
  
  uploadLabel.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadLabel.style.borderColor = 'var(--border-medium)';
  });
  
  uploadLabel.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadLabel.style.borderColor = 'var(--border-medium)';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('audio/')) {
        uploadedAudioFile = file;
        audioUpload.files = files;
        uploadLabel.innerHTML = '<i class="fas fa-check-circle" style="font-size: 2rem; color: var(--primary-green);"></i><span>' + file.name + '</span><span style="font-size: 0.875rem; opacity: 0.7;">(' + (file.size / 1024 / 1024).toFixed(1) + ' MB)</span>';
        uploadLabel.classList.add('has-file');
        updateOutput('File uploaded: ' + file.name, 'success');
      } else {
        showToast('Please upload an audio file', 'error');
      }
    }
  });
}

// Smooth Scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  // Theme toggle
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
  
  // Voice controls
  document.getElementById('refreshVoices').addEventListener('click', loadVoices);
  document.getElementById('voiceSearch').addEventListener('input', filterVoices);
  document.getElementById('languageSelect').addEventListener('change', filterVoices);
  document.getElementById('genderSelect').addEventListener('change', filterVoices);
  
  // Text input controls
  document.getElementById('previewBtn').addEventListener('click', previewVoice);
  document.getElementById('generateBtn').addEventListener('click', generateSpeech);
  document.getElementById('cleanupBtn').addEventListener('click', cleanupSession);
  
  // Audio controls
  document.getElementById('transcribeUploadBtn').addEventListener('click', transcribeUpload);
  document.getElementById('downloadAudioBtn').addEventListener('click', downloadAudio);
  document.getElementById('transcribeAudioBtn').addEventListener('click', transcribeAudio);
  
  // Speed control
  document.getElementById('speed').addEventListener('input', (e) => {
    const value = parseFloat(e.target.value);
    if (value < 0.5) e.target.value = '0.5';
    if (value > 2.0) e.target.value = '2.0';
  });
});

// Initialize Application
window.addEventListener('load', () => {
  initTheme();
  populateRecommendedVoices();
  loadVoices();
  handleFileUpload();
  
  // Add fade-in animation to main container
  document.querySelector('.main-container').classList.add('fade-in');
});
</script>
</body>
</html>
"""

# Flask Routes
@app.route('/')
def index():
    """Main page"""
    return HTML_TEMPLATE

@app.route('/api/voices')
def get_voices():
    """Get all voices"""
    offline_mode = len(LANGUAGE_VOICES) <= 3
    return jsonify({
        'languages': list(LANGUAGE_VOICES.keys()),
        'voices': LANGUAGE_VOICES,
        'total_voices': len(VOICE_DATA),
        'offline_mode': offline_mode
    })

@app.route('/api/filter_voices')
def filter_voices():
    """Filter voices"""
    language = request.args.get('language', 'All')
    gender = request.args.get('gender', 'All')
    search = request.args.get('search', '').lower().strip()
    
    if language == "All":
        source_voices = list(VOICE_DATA.values())
    else:
        source_voices = LANGUAGE_VOICES.get(language, [])
    
    filtered = []
    for voice in source_voices:
        if gender != "All" and voice['gender'] != gender:
            continue
        if search and search not in voice['display_name'].lower():
            continue
        filtered.append(voice)
    
    return jsonify({'voices': filtered})

@app.route('/api/preview', methods=['POST'])
def preview_voice():
    """Generate preview"""
    data = request.json
    voice_input = data.get('voice')
    speed = float(data.get('speed', 1.0))
    text = data.get('text', 'Hello! This is a preview.')

    voice_obj = find_voice_by_input(voice_input)
    if not voice_obj:
        return jsonify({'error': 'Invalid voice'}), 400

    try:
        voice_short = voice_obj['short_name']
        rate = calculate_rate_parameter(speed)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        
        session_id = get_session_id()
        if session_id not in TEMP_FILES:
            TEMP_FILES[session_id] = []
        TEMP_FILES[session_id].append(temp_file.name)
        
        async def generate():
            comm = edge_tts.Communicate(text, voice_short, rate=rate)
            await comm.save(temp_file.name)
        
        asyncio.run(generate())
        
        return jsonify({
            'audio_url': f'/audio/{session_id}/{os.path.basename(temp_file.name)}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_speech():
    """Generate speech"""
    data = request.json
    text = data.get('text', '').strip()
    voice_input = data.get('voice')
    speed = float(data.get('speed', 1.0))
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    voice_obj = find_voice_by_input(voice_input)
    if not voice_obj:
        return jsonify({'error': 'Invalid voice'}), 400
    
    try:
        voice_short = voice_obj['short_name']
        rate = calculate_rate_parameter(speed)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        
        session_id = get_session_id()
        if session_id not in TEMP_FILES:
            TEMP_FILES[session_id] = []
        TEMP_FILES[session_id].append(temp_file.name)
        
        async def generate():
            comm = edge_tts.Communicate(text, voice_short, rate=rate)
            await comm.save(temp_file.name)
        
        asyncio.run(generate())
        
        filename = os.path.basename(temp_file.name)
        return jsonify({
            'audio_url': f'/audio/{session_id}/{filename}',
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<session_id>/<filename>')
def serve_audio(session_id, filename):
    """Serve audio files"""
    if session_id in TEMP_FILES:
        for temp_file in TEMP_FILES[session_id]:
            if os.path.basename(temp_file) == filename:
                return send_file(temp_file, as_attachment=False, mimetype='audio/mpeg')
    return "File not found", 404

@app.route('/api/transcribe_upload', methods=['POST'])
def transcribe_upload():
    """Transcribe uploaded audio"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if WHISPER_MODEL is None:
        return jsonify({
            'success': True,
            'engine': 'Mock Engine',
            'transcript': 'This is a mock transcription. Install whisper engines for real transcription.',
            'full_text': 'Mock transcription text'
        })
    
    try:
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_audio.close()  # Close the file to release the lock
        audio_file.save(temp_audio.name)
        
        segments, info = WHISPER_MODEL.transcribe(temp_audio.name, beam_size=5)
        transcript_parts = []
        for segment in segments:
            start_time = timedelta(seconds=int(segment.start))
            timestamp = f"[{start_time}]"
            transcript_parts.append(f"{timestamp} {segment.text.strip()}")
        transcript = '\n'.join(transcript_parts)
        
        os.unlink(temp_audio.name)
        
        return jsonify({
            'success': True,
            'engine': 'Faster Whisper',
            'transcript': transcript,
            'full_text': transcript
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe_generated', methods=['POST'])
def transcribe_generated():
    """Transcribe generated audio"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if WHISPER_MODEL is None:
        return jsonify({
            'success': True,
            'engine': 'Mock Engine',
            'transcript': 'This is a mock transcription of your generated audio. Install whisper engines for real transcription.',
            'full_text': 'Mock transcription of generated audio'
        })
    
    try:
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_audio.close()  # Close the file to release the lock
        audio_file.save(temp_audio.name)
        
        segments, info = WHISPER_MODEL.transcribe(temp_audio.name, beam_size=5)
        transcript_parts = []
        for segment in segments:
            start_time = timedelta(seconds=int(segment.start))
            timestamp = f"[{start_time}]"
            transcript_parts.append(f"{timestamp} {segment.text.strip()}")
        transcript = '\n'.join(transcript_parts)
        
        os.unlink(temp_audio.name)
        
        return jsonify({
            'success': True,
            'engine': 'Faster Whisper',
            'transcript': transcript,
            'full_text': transcript
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_session():
    """Clean up session"""
    session_id = get_session_id()
    cleanup_temp_files(session_id)
    return jsonify({'success': True})

# Initialize app
def initialize_app():
    """Initialize the application"""
    print("Initializing LumoGen Voice Studio...")
    
    try:
        success = asyncio.run(load_voices())
        print(f"Voice loading: {'OK' if success else 'FAILED'}")
    except Exception as e:
        print(f"Voice loading error: {e}")
    
    return True

# Clean up on shutdown
import atexit
def cleanup_all():
    for session_id in list(TEMP_FILES.keys()):
        cleanup_temp_files(session_id)
atexit.register(cleanup_all)

# Initialize
network_ok = initialize_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8001))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)