# Check a user-submitted "proof" photo against the eco challenge they picked.
#
# Uses Claude vision when an Anthropic key is configured (ANTHROPIC_API_KEY or
# ANTHROPIC_AUTH_TOKEN). When it is not — or the call fails — we fall back to
# accepting the photo so the prototype keeps working offline.

import base64
import binascii
import json
import os
import re

MODEL = "claude-opus-5"  # swap to "claude-haiku-4-5" if you want a faster/cheaper check

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024

SYSTEM_PROMPT = (
    "You verify photo proof for Ecolings, an app where people complete small "
    "energy-saving actions at home. You are given the challenge a user accepted "
    "and one photo they submitted as proof.\n\n"
    "Decide whether the photo is a plausible, genuine first-hand attempt at THAT "
    "specific challenge. Be encouraging and lenient about lighting, blur, framing "
    "and camera quality. Reject only when the photo clearly does not relate to the "
    "challenge, shows nothing relevant, or is obviously not a real photo taken by "
    "the user (a screenshot, meme, stock image, or a picture of a screen).\n\n"
    "Reply with ONLY a JSON object, no other text:\n"
    '{"verified": true|false, "confidence": "high"|"medium"|"low", '
    '"reason": "<one short sentence addressed to the user>"}'
)


def decode_data_url(data_url):
    """Turn a `data:image/...;base64,xxxx` string into (bytes, media_type)."""
    if not isinstance(data_url, str) or not data_url.startswith("data:"):
        raise ValueError("A photo is required")
    try:
        header, encoded = data_url.split(",", 1)
    except ValueError:
        raise ValueError("The photo could not be read")
    media_type = header[len("data:"):].split(";")[0].strip() or "image/jpeg"
    if media_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Please use a JPEG or PNG photo")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("The photo could not be read")
    if not raw:
        raise ValueError("The photo is empty")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("The photo is too large (max 5 MB)")
    return raw, media_type


def _has_credentials():
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def _accept(reason):
    return {"verified": True, "confidence": "low", "reason": reason, "checked_by": "fallback"}


def _parse(text):
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) and "verified" in data else None


async def verify_photo(image_bytes, media_type, quest_title, quest_description):
    """Return {verified, confidence, reason, checked_by}."""
    if not _has_credentials():
        return _accept("Photo received — automatic checking is off, so you're trusted on this one!")

    try:
        import anthropic
    except ImportError:
        return _accept("Photo received — the verifier isn't installed, so you're trusted on this one!")

    encoded = base64.standard_b64encode(image_bytes).decode("utf-8")
    prompt = (
        f"Challenge: {quest_title}\n"
        f"What it involves: {quest_description}\n\n"
        "Here is the user's proof photo. Does it show a genuine attempt at this challenge?"
    )

    try:
        client = anthropic.AsyncAnthropic()
        response = await client.messages.create(
            model=MODEL,
            max_tokens=2000,
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": encoded},
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
    except anthropic.AnthropicError:
        return _accept("Photo received — the verifier was unavailable, so you're trusted on this one!")
    except Exception:  # noqa: BLE001 - a proof check must never break the app
        return _accept("Photo received — the verifier hit a snag, so you're trusted on this one!")

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    parsed = _parse(text)
    if parsed is None:
        return _accept("Photo received — the verifier gave an unclear answer, so you're trusted on this one!")

    verified = bool(parsed.get("verified"))
    default_reason = (
        "Nice work — that looks like a real effort!"
        if verified
        else "That photo doesn't seem to match this challenge — try another shot."
    )
    return {
        "verified": verified,
        "confidence": parsed.get("confidence", "medium"),
        "reason": (parsed.get("reason") or default_reason).strip(),
        "checked_by": "ai",
    }
