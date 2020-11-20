import os
import json
import dj_database_url

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'true').lower() == "true"
DEFAULT_CONNECTION = dj_database_url.parse(os.environ.get("DATABASE_URL"))
DEFAULT_CONNECTION.update({"CONN_MAX_AGE": 600})
DATABASES = {"default": DEFAULT_CONNECTION}
ALLOWED_HOSTS = json.loads(os.environ.get("ALLOWED_HOSTS", "[\"*\"]"))
CORS_ORIGIN_REGEX_WHITELIST = json.loads(os.environ.get("CORS_ORIGIN", "[]"))
FRONTEND_DOMAIN_NAME = os.environ.get("FRONTEND_DOMAIN_NAME")

# Must generate specific password for your app in [gmail settings][1]
EMAIL_HOST = 'smtp.sendgrid.net'  # 'smtp.gmail.com'
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_USE_TLS = True
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

# Celery settings.
CELERY_BROKER_URL = os.environ.get('CLOUDAMQP_URL')
CELERY_BROKER_POOL_LIMIT = int(os.environ.get('CELERY_BROKER_POOL_LIMIT'))
#CELERY_RESULT_BACKEND = os.environ.get("CLOUDAMQP_URL")

# Google Credentials.
# GOOGLE_AUTH = {
#    'client_id': os.getenv('GOOGLE_CLIENT_ID'),
#    'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
# }

# social-rest-knox settings.
#SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_CLIENT_ID'),
#SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_CLIENT_SECRET'),
#SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile', 'https://www.googleapis.com/auth/gmail.readonly']
#REST_SOCIAL_OAUTH_ABSOLUTE_REDIRECT_URI  = os.getenv('REST_SOCIAL_OAUTH_ABSOLUTE_REDIRECT_URI')

# For persistence handler class
# cwd = os.getcwd()

PYZOHO_CONFIG = {
    'apiBaseUrl': 'https://www.zohoapis.com',
    'apiVersion': 'v2',
    'currentUserEmail': os.environ.get('PYZOHO_USER'),
    'sandbox': os.environ.get('IS_SANDBOX'),
    'applicationLogFilePath': '',
    'client_id': os.environ.get('PYZOHO_CLIENT_ID'),
    'client_secret': os.environ.get('PYZOHO_CLIENT_SECRET'),
    'redirect_uri': os.environ.get('PYZOHO_REDIRECT_URL'),
    'accounts_url': os.environ.get('PYZOHO_ACCOUNT_URL'),
    # 'token_persistence_path': os.environ.get('TOKEN_PERSISTENCE_PATH'),
    # 'access_type': 'offline',
    'persistence_handler_class' : 'ZohoOAuthHandler',
    'persistence_handler_path': '/app/src/core/persist_crm_token.py'
}

# if DEBUG:
#     PYZOHO_CONFIG['sandbox'] = 'true'

PYZOHO_REFRESH_TOKEN = os.environ.get('PYZOHO_REFRESH_TOKEN')
PYZOHO_USER_IDENTIFIER = os.environ.get('PYZOHO_USER')
REDIS_URL = os.environ.get('REDIS_URL')

# Box configuration
BOX_CLIENT_ID = os.environ.get('BOX_CLIENT_ID')
BOX_CLIENT_SECRET = os.environ.get('BOX_CLIENT_SECRET')
BOX_REFRESH_TOKEN = os.environ.get('BOX_REFRESH_TOKEN')
BOX_ACCESS_TOKEN = os.environ.get('BOX_ACCESS_TOKEN')
LICENSE_PARENT_FOLDER_ID = os.environ.get('LICENSE_PARENT_FOLDER_ID')
TEMP_LICENSE_FOLDER = os.environ.get('TEMP_LICENSE_FOLDER')
BOX_JWT_DICT = os.environ.get('BOX_JWT_DICT')
BOX_JWT_USER = os.environ.get('BOX_JWT_USER')

