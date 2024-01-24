# Sins, Love and Rainbows Django app

Simple Django application to manage personal parties.

This is a personal project, it is not maintained professionally and does not follow any best practice.

## What this does.

It allows you to create parties and invite people to them.

From the admin panel, create the people and the parties, then invite them to the parties.

Add the people's numbers to their profile, you will see a link in the people's list that you can simply click to send them a message on whatsapp, with their personal link to the party.

People do not need to login manually: the link contains a token that logs them in automatically (except if they are admins, in which case they have to login manually).
Is this secure? No. But it's a party, so who cares, no one wants to create an account and login to come to your party.

### Features

- Create parties, decide whether they are public or private and how many people can attend.
- Create people
  * bonus: if you have twilio enabled, instead of having to add people manually to your database like a peasant, you can simply share their contact to your twilio whatsapp number and it will create the people for you. In this case, if there's an upcoming party, it will also send them an invitation message.
- Invite people to parties:
  * bonus: As soon as you create the invite, an invitation message is sent to the person via whatsapp (if you have twilio enabled).
- Send messages to people via whatsapp (even automatically, see below) via a click of a button from the admin panel.
- People can RSVP to parties and decide whether they want their name to be shown in the list of attendees
- Every party has a shared task list that people can add tasks/items to and claim them. It also takes into account allergies and intolerances of the attendees.
- Every party has a section with links to useful stuff.
- There's a built-in link shortener that allows you to create short links to external websites.


#### Automatic messages

It also allows you to send messages to the people you invited automatically, using twilio. You can do this in two ways:

##### via the admin
```
python manage.py send-messages
```

##### using the celery task

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
python manage.py bootstrap
python manage.py runserver
```

Note: static files are served via whitenoise, so you don't need to run `collectstatic`.

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

Note: you want to deploy this properly either using docker or using systemd.