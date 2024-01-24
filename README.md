# Sins, Love and Rainbows Django app

Simple Django application to manage personal parties.

This is a personal project, it is not maintained professionally and does not follow any best practice.

## What this does.

It allows you to create parties and invite people to them.

From the admin panel, create the people and the parties, then invite them to the parties.

Add the people's numbers to their profile, you will see a link in the people's list that you can simply click to send them a message on whatsapp, with their personal link to the party.

People do not need to login manually: the link contains a token that logs them in automatically.
Is this secure? No. But it's a party, so who cares, no one wants to create an account and login to come to your party.

It also allows you to send messages to the people you invited automatically, using twilio. You can do this in two ways:

### via the admin
```
python manage.py send-messages
```

### using the celery task

Go to your admin panel, go to periodic tasks, select `api.tasks.send_due_messages`.
You can set the schedule there using the crontab syntax.

You have to have a twilio account and a whatsapp business number to use this.

In order to send messages, you have to get your template approved by whatsapp. They are in `src/api/templates/api`.

## Settings

Have a `.env` file in the root of the project with the following variables:

```dotenv
SECRET_KEY=<your-secret-key>
ALLOWED_HOSTS=<your-allowed-hosts-separated-by-comma>

EMAIL_HOST=<your-email-host>
EMAIL_PORT=<your-email-port>
EMAIL_HOST_USER=<your-email-host-user>
EMAIL_HOST_PASSWORD=<your-email-host-password>
DEFAULT_FROM_EMAIL=<your-default-from-email>

# Twilio
TWILIO_ACCOUNT_SID=<your-twilio-account-sid>
TWILIO_AUTH_TOKEN=<your-twilio-auth-token>

# TWILIO_FROM_WHATSAPP_NUMBER=+19703721365
TWILIO_FROM_WHATSAPP_NUMBER=<your-twilio-whatsapp-number>
DEBUG_NUMBERS_ALLOWED=<numbers that will receive messages even when DEBUG=True, separated by a comma>
MY_PHONE_NUMBER=<your-phone-number>

ADMIN_URL=admin/

DEFAULT_SUPERUSER_USERNAME=admin
DEFAULT_SUPERUSER_PASSWORD=admin
```

Clone the thing.

```bash
git clone git@github.com:biagiodistefano/sins-love-and-rainbows.git
python3.11 -m pip install poetry
python3.11 -m poetry install
source .venv/bin/activate
cd src
python manage.py migrate
python manage.py bootstrap
python manage.py runserver
```

## Celery
Have redis running, then, from the `src` directory:

Start the worker:

```bash
celery -A sinsloveandrainbows worker --loglevel=INFO
```

Start the beat:

```bash
celery -A sinsloveandrainbows beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
