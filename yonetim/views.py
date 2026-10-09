from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date as django_parse_date

from .models import (
    Alacak,
    Butce,
    CariHesap,
    CekSenet,
    Fatura,
    Fis,
    GiderKategorisi,
    HaftalikPlan,
    IsletmeGideri,
    Kasa,
    KasaHareketi,
    Odeme,
    TekUrunAyari,
)

def is_kurum(unvan):
    return True
    u = unvan.lower()
    kurum_kelimeleri = ['ltd', 'şti', 'a.ş', 'a.s', 'tic.', 'ticaret', 'san.', 'sanayi', 'market', 'inşaat', 'insaat', 'bilişim', 'hizmet', 'ajans']
    if '(' in unvan and ')' in unvan:
        return True
    for k in kurum_kelimeleri:
        if k in u:
            return True
    return False
from .services.butce_hesapla import (
    butce_guncelle,
    butce_ozetini_hesapla,
    vergi_ayarlarini_getir,
)
from .services.muhasebe import (
    cari_guncelle,
    kasa_guncelle,
    kasa_hareketi_olustur,
    kdv_hesapla,
)


def _parse_decimal(value, field_label):
    if not value or not str(value).strip():
        raise ValueError(f'{field_label} alanı zorunludur.')
    try:
        return Decimal(str(value).replace(',', '.'))
    except InvalidOperation as exc:
        raise ValueError(f'{field_label} geçerli bir sayı olmalıdır.') from exc


def _parse_decimal_optional(value, default=Decimal('0')):
    if not value or not str(value).strip():
        return default
    try:
        return Decimal(str(value).replace(',', '.'))
    except InvalidOperation as exc:
        raise ValueError('Geçerli bir sayı girilmelidir.') from exc


def _parse_date(value, field_label):
    if not value or not str(value).strip():
        raise ValueError(f'{field_label} alanı zorunludur.')
    parsed = django_parse_date(str(value))
    if parsed is None:
        raise ValueError(f'{field_label} geçerli bir tarih olmalıdır.')
    return parsed


def _parse_date_optional(value):
    if not value or not str(value).strip():
        return None
    return django_parse_date(str(value))


def ana_sayfa(request):
    return redirect('yonetim:butce_liste')


# ---------- Ödemeler ----------

def odeme_liste(request):
    odemeler = Odeme.objects.select_related('butce').all()
    return render(request, 'yonetim/odeme_liste.html', {'odemeler': odemeler})


