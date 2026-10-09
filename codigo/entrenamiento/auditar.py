"""Contrastar todos los cierres con las métricas y posteriores guardadas."""
import argparse
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev


def auditar(p: Path) -> dict:
    s = json.loads((p / "resumen_experimentos.json").read_text(encoding="utf-8"))
    assert not set(s["semillas_entrenamiento"]) & set(s["semillas_evaluacion"]), "Semillas solapadas."
    total_observaciones = 0
    corridas_eval = []
    paths = sorted(p.glob("observaciones_*.jsonl.gz"))
    esperados = len(s["modelos"]) * 4
    assert len(paths) == esperados, "Esta revisión requiere los registros completos de cada corrida."
    for path in paths:
        idrun = path.name.removeprefix("observaciones_").removesuffix(".jsonl.gz")
        corrida = json.loads((p / "corridas" / f"{idrun}.json").read_text(encoding="utf-8"))
        ids = set()
        counts = Counter()
        por_clave = defaultdict(Counter)
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                assert r["observacion_id"] not in ids, f"Observación duplicada en {idrun}."
                ids.add(r["observacion_id"])
                y = r["resultado"]
                key = "sin_etiqueta" if y is None else f"y{y}"
                counts[key] += 1
                z = r["contexto"]
                v = r["variante_id"]
                clave = (z["habitat_guia_id"], z["nivel"], z["repeticion_previa"], v)
                por_clave[clave][key] += 1
                if y == 0: assert r["evento_cierre"] == "NUEVA_AYUDA"
                if y == 1: assert r["evento_cierre"] == "SELECCION_VALIDA"
                if y is None: assert r["evento_cierre"] in {"SELECCION_PENDIENTE", "SALIDA"}
                assert v in r["variantes_elegibles"]
                if r["politica"] != "ID3" and r["variante_anterior"]:
                    assert v != r["variante_anterior"]
                if idrun.startswith("EVAL_"):
                    assert r["origen"] == "SIMULACION_EVALUACION"
                    assert r["modelo_actualizado"] is False
                    assert r["decision"]["parametros_congelados"] is True
                else:
                    assert r["origen"] == "SIMULACION_ENTRENAMIENTO"
                    assert r["modelo_actualizado"] == (y is not None)
        assert len(ids) == corrida["ayudas"], f"Ayudas y cierres no coinciden en {idrun}."
        total_observaciones += len(ids)
        for key in ("y0", "y1", "sin_etiqueta"):
            assert counts[key] == corrida.get(key, 0), f"Conteo inconsistente en {idrun}."
        if idrun.startswith("TRAIN_"):
            modelo = json.loads((p / "modelos" / f"{idrun.removeprefix('TRAIN_')}.json").read_text(encoding="utf-8"))
            assert modelo["actualizaciones"] == counts["y0"] + counts["y1"]
            assert modelo["cierres_sin_etiqueta"] == counts["sin_etiqueta"]
            for r in modelo["items"]:
                z = r["contexto"]
                clave = (z["habitat_guia_id"], z["nivel"], z["repeticion_previa"], r["variante_id"])
                assert r["alpha"] == 1 + por_clave[clave]["y1"]
                assert r["beta"] == 1 + por_clave[clave]["y0"]
        else:
            etiquetas = counts["y0"] + counts["y1"]
            if etiquetas:
                assert math.isclose(corrida["tasa_y1_etiquetadas"], counts["y1"] / etiquetas)
            corridas_eval.append(corrida)
    for modelo in s["modelos"]:
        assert hashlib.sha256((p / modelo["ruta"]).read_bytes()).hexdigest() == modelo["sha256"]
    for agregado in s["agregado"]:
        rows = [r for r in corridas_eval if r["condicion"] == agregado["condicion"]
                and r["politica"] == agregado["politica"]]
        assert len(rows) == s["configuracion"]["replicas"]
        valores = [r["tasa_y1_etiquetadas"] for r in rows if r["tasa_y1_etiquetadas"] is not None]
        if valores:
            assert math.isclose(mean(valores), agregado["tasa_y1_etiquetadas"]["media"])
            desviacion = stdev(valores) if len(valores) > 1 else 0.0
            assert math.isclose(desviacion, agregado["tasa_y1_etiquetadas"]["desviacion_entre_semillas"])
    return {"resultado": "CORRECTO", "archivos_de_observaciones": len(paths),
            "observaciones_cerradas_comprobadas": total_observaciones,
            "modelos_reconciliados": len(s["modelos"]), "corridas_evaluacion": len(corridas_eval),
            "parametros_evaluacion_congelados": True, "actualizaciones_unicas": True,
            "semillas_separadas": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resultados", type=Path, default=Path("docs/experimentos"))
    args = parser.parse_args()
    revision = auditar(args.resultados)
    (args.resultados / "revision_experimentos.json").write_text(
        json.dumps(revision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(revision, ensure_ascii=False))


if __name__ == "__main__":
    main()

