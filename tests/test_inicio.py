"""El fallo de preparación no debe bloquear el juego ni ocultar un fallo del servidor."""
from pathlib import Path
import json
import os
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen

from codigo.interfaz import iniciar


class Inicio(unittest.TestCase):
    def invocar(self, argumentos, fallo=None):
        with patch.object(sys, "argv", ["iniciar", *argumentos]), \
                patch.object(iniciar, "preparar", return_value=Path("python-local"), side_effect=fallo) as preparar, \
                patch.object(iniciar, "python_disponible", return_value=Path("python-disponible")), \
                patch.object(iniciar, "ejecutar") as ejecutar:
            iniciar.main()
            return preparar, ejecutar

    def test_descarga_fallida_abre_juego_y_conserva_puerto(self):
        _, ejecutar = self.invocar(["--puerto", "8767"], subprocess.CalledProcessError(1, "preparar_voces"))
        ejecutar.assert_called_once_with(Path("python-disponible"), "-m", "codigo.interfaz.servidor", "--abrir", "--puerto", 8767)

    def test_instalacion_fallida_tambien_abre_juego(self):
        _, ejecutar = self.invocar([], OSError("Sin conexión"))
        self.assertEqual(Path("python-disponible"), ejecutar.call_args.args[0])

    def test_sin_descargas_no_prepara_ni_instala(self):
        preparar, ejecutar = self.invocar(["--sin-descargas"])
        preparar.assert_not_called()
        ejecutar.assert_called_once()

    def test_preparacion_completa_utiliza_entorno_local(self):
        _, ejecutar = self.invocar([])
        self.assertEqual(Path("python-local"), ejecutar.call_args.args[0])

    def test_solo_preparar_no_abre_juego(self):
        _, ejecutar = self.invocar(["--solo-preparar"])
        ejecutar.assert_not_called()

    def test_solo_preparar_fallido_sigue_informando_error(self):
        with self.assertRaises(SystemExit) as error:
            self.invocar(["--solo-preparar"], OSError("Sin conexión"))
        self.assertEqual(1, error.exception.code)

    def test_opciones_contradictorias_se_rechazan(self):
        with self.assertRaises(SystemExit) as error:
            self.invocar(["--solo-preparar", "--sin-descargas"])
        self.assertEqual(2, error.exception.code)

    def test_fallo_del_servidor_no_se_reintenta(self):
        with patch.object(sys, "argv", ["iniciar", "--sin-descargas"]), \
                patch.object(iniciar, "python_disponible", return_value=Path("python-disponible")), \
                patch.object(iniciar, "ejecutar", side_effect=OSError("Puerto ocupado")) as ejecutar:
            with self.assertRaises(SystemExit):
                iniciar.main()
            ejecutar.assert_called_once()

    def test_sin_entorno_utiliza_python_actual(self):
        with TemporaryDirectory() as carpeta, patch.object(iniciar, "RAIZ_PROYECTO", Path(carpeta)):
            self.assertEqual(Path(sys.executable), iniciar.python_disponible())

    def test_con_entorno_reutiliza_python_local(self):
        with TemporaryDirectory() as carpeta, patch.object(iniciar, "RAIZ_PROYECTO", Path(carpeta)):
            python = Path(carpeta) / ".venv-voz" / ("Scripts/python.exe" if iniciar.os.name == "nt" else "bin/python")
            python.parent.mkdir(parents=True)
            python.touch()
            self.assertEqual(python, iniciar.python_disponible())

    def test_servidor_real_abre_sin_modelos_tras_fallo_o_sin_descargas(self):
        # Usa el Python de las pruebas y una carpeta vacía para simular un equipo
        # que no tiene modelos; no instala paquetes ni abre ventanas del navegador.
        with TemporaryDirectory() as carpeta:
            for opcion in ("", "--sin-descargas"):
                with self.subTest(opcion=opcion), socket.socket() as reserva:
                    reserva.bind(("127.0.0.1", 0))
                    puerto = reserva.getsockname()[1]
                    reserva.close()
                    programa = (
                        "from unittest.mock import patch\nfrom pathlib import Path\nimport sys, runpy\n"
                        "from codigo.interfaz import iniciar\n"
                        "def abrir_servidor(*argumentos):\n"
                        "    sys.argv = ['servidor', *map(str, argumentos[3:])]\n"
                        "    runpy.run_module('codigo.interfaz.servidor', run_name='__main__')\n"
                        "patch('webbrowser.open').start()\n"
                        "patch.object(iniciar, 'ejecutar', side_effect=abrir_servidor).start()\n"
                        "patch.object(iniciar, 'preparar', side_effect=OSError('Sin conexion')).start()\n"
                        "patch.object(iniciar, 'python_disponible', return_value=Path(sys.executable)).start()\n"
                        "iniciar.main()"
                    )
                    proceso = subprocess.Popen(
                        [sys.executable, "-c", programa, "--puerto", str(puerto), *([opcion] if opcion else [])],
                        cwd=iniciar.RAIZ_PROYECTO,
                        env={**os.environ, "ZOONAUTA_VOCES_DIR": carpeta},
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    )
                    try:
                        limite = time.monotonic() + 15
                        while True:
                            try:
                                with urlopen(f"http://127.0.0.1:{puerto}/api/vista", timeout=1) as respuesta:
                                    vista = json.load(respuesta)
                                break
                            except OSError:
                                if proceso.poll() is not None or time.monotonic() >= limite:
                                    self.fail("El iniciador no abrió el servidor sin modelos de voz.")
                                time.sleep(0.1)
                        self.assertEqual(48, len(vista["catalogo_animales"]))
                        with urlopen(f"http://127.0.0.1:{puerto}/api/voz/config", timeout=2) as respuesta:
                            voces = json.load(respuesta)["voces"]
                        self.assertEqual(14, len(voces))
                        self.assertFalse(any(v["disponible"] for v in voces))
                        with urlopen(f"http://127.0.0.1:{puerto}/animales/A01.webp", timeout=2) as respuesta:
                            self.assertEqual(200, respuesta.status)
                    finally:
                        proceso.terminate()
                        proceso.communicate(timeout=5)
