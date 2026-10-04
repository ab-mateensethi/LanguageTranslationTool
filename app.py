import html
import io
import json
import time

import streamlit as st
import streamlit.components.v1 as components

from deep_translator import GoogleTranslator, MyMemoryTranslator
from gtts import gTTS


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Lingua AI",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# TRANSLATION BACKEND
# (was a separate translator.py — merged here into one file)
# ============================================================

# Display name -> Google Translate code
SUPPORTED_LANGUAGES = {
    "English": "en",
    "Urdu": "ur",
    "Hindi": "hi",
    "Arabic": "ar",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja",
    "Korean": "ko",
    "Russian": "ru",
    "Turkish": "tr",
    "Italian": "it",
    "Portuguese": "pt",
    "Bengali": "bn",
    "Punjabi": "pa",
    "Persian": "fa",
}

# MyMemory (fallback engine) needs locale-style codes like "en-GB",
# not plain "en". This maps each display name to what MyMemory expects.
_MYMEMORY_CODES = {
    "English": "en-GB",
    "Urdu": "ur-PK",
    "Hindi": "hi-IN",
    "Arabic": "ar-SA",
    "French": "fr-FR",
    "Spanish": "es-ES",
    "German": "de-DE",
    "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja-JP",
    "Korean": "ko-KR",
    "Russian": "ru-RU",
    "Turkish": "tr-TR",
    "Italian": "it-IT",
    "Portuguese": "pt-PT",
    "Bengali": "bn-IN",
    "Punjabi": "pa-IN",
    "Persian": "fa-IR",
}

# Languages gTTS can reliably speak (covers everything above)
TTS_SUPPORTED_LANGUAGES = set(SUPPORTED_LANGUAGES.keys())


def translate_text(text: str, source_language: str, target_language: str):
    """
    Translate `text` from `source_language` to `target_language`
    (both given as display names, e.g. "English", "Urdu").

    Tries Google Translate first, retrying a few times with an increasing
    delay if it is rate-limited, then falls back to MyMemory so the app
    keeps working either way.

    Returns a tuple: (translated_text, used_fallback: bool)
    """
    source_code = SUPPORTED_LANGUAGES.get(source_language)
    target_code = SUPPORTED_LANGUAGES.get(target_language)

    if source_code is None or target_code is None:
        raise ValueError("Unsupported language selected.")

    last_error = None

    # 1) Try Google Translate, retrying with an increasing delay each time
    #    a rate-limit error is hit. This gives Google's server more time
    #    to allow requests again, so we rarely need the (less accurate)
    #    backup translator.
    retry_delays = [1.5, 3, 4.5]  # seconds to wait before each retry
    for attempt in range(len(retry_delays) + 1):
        try:
            result = GoogleTranslator(source=source_code, target=target_code).translate(text)
            return result, False
        except Exception as e:
            last_error = e
            if "too many requests" in str(e).lower() or "429" in str(e):
                if attempt < len(retry_delays):
                    time.sleep(retry_delays[attempt])
                    continue
            else:
                break  # a different kind of error, no point retrying Google

    # 2) Fallback: MyMemory (needs locale-style codes)
    try:
        mm_source = _MYMEMORY_CODES.get(source_language, "en-GB")
        mm_target = _MYMEMORY_CODES.get(target_language, target_code)
        result = MyMemoryTranslator(source=mm_source, target=mm_target).translate(text)
        return result, True
    except Exception as e:
        raise RuntimeError(
            f"Google Translate failed ({last_error}) and the backup "
            f"translator also failed ({e}). Please try again in a moment."
        )


def text_to_speech_bytes(text: str, language_name: str) -> bytes:
    """Convert text to speech and return the audio as in-memory mp3 bytes."""
    lang_code = SUPPORTED_LANGUAGES.get(language_name, "en")
    tts = gTTS(text=text, lang=lang_code)
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.read()


# ============================================================
# SESSION STATE
# ============================================================

if "translation" not in st.session_state:
    st.session_state.translation = ""

if "history" not in st.session_state:
    st.session_state.history = []

if "translation_input" not in st.session_state:
    st.session_state.translation_input = ""

if "tts_audio" not in st.session_state:
    st.session_state.tts_audio = None

if "used_fallback" not in st.session_state:
    st.session_state.used_fallback = False


