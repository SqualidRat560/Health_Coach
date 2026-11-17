# Health Coach: early-warning health monitoring agent

This is a team hackathon project (Sun Life challenge). It watches daily health signals for gradual decline and escalates a risk tier as a pattern emerges. A Claude-powered agent then explains *why* in plain language, with Canada-specific guidance such as province-level 811 nurse-line advice and seasonal vitamin-D risk.

**My part:** the Flask web server and the JSON API that drives the dashboard.

## How it works

1. **Signals:** daily health inputs are compared against each person's own baseline (today's value vs. baseline, trend, consecutive days of decline).
2. **Scoring:** declining signals are rolled up into a risk tier and a severity score. Some signals are flagged as urgent on their own.
3. **Context:** province and month add Canadian context, such as whether to call 811 and vitamin-D risk in winter months.
4. **Agent:** Claude turns the scored payload into an explanation and next steps for the person.

The demo walks through a 7-day sequence in which one simulated patient's pattern slowly emerges and the risk tier escalates day by day.

## API

| Endpoint | Returns |
|---|---|
| `GET /` | Dashboard UI |
| `GET /api/patients` | Demo patient profiles (declining, extended 8-signal, low-risk, healthy baseline) |
| `GET /api/provinces` | Canadian province codes |
| `GET /api/score?patient=&province=&month=&day=` | Scored payload: risk tier, severity, per-signal trends, Canadian context |
| `GET /api/sequence?patient=` | 7-day escalation sequence for the demo animation |
| `GET /api/agent?patient=&province=` | Claude's explanation of the result |

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env    # then add your ANTHROPIC_API_KEY
python app.py           # web dashboard
python main.py          # terminal demo
```

## Stack

Python · Flask · NumPy · Claude API
