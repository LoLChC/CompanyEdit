from yonetim.models import Alacak, Odeme, CariHesap
from django.db.models import Q

# Alacak temizligi
alacak_qs = Alacak.objects.filter(
    Q(aciklama__icontains='Ürün Satışı') |
    Q(aciklama__icontains='Ana Ürün') |
    Q(aciklama__icontains='Satış') |
    Q(aciklama__icontains='Adet') |
    Q(kimden__in=CariHesap.objects.values_list('unvan', flat=True))
)
alacak_count = alacak_qs.count()
alacak_qs.delete()

# Odeme temizligi
odeme_qs = Odeme.objects.filter(
    Q(aciklama__icontains='Ürün Alışı') |
    Q(aciklama__icontains='Elmaslar Pide') |
    Q(aciklama__icontains='Alış')
)
odeme_count = odeme_qs.count()
odeme_qs.delete()

print(f'ALACAK_SILINEN:{alacak_count}')
print(f'ODEME_SILINEN:{odeme_count}')