# ============================================================
# CALLBACKS
# ============================================================

def clear_workspace():
    """
    Clear the input widget and translation result.
    This callback runs before Streamlit renders the widget,
    so the widget state can be safely changed.
    """
    st.session_state.translation_input = ""
    st.session_state.translation = ""
    st.session_state.tts_audio = None
    st.session_state.used_fallback = False


def clear_history():
    """
    Clear all recent translations.
    """
    st.session_state.history = []


# ============================================================
# HISTORY SAFETY
# ============================================================

if not isinstance(st.session_state.history, list):
    st.session_state.history = []


# ============================================================
# COLORS
# ============================================================

BG = "#f6f8fc"
CARD = "#ffffff"
INPUT_BG = "#ffffff"
TEXT = "#101828"
MUTED = "#64748b"
BORDER = "#dfe5ee"

RED = "#e3342f"


# ============================================================
# CUSTOM CSS
# ============================================================

st.html(
    f"""
    <style>

        /* ====================================================
           APP
           ==================================================== */

        [data-testid="stAppViewContainer"] {{
            background: {BG};
        }}

        [data-testid="stHeader"] {{
            background: transparent !important;
        }}

        [data-testid="stDecoration"] {{
            display: none !important;
        }}

        [data-testid="stToolbar"] {{
            display: none !important;
        }}

        .block-container {{
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}


        /* ====================================================
           GENERAL
           ==================================================== */

        p,
        label,
        div,
        button,
        textarea {{
            font-family: Inter, Arial, sans-serif;
        }}


        /* ====================================================
           BRAND
           ==================================================== */

        .lingua-brand {{
            font-size: 34px;
            font-weight: 800;
            letter-spacing: -1.5px;
            color: {TEXT};
        }}

        .lingua-ai {{
            color: {RED};
        }}

        .workspace-subtitle {{
            color: {MUTED};
            font-size: 16px;
            margin-top: 5px;
        }}


        /* ====================================================
           HERO
           ==================================================== */

        .hero-title {{
            font-size: clamp(38px, 5vw, 68px);
            line-height: 1.02;
            font-weight: 800;
            letter-spacing: -3px;
            color: {TEXT};
            margin-top: 55px;
            margin-bottom: 18px;
        }}

        .hero-red {{
            color: {RED};
        }}

        .hero-description {{
            color: {MUTED};
            font-size: 18px;
            line-height: 1.7;
            max-width: 1000px;
            margin-bottom: 35px;
        }}


        /* ====================================================
           FEATURE CARDS
           ==================================================== */

        .feature-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 24px;
            height: 160px;
            box-sizing: border-box;
        }}

        .feature-number {{
            color: {RED};
            font-size: 13px;
            font-weight: 800;
            margin-bottom: 12px;
        }}

        .feature-heading {{
            color: {TEXT};
            font-size: 18px;
            font-weight: 750;
            margin-bottom: 8px;
        }}

        .feature-text {{
            color: {MUTED};
            font-size: 14px;
            line-height: 1.6;
        }}


        /* ====================================================
           SECTION
           ==================================================== */

        .section-heading {{
            color: {TEXT};
            font-size: 24px;
            font-weight: 750;
            margin-top: 42px;
            margin-bottom: 18px;
        }}


        /* ====================================================
           LABELS
           ==================================================== */

        [data-testid="stWidgetLabel"] p {{
            color: {TEXT} !important;
            font-weight: 650 !important;
        }}


        /* ====================================================
           SELECT BOX
           ==================================================== */

        [data-baseweb="select"] > div {{
            background: {INPUT_BG} !important;
            border-color: {BORDER} !important;
            color: {TEXT} !important;
        }}


        /* ====================================================
           TEXT AREA
           ==================================================== */

        textarea {{
            background: {INPUT_BG} !important;
            color: {TEXT} !important;
            border-color: {BORDER} !important;
            border-radius: 12px !important;
            font-size: 16px !important;
            line-height: 1.6 !important;
        }}

        textarea:focus {{
            border-color: {RED} !important;
            box-shadow: 0 0 0 1px {RED} !important;
        }}


        /* ====================================================
           TRANSLATION OUTPUT
           ==================================================== */

        .translation-output {{
            background: {INPUT_BG};
            border: 1px solid {BORDER};
            border-radius: 12px;
            height: 300px;
            padding: 18px;
            color: {TEXT};
            font-size: 16px;
            line-height: 1.7;
            white-space: pre-wrap;
            overflow-y: auto;
            overflow-wrap: anywhere;
            box-sizing: border-box;
        }}

        .translation-empty {{
            color: {MUTED};
            text-align: center;
            padding-top: 105px;
        }}


        /* ====================================================
           CHARACTER COUNTER
           ==================================================== */

        .character-counter {{
            color: {MUTED};
            text-align: right;
            font-size: 12px;
            margin-top: 5px;
        }}


        /* ====================================================
           MAIN BUTTONS
           ==================================================== */

        .stButton > button {{
            width: 100%;
            min-height: 44px;
            border-radius: 10px;
            border: 1px solid {BORDER};
            background: {CARD};
            color: {TEXT};
            font-weight: 700;
            transition: all 0.15s ease;
        }}

        .stButton > button:hover {{
            border-color: {RED};
            color: {RED};
        }}

        .stButton > button[kind="primary"] {{
            background: {RED};
            color: white;
            border-color: {RED};
        }}

        .stButton > button[kind="primary"]:hover {{
            background: #c92d28;
            border-color: #c92d28;
            color: white;
        }}


        /* ====================================================
           CLEAR HISTORY BUTTON
           ==================================================== */

        .clear-cache-wrapper {{
            margin-top: 4px;
            margin-bottom: 5px;
        }}


        /* ====================================================
           HISTORY
           ==================================================== */

        .history-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 12px;
        }}

        .history-language {{
            color: {RED};
            font-size: 13px;
            font-weight: 750;
            margin-bottom: 7px;
        }}

        .history-source {{
            color: {TEXT};
            font-size: 14px;
            margin-bottom: 5px;
        }}

        .history-result {{
            color: {MUTED};
            font-size: 14px;
            line-height: 1.5;
        }}


        /* ====================================================
           FOOTER
           ==================================================== */

        .footer {{
            border-top: 1px solid {BORDER};
            margin-top: 55px;
            padding-top: 22px;
            padding-bottom: 5px;
            text-align: center;
            color: {MUTED};
            font-size: 13px;
            line-height: 1.7;
        }}

        .footer-name {{
            color: {TEXT};
            font-weight: 750;
        }}


        /* ====================================================
           LOADING SPINNER
           ==================================================== */

        @keyframes lingua-spin {{
            0%   {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .lingua-loading-wrapper {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 4px;
        }}

        .lingua-spinner {{
            width: 22px;
            height: 22px;
            border: 3px solid {BORDER};
            border-top-color: {RED};
            border-radius: 50%;
            animation: lingua-spin 0.7s linear infinite;
            flex-shrink: 0;
        }}

        .lingua-loading-text {{
            color: {TEXT};
            font-size: 15px;
            font-weight: 650;
        }}

    </style>
    """
)


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns(
    [8, 1],
    vertical_alignment="top",
)


