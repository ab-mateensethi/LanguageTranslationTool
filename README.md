# 🌐 Lingua AI — Language Translation Tool

An AI-powered language translation web app that lets you translate text between 17+ languages in real time, with text-to-speech, copy-to-clipboard and translation history — all wrapped in a clean, modern interface.

**🔗 Live Demo:** [lingua-ai-translate.streamlit.app](https://lingua-ai-translate.streamlit.app)

---

## ✨ Features

- **Real-time translation** across 17+ languages, including English, Urdu, Hindi, Arabic, French, Spanish, German, Chinese, Japanese, Korean, Russian, Turkish, Italian, Portuguese, Bengali, Punjabi and Persian.
- **Reliable translation engine** — powered by Google Translate, with an automatic quality-checked backup translator that kicks in only if Google is temporarily busy, so you always get a trustworthy result.
- **Text-to-speech playback** — listen to the translated text out loud.
- **One-click copy** — copy any translation to your clipboard instantly.
- **Translation history** — your last 10 translations are saved during your session so you can revisit them anytime.
- **Live character counter** and a smooth animated loading indicator while translating.
- **Clean, responsive UI** built with a custom design system — no clutter, just a focused translation workspace.

## 🖥️ Tech Stack

| Layer              | Technology                          |
|---------------------|--------------------------------------|
| Frontend / UI        | Streamlit + custom CSS               |
| Primary translation  | Google Translate (via `deep-translator`) |
| Backup translation   | MyMemory API (quality-filtered)      |
| Text-to-speech       | gTTS (Google Text-to-Speech)         |
| Language             | Python 3.9+                          |

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/ab-mateensethi/LanguageTranslationTool.git
cd LanguageTranslationTool
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\Activate      # Windows
source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

> ⚠️ An active internet connection is required, since the app communicates with Google Translate and MyMemory's translation services.

## 📂 Project Structure

```
LanguageTranslationTool/
│
├── app.py               # Main application — UI, translation logic and text-to-speech
├── requirements.txt      # Python dependencies
├── .gitignore             # Files and folders excluded from version control
└── README.md              # Project documentation
```

## 🧠 How Translation Reliability Works

Free translation services can occasionally be rate-limited or return an unreliable result. This app handles that gracefully:

1. **Google Translate is tried first**, with automatic retries if it's temporarily busy.
2. If Google is unavailable, the app **falls back to MyMemory**, but only accepts the result if it passes a **confidence-score check** — low-quality or suspicious matches are rejected rather than shown to the user.
3. If a backup translation is used, a small notice is displayed so you always know which engine produced your result.

This ensures the app stays functional under load while prioritizing translation accuracy.

## 🔮 Future Improvements

- Support for translating uploaded documents (PDF, DOCX).
- Automatic source language detection.
- Side-by-side pronunciation guide for non-Latin scripts.
- Dark mode toggle.

## 👤 Author

**Abdul Mateen**
Computer Engineering student at the University of Engineering and Technology (UET), Lahore — passionate about exploring the ever-evolving world of technology through code.

🔗 [LinkedIn](https://www.linkedin.com/in/abdul-mateen-a03696392)

---

⭐ If you found this project interesting, consider giving it a star on GitHub!
