from django.urls import path

from . import views

app_name = 'yonetim'

urlpatterns = [
    path('', views.ana_sayfa, name='ana_sayfa'),

    path('odemeler/', views.odeme_liste, name='odeme_liste'),
    path('odemeler/yeni/', views.odeme_ekle, name='odeme_ekle'),
    path('odemeler/<int:pk>/duzenle/', views.odeme_duzenle, name='odeme_duzenle'),
    path('odemeler/<int:pk>/sil/', views.odeme_sil, name='odeme_sil'),
    path('odemeler/<int:pk>/durum/', views.odeme_durum_degistir, name='odeme_durum_degistir'),

    path('alacaklar/', views.alacak_liste, name='alacak_liste'),
    path('alacaklar/yeni/', views.alacak_ekle, name='alacak_ekle'),
    path('alacaklar/<int:pk>/duzenle/', views.alacak_duzenle, name='alacak_duzenle'),
    path('alacaklar/<int:pk>/sil/', views.alacak_sil, name='alacak_sil'),
    path('alacaklar/<int:pk>/durum/', views.alacak_durum_degistir, name='alacak_durum_degistir'),

    path('planlar/', views.haftalik_plan_liste, name='haftalik_plan_liste'),
    path('planlar/yeni/', views.haftalik_plan_ekle, name='haftalik_plan_ekle'),
    path('planlar/<int:pk>/durum/', views.haftalik_plan_durum_degistir, name='haftalik_plan_durum_degistir'),

    path('cariler/', views.cari_liste, name='cari_liste'),
    path('cariler/yeni/', views.cari_ekle, name='cari_ekle'),
    path('cariler/<int:pk>/', views.cari_detay, name='cari_detay'),
    path('cariler/<int:pk>/sil/', views.cari_sil, name='cari_sil'),

    path('butce/', views.butce_liste, name='butce_liste'),
    path('butce/yeni/', views.butce_ekle, name='butce_ekle'),

    path('vergilendirme/', views.vergi_ayarlari, name='vergi_ayarlari'),

    path('fisler/', views.fis_liste, name='fis_liste'),
    path('fisler/yeni/', views.fis_ekle, name='fis_ekle'),
    path('fisler/<int:pk>/duzenle/', views.fis_duzenle, name='fis_duzenle'),
    path('fisler/<int:pk>/sil/', views.fis_sil, name='fis_sil'),
    path('fisler/<int:pk>/durum/', views.fis_durum_degistir, name='fis_durum_degistir'),

    path('kasalar/', views.kasa_liste, name='kasa_liste'),
    path('kasalar/yeni/', views.kasa_ekle, name='kasa_ekle'),
    path('kasalar/hareket-ekle/', views.kasa_hareket_ekle, name='kasa_hareket_ekle'),

    path('giderler/', views.gider_liste, name='gider_liste'),
    path('giderler/yeni/', views.gider_ekle, name='gider_ekle'),

    path('faturalar/', views.fatura_liste, name='fatura_liste'),
    path('faturalar/yeni/', views.fatura_ekle, name='fatura_ekle'),

    path('ceksenet/', views.ceksenet_liste, name='ceksenet_liste'),
    path('ceksenet/yeni/', views.ceksenet_ekle, name='ceksenet_ekle'),

    path('portfoy/', views.finans_portfoy, name='finans_portfoy'),
    path('urun-islemleri/', views.urun_islemleri, name='urun_islemleri'),
]
