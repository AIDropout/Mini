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

celery -A mini.server.celery.celery flower
export PYTHONPATH=$PYTHONPATH:/Users/chris/Desktop/mini


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
