from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

AUTHENTICATION_BACKENDS = [
    'account.authentication.ApiBackend',
    'django.contrib.auth.backends.ModelBackend',
    ]

with open(os.path.join(BASE_DIR, 'secret_key.txt')) as f:
    SECRET_KEY = f.read().strip()

DEBUG = True

swappable = 'AUTH_USER_MODEL'

AUTH_USER_MODEL = 'account.User'

ADMIN_URL = 'puma_gs/admin/'

ALLOWED_HOSTS = ['*']

CSRF_COOKIE_SECURE = False

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    'django_crontab',
    "account",
    "report",
    "bootstrap5",
    "fontawesomefree",
    "django_filters",
    "mathfilters",
    "widget_tweaks",
    "django_extensions",
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

ROOT_URLCONF = "report_gs.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'account', 'templates', 'fragment'), os.path.join(BASE_DIR, 'account', 'templates', 'site'), 
                 os.path.join(BASE_DIR, 'account', 'templates', 'line'), os.path.join(BASE_DIR, 'account', 'templates', 'shift'),
                 os.path.join(BASE_DIR, 'account', 'templates', 'user'), os.path.join(BASE_DIR, 'account', 'templates', 'emplacement'),
                 os.path.join(BASE_DIR, 'account', 'templates', 'warehouse'), os.path.join(BASE_DIR, 'report', 'templates', 'family'),
                 os.path.join(BASE_DIR, 'report', 'templates', 'product'), os.path.join(BASE_DIR, 'report', 'templates', 'packing'),
                 os.path.join(BASE_DIR, 'report', 'templates', 'move'), os.path.join(BASE_DIR, 'report', 'templates', 'fragment'), 
                 os.path.join(BASE_DIR, 'report', 'templates', 'dispo'), 
                 os.path.join(BASE_DIR, 'report', 'templates', 'move', 'mp'), os.path.join(BASE_DIR, 'report', 'templates', 'move', 'pf'), 
                ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "report_gs.wsgi.application"
CORS_ALLOW_ALL_ORIGINS = True



CRONJOBS = [
    # ('0 * * * *', 'report.cron.check_temp_emplacements'),
    ('0 * * * *', 'report.cron.check_transfer_mirror'),
    ('0 8 * * *', 'report.cron.send_stock'),
    ('0 6 * * *', 'report.cron.send_site_inventory_reports'),
    ('30 9 * * *', 'report.cron.check_min_max'),
    ('30 12 * * 0', 'report.cron.send_expiring_lot_alerts')
]



CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'x-csrf-token',
    'x-requested-with',
    'accept',
]


DATABASES = {
    # 'default': {
    #   'ENGINE': 'django.db.backends.postgresql',
    #   'NAME': 'PumaGS',
    #   'USER': 'puma_gs',
    #   'PASSWORD': 'puma_gs',
    #   'HOST': '10.10.10.53',
    #   'PORT': '5176',
    # },
    # 'default': {
    #   'ENGINE': 'django.db.backends.postgresql',
    #   'NAME': 'PumaGS',
    #   'USER': 'puma_gs',
    #   'PASSWORD': 'puma_gs',
    #   'HOST': '10.10.10.20',
    #   'PORT': '5176',
    # },
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'PumaGS',
    #     'USER': 'puma_gs',
    #     'PASSWORD': 'puma_gs',
    #     'HOST': '127.0.0.1',
    #     'PORT': '5432',
    # },
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "fr"

TIME_ZONE = "Africa/Algiers"

USE_I18N = True

USE_TZ = True

LOGIN_REDIRECT_URL = 'login_success'
LOGOUT_REDIRECT_URL = '/login'

STATIC_URL = "static/"

STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_REDIRECT_URL = 'login_success'
LOGOUT_REDIRECT_URL = '/login'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'm13o13bmw@gmail.com'
EMAIL_HOST_PASSWORD = 'utovgkbuqnjrphja'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'm13o13bmw@gmail.com'
