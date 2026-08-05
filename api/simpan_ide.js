// Vercel Serverless function to generate content ideas using Groq API
// Deploy this file under /api on Vercel (it will be available at /api/simpan_ide)

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const body = req.body && Object.keys(req.body).length ? req.body : await jsonFromStream(req);
    const nama_aset = body.aset || '';
    const nama_gaya = body.gaya || '';
    const custom_prompt = body.custom_prompt || `Buatkan ide konten tentang ${nama_aset} dengan gaya ${nama_gaya}`;

    const { fetch } = require('undici');
    // Memasukkan API key Groq yang Anda berikan
    const groqToken = process.env.GROQ_API_KEY;

    const platform_terbaik = 'Instagram';

    const prompt = `Anda adalah Tim Kreatif Social Media Senior di Cigem Creative (perusahaan konveksi & garment custom premium).\nArahan dari tim: ${custom_prompt}\nATURAN KRUSIAL KONVEKSI: Jika melibatkan aset alat/mesin, fokuskan pada keseruan proses produksi (ASMR/satisfying BTS) dan pembuktian kualitas kerapian orderan klien (Portofolio) agar calon klien terkesan dan percaya memesan produk custom di Cigem. Jangan pernah buat tutorial service/rawat mesin!\nSesuaikan ide ini khusus untuk algoritma platform ${platform_terbaik}.\nKeluaran harus berupa valid JSON dengan struktur:{\n  "ideas": [{"title":..., "hook":..., "caption":..., "script":..., "hashtags": [...], "CTA":...}]\n} Buat maksimal 3 ide. Jangan sertakan teks penjelasan di luar JSON.`;

    const modelUrl = 'https://api.groq.com/openai/v1/chat/completions';
    const payload = {
      model: "llama-3.3-70b-versatile", // Model dari Meta di Groq (cepat, cerdas, dan aktif)
      messages: [
        {
          role: "user",
          content: prompt
        }
      ],
      response_format: { type: "json_object" }, // Memaksa format respons sebagai JSON
      temperature: 0.8,
      max_tokens: 1500
    };

    let resp;
    try {
      resp = await fetch(modelUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${groqToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
      });
    } catch (fetchError) {
      console.error('Fetch error:', fetchError);
      return res.status(500).json({ error: `Fetch failed: ${fetchError.message}` });
    }

    let out;
    try {
      out = await resp.json();
    } catch (parseError) {
      const text = await resp.text();
      return res.status(500).json({ error: `Invalid JSON response from Groq: ${text}` });
    }

    if (!resp.ok) {
      return res.status(resp.status).json({ error: out });
    }

    let teks = '';
    if (out.choices && out.choices.length > 0 && out.choices[0].message) {
      teks = out.choices[0].message.content;
    } else {
      teks = JSON.stringify(out);
    }

    try {
      const parsed = JSON.parse(teks);
      return res.status(200).json({ ide_konten: parsed });
    } catch (e) {
      // try to extract JSON substring
      const m = teks.match(/\{\s*\"ideas\"[\s\S]*\}/);
      if (m) {
        try { return res.status(200).json({ ide_konten: JSON.parse(m[0]) }); } catch (e) {}
      }
      // fallback
      return res.status(200).json({ ide_konten: { ideas: [{ title: `Ide: ${nama_aset}`, hook: teks.slice(0,80), caption: teks, script: '', hashtags: [], CTA: 'Tanya di komentar' }] } });
    }
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: String(err) });
  }
}

async function jsonFromStream(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => data += chunk);
    req.on('end', () => {
      try { resolve(JSON.parse(data || '{}')); } catch (e) { resolve({}); }
    });
    req.on('error', reject);
  });
}
