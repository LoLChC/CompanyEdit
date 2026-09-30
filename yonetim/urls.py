from django.urls import path

from . import views

app_name = 'yonetim'

urlpatterns = [
    path('', views.ana_sayfa, name='ana_sayfa'),

    path('odemeler/', views.odeme_liste, name='odeme_liste'),
    path('odemeler/yeni/', views.odeme_ekle, name='odeme_ekle'),

    path('alacaklar/', views.alacak_liste, name='alacak_liste'),
    path('alacaklar/yeni/', views.alacak_ekle, name='alacak_ekle'),

    path('planlar/', views.haftalik_plan_liste, name='haftalik_plan_liste'),
    path('planlar/yeni/', views.haftalik_plan_ekle, name='haftalik_plan_ekle'),

    path('stoklar/', views.stok_liste, name='stok_liste'),
    path('stoklar/yeni/', views.stok_ekle, name='stok_ekle'),

    path('butce/', views.butce_liste, name='butce_liste'),
    path('butce/yeni/', views.butce_ekle, name='butce_ekle'),

    path('vergilendirme/', views.vergi_ayarlari, name='vergi_ayarlari'),

    path('fisler/', views.fis_liste, name='fis_liste'),
    path('fisler/yeni/', views.fis_ekle, name='fis_ekle'),

    # Cari Hesaplar
    path('cariler/', views.cari_liste, name='cari_liste'),
    path('cariler/yeni/', views.cari_ekle, name='cari_ekle'),

    # Kasa ve Banka
    path('kasalar/', views.kasa_liste, name='kasa_liste'),
    path('kasalar/yeni/', views.kasa_ekle, name='kasa_ekle'),
    path('kasalar/hareket-ekle/', views.kasa_hareket_ekle, name='kasa_hareket_ekle'),

    # İşletme Giderleri
    path('giderler/', views.gider_liste, name='gider_liste'),
    path('giderler/yeni/', views.gider_ekle, name='gider_ekle'),

    # Faturalar
    path('faturalar/', views.fatura_liste, name='fatura_liste'),
    path('faturalar/yeni/', views.fatura_ekle, name='fatura_ekle'),

    # Çek / Senet Takibi
    path('ceksenet/', views.ceksenet_liste, name='ceksenet_liste'),
    path('ceksenet/yeni/', views.ceksenet_ekle, name='ceksenet_ekle'),
]
