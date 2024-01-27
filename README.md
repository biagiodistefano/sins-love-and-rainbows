# Sins, Love, and Rainbows: A Django Party Manager 🎉🌈

Unleash the ultimate party planning experience with this Django-based application, tailored for orchestrating unforgettable personal gatherings.

**Disclaimer:** This project is a labor of love, crafted in a personal capacity. It's unshackled from the chains of professional maintenance or adherence to conventional best practices.

## Core Features 🚀

- **Party Creation & Customization:** Forge your own party universe, toggling between public and private realms, and setting attendee limits.
- **Dynamic People Management:** Effortlessly populate your guest list with Twilio: send contact cards to your Twilio number and let it handle the heavy lifting, automatically adding contacts and firing off invites.
- **One-Click WhatsApp Invites:** Seamlessly connect with guests using WhatsApp. A simple click in the admin panel sends out personalized invites.
- **RSVPs & Anonymity Preferences:** Guests can confirm attendance and choose whether to display their names on the attendee list.
- **Collaborative Task Lists:** Foster a community spirit with shared task lists. Attendees can claim tasks, mindful of everyone's allergies and dietary restrictions.
- **Resourceful Party Links:** Provide handy links to essential party resources.
- **URL Shortening Tool:** Effortlessly create and share concise, memorable links.

### Enliven Your Parties with Automatic Messaging 📱

Utilize Twilio to send automatic, personalized messages to your guests.

As soon as a new Party is created, four messages are queued up:

- **Invitation:** Scheduled to be sent 1 month before the party, containing the link to the party page to RSVP.
- **2-Week Reminder:** Scheduled to be sent 2 weeks before the party, containing the link to the party page to RSVP.
- **1-Week Reminder:** Scheduled to be sent 1 week before the party, containing the link to the party page to RSVP.
- **2-Day Reminder:** Scheduled to be sent 2 days before the party, containing the link to the party page to RSVP.

There are two ways to set this in motion:

#### Via Command Line:
```bash
python manage.py send-messages
```

#### Through Celery Tasks:
Configure `api.tasks.send_due_messages` in the admin panel with crontab syntax.

**Note:** A Twilio account and WhatsApp business number are prerequisites.

## Quick Start Guide 🚀

1. **Clone the Repository:**
   ```bash
   git clone git@github.com:biagiodistefano/sins-love-and-rainbows.git
   ```
2. **Set Up the Environment:**
   ```bash
   python3.11 -m pip install poetry
   python3.11 -m poetry install
   source .venv/bin/activate
   ```
3. **Configure Settings:**

   **A couple of notes**:
   - *Note on the database: This project uses SQLite by default, as it is meant to be small. If you'd like to use PostgreSQL, tweak `settings/database.py` accordingly.*
   - *Note on `DEBUG`: This project uses an ugly hack, where DEBUG is True if the git branch is != `production`. You might rightfully be disgusted by this, but it's a personal project, so I'm not too bothered by it. Feel free to change it to your liking in `settings/base.py`.*


   Populate a `.env` file at the root with necessary:
   
   ```bash
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

4. **Bootstrap & Launch:**
   ```bash
   cd src
   python manage.py bootstrap
   python manage.py runserver
   ```

**Static Files:** Managed effortlessly via whitenoise, no need for `collectstatic`.

## Celery Integration 🌱

- Ensure Redis is operational.
- From the `src` directory, activate Celery components:

  **Worker:**
  ```bash
  celery -A sinsloveandrainbows worker --loglevel=INFO
  ```

  **Beat Scheduler:**
  ```bash
  celery -A sinsloveandrainbows beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
  ```

**Deployment Tip:** Consider Docker or systemd for a robust deployment.

---

Embrace this Django marvel and transform your party planning from mundane to magical! 🌟
