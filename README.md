<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" />
    <img height="130" src="docs/images/banner.png"/>
  </picture>
 <br />
</h1>
<p align="center">
minis are the first open-source digital humans 👩🏽‍🤝‍👩🏼🧍
</p>
<p align="center">
  <a href="https://discord.com/invite/k2taFvaJGr"><img src="https://img.shields.io/discord/1217283257469501450?logo=discord&label=discord"/></a>
  <a href="https://github.com/AIDropout/Mini"><img src="https://img.shields.io/github/stars/AIDropout/Mini" /></a>
  <a href="https://github.com/AIDropout/Mini/blob/main/LICENSE"><img src="https://img.shields.io/github/license/AIDropout/Mini"/></a>
</p>

Help us build characters that are highly convincing, powerful, and dynamic — from a boyfriend that remembers everything about you to a personal secretary that can manage your calendar and email.

Use our lego blocks to create and deploy your own talk & text agent. That means your own `Twilio SMS`  mini powered by `Llama 3` with `Web Browsing` & `Proactive Messaging` in minutes, not weeks ⚡

#### mini demos:

- [Boyfriend](https://boyfriend.so)
- [David Goggins](https://textmini.com/goggins)

## 🌆 Features

- [x] All LLMs supported (LiteLLM)
- [x] Scalable agent DB architecture (Supabase)
- [x] Omnichannel messaging (Bird SMS, Telegram)
- [x] Task scheduling (Celery & Redis)
- [x] Local, memory, cloud storage (AWS S3)

### Modules

- [x] Proactive messages
- [x] Quality check filter to re-generate a message to meet standard
- [x] Schedule tasks
- [x] Human-like memory
- [x] Processes images using vision
- [x] Use TTS to send audio recordings
- [x] System prompt building (for dynamic personality and mood)
- [x] Read multiple rapid messages before responding
- [x] Human-like responsiveness (& unresponsiveness... 😜)
- [ ] Send images
- [ ] User preference tracking
- [ ] Phone calls
- [ ] Web browsing

### Intents (with confidence thresholds)

- [x] Whether to fix its own prompt and re-generate a message
- [x] Whether to not respond to a message (e.g. "ok" or "bye")
- [x] Whether to schedule a reminder in the future

## 🛠️ Environment Setup

Ensure that [ngrok](https://ngrok.com/), and [uv](https://github.com/astral-sh/uv) are installed.

Grab your ngrok auth token here (https://dashboard.ngrok.com/get-started/your-authtoken)

```bash
# 1 Navigate to the repository.
pip install uv

# 2. Create a virtual environment at .venv
uv venv

# 3. Activate environment.
source .venv/bin/activate # macOS and Linux
.venv\Scripts\activate # Windows

# 4. Install dependencies
uv pip install -r requirements.txt

```

Copy `config.yaml.example` to a new file called `config.yaml` in the same directory and configure keys.

## 🚀 Usage

Run the project:

```bash
   # 1. Run the FastAPI server
    python main.py
```

## Testing Stripe webhook

https://dashboard.stripe.com/test/webhooks

```bash
stripe login # Download the CLI and log in with your Stripe account
stripe listen --forward-to http://127.0.0.1:8000/payment/webhook # Forward events to your webhook
stripe trigger checkout.session.completed # Manually trigger events with the CLI for testing
stripe trigger customer.subscription.deleted
```
celery -A mini.server.celery.celery worker -n worker1@%h --concurrency=2 & gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --timeout 120 -w 1
ps aux | grep -E 'celery|gunicorn|python' | awk '{sum+=$6} END {print sum/1024 " MB"}'
ps aux | grep -E 'celery|gunicorn|python' | grep -v grep | awk '{printf "%.2f MB - %s\n", $6/1024, $11}'

pkill -f gunicorn
pkill -f celery

ps aux | grep -E 'celery|gunicorn|python' | grep -v grep


Interact with the demo:

- Add +1 (833) 819-1677 to contacts, or
- Add @AIHealthCoachBot on Telegram

SSH

ssh -i "minikeypair.pem" ubuntu@ec2-44-194-155-71.compute-1.amazonaws.com
cd mini
source .venv/bin/activate


## Dependencies

Add new dependencies:

```bash
uv pip install [package_name]
uv pip freeze > requirements.txt
```

## Contributors

[![Contributors](https://contrib.rocks/image?repo=AIDropout/Mini)](https://github.com/AIDropout/Mini/graphs/contributors)
