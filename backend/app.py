import os

from flask import Flask, jsonify, request

from backend.rules import get_quests

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/quest")
def quest_post():
    body = request.get_json(silent=True) or {}
    temperature = body.get("temperature")

    if temperature is None:
        return jsonify({"error": "temperature is required"}), 400

    try:
        result = get_quests(
            temperature=temperature,
            unit=body.get("unit"),
            condition=body.get("condition"),
            humidity=body.get("humidity"),
            wind_speed=body.get("windSpeed"),
        )
        return jsonify(result)
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


# Convenience GET for quick testing via query params, e.g.
# /api/quest?temperature=10&unit=C&condition=rain
@app.get("/api/quest")
def quest_get():
    temperature = request.args.get("temperature")

    if temperature is None:
        return jsonify({"error": "temperature is required"}), 400

    try:
        result = get_quests(
            temperature=temperature,
            unit=request.args.get("unit"),
            condition=request.args.get("condition"),
            humidity=request.args.get("humidity"),
            wind_speed=request.args.get("windSpeed"),
        )
        return jsonify(result)
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(port=port)
