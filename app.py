"""Plivo demo IVR: outbound call -> OTP -> language menu -> audio / live associate."""
import os
import time
import plivo
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify, render_template

load_dotenv()

AUTH_ID = os.getenv("PLIVO_AUTH_ID")
AUTH_TOKEN = os.getenv("PLIVO_AUTH_TOKEN")
PLIVO_NUMBER = os.getenv("PLIVO_NUMBER")
DEFAULT_PHONE = os.getenv("YOUR_PHONE", "")
BASE_URL = (os.getenv("BASE_URL") or "").rstrip("/")
ASSOCIATE = os.getenv("ASSOCIATE_NUMBER", "912264236412")  # country code, no + or leading 0

CORRECT_OTP = "3105"

AUDIO_URL = "https://s3.amazonaws.com/plivocloud/Trumpet.mp3"

client = plivo.RestClient(AUTH_ID, AUTH_TOKEN)
app = Flask(__name__)

# In-memory event log, shown live on the demo page
EVENTS = []


def log(message):
    EVENTS.append({"t": time.strftime("%H:%M:%S"), "msg": message})


def xml(body):
    return Response(body, mimetype="text/xml")


def speak(text, lang):
    if lang == "es":
        return f'<Speak language="es-ES" voice="WOMAN">{text}</Speak>'
    return f"<Speak>{text}</Speak>"


# ---------- Demo front end ----------
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", default_phone=DEFAULT_PHONE)


@app.route("/call", methods=["POST"])
def call():
    to = (request.form.get("to") or DEFAULT_PHONE).strip()
    EVENTS.clear()
    try:
        client.calls.create(
            from_=PLIVO_NUMBER,
            to_=to,
            answer_url=f"{BASE_URL}/answer",
            answer_method="POST",
        )
    except Exception as e:
        log(f"Call failed: {e}")
        return jsonify(ok=False, message=str(e)), 400
    log(f"Calling {to} ...")
    return jsonify(ok=True, message=f"Calling {to} ...")


@app.route("/events", methods=["GET"])
def events():
    return jsonify(EVENTS)


# ---------- OTP authentication ----------
@app.route("/answer", methods=["GET", "POST"])
def answer():
    log("Call answered. Asking for OTP.")
    return xml(f"""
    <Response>
      <GetDigits action="{BASE_URL}/check_otp" method="POST" numDigits="4" timeout="10">
        <Speak>Please enter your 4 digit OTP.</Speak>
      </GetDigits>
      <Redirect>{BASE_URL}/answer</Redirect>
    </Response>""")


@app.route("/check_otp", methods=["GET", "POST"])
def check_otp():
    digits = request.values.get("Digits", "")
    if digits == CORRECT_OTP:
        log("OTP correct.")
        return xml(f"""
        <Response>
          <Speak>OTP correct. Welcome.</Speak>
          <Redirect>{BASE_URL}/language</Redirect>
        </Response>""")
    log("Wrong OTP entered. Re-prompting.")
    return xml(f"""
    <Response>
      <Speak>Wrong OTP. Please try again.</Speak>
      <Redirect>{BASE_URL}/answer</Redirect>
    </Response>""")


# ---------- Level 1: language ----------
@app.route("/language", methods=["GET", "POST"])
def language():
    log("Level 1: asking for language.")
    return xml(f"""
    <Response>
      <GetDigits action="{BASE_URL}/language_choice" method="POST" numDigits="1" timeout="10">
        <Speak>Press 1 for English.</Speak>
        <Speak language="es-ES" voice="WOMAN">Presione 2 para español.</Speak>
      </GetDigits>
      <Redirect>{BASE_URL}/language</Redirect>
    </Response>""")


@app.route("/language_choice", methods=["GET", "POST"])
def language_choice():
    digit = request.values.get("Digits", "")
    if digit == "1":
        log("Language chosen: English.")
        return xml(f"<Response><Redirect>{BASE_URL}/menu?lang=en</Redirect></Response>")
    if digit == "2":
        log("Language chosen: Spanish.")
        return xml(f"<Response><Redirect>{BASE_URL}/menu?lang=es</Redirect></Response>")
    log("Invalid language choice. Repeating.")
    return xml(f"""
    <Response>
      <Speak>Invalid choice.</Speak>
      <Redirect>{BASE_URL}/language</Redirect>
    </Response>""")


# ---------- Level 2: audio or live associate ----------
@app.route("/menu", methods=["GET", "POST"])
def menu():
    lang = request.values.get("lang", "en")
    log("Level 2: asking for action (audio or associate).")
    prompt = {
        "en": "Press 1 to hear an audio message. Press 2 to talk to a live associate.",
        "es": "Presione 1 para escuchar un mensaje de audio. Presione 2 para hablar con un asociado.",
    }[lang]
    return xml(f"""
    <Response>
      <GetDigits action="{BASE_URL}/action?lang={lang}" method="POST" numDigits="1" timeout="10">
        {speak(prompt, lang)}
      </GetDigits>
      <Redirect>{BASE_URL}/menu?lang={lang}</Redirect>
    </Response>""")


@app.route("/action", methods=["GET", "POST"])
def action():
    lang = request.values.get("lang", "en")
    digit = request.values.get("Digits", "")
    if digit == "1":
        log("Playing audio message.")
        return xml(f"<Response><Play>{AUDIO_URL}</Play></Response>")
    if digit == "2":
        log("Forwarding call to live associate.")
        connecting = {"en": "Connecting you to an associate.",
                      "es": "Conectándolo con un asociado."}[lang]
        return xml(f"""
        <Response>
          {speak(connecting, lang)}
          <Dial callerId="{PLIVO_NUMBER}"><Number>{ASSOCIATE}</Number></Dial>
        </Response>""")
    log("Invalid action choice. Repeating.")
    invalid = {"en": "Invalid choice.", "es": "Opción inválida."}[lang]
    return xml(f"""
    <Response>
      {speak(invalid, lang)}
      <Redirect>{BASE_URL}/menu?lang={lang}</Redirect>
    </Response>""")


if __name__ == "__main__":
    app.run(port=5000)
