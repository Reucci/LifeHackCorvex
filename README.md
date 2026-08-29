# LifeHackCorvex
LifeHack Hackhaton Repo

## Photo-proof challenges

Picking a quest on the Home screen now opens a **camera / proof** step
(`frontend/src/pages/Verify.jsx`). The user snaps a photo of themselves doing the
action, it is sent to `POST /actions/verify`, and a Claude vision check
(`backend/verification_service.py`) decides whether the photo matches the
challenge. Only a passing photo completes the quest and awards gold.

- Set `ANTHROPIC_API_KEY` in the backend environment to enable the real check.
- With no key configured the verifier falls back to accepting the photo, so the
  demo still works offline. Guest mode always uses the local fallback.
