"""PreToolUse (Bash y PowerShell): bloquea ordenes de git que pueden destruir o publicar trabajo ajeno."""
import json
import re
import sys

PROHIBIDO = [
    (r"\bgit\s+add\s+(-A\b|--all\b|\.(\s|$))", "git add masivo: anade rutas explicitas"),
    (r"\bgit\s+commit\b[^|;&]*\s(-[a-zA-Z]*a[a-zA-Z]*|--all)\b", "git commit -a: anade rutas explicitas"),
    (r"\bgit\s+commit\b[^|;&]*--amend", "--amend reescribe historial"),
    (r"\bgit\s+reset\s+--hard", "reset --hard prohibido"),
    (r"\bgit\s+clean\b", "git clean prohibido"),
    (r"\bgit\s+push\b", "push requiere autorizacion del propietario"),
    (r"\bgit\s+checkout\b[^|;&]*\s--(\s|$)", "checkout que descarta cambios prohibido"),
    (r"\bgit\s+checkout\s+\.", "checkout . prohibido"),
    (r"\bgit\s+stash\b", "stash prohibido: hay cambios del propietario sin confirmar"),
    (r"\bgit\s+restore\b", "git restore puede descartar cambios ajenos"),
]


def main():
    try:
        orden = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except Exception:
        return 0
    for patron, motivo in PROHIBIDO:
        if re.search(patron, orden):
            print(f"Bloqueado por el proyecto: {motivo}. Pidelo al propietario si es necesario.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
