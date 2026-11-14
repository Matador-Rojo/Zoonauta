"""Integridad del catálogo ampliado y cobertura de traducciones de la interfaz."""
import unittest

from codigo.nucleo.validar_catalogo import validar as validar_catalogo
from codigo.nucleo.validar_textos_interfaz import validar as validar_textos


class PruebasValidacionContenido(unittest.TestCase):
    def test_catalogo_ampliado_sin_errores(self):
        resultado = validar_catalogo()
        self.assertEqual(resultado["errores"], [])
        self.assertEqual(resultado["conteos"]["animales"], 288)
        self.assertEqual(resultado["conteos"]["habitats"], 48)
        self.assertEqual(resultado["conteos"]["pistas"], 144)
        self.assertEqual(resultado["conteos"]["secundarios"], 31)
        # Ningún texto con marcas de es-ES o pt-PT.
        motivos = resultado["avisos_por_motivo"]
        self.assertNotIn("posible forma de España (es-ES)", motivos)
        self.assertNotIn("posible forma de Portugal (pt-PT)", motivos)

    def test_textos_de_interfaz_traducidos(self):
        resultado = validar_textos()
        self.assertEqual(resultado["sin_traduccion"], [], "añade la traducción o un borrador en TEXTOS_NUEVOS_PENDIENTES")
        self.assertEqual(resultado["variables_distintas"], [])


if __name__ == "__main__":
    unittest.main()
