from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
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
    Stok,
)
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
    if request.method == 'POST':
        try:
            with transaction.atomic():
                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                islem_tarihi = _parse_date(request.POST.get('islem_tarihi'), 'İşlem Tarihi')
                vade_tarihi = _parse_date(request.POST.get('vade_tarihi'), 'Ödeme Tarihi')
                kime = (request.POST.get('kime') or '').strip()
                if not kime:
                    raise ValueError('Kime alanı zorunludur.')
                durum = request.POST.get('durum') or Odeme.DURUM_BEKLIYOR
                aciklama = request.POST.get('aciklama', '')
                butce_id = request.POST.get('butce') or None
                butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None

                Odeme.objects.create(
                    tutar=tutar,
                    islem_tarihi=islem_tarihi,
                    vade_tarihi=vade_tarihi,
                    kime=kime,
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
        'durum_secenekleri': Odeme.DURUM_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


# ---------- Alacaklar ----------

def alacak_liste(request):
    alacaklar = Alacak.objects.select_related('butce').all()
    return render(request, 'yonetim/alacak_liste.html', {'alacaklar': alacaklar})


def alacak_ekle(request):
    butceler = Butce.objects.all()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                islem_tarihi = _parse_date(request.POST.get('islem_tarihi'), 'İşlem Tarihi')
                tahsil_tarihi = _parse_date(request.POST.get('tahsil_tarihi'), 'Tahsil Tarihi')
                kimden = (request.POST.get('kimden') or '').strip()
                if not kimden:
                    raise ValueError('Kimden alanı zorunludur.')
                durum = request.POST.get('durum') or Alacak.DURUM_BEKLIYOR
                aciklama = request.POST.get('aciklama', '')
                butce_id = request.POST.get('butce') or None
                butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None

                Alacak.objects.create(
                    tutar=tutar,
                    islem_tarihi=islem_tarihi,
                    tahsil_tarihi=tahsil_tarihi,
                    kimden=kimden,
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
        'durum_secenekleri': Alacak.DURUM_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


# ---------- Haftalık Planlar ----------

def haftalik_plan_liste(request):
    planlar = HaftalikPlan.objects.all()
    return render(request, 'yonetim/haftalik_plan_liste.html', {'planlar': planlar})


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


# ---------- Stoklar ----------

def stok_liste(request):
    stoklar = Stok.objects.all()
    return render(request, 'yonetim/stok_liste.html', {'stoklar': stoklar})


def stok_ekle(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                urun_adi = (request.POST.get('urun_adi') or '').strip()
                if not urun_adi:
                    raise ValueError('Ürün adı zorunludur.')
                adet_miktar = _parse_decimal(request.POST.get('adet_miktar'), 'Adet / Miktar')
                birim = (request.POST.get('birim') or 'Adet').strip()
                alis_fiyati = _parse_decimal_optional(request.POST.get('alis_fiyati'))
                alim_tarihi = _parse_date(request.POST.get('alim_tarihi'), 'Alım Tarihi')

                Stok.objects.create(
                    urun_adi=urun_adi,
                    adet_miktar=adet_miktar,
                    birim=birim,
                    alis_fiyati=alis_fiyati,
                    alim_tarihi=alim_tarihi,
                )
            messages.success(request, 'Stok kaydı başarıyla oluşturuldu.')
            return redirect('yonetim:stok_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/stok_form.html', {
        'bugun': timezone.now().date(),
    })


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
    if request.method == 'POST':
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

    return render(request, 'yonetim/vergi_ayarlari.html', {'ayar': ayar})


# ---------- Fişler ----------

def fis_liste(request):
    fisler = Fis.objects.select_related('butce').all()
    return render(request, 'yonetim/fis_liste.html', {'fisler': fisler})


def fis_ekle(request):
    butceler = Butce.objects.all()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
                tarih = _parse_date(request.POST.get('tarih'), 'Tarih')
                kategori = (request.POST.get('kategori') or '').strip()
                if not kategori:
                    raise ValueError('Kategori alanı zorunludur.')
                aciklama = request.POST.get('aciklama', '')
                butce_id = request.POST.get('butce') or None
                butce = Butce.objects.filter(pk=butce_id).first() if butce_id else None
                fis_gorseli = request.FILES.get('fis_gorseli')

                Fis.objects.create(
                    tutar=tutar,
                    tarih=tarih,
                    kategori=kategori,
                    aciklama=aciklama,
                    butce=butce,
                    fis_gorseli=fis_gorseli,
                )
                if butce:
                    butce_guncelle(butce)
            messages.success(request, 'Fiş başarıyla kaydedildi.')
            return redirect('yonetim:fis_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/fis_form.html', {'butceler': butceler})


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
