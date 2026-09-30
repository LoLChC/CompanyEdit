from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_none, get_object_or_404, redirect, render
from django.utils import timezone

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
    VergiAyarlari,
)
from .services.butce_hesapla import butce_guncelle, butce_ozetini_hesapla, vergi_ayarlarini_getir
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
    return value


def _get_butce_or_none(butce_id):
    if not butce_id:
        return None
    try:
        return Butce.objects.get(pk=int(butce_id))
    except (Butce.DoesNotExist, ValueError, TypeError):
        return None


def _butceyi_yenile(butce):
    if butce is not None:
        butce_guncelle(butce)
        return
    for kayit in Butce.objects.all():
        butce_guncelle(kayit)


def ana_sayfa(request):
    return redirect('yonetim:butce_liste')


def odeme_liste(request):
    odemeler = Odeme.objects.select_related('butce').all()
    return render(request, 'yonetim/odeme_liste.html', {'odemeler': odemeler})


def odeme_ekle(request):
    butceler = Butce.objects.all()
    if request.method == 'POST':
        try:
            tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
            islem_tarihi = _parse_date(request.POST.get('islem_tarihi'), 'İşlem Tarihi')
            vade_tarihi = _parse_date(request.POST.get('vade_tarihi'), 'Ödeme Tarihi')
            kime = request.POST.get('kime', '').strip()
            if not kime:
                raise ValueError('Kime alanı zorunludur.')
            aciklama = request.POST.get('aciklama', '').strip()
            durum = request.POST.get('durum', Odeme.DURUM_BEKLIYOR)
            if durum not in (Odeme.DURUM_ODENDI, Odeme.DURUM_BEKLIYOR):
                durum = Odeme.DURUM_BEKLIYOR
            butce = _get_butce_or_none(request.POST.get('butce'))
            odeme = Odeme.objects.create(
                tutar=tutar,
                islem_tarihi=islem_tarihi,
                vade_tarihi=vade_tarihi,
                aciklama=aciklama,
                kime=kime,
                durum=durum,
                butce=butce,
            )
            _butceyi_yenile(butce)
            messages.success(request, f'Ödeme kaydı oluşturuldu (#{odeme.id}).')
            return redirect('yonetim:odeme_liste')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/odeme_form.html', {
        'butceler': butceler,
        'durum_secenekleri': Odeme.DURUM_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


def alacak_liste(request):
    alacaklar = Alacak.objects.select_related('butce').all()
    return render(request, 'yonetim/alacak_liste.html', {'alacaklar': alacaklar})


def alacak_ekle(request):
    butceler = Butce.objects.all()
    if request.method == 'POST':
        try:
            tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
            islem_tarihi = _parse_date(request.POST.get('islem_tarihi'), 'İşlem Tarihi')
            tahsil_tarihi = _parse_date(request.POST.get('tahsil_tarihi'), 'Tahsil Tarihi')
            kimden = request.POST.get('kimden', '').strip()
            if not kimden:
                raise ValueError('Kimden alanı zorunludur.')
            aciklama = request.POST.get('aciklama', '').strip()
            durum = request.POST.get('durum', Alacak.DURUM_BEKLIYOR)
            if durum not in (Alacak.DURUM_TAHSIL, Alacak.DURUM_BEKLIYOR):
                durum = Alacak.DURUM_BEKLIYOR
            butce = _get_butce_or_none(request.POST.get('butce'))
            alacak = Alacak.objects.create(
                tutar=tutar,
                islem_tarihi=islem_tarihi,
                tahsil_tarihi=tahsil_tarihi,
                aciklama=aciklama,
                kimden=kimden,
                durum=durum,
                butce=butce,
            )
            _butceyi_yenile(butce)
            messages.success(request, f'Alacak kaydı oluşturuldu (#{alacak.id}).')
            return redirect('yonetim:alacak_liste')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/alacak_form.html', {
        'butceler': butceler,
        'durum_secenekleri': Alacak.DURUM_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


def haftalik_plan_liste(request):
    planlar = HaftalikPlan.objects.all()
    return render(request, 'yonetim/haftalik_plan_liste.html', {'planlar': planlar})


