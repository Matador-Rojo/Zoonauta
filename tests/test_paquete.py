"""Integridad de una descarga sin ignorar modificaciones reales de los BAT."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from codigo.nucleo.verificar_paquete import verificar


class Paquete(unittest.TestCase):
    def preparar(self, carpeta, contenido=b"@echo off\npause\n"):
        raiz = Path(carpeta)
        (raiz / "datos").mkdir()
        (raiz / ".gitattributes").write_text("*.bat text eol=crlf\n", encoding="utf-8")
        (raiz / "iniciar.bat").write_bytes(contenido)
        ficha = {"ruta": "iniciar.bat", "bytes": len(contenido), "sha256": hashlib.sha256(contenido).hexdigest()}
        (raiz / "datos/manifest.json").write_text(json.dumps({"archivos": [ficha]}), encoding="utf-8")
        return raiz

    def test_paquete_original_correcto(self):
        with TemporaryDirectory() as carpeta:
            r = verificar(self.preparar(carpeta))
            self.assertTrue(r["correcto"])
            self.assertEqual([], r["normalizaciones_crlf_declaradas"])

    def test_exportacion_crlf_declarada_es_el_mismo_contenido(self):
        with TemporaryDirectory() as carpeta:
            raiz = self.preparar(carpeta)
            (raiz / "iniciar.bat").write_bytes(b"@echo off\r\npause\r\n")
            r = verificar(raiz)
            self.assertTrue(r["correcto"])
            self.assertEqual(["iniciar.bat"], r["normalizaciones_crlf_declaradas"])

    def test_modificacion_real_se_rechaza(self):
        with TemporaryDirectory() as carpeta:
            raiz = self.preparar(carpeta)
            (raiz / "iniciar.bat").write_bytes(b"@echo off\r\necho MODIFICADO\r\npause\r\n")
            self.assertFalse(verificar(raiz)["correcto"])

    def test_sin_declaracion_no_se_normaliza(self):
        with TemporaryDirectory() as carpeta:
            raiz = self.preparar(carpeta)
            (raiz / ".gitattributes").write_text("", encoding="utf-8")
            (raiz / "iniciar.bat").write_bytes(b"@echo off\r\npause\r\n")
            self.assertFalse(verificar(raiz)["correcto"])

    def test_no_admite_rutas_externas_ni_duplicadas(self):
        with TemporaryDirectory() as carpeta:
            raiz = self.preparar(carpeta)
            p = raiz / "datos/manifest.json"
            d = json.loads(p.read_text("utf-8"))
            d["archivos"].extend([dict(d["archivos"][0]), {"ruta": "../fuera", "bytes": 0, "sha256": ""}])
            p.write_text(json.dumps(d), encoding="utf-8")
            self.assertEqual(2, len(verificar(raiz)["errores"]))


if __name__ == "__main__":
    unittest.main()
