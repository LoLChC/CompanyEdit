import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sirket_panel.settings')
sys.path.append(r'C:\Users\lolch\Desktop\CompanyEdit')
django.setup()

from yonetim.models import Alacak, Odeme

print("=== ALACAK KAYITLARI ===")
for a in Alacak.objects.all()[:10]:
    print(f"ID: {a.id} | Kimden: {a.kimden} | Tutar: {a.tutar} | Aciklama: {a.aciklama}")

print("\n=== ODEME KAYITLARI ===")
for o in Odeme.objects.all()[:10]:
    print(f"ID: {o.id} | Kime: {o.kime} | Tutar: {o.tutar} | Aciklama: {o.aciklama}")