def haftalik_plan_ekle(request):
    if request.method == 'POST':
        try:
            baslik = request.POST.get('baslik', '').strip()
            if not baslik:
                raise ValueError('Başlık alanı zorunludur.')
            detay = request.POST.get('detay', '').strip()
            baslangic_tarihi = _parse_date(request.POST.get('baslangic_tarihi'), 'Başlangıç Tarihi')
            bitis_tarihi = _parse_date(request.POST.get('bitis_tarihi'), 'Bitiş Tarihi')
            if baslangic_tarihi > bitis_tarihi:
                raise ValueError('Başlangıç tarihi bitiş tarihinden sonra olamaz.')
            durum = request.POST.get('durum', HaftalikPlan.DURUM_BEKLIYOR)
            if durum not in (HaftalikPlan.DURUM_TAMAMLANDI, HaftalikPlan.DURUM_BEKLIYOR):
                durum = HaftalikPlan.DURUM_BEKLIYOR
            plan = HaftalikPlan.objects.create(
                baslik=baslik,
                detay=detay,
                baslangic_tarihi=baslangic_tarihi,
                bitis_tarihi=bitis_tarihi,
                durum=durum,
            )
            messages.success(request, f'Haftalık plan oluşturuldu (#{plan.id}).')
            return redirect('yonetim:haftalik_plan_liste')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/haftalik_plan_form.html', {
        'durum_secenekleri': HaftalikPlan.DURUM_SECENEKLERI,
    })


def stok_liste(request):
    stoklar = Stok.objects.all()
    return render(request, 'yonetim/stok_liste.html', {'stoklar': stoklar})


def stok_ekle(request):
    if request.method == 'POST':
        try:
            urun_adi = request.POST.get('urun_adi', '').strip()
            if not run_adi := urun_adi:
                raise ValueError('Ürün adı alanı zorunludur.')
            adet_miktar = _parse_decimal(request.POST.get('adet_miktar'), 'Adet / Miktar')
            birim = request.POST.get('birim', 'Adet').strip() or 'Adet'
            alis_fiyati = _parse_decimal_optional(request.POST.get('alis_fiyati'))
            alim_tarihi = _parse_date(request.POST.get('alim_tarihi'), 'Alım Tarihi')
            stok = Stok.objects.create(
                urun_adi=urun_adi,
                adet_miktar=adet_miktar,
                birim=birim,
                alis_fiyati=alis_fiyati,
                alim_tarihi=alim_tarihi,
            )
            messages.success(request, f'Stok kaydı oluşturuldu (#{stok.id}).')
            return redirect('yonetim:stok_liste')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/stok_form.html', {
        'bugun': timezone.now().date(),
    })


def butce_liste(request):
    butceler = Butce.objects.all()
    butce_ozetleri = []
    for butce in butceler:
        ozet = butce_guncelle(butce)
        butce_ozetleri.append({'butce': butce, 'ozet': ozet})
    genel_ozet = butce_ozetini_hesapla()
    return render(request, 'yonetim/butce_liste.html', {
        'butce_ozetleri': butce_ozetleri,
        'genel_ozet': genel_ozet,
    })


def butce_ekle(request):
    if request.method == 'POST':
        try:
            baslangic_butcesi = _parse_decimal(request.POST.get('baslangic_butcesi'), 'Başlangıç Bütçesi')
            aciklama = request.POST.get('aciklama', '').strip()
            butce = Butce.objects.create(
                baslangic_butcesi=baslangic_butcesi,
                guncel_butce=baslangic_butcesi,
                son_islem_tarihi=timezone.now().date(),
                aciklama=aciklama,
            )
            butce_guncelle(butce)
            messages.success(request, f'Bütçe kaydı oluşturuldu (#{butce.id}).')
            return redirect('yonetim:butce_liste')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/butce_form.html')


def vergi_ayarlari(request):
    ayar = vergi_ayarlarini_getir()
    if request.method == 'POST':
        try:
            ayar.kdv_orani = _parse_decimal(request.POST.get('kdv_orani'), 'KDV Oranı')
            ayar.gelir_vergisi_orani = _parse_decimal_optional(request.POST.get('gelir_vergisi_orani'))
            ayar.kurumlar_vergisi_orani = _parse_decimal_optional(
                request.POST.get('kurumlar_vergisi_orani'),
                default=Decimal('25'),
            )
            ayar.stopaj_orani = _parse_decimal_optional(request.POST.get('stopaj_orani'))
            ayar.kdv_dahil = request.POST.get('kdv_dahil') == 'on'
            ayar.save()
            for butce in Butce.objects.all():
                butce_guncelle(butce)
            messages.success(request, 'Vergilendirme ayarları kaydedildi ve bütçe yeniden hesaplandı.')
            return redirect('yonetim:vergi_ayarlari')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/vergi_ayarlari.html', {'ayar': ayar})


def fis_liste(request):
    fisler = Fis.objects.select_related('butce').all()
    return render(request, 'yonetim/fis_liste.html', {'fisler': fisler})


