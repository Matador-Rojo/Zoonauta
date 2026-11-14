"""El iniciador solo abre el juego: no descarga ni instala nada (Zoonauta 6.0, 2026-11-14)."""
import json
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen

from codigo.interfaz import iniciar


class Inicio(unittest.TestCase):
    def test_abre_el_servidor_con_el_python_actual_y_el_puerto_pedido(self):
        with patch.object(sys, "argv", ["iniciar", "--puerto", "8767"]), \
                patch.object(iniciar.subprocess, "run") as ejecutar:
            iniciar.main()
        orden = ejecutar.call_args.args[0]
        self.assertEqual([sys.executable, "-m", "codigo.interfaz.servidor", "--abrir", "--puerto", "8767"], orden)

    def test_fallo_del_servidor_se_informa_sin_reintentar(self):
        with patch.object(sys, "argv", ["iniciar"]), \
                patch.object(iniciar.subprocess, "run", side_effect=OSError("Puerto ocupado")) as ejecutar:
            with self.assertRaises(SystemExit) as error:
                iniciar.main()
        self.assertEqual(1, error.exception.code)
        ejecutar.assert_called_once()

    def test_no_quedan_opciones_de_descarga(self):
        with patch.object(sys, "argv", ["iniciar", "--sin-descargas"]), patch.object(iniciar.subprocess, "run"):
            with self.assertRaises(SystemExit) as error:
                iniciar.main()
        self.assertEqual(2, error.exception.code, "--sin-descargas ya no existe")

    def test_servidor_real_abre_la_6_0_con_su_voz_grabada(self):
        # Arranca el iniciador de verdad (sin abrir el navegador) y comprueba el juego.
        with socket.socket() as reserva:
            reserva.bind(("127.0.0.1", 0))
            puerto = reserva.getsockname()[1]
        # Proceso hijo: el iniciador real, con el navegador desactivado y el servidor en el
        # mismo proceso (en lugar de un subprocess), para poder terminarlo al final.
        programa = """
import runpy, sys
from unittest.mock import patch
import codigo.interfaz.iniciar as iniciar

def servidor_en_este_proceso(orden, **_):
    sys.argv = ["servidor", *orden[3:]]
    runpy.run_module("codigo.interfaz.servidor", run_name="__main__")

patch("webbrowser.open").start()
patch.object(iniciar.subprocess, "run", servidor_en_este_proceso).start()
sys.argv = ["iniciar", "--puerto", PUERTO]
iniciar.main()
""".replace("PUERTO", repr(str(puerto)))
        proceso = subprocess.Popen([sys.executable, "-c", programa], cwd=iniciar.RAIZ_PROYECTO,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            limite = time.monotonic() + 20
            while True:
                try:
                    with urlopen(f"http://127.0.0.1:{puerto}/api/vista", timeout=1) as respuesta:
                        vista = json.load(respuesta)
                    break
                except OSError:
                    if proceso.poll() is not None or time.monotonic() >= limite:
                        self.fail("El iniciador no abrió el servidor: " + proceso.stderr.read().decode(errors="replace")[-500:])
                    time.sleep(0.1)
            self.assertEqual(288, len(vista["catalogo_animales"]))
            with urlopen(f"http://127.0.0.1:{puerto}/", timeout=2) as respuesta:
                self.assertIn(b"/v6/assets/", respuesta.read(), "«/» sirve la 6.0")
            with urlopen(f"http://127.0.0.1:{puerto}/api/voz/config", timeout=2) as respuesta:
                grabadas = json.load(respuesta)["grabadas"]
            self.assertGreaterEqual(grabadas["es"], 350, "la voz grabada de Zoonauta está disponible")
        finally:
            proceso.terminate()
            proceso.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
