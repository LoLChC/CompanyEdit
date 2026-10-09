import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sirket_panel.settings")
django.setup()

from yonetim.models import Alacak, Odeme, CariHesap
from django.db import transaction

def recover_cariler():
    print("RECOVERY BASCALADI")
    
    unique_names = set()
    for a in Alacak.objects.all():
        if a.kimden:
            unique_names.add(a.kimden.strip())
            
    for o in Odeme.objects.all():
        if o.kime:
            unique_names.add(o.kime.strip())
            
    with transaction.atomic():
        created_count = 0
        for name in unique_names:
            cari, created = CariHesap.objects.get_or_create(unvan=name)
            if created:
                created_count += 1
                
        # Simdi alacaklari ve odemeleri baglayalim
        for a in Alacak.objects.all():
            if a.kimden:
                cari = CariHesap.objects.get(unvan=a.kimden.strip())
                if a.cari_hesap != cari:
                    a.cari_hesap = cari
                    a.save()
                    
        for o in Odeme.objects.all():
            if o.kime:
                cari = CariHesap.objects.get(unvan=o.kime.strip())
                if o.cari_hesap != cari:
                    o.cari_hesap = cari
                    o.save()
                    
        # Bakiyeleri guncelle
        for cari in CariHesap.objects.all():
            alacaklar = cari.alacaklar.all()
            odemeler = cari.odemeler.all()
            
            bakiye = cari.baslangic_bakiyesi
            for o in odemeler:
                bakiye += o.tutar
            for a in alacaklar:
                bakiye -= a.tutar
                
            cari.guncel_bakiye = bakiye
            cari.save(update_fields=['guncel_bakiye'])
            
    print(f"Recovery tamamlandi. Olusturulan cari sayisi: {created_count}")

if __name__ == '__main__':
    recover_cariler()
