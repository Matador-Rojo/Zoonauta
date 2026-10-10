"""Contratos de voz: lecturas fieles, caché y límites HTTP. Sin usar una API real."""
import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import http.client
import io
import json
import os
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from codigo.interfaz.servidor import Servidor
from codigo.interfaz.voz import SALUDO, VozNatural, VozNoDisponible


def audio_simulado(texto):
    return io.BytesIO(json.dumps({'choices': [{'finish_reason': 'stop', 'message': {
        'audio': {'data': base64.b64encode(b'ID3audio-simulado').decode(),
                  'transcript': texto}}}]}).encode())


@contextmanager
def servidor_prueba():
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
        servidor = Servidor(('127.0.0.1', 0))
    hilo = Thread(target=servidor.serve_forever, daemon=True); hilo.start()
    try:
        yield servidor
    finally:
        servidor.shutdown(); servidor.server_close(); hilo.join()


class PruebasVoz(unittest.TestCase):
    def test_sin_clave_no_realiza_ninguna_solicitud(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}), patch('codigo.interfaz.voz.urlopen') as api:
            voz = VozNatural()
            self.assertFalse(voz.configuracion()['disponible'])
            with self.assertRaises(VozNoDisponible):
                voz.generar(SALUDO, 'marin')
            api.assert_not_called()

    def test_repetir_y_concurrencia_reutilizan_el_mismo_audio(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'clave-simulada'}):
            voz = VozNatural()
        with patch('codigo.interfaz.voz.urlopen', return_value=audio_simulado(SALUDO)) as api:
            with ThreadPoolExecutor(3) as pool:
                salidas = list(pool.map(lambda _: voz.generar(SALUDO, 'marin'), range(3)))
            self.assertEqual([b'ID3audio-simulado'] * 3, salidas)
            api.assert_called_once()
            cuerpo = json.loads(api.call_args.args[0].data)
            self.assertEqual(SALUDO, cuerpo['messages'][1]['content'])
            self.assertFalse(cuerpo['store'])
            self.assertEqual({'voice': 'marin', 'format': 'mp3'}, cuerpo['audio'])
            self.assertNotIn('clave-simulada', json.dumps(voz.configuracion()))

    def test_transcripcion_distinta_se_rechaza_y_no_se_guarda(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'clave-simulada'}):
            voz = VozNatural()
        with patch('codigo.interfaz.voz.urlopen', return_value=audio_simulado('Esta sería una pista diferente.')):
            with self.assertRaises(VozNoDisponible):
                voz.generar(SALUDO, 'marin')
        self.assertEqual(0, len(voz._cache))

    def test_errores_del_proveedor_no_exponen_credenciales(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'clave-simulada'}):
            voz = VozNatural()
        for codigo in [401, 429, 500]:
            with patch('codigo.interfaz.voz.urlopen', side_effect=HTTPError('https://api.openai.com', codigo, 'error', {}, None)):
                with self.assertRaises(VozNoDisponible) as error:
                    voz.generar(SALUDO, 'marin')
                self.assertNotIn('clave-simulada', str(error.exception))

    def test_http_solo_lee_la_respuesta_actual_sin_mutar_el_juego(self):
        with servidor_prueba() as servidor:
            cliente = http.client.HTTPConnection('127.0.0.1', servidor.server_port)
            cliente.request('GET', '/api/vista'); r = cliente.getresponse()
            cookie = r.getheader('Set-Cookie').split(';')[0]; vista = json.loads(r.read())
            headers = {'Cookie': cookie, 'Content-Type': 'application/json'}
            payload = {'revision': vista['revision'], 'voz': 'marin', 'texto': 'No leer este texto arbitrario.'}
            with patch.object(servidor.voz, 'generar', return_value=b'ID3audio-simulado') as api:
                cliente.request('POST', '/api/voz', json.dumps(payload), headers); r = cliente.getresponse()
                self.assertEqual(200, r.status); self.assertEqual(b'ID3audio-simulado', r.read())
                self.assertIn("media-src 'self' blob:", r.getheader('Content-Security-Policy'))
                api.assert_called_once_with(vista['respuesta']['texto_voz'], 'marin')
                api.reset_mock(); payload['revision'] += 1
                cliente.request('POST', '/api/voz', json.dumps(payload), headers); r = cliente.getresponse()
                self.assertEqual(409, r.status); r.read(); api.assert_not_called()
                headers['Origin'] = 'https://otro-origen.example'
                cliente.request('POST', '/api/voz', json.dumps(payload), headers); r = cliente.getresponse()
                self.assertEqual(403, r.status); r.read(); api.assert_not_called()
            cliente.request('GET', '/api/vista', headers={'Cookie': cookie}); r = cliente.getresponse()
            self.assertEqual(vista['revision'], json.loads(r.read())['revision']); cliente.close()


if __name__ == '__main__':
    unittest.main()
