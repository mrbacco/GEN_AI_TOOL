"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Feb 21, 2026

"""

from flask import Flask, render_template, request, jsonify
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import *
from llm.gemini_client import gemini_chat
from llm.lmstudio_client import lmstudio_chat

from memory.memory_store import save_message, save_message_and_get_memory


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


def bac_log(message):
    if ENABLE_BAC_LOGS:
        print(message)


@app.after_request
def disable_static_cache(response):
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# -------------------------
# HOME
# -------------------------

@app.route("/")
def home():
    bac_log("BAC: GET / requested")

    return render_template("index.html")


# -------------------------
# CHAT
# -------------------------

@app.route("/chat", methods=["POST"])
def chat():
    bac_log("BAC: POST /chat started")

    data = request.json or {}
    bac_log(f"BAC: /chat payload keys = {list(data.keys())}")

    model = data["model"]
    bac_log(f"BAC: /chat model = {model}")

    message = data["message"]
    bac_log(f"BAC: /chat message length = {len(message)}")

    memory = save_message_and_get_memory(model, "user", message, MAX_CONTEXT_MESSAGES)
    bac_log(f"BAC: /chat context size = {len(memory)} for model {model}")

    response = run_model(model, memory)
    bac_log(f"BAC: /chat received response length = {len(response) if response else 0}")

    save_message(model, "assistant", response)
    bac_log(f"BAC: /chat saved assistant response for model {model}")
    bac_log("BAC: POST /chat completed")

    return jsonify({

        "response": response

    })


# -------------------------
# COMPARE
# -------------------------

@app.route("/compare", methods=["POST"])
def compare():
    bac_log("BAC: POST /compare started")

    data = request.json or {}
    bac_log(f"BAC: /compare payload keys = {list(data.keys())}")

    message = data.get("message", "").strip()
    bac_log(f"BAC: /compare message length = {len(message)}")

    models = data.get("models", [])
    bac_log(f"BAC: /compare models = {models}")

    if not message:
        bac_log("BAC: /compare validation failed: empty message")
        return jsonify({"error": "Message is required"}), 400

    if not isinstance(models, list) or not models:
        bac_log("BAC: /compare validation failed: invalid models list")
        return jsonify({"error": "At least one model is required"}), 400

    result = {}
    all_remote = all(model.startswith(("gpt", "gemini")) for model in models)
    workers = 1
    if all_remote:
        workers = max(1, min(len(models), COMPARE_MAX_WORKERS))

    if workers == 1:
        for model in models:
            try:
                result[model] = compare_one_model(model, message)
                bac_log(f"BAC: /compare completed model {model}")
            except Exception as exc:
                bac_log(f"BAC: /compare error for model {model}: {exc}")
                result[model] = f"Error: {exc}"
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(compare_one_model, model, message): model
                for model in models
            }

            for future in as_completed(futures):
                model = futures[future]
                try:
                    result[model] = future.result()
                    bac_log(f"BAC: /compare completed model {model}")
                except Exception as exc:
                    bac_log(f"BAC: /compare error for model {model}: {exc}")
                    result[model] = f"Error: {exc}"

    bac_log("BAC: POST /compare completed")
    return jsonify(result)


# -------------------------
# FILE UPLOAD
# -------------------------

@app.route("/upload", methods=["POST"])
def upload():
    bac_log("BAC: POST /upload started")

    file = request.files["file"]
    bac_log(f"BAC: /upload filename = {file.filename}")

    path = os.path.join(

        app.config["UPLOAD_FOLDER"],

        file.filename

    )

    file.save(path)
    bac_log(f"BAC: /upload saved file to {path}")
    bac_log("BAC: POST /upload completed")

    return jsonify({"status": "ok"})


# -------------------------
# MODEL ROUTER
# -------------------------

def run_model(model, messages):
    bac_log(f"BAC: run_model called with model = {model}, messages = {len(messages)}")

    if model.startswith("gemini"):
        bac_log("BAC: run_model routing to Gemini")
        return gemini_chat(model, messages)

    elif model.startswith("lmstudio"):
        bac_log("BAC: run_model routing to LM Studio")

        return lmstudio_chat(model, messages)

    else:
        raise ValueError(f"Unsupported model: {model}. Use a Gemini model like gemini-1.5-flash.")


def compare_one_model(model, message):
    bac_log(f"BAC: /compare processing model {model}")
    memory = save_message_and_get_memory(model, "user", message, MAX_CONTEXT_MESSAGES)
    bac_log(f"BAC: /compare context size = {len(memory)} for model {model}")
    answer = run_model(model, memory)
    save_message(model, "assistant", answer)
    return answer


# -------------------------

if __name__ == "__main__":
    bac_log(f"BAC: starting Flask app on port 5050 with debug={APP_DEBUG}")

    app.run(debug=APP_DEBUG, port=5050)
