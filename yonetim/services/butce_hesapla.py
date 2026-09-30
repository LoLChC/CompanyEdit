from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from yonetim.models import Alacak, Butce, Fis, Odeme, VergiAyarlari

SIFIR = Decimal('0.00')


def _toplam(queryset, alan='tutar'):
    sonuc = queryset.aggregate(toplam=Sum(alan))['toplam']
    return sonuc if sonuc is not None else SIFIR


def _kdv_ayir(tutar, kdv_orani, kdv_dahil):
    if tutar <= SIFIR or kdv_orani <= SIFIR:
        return tutar, SIFIR
    oran = kdv_orani / Decimal('100')
    if kdv_dahil:
        net = tutar / (Decimal('1') + oran)
        kdv = tutar - net
        return net.quantize(Decimal('0.01')), kdv.quantize(Decimal('0.01'))
    kdv = tutar * oran
    return tutar, kdv.quantize(Decimal('0.01'))


def vergi_ayarlarini_getir():
    ayar, _ = VergiAyarlari.objects.get_or_create(
        pk=1,
        defaults={
            'kdv_orani': Decimal('20.00'),
            'gelir_vergisi_orani': Decimal('0.00'),
            'kurumlar_vergisi_orani': Decimal('25.00'),
            'stopaj_orani': Decimal('0.00'),
            'kdv_dahil': True,
        },
    )
    return ayar


def butce_ozetini_hesapla(butce=None):
    ayar = vergi_ayarlarini_getir()

    if butce is not None:
        alacak_qs = Alacak.objects.filter(butce=butce)
        odeme_qs = Odeme.objects.filter(butce=butce)
        fis_qs = Fis.objects.filter(butce=butce)
        baslangic = butce.baslangic_butcesi
    else:
        alacak_qs = Alacak.objects.all()
        odeme_qs = Odeme.objects.all()
        fis_qs = Fis.objects.all()
        aktif = Butce.objects.order_by('-id').first()
        baslangic = aktif.baslangic_butcesi if aktif else SIFIR

    tahsil_alacaklar = alacak_qs.filter(durum=Alacak.DURUM_TAHSIL)
    bekleyen_alacaklar = alacak_qs.filter(durum=Alacak.DURUM_BEKLIYOR)
    odenen_odemeler = odeme_qs.filter(durum=Odeme.DURUM_ODENDI)
    bekleyen_odemeler = odeme_qs.filter(durum=Odeme.DURUM_BEKLIYOR)

    brut_gelen = _toplam(tahsil_alacaklar)
    brut_giden = _toplam(odenen_odemeler)
    brut_fis = _toplam(fis_qs)
    bekleyen_gelen = _toplam(bekleyen_alacaklar)
    bekleyen_giden = _toplam(bekleyen_odemeler)

    net_gelen, kdv_gelen = _kdv_ayir(brut_gelen, ayar.kdv_orani, ayar.kdv_dahil)
    net_giden, kdv_giden = _kdv_ayir(brut_giden, ayar.kdv_orani, ayar.kdv_dahil)
    net_fis, kdv_fis = _kdv_ayir(brut_fis, ayar.kdv_orani, ayar.kdv_dahil)

    kdv_farki = kdv_gelen - kdv_giden - kdv_fis
    if kdv_farki < SIFIR:
        kdv_odenecek = abs(kdv_farki)
        kdv_iadesi = SIFIR
    else:
        kdv_odenecek = SIFIR
        kdv_iadesi = kdv_farki

    kar_zarar = net_gelen - net_giden - net_fis
    if kar_zarar > SIFIR:
        gelir_vergisi = (kar_zarar * ayar.gelir_vergisi_orani / Decimal('100')).quantize(Decimal('0.01'))
        kurumlar_vergisi = (kar_zarar * ayar.kurumlar_vergisi_orani / Decimal('100')).quantize(Decimal('0.01'))
    else:
        gelir_vergisi = SIFIR
        kurumlar_vergisi = SIFIR

    stopaj = (brut_gelen * ayar.stopaj_orani / Decimal('100')).quantize(Decimal('0.01'))
    toplam_vergi = kdv_odenecek + gelir_vergisi + kurumlar_vergisi + stopaj

    guncel_butce = baslangic + brut_gelen - brut_giden - brut_fis - toplam_vergi

    return {
        'baslangic_butcesi': baslangic,
        'brut_gelen': brut_gelen,
        'brut_giden': brut_giden,
        'brut_fis': brut_fis,
        'bekleyen_gelen': bekleyen_gelen,
        'bekleyen_giden': bekleyen_giden,
        'net_gelen': net_gelen,
        'net_giden': net_giden,
        'net_fis': net_fis,
        'kdv_gelen': kdv_gelen,
        'kdv_giden': kdv_giden,
        'kdv_fis': kdv_fis,
        'kdv_odenecek': kdv_odenecek,
        'kdv_iadesi': kdv_iadesi,
        'gelir_vergisi': gelir_vergisi,
        'kurumlar_vergisi': kurumlar_vergisi,
        'stopaj': stopaj,
        'toplam_vergi': toplam_vergi,
        'kar_zarar': kar_zarar,
        'guncel_butce': guncel_butce.quantize(Decimal('0.01')),
        'vergi_ayarlari': ayar,
    }


def butce_guncelle(butce):
    ozet = butce_ozetini_hesapla(butce)
    butce.guncel_butce = ozet['guncel_butce']
    butce.son_islem_tarihi = timezone.now().date()
    butce.save(update_fields=['guncel_butce', 'son_islem_tarihi'])
    return ozet
