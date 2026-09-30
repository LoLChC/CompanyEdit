from decimal import Decimal
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


class CariHesap(models.Model):
    TUR_MUSTERI = 'musteri'
    TUR_TEDARIKCI = 'tedarikci'
    TUR_DIGER = 'diger'
    TUR_SECENEKLERI = [
        (TUR_MUSTERI, 'Müşteri'),
        (TUR_TEDARIKCI, 'Tedarikçi'),
        (TUR_DIGER, 'Diğer Cari'),
    ]

    unvan = models.CharField(
        max_length=255,
        verbose_name='Ad / Unvan',
    )
    tur = models.CharField(
        max_length=20,
        choices=TUR_SECENEKLERI,
        default=TUR_MUSTERI,
        verbose_name='Cari Türü',
    )
    yetkili = models.CharField(
        max_length=150,
        verbose_name='Yetkili Kişi',
        blank=True,
        default='',
    )
    telefon = models.CharField(
        max_length=50,
        verbose_name='Telefon',
        blank=True,
        default='',
    )
    eposta = models.EmailField(
        max_length=150,
        verbose_name='E-posta',
        blank=True,
        default='',
    )
    adres = models.TextField(
        verbose_name='Adres',
        blank=True,
        default='',
    )
    vergi_dairesi = models.CharField(
        max_length=100,
        verbose_name='Vergi Dairesi',
        blank=True,
        default='',
    )
    vergi_no = models.CharField(
        max_length=50,
        verbose_name='Vergi No / TC Kimlik No',
        blank=True,
        default='',
    )
    baslangic_bakiyesi = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Başlangıç Bakiyesi (TL)',
        help_text='Pozitif ise bizden alacaklı, negatif ise bize borçludur.',
    )
    guncel_bakiye = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Güncel Bakiye (TL)',
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturma Tarihi',
    )

    class Meta:
        verbose_name = 'Cari Hesap'
        verbose_name_plural = 'Cari Hesaplar'
        ordering = ['unvan']

    def __str__(self):
        return f'{self.unvan} ({self.get_tur_display()})'

    @property
    def bakiye_durumu(self):
        if self.guncel_bakiye > Decimal('0.00'):
            return 'Alacaklı (Biz Borçluyuz)'
        elif self.guncel_bakiye < Decimal('0.00'):
            return 'Borçlu (Biz Alacaklıyız)'
        return 'Bakiye Sıfır'


class Kasa(models.Model):
    kasa_adi = models.CharField(
        max_length=150,
        verbose_name='Kasa / Hesap Adı',
        help_text='Örn: Merkez Nakit Kasa, Ziraat Bankası Vadesiz vb.',
    )
    para_birimi = models.CharField(
        max_length=10,
        default='TL',
        verbose_name='Para Birimi',
    )
    aciklama = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Açıklama',
    )
    baslangic_bakiyesi = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Başlangıç Bakiyesi',
    )
    guncel_bakiye = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Güncel Bakiye',
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturma Tarihi',
    )

    class Meta:
        verbose_name = 'Kasa / Banka'
        verbose_name_plural = 'Kasalar & Bankalar'
        ordering = ['kasa_adi']

    def __str__(self):
        return f'{self.kasa_adi} ({self.guncel_bakiye} {self.para_birimi})'


class GiderKategorisi(models.Model):
    ad = models.CharField(
        max_length=100,
        verbose_name='Kategori Adı',
        unique=True,
    )
    aciklama = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Açıklama',
    )

    class Meta:
        verbose_name = 'Gider Kategorisi'
        verbose_name_plural = 'Gider Kategorileri'
        ordering = ['ad']

    def __str__(self):
        return self.ad


