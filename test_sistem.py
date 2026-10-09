import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sirket_panel.settings")
django.setup()

from django.test import Client
from yonetim.models import CariHesap, Alacak, Odeme

def test_sistem():
    client = Client()
    
    routes = [
        '/',
        '/cariler/',
        '/urun-islemleri/',
        '/alacaklar/',
        '/odemeler/',
    ]
    
    # Get the first available CariHesap id
    cari = CariHesap.objects.first()
    if cari:
        routes.append(f'/cariler/{cari.id}/')
    else:
        print("Uyari: Hic cari bulunamadi, cari detay sayfasi test edilmeyecek.")

    all_passed = True
    print("\n--- TEST SONUCLARI ---")
    for route in routes:
        try:
            response = client.get(route)
            if response.status_code == 200 or (route == '/' and response.status_code == 302):
                print(f"[OK] {route} - HTTP {response.status_code}")
            else:
                print(f"[FAIL] {route} - HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] {route} - {type(e).__name__}: {e}")
            all_passed = False
            
    print("\nTestler tamamlandi.")
    return all_passed

if __name__ == '__main__':
    test_sistem()
