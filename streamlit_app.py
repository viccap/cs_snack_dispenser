from __future__ import annotations

import json
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from backend import code_generator, emailer, storage

load_dotenv()
storage.ensure_storage()

MESSAGES = [
    "Syncing biometric glitter...",
    "Reticulating user reputation...",
    "Consulting pantry surveillance satellites...",
    "Scoring meme alignment...",
    "Decrypting your third-grade report card...",
    "Negotiating with the smart fridge...",
    "Cross-validating with intergalactic snack law...",
]

STEPS = [
    ("Zustimmung", "Verträge & Richtlinien bestätigen"),
    ("Selfie", "Momentaufnahme für die Snack-Akte"),
    ("Email", "Kontakt für die Nachbereitung"),
    ("Code", "Einmal-PIN empfangen"),
]

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;600&display=swap');
:root { color-scheme: dark; }
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 10% 20%, #1e293b 0%, #020617 55%, #000 100%);
    color: #f5f6f7;
    font-family: 'Space Grotesk', 'Inter', sans-serif;
}
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container {
    padding: 2.4rem 2.4rem 3rem;
    max-width: 960px;
}
.hero-card {
    position: relative;
    padding: 2.6rem;
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(99,102,241,0.35), rgba(14,116,144,0.25));
    border: 1px solid rgba(148,163,184,0.25);
    box-shadow: 0 25px 50px rgba(15,23,42,0.4);
    overflow: hidden;
}
.hero-card:before {
    content: "";
    position: absolute;
    inset: -80px;
    background: radial-gradient(circle at top left, rgba(94,234,212,0.35), transparent 65%);
    filter: blur(70px);
}
.hero-badge {
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #a5b4fc;
}
.hero-title {
    font-size: clamp(2.4rem, 4vw, 3.2rem);
    font-weight: 700;
    margin-top: 0.75rem;
    margin-bottom: 0.6rem;
    color: #f8fafc;
}
.hero-sub {
    max-width: 640px;
    color: #cbd5f5;
    font-size: 1.05rem;
}
.stepper {
    display: flex;
    gap: 0.75rem;
    margin: 2.4rem 0 1.6rem;
    flex-wrap: wrap;
}
.step {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.95rem 1.25rem;
    border-radius: 18px;
    border: 1px solid rgba(148,163,184,0.22);
    background: rgba(15,23,42,0.6);
    flex: 1 1 180px;
    min-width: 180px;
    transition: transform 0.3s ease, border-color 0.3s ease, background 0.3s ease;
}
.step:hover { transform: translateY(-2px); }
.step-index {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-weight: 600;
    background: rgba(96,165,250,0.2);
    color: #60a5fa;
}
.step.active {
    border-color: rgba(96,165,250,0.65);
    background: rgba(30,64,175,0.45);
    box-shadow: 0 14px 26px rgba(59,130,246,0.25);
}
.step.active .step-index {
    background: rgba(96,165,250,0.35);
    color: #bfdbfe;
}
.step.done {
    border-color: rgba(34,197,94,0.5);
    background: rgba(21,128,61,0.35);
}
.step.done .step-index {
    background: rgba(34,197,94,0.4);
    color: #bbf7d0;
}
.step-title {
    font-weight: 600;
    color: #f8fafc;
    display: block;
}
.step-desc {
    font-size: 0.85rem;
    color: white;
}
.section-card {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 1.6rem 0;
    margin-bottom: 1.3rem;
    box-shadow: none;
    border-bottom: 1px solid rgba(148,163,184,0.2);
}
.section-card:last-of-type {
    border-bottom: none;
}
.section-card h3 {
    color: #f8fafc;
    margin-bottom: 0.35rem;
}
.section-card [data-testid=\"stMarkdownContainer\"] {
    color: #e2e8f0 !important;
}
.section-card [data-testid=\"stMarkdownContainer\"] * {
    color: #e2e8f0 !important;
}
.section-card .stMarkdown {
    color: #e2e8f0 !important;
}
.section-card .stMarkdown p,
.section-card .stMarkdown span,
.section-card .stMarkdown li {
    color: #e2e8f0 !important;
}
[data-testid="stCaption"] {
    color: #cbd5f5 !important;
}
[data-testid="stCheckbox"] label {
    font-weight: 600;
    color: #ffffff !important;
}
[data-testid="stCheckbox"] label span {
    color: #ffffff !important;
}
.stCheckbox > div:first-child {
    border-radius: 12px;
}
.stButton button {
    background: linear-gradient(135deg, #6366f1, #0ea5e9);
    color: white;
    font-weight: 600;
    border: none;
    border-radius: 999px;
    padding: 0.75rem 1.75rem;
    box-shadow: 0 22px 40px rgba(14,165,233,0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 28px 44px rgba(99,102,241,0.45);
}
.stButton button:disabled {
    background: linear-gradient(135deg, rgba(71,85,105,0.7), rgba(71,85,105,0.45));
    box-shadow: none;
}
[data-testid="stCameraInput"] button {
    background: linear-gradient(135deg, #fbbf24, #f97316);
    color: #0f172a;
    font-weight: 700;
    border: none;
    border-radius: 16px;
    padding: 0.85rem 1.6rem;
    box-shadow: 0 20px 36px rgba(249,115,22,0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stCameraInput"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 26px 44px rgba(251,191,36,0.45);
}
.stTextInput > div > div > input {
    background: rgba(15,23,42,0.85);
    color: #e2e8f0;
    border-radius: 14px;
    border: 1px solid rgba(100,116,139,0.45);
    padding: 0.75rem 0.9rem;
}
.stTextInput > label {
    color: #cbd5f5;
    font-weight: 600;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(96,165,250,0.85);
    box-shadow: 0 0 0 2px rgba(59,130,246,0.3);
}
.stAlert {
    background: rgba(15,23,42,0.8);
    border-radius: 16px;
    border: 1px solid rgba(148,163,184,0.25);
}
img {
    border-radius: 22px !important;
    box-shadow: 0 24px 44px rgba(15,23,42,0.45);
}
.stSpinner > div {
    border-top-color: #38bdf8;
}
.code-block {
    padding: 1rem 1.4rem;
    border-radius: 18px;
    border: 1px solid rgba(148,163,184,0.25);
    background: rgba(2,6,23,0.7);
    font-size: 1.45rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-align: center;
    color: #bbf7d0;
}
@media (max-width: 900px) {
    .block-container {
        padding: 1.8rem 1.6rem 2.5rem;
    }
    .hero-card {
        padding: 2rem;
    }
    .hero-sub {
        font-size: 1rem;
    }
}
@media (max-width: 640px) {
    .block-container {
        padding: 1.2rem 1rem 2rem;
        max-width: 100%;
    }
    .hero-card {
        padding: 1.6rem;
        border-radius: 20px;
        background: transparent;
        border: none;
        box-shadow: none;
    }
    .hero-card:before {
        display: none;
    }
    .hero-sub {
        font-size: 0.95rem;
    }
    .section-card {
        padding: 1.3rem 0;
        margin-bottom: 1.1rem;
        border-bottom-color: rgba(148,163,184,0.12);
    }
    .stepper {
        flex-direction: column;
        gap: 1rem;
    }
    .step {
        flex: 1 1 100%;
        min-width: 100%;
        padding: 0.85rem 1rem;
    }
    .code-block {
        font-size: 1.1rem;
        letter-spacing: 0.16em;
    }
    .stButton button, [data-testid="stCameraInput"] button {
        width: 100%;
        text-align: center;
    }
}
@media (max-width: 480px) {
    .hero-title {
        font-size: 2rem;
    }
    .hero-badge {
        font-size: 0.8rem;
    }
    .hero-card {
        padding: 1.4rem;
    }
}
</style>
"""


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Creative Space • Snack Vault</div>
            <h1 class="hero-title">Daten zuerst, Snacks danach.</h1>
            <p class="hero-sub">
                Stimme den Bedingungen zu, schenke uns dein bestes Selfie, 
                hinterlasse deine Email – und erhalte
                einen temporären Zugangscode zum heiligen Vorrat. 
                Wie viele persönliche Informationen bist du bereit für einen Snack zu geben? 
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stepper(active_stage: int) -> None:
    chips = []
    for idx, (title, desc) in enumerate(STEPS):
        if idx < active_stage:
            state_cls = "step done"
        elif idx == active_stage:
            state_cls = "step active"
        else:
            state_cls = "step"
        chips.append(
            f"""
            <div class="{state_cls}">
                <div class="step-index">{idx + 1}</div>
                <div class="step-body">
                    <span class="step-title">{title}</span>
                    <span class="step-desc">{desc}</span>
                </div>
            </div>
            """
        )
    #st.markdown(f"<div class='stepper'>{''.join(chips)}</div>", unsafe_allow_html=True)


def validate_email(value: str) -> bool:
    return bool(value) and "@" in value and "." in value


def init_state() -> None:
    st.session_state.setdefault("accepted", False)
    st.session_state.setdefault("selfie_bytes", None)
    st.session_state.setdefault("selfie_mime", None)
    st.session_state.setdefault("email", "")
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("error", "")


def render_consent_step() -> None:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### Schritt 1 · Digitale Zustimmung")
    st.caption("Wir lieben Snacks, aber noch mehr lieben wir Checkboxen. Für Informationen über den Inhalt der Richtilinen, schreiben sie uns gerne eine Email. (Bearbeitungszeit 3-4 Werktage) :)")

    policy = st.checkbox("Datenschutzrichtlinie", key="policy")
    terms = st.checkbox("Nutzungsbedingungen", key="terms")
    emails = st.checkbox("Erhalt von E-Mails", key="emails")
    cookies = st.checkbox("Cookies akzeptieren", key="cookies")

    all_checked = policy and terms and emails and cookies
    st.button(
        "✅ Zustimmen & weiter",
        disabled=not all_checked,
        on_click=lambda: st.session_state.update({"accepted": True}),
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_selfie_step() -> None:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### Schritt 2 · Selfie für die Snack-Akte")
    st.caption("Wir archivieren dein strahlendes Gesicht für wissenschaftliche Snack-Zwecke.")

    photo = st.camera_input("Starte die Kamera", key="selfie_input")
    if photo is not None:
        st.session_state.selfie_bytes = photo.getvalue()
        st.session_state.selfie_mime = photo.type
        #st.image(photo, caption="Selfie Vorschau", use_column_width=True)
        st.success("Selfie gespeichert. Gute Haltung!")
    st.markdown("</div>", unsafe_allow_html=True)


def handle_submission(email: str) -> None:
    st.session_state.error = ""

    if not st.session_state.selfie_bytes:
        st.session_state.error = "Bitte mache zuerst ein Selfie."
        return
    if not validate_email(email):
        st.session_state.error = "Bitte gib eine gültige E-Mail-Adresse ein."
        return

    with st.spinner("Bitte warten, wir organisieren deinen Snack-Zauber…"):
        status_placeholder = st.empty()
        for message in MESSAGES:
            status_placeholder.info(message)
            time.sleep(0.65)

        selfie_path = storage.save_selfie_bytes(
            st.session_state.selfie_bytes,
            mime_type=st.session_state.selfie_mime,
        )
        send_at_iso = emailer.schedule_privacy_email(email=email, selfie_path=selfie_path, description=None)

        try:
            code = code_generator.generate_code()
        except code_generator.CodeGenerationError as exc:
            st.session_state.error = f"❌ Fehler bei der Code-Erzeugung: {exc}"
            return

    st.session_state.result = {
        "code": code,
        "selfie_path": str(selfie_path),
        "send_at": send_at_iso,
    }
    st.session_state.email = email
    status_placeholder.empty()
    st.toast("✅ Einmal-PIN generiert – check deine Inbox in Kürze!")


def render_email_step() -> None:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### Schritt 3 · Email für die Nachbesprechung")
    st.caption("Wir melden uns mit einer hochpersönlichen Analyse – die Email landet sofort in deinem Postfach.")

    email = st.text_input("Email-Adresse", value=st.session_state.email or "")
    submit = st.button("✉️ Absenden & Code erhalten")
    if submit:
        handle_submission(email)
    st.markdown("</div>", unsafe_allow_html=True)


def render_result() -> None:
    if st.session_state.error:
        st.error(st.session_state.error)
    if not st.session_state.result:
        return

    result = st.session_state.result
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### Schritt 4 · Dein Snack-Zugang")
    st.success("✅ Hier ist dein temporärer Zugangscode, er wird zur nächsten vollen Stunde aktiviert.")
    st.markdown(f"<div class='code-block'>{result['code']}</div>", unsafe_allow_html=True)

    send_at = result.get("send_at")
    if send_at:
        try:
            send_at_dt = datetime.fromisoformat(send_at)
            st.info(
                "Personalisierte Nachricht wurde soeben ausgelöst "
                f"({send_at_dt.strftime('%d.%m.%Y %H:%M:%S')} UTC)."
            )
        except ValueError:
            st.info("Personalisierte Nachricht wurde soeben versendet.")

    #with st.expander("📄 Audit-Log anzeigen"):
    #    st.write(f"Selfie gespeichert unter: `{result['selfie_path']}`")
    #    raw_output = result.get("raw_output")
    #    try:
    #        parsed = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
    #        st.json(parsed)
    #    except json.JSONDecodeError:
    #        st.write(raw_output)
    #st.markdown("</div>", unsafe_allow_html=True)


def determine_stage() -> int:
    if not st.session_state.accepted:
        return 0
    if st.session_state.accepted and not st.session_state.selfie_bytes:
        return 1
    if st.session_state.accepted and st.session_state.selfie_bytes and not st.session_state.result:
        return 2
    return 3


def main() -> None:
    st.set_page_config(page_title="cs_lock_app", page_icon="🔐", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_state()
    emailer.process_due_emails()

    render_hero()
    render_stepper(determine_stage())

    if not st.session_state.accepted:
        render_consent_step()
    else:
        if not st.session_state.selfie_bytes:
            render_selfie_step()
        render_email_step()

    render_result()


if __name__ == "__main__":
    main()
