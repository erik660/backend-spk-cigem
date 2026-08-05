import os
import json
import hashlib
import traceback
import requests
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
    
    # Force refresh dari database setiap kali dipanggil untuk memastikan fitur SPK selalu muncul
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
    """Generate dynamic structured content ideas using Groq API."""
    groq_token = os.environ.get('GROQ_API_KEY')

    konteks_gaya = ""
    if "Edukasi" in nama_gaya:
        konteks_gaya = "Karena ini gaya Edukasi, fokuskan untuk memberikan ilmu bermanfaat seperti penjelasan jenis bahan (cotton combed, dll), jenis jahitan, cara perawatan kaos, atau wawasan industri konveksi."
    elif "Promosi" in nama_gaya or "Jualan" in nama_gaya:
        konteks_gaya = "Karena ini gaya Promosi, fokuskan pada jualan langsung (direct selling). Tonjolkan kualitas, promo/diskon (jika relevan), kemudahan pemesanan, dan ajak audiens untuk segera order."
    elif "Journey" in nama_gaya or "PO" in nama_gaya or "BTS" in nama_gaya:
        konteks_gaya = "Karena ini gaya Journey/BTS, ceritakan alur produksi secara jujur dan menarik. Mulai dari pemotongan bahan, proses jahit/sablon, hingga packing pesanan klien. Buat audiens merasa ikut dalam perjalanan pembuatannya."
    elif "Portofolio" in nama_gaya:
        konteks_gaya = "Karena ini gaya Portofolio, fokuskan pada memamerkan hasil jadi pesanan klien (showcase). Perlihatkan detail kerapian jahitan, ketajaman sablon/bordir, dan betapa kerennya hasil akhir produk tersebut."
    elif "Komedi" in nama_gaya or "Tren" in nama_gaya:
        konteks_gaya = "Karena ini gaya Komedi/Tren, buat ide konten yang relate, lucu, atau mengikuti tren viral saat ini, tapi tetap nyambung dengan kehidupan konveksi atau custom baju."
    else:
        konteks_gaya = f"Sesuaikan ide konten ini sebaik mungkin dengan gaya: {nama_gaya}."

    prompt_text = (
        f"Anda adalah Tim Kreatif Social Media Senior di Cigem Creative (perusahaan konveksi & garment custom premium).\n"
        f"Aset perusahaan: {nama_aset}\n"
        f"Gaya konten yang diinginkan: {nama_gaya}\n"
        f"Arahan spesifik dari user: {custom_prompt}\n"
        f"Platform target: {platform_terbaik}\n\n"
        f"LINGKUP KONTEKS KONVEKSI KREATIF:\n"
        f"1. Jika aset berupa Alat/Mesin (seperti Mesin Jahit, Sablon, dll), JANGAN PERNAH membuat tutorial mekanik! Audiens kami adalah calon pemesan baju custom.\n"
        f"2. Gunakan kehadiran alat untuk memperlihatkan ASMR/satisfying production, memamerkan kerapian (Portofolio), dan membangun rasa percaya (trust).\n"
        f"3. ARAHAN KHUSUS GAYA KONTEN: {konteks_gaya}\n\n"
        f"Tugas Anda: Berikan maksimal 3 ide konten sosial media yang spesifik, sangat asik, kreatif, bervariasi, dan tidak kaku.\n"
        f"Keluaran HARUS berupa valid JSON dengan struktur persis seperti ini:\n"
        f"{{\n"
        f"  \"ideas\": [\n"
        f"    {{\n"
        f"      \"title\": \"Judul Ide Konten\",\n"
        f"      \"hook\": \"Kalimat pembuka (hook) 3 detik pertama yang memancing perhatian\",\n"
        f"      \"caption\": \"Caption lengkap dan menarik untuk postingan media sosial\",\n"
        f"      \"script\": \"Alur skrip video singkat atau deskripsi adegan visual\",\n"
        f"      \"hashtags\": [\"#tag1\", \"#tag2\", \"#tag3\"],\n"
        f"      \"CTA\": \"Kalimat Call to Action di akhir konten\"\n"
        f"    }}\n"
        f"  ]\n"
        f"}}\n"
        f"Jangan sertakan teks penjelasan apapun di luar format JSON tersebut."
    )

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt_text}],
            "response_format": {"type": "json_object"},
            "temperature": 0.8,
            "max_tokens": 1500
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=25)
        if resp.status_code == 200:
            res_json = resp.json()
            if 'choices' in res_json and len(res_json['choices']) > 0:
                content = res_json['choices'][0]['message']['content']
                parsed = json.loads(content)
                if isinstance(parsed, dict) and 'ideas' in parsed:
                    return parsed
                elif isinstance(parsed, dict):
                    return {"ideas": [parsed]}
        else:
            print(f"Groq API Error {resp.status_code}: {resp.text}")
            
    except Exception as e:
        print(f"Error calling Groq API: {e}")

    # Fallback yang terstruktur rapi jika AI gagal atau koneksi bermasalah
    return {
        "ideas": [
            {
                "title": f"Ide Kreatif: {nama_aset}",
                "hook": f"Yakin sudah tahu cara terbaik memanfaatkan {nama_aset}?",
                "caption": f"Dalam postingan kali ini, kita akan membahas rahasia di balik {nama_aset} dengan pendekatan gaya {nama_gaya} yang menarik dan mudah dipahami. Simak penjelasan lengkapnya!",
                "script": f"1. [Visual: Sorot jelas {nama_aset} di 3 detik pertama]\n2. [Audio/VO]: Jelaskan keunggulan utama dengan gaya {nama_gaya}.\n3. [Outro]: Ajak audiens berinteraksi.",
                "hashtags": [f"#{nama_aset.replace(' ', '')}", f"#{nama_gaya.replace(' ', '')}", f"#{platform_terbaik.replace(' ', '')}", "#CigemCreative"],
                "CTA": "Bagikan pendapatmu atau tag temanmu di kolom komentar ya!"
            }
        ]
    }

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


@csrf_exempt
def health_check(request):
    """Simple health check for deployment/platform probes."""
    return JsonResponse({'status': 'ok', 'time': timezone.now().isoformat()})