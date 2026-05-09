from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS += ["debug_toolbar"]

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

INTERNAL_IPS = ["127.0.0.1"]

# SQLite pour dev rapide (override explicite, sauf si USE_MYSQL_DEV=true)
USE_MYSQL_DEV = env.bool("USE_MYSQL_DEV", default=False)
if not USE_MYSQL_DEV:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

# Email dans la console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logs verbeux
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "DEBUG"},
    "loggers": {
        "django.db.backends": {"level": "INFO"},  # trop verbeux sinon
    },
}
