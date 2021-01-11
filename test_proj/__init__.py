import os

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_proj.settings'
django.setup()