def fis_ekle(request):
    butceler = Butce.objects.all()
    if request.method == 'POST':
        try:
            tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
            tarih = _parse_date(request.POST.get('tarih'), 'Tarih')
            kategori = request.POST.get('kategori', '').strip()
            if not kategori:
                raise ValueError('Kategori alanı zorunludur.')
            aciklama = request.POST.get('aciklama', '').strip()
            butce = _get_butce_or_none(request.POST.get('butce'))
            fis_gorseli = request.FILES.get('fis_gorseli')
            fis = Fis.objects.create(
                tutar=tutar,
                tarih=tarih,
                kategori=kategori,
                aciklama=aciklama,
                fis_gorseli=fis_gorseli,
                butce=butce,
            )
            _butceyi_yenile(butce)
            messages.success(request, f'Fiş kaydı oluşturuldu (#{fis.id}).')
            return redirect('yonetim:fis_liste')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/fis_form.html', {'butceler': butceler})


# ==========================================
# Yeni Modüller: Cari Hesap Yönetimi
# ==========================================

def cari_liste(request):
    cariler = CariHesap.objects.all()
    toplam_alacak = sum((c.guncel_bakiye for c in cariler if c.guncel_bakiye > 0), Decimal('0'))
    toplam_borc = sum((abs(c.guncel_bakiye) for c in cariler if c.guncel_bakiye < 0), Decimal('0'))
    return render(request, 'yonetim/cari_liste.html', {
        'cariler': cariler,
        'toplam_alacak': toplam_alacak,
        'toplam_borc': toplam_borc,
    })


def cari_ekle(request):
    if request.method == 'POST':
        try:
            unvan = request.POST.get('unvan', '').strip()
            if not unvan:
                raise ValueError('Ad / Unvan alanı zorunludur.')
            tur = request.POST.get('tur', CariHesap.TUR_MUSTERI)
            yetkili = request.POST.get('yetkili', '').strip()
            telefon = request.POST.get('telefon', '').strip()
            eposta = request.POST.get('eposta', '').strip()
            adres = request.POST.get('adres', '').strip()
            vergi_dairesi = request.POST.get('vergi_dairesi', '').strip()
            vergi_no = request.POST.get('vergi_no', '').strip()
            baslangic_bakiyesi = _parse_decimal_optional(request.POST.get('baslangic_bakiyesi'))

            cari = CariHesap.objects.create(
                unvan=unvan,
                tur=tur,
                yetkili=yetkili,
                telefon=telefon,
                eposta=eposta,
                adres=adres,
                vergi_dairesi=vergi_dairesi,
                vergi_no=vergi_no,
                baslangic_bakiyesi=baslangic_bakiyesi,
                guncel_bakiye=baslangic_bakiyesi,
            )
            messages.success(request, f'Cari hesap oluşturuldu: {cari.unvan}')
            return redirect('yonetim:cari_liste')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/cari_form.html', {
        'tur_secenekleri': CariHesap.TUR_SECENEKLERI,
    })


# ==========================================
# Yeni Modüller: Kasa / Banka Yönetimi
# ==========================================

def kasa_liste(request):
    kasalar = Kasa.objects.all()
    hareketler = KasaHareketi.objects.select_related('kasa', 'cari_hesap', 'isletme_gideri', 'fatura').all()[:50]
    toplam_kasa = sum((k.guncel_bakiye for k in kasalar), Decimal('0'))
    return render(request, 'yonetim/kasa_liste.html', {
        'kasalar': kasalar,
        'hareketler': hareketler,
        'toplam_kasa': toplam_kasa,
    })


def kasa_ekle(request):
    if request.method == 'POST':
        try:
            kasa_adi = request.POST.get('kasa_adi', '').strip()
            if not kasa_adi:
                raise ValueError('Kasa adı alanı zorunludur.')
            para_birimi = request.POST.get('para_birimi', 'TL').strip() or 'TL'
            aciklama = request.POST.get('aciklama', '').strip()
            baslangic_bakiyesi = _parse_decimal_optional(request.POST.get('baslangic_bakiyesi'))

            kasa = Kasa.objects.create(
                kasa_adi=kasa_adi,
                para_birimi=para_birimi,
                aciklama=aciklama,
                baslangic_bakiyesi=baslangic_bakiyesi,
                guncel_bakiye=baslangic_bakiyesi,
            )
            messages.success(request, f'Kasa/Hesap oluşturuldu: {kasa.kasa_adi}')
            return redirect('yonetim:kasa_liste')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/kasa_form.html')