class IsletmeGideri(models.Model):
    kategori = models.ForeignKey(
        GiderKategorisi,
        on_delete=models.PROTECT,
        related_name='giderler',
        verbose_name='Gider Kategorisi',
    )
    tutar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Tutar (TL)',
    )
    kdv_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        verbose_name='KDV Oranı (%)',
    )
    odeme_tarihi = models.DateField(
        default=timezone.now,
        verbose_name='Ödeme Tarihi',
    )
    kasa = models.ForeignKey(
        Kasa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='giderler',
        verbose_name='Ödenen Kasa / Banka',
    )
    aciklama = models.TextField(
        blank=True,
        default='',
        verbose_name='Açıklama',
    )
    belge = models.FileField(
        upload_to='giderler/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Belge / Fiş Görseli',
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Kayıt Tarihi',
    )

    class Meta:
        verbose_name = 'İşletme Gideri'
        verbose_name_plural = 'İşletme Giderleri'
        ordering = ['-odeme_tarihi', '-id']

    def __str__(self):
        return f'{self.kategori.ad} - {self.tutar} TL ({self.odeme_tarihi})'


class Fatura(models.Model):
    TUR_GELEN = 'gelen'
    TUR_GIDEN = 'giden'
    TUR_SECENEKLERI = [
        (TUR_GELEN, 'Gelen Fatura (Alış / Gider)'),
        (TUR_GIDEN, 'Giden Fatura (Satış / Gelir)'),
    ]

    DURUM_BEKLIYOR = 'bekliyor'
    DURUM_ODENDI = 'odendi'
    DURUM_KISMI = 'kismi_odendi'
    DURUM_SECENEKLERI = [
        (DURUM_BEKLIYOR, 'Bekliyor'),
        (DURUM_KISMI, 'Kısmi Ödendi'),
        (DURUM_ODENDI, 'Ödendi'),
    ]

    fatura_no = models.CharField(
        max_length=60,
        verbose_name='Fatura No',
    )
    tur = models.CharField(
        max_length=10,
        choices=TUR_SECENEKLERI,
        verbose_name='Fatura Türü',
    )
    cari_hesap = models.ForeignKey(
        CariHesap,
        on_delete=models.PROTECT,
        related_name='faturalar',
        verbose_name='Cari Hesap',
    )
    tarih = models.DateField(
        default=timezone.now,
        verbose_name='Fatura Tarihi',
    )
    vade_tarihi = models.DateField(
        null=True,
        blank=True,
        verbose_name='Vade Tarihi',
    )
    matrah = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Matrah (KDV Hariç Tutar)',
    )
    kdv_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        verbose_name='KDV Oranı (%)',
    )
    kdv_tutari = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='KDV Tutarı',
    )
    toplam_tutar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Toplam Tutar',
    )
    odenen_tutar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Ödenen Tutar',
    )
    durum = models.CharField(
        max_length=20,
        choices=DURUM_SECENEKLERI,
        default=DURUM_BEKLIYOR,
        verbose_name='Durum',
    )
    aciklama = models.TextField(
        blank=True,
        default='',
        verbose_name='Açıklama',
    )
    fatura_dosyasi = models.FileField(
        upload_to='faturalar/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Fatura Dosyası / PDF',
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturma Tarihi',
    )

    class Meta:
        verbose_name = 'Fatura'
        verbose_name_plural = 'Faturalar'
        ordering = ['-tarih', '-id']

    def __str__(self):
        return f'{self.fatura_no} - {self.cari_hesap.unvan} ({self.toplam_tutar} TL)'


