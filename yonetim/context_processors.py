MENU_MAP = {
    'odeme_liste': 'odemeler',
    'odeme_ekle': 'odemeler',
    'alacak_liste': 'alacaklar',
    'alacak_ekle': 'alacaklar',
    'haftalik_plan_liste': 'planlar',
    'haftalik_plan_ekle': 'planlar',
    'stok_liste': 'stoklar',
    'stok_ekle': 'stoklar',
    'butce_liste': 'butce',
    'butce_ekle': 'butce',
    'vergi_ayarlari': 'vergilendirme',
    'fis_liste': 'fisler',
    'fis_ekle': 'fisler',
}


def sidebar_menu(request):
    url_name = ''
    if request.resolver_match:
        url_name = request.resolver_match.url_name or ''
    return {
        'active_menu': MENU_MAP.get(url_name, ''),
    }
