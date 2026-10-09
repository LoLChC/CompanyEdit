import os
import sys
import django
import re

# 1. Update views.py for is_kurum
views_path = os.path.join(os.path.dirname(__file__), 'yonetim', 'views.py')
with open(views_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r"def is_kurum\(unvan\):.*?return False", re.DOTALL)
new_content = pattern.sub("def is_kurum(unvan):\n    return True", content)

with open(views_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("1. views.py 'is_kurum' kontrolü kaldırıldı.")

# 2. Kurtarma işlemi
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sirket_panel.settings')
django.setup()

from yonetim.models import Alacak, Odeme, CariHesap
from decimal import Decimal

def kurtar():
    alacaklar = Alacak.objects.all()
    odemeler = Odeme.objects.all()
    
    isimler = set()
    for a in alacaklar:
        if a.kimden:
            isimler.add(a.kimden.strip())
            
    for o in odemeler:
        if o.kime:
            isimler.add(o.kime.strip())
            
    print(f"\nToplam {len(isimler)} farklı cari isim (Alacak ve Ödeme) bulundu.")
    
    olusturulan = 0
    baglanan_alacak = 0
    baglanan_odeme = 0
    
    for isim in isimler:
        cari = CariHesap.objects.filter(unvan=isim).first()
        if not cari:
            cari = CariHesap.objects.create(unvan=isim, tur=CariHesap.TUR_DIGER)
            olusturulan += 1
            print(f"Oluşturuldu: {isim}")
            
        # Alacaklar
        for a in Alacak.objects.filter(kimden__iexact=isim):
            if a.cari_hesap != cari:
                a.cari_hesap = cari
                a.save()
                baglanan_alacak += 1
                
        # Ödemeler
        for o in Odeme.objects.filter(kime__iexact=isim):
            if o.cari_hesap != cari:
                o.cari_hesap = cari
                o.save()
                baglanan_odeme += 1
                
    # Bakiyeleri hesapla
    for cari in CariHesap.objects.all():
        alacak_toplam = sum([a.tutar for a in cari.alacaklar.filter(durum=Alacak.DURUM_BEKLIYOR)])
        odeme_toplam = sum([o.tutar for o in cari.odemeler.filter(durum=Odeme.DURUM_BEKLIYOR)])
        
        yeni_bakiye = odeme_toplam - alacak_toplam
        cari.guncel_bakiye = yeni_bakiye
        cari.save()
        
    print(f"\nKurtarma Özeti:")
    print(f"Yeni oluşturulan cari: {olusturulan}")
    print(f"Geri bağlanan alacak sayısı: {baglanan_alacak}")
    print(f"Geri bağlanan ödeme sayısı: {baglanan_odeme}")
    print("Tüm bakiyeler güncellendi!")

if __name__ == '__main__':
    kurtar()
