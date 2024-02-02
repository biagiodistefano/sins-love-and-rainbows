LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "django_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "django_error.log",  # File for logging Django errors
        },
        "twilio_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "twilio_messages.log",  # File for logging Twilio messages
            "formatter": "verbose",
        },
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
        },
        "twilio_console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["django_file", "console"],
            "level": "ERROR",
            "propagate": True,
        },
        "twilio_whatsapp": {
            "handlers": ["twilio_file", "twilio_console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