class KasaHareketi(models.Model):
    ISLEM_GIRIS = 'giris'
    ISLEM_CIKIS = 'cikis'
    ISLEM_SECENEKLERI = [
        (ISLEM_GIRIS, 'Giriş (Tahsilat / Gelir)'),
        (ISLEM_CIKIS, 'Çıkış (Ödeme / Gider)'),
    ]

    kasa = models.ForeignKey(
        Kasa,
        on_delete=models.CASCADE,
        related_name='hareketler',
        verbose_name='İlgili Kasa / Banka',
    )
    islem_turu = models.CharField(
        max_length=10,
        choices=ISLEM_SECENEKLERI,
        verbose_name='İşlem Türü',
    )
    tutar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Tutar (TL)',
    )
    tarih = models.DateField(
        default=timezone.now,
        verbose_name='İşlem Tarihi',
    )
    aciklama = models.TextField(
        blank=True,
        default='',
        verbose_name='Açıklama',
    )
    cari_hesap = models.ForeignKey(
        CariHesap,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kasa_hareketleri',
        verbose_name='İlişkili Cari Hesap',
    )
    isletme_gideri = models.ForeignKey(
        IsletmeGideri,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kasa_hareketleri',
        verbose_name='İlişkili İşletme Gideri',
    )
    fatura = models.ForeignKey(
        Fatura,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kasa_hareketleri',
        verbose_name='İlişkili Fatura',
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Kayıt Tarihi',
    )

    class Meta:
        verbose_name = 'Kasa Hareketi'
        verbose_name_plural = 'Kasa Hareketleri'
        ordering = ['-tarih', '-id']

    def __str__(self):
        return f'{self.kasa.kasa_adi} - {self.get_islem_turu_display()} - {self.tutar} TL'


class CekSenet(models.Model):
    TUR_CEK = 'cek'
    TUR_SENET = 'senet'
    TUR_SECENEKLERI = [
        (TUR_CEK, 'Çek'),
        (TUR_SENET, 'Senet'),
    ]

    YON_ALINAN = 'alinan'
    YON_VERILEN = 'verilen'
    YON_SECENEKLERI = [
        (YON_ALINAN, 'Alınan (Müşteri Evrağı)'),
        (YON_VERILEN, 'Verilen (Kendi Evrağımız)'),
    ]

    DURUM_PORTFOY = 'portfoyde'
    DURUM_TAHSIL = 'tahsil_edildi'
    DURUM_CIRO = 'ciro_edildi'
    DURUM_KARSILIKSIZ = 'karsiliksiz_protestolu'
    DURUM_SECENEKLERI = [
        (DURUM_PORTFOY, 'Portföyde'),
        (DURUM_TAHSIL, 'Tahsil Edildi / Ödendi'),
        (DURUM_CIRO, 'Ciro Edildi'),
        (DURUM_KARSILIKSIZ, 'Karşılıksız / Protestolu'),
    ]

    tur = models.CharField(
        max_length=10,
        choices=TUR_SECENEKLERI,
        default=TUR_CEK,
        verbose_name='Evrak Türü',
    )
    yon = models.CharField(
        max_length=10,
        choices=YON_SECENEKLERI,
        default=YON_ALINAN,
        verbose_name='Yönü',
    )
    portfoy_no = models.CharField(
        max_length=50,
        verbose_name='Portföy / Seri No',
    )
    cari_hesap = models.ForeignKey(
        CariHesap,
        on_delete=models.PROTECT,
        related_name='cek_senetler',
        verbose_name='İlgili Cari Hesap',
    )
    tutar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Tutar (TL)',
    )
    vade_tarihi = models.DateField(
        verbose_name='Vade Tarihi',
    )
    keside_tarihi = models.DateField(
        default=timezone.now,
        verbose_name='Keşide / Düzenleme Tarihi',
    )
    banka_sube = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name='Banka / Şube Bilgisi',
    )
    durum = models.CharField(
        max_length=30,
        choices=DURUM_SECENEKLERI,
        default=DURUM_PORTFOY,
        verbose_name='Durum',
    )
    aciklama = models.TextField(
        blank=True,
        default='',
        verbose_name='Açıklama',
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturma Tarihi',
    )

    class Meta:
        verbose_name = 'Çek / Senet'
        verbose_name_plural = 'Çekler & Senetler'
        ordering = ['vade_tarihi', '-id']

    def __str__(self):
        return f'{self.get_tur_display()} ({self.portfoy_no}) - {self.tutar} TL - {self.cari_hesap.unvan}'
