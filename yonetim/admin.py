from django.contrib import admin

from .models import Alacak, Butce, Fis, HaftalikPlan, Odeme, Stok, VergiAyarlari


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
