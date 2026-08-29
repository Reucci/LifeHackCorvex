"""Prepare, submit, inspect, and download a discounted OpenAI quest-generation batch."""

import argparse
import json
import os
from pathlib import Path

import httpx


API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1").rstrip("/")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
INPUT_RATE = float(os.getenv("OPENAI_INPUT_USD_PER_MTOK", "0.75"))
OUTPUT_RATE = float(os.getenv("OPENAI_OUTPUT_USD_PER_MTOK", "4.50"))

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "quests": {
            "type": "array", "minItems": 5, "maxItems": 5,
            "items": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "title": {"type": "string", "minLength": 8, "maxLength": 72},
                    "description": {"type": "string", "minLength": 20, "maxLength": 220},
                    "category": {"type": "string"},
                    "weather_trigger": {"type": "string"},
                    "duration_minutes": {"type": "integer", "minimum": 2, "maximum": 120},
                    "safety_note": {"type": "string", "maxLength": 180},
                },
                "required": ["title", "description", "category", "weather_trigger", "duration_minutes", "safety_note"],
            },
        },
    },
    "required": ["quests"],
}


def scenarios(count):
    conditions = ["Fair", "Partly Cloudy", "Cloudy", "Light Showers", "Moderate Rain", "Thundery Showers"]
    for index in range(count):
        yield {
            "temperature_c": 25 + index % 10,
            "humidity_pct": 62 + (index * 7) % 34,
            "wind_kmh": 2 + (index * 5) % 28,
            "rainfall_mm": [0, 0, 0, 0.2, 2.5, 8.0][index % 6],
            "condition": conditions[index % len(conditions)],
            "hour": (6 + index * 2) % 24,
            "radar_movement": ["none", "approaching", "moving_away"][index % 3],
        }


def prepare(args):
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for index, scenario in enumerate(scenarios(args.requests)):
            prompt = (
                "Generate five distinct, safe, practical, visibly verifiable household energy-saving quests for "
                "Singapore. Every quest must be directly justified by the supplied weather and completable within "
                "two hours. No electrical repairs, climbing, purchases, standing water, or opening windows in rain. "
                f"Weather scenario: {json.dumps(scenario, separators=(',', ':'))}"
            )
            request = {
                "custom_id": f"weather-{index:05d}", "method": "POST", "url": "/v1/responses",
                "body": {
                    "model": MODEL, "store": False, "max_output_tokens": 1200,
                    "input": prompt,
                    "text": {"format": {"type": "json_schema", "name": "quest_library", "strict": True, "schema": SCHEMA}},
                },
            }
            handle.write(json.dumps(request, separators=(",", ":")) + "\n")
    estimated = args.requests * (900 * INPUT_RATE + 900 * OUTPUT_RATE) / 1_000_000 * 0.5
    print(f"Prepared {args.requests} requests at {output}")
    print(f"Conservative estimated Batch cost: ${estimated:.2f}; actual token usage determines billing.")


def headers():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise SystemExit("Set OPENAI_API_KEY in the environment first.")
    return {"Authorization": f"Bearer {key}"}


def submit(args):
    if not args.confirm_spend:
        raise SystemExit("Submission spends API credit. Re-run with --confirm-spend after reviewing the JSONL file.")
    with httpx.Client(timeout=60) as client, open(args.input, "rb") as batch_file:
        uploaded = client.post(
            f"{API_URL}/files", headers=headers(), data={"purpose": "batch"},
            files={"file": (Path(args.input).name, batch_file, "application/jsonl")},
        )
        uploaded.raise_for_status()
        batch = client.post(
            f"{API_URL}/batches", headers={**headers(), "Content-Type": "application/json"},
            json={"input_file_id": uploaded.json()["id"], "endpoint": "/v1/responses", "completion_window": "24h"},
        )
        batch.raise_for_status()
    print(json.dumps(batch.json(), indent=2))


def status(args):
    response = httpx.get(f"{API_URL}/batches/{args.batch_id}", headers=headers(), timeout=30)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


def download(args):
    batch = httpx.get(f"{API_URL}/batches/{args.batch_id}", headers=headers(), timeout=30)
    batch.raise_for_status()
    file_id = batch.json().get("output_file_id")
    if not file_id:
        raise SystemExit(f"Batch has no output file yet (status: {batch.json().get('status')}).")
    content = httpx.get(f"{API_URL}/files/{file_id}/content", headers=headers(), timeout=60)
    content.raise_for_status()
    Path(args.output).write_bytes(content.content)
    print(f"Downloaded results to {args.output}")


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    prepare_cmd = commands.add_parser("prepare")
    prepare_cmd.add_argument("--requests", type=int, default=500)
    prepare_cmd.add_argument("--output", default="artifacts/openai/weather-quest-batch.jsonl")
    prepare_cmd.set_defaults(run=prepare)
    submit_cmd = commands.add_parser("submit")
    submit_cmd.add_argument("--input", default="artifacts/openai/weather-quest-batch.jsonl")
    submit_cmd.add_argument("--confirm-spend", action="store_true")
    submit_cmd.set_defaults(run=submit)
    status_cmd = commands.add_parser("status")
    status_cmd.add_argument("batch_id")
    status_cmd.set_defaults(run=status)
    download_cmd = commands.add_parser("download")
    download_cmd.add_argument("batch_id")
    download_cmd.add_argument("--output", default="artifacts/openai/weather-quest-results.jsonl")
    download_cmd.set_defaults(run=download)
    return root


if __name__ == "__main__":
    args = parser().parse_args()
    args.run(args)