# ============================================================
# BRAND
# ============================================================

with header_left:

    st.html(
        f"""
        <div class="lingua-brand">
            🌐 Lingua <span class="lingua-ai">AI</span>
        </div>

        <div class="workspace-subtitle">
            Translation Workspace
        </div>
        """
    )


# ============================================================
# HERO
# ============================================================

st.html(
    """
    <div class="hero-title">
        Translate without
        <span class="hero-red">language barriers</span>
    </div>

    <div class="hero-description">
        Enter your message, choose a source language and destination language,
        then translate your content through a clean global workspace.
    </div>
    """
)


# ============================================================
# FEATURE CARDS
# ============================================================

feature_1, feature_2, feature_3 = st.columns(3)


with feature_1:

    st.html(
        """
        <div class="feature-card">
            <div class="feature-number">01</div>
            <div class="feature-heading">Global Languages</div>
            <div class="feature-text">
                Translate your content across multiple supported languages
                through one workspace.
            </div>
        </div>
        """
    )


with feature_2:

    st.html(
        """
        <div class="feature-card">
            <div class="feature-number">02</div>
            <div class="feature-heading">Fast Translation</div>
            <div class="feature-text">
                Send your text to the translation service and receive
                the translated result.
            </div>
        </div>
        """
    )


with feature_3:

    st.html(
        """
        <div class="feature-card">
            <div class="feature-number">03</div>
            <div class="feature-heading">Smart Experience</div>
            <div class="feature-text">
                Copy and clear your translation with simple
                workspace controls.
            </div>
        </div>
        """
    )


