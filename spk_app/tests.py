import json
from django.test import TestCase
from unittest.mock import patch


class IdeKontenTests(TestCase):
	def test_simpan_ide_konten_returns_structured_json(self):
		payload = {'aset': 'Mesin Jahit', 'gaya': 'Edukasi'}
		fake = {
			'ideas': [
				{
					'title': 'Cara Pakai Mesin Jahit',
					'hook': 'Ngerjain kain dalam 5 menit',
					'caption': 'Tutorial singkat tentang mesin jahit',
					'script': 'Buka mesin, pasang benang, jahit',
					'hashtags': ['#jahit', '#craft'],
					'CTA': 'Coba sekarang'
				}
			]
		}

		with patch('spk_app.views._generate_ide_konten_ai', return_value=fake):
			resp = self.client.post('/api/simpan_ide/', data=json.dumps(payload), content_type='application/json')
			self.assertEqual(resp.status_code, 200)
			data = resp.json()
			self.assertIn('ide_konten', data)
			self.assertIsInstance(data['ide_konten'], dict)
			self.assertIn('ideas', data['ide_konten'])
			self.assertIsInstance(data['ide_konten']['ideas'], list)
