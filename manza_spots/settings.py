import os
from datetime import timedelta
from pathlib import Path
import os
from decouple import config
import sentry_sdk
from rich.logging import RichHandler
from datetime import timedelta
import warnings
import logging.config
from django.conf import settings
DEBUG = config('DEBUG', cast=bool)

#Porblema de django avienta warnings estupidos toco ignorarlos
warnings.filterwarnings(
    "ignore",
    message="app_settings.USERNAME_REQUIRED is deprecated",
)
warnings.filterwarnings(
    "ignore",
    message="app_settings.EMAIL_REQUIRED is deprecated",
)

#------------------------------ CONFIGURACION DE SENTRY ----------------------------------------
if not config('DEBUG', default=True, cast=bool):
    sentry_sdk.init(
        dsn=config('SDK_SENTRY', default=None),
        send_default_pii=True,
    )


#----------------------------- CARPETAS RELEVANTES ----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


#----------------------------- APPS INSTALADAS ----------------------------------------------------
INSTALLED_APPS = [
    #Default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django_rest_passwordreset",
    'django.contrib.sites',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'drf_spectacular',
    'django_filters',
    'rest_framework_gis',
    
    # JWT apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  
    'corsheaders',
    'rest_framework.authtoken',
 
    # Django Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',

     # GeoDjango
    'django.contrib.gis',
    
    # Local apps
    'authentication',
    'core',
    'logs',
    'users.apps.UsersConfig',
    'spots_routes'
]

#----------------------------- MIDDLEWARE ----------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',    
]


#----------------------------- DIRECCION DE LOS TEMPLATES(EN ESTE CASO SOLO LOS DE EMAILS) ----------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


#----------------------------- DATABASE ----------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
    }
}

#-------------------------------------- PASSWORD VALIDATORS --------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

#-------------------------------------- IDIOMA - ZONA HORARIA  --------------------------------------------
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

#-------------------------------------- STATIC FILES  --------------------------------------------
STATIC_URL = 'static/'


#-------------------------------------- JWT ---------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': config('SECRET_KEY'),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
}

# REST_USE_JWT = True
# JWT_AUTH_COOKIE = 'access'
# JWT_AUTH_REFRESH_COOKIE = 'refresh'

# ---------------------------------------------- CORS ----------------------------------------
CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=lambda v: [s.strip() for s in v.split(",") if s]
) if not DEBUG else []

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

#---------------------------------------------- REST AUTH -----------------------------------------------------
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_RETURN_EXPIRATION': True,
    'REGISTER_SERIALIZER': 'dj_rest_auth.registration.serializers.RegisterSerializer',
    'TOKEN_MODEL': None,  
}

#---------------------------------------------- ALL AUTH -----------------------------------------------------
ACCOUNT_LOGIN_METHODS = {'email'}

ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_AUTO_SIGNUP = True

# ---------------------------------------- EMAIL CONFIG -------------------------------------------
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')


# ---------------------------------------- LOGGING -------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'rich': {
            'format': "%(message)s",
            'datefmt': "[%X]",
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            "class": "rich.logging.RichHandler",
            'formatter': 'rich',
            'rich_tracebacks': True,   
            'markup': True,
            'log_time_format': "%H:%M:%S",
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
            'filters': ['require_debug_false']
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'errors.log',
            'maxBytes': 1024 * 1024 * 15,
            'backupCount': 10,
            'formatter': 'verbose',
            'filters': ['require_debug_false']
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'authentication': {  
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'users': {  
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

#-------------------------------------------- SOCIALACCOUNT_PROVIDERS DE ALLAUTH -------------------------------------------
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': config('ID_GOOGLE_CLIENT'),
            'secret': config('SECRET_GOOGLE_CLIENT'),
            'key': ''
        }
    },
    
    'facebook': {
        'SCOPE': [
            'email',
            'public_profile'
        ],
        'AUTH_PARAMS': {
            'auth_type': 'reauthenticate'
        },
        'APP': {
            'client_id': config('FACEBOOK_APP_ID'),
            'secret': config('FACEBOOK_APP_SECRET'),
            'key': ''
        }
    }
}
GOOGLE_OAUTH2_CLIENT_ID = config('ID_GOOGLE_CLIENT')