# ============================================================
# WORKSPACE
# ============================================================

st.html(
    '<div class="section-heading">Translation Workspace</div>'
)


# ============================================================
# LANGUAGE SELECTION
# ============================================================

languages = list(SUPPORTED_LANGUAGES.keys())


source_index = (
    languages.index("English")
    if "English" in languages
    else 0
)


target_index = (
    languages.index("Urdu")
    if "Urdu" in languages
    else min(1, len(languages) - 1)
)


source_col, target_col = st.columns(
    2,
    gap="large",
)


with source_col:

    source_language = st.selectbox(
        "Source language",
        languages,
        index=source_index,
        key="source_language",
    )


with target_col:

    target_language = st.selectbox(
        "Destination language",
        languages,
        index=target_index,
        key="target_language",
    )


# ============================================================
# INPUT / OUTPUT
# ============================================================

input_col, output_col = st.columns(
    2,
    gap="large",
)


# ============================================================
# INPUT
# ============================================================

with input_col:

    st.markdown("**Your text**")

    input_text = st.text_area(
        "Your text",
        height=300,
        placeholder="Type or paste your text here...",
        label_visibility="collapsed",
        key="translation_input",
    )

    st.html(
        f"""
        <div class="character-counter">
            {len(input_text)} characters
        </div>
        """
    )


# ============================================================
# OUTPUT
# ============================================================

with output_col:

    st.markdown("**Translation**")

    if st.session_state.translation:

        safe_translation = html.escape(
            str(st.session_state.translation)
        )

        st.html(
            f"""
            <div class="translation-output">{safe_translation}</div>
            """
        )

        if st.session_state.used_fallback:

            st.caption(
                "⚠️ Google Translate was busy, so a backup translator was "
                "used. Please double-check important translations, or "
                "wait a moment and translate again for the primary engine."
            )

    else:

        st.html(
            """
            <div class="translation-output">
                <div class="translation-empty">
                    Your translation will appear here.
                </div>
            </div>
            """
        )


# ============================================================
# MAIN ACTION BUTTONS
# ============================================================

translate_col, copy_col, clear_col = st.columns(
    3,
    gap="medium",
)


# ============================================================
# TRANSLATE BUTTON
# ============================================================

with translate_col:

    translate_clicked = st.button(
        "Translate",
        type="primary",
        use_container_width=True,
        key="translate_button",
    )


# ============================================================
# COPY BUTTON
# ============================================================