def kasa_hareket_ekle(request):
    kasalar = Kasa.objects.all()
    cariler = CariHesap.objects.all()
    if request.method == 'POST':
        try:
            kasa_id = request.POST.get('kasa')
            if not kasa_id:
                raise ValueError('Kasa seçimi zorunludur.')
            kasa = get_object_or_404(Kasa, pk=kasa_id)
            islem_turu = request.POST.get('islem_turu')
            if islem_turu not in (KasaHareketi.ISLEM_GIRIS, KasaHareketi.ISLEM_CIKIS):
                raise ValueError('Geçerli bir işlem türü seçiniz.')
            tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
            tarih = _parse_date(request.POST.get('tarih'), 'Tarih')
            aciklama = request.POST.get('aciklama', '').strip()

            cari_id = request.POST.get('cari_hesap')
            cari = CariHesap.objects.filter(pk=cari_id).first() if cari_id else None

            kasa_hareketi_olustur(
                kasa=kasa,
                islem_turu=islem_turu,
                tutar=tutar,
                tarih=tarih,
                aciklama=aciklama,
                cari_hesap=cari,
            )
            messages.success(request, 'Kasa hareketi başarıyla işlendi ve bakiyeler güncellendi.')
            return redirect('yonetim:kasa_liste')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'yonetim/kasa_hareket_form.html', {
        'kasalar': kasalar,
        'cariler': cariler,
        'islem_secenekleri': KasaHareketi.ISLEM_SECENEKLERI,
        'bugun': timezone.now().date(),
    })


# ==========================================
# Yeni Modüller: İşletme Giderleri
# ==========================================

def gider_liste(request):
    giderler = IsletmeGideri.objects.select_related('kategori', 'kasa').all()
    kategoriler = GiderKategorisi.objects.all()
    toplam_gider = giderler.aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
    return render(request, 'yonetim/gider_liste.html', {
        'giderler': giderler,
        'kategoriler': kategoriler,
        'toplam_gider': toplam_gider,
    })


def gider_ekle(request):
    kategoriler = GiderKategorisi.objects.all()
    kasalar = Kasa.objects.all()
    ayar = vergi_ayarlarini_getir()

    if request.method == 'POST':
        # Yeni kategori hızlı oluşturma desteği
        yeni_kategori_adi = request.POST.get('yeni_kategori', '').strip()
        kategori_id = request.POST.get('kategori')
        try:
            if yeni_kategori_adi:
                kategori, _ = GiderKategorisi.objects.get_or_create(ad=yeni_kategori_adi)
            elif kategori_id:
                kategori = get_object_or_404(GiderKategorisi, pk=kategori_id)
            else:
                raise ValueError('Lütfen bir gider kategorisi seçin veya yeni oluşturun.')

            tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
            kdv_orani = _parse_decimal_optional(request.POST.get('kdv_orani'), default=ayar.kdv_orani)
            odeme_tarihi = _parse_date(request.POST.get('odeme_tarihi'), 'Ödeme Tarihi')
            aciklama = request.POST.get('aciklama', '').strip()
            belge = request.FILES.get('belge')

            kasa_id = request.POST.get('kasa')
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

            # Kasa seçildiyse kasadan otomatik çıkış hareketi oluşturulur
            if kasa:
                kasa_hareketi_olustur(
                    kasa=kasa,
                    islem_turu=KasaHareketi.ISLEM_CIKIS,
                    tutar=tutar,
                    tarih=odeme_tarihi,
                    aciklama=f'Gider Ödemesi: {kategori.ad} - {aciklama}'.strip(),
                    isletme_gideri=gider,
                )

            messages.success(request, f'İşletme gideri kaydedildi: {kategori.ad} ({tutar} TL)')
            return redirect('yonetim:gider_liste')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'yonetim/gider_form.html', {
        'kategoriler': kategoriler,
        'kasalar': kasalar,
        'varsayilan_kdv': ayar.kdv_orani,
        'bugun': timezone.now().date(),
    })


# ==========================================
# Yeni Modüller: Fatura Yönetimi
# ==========================================