#--------------------------------- DJANGO GEO ------------------------------------------------
#Si se quiere ejecutar de forma local desde una maquina windows, es necesario tener instalado OSGeo4W en el disco.
#No es necesario si se ejecutara desde mac, linux o docker
if os.name == 'nt':
    OSGEO_PATH = config('OSGEO_PATH')
    
    GDAL_LIBRARY_PATH = os.path.join(OSGEO_PATH, 'bin', config('GDAL_LIBRARY_PATH'))
    GEOS_LIBRARY_PATH = os.path.join(OSGEO_PATH, 'bin', config('GEOS_LIBRARY_PATH'))
    
    # Agrega OSGeo4W al PATH del sistema
    os.environ['PATH'] = os.path.join(OSGEO_PATH, 'bin') + ';' + os.environ['PATH']
    os.environ['PROJ_LIB'] = os.path.join(OSGEO_PATH, 'share', 'proj')
    
    
#--------------------------------- REST_FRAMEWORK ------------------------------------------------
#Configuracion de los limites de peticiones de la api
if config('ACTIVE_RATES', default=False, cast=bool):
    DEFAULT_THROTTLE_CLASSES = (
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
            'manza_spots.throttling.BurstRateThrottle',
    )
    DEFAULT_THROTTLE_RATES = {
            'anon': '35/hour',
            'user': '500/hour',
            'login': '5/hour',
            'register': '3/hour',
            'sensitive': '5/hour',
            'heavy': '20/hour',
            'burst': '30/min',
    }
else:
    DEFAULT_THROTTLE_CLASSES = (
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
            'manza_spots.throttling.BurstRateThrottle',
    )
    DEFAULT_THROTTLE_RATES = {
            'anon': '9935/hour',
            'user': '99500/hour',
            'login': '995/hour',
            'register': '993/hour',
            'sensitive': '995/hour',
            'heavy': '9920/hour',
            'burst': '9930/min',
    }


REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    'DEFAULT_THROTTLE_CLASSES': DEFAULT_THROTTLE_CLASSES,
    'DEFAULT_THROTTLE_RATES': DEFAULT_THROTTLE_RATES,

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': config('PAGINATION_LIMIT'),

    'DEFAULT_RENDERER_CLASSES': [
        'manza_spots.renderers.StandardJSONRenderer',
    ],

    'EXCEPTION_HANDLER': 'core.utils.exceptions.custom_exception_handler',
}

#-------------------------------------------- SPECTACULAR SETTINGS  ------------------------------------------------
#configuracion de la documentacion
SPECTACULAR_SETTINGS = {
    'TITLE': 'Manza Spots',
    'DESCRIPTION': 'API para gestión de spots, rutas y perfiles de usuarios',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    
    'TAGS': [
        {'name': 'auth', 'description': 'Autenticación, providers y tokens JWT'},
        {'name': 'users', 'description': 'Gestión de usuarios'},
        {'name': 'spots', 'description': 'Spots y relacionado'},
        {'name': 'spot-captions', 'description': 'Fotos de los spots'},
        {'name': 'spots-favorite', 'description' : 'Spots favoritos'},
        {'name': 'routes', 'description': 'Rutas y recorridos'},
        {'name': 'routes-photos', 'description': 'Fotos de las rutas'},
        {'name': 'routes-favorite', 'description' : 'Rutas favoritas'},                
    ],
        
        
    'COMPONENT_SPLIT_REQUEST': True,  
    'SCHEMA_PATH_PREFIX': r'/api/',   # Prefijo de tus URLs
    
    # Autenticación
    'SECURITY': [{'bearerAuth': []}],
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
}


#------------------------------ CACHE -------------------------------------------------------------

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{os.getenv("REDIS_HOST", "localhost")}:{os.getenv("REDIS_PORT", "6379")}/1',
        'OPTIONS': {
            'socket_connect_timeout': 5,
            'socket_timeout': 5,
        }
    }
}


db_config = DATABASES['default']
SCHEDULER_CONFIG = {
    'apscheduler.jobstores.default': {
        'type': 'sqlalchemy',
        'url': f"postgresql://{db_config['USER']}:{db_config['PASSWORD']}@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': '3'
    },
    'apscheduler.job_defaults.coalesce': 'true',
    'apscheduler.job_defaults.max_instances': '1',
    'apscheduler.timezone': 'America/Mexico_City',
}

UNVERIFIED_USER_EXPIRATION_DAYS = 7

# ==================== SECURITY (Producción) ====================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

#================================================ AUTH BACKEND =====================================================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

#----------------------------- EXTRAS -----------------------------------------------------------
SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",")]
)

ROOT_URLCONF = 'manza_spots.urls'
WSGI_APPLICATION = 'manza_spots.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1

#================================================ AUTH BACKEND =====================================================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

#Obligamos a django a crear los loggins
logging.config.dictConfig(settings.LOGGING)