def odeme_ekle(request):
    butceler = Butce.objects.all()
    tek_urun = TekUrunAyari.objects.first()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                islem_tarihi = _parse_date(request.POST.get('islem_tarihi'), 'İşlem Tarihi')
                vade_tarihi = _parse_date_optional(request.POST.get('vade_tarihi'))
                
                kime = (request.POST.get('kime') or '').strip()
                if not kime:
                    raise ValueError('Kime alanı zorunludur.')
                
                cari = None
                if is_kurum(kime):
                    cari = CariHesap.objects.filter(unvan=kime).first()
                    if not cari:
                        cari = CariHesap.objects.create(unvan=kime, tur=CariHesap.TUR_TEDARIKCI)
                
                durum = request.POST.get('durum') or Odeme.DURUM_BEKLIYOR
                aciklama = request.POST.get('aciklama', '')
                butce_id = request.POST.get('butce') or None
                butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None

                Odeme.objects.create(
                    tutar=tutar,
                    islem_tarihi=islem_tarihi,
                    vade_tarihi=vade_tarihi,
                    kime=kime,
                    cari_hesap=cari,
                    durum=durum,
                    aciklama=aciklama,
                    butce=butce,
                )
                if butce:
                    butce_guncelle(butce)
            messages.success(request, 'Ödeme başarıyla kaydedildi.')
            return redirect('yonetim:odeme_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/odeme_form.html', {
        'butceler': butceler,
        'tek_urun': tek_urun,
        'durum_secenekleri': Odeme.DURUM_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


# ---------- Alacaklar ----------

def alacak_liste(request):
    alacaklar = Alacak.objects.select_related('butce', 'cari_hesap').all()
    return render(request, 'yonetim/alacak_liste.html', {'alacaklar': alacaklar})


def alacak_ekle(request):
    butceler = Butce.objects.all()
    tek_urun = TekUrunAyari.objects.first()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                islem_tarihi = _parse_date(request.POST.get('islem_tarihi'), 'İşlem Tarihi')
                tahsil_tarihi = _parse_date_optional(request.POST.get('tahsil_tarihi'))
                
                kimden = (request.POST.get('kimden') or '').strip()
                if not kimden:
                    raise ValueError('Kimden alanı zorunludur.')
                
                cari = None
                if is_kurum(kimden):
                    cari = CariHesap.objects.filter(unvan=kimden).first()
                    if not cari:
                        cari = CariHesap.objects.create(unvan=kimden, tur=CariHesap.TUR_MUSTERI)

                durum = request.POST.get('durum') or Alacak.DURUM_BEKLIYOR
                aciklama = request.POST.get('aciklama', '')
                butce_id = request.POST.get('butce') or None
                butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None

                Alacak.objects.create(
                    tutar=tutar,
                    islem_tarihi=islem_tarihi,
                    tahsil_tarihi=tahsil_tarihi,
                    kimden=kimden,
                    cari_hesap=cari,
                    durum=durum,
                    aciklama=aciklama,
                    butce=butce,
                )
                if butce:
                    butce_guncelle(butce)
            messages.success(request, 'Alacak başarıyla kaydedildi.')
            return redirect('yonetim:alacak_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/alacak_form.html', {
        'butceler': butceler,
        'tek_urun': tek_urun,
        'durum_secenekleri': Alacak.DURUM_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


# ---------- Haftalık Planlar ----------

def haftalik_plan_liste(request):
    bugun = timezone.now().date()

    baslangic_param = request.GET.get('baslangic')
    secilen = django_parse_date(baslangic_param) if baslangic_param else None
    if secilen is None:
        secilen = bugun

    # Haftanın Pazartesi gününe normalize et
    hafta_baslangic = secilen - timedelta(days=secilen.weekday())
    hafta_bitis = hafta_baslangic + timedelta(days=6)

    planlar = HaftalikPlan.objects.filter(
        baslangic_tarihi__lte=hafta_bitis,
        bitis_tarihi__gte=hafta_baslangic,
    ).order_by('baslangic_tarihi', 'id')

    gun_isimleri = [
        'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe',
        'Cuma', 'Cumartesi', 'Pazar',
    ]

    gunler = []
    for i in range(7):
        gun_tarihi = hafta_baslangic + timedelta(days=i)
        gun_planlari = [
            p for p in planlar
            if p.baslangic_tarihi <= gun_tarihi <= p.bitis_tarihi
        ]
        gunler.append({
            'tarih': gun_tarihi,
            'isim': gun_isimleri[i],
            'planlar': gun_planlari,
            'bugun_mu': gun_tarihi == bugun,
        })

    onceki_hafta = hafta_baslangic - timedelta(days=7)
    sonraki_hafta = hafta_baslangic + timedelta(days=7)

    return render(request, 'yonetim/haftalik_plan_liste.html', {
        'gunler': gunler,
        'hafta_baslangic': hafta_baslangic,
        'hafta_bitis': hafta_bitis,
        'onceki_hafta': onceki_hafta,
        'sonraki_hafta': sonraki_hafta,
        'bugun': bugun,
    })


def haftalik_plan_ekle(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                baslik = (request.POST.get('baslik') or '').strip()
                if not baslik:
                    raise ValueError('Başlık alanı zorunludur.')
                baslangic_tarihi = _parse_date(request.POST.get('baslangic_tarihi'), 'Başlangıç Tarihi')
                bitis_tarihi = _parse_date(request.POST.get('bitis_tarihi'), 'Bitiş Tarihi')
                durum = request.POST.get('durum') or HaftalikPlan.DURUM_BEKLIYOR
                detay = request.POST.get('detay', '')

                HaftalikPlan.objects.create(
                    baslik=baslik,
                    baslangic_tarihi=baslangic_tarihi,
                    bitis_tarihi=bitis_tarihi,
                    durum=durum,
                    detay=detay,
                )
            messages.success(request, 'Haftalık plan başarıyla kaydedildi.')
            return redirect('yonetim:haftalik_plan_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/haftalik_plan_form.html', {
        'durum_secenekleri': HaftalikPlan.DURUM_SECENEKLERI,
    })


def haftalik_plan_durum_degistir(request, pk):
    plan = get_object_or_404(HaftalikPlan, pk=pk)
    if request.method == 'POST':
        if plan.durum == HaftalikPlan.DURUM_TAMAMLANDI:
            plan.durum = HaftalikPlan.DURUM_BEKLIYOR
        else:
            plan.durum = HaftalikPlan.DURUM_TAMAMLANDI
        plan.save(update_fields=['durum'])
        messages.success(request, f'"{plan.baslik}" planının durumu güncellendi.')

    geri_donus = request.META.get('HTTP_REFERER')
    if geri_donus:
        return redirect(geri_donus)
    return redirect('yonetim:haftalik_plan_liste')



# ---------- Bütçe ----------

def butce_liste(request):
    butceler = Butce.objects.all()
    butce_ozetleri = []
    for b in butceler:
        ozet = butce_ozetini_hesapla(b)
        butce_ozetleri.append({'butce': b, 'ozet': ozet})
    genel_ozet = butce_ozetini_hesapla()
    return render(request, 'yonetim/butce_liste.html', {
        'butce_ozetleri': butce_ozetleri,
        'genel_ozet': genel_ozet,
    })


def butce_ekle(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                baslangic = _parse_decimal(request.POST.get('baslangic_butcesi'), 'Başlangıç Bütçesi')
                aciklama = request.POST.get('aciklama', '')
                butce = Butce.objects.create(
                    baslangic_butcesi=baslangic,
                    guncel_butce=baslangic,
                    aciklama=aciklama,
                )
                butce_guncelle(butce)
            messages.success(request, 'Bütçe başarıyla oluşturuldu.')
            return redirect('yonetim:butce_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/butce_form.html')


# ---------- Vergi Ayarları ----------

def vergi_ayarlari(request):
    ayar = vergi_ayarlarini_getir()
    tek_urun = TekUrunAyari.objects.first()
    if not tek_urun:
        tek_urun = TekUrunAyari.objects.create()
    cariler = CariHesap.objects.all()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'ayarlar':
            try:
                with transaction.atomic():
                    ayar.kdv_orani = _parse_decimal_optional(request.POST.get('kdv_orani'), ayar.kdv_orani)
                    ayar.gelir_vergisi_orani = _parse_decimal_optional(request.POST.get('gelir_vergisi_orani'), ayar.gelir_vergisi_orani)
                    ayar.kurumlar_vergisi_orani = _parse_decimal_optional(request.POST.get('kurumlar_vergisi_orani'), ayar.kurumlar_vergisi_orani)
                    ayar.stopaj_orani = _parse_decimal_optional(request.POST.get('stopaj_orani'), ayar.stopaj_orani)
                    ayar.kdv_dahil = bool(request.POST.get('kdv_dahil'))
                    ayar.save()
                    for b in Butce.objects.all():
                        butce_guncelle(b)
                messages.success(request, 'Vergi ayarları güncellendi ve bütçe yeniden hesaplandı.')
                return redirect('yonetim:vergi_ayarlari')
            except ValueError as exc:
                messages.error(request, str(exc))
                
        elif form_type == 'tek_urun':
            try:
                tek_urun.urun_adi = request.POST.get('urun_adi', 'Ana Ürün / Hizmet')
                tek_urun.alis_fiyati = _parse_decimal_optional(request.POST.get('alis_fiyati'), tek_urun.alis_fiyati)
                tek_urun.satis_fiyati = _parse_decimal_optional(request.POST.get('satis_fiyati'), tek_urun.satis_fiyati)
                tek_urun.save()
                messages.success(request, 'Tek Ürün ayarları güncellendi.')
                return redirect('yonetim:vergi_ayarlari')
            except ValueError as exc:
                messages.error(request, str(exc))

    return render(request, 'yonetim/vergi_ayarlari.html', {
        'ayar': ayar,
        'tek_urun': tek_urun,
        'cariler': cariler
    })


# ---------- Fişler ----------

def fis_liste(request):
    fisler = Fis.objects.select_related('butce', 'cari_hesap').all()
    return render(request, 'yonetim/fis_liste.html', {'fisler': fisler})


def fis_ekle(request):
    butceler = Butce.objects.all()
    cariler = CariHesap.objects.all()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                fis_turu = request.POST.get('fis_turu') or Fis.FIS_ALIS
                fis_no = request.POST.get('fis_no', '').strip()
                tarih = _parse_date(request.POST.get('tarih'), 'Tarih')
                
                cari_id = request.POST.get('cari_hesap') or None
                cari = CariHesap.objects.filter(pk=cari_id).first() if cari_id else None

                aciklama = request.POST.get('aciklama', '')
                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                kdv_orani = _parse_decimal_optional(request.POST.get('kdv_orani'), Decimal('20'))
                odeme_durumu = request.POST.get('odeme_durumu') or Fis.DURUM_BEKLIYOR
                butce_id = request.POST.get('butce') or None
                butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None
                fis_gorseli = request.FILES.get('fis_gorseli')

                Fis.objects.create(
                    fis_turu=fis_turu,
                    fis_no=fis_no,
                    tarih=tarih,
                    cari_hesap=cari,
                    aciklama=aciklama,
                    tutar=tutar,
                    kdv_orani=kdv_orani,
                    odeme_durumu=odeme_durumu,
                    butce=butce,
                    fis_gorseli=fis_gorseli,
                )
                
                if cari:
                    if fis_turu == Fis.FIS_ALIS:
                        cari.guncel_bakiye += tutar
                    else:
                        cari.guncel_bakiye -= tutar
                    cari.save(update_fields=['guncel_bakiye'])

                if butce:
                    butce_guncelle(butce)
            messages.success(request, 'Fiş başarıyla kaydedildi.')
            return redirect('yonetim:fis_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/fis_form.html', {
        'butceler': butceler,
        'cariler': cariler,
        'durum_secenekleri': Fis.DURUM_SECENEKLERI,
        'fis_turu_secenekleri': Fis.FIS_TURU_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


# ---------- Cari Hesaplar ----------

def cari_liste(request):
    cariler = CariHesap.objects.all()
    toplam_alacak = sum((c.guncel_bakiye for c in cariler if c.guncel_bakiye > 0), Decimal('0'))
    toplam_borc = sum((c.guncel_bakiye for c in cariler if c.guncel_bakiye < 0), Decimal('0'))
    return render(request, 'yonetim/cari_liste.html', {
        'cariler': cariler,
        'toplam_alacak': toplam_alacak,
        'toplam_borc': abs(toplam_borc),
    })


def cari_ekle(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                unvan = (request.POST.get('unvan') or '').strip()
                if not unvan:
                    raise ValueError('Unvan alanı zorunludur.')
                tur = request.POST.get('tur') or CariHesap.TUR_MUSTERI
                baslangic_bakiyesi = _parse_decimal_optional(request.POST.get('baslangic_bakiyesi'))

                cari = CariHesap.objects.create(
                    unvan=unvan,
                    tur=tur,
                    yetkili=request.POST.get('yetkili', ''),
                    telefon=request.POST.get('telefon', ''),
                    eposta=request.POST.get('eposta', ''),
                    adres=request.POST.get('adres', ''),
                    vergi_dairesi=request.POST.get('vergi_dairesi', ''),
                    vergi_no=request.POST.get('vergi_no', ''),
                    baslangic_bakiyesi=baslangic_bakiyesi,
                    guncel_bakiye=baslangic_bakiyesi,
                )
                cari_guncelle(cari)
            messages.success(request, 'Cari hesap başarıyla oluşturuldu.')
            return redirect('yonetim:cari_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/cari_form.html', {
        'tur_secenekleri': CariHesap.TUR_SECENEKLERI,
    })


def cari_detay(request, pk):
    cari = get_object_or_404(CariHesap, pk=pk)
    alacaklar = list(cari.alacaklar.all())
    odemeler = list(cari.odemeler.all()) # wait, Odeme model has 'kime' string, not a ForeignKey to CariHesap?
    faturalar = list(cari.faturalar.all())
    fisler = list(cari.fisler.all())
    
    # We need to build a combined timeline. 
    # BUT wait, Odeme and Alacak in models.py don't have a ForeignKey to CariHesap! 
    # Let me check Odeme and Alacak models. 
    # Ah, Odeme has kime (CharField), Alacak has kimden (CharField).
    # Did the user change it? No, they didn't. 
    # Wait, the prompt says "Altında o cariye ait geçmiş tüm Alacaklar, Ödemeler, Faturalar ve Fişler birleşik bir kronolojik tablo (Cari Ekstre) olarak listelensin."
    # If Odeme/Alacak don't link to CariHesap by ForeignKey, I must filter by `kimden=cari.unvan` or similar. Let's do that.
    alacaklar = list(Alacak.objects.filter(kimden=cari.unvan))
    odemeler = list(Odeme.objects.filter(kime=cari.unvan))
    
    hareketler = []
    
    for a in alacaklar:
        hareketler.append({
            'tarih': a.islem_tarihi,
            'tur': 'Alacak',
            'aciklama': a.aciklama or 'Alacak Kaydı',
            'tutar': a.tutar,
            'borc_alacak': 'alacak', # Bize borçlular, biz alacaklıyız
            'renk': 'success',
        })
        
    for o in odemeler:
        hareketler.append({
            'tarih': o.islem_tarihi,
            'tur': 'Ödeme',
            'aciklama': o.aciklama or 'Ödeme Kaydı',
            'tutar': o.tutar,
            'borc_alacak': 'borc', # Biz ödüyoruz, biz borçluyuz
            'renk': 'danger',
        })
        
    for f in faturalar:
        hareketler.append({
            'tarih': f.tarih,
            'tur': 'Fatura',
            'aciklama': f.fatura_no + ' (' + f.get_tur_display() + ')',
            'tutar': f.toplam_tutar,
            'borc_alacak': 'borc' if f.tur == 'gelen' else 'alacak',
            'renk': 'danger' if f.tur == 'gelen' else 'success',
        })
        
    for fis in fisler:
        hareketler.append({
            'tarih': fis.tarih,
            'tur': 'Fiş',
            'aciklama': fis.aciklama or 'Mal/Hizmet Alımı',
            'tutar': fis.tutar,
            'borc_alacak': 'borc',
            'renk': 'danger',
        })
        
    # Kasa hareketlerini de ekleyelim
    kasa_hareketleri = list(cari.kasa_hareketleri.all())
    for k in kasa_hareketleri:
        hareketler.append({
            'tarih': k.tarih,
            'tur': 'Kasa Hareketi',
            'aciklama': k.aciklama or k.get_islem_turu_display(),
            'tutar': k.tutar,
            'borc_alacak': 'alacak' if k.islem_turu == 'giris' else 'borc',
            'renk': 'success' if k.islem_turu == 'giris' else 'danger',
        })
        
    # Sort by date
    hareketler.sort(key=lambda x: x['tarih'], reverse=True)
    
    return render(request, 'yonetim/cari_detay.html', {
        'cari': cari,
        'hareketler': hareketler
    })


# ---------- Kasa ----------

def kasa_liste(request):
    kasalar = Kasa.objects.all()
    hareketler = KasaHareketi.objects.select_related(
        'kasa', 'cari_hesap', 'fatura', 'isletme_gideri'
    ).all()[:50]
    toplam_kasa = sum((k.guncel_bakiye for k in kasalar), Decimal('0'))
    return render(request, 'yonetim/kasa_liste.html', {
        'kasalar': kasalar,
        'hareketler': hareketler,
        'toplam_kasa': toplam_kasa,
    })


def kasa_ekle(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                kasa_adi = (request.POST.get('kasa_adi') or '').strip()
                if not kasa_adi:
                    raise ValueError('Kasa adı zorunludur.')
                para_birimi = (request.POST.get('para_birimi') or 'TL').strip()
                baslangic_bakiyesi = _parse_decimal_optional(request.POST.get('baslangic_bakiyesi'))
                aciklama = request.POST.get('aciklama', '')

                kasa = Kasa.objects.create(
                    kasa_adi=kasa_adi,
                    para_birimi=para_birimi,
                    baslangic_bakiyesi=baslangic_bakiyesi,
                    guncel_bakiye=baslangic_bakiyesi,
                    aciklama=aciklama,
                )
                kasa_guncelle(kasa)
            messages.success(request, 'Kasa başarıyla oluşturuldu.')
            return redirect('yonetim:kasa_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/kasa_form.html')


def kasa_hareket_ekle(request):
    kasalar = Kasa.objects.all()
    cariler = CariHesap.objects.all()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                kasa_id = request.POST.get('kasa')
                kasa = Kasa.objects.filter(pk=kasa_id).first()
                if not kasa:
                    raise ValueError('Kasa seçimi zorunludur.')
                islem_turu = request.POST.get('islem_turu')
                if islem_turu not in dict(KasaHareketi.ISLEM_SECENEKLERI):
                    raise ValueError('Geçerli bir işlem türü seçiniz.')
                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                tarih = _parse_date(request.POST.get('tarih'), 'İşlem Tarihi')
                aciklama = request.POST.get('aciklama', '')
                cari_id = request.POST.get('cari_hesap') or None
                cari = CariHesap.objects.filter(pk=cari_id).first() if cari_id else None

                kasa_hareketi_olustur(
                    kasa=kasa,
                    islem_turu=islem_turu,
                    tutar=tutar,
                    tarih=tarih,
                    aciklama=aciklama,
                    cari_hesap=cari,
                )
            messages.success(request, 'Kasa hareketi başarıyla kaydedildi.')
            return redirect('yonetim:kasa_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/kasa_hareket_form.html', {
        'kasalar': kasalar,
        'cariler': cariler,
        'islem_secenekleri': KasaHareketi.ISLEM_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


# ---------- İşletme Giderleri ----------

def gider_liste(request):
    giderler = IsletmeGideri.objects.select_related('kategori', 'kasa').all()
    toplam_gider = sum((g.tutar for g in giderler), Decimal('0'))
    return render(request, 'yonetim/gider_liste.html', {
        'giderler': giderler,
        'toplam_gider': toplam_gider,
    })


def gider_ekle(request):
    kategoriler = GiderKategorisi.objects.all()
    kasalar = Kasa.objects.all()
    ayar = vergi_ayarlarini_getir()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                kategori_id = request.POST.get('kategori') or None
                yeni_kategori = (request.POST.get('yeni_kategori') or '').strip()
                if yeni_kategori:
                    kategori, _ = GiderKategorisi.objects.get_or_create(ad=yeni_kategori)
                elif kategori_id:
                    kategori = GiderKategorisi.objects.filter(pk=kategori_id).first()
                    if not kategori:
                        raise ValueError('Seçilen kategori bulunamadı.')
                else:
                    raise ValueError('Kategori seçimi veya yeni kategori adı zorunludur.')

                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                kdv_orani = _parse_decimal_optional(request.POST.get('kdv_orani'), ayar.kdv_orani)
                odeme_tarihi = _parse_date(request.POST.get('odeme_tarihi'), 'Ödeme Tarihi')
                aciklama = request.POST.get('aciklama', '')
                belge = request.FILES.get('belge')
                kasa_id = request.POST.get('kasa') or None
                kasa = Kasa.objects.filter(pk=kasa_id).first() if kasa_id else None

                gider = IsletmeGideri.objects.create(
                    kategori=kategori,
                    tutar=tutar,
                    kdv_orani=kdv_orani,
                    odeme_tarihi=odeme_tarihi,
                    kasa=kasa,
                    aciklama=aciklama,
                    belge=belge,
                )
                if kasa:
                    kasa_hareketi_olustur(
                        kasa=kasa,
                        islem_turu=KasaHareketi.ISLEM_CIKIS,
                        tutar=tutar,
                        tarih=odeme_tarihi,
                        aciklama=f'İşletme gideri: {kategori.ad}',
                        isletme_gideri=gider,
                    )
            messages.success(request, 'İşletme gideri başarıyla kaydedildi.')
            return redirect('yonetim:gider_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/gider_form.html', {
        'kategoriler': kategoriler,
        'kasalar': kasalar,
        'varsayilan_kdv': ayar.kdv_orani,
        'bugun': timezone.now().date(),
    })


# ---------- Faturalar ----------

def fatura_liste(request):
    faturalar = Fatura.objects.select_related('cari_hesap').all()
    toplam_gelen = sum((f.toplam_tutar for f in faturalar if f.tur == Fatura.TUR_GELEN), Decimal('0'))
    toplam_giden = sum((f.toplam_tutar for f in faturalar if f.tur == Fatura.TUR_GIDEN), Decimal('0'))
    return render(request, 'yonetim/fatura_liste.html', {
        'faturalar': faturalar,
        'toplam_gelen': toplam_gelen,
        'toplam_giden': toplam_giden,
    })


def fatura_ekle(request):
    cariler = CariHesap.objects.all()
    kasalar = Kasa.objects.all()
    ayar = vergi_ayarlarini_getir()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                fatura_no = (request.POST.get('fatura_no') or '').strip()
                if not fatura_no:
                    raise ValueError('Fatura No zorunludur.')
                tur = request.POST.get('tur')
                if tur not in dict(Fatura.TUR_SECENEKLERI):
                    raise ValueError('Geçerli bir fatura türü seçiniz.')
                cari_id = request.POST.get('cari_hesap')
                cari = CariHesap.objects.filter(pk=cari_id).first()
                if not cari:
                    raise ValueError('Cari hesap seçimi zorunludur.')
                tarih = _parse_date(request.POST.get('tarih'), 'Fatura Tarihi')
                vade_tarihi = _parse_date_optional(request.POST.get('vade_tarihi'))
                matrah = _parse_decimal(request.POST.get('matrah'), 'Matrah')
                kdv_orani = _parse_decimal_optional(request.POST.get('kdv_orani'), ayar.kdv_orani)
                durum = request.POST.get('durum') or Fatura.DURUM_BEKLIYOR
                aciklama = request.POST.get('aciklama', '')
                fatura_dosyasi = request.FILES.get('fatura_dosyasi')
                kasa_id = request.POST.get('kasa') or None
                kasa = Kasa.objects.filter(pk=kasa_id).first() if kasa_id else None

                kdv_tutari, toplam_tutar = kdv_hesapla(matrah, kdv_orani)

                fatura = Fatura.objects.create(
                    fatura_no=fatura_no,
                    tur=tur,
                    cari_hesap=cari,
                    tarih=tarih,
                    vade_tarihi=vade_tarihi,
                    matrah=matrah,
                    kdv_orani=kdv_orani,
                    kdv_tutari=kdv_tutari,
                    toplam_tutar=toplam_tutar,
                    durum=durum,
                    aciklama=aciklama,
                    fatura_dosyasi=fatura_dosyasi,
                )

                if durum == Fatura.DURUM_ODENDI:
                    fatura.odenen_tutar = toplam_tutar
                    fatura.save(update_fields=['odenen_tutar'])
                    if kasa:
                        islem = KasaHareketi.ISLEM_GIRIS if tur == Fatura.TUR_GIDEN else KasaHareketi.ISLEM_CIKIS
                        kasa_hareketi_olustur(
                            kasa=kasa,
                            islem_turu=islem,
                            tutar=toplam_tutar,
                            tarih=tarih,
                            aciklama=f'Fatura: {fatura_no}',
                            cari_hesap=cari,
                            fatura=fatura,
                        )

                cari_guncelle(cari)
            messages.success(request, 'Fatura başarıyla kaydedildi.')
            return redirect('yonetim:fatura_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/fatura_form.html', {
        'cariler': cariler,
        'kasalar': kasalar,
        'tur_secenekleri': Fatura.TUR_SECENEKLERI,
        'durum_secenekleri': Fatura.DURUM_SECENEKLERI,
        'varsayilan_kdv': ayar.kdv_orani,
        'bugun': timezone.now().date(),
    })


# ---------- Çek / Senet ----------

def ceksenet_liste(request):
    belgeler = CekSenet.objects.select_related('cari_hesap').all()
    toplam_alinan = sum((b.tutar for b in belgeler if b.yon == CekSenet.YON_ALINAN), Decimal('0'))
    toplam_verilen = sum((b.tutar for b in belgeler if b.yon == CekSenet.YON_VERILEN), Decimal('0'))
    return render(request, 'yonetim/ceksenet_liste.html', {
        'belgeler': belgeler,
        'toplam_alinan': toplam_alinan,
        'toplam_verilen': toplam_verilen,
    })


def ceksenet_ekle(request):
    cariler = CariHesap.objects.all()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                tur = request.POST.get('tur')
                if tur not in dict(CekSenet.TUR_SECENEKLERI):
                    raise ValueError('Geçerli bir evrak türü seçiniz.')
                yon = request.POST.get('yon')
                if yon not in dict(CekSenet.YON_SECENEKLERI):
                    raise ValueError('Geçerli bir yön seçiniz.')
                portfoy_no = (request.POST.get('portfoy_no') or '').strip()
                if not portfoy_no:
                    raise ValueError('Portföy / Seri No zorunludur.')
                cari_id = request.POST.get('cari_hesap')
                cari = CariHesap.objects.filter(pk=cari_id).first()
                if not cari:
                    raise ValueError('Cari hesap seçimi zorunludur.')
                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                vade_tarihi = _parse_date(request.POST.get('vade_tarihi'), 'Vade Tarihi')
                keside_tarihi = _parse_date(request.POST.get('keside_tarihi'), 'Keşide Tarihi')
                durum = request.POST.get('durum') or CekSenet.DURUM_PORTFOY
                banka_sube = request.POST.get('banka_sube', '')
                aciklama = request.POST.get('aciklama', '')

                CekSenet.objects.create(
                    tur=tur,
                    yon=yon,
                    portfoy_no=portfoy_no,
                    cari_hesap=cari,
                    tutar=tutar,
                    vade_tarihi=vade_tarihi,
                    keside_tarihi=keside_tarihi,
                    durum=durum,
                    banka_sube=banka_sube,
                    aciklama=aciklama,
                )
                cari_guncelle(cari)
            messages.success(request, 'Çek / Senet kaydı başarıyla oluşturuldu.')
            return redirect('yonetim:ceksenet_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/ceksenet_form.html', {
        'cariler': cariler,
        'tur_secenekleri': CekSenet.TUR_SECENEKLERI,
        'yon_secenekleri': CekSenet.YON_SECENEKLERI,
        'durum_secenekleri': CekSenet.DURUM_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


# ---------- Finansal Portföy (Yönetici Dashboard) ----------

def finans_portfoy(request):
    # Kasa & Banka toplamı
    kasalar = Kasa.objects.all()
    toplam_kasa = sum((k.guncel_bakiye for k in kasalar), Decimal('0'))

    # Cari alacak / borç dengesi
    cariler = CariHesap.objects.all()
    toplam_alacak = sum((c.guncel_bakiye for c in cariler if c.guncel_bakiye > 0), Decimal('0'))
    toplam_borc = sum((c.guncel_bakiye for c in cariler if c.guncel_bakiye < 0), Decimal('0'))
    toplam_borc = abs(toplam_borc)
    net_cari = toplam_alacak - toplam_borc

    # Bekleyen çek / senet toplamları (portföyde olanlar)
    bekleyen_belgeler = CekSenet.objects.filter(durum=CekSenet.DURUM_PORTFOY)
    bekleyen_alinan = sum(
        (b.tutar for b in bekleyen_belgeler if b.yon == CekSenet.YON_ALINAN),
        Decimal('0'),
    )
    bekleyen_verilen = sum(
        (b.tutar for b in bekleyen_belgeler if b.yon == CekSenet.YON_VERILEN),
        Decimal('0'),
    )
    net_ceksenet = bekleyen_alinan - bekleyen_verilen

    # Faturalar
    faturalar = Fatura.objects.all()
    toplam_gelen_fatura = sum(
        (f.toplam_tutar for f in faturalar if f.tur == Fatura.TUR_GELEN),
        Decimal('0'),
    )
    toplam_giden_fatura = sum(
        (f.toplam_tutar for f in faturalar if f.tur == Fatura.TUR_GIDEN),
        Decimal('0'),
    )

    # İşletme giderleri
    giderler = IsletmeGideri.objects.all()
    toplam_gider = sum((g.tutar for g in giderler), Decimal('0'))

    # Operasyonel kâr / zarar
    operasyonel_kar = toplam_gelen_fatura - toplam_giden_fatura - toplam_gider

    # Son kasa hareketleri
    son_hareketler = KasaHareketi.objects.select_related(
        'kasa', 'cari_hesap', 'fatura', 'isletme_gideri'
    ).order_by('-tarih', '-id')[:20]

    return render(request, 'yonetim/finans_portfoy.html', {
        'toplam_kasa': toplam_kasa,
        'toplam_alacak': toplam_alacak,
        'toplam_borc': toplam_borc,
        'net_cari': net_cari,
        'bekleyen_alinan': bekleyen_alinan,
        'bekleyen_verilen': bekleyen_verilen,
        'net_ceksenet': net_ceksenet,
        'toplam_gelen_fatura': toplam_gelen_fatura,
        'toplam_giden_fatura': toplam_giden_fatura,
        'toplam_gider': toplam_gider,
        'operasyonel_kar': operasyonel_kar,
        'son_hareketler': son_hareketler,
    })

# ---------- Ürün İşlemleri ----------

def urun_islemleri(request):
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
    })
def alacak_durum_degistir(request, pk):
    alacak = get_object_or_404(Alacak, pk=pk)
    if alacak.durum == Alacak.DURUM_BEKLIYOR:
        alacak.durum = Alacak.DURUM_TAHSIL
    else:
        alacak.durum = Alacak.DURUM_BEKLIYOR
    alacak.save(update_fields=['durum'])
    if alacak.cari_hesap:
        cari_guncelle(alacak.cari_hesap)
    return redirect(request.META.get('HTTP_REFERER', 'yonetim:alacak_liste'))

def odeme_durum_degistir(request, pk):
    odeme = get_object_or_404(Odeme, pk=pk)
    if odeme.durum == Odeme.DURUM_BEKLIYOR:
        odeme.durum = Odeme.DURUM_ODENDI
    else:
        odeme.durum = Odeme.DURUM_BEKLIYOR
    odeme.save(update_fields=['durum'])
    if odeme.cari_hesap:
        cari_guncelle(odeme.cari_hesap)
    return redirect(request.META.get('HTTP_REFERER', 'yonetim:odeme_liste'))


def alacak_duzenle(request, pk):
    alacak = get_object_or_404(Alacak, pk=pk)
    butceler = Butce.objects.all()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                alacak.tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                alacak.islem_tarihi = _parse_date(request.POST.get('islem_tarihi'), 'İşlem Tarihi')
                alacak.tahsil_tarihi = _parse_date_optional(request.POST.get('tahsil_tarihi'))
                
                kimden = (request.POST.get('kimden') or '').strip()
                if not kimden:
                    raise ValueError('Kimden alanı zorunludur.')
                alacak.kimden = kimden
                
                cari = None
                if is_kurum(kimden):
                    cari = CariHesap.objects.filter(unvan=kimden).first()
                    if not cari:
                        cari = CariHesap.objects.create(unvan=kimden, tur=CariHesap.TUR_MUSTERI)
                alacak.cari_hesap = cari
                
                alacak.durum = request.POST.get('durum') or Alacak.DURUM_BEKLIYOR
                alacak.aciklama = request.POST.get('aciklama', '')
                butce_id = request.POST.get('butce') or None
                alacak.butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None
                alacak.save()
                
                if alacak.cari_hesap:
                    cari_guncelle(alacak.cari_hesap)
                if alacak.butce:
                    butce_guncelle(alacak.butce)
                    
            messages.success(request, 'Alacak başarıyla güncellendi.')
            return redirect('yonetim:alacak_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/alacak_duzenle.html', {
        'alacak': alacak,
        'butceler': butceler,
        'durum_secenekleri': Alacak.DURUM_SECENEKLERI,
    })

def alacak_sil(request, pk):
    alacak = get_object_or_404(Alacak, pk=pk)
    if request.method == 'POST':
        cari = alacak.cari_hesap
        alacak.delete()
        if cari:
            cari_guncelle(cari)
        messages.success(request, 'Alacak başarıyla silindi.')
    return redirect('yonetim:alacak_liste')

def odeme_duzenle(request, pk):
    odeme = get_object_or_404(Odeme, pk=pk)
    butceler = Butce.objects.all()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                odeme.tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                odeme.islem_tarihi = _parse_date(request.POST.get('islem_tarihi'), 'İşlem Tarihi')
                odeme.vade_tarihi = _parse_date_optional(request.POST.get('vade_tarihi'))
                
                kime = (request.POST.get('kime') or '').strip()
                if not kime:
                    raise ValueError('Kime alanı zorunludur.')
                odeme.kime = kime
                
                cari = None
                if is_kurum(kime):
                    cari = CariHesap.objects.filter(unvan=kime).first()
                    if not cari:
                        cari = CariHesap.objects.create(unvan=kime, tur=CariHesap.TUR_TEDARIKCI)
                odeme.cari_hesap = cari
                
                odeme.durum = request.POST.get('durum') or Odeme.DURUM_BEKLIYOR
                odeme.aciklama = request.POST.get('aciklama', '')
                butce_id = request.POST.get('butce') or None
                odeme.butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None
                odeme.save()
                
                if odeme.cari_hesap:
                    cari_guncelle(odeme.cari_hesap)
                if odeme.butce:
                    butce_guncelle(odeme.butce)
                    
            messages.success(request, 'Ödeme başarıyla güncellendi.')
            return redirect('yonetim:odeme_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/odeme_duzenle.html', {
        'odeme': odeme,
        'butceler': butceler,
        'durum_secenekleri': Odeme.DURUM_SECENEKLERI,
    })

def odeme_sil(request, pk):
    odeme = get_object_or_404(Odeme, pk=pk)
    if request.method == 'POST':
        cari = odeme.cari_hesap
        odeme.delete()
        if cari:
            cari_guncelle(cari)
        messages.success(request, 'Ödeme başarıyla silindi.')
    return redirect('yonetim:odeme_liste')

def fis_duzenle(request, pk):
    fis = get_object_or_404(Fis, pk=pk)
    butceler = Butce.objects.all()
    cariler = CariHesap.objects.all()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                fis_turu = request.POST.get('fis_turu') or Fis.FIS_ALIS
                fis.fis_turu = fis_turu
                fis.fis_no = request.POST.get('fis_no', '').strip()
                fis.tarih = _parse_date(request.POST.get('tarih'), 'Tarih')
                
                cari_id = request.POST.get('cari_hesap') or None
                cari = CariHesap.objects.filter(pk=cari_id).first() if cari_id else None
                old_cari = fis.cari_hesap
                fis.cari_hesap = cari
                
                fis.aciklama = request.POST.get('aciklama', '')
                fis.tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                fis.kdv_orani = _parse_decimal_optional(request.POST.get('kdv_orani'), Decimal('20'))
                fis.odeme_durumu = request.POST.get('odeme_durumu') or Fis.DURUM_BEKLIYOR
                
                butce_id = request.POST.get('butce') or None
                fis.butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None
                if 'fis_gorseli' in request.FILES:
                    fis.fis_gorseli = request.FILES.get('fis_gorseli')
                
                fis.save()
                
                if old_cari and old_cari != cari:
                    cari_guncelle(old_cari)
                if cari:
                    cari_guncelle(cari)
                if fis.butce:
                    butce_guncelle(fis.butce)
                    
            messages.success(request, 'Fiş başarıyla güncellendi.')
            return redirect('yonetim:fis_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/fis_duzenle.html', {
        'fis': fis,
        'butceler': butceler,
        'cariler': cariler,
        'durum_secenekleri': Fis.DURUM_SECENEKLERI,
        'fis_turu_secenekleri': Fis.FIS_TURU_SECENEKLERI,
    })

def fis_sil(request, pk):
    fis = get_object_or_404(Fis, pk=pk)
    if request.method == 'POST':
        cari = fis.cari_hesap
        fis.delete()
        if cari:
            cari_guncelle(cari)
        messages.success(request, 'Fiş başarıyla silindi.')
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER', 'yonetim:fis_liste'))

def cari_sil(request, pk):
    cari = get_object_or_404(CariHesap, pk=pk)
    if request.method == 'POST':
        # Silinecek ilişkili veriler
        cari.alacaklar.all().delete()
        cari.odemeler.all().delete()
        cari.fisler.all().delete()
        cari.faturalar.all().delete()
        cari.kasa_hareketleri.all().delete()
        cari.cek_senetler.all().delete()
        
        cari.delete()
        messages.success(request, 'Cari hesap ve tüm ilişkili kayıtları başarıyla silindi.')
    return redirect('yonetim:cari_liste')

def fis_durum_degistir(request, pk):
    fis = get_object_or_404(Fis, pk=pk)
    if fis.odeme_durumu == Fis.DURUM_BEKLIYOR:
        fis.odeme_durumu = Fis.DURUM_ODENDI
    else:
        fis.odeme_durumu = Fis.DURUM_BEKLIYOR
    fis.save(update_fields=['odeme_durumu'])
    if fis.cari_hesap:
        cari_guncelle(fis.cari_hesap)
    return redirect(request.META.get('HTTP_REFERER', 'yonetim:fis_liste'))
