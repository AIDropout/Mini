<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" />
    <img height="130" src="docs/images/banner.png"/>
  </picture>
 <br />
</h1>
<p align="center">
Zootopians are the First Open-Source Digital Humans 👩🏽‍🤝‍👩🏼🧍
</p>
<p align="center">
  <a href="https://discord.gg/w7p3U9wn"><img src="https://img.shields.io/discord/1217283257469501450?logo=discord&label=discord"/></a>
  <a href="https://github.com/AIDropout/ZOOTOPIA"><img src="https://img.shields.io/github/stars/AIDropout/ZOOTOPIA" /></a>
  <a href="https://github.com/AIDropout/ZOOTOPIA/blob/main/LICENSE"><img src="https://img.shields.io/github/license/AIDropout/ZOOTOPIA"/></a>
</p>

Help us build characters that are highly convincing, customizable, and dynamic — from boyfriend to personal secretary.

Make your own `Twilio SMS` Zootopian powered by `Gemini LLM` with `Bing Search` & `Stripe Payment` in minutes, not weeks ⚡

#### Zootopia character demos:
- [Boyfriend](https://boyfriend.so)
- [David Goggins](https://textmini.com/goggins)

## 🌆 Features
- [x] All LLMs supported (LiteLLM)
- [x] Scalable agent DB architecture (Supabase)
- [x] Omnichannel messaging (Bird SMS, Telegram)
- [x] Task scheduling (Celery & Redis)
- [x] Local, memory, cloud storage (AWS S3)

### Behaviors
- [x] Proactive messages
- [x] Filtering messages
- [x] Reading multiple rapid messages before responding
- [x] Human-like responsiveness (& unresponsiveness... 😜)
- [x] Quality check filter to re-generate a message
- [x] Scheduled messages
- [x] Human-like memory
- [x] Receive images
- [x] Send a Stripe checkout link after x messages
- [ ] Send images
- [ ] User preference tracking
- [ ] Phone calls
- [ ] Web browsing


### Intents (with confidence thresholds)
[x] Whether to fix its own prompt and re-generate a message
[x] Whether to not respond to a message (e.g. "ok" or "bye")
[x] Whether to schedule a reminder in the future


## 🛠️ Environment Setup
Make sure Python, [ngrok](https://ngrok.com/), and [uv]() are installed.

   ```bash
   # 1 Navigate to the repository. Install [uv](https://github.com/astral-sh/uv):
   pip install uv 

   # 2. Create a virtual environment at .venv
   uv venv  

   # 3. Activate environment. 
   source .venv/bin/activate # macOS and Linux
   .venv\Scripts\activate # Windows

   # 4. Install dependencies  
   uv pip install -r requirements.txt

   ```

Copy `config.yaml.example` to a new file called `config.yaml` in the same directory
Configure keys

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

Interact with the demo:
- Add +1 (833) 819-1677 to contacts, or
- Add @AIHealthCoachBot on Telegram

## Dependencies
Add new dependencies:
```bash
uv pip install [package_name]
uv pip freeze > requirements.txt
```

## Contributors

[![Contributors](https://contrib.rocks/image?repo=AIDropout/ZOOTOPIA)](https://github.com/AIDropout/ZOOTOPIA/graphs/contributors)
