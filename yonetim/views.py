from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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
from .services.butce_hesapla import butce_guncelle, butce_ozetini_hesapla, vergi_ayarlarini_getir
from .services.muhasebe import (
    cari_guncelle,
    kasa_guncelle,
    kasa_hareketi_olustur,
    kdv_hesapla,
)


def _parse_decimal(value, field_label):
    if not value or not str(value).strip():
        raise ValueError(f'{field_label} alanı zorunludur.')
    try:
        return Decimal(str(value).replace(',', '.'))
    except InvalidOperation as exc:
        raise ValueError(f'{field_label} geçerli bir sayı olmalıdır.') from exc


def _parse_decimal_optional(value, default=Decimal('0')):
    if not value or not str(value).strip():
        return default
    try:
        return Decimal(str(value).replace(',', '.'))
    except InvalidOperation as exc:
        raise ValueError('Geçerli bir sayı girilmelidir.') from exc


def _parse_date(value, field_label):
    if not value or not str