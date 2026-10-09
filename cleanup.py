import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sirket_panel.settings')
django.setup()

from yonetim.models import Alacak, CariHesap, Fis, Odeme, KasaHareketi

# Delete test records
Alacak.objects.filter(kimden__icontains='Ahmet Bey(Espiye ÇPL)', tutar=0).delete()
CariHesap.objects.filter(unvan__icontains='Ahmet Bey(Espiye ÇPL)').delete()
CariHesap.objects.filter(unvan__icontains='İlker').delete()

# Create or get 'Elmaslar Pide'
CariHesap.objects.get_or_create(unvan='Elmaslar Pide', defaults={'tur': 'tedarikci'})
print('Cleanup done!')
