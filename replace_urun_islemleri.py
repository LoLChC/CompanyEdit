import re

with open("yonetim/views.py", "r", encoding="utf-8") as f:
    content = f.read()

new_func = """def urun_islemleri(request):
    tek_urun = TekUrunAyari.objects.first()
    cariler = CariHesap.objects.all()
    butceler = Butce.objects.all()
    
    # En son 50 ürün alış/satış fişini çekelim
    fisler = Fis.objects.filter(fis_turu__in=[Fis.FIS_SATIS, Fis.FIS_ALIS]).order_by('-id')[:50]
    
    gecmis = []
    for f in fisler:
        tur_gosterim = 'Satış (Fiş)' if f.fis_turu == Fis.FIS_SATIS else 'Alış (Fiş)'
        kisi = f.cari_hesap.unvan if f.cari_hesap else '-'
        renk = 'success' if f.fis_turu == Fis.FIS_SATIS else 'danger'
        
        gecmis.append({
            'tarih': f.tarih,
            'tur': tur_gosterim,
            'kisi': kisi,
            'tutar': f.tutar,
            'durum': f.get_odeme_durumu_display(),
            'renk': renk,
            'id': f.id
        })
        
    if request.method == 'POST':
        try:
            with transaction.atomic():
                islem_turu = request.POST.get('islem_turu')
                cari_id = request.POST.get('cari_hesap')
                adet = _parse_decimal(request.POST.get('adet'), 'Adet')
                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                islem_tarihi = _parse_date(request.POST.get('islem_tarihi') or timezone.now().date(), 'İşlem Tarihi')
                butce_id = request.POST.get('butce') or None
                butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None
                
                if islem_turu == 'satis':
                    cari = CariHesap.objects.filter(pk=cari_id).first()
                    if not cari:
                        raise ValueError('Müşteri carisi seçimi zorunludur.')
                    aciklama = f"{adet} adet {tek_urun.urun_adi} Satışı"
                    
                    Fis.objects.create(
                        fis_turu=Fis.FIS_SATIS,
                        cari_hesap=cari,
                        tarih=islem_tarihi,
                        tutar=tutar,
                        odeme_durumu=Fis.DURUM_BEKLIYOR,
                        aciklama=aciklama,
                        butce=butce,
                    )
                    from yonetim.services.muhasebe import cari_guncelle
                    cari_guncelle(cari)
                    
                elif islem_turu == 'alis':
                    cari = CariHesap.objects.filter(unvan__icontains='Elmaslar Pide').first()
                    if not cari:
                        cari = CariHesap.objects.filter(pk=cari_id).first()
                    if not cari:
                        raise ValueError('Tedarikçi carisi bulunamadı.')
                        
                    aciklama = f"{adet} adet {tek_urun.urun_adi} Alışı"
                    
                    Fis.objects.create(
                        fis_turu=Fis.FIS_ALIS,
                        cari_hesap=cari,
                        tarih=islem_tarihi,
                        tutar=tutar,
                        odeme_durumu=Fis.DURUM_BEKLIYOR,
                        aciklama=aciklama,
                        butce=butce,
                    )
                    from yonetim.services.muhasebe import cari_guncelle
                    cari_guncelle(cari)
                else:
                    raise ValueError('Geçersiz işlem türü.')
                    
                if butce:
                    butce_guncelle(butce)
                    
            messages.success(request, 'Ürün işlemi başarıyla kaydedildi.')
            return redirect('yonetim:urun_islemleri')
        except ValueError as exc:
            messages.error(request, str(exc))
            
    return render(request, 'yonetim/urun_islemleri.html', {
        'tek_urun': tek_urun,
        'cariler': cariler,
        'butceler': butceler,
        'gecmis': gecmis,
    })"""

import re
# Find the start of urun_islemleri
start_idx = content.find("def urun_islemleri(request):")
if start_idx == -1:
    print("Function not found!")
else:
    # Find the start of the next function to replace up to there
    next_func_match = re.search(r'\ndef [a-zA-Z_]+\(request.*?\):', content[start_idx+20:])
    if next_func_match:
        end_idx = start_idx + 20 + next_func_match.start()
        new_content = content[:start_idx] + new_func + content[end_idx:]
    else:
        # If no next function, replace till end
        new_content = content[:start_idx] + new_func + "\n"
        
    with open("yonetim/views.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Replaced successfully!")
