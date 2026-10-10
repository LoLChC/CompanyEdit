from decimal import Decimal

from yonetim.models import CariHesap, CekSenet, Fatura, Kasa, KasaHareketi

SIFIR = Decimal('0.00')


def _q(tutar):
    if tutar is None:
        return SIFIR
    return Decimal(str(tutar)).quantize(Decimal('0.01'))


def kdv_hesapla(matrah, kdv_orani):
    matrah = _q(matrah)
    kdv_orani = _q(kdv_orani)
    kdv_tutari = (matrah * kdv_orani / Decimal('100')).quantize(Decimal('0.01'))
    toplam = (matrah + kdv_tutari).quantize(Decimal('0.01'))
    return kdv_tutari, toplam


def cari_guncelle(cari):
    if cari is None:
        return None

    bakiye = _q(cari.baslangic_bakiyesi)

    from yonetim.models import Fis

    is_tedarikci = (cari.tur == CariHesap.TUR_TEDARIKCI)

    # Ürün Satışlarında/Alışlarında (Fişler)
    for fis in Fis.objects.filter(cari_hesap=cari):
        if fis.fis_turu == Fis.FIS_SATIS:
            # Satış fişi
            if is_tedarikci:
                bakiye -= _q(fis.tutar)
            else:
                bakiye += _q(fis.tutar)
        else:
            # Alış fişi
            if is_tedarikci:
                bakiye += _q(fis.tutar)
            else:
                bakiye -= _q(fis.tutar)

    # Faturalar
    for fatura in Fatura.objects.filter(cari_hesap=cari):
        if fatura.tur == Fatura.TUR_GIDEN:
            # Giden (Satış)
            if is_tedarikci:
                bakiye -= _q(fatura.toplam_tutar)
            else:
                bakiye += _q(fatura.toplam_tutar)
        else:
            # Gelen (Alış)
            if is_tedarikci:
                bakiye += _q(fatura.toplam_tutar)
            else:
                bakiye -= _q(fatura.toplam_tutar)

    # Kasa/Para Hareketleri (Tahsilatlar / Ödemeler)
    for hareket in KasaHareketi.objects.filter(cari_hesap=cari, isletme_gideri__isnull=True):
        if hareket.islem_turu == KasaHareketi.ISLEM_GIRIS:
            # Tahsilat (Bize giren para)
            if is_tedarikci:
                bakiye += _q(hareket.tutar)
            else:
                bakiye -= _q(hareket.tutar)
        else:
            # Ödeme (Bizden çıkan para)
            if is_tedarikci:
                bakiye -= _q(hareket.tutar)
            else:
                bakiye += _q(hareket.tutar)

    # Çek / Senetler
    for belge in CekSenet.objects.filter(cari_hesap=cari).exclude(durum=CekSenet.DURUM_KARSILIKSIZ):
        if belge.yon == CekSenet.YON_ALINAN:
            # Müşteriden/Tedarikçiden alınan evrak (Tahsilat)
            if is_tedarikci:
                bakiye += _q(belge.tutar)
            else:
                bakiye -= _q(belge.tutar)
        else:
            # Bizim verdiğimiz evrak (Ödeme)
            if is_tedarikci:
                bakiye -= _q(belge.tutar)
            else:
                bakiye += _q(belge.tutar)

    cari.guncel_bakiye = _q(bakiye)
    cari.save(update_fields=['guncel_bakiye'])
    return cari.guncel_bakiye


def kasa_guncelle(kasa):
    if kasa is None:
        return None

    bakiye = _q(kasa.baslangic_bakiyesi)
    for hareket in KasaHareketi.objects.filter(kasa=kasa):
        if hareket.islem_turu == KasaHareketi.ISLEM_GIRIS:
            bakiye += _q(hareket.tutar)
        else:
            bakiye -= _q(hareket.tutar)

    kasa.guncel_bakiye = _q(bakiye)
    kasa.save(update_fields=['guncel_bakiye'])
    return kasa.guncel_bakiye


def kasa_hareketi_olustur(
    kasa,
    islem_turu,
    tutar,
    tarih,
    aciklama='',
    cari_hesap=None,
    isletme_gideri=None,
    fatura=None,
):
    if kasa is None or tutar is None or Decimal(str(tutar)) <= SIFIR:
        return None

    hareket = KasaHareketi.objects.create(
        kasa=kasa,
        islem_turu=islem_turu,
        tutar=_q(tutar),
        tarih=tarih,
        aciklama=aciklama,
        cari_hesap=cari_hesap,
        isletme_gideri=isletme_gideri,
        fatura=fatura,
    )
    kasa_guncelle(kasa)
    if cari_hesap is not None:
        cari_guncelle(cari_hesap)
    return hareket


def tum_kasalari_guncelle():
    for kasa in Kasa.objects.all():
        kasa_guncelle(kasa)


def tum_carileri_guncelle():
    for cari in CariHesap.objects.all():
        cari_guncelle(cari)
