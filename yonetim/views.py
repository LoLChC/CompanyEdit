from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Alacak, Butce, Fis, HaftalikPlan, Odeme, Stok, VergiAyarlari
from .services.butce_hesapla import butce_guncelle, butce_ozetini_hesapla, vergi_ayarlarini_getir


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
            if not urun_adi:
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
