from django.db import models
from django.utils import timezone


class VergiAyarlari(models.Model):
    kdv_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='KDV Oranı (%)',
        default=20,
    )
    gelir_vergisi_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Gelir Vergisi Oranı (%)',
        default=0,
    )
    kurumlar_vergisi_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Kurumlar Vergisi Oranı (%)',
        default=25,
    )
    stopaj_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Stopaj Oranı (%)',
        default=0,
    )
    kdv_dahil = models.BooleanField(
        verbose_name='Tutarlar KDV Dahil',
        default=True,
        help_text='İşaretliyse girilen tutarlar KDV dahil kabul edilir.',
    )
    guncelleme_tarihi = models.DateTimeField(
        verbose_name='Son Güncelleme',
        auto_now=True,
    )

    class Meta:
        verbose_name = 'Vergi Ayarı'
        verbose_name_plural = 'Vergi Ayarları'

    def __str__(self):
        return f'Vergilendirme (KDV %{self.kdv_orani})'


class Butce(models.Model):
    baslangic_butcesi = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Başlangıç Bütçesi',
    )
    guncel_butce = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Güncel Bütçe',
        default=0,
    )
    son_islem_tarihi = models.DateField(
        verbose_name='Son İşlem Tarihi',
        default=timezone.now,
    )
    aciklama = models.CharField(
        max_length=255,
        verbose_name='Açıklama',
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = 'Bütçe'
        verbose_name_plural = 'Bütçeler'
        ordering = ['-son_islem_tarihi']

    def __str__(self):
        return f'Bütçe: {self.guncel_butce} TL ({self.son_islem_tarihi})'


class Odeme(models.Model):
    DURUM_ODENDI = 'odendi'
    DURUM_BEKLIYOR = 'bekliyor'
    DURUM_SECENEKLERI = [
        (DURUM_ODENDI, 'Ödendi'),
        (DURUM_BEKLIYOR, 'Bekliyor'),
    ]

    tutar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Tutar (TL)',
    )
    islem_tarihi = models.DateField(
        verbose_name='İşlem Tarihi',
        default=timezone.now,
        help_text='Ödeme kaydının oluşturulduğu / işlemin yapıldığı tarih',
    )
    vade_tarihi = models.DateField(
        verbose_name='Ödeme Tarihi',
        help_text='Paranın ne zaman ödeneceği',
    )
    kime = models.CharField(
        max_length=200,
        verbose_name='Kime',
    )
    aciklama = models.TextField(
        verbose_name='Açıklama',
        blank=True,
        default='',
    )
    durum = models.CharField(
        max_length=20,
        choices=DURUM_SECENEKLERI,
        default=DURUM_BEKLIYOR,
        verbose_name='Durum',
    )
    butce = models.ForeignKey(
        Butce,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='odemeler',
        verbose_name='İlgili Bütçe',
    )

    class Meta:
        verbose_name = 'Ödeme'
        verbose_name_plural = 'Ödemeler'
        ordering = ['-islem_tarihi', '-id']

    def __str__(self):
        return f'{self.kime} - {self.tutar} TL'


class Alacak(models.Model):
    DURUM_TAHSIL = 'tahsil_edildi'
    DURUM_BEKLIYOR = 'bekliyor'
    DURUM_SECENEKLERI = [
        (DURUM_TAHSIL, 'Tahsil Edildi'),
        (DURUM_BEKLIYOR, 'Bekliyor'),
    ]

    tutar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Tutar (TL)',
    )
    islem_tarihi = models.DateField(
        verbose_name='İşlem Tarihi',
        default=timezone.now,
        help_text='Alacağın oluştuğu / kaydedildiği tarih',
    )
    tahsil_tarihi = models.DateField(
        verbose_name='Tahsil Tarihi',
        help_text='Paranın ne zaman alınacağı',
    )
    kimden = models.CharField(
        max_length=200,
        verbose_name='Kimden',
    )
    aciklama = models.TextField(
        verbose_name='Açıklama',
        blank=True,
        default='',
    )
    durum = models.CharField(
        max_length=20,
        choices=DURUM_SECENEKLERI,
        default=DURUM_BEKLIYOR,
        verbose_name='Durum',
    )
    butce = models.ForeignKey(
        Butce,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alacaklar',
        verbose_name='İlgili Bütçe',
    )

    class Meta:
        verbose_name = 'Alacak'
        verbose_name_plural = 'Alacaklar'
        ordering = ['-islem_tarihi', '-id']

    def __str__(self):
        return f'{self.kimden} - {self.tutar} TL'


class HaftalikPlan(models.Model):
    DURUM_TAMAMLANDI = 'tamamlandi'
    DURUM_BEKLIYOR = 'bekliyor'
    DURUM_SECENEKLERI = [
        (DURUM_TAMAMLANDI, 'Tamamlandı'),
        (DURUM_BEKLIYOR, 'Bekliyor'),
    ]

    baslik = models.CharField(
        max_length=200,
        verbose_name='Başlık',
    )
    detay = models.TextField(
        verbose_name='Detay',
        blank=True,
        default='',
    )
    baslangic_tarihi = models.DateField(
        verbose_name='Başlangıç Tarihi',
    )
    bitis_tarihi = models.DateField(
        verbose_name='Bitiş Tarihi',
    )
    durum = models.CharField(
        max_length=20,
        choices=DURUM_SECENEKLERI,
        default=DURUM_BEKLIYOR,
        verbose_name='Durum',
    )

    class Meta:
        verbose_name = 'Haftalık Plan'
        verbose_name_plural = 'Haftalık Planlar'
        ordering = ['-baslangic_tarihi']

    def __str__(self):
        return self.baslik


class Stok(models.Model):
    urun_adi = models.CharField(
        max_length=200,
        verbose_name='Ürün Adı',
    )
    adet_miktar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Adet / Miktar',
    )
    birim = models.CharField(
        max_length=50,
        verbose_name='Birim',
        default='Adet',
    )
    alis_fiyati = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Alış Fiyatı (TL)',
        default=0,
    )
    alim_tarihi = models.DateField(
        verbose_name='Alım Tarihi',
        default=timezone.now,
    )
    son_guncelleme = models.DateTimeField(
        verbose_name='Son Güncelleme',
        auto_now=True,
    )

    class Meta:
        verbose_name = 'Stok'
        verbose_name_plural = 'Stoklar'
        ordering = ['urun_adi']

    def __str__(self):
        return f'{self.urun_adi} ({self.adet_miktar} {self.birim})'

    @property
    def toplam_maliyet(self):
        return self.adet_miktar * self.alis_fiyati


class Fis(models.Model):
    tutar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Tutar',
    )
    tarih = models.DateField(
        verbose_name='Tarih',
        default=timezone.now,
    )
    kategori = models.CharField(
        max_length=100,
        verbose_name='Kategori',
    )
    aciklama = models.TextField(
        verbose_name='Açıklama',
        blank=True,
        default='',
    )
    fis_gorseli = models.ImageField(
        upload_to='fisler/%Y/%m/',
        verbose_name='Fiş Görseli',
        blank=True,
        null=True,
    )
    butce = models.ForeignKey(
        Butce,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fisler',
        verbose_name='İlgili Bütçe',
    )

    class Meta:
        verbose_name = 'Fiş'
        verbose_name_plural = 'Fişler'
        ordering = ['-tarih', '-id']

    def __str__(self):
        return f'{self.kategori} - {self.tutar} TL'
