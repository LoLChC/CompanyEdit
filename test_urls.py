# -*- coding: utf-8 -*-
import os
import django
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sirket_panel.settings')
django.setup()

client = Client()

urls_to_test = [
    '/cariler/',
    '/alacaklar/',
    '/odemeler/',
    '/urun-islemleri/'
]

all_passed = True
for url in urls_to_test:
    response = client.get(url)
    if response.status_code == 200:
        print(f"PASS: {url} returned 200 OK.")
    else:
        print(f"FAIL: {url} returned {response.status_code}.")
        all_passed = False

if all_passed:
    print("ALL TESTS PASSED.")
else:
    print("SOME TESTS FAILED.")
