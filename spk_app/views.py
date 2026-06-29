import os
import json
import hashlib
import traceback
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import PlatformMedsos, TargetPlatform, NilaiGayaKonten, User, AsetCigem, GayaKonten, RiwayatSpk
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta

def hitung_bobot_gap(gap):
    pemetaan = {
        0: 5.0, 1: 4.5, -1: 4.0, 2: 3.5, -2: 3.0,
        3: 2.5, -3: 2.0, 4: 1.5, -4: 1.0, 5: 0.5, -5: 0.0
    }
    return pemetaan.get(gap, 0.0)


def _get_cached_platform_data():
    cache_key = 'platform_ranking_data'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    platforms = list(PlatformMedsos.objects.all())
    target_items = list(
        TargetPlatform.objects.select_related('id_platform', 'id_kriteria').all()
    )

    targets_by_platform = {}
    for target in target_items:
        targets_by_platform.setdefault(target.id_platform_id, []).append(target)

    data = {
        'platforms': platforms,
        'targets_by_platform': targets_by_platform,
    }
    cache.set(cache_key, data, 300)
    return data


def _generate_ide_konten_ai(nama_aset, nama_gaya, custom_prompt, platform_terbaik):
    """Generate content ideas from AI only - no caching, no fallback, pure AI."""
    api_key_gemini = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key_gemini:
        raise RuntimeError('GEMINI_API_KEY belum dikonfigurasi di environment Railway')
    
    prompt_text = (
        f"Bertindaklah sebagai Tim Kreatif Social Media Cigem Creative.\n"
        f"{custom_prompt}\n"
        f"Sesuaikan ide ini khusus untuk algoritma platform {platform_terbaik}.\n"
        f"Tuliskan maksimal 3 kalimat yang memancing interaksi audiens.\n\n"
        f"ATURAN PENTING:\n"
        f"1. LANGSUNG berikan isi caption atau kontennya saja.\n"
        f"2. DILARANG KERAS menggunakan kata pengantar atau basa-basi.\n"
        f"3. DILARANG menggunakan simbol format markdown."
    )

    from google import genai
    client = genai.Client(api_key=api_key_gemini)
    response = client.models.generate_content(
        model=os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash'),
        contents=prompt_text
    )
    teks_ide = getattr(response, 'text', '').strip()
    if not teks_ide:
        raise RuntimeError('Gemini tidak mengembalikan konten')
    
    return teks_ide


def _build_ranking(dict_aktual, nilai_default=3):
    data = _get_cached_platform_data()
    platforms = data['platforms']
    targets_by_platform = data['targets_by_platform']

    hasil_rekomendasi = []
    for platform in platforms:
        target_qs = targets_by_platform.get(platform.id_platform, [])
        total_bobot_core = 0
        count_core = 0
        total_bobot_secondary = 0
        count_secondary = 0

        for target in target_qs:
            id_kriteria = target.id_kriteria_id
            nilai_target = target.nilai_target
            jenis_faktor = target.jenis_faktor
            nilai_aktual = dict_aktual.get(id_kriteria, nilai_default)
            gap = nilai_aktual - nilai_target
            bobot = hitung_bobot_gap(gap)
            if jenis_faktor == 'Core':
                total_bobot_core += bobot
                count_core += 1
            else:
                total_bobot_secondary += bobot
                count_secondary += 1

        ncf = (total_bobot_core / count_core) if count_core > 0 else 0
        nsf = (total_bobot_secondary / count_secondary) if count_secondary > 0 else 0
        nilai_total = (0.6 * ncf) + (0.4 * nsf)
        hasil_rekomendasi.append({
            'id_platform': platform.id_platform,
            'nama_platform': platform.nama_platform,
            'skor_akhir_spk': round(nilai_total, 2)
        })

    hasil_rekomendasi.sort(key=lambda x: x['skor_akhir_spk'], reverse=True)
    return hasil_rekomendasi


def rekomendasi_medsos(request, gaya_id):
    try:
        nilai_aktual_qs = NilaiGayaKonten.objects.filter(id_gaya=gaya_id)
        if not nilai_aktual_qs.exists():
            return JsonResponse({'error': 'Gaya konten tidak ditemukan'}, status=404)
        dict_aktual = {item.id_kriteria_id: item.skor_aktual for item in nilai_aktual_qs}
        hasil_rekomendasi = []
        ranking = _build_ranking(dict_aktual, nilai_default=0)
        for item in ranking:
            hasil_rekomendasi.append({
                'id_platform': item['id_platform'],
                'nama_platform': item['nama_platform'],
                'ncf': 0,
                'nsf': 0,
                'skor_akhir_spk': item['skor_akhir_spk']
            })
        return JsonResponse({
            'status': 'success',
            'gaya_terpilih': gaya_id,
            'data': hasil_rekomendasi
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def rekomendasi_dinamis(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dict_aktual = {
                'K01': data.get('K01', 3),
                'K02': data.get('K02', 3),
                'K03': data.get('K03', 3),
                'K04': data.get('K04', 3),
                'K05': data.get('K05', 3),
                'K06': data.get('K06', 3),
            }
            hasil_rekomendasi = []
            ranking = _build_ranking(dict_aktual, nilai_default=0)
            for item in ranking:
                hasil_rekomendasi.append({
                    'id_platform': item['id_platform'],
                    'nama_platform': item['nama_platform'],
                    'ncf': 0,
                    'nsf': 0,
                    'skor_akhir_spk': item['skor_akhir_spk']
                })
            return JsonResponse({
                'status': 'success',
                'data': hasil_rekomendasi
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
def simpan_ide_konten(request):
    if request.method == 'GET':
        return JsonResponse({'status': 'ok'})
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nama_aset = data.get('aset', '')
            nama_gaya = data.get('gaya', '')
            
            custom_prompt = data.get('custom_prompt', f"Buatkan ide konten tentang {nama_aset} dengan gaya {nama_gaya}")
            
            gaya_scores = {
                'Edukasi': {'K01': 3, 'K02': 3, 'K03': 2, 'K04': 3, 'K05': 2, 'K06': 2},
                'Promosi / Jualan': {'K01': 4, 'K02': 2, 'K03': 5, 'K04': 5, 'K05': 5, 'K06': 4},
                'Journey PO / BTS': {'K01': 3, 'K02': 4, 'K03': 3, 'K04': 2, 'K05': 2, 'K06': 2},
                'Komedi / Tren': {'K01': 5, 'K02': 5, 'K03': 4, 'K04': 2, 'K05': 2, 'K06': 5},
                'Portofolio': {'K01': 1, 'K02': 2, 'K03': 1, 'K04': 5, 'K05': 5, 'K06': 5},
            }
            dict_aktual = gaya_scores.get(nama_gaya, {'K01': 3, 'K02': 3, 'K03': 3, 'K04': 3, 'K05': 3, 'K06': 3})
            ranking_medsos = _build_ranking(dict_aktual, nilai_default=3)
            platform_terbaik = ranking_medsos[0]['nama_platform'] if ranking_medsos else 'Instagram'
            
            # Generate content ideas from AI only
            teks_ide = _generate_ide_konten_ai(nama_aset, nama_gaya, custom_prompt, platform_terbaik)
            
            return JsonResponse({
                'status': 'success', 
                'ide_konten': teks_ide, 
                'ranking': ranking_medsos
            })
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({
                'status': 'error', 
                'error': str(e)
            }, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def get_assets(request):
    assets = list(AsetCigem.objects.values('id_aset', 'kategori_aset', 'nama_aset'))
    return JsonResponse({'assets': assets}, safe=False)