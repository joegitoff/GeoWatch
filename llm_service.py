"""
llm_service.py - OPTIONAL plain-language explanations.

How it works (beginner view)
----------------------------
1. Python (alert_engine.py) has ALREADY decided which alerts exist.
2. We pack the real data + alerts into a small JSON "payload".
3. We send the payload to an LLM (Anthropic Claude API) with strict instructions:
   "only use numbers from the payload; do not invent anything".
4. We check the answer. If the API fails, there is no key, the answer is empty,
   or it contains numbers that were not in the payload -> we use
   fallback_explanation(), which is ordinary Python and always works.

The LLM never makes alert decisions and never computes numbers.

Python concepts: environment variables, try/except with several exception types,
JSON, regular expressions, dependency injection (client parameter), fallbacks.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

try:                       # python-dotenv is optional; it loads the .env file if present
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:        # pragma: no cover
    pass

# Model name can be changed in .env without editing code. Check Anthropic's docs for current names:
# https://docs.claude.com/en/docs/about-claude/models
DEFAULT_MODEL = "claude-haiku-5-5"

SYSTEM_PROMPT = (
    "You explain environmental alerts to ordinary people in simple English (max 150 words). "
    "Use ONLY the data in the JSON the user provides. Never invent weather values, AQI values, "
    "official warnings or flood predictions. Do not say anything will flood. If no alerts are "
    "present, say conditions are within the configured thresholds. Mention that alerts are "
    "app-generated and not official warnings. Do not add numbers that are not in the JSON."
)


@dataclass
class Explanation:
    text: str
    source: str                 # "LLM" or "Python fallback"
    note: str = ""              # why the fallback was used, if it was


# ---------------------------------------------------------------- payload ----
def build_payload(location_label: str, weather, air, alerts) -> dict:
    """Collect only real data we already have. Missing values stay None."""
    def num(v):
        try:
            f = float(v)
            return None if f != f else round(f, 1)
        except (TypeError, ValueError):
            return None

    cur = weather.current if weather is not None else {}
    aq = air.current if air is not None else {}
    return {
        "location": location_label,
        "data_is_sample_demo": bool(getattr(weather, "is_sample", False)),
        "current_weather": {
            "temperature_c": num(cur.get("temperature_2m")),
            "humidity_percent": num(cur.get("relative_humidity_2m")),
            "wind_speed_kmh": num(cur.get("wind_speed_10m")),
            "condition": cur.get("weather_text"),
        },
        "current_air_quality": {"us_aqi": num(aq.get("us_aqi")), "pm2_5": num(aq.get("pm2_5"))},
        "alerts": [
            {"variable": a.variable, "value": a.value, "unit": a.unit, "rule": a.rule,
             "when": a.when, "level": a.level.label, "advice": a.advice}
            for a in alerts
        ],
    }


# --------------------------------------------------------------- fallback ----
def fallback_explanation(location_label: str, alerts, is_sample: bool = False) -> str:
    """Plain Python explanation - used when the LLM is off or failing."""
    prefix = "[SAMPLE DATA] " if is_sample else ""
    if not alerts:
        return (f"{prefix}For {location_label}, no configured rule was triggered in the forecast, "
                "so conditions are within the thresholds set in this app. These alerts are "
                "app-generated, not official warnings.")
    lines = [f"{prefix}For {location_label}, {len(alerts)} rule(s) were triggered. "
             "These are app-generated alerts, not official warnings:"]
    for a in alerts[:6]:
        lines.append(f"- {a.when}: {a.variable} = {a.value:g} {a.unit} ({a.level.label}).")
    if len(alerts) > 6:
        lines.append(f"- ...and {len(alerts) - 6} more.")
    lines.append("See the precautions section for practical steps, and follow official advisories.")
    return "\n".join(lines)


# ------------------------------------------------------------ validation -----
_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def numbers_are_grounded(text: str, payload: dict) -> bool:
    """Reject answers that mention numbers (>10) which are not present in the payload."""
    allowed = set()
    for token in _NUMBER.findall(json.dumps(payload)):
        allowed.add(float(token))
    for token in _NUMBER.findall(text):
        value = float(token)
        if value > 10 and value not in allowed:
            return False
    return True


# ----------------------------------------------------------------- LLM call --
def explain(location_label: str, weather, air, alerts, use_llm: bool = True,
            client=None) -> Explanation:
    """Return an Explanation. Never raises: any problem -> Python fallback."""
    is_sample = bool(getattr(weather, "is_sample", False))
    fallback = fallback_explanation(location_label, alerts, is_sample)
    if not use_llm:
        return Explanation(fallback, "Python fallback", "LLM explanations are switched off.")

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if client is None and not api_key:
        return Explanation(fallback, "Python fallback", "No ANTHROPIC_API_KEY found (this is fine).")

    payload = build_payload(location_label, weather, air, alerts)
    try:
        if client is None:
            import anthropic                      # imported lazily: core app works without it
            client = anthropic.Anthropic(api_key=api_key, timeout=20.0)
        message = client.messages.create(
            model=os.getenv("GEOSHIELD_LLM_MODEL", DEFAULT_MODEL),
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
        text = "".join(block.text for block in message.content
                       if getattr(block, "type", "") == "text").strip()
    except ImportError:
        return Explanation(fallback, "Python fallback", "The 'anthropic' package is not installed.")
    except Exception as exc:                      # network, auth, rate limit, bad response...
        return Explanation(fallback, "Python fallback", f"LLM unavailable ({_describe(exc)}).")

    if not text:
        return Explanation(fallback, "Python fallback", "LLM returned an empty answer.")
    if not numbers_are_grounded(text, payload):
        return Explanation(fallback, "Python fallback",
                           "LLM answer contained numbers not present in the data, so it was discarded.")
    return Explanation(text, "LLM")


def _describe(exc: Exception) -> str:
    """Short, key-safe description of an exception (never prints secrets)."""
    name = type(exc).__name__
    status = getattr(exc, "status_code", None)
    return f"{name}, HTTP {status}" if status else name
