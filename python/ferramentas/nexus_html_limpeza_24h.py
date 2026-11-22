#!/usr/bin/env python3
# NEXUS - Limpeza automática 24h - Roda dentro do Render, sem Secrets novas
# Apaga do disco + do Realtime só o que já tem mais de 24h e não tem _manter
import sys
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
GERADOS_DIR = BASE_DIR / "html" / "html_gerados"
LIMITE_SEGUNDOS = 24 * 60 * 60

def main():
    if not GERADOS_DIR.exists():
        print("📭 Pasta html_gerados não existe")
        return 0
    agora = time.time()
    apagados = []
    mantidos = []
    for arquivo in GERADOS_DIR.glob("*.html"):
        nome = arquivo.name
        if "_manter" in nome.lower():
            mantidos.append(nome)
            continue
        idade = agora - arquivo.stat().st_mtime
        if idade < LIMITE_SEGUNDOS:
            mantidos.append(f"{nome} ({int(idade//3600)}h)")
            continue
        # Chama o excluir que já apaga do disco + Realtime
        excluir_script = BASE_DIR / "python" / "ferramentas" / "nexus_html_excluir.py"
        proc = subprocess.run(
            [sys.executable, str(excluir_script), nome],
            capture_output=True, text=True, timeout=120
        )
        print(f"🗑️ {nome} - {proc.stdout.strip()[:200]}")
        apagados.append(nome)
    print(f"✅ Limpeza 24h: {len(apagados)} apagados, {len(mantidos)} mantidos")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
