from django.contrib import admin
from .models import (
    User, 
    PlatformMedsos, 
    Kriteria, 
    AsetCigem, 
    GayaKonten, 
    TargetPlatform, 
    NilaiGayaKonten, 
    RiwayatSpk, 
    DetailRiwayatAset, 
    EvaluasiKonten
)

# Daftarkan semua tabel biar muncul di web Admin
admin.site.register(User)
admin.site.register(PlatformMedsos)
admin.site.register(Kriteria)
admin.site.register(AsetCigem)
admin.site.register(GayaKonten)
admin.site.register(TargetPlatform)
admin.site.register(NilaiGayaKonten)
admin.site.register(RiwayatSpk)
admin.site.register(DetailRiwayatAset)
admin.site.register(EvaluasiKonten)