# spk_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Endpoint API: /api/rekomendasi/<id_gaya>/
    path('rekomendasi/<int:gaya_id>/', views.rekomendasi_medsos, name='rekomendasi_medsos'),
    path('rekomendasi_dinamis/', views.rekomendasi_dinamis, name='rekomendasi_dinamis'),
    path('simpan_ide/', views.simpan_ide_konten, name='simpan_ide_konten'),
    path('get_assets/', views.get_assets, name='get_assets'),
]