def fatura_liste(request):
    faturalar = Fatura.objects.select_related('cari_hesap').all()
    toplam_gelen = faturalar.filter(tur=Fatura.TUR_GELEN).aggregate(t=Sum('toplam_tutar'))['t'] or Decimal('0')
    toplam_giden = faturalar.filter(tur=Fatura.TUR_GIDEN).aggregate(t=Sum('toplam_tutar'))['t'] or Decimal('0')
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
            fatura_no = request.POST.get('fatura_no', '').strip()
            if not fatura_no:
                raise ValueError('Fatura No alanı zorunludur.')
            tur = request.POST.get('tur', Fatura.TUR_GELEN)
            cari_id = request.POST.get('cari_hesap')
            if not cari_id:
                raise ValueError('Cari hesap seçimi zorunludur.')
            cari = get_object_or_404(CariHesap, pk=cari_id)

            tarih = _parse_date(request.POST.get('tarih'), 'Fatura Tarihi')
            vade_tarihi = request.POST.get('vade_tarihi') or None
            matrah = _parse_decimal(request.POST.get('matrah'), 'Matrah (KDV Hariç Tutar)')
            kdv_orani = _parse_decimal_optional(request.POST.get('kdv_orani'), default=ayar.kdv_orani)
            durum = request.POST.get('durum', Fatura.DURUM_BEKLIYOR)
            aciklama = request.POST.get('aciklama', '').strip()
            fatura_dosyasi = request.FILES.get('fatura_dosyasi')

            kdv_tutari, toplam_tutar = kdv_hesapla(matrah, kdv_orani)
            odenen_tutar = Decimal('0')
            if durum == Fatura.DURUM_ODENDI:
                odenen_tutar = toplam_tutar

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
                odenen_tutar=odenen_tutar,
                durum=durum,
                aciklama=aciklama,
                fatura_dosyasi=fatura_dosyasi,
            )

            # Ödendi olarak işaretlendiyse ve kasa seçilmişse kasa hareketi işlenir
            kasa_id = request.POST.get('kasa')
            if durum == Fatura.DURUM_ODENDI and kasa_id:
                kasa = Kasa.objects.filter(pk=kasa_id).first()
                if kasa:
                    islem = KasaHareketi.ISLEM_CIKIS if tur == Fatura.TUR_GELEN else KasaHareketi.ISLEM_GIRIS
                    kasa_hareketi_olustur(
                        kasa=kasa,
                        islem_turu=islem,
                        tutar=toplam_tutar,
                        tarih=tarih,
                        aciklama=f'Fatura Ödemesi: {fatura_no}'.strip(),
                        cari_hesap=cari,
                        fatura=fatura,
                    )

            cari_guncelle(cari)
            messages.success(request, f'Fatura kaydedildi: {fatura_no} ({toplam_tutar} TL)')
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


# ==========================================
# Yeni Modüller: Çek / Senet Takibi
# ==========================================

def ceksenet_liste(request):
    belgeler = CekSenet.objects.select_related('cari_hesap').all()
    toplam_alinan = belgeler.filter(yon=CekSenet.YON_ALINAN).aggregate(t=Sum('tutar'))['t'] or Decimal('0')
    toplam_verilen = belgeler.filter(yon=CekSenet.YON_VERILEN).aggregate(t=Sum('tutar'))['t'] or Decimal('0')
    return render(request, 'yonetim/ceksenet_liste.html', {
        'belgeler': belgeler,
        'toplam_alinan': toplam_alinan,
        'toplam_verilen': toplam_verilen,
    })


def ceksenet_ekle(request):
    cariler = CariHesap.objects.all()
    if request.method == 'POST':
        try:
            tur = request.POST.get('tur', CekSenet.TUR_CEK)
            yon = request.POST.get('yon', CekSenet.YON_ALINAN)
            portfoy_no = request.POST.get('portfoy_no', '').strip()
            if not portfoy_no:
                raise ValueError('Portföy / Seri No zorunludur.')
            cari_id = request.POST.get('cari_hesap')
            if not cari_id:
                raise ValueError('Cari hesap seçimi zorunludur.')
            cari = get_object_or_404(CariHesap, pk=cari_id)

            tutar = _parse_decimal(request.POST.get('tutar'), 'Tutar')
            vade_tarihi = _parse_date(request.POST.get('vade_tarihi'), 'Vade Tarihi')
            keside_tarihi = _parse_date(request.POST.get('keside_tarihi'), 'Keşide Tarihi')
            banka_sube = request.POST.get('banka_sube', '').strip()
            durum = request.POST.get('durum', CekSenet.DURUM_PORTFOY)
            aciklama = request.POST.get('aciklama', '').strip()

            belge = CekSenet.objects.create(
                tur=tur,
                yon=yon,
                portfoy_no=portfoy_no,
                cari_hesap=cari,
                tutar=tutar,
                vade_tarihi=vade_tarihi,
                keside_tarihi=keside_tarihi,
                banka_sube=banka_sube,
                durum=durum,
                aciklama=aciklama,
            )
            cari_guncelle(cari)
            messages.success(request, f'{belge.get_tur_display()} kaydı eklendi (#{belge.portfoy_no}).')
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
