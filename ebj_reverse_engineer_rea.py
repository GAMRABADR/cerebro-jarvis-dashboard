# -*- coding: utf-8 -*-
"""
==============================================================================
🔍 EBJ REA REVERSE ENGINEERING & ARTCRAFT RUST SUITE ENGINE
==============================================================================
Ponte operativo tra EBJ e il toolkit REA (Reverse Engineer Anything):
  - Analisi PE Windows (.exe / .dll), binari Rust e .NET
  - Decompilazione e recupero sorgenti JavaScript / Electron (ASAR)
  - Integrazione con la suite di 13 app creative in Rust di ArtCraft via MCP
==============================================================================
"""

from __future__ import annotations
import os
import sys
import json
import time
import subprocess
import urllib.request
import zipfile
from typing import Dict, Any, List, Optional

REA_CMD = r"D:\home\badr1988\.npm-global\rea.cmd"

ARTCRAFT_APPS = {
    "photocraft": {"name": "Photocraft", "role": "Alternativa a Photoshop in pure Rust", "category": "Raster Image Editing", "mcp": True},
    "vectorcraft": {"name": "Vectorcraft", "role": "Alternativa a Illustrator in pure Rust", "category": "Vector Illustration", "mcp": True},
    "cadcraft": {"name": "CADCraft", "role": "Alternativa ad AutoCAD 2D/3D in pure Rust", "category": "CAD Design", "mcp": True},
    "gridcraft": {"name": "Gridcraft", "role": "Alternativa a Microsoft Excel in pure Rust", "category": "Spreadsheets", "mcp": True},
    "wordcraft": {"name": "Wordcraft", "role": "Alternativa a Microsoft Word in pure Rust", "category": "Document Processing", "mcp": True},
    "deckcraft": {"name": "Deckcraft", "role": "Alternativa a PowerPoint in pure Rust", "category": "Presentations", "mcp": True},
    "pdfcraft": {"name": "PDFcraft", "role": "Alternativa ad Adobe Acrobat in pure Rust", "category": "PDF Reader & Editor", "mcp": True},
    "filmcraft": {"name": "Filmcraft", "role": "Alternativa a Premiere in pure Rust", "category": "Video Editing", "mcp": True},
    "figcraft": {"name": "Figcraft", "role": "Alternativa a Figma in pure Rust", "category": "UI & Interface Design", "mcp": True},
    "soundcraft": {"name": "Soundcraft", "role": "Alternativa ad Audition in pure Rust", "category": "Multi-track Audio", "mcp": True},
    "lightcraft": {"name": "Lightcraft", "role": "Alternativa a Lightroom in pure Rust", "category": "Photo Workflow", "mcp": True},
    "effectcraft": {"name": "Effectcraft", "role": "Alternativa ad After Effects in pure Rust", "category": "Motion Graphics", "mcp": True},
    "designcraft": {"name": "Designcraft", "role": "Alternativa a InDesign in pure Rust", "category": "Page Layout", "mcp": True}
}

def is_rea_available() -> bool:
    """Verifica se l'eseguibile di REA è presente sul sistema."""
    return os.path.exists(REA_CMD)

def run_rea_command(subcommand: str, target_path: str, extra_args: Optional[List[str]] = None, timeout_s: float = 30.0) -> Dict[str, Any]:
    """Esegue un comando REA e restituisce il risultato formattato."""
    t0 = time.perf_counter()
    if not is_rea_available():
        return {
            "status": "ERROR",
            "message": f"Eseguibile REA non trovato in {REA_CMD}",
            "latency_ms": 0.0
        }

    cmd = [REA_CMD, subcommand, target_path]
    if extra_args:
        cmd.extend(extra_args)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, shell=True)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        latency = (time.perf_counter() - t0) * 1000.0

        return {
            "status": "SUCCESS" if proc.returncode == 0 else "PARTIAL_OR_ERROR",
            "exit_code": proc.returncode,
            "subcommand": subcommand,
            "target": target_path,
            "stdout": stdout,
            "stderr": stderr,
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        return {
            "status": "EXCEPTION",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
        }

def inspect_pe_file(pe_path: str) -> Dict[str, Any]:
    """Ispezione completa di un eseguibile Windows .exe o libreria .dll tramite REA."""
    return run_rea_command("inspect-artifact", pe_path)

def inspect_binary_layout(binary_path: str) -> Dict[str, Any]:
    """Ispezione del layout binario (sezioni, header, offset)."""
    return run_rea_command("inspect-binary-layout", binary_path)

def inspect_rust_binary(binary_path: str) -> Dict[str, Any]:
    """Ispezione delle dipendenze auditable e crate embeddate in un binario Rust."""
    return run_rea_command("inspect-rust-binary", binary_path)

def analyze_javascript_application(app_path: str) -> Dict[str, Any]:
    """Analisi di una web app o applicazione Electron decompilata."""
    return run_rea_command("analyze-javascript-application", app_path, extra_args=["--json"])

def recover_javascript_sources(asar_or_bundle: str, output_directory: str) -> Dict[str, Any]:
    """Ricostruisce i sorgenti leggibili da un archivio Electron ASAR o bundle compresso."""
    os.makedirs(output_directory, exist_ok=True)
    return run_rea_command("recover-javascript-sources", asar_or_bundle, extra_args=[output_directory])

def get_artcraft_suite() -> Dict[str, Any]:
    """Restituisce il catalogo delle 13 applicazioni ArtCraft in pure Rust controllabili via MCP."""
    return {
        "status": "SUCCESS",
        "total_apps": len(ARTCRAFT_APPS),
        "apps": ARTCRAFT_APPS,
        "pure_rust": True,
        "native_mcp_supported": True,
        "official_site": "https://getartcraft.com/apps",
        "github_launcher": "https://github.com/storytold/craft-launcher"
    }

def download_artcraft_launcher(destination_folder: str = "D:\\ArtCraft") -> Dict[str, Any]:
    """Scarica e predispone la versione portatile Windows x64 di ArtCraft Launcher."""
    t0 = time.perf_counter()
    os.makedirs(destination_folder, exist_ok=True)
    zip_path = os.path.join(destination_folder, "artcraft-launcher-windows-x64-portable.zip")
    launcher_exe = os.path.join(destination_folder, "artcraft-launcher.exe")

    if os.path.exists(launcher_exe):
        return {
            "status": "EXISTS",
            "message": "ArtCraft Launcher già presente e pronto all'uso.",
            "path": launcher_exe,
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
        }

    download_url = "https://github.com/storytold/craft-launcher/releases/download/v0.4.1/artcraft-launcher-0.4.1-windows-x64-portable.zip"
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) EBJ-Supreme')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(download_url, zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(destination_folder)

        return {
            "status": "SUCCESS",
            "message": "ArtCraft Launcher scaricato ed estratto con successo.",
            "destination": destination_folder,
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "download_url": download_url
        }

if __name__ == "__main__":
    print("=== TEST EBJ REA REVERSE ENGINEERING CONNECTOR ===")
    print("REA Disponibile:", is_rea_available())
    suite = get_artcraft_suite()
    print(f"Suite ArtCraft Caricata: {suite['total_apps']} applicazioni in Pure Rust.")
    for k, v in list(suite["apps"].items())[:4]:
        print(f" -> {v['name']}: {v['role']} ({v['category']})")
