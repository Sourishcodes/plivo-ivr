# Plivo IVR Demo

A demo IVR built with Plivo's Voice API and Flask. It places an outbound call, authenticates
the caller with a 4-digit OTP (birthdate in DDMM), then offers a two-level menu.

## Call flow

```
Outbound call -> OTP (re-prompts until correct)
  -> Level 1: 1 = English, 2 = Spanish
    -> Level 2: 1 = play audio message, 2 = forward to live associate
```

Invalid or missing input repeats the current prompt.

## Requirements

- Python 3.9+
- A Plivo account (Auth ID, Auth Token, a Plivo voice number)
- [ngrok](https://ngrok.com) (Plivo needs a public URL to reach the local server)

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in:
   - `PLIVO_AUTH_ID` and `PLIVO_AUTH_TOKEN` (from the Plivo console)
   - `PLIVO_NUMBER` (the Plivo number calls are made from)
   - `ASSOCIATE_NUMBER` (live associate number, country code, no `+`)
   - `YOUR_PHONE` (your phone in international format, e.g. `+91XXXXXXXXXX`)
3. In `app.py`, set `CORRECT_OTP` to your birthdate in DDMM format.
4. Start ngrok in a separate terminal:
   ```
   ngrok http 5000
   ```
   Copy the `https://...` URL into `BASE_URL` in `.env` (no trailing slash).

## Run and test

1. Start the server:
   ```
   python app.py
   ```
2. Open `http://localhost:5000` in your browser. Enter your number and click **Call me**.
   The page shows a live log of each step of the call. (You can also trigger a call with
   `curl -X POST http://localhost:5000/call -d "to=+91XXXXXXXXXX"`.)
3. Answer the call and test:
   - Enter a wrong OTP, then the correct one
   - Choose a language, then press 1 (audio) or 2 (associate)
   - Press an invalid key to hear the prompt repeat

Note: trial Plivo accounts can only call verified (sandbox) numbers.
If you restart ngrok, update `BASE_URL` and restart the server.

## Routes

| Route | Purpose |
|---|---|
| `/` | Demo front end (call button + live call log) |
| `/call`, `/events` | Starts the outbound call; returns the live event log |
| `/answer` | Plays the OTP prompt |
| `/check_otp` | Verifies OTP, re-prompts if wrong |
| `/language`, `/language_choice` | Level 1 menu |
| `/menu`, `/action` | Level 2 menu (audio or forward) |

## Security

Credentials are read from environment variables and `.env` is git-ignored. Never commit real credentials.
