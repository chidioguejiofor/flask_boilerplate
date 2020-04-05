CELERY_TASKS = ['api.services.emails']

APP_EMAIL = 'info@<your-app>.com'

#  redis constants
VERIFY_EMAIL_HASH = 'VERIFY_EMAIL'
AUTH_HASH = 'AUTH_REDIS_HASH'
RESET_HASH = 'RESET_HASH'
LOGIN = 'You have successfully logged into the application'
AUTH_LOGIN_TIME_DELTA = {'days': 3}
VERIFY_EMAIL_TIME_DELTA = RESET_PASSWORD_DELTA = {'minutes': 15}
COOKIE_AUTH_KEY = 'auth_id'
