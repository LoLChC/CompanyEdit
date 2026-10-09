import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sirket_panel.settings')
sys.path.append(r'C:\Users\lolch\Desktop\CompanyEdit')
django.setup()

from yonetim.models import Alacak, Odeme

with open(r'C:\Users\lolch\Desktop\CompanyEdit\dump.txt', 'w', encoding='utf-8') as f:
    f.write("=== ALACAK KAYITLARI ===\n")
    for a in Alacak.objects.all():
        f.write(f"ID: {a.id} | Kimden: {a.kimden} | Tutar: {a.tutar} | Aciklama: {a.aciklama}\n")

    f.write("\n=== ODEME KAYITLARI ===\n")
    for o in Odeme.objects.all():
        f.write(f"ID: {o.id} | Kime: {o.kime} | Tutar: {o.tutar} | Aciklama: {o.aciklama}\n")
