from django.db import models

class User(models.Model):
    id_user = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    nama_lengkap = models.CharField(max_length=150)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.nama_lengkap

class PlatformMedsos(models.Model):
    id_platform = models.AutoField(primary_key=True)
    nama_platform = models.CharField(max_length=100)

    class Meta:
        db_table = 'platform_medsos'

    def __str__(self):
        return self.nama_platform

class Kriteria(models.Model):
    id_kriteria = models.CharField(max_length=50, primary_key=True)
    nama_kriteria = models.CharField(max_length=150)

    class Meta:
        db_table = 'kriteria'

    def __str__(self):
        return self.nama_kriteria

class AsetCigem(models.Model):
    KATEGORI_CHOICES = [
        ('Alat', 'Alat'),
        ('Bahan', 'Bahan'),
        ('Lainnya', 'Lainnya'),
    ]
    id_aset = models.AutoField(primary_key=True)
    kategori_aset = models.CharField(max_length=50, choices=KATEGORI_CHOICES)
    nama_aset = models.CharField(max_length=150)

    class Meta:
        db_table = 'aset_cigem'

    def __str__(self):
        return self.nama_aset

class GayaKonten(models.Model):
    id_gaya = models.AutoField(primary_key=True)
    nama_gaya = models.CharField(max_length=100)

    class Meta:
        db_table = 'gaya_konten'

    def __str__(self):
        return self.nama_gaya

class TargetPlatform(models.Model):
    JENIS_FAKTOR_CHOICES = [
        ('Core', 'Core'),
        ('Secondary', 'Secondary'),
    ]
    id_target = models.AutoField(primary_key=True)
    id_platform = models.ForeignKey(PlatformMedsos, on_delete=models.CASCADE, db_column='id_platform')
    id_kriteria = models.ForeignKey(Kriteria, on_delete=models.CASCADE, db_column='id_kriteria')
    nilai_target = models.IntegerField()
    jenis_faktor = models.CharField(max_length=50, choices=JENIS_FAKTOR_CHOICES)

    class Meta:
        db_table = 'target_platform'

    def __str__(self):
        return f"{self.id_platform.nama_platform} - {self.id_kriteria.nama_kriteria}"

class NilaiGayaKonten(models.Model):
    id_nilai_gaya = models.AutoField(primary_key=True)
    id_gaya = models.ForeignKey(GayaKonten, on_delete=models.CASCADE, db_column='id_gaya')
    id_kriteria = models.ForeignKey(Kriteria, on_delete=models.CASCADE, db_column='id_kriteria')
    skor_aktual = models.IntegerField()

    class Meta:
        db_table = 'nilai_gaya_konten'

    def __str__(self):
        return f"{self.id_gaya.nama_gaya} - {self.id_kriteria.nama_kriteria}"

class RiwayatSpk(models.Model):
    id_riwayat = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='id_user')
    tanggal = models.DateTimeField(auto_now_add=True)
    kategori_input = models.CharField(max_length=100)
    id_platform_rekomendasi = models.ForeignKey(PlatformMedsos, on_delete=models.CASCADE, related_name='rekomendasi', db_column='id_platform_rekomendasi')
    nama_platform = models.CharField(max_length=100)
    teks_ide_konten = models.TextField()
    id_platform = models.ForeignKey(PlatformMedsos, on_delete=models.CASCADE, related_name='platform_asal', db_column='id_platform')
    skor_akhir_spk = models.FloatField()

    class Meta:
        db_table = 'riwayat_spk'

    def __str__(self):
        return f"Riwayat {self.id_riwayat} - {self.id_user.nama_lengkap}"

class DetailRiwayatAset(models.Model):
    id_detail = models.AutoField(primary_key=True)
    id_riwayat = models.ForeignKey(RiwayatSpk, on_delete=models.CASCADE, db_column='id_riwayat')
    id_aset = models.ForeignKey(AsetCigem, on_delete=models.CASCADE, db_column='id_aset')

    class Meta:
        db_table = 'detail_riwayat_aset'

    def __str__(self):
        return f"Riwayat {self.id_riwayat.id_riwayat} - {self.id_aset.nama_aset}"

class EvaluasiKonten(models.Model):
    STATUS_CHOICES = [
        ('Sukses', 'Sukses'),
        ('Gagal', 'Gagal'),
        ('Pending', 'Pending'),
    ]
    id_evaluasi = models.AutoField(primary_key=True)
    id_riwayat = models.OneToOneField(RiwayatSpk, on_delete=models.CASCADE, db_column='id_riwayat')
    jumlah_tayangan = models.IntegerField()
    status_konten = models.CharField(max_length=50, choices=STATUS_CHOICES)
    catatan = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'evaluasi_konten'

    def __str__(self):
        return f"Evaluasi {self.id_evaluasi} - {self.status_konten}"