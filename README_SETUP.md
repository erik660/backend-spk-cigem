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

---

Deployment (Render / Vercel)

- Pilihan yang direkomendasikan: Render (Web Service) atau Vercel (Serverless functions). Untuk Django full app, Render lebih langsung.

Render quick steps:

1. Push repo ke GitHub.
2. Di Render dashboard -> New -> Web Service -> Connect GitHub repo -> pilih branch.
3. Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
4. Start Command (Render biasanya pakai `gunicorn` dari Procfile); jika perlu gunakan: `gunicorn backend_cigem.wsgi --log-file -`
5. Tambahkan Environment Variables di dashboard:
  - `HUGGINGFACE_API_KEY` = <token dari Hugging Face>
  - `HF_MODEL_URL` = https://api-inference.huggingface.co/models/google/flan-t5-base (opsional)
  - `DEV_SQLITE` = `1` (jika ingin pakai SQLite di Render; catatan: filesystem Render ephemeral)
  - `SECRET_KEY` = set ke value random
  - `DEBUG` = `False`

6. Deploy. Setelah deploy selesai, cek health endpoint:

  curl -i https://<your-render-url>/health/

Vercel notes (Serverless):
- Vercel is a good option for serverless API endpoints. For simplicity we added a lightweight serverless endpoint at `/api/simpan_ide` that you can deploy to Vercel and use directly from your Flutter app.

Deploying to Vercel:
1. Push your repo to GitHub (already done).
2. Go to https://vercel.com/new and import the GitHub repo `erik660/backend-spk-cigem`.
3. Ensure the `Framework Preset` is set to `Other` (or leave auto-detected). Vercel will expose serverless functions under `/api`.
4. Add the following Environment Variables in Vercel project settings:
   - `HUGGINGFACE_API_KEY` = <your HF token>
   - `HF_MODEL_URL` = https://api-inference.huggingface.co/models/google/flan-t5-large (optional)
   - `HF_TEMPERATURE`, `HF_TOP_K`, `HF_TOP_P`, `HF_REP_PEN` (optional)
5. Deploy. The function will be available at `https://<your-vercel-app>/api/simpan_ide`.

Environment & Safety:
- Pastikan `HUGGINGFACE_API_KEY` tidak dikommit. Simpan di Vercel dashboard Secrets.

Testing the content-ideas endpoint (example):

```bash
curl -X POST https://<your-vercel-app>/api/simpan_ide \
  -H "Content-Type: application/json" \
  -d '{"aset":"Mesin Jahit", "gaya":"Edukasi"}'
```

Jika butuh, saya bisa:
- Membuat PR khusus yang memisahkan endpoint ini ke folder `api/` (sudah dilakukan),
- Membantu Anda konfigurasi Vercel dan set env vars.
