Panduan singkat: setup HUGGINGFACE dan tes endpoint (Bahasa Indonesia)

1) Dapatkan token Hugging Face
- Daftar di https://huggingface.co/ lalu masuk ke Settings -> Access Tokens -> New token
- Beri nama token, scope `read` sudah cukup. Salin token.

2) Simpan token ke environment
- PowerShell (sesi sekarang):
  $env:HUGGINGFACE_API_KEY="PASTE_TOKEN_DI_SINI"
- PowerShell (persisten untuk user):
  setx HUGGINGFACE_API_KEY "PASTE_TOKEN_DI_SINI"
  lalu buka ulang terminal / redeploy app
- Railway / hosting: Project -> Variables -> tambahkan `HUGGINGFACE_API_KEY` = token -> redeploy

3) Pasang dependency
- Aktifkan virtualenv, lalu:
  pip install -r requirements.txt
  (atau pip install requests jika hanya ingin menambah requests)

4) Jalankan server (local)
- python manage.py runserver

5) Tes API
- Contoh curl (ganti host jika perlu):
  curl -X POST http://127.0.0.1:8000/simpan_ide_konten -H "Content-Type: application/json" -d '{"aset":"ProdukA","gaya":"Edukasi"}'

6) Pengaturan opsi (opsional)
- Ubah model HF via env `HF_MODEL_URL` (contoh: https://api-inference.huggingface.co/models/google/flan-t5-base)
- Atur sampling via env: `HF_TEMPERATURE`, `HF_TOP_K`, `HF_TOP_P`, `HF_REP_PEN`
- Cache prompt identik disimpan 60 detik untuk mengurangi pemanggilan API.

7) Catatan keamanan
- Jangan commit token ke repo. Simpan di environment variables.

Butuh saya tambahkan file ini ke repo (sudah dibuat) atau langsung saya jalankan `pip install -r requirements.txt` di terminal untuk Anda?