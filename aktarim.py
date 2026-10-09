import os
import django
import sys
import re
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sirket_panel.settings')
sys.path.append(r'C:\Users\lolch\Desktop\CompanyEdit')
django.setup()

from yonetim.models import Alacak, Odeme, Urun, UrunHareketi, CariHesap

def run_import():
    satis_count = 0
    alis_count = 0
    
    # Process Alacak (Sales)
    for alacak in Alacak.objects.all():
        # Prevent duplicates
        ref_text = f"(Alacak Ref: {alacak.id})"
        if UrunHareketi.objects.filter(aciklama__endswith=ref_text).exists():
            continue
            
        # Parse text
        text = f"{alacak.kimden} {alacak.aciklama}"
        adet = 1
        urun_adi = "Standart Ürün"
        
        match = re.search(r'(\d+)\s*(?:adet|Adet|ADET)?\s*(?:[üÜ]r[üu]n)?', alacak.aciklama)
        if match:
            adet = Decimal(match.group(1))
            if adet == 0:
                adet = Decimal(1)
        
        # Determine unit price
        birim_fiyat = alacak.tutar / adet if adet else alacak.tutar
        
        # Get or create Urun
        urun, _ = Urun.objects.get_or_create(
            urun_adi=urun_adi,
            defaults={
                'birim': 'Adet',
                'alis_fiyati': Decimal('0.00'),
                'satis_fiyati': birim_fiyat,
                'mevcut_stok': Decimal('0.00')
            }
        )
        
        # Get or create CariHesap
        cari, _ = CariHesap.objects.get_or_create(
            unvan=alacak.kimden,
            defaults={'tur': 'musteri'}
        )
        
        # Create UrunHareketi
        UrunHareketi.objects.create(
            islem_turu='satis',
            urun=urun,
            cari_hesap=cari,
            adet=adet,
            birim_fiyat=birim_fiyat,
            toplam_tutar=alacak.tutar,
            tarih=alacak.islem_tarihi,
            aciklama=f"{alacak.aciklama} {ref_text}".strip()
        )
        satis_count += 1
        
    # Process Odeme (Purchases)
    for odeme in Odeme.objects.all():
        ref_text = f"(Odeme Ref: {odeme.id})"
        if UrunHareketi.objects.filter(aciklama__endswith=ref_text).exists():
            continue
            
        # Skip bank payments
        kime_lower = odeme.kime.lower()
        aciklama_lower = odeme.aciklama.lower()
        if 'bank' in kime_lower or 'express' in kime_lower or 'kart' in aciklama_lower or 'banka' in aciklama_lower:
            continue
            
        adet = Decimal('1.00')
        urun_adi = odeme.kime  # Use the supplier/person name as the product for lack of specific product
        
        match = re.search(r'(\d+)\s*(?:adet|Adet|ADET)?', odeme.aciklama)
        if match:
            adet = Decimal(match.group(1))
            if adet == 0:
                adet = Decimal(1)
                
        birim_fiyat = odeme.tutar / adet if adet else odeme.tutar
        
        # Get or create Urun
        urun, _ = Urun.objects.get_or_create(
            urun_adi=urun_adi,
            defaults={
                'birim': 'Adet',
                'alis_fiyati': birim_fiyat,
                'satis_fiyati': birim_fiyat * Decimal('1.5'),
                'mevcut_stok': Decimal('0.00')
            }
        )
        
        # Get or create CariHesap
        cari, _ = CariHesap.objects.get_or_create(
            unvan=odeme.kime,
            defaults={'tur': 'tedarikci'}
        )
        
        # Create UrunHareketi
        UrunHareketi.objects.create(
            islem_turu='alis',
            urun=urun,
            cari_hesap=cari,
            adet=adet,
            birim_fiyat=birim_fiyat,
            toplam_tutar=odeme.tutar,
            tarih=odeme.islem_tarihi,
            aciklama=f"{odeme.aciklama} {ref_text}".strip()
        )
        alis_count += 1

    print(f"Aktarım Tamamlandı! {satis_count} adet satış hareketi, {alis_count} adet alış hareketi eklendi.")

if __name__ == '__main__':
    run_import()
