import os
import json
import requests
from dotenv import load_dotenv

def test_groq():
    load_dotenv()
    groq_token = os.environ.get('GROQ_API_KEY')
    print(f"Menguji koneksi Groq API (Key terdeteksi: {'Ya' if groq_token else 'Tidak'})...")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": 'Berikan 1 ide konten singkat untuk produk "Mesin Jahit" dengan gaya "Edukasi" dalam format JSON {"ideas": [{"title": "...", "hook": "...", "caption": "..."}]}'}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.8,
        "max_tokens": 500
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            print("\n[SUKSES] Respons AI dari Groq:")
            print(resp.json()['choices'][0]['message']['content'])
        else:
            print(f"\n[GAGAL] Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"\n[ERROR] Exception: {e}")

if __name__ == '__main__':
    test_groq()