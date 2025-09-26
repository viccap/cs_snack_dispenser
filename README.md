# cs_lock_app

Interactive Streamlit experience that explores data privacy consent around opening a smart lock. Visitors must accept a series of conditions, capture a selfie, and provide their email; the app stores the selfie locally, queues a delayed email notification, and calls the Igloohome API (via `test4.py`) to mint a one-time PIN for unlocking the snack box. Twenty-four hours later the queue is processed: the selfie is analysed with the configured LLM, a personalised email is generated, and the selfie plus description are sent to the user via SMTP.

## Project layout

```
cs_lock_app/
├─ streamlit_app.py        # Main Streamlit UI
├─ backend/
│  ├─ code_generator.py    # Wraps test4.generate_one_time_pin()
│  ├─ emailer.py           # Queues + sends delayed emails with LLM content
│  ├─ selfie_llm.py        # Uses image-capable LLM to build email copy
│  ├─ storage.py           # Persists selfies + email queue metadata
│  ├─ test4.py             # Igloohome OTP helper (env-driven)
│  ├─ requirements.txt     # Python dependencies for the app
│  └─ .env.example         # Template for required secrets
└─ README.md
```

> The earlier React/Next prototype remains under `frontend/` but is optional once you adopt the Streamlit experience.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Copy `backend/.env.example` to `backend/.env` and populate:
   - `IGLOO_CLIENT_ID`, `IGLOO_CLIENT_SECRET`, `IGLOO_DEVICE_ID`
   - `LLM_API_KEY` (plus optional overrides for `LLM_BASE_URL`, `LLM_IMAGE_MODEL`, `LLM_EMAIL_MODEL`)
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS`, `EMAIL_SUBJECT`

## Running the app

Launch Streamlit from the repo root (or any directory) with:
```bash
streamlit run cs_lock_app/streamlit_app.py
```
The interface walks through the consent checklist, opens the device camera to take a selfie (`st.camera_input`), collects an email, and then:

1. Saves the selfie to `backend/storage/selfies/`.
2. Stores a follow-up reminder entry (timestamped at request time) in `backend/storage/email_queue.json`.
3. Sends the personalised email immediately via `backend/emailer.schedule_privacy_email`.
4. Invokes `test4.generate_one_time_pin()` to retrieve an OTP from Igloohome and displays it.

On every interaction the app also calls `backend/emailer.process_due_emails`, which double-checks the queue for any missed messages and re-sends if necessary. For each pending entry it:

- Generates a friendly description and personalised email body via `backend/selfie_llm.llm_email_main`.
- Sends the email using the configured SMTP server right away, attaching the stored selfie.
- Marks the queue entry as sent (or failed, with error details).

For production deployments consider running `process_due_emails` in a dedicated background worker or scheduled job so messages are delivered even if no user is interacting with the Streamlit UI.

## Notes

- Ensure `.env` is protected; it contains Igloohome, SMTP, and LLM secrets.
- The emoji-laden loading sequence mirrors the consent theatre from the original React proof-of-concept.
- NFC tags can simply point to the deployed Streamlit URL.
