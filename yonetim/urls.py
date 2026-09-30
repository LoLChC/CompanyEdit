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
]
