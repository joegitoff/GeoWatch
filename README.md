# 🛡️ GeoShield — Location-Based Environmental Risk Alert System

A Streamlit dashboard that shows weather, forecast, rainfall, wind and air-quality data for a chosen
city and applies **transparent, rule-based alerts** with plain-language precautions.

> **Honest status:** The automated tests (39) pass and the app starts correctly in Demo mode and in
> offline-error mode. The live API calls could **not** be executed in the environment where this
> code was written (no access to open-meteo.com). Endpoints, parameters and response fields were
> checked against Open-Meteo's published documentation (accessed 20 Oct 2026). **Run the app once
> with internet access and confirm that live data loads before your demo.**

## What it is (and is not)
- ✅ Weather + air-quality display, interactive charts, configurable threshold alerts, explanations.
- ✅ Works with **no API key**. LLM explanations are optional; a Python fallback always works.
- ❌ It is **not** an official warning system. It does **not** predict street-level flooding.
- ❌ AQI shown is the **US AQI scale computed by a CAMS model** via Open-Meteo — not CPCB's NAQI and
  not a ground-station reading.

## Project structure
```
GeoShield/
├── app.py               Streamlit user interface
├── config.py            Thresholds, URLs, level definitions, constants
├── data_service.py      API calls (geocoding, weather, air quality) + parsing + error classes
├── alert_engine.py      Rule-based alert logic
├── recommendations.py   Precaution text per alert type/level
├── llm_service.py       Optional LLM explanation + Python fallback
├── charts.py            Plotly charts
├── sample_data.py       INVENTED offline demo/test data (always labelled SAMPLE)
├── requirements.txt  .env.example  .gitignore  pytest.ini
├── tests/               39 pytest tests
└── docs/                REPORT.md, PRESENTATION.md
```
Extra files vs. the suggested structure: `config.py` (one place for editable thresholds),
`charts.py` (keeps `app.py` short), `sample_data.py` (safe offline demo, clearly labelled).

## Install & run

### Windows (PowerShell or Command Prompt) — run inside the `GeoShield` folder
```
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.

### Ubuntu / Linux — run inside the `GeoShield` folder
```
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```
Streamlit prints a **Local URL** (normally `http://localhost:8501`). Open it in your browser.

### Opening in an IDE
- **VS Code:** *File → Open Folder → GeoShield*. Press `Ctrl+Shift+P` → *Python: Select Interpreter* →
  choose `.venv`. Use the built-in terminal (`Ctrl+``) for the commands above.
- **PyCharm:** *Open* the folder → *Settings → Project → Python Interpreter → Add Interpreter →
  Existing* → choose `.venv/bin/python` (Windows: `.venv\Scripts\python.exe`).

## Optional LLM setup (Anthropic Claude API)
1. Create a key in the Anthropic Console (https://console.anthropic.com).
2. Copy `.env.example` to `.env` and paste the key after `ANTHROPIC_API_KEY=`.
   (Windows: `copy .env.example .env` · Linux: `cp .env.example .env`)
3. `.gitignore` already excludes `.env`. **Never** put a key in source code or screenshots.
4. In the app sidebar tick **Use LLM explanation**, then press **Generate LLM explanation**.
The model name defaults to `claude-haiku-5-5`; change it via `GEOSHIELD_LLM_MODEL` in `.env` if
Anthropic's model list (https://docs.claude.com/en/docs/about-claude/models) shows a different name.
If the key is missing, the network fails, a rate limit is hit, the answer is empty, or the answer
contains numbers not found in our data, the app silently uses the Python fallback and says so.

## Run the tests
```
pytest -q
```
Tests use **sample/mocked data** to verify logic. They are *not* validation against real observations.

## Reliable demonstrations
Switch on **Demo mode** in the sidebar. A red banner *“SAMPLE DATA – invented numbers”* is shown on
every run, and alert sources are tagged `[SAMPLE DATA]`. Say clearly to the audience that Demo mode
is offline sample data; show live mode first, and use Demo mode only if the network fails.

## Troubleshooting
| Problem | Fix |
|---|---|
| `streamlit: command not found` | Activate the virtual environment, then `pip install -r requirements.txt`. |
| `ModuleNotFoundError: No module named 'x'` | Same as above; check the interpreter selected in your IDE. |
| “Could not connect…” | Check internet/proxy/firewall. Use Demo mode meanwhile. |
| “Too many requests…” (HTTP 429) | Open-Meteo free limits: 600/min, 5,000/hour, 10,000/day, 300,000/month. Wait and retry; results are cached for 10 minutes. |
| “No place found for …” | Check spelling, try a larger nearby city, or add the state/country (e.g. `Kumbakonam`). |
| Some values show `n/a` or blank | The API returned null for that variable; the app skips it safely. |
| Air-quality section unavailable | Air-quality service failed; weather still works. Retry later. |
| Port 8501 busy | `streamlit run app.py --server.port 8502` |

## Data sources, licences, attribution
- Weather: Open-Meteo.com — data licensed CC BY 4.0; free API is for **non-commercial** use.
- Air quality: Open-Meteo Air Quality API, based on CAMS (Copernicus Atmosphere Monitoring Service) data.
  Open-Meteo requires attribution to the CAMS data provider and Open-Meteo (shown in the app footer tab).
- Geocoding: Open-Meteo Geocoding API, based on GeoNames.
- For real decisions use **IMD** (mausam.imd.gov.in), **CPCB** (cpcb.nic.in) and your state disaster
  management authority.