with copy_col:

    # --------------------------------------------------------
    # No translation yet
    # --------------------------------------------------------

    if not st.session_state.translation:

        st.button(
            "Copy",
            use_container_width=True,
            disabled=True,
            key="copy_disabled_button",
        )

    # --------------------------------------------------------
    # Translation available
    # --------------------------------------------------------

    else:

        translation_for_copy = json.dumps(
            str(st.session_state.translation),
            ensure_ascii=False,
        )

        components.html(
            f"""
            <!DOCTYPE html>
            <html>

            <head>

                <meta charset="UTF-8">

                <style>

                    * {{
                        box-sizing: border-box;
                    }}

                    body {{
                        margin: 0;
                        padding: 0;
                        background: transparent;
                        font-family:
                            Inter,
                            Arial,
                            sans-serif;
                    }}

                    .copy-wrapper {{
                        width: 100%;
                        position: relative;
                    }}

                    .copy-button {{
                        width: 100%;
                        min-height: 44px;

                        border-radius: 10px;

                        border: 1px solid {BORDER};

                        background: {CARD};

                        color: {TEXT};

                        font-family:
                            Inter,
                            Arial,
                            sans-serif;

                        font-size: 14px;
                        font-weight: 700;

                        cursor: pointer;

                        transition:
                            border-color 0.15s ease,
                            color 0.15s ease,
                            background 0.15s ease;
                    }}

                    .copy-button:hover {{
                        border-color: {RED};
                        color: {RED};
                    }}

                    .copy-button:active {{
                        transform: translateY(1px);
                    }}

                    .copy-toast {{
                        position: fixed;

                        left: 50%;
                        bottom: 8px;

                        transform:
                            translateX(-50%)
                            translateY(10px);

                        display: flex;
                        align-items: center;
                        gap: 8px;

                        padding: 9px 13px;

                        border-radius: 9px;

                        background: #101828;

                        color: #ffffff;

                        font-size: 13px;
                        font-weight: 600;

                        white-space: nowrap;

                        opacity: 0;

                        pointer-events: none;

                        box-shadow:
                            0 8px 24px
                            rgba(0, 0, 0, 0.20);

                        transition:
                            opacity 0.2s ease,
                            transform 0.2s ease;

                        z-index: 999999;
                    }}

                    .copy-toast.show {{
                        opacity: 1;

                        transform:
                            translateX(-50%)
                            translateY(0);
                    }}

                    .toast-icon {{
                        width: 17px;
                        height: 17px;

                        border-radius: 50%;

                        display: flex;
                        align-items: center;
                        justify-content: center;

                        background: #ffffff;
                        color: #101828;

                        font-size: 11px;
                        font-weight: 800;
                    }}

                </style>

            </head>

            <body>

                <div class="copy-wrapper">

                    <button
                        id="copyButton"
                        class="copy-button"
                        type="button"
                    >
                        Copy
                    </button>

                    <div
                        id="copyToast"
                        class="copy-toast"
                    >

                        <span class="toast-icon">
                            ✓
                        </span>

                        <span id="toastText">
                            Translation copied
                        </span>

                    </div>

                </div>


                <script>

                    const translation =
                        {translation_for_copy};


                    const button =
                        document.getElementById(
                            "copyButton"
                        );


                    const toast =
                        document.getElementById(
                            "copyToast"
                        );


                    const toastText =
                        document.getElementById(
                            "toastText"
                        );


                    let toastTimer = null;


                    function showToast(
                        message
                    ) {{

                        toastText.textContent =
                            message;

                        toast.classList.add(
                            "show"
                        );

                        if (toastTimer) {{
                            clearTimeout(
                                toastTimer
                            );
                        }}

                        toastTimer =
                            setTimeout(
                                function() {{
                                    toast.classList.remove(
                                        "show"
                                    );
                                }},
                                2200
                            );
                    }}


                    async function copyTranslation() {{

                        let copied = false;


                        // =================================================
                        // METHOD 1 — Modern Clipboard API
                        // =================================================

                        try {{

                            if (
                                navigator.clipboard &&
                                window.isSecureContext
                            ) {{

                                await navigator
                                    .clipboard
                                    .writeText(
                                        translation
                                    );

                                copied = true;

                            }}

                        }} catch (error) {{

                            copied = false;

                        }}


                        // =================================================
                        // METHOD 2 — Textarea fallback
                        // =================================================

                        if (!copied) {{

                            try {{

                                const textarea =
                                    document.createElement(
                                        "textarea"
                                    );

                                textarea.value =
                                    translation;

                                textarea.setAttribute(
                                    "readonly",
                                    ""
                                );

                                textarea.style.position =
                                    "fixed";

                                textarea.style.top =
                                    "0";

                                textarea.style.left =
                                    "-9999px";

                                textarea.style.opacity =
                                    "0";

                                document.body.appendChild(
                                    textarea
                                );

                                textarea.focus();

                                textarea.select();

                                textarea.setSelectionRange(
                                    0,
                                    textarea.value.length
                                );


                                copied =
                                    document.execCommand(
                                        "copy"
                                    );


                                document.body.removeChild(
                                    textarea
                                );

                            }} catch (error) {{

                                copied = false;

                            }}

                        }}


                        // =================================================
                        // RESULT
                        // =================================================

                        if (copied) {{

                            showToast(
                                "Translation copied"
                            );

                        }} else {{

                            showToast(
                                "Copy failed. Please try again."
                            );

                        }}

                    }}


                    button.addEventListener(
                        "click",
                        copyTranslation
                    );

                </script>

            </body>

            </html>
            """,
            height=54,
            scrolling=False,
        )


# ============================================================
# CLEAR BUTTON
# ============================================================

