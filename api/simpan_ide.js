// Vercel Serverless function to generate content ideas using Hugging Face Inference API
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

    const hfToken = process.env.HUGGINGFACE_API_KEY;
    if (!hfToken) return res.status(500).json({ error: 'HUGGINGFACE_API_KEY not configured' });

    const platform_terbaik = 'Instagram';

    const prompt = `Anda adalah Tim Kreatif Social Media Cigem Creative.\n${custom_prompt}\nSesuaikan ide ini khusus untuk algoritma platform ${platform_terbaik}.\nKeluaran harus berupa valid JSON dengan struktur:{\n  "ideas": [{"title":..., "hook":..., "caption":..., "script":..., "hashtags": [...], "CTA":...}]\n} Buat maksimal 3 ide. Jangan sertakan teks penjelasan di luar JSON.`;

    const modelUrl = process.env.HF_MODEL_URL || 'https://api-inference.huggingface.co/models/google/flan-t5-large';
    const payload = {
      inputs: prompt,
      parameters: {
        max_new_tokens: 180,
        do_sample: true,
        temperature: parseFloat(process.env.HF_TEMPERATURE || '0.8'),
        top_k: parseInt(process.env.HF_TOP_K || '50'),
        top_p: parseFloat(process.env.HF_TOP_P || '0.95'),
        repetition_penalty: parseFloat(process.env.HF_REP_PEN || '1.1')
      },
      options: { wait_for_model: true }
    };

    const resp = await fetch(modelUrl, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${hfToken}`,
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
    });

    const out = await resp.json();
    let teks = '';
    if (Array.isArray(out) && out.length && out[0].generated_text) teks = out[0].generated_text;
    else if (out.generated_text) teks = out.generated_text;
    else teks = typeof out === 'string' ? out : JSON.stringify(out);

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
