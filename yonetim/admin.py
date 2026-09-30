from django.contrib import admin

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


@admin.register(VergiAyarlari)
class VergiAyarlariAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'kdv_orani',
        'gelir_vergisi_orani',
        'kurumlar_vergisi_orani',
        'stopaj_orani',
        'kdv_dahil',
        'guncelleme_tarihi',
    )


@admin.register(Butce)
class ButceAdmin(admin.ModelAdmin):
    list_display = ('id', 'baslangic_butcesi', 'guncel_butce', 'son_islem_tarihi', 'aciklama')
    search_fields = ('aciklama',)


@admin.register(Odeme)
class OdemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tutar', 'islem_tarihi', 'vade_tarihi', 'kime', 'durum', 'butce')
    list_filter = ('durum', 'islem_tarihi')
    search_fields = ('kime', 'aciklama')


@admin.register(Alacak)
class AlacakAdmin(admin.ModelAdmin):
    list_display = ('id', 'tutar', 'islem_tarihi', 'tahsil_tarihi', 'kimden', 'durum', 'butce')
    list_filter = ('durum', 'islem_tarihi')
    search_fields = ('kimden', 'aciklama')


@admin.register(HaftalikPlan)
class HaftalikPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'baslik', 'baslangic_tarihi', 'bitis_tarihi', 'durum')
    list_filter = ('durum',)


@admin.register(Stok)
class StokAdmin(admin.ModelAdmin):
    list_display = ('id', 'urun_adi', 'adet_miktar', 'birim', 'alis_fiyati', 'alim_tarihi', 'son_guncelleme')
    search_fields = ('urun_adi',)


@admin.register(Fis)
class FisAdmin(admin.ModelAdmin):
    list_display = ('id', 'tutar', 'tarih', 'kategori', 'butce')
    list_filter = ('tarih', 'kategori')
    search_fields = ('kategori', 'aciklama')


@admin.register(CariHesap)
class CariHesapAdmin(admin.ModelAdmin):
    list_display = ('id', 'unvan', 'tur', 'yetkili', 'telefon', 'guncel_bakiye')
    list_filter = ('tur',)
    search_fields = ('unvan', 'yetkili', 'vergi_no')


@admin.register(Kasa)
class KasaAdmin(admin.ModelAdmin):
    list_display = ('id', 'kasa_adi', 'para_birimi', 'guncel_bakiye')
    search_fields = ('kasa_adi',)


@admin.register(GiderKategorisi)
class GiderKategorisiAdmin(admin.ModelAdmin):
    list_display = ('id', 'ad', 'aciklama')
    search_fields = ('ad',)


@admin.register(IsletmeGideri)
class IsletmeGideriAdmin(admin.ModelAdmin):
    list_display = ('id', 'kategori', 'tutar', 'kdv_orani', 'odeme_tarihi', 'kasa')
    list_filter = ('kategori', 'odeme_tarihi')
    search_fields = ('kategori__ad', 'aciklama')


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fatura_no', 'tur', 'cari_hesap', 'tarih', 'toplam_tutar', 'durum')
    list_filter = ('tur', 'durum', 'tarih')
    search_fields = ('fatura_no', 'cari_hesap__unvan')


@admin.register(KasaHareketi)
class KasaHareketiAdmin(admin.ModelAdmin):
    list_display = ('id', 'kasa', 'islem_turu', 'tutar', 'tarih', 'cari_hesap')
    list_filter = ('islem_turu', 'tarih')
    search_fields = ('kasa__kasa_adi', 'aciklama')


@admin.register(CekSenet)
class CekSenetAdmin(admin.ModelAdmin):
    list_display = ('id', 'tur', 'yon', 'portfoy_no', 'cari_hesap', 'tutar', 'vade_tarihi', 'durum')
    list_filter = ('tur', 'yon', 'durum', 'vade_tarihi')
    search_fields = ('portfoy_no', 'cari_hesap__unvan', 'banka_sube')