# Zoho Inventory configuration
INVENTORY_CLIENT_ID = os.environ.get('INVENTORY_CLIENT_ID')
INVENTORY_CLIENT_SECRET = os.environ.get('INVENTORY_CLIENT_SECRET')
INVENTORY_REFRESH_TOKEN = os.environ.get('INVENTORY_REFRESH_TOKEN')
INVENTORY_REDIRECT_URI = os.environ.get('INVENTORY_REDIRECT_URO=I')
INVENTORY_ORGANIZATION_ID = os.environ.get('INVENTORY_ORGANIZATION_ID')
INVENTORY_EFD_ORGANIZATION_ID = os.environ.get('INVENTORY_EFD_ORGANIZATION_ID')
INVENTORY_EFL_ORGANIZATION_ID = os.environ.get('INVENTORY_EFL_ORGANIZATION_ID')
INVENTORY_TAXES = os.environ.get('INVENTORY_TAXES')
INVENTORY_BOX_ID = os.environ.get('INVENTORY_BOX_ID')

# Zoho Books configuration
BOOKS_CLIENT_ID = os.environ.get('BOOKS_CLIENT_ID')
BOOKS_CLIENT_SECRET = os.environ.get('BOOKS_CLIENT_SECRET')
BOOKS_ORGANIZATION_ID = os.environ.get('BOOKS_ORGANIZATION_ID')
BOOKS_REDIRECT_URI = os.environ.get('BOOKS_REDIRECT_URI')
BOOKS_REFRESH_TOKEN = os.environ.get('BOOKS_REFRESH_TOKEN')
ESTIMATE_TAXES = os.environ.get('ESTIMATE_TAXES')

# Zoho Sign configuration
SIGN_CLIENT_ID = os.environ.get('SIGN_CLIENT_ID')
SIGN_CLIENT_SECRET = os.environ.get('SIGN_CLIENT_SECRET')
SIGN_REDIRECT_URI = os.environ.get('SIGN_REDIRECT_URI')
SIGN_REFRESH_TOKEN = os.environ.get('SIGN_REFRESH_TOKEN')
SIGN_HOST_URL = os.environ.get('SIGN_HOST_URL')
ESTIMATE_UPLOAD_FOLDER_ID = os.environ.get('ESTIMATE_UPLOAD_FOLDER_ID')
TRANSPORTATION_FEES = os.environ.get('TRANSPORTATION_FEES')
FARM_FOLDER_ID = os.environ.get('FARM_FOLDER_ID')

# slack tokens'
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_CHANNEL_NAME = os.environ.get("SLACK_CHANNEL_NAME")
#sales
SLACK_SALES_CHANNEL = os.environ.get("SLACK_SALES_CHANNEL")
# Admin Email
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")

# layouts
VENDOR_LAYOUT = os.environ.get("VENDOR_LAYOUT")
LEADS_LAYOUT = os.environ.get("LEADS_LAYOUT")

GOOGLEMAPS_API_KEY = os.environ.get('GOOGLEMAPS_API_KEY')
TWILIO_ACCOUNT = os.environ.get('TWILIO_ACCOUNT')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
DEFAULT_PHONE_NUMBER = os.environ.get('DEFAULT_PHONE_NUMBER')
TMP_DIR = os.environ.get('TMP_DIR')

#AWS Creds
AWS_CLIENT_ID = os.environ.get('AWS_CLIENT_ID')
AWS_CLIENT_SECRET = os.environ.get('AWS_CLIENT_SECRET')
AWS_BUCKET = os.environ.get('AWS_BUCKET')
AWS_REGION = os.environ.get('AWS_REGION')

# Authy Application Key
# You can get/create one here : https://www.twilio.com/console/authy/applications
AUTHY_ACCOUNT_SECURITY_API_KEY = os.environ.get('AUTHY_ACCOUNT_SECURITY_API_KEY')
AUTHY_APP_ID = os.environ.get('AUTHY_APP_ID')
AUTHY_APP_NAME = os.environ.get('AUTHY_APP_NAME')

AUTHY_USER_REGISTRATION_CALLBACK_SIGNING_KEY=os.environ.get('AUTHY_USER_REGISTRATION_CALLBACK_SIGNING_KEY')

BCC_APP_ID = os.environ.get('BCC_APP_ID')
BCC_APP_KEY = os.environ.get('BCC_APP_KEY')