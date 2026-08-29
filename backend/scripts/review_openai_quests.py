"""Extract and deterministically screen quest candidates from Batch API results."""

import argparse
import json
import re
from pathlib import Path


UNSAFE = re.compile(r"\b(climb|roof|rewire|electrical panel|bare wire|bypass|disable|standing water)\b", re.I)


def response_text(body):
    if body.get("output_text"):
        return body["output_text"]
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text")
    return None


def main(args):
    accepted = []
    rejected = []
    seen = set()
    with open(args.input, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            body = ((row.get("response") or {}).get("body") or {})
            text = response_text(body)
            if not text:
                rejected.append({"source": row.get("custom_id"), "reason": "missing output"})
                continue
            try:
                quests = json.loads(text)["quests"]
            except (json.JSONDecodeError, KeyError, TypeError):
                rejected.append({"source": row.get("custom_id"), "reason": "invalid structured output"})
                continue
            for quest in quests:
                title_key = quest.get("title", "").strip().lower()
                combined = title_key + " " + quest.get("description", "")
                reason = None
                if title_key in seen:
                    reason = "duplicate title"
                elif UNSAFE.search(combined):
                    reason = "unsafe term"
                elif not 2 <= int(quest.get("duration_minutes", 0)) <= 120:
                    reason = "invalid duration"
                if reason:
                    rejected.append({"source": row.get("custom_id"), "title": quest.get("title"), "reason": reason})
                else:
                    seen.add(title_key)
                    accepted.append({**quest, "batch_source": row.get("custom_id"), "review_status": "needs_human_review"})
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"accepted": accepted, "rejected": rejected}, indent=2), encoding="utf-8")
    print(f"Screened {len(accepted)} candidates for human review; rejected {len(rejected)}. Output: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="artifacts/openai/weather-quest-results.jsonl")
    parser.add_argument("--output", default="artifacts/openai/reviewed-quest-candidates.json")
    main(parser.parse_args())