with clear_col:

    st.button(
        "Clear",
        use_container_width=True,
        key="clear_button",
        on_click=clear_workspace,
    )


# ============================================================
# LOADING PLACEHOLDER
# (filled in with a custom spinning circle while translating)
# ============================================================

loading_placeholder = st.empty()


# ============================================================
# TEXT-TO-SPEECH ROW  (only shown once a translation exists)
# ============================================================

if st.session_state.translation and target_language in TTS_SUPPORTED_LANGUAGES:

    listen_col, _spacer_col = st.columns([1, 2], gap="medium")

    with listen_col:

        listen_clicked = st.button(
            "🔊 Listen (Text-to-Speech)",
            use_container_width=True,
            key="listen_button",
        )

    if listen_clicked:

        try:

            with st.spinner("Generating audio..."):

                st.session_state.tts_audio = text_to_speech_bytes(
                    str(st.session_state.translation),
                    target_language,
                )

        except Exception as error:

            st.error(f"Could not generate audio: {error}")

    if st.session_state.tts_audio:

        st.audio(st.session_state.tts_audio, format="audio/mp3")


# ============================================================
# TRANSLATE ACTION
# ============================================================

if translate_clicked:

    text = input_text.strip()


    # --------------------------------------------------------
    # Empty input
    # --------------------------------------------------------

    if not text:

        st.warning(
            "Please enter some text to translate."
        )


    # --------------------------------------------------------
    # Same source and destination
    # --------------------------------------------------------

    elif source_language == target_language:

        st.session_state.translation = text
        st.session_state.tts_audio = None
        st.session_state.used_fallback = False

        st.session_state.history.insert(
            0,
            {
                "source_language": source_language,
                "target_language": target_language,
                "source_text": text,
                "translated_text": text,
            },
        )

        st.session_state.history = (
            st.session_state.history[:10]
        )

        st.rerun()


    # --------------------------------------------------------
    # Normal translation
    # --------------------------------------------------------

    else:

        try:

            loading_placeholder.html(
                """
                <div class="lingua-loading-wrapper">
                    <div class="lingua-spinner"></div>
                    <div class="lingua-loading-text">Translating...</div>
                </div>
                """
            )

            translated, used_fallback = translate_text(
                text,
                source_language,
                target_language,
            )

            loading_placeholder.empty()


            st.session_state.translation = (
                translated
            )

            st.session_state.tts_audio = None
            st.session_state.used_fallback = used_fallback


            st.session_state.history.insert(
                0,
                {
                    "source_language": source_language,
                    "target_language": target_language,
                    "source_text": text,
                    "translated_text": translated,
                },
            )


            st.session_state.history = (
                st.session_state.history[:10]
            )


            st.rerun()


        except Exception as error:

            loading_placeholder.empty()

            st.error(
                f"Translation failed: {error}"
            )


# ============================================================
# RECENT TRANSLATIONS
# ============================================================

if st.session_state.history:

    st.html(
        '<div class="section-heading">'
        'Recent translations'
        '</div>'
    )


    # ========================================================
    # CLEAR HISTORY BUTTON
    # ========================================================

    clear_cache_clicked = st.button(
        "Clear History",
        type="primary",
        use_container_width=False,
        key="clear_cache_button",
        on_click=clear_history,
    )


    for item in st.session_state.history:

        source = html.escape(
            str(
                item.get(
                    "source_text",
                    "",
                )
            )
        )


        result = html.escape(
            str(
                item.get(
                    "translated_text",
                    "",
                )
            )
        )


        source_language_history = html.escape(
            str(
                item.get(
                    "source_language",
                    "",
                )
            )
        )


        target_language_history = html.escape(
            str(
                item.get(
                    "target_language",
                    "",
                )
            )
        )


        language_pair = (
            f"{source_language_history} → "
            f"{target_language_history}"
        )


        st.html(
            f"""
            <div class="history-card">

                <div class="history-language">
                    {language_pair}
                </div>

                <div class="history-source">
                    {source}
                </div>

                <div class="history-result">
                    {result}
                </div>

            </div>
            """
        )


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="footer">

        © 2026 Lingua AI · Crafted by
        <span class="footer-name">
            Abdul Mateen
        </span>

        <br>

        AI &amp; Machine Learning Developer

    </div>
    """
)