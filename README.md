# Sins, Love and Rainbows Django app

## Celery

Start the worker:

```bash
celery -A sinsloveandrainbows worker --loglevel=INFO
```

Start the beat:

```bash
celery -A sinsloveandrainbows beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
