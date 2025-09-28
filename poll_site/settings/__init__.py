import os
from dotenv import load_dotenv
load_dotenv()
env = os.environ.get('DJANGO_ENV', 'production')

if env == 'production':
    from .production import *
else:
    from .local import *
