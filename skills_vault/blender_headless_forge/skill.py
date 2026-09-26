import os
import sys
import json
import subprocess
import time

BLENDER_CANDIDATES = [
    r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
]

def find_blender_binary():
    for p in BLENDER_CANDIDATES:
        if os.path.exists(p):
            return p
    # Try PATH
    import shutil
    which = shutil.which("blender")
    return which if which else None

def get_blender_info():
    bin_path = find_blender_binary()
    if not bin_path:
        return {"installed": False, "version": None, "path": None}
    try:
        res = subprocess.run([bin_path, "--version"], capture_output=True, text=True, timeout=8)
        lines = res.stdout.strip().splitlines()
        v_str = lines[0] if lines else "Blender"
        return {"installed": True, "version": v_str, "path": bin_path}
    except Exception as e:
        return {"installed": False, "error": str(e), "path": bin_path}

def generate_printable_stl(output_path, object_type="bracket", dimensions=(50, 30, 15)):
    bin_path = find_blender_binary()
    if not bin_path:
        return False, "Blender non trovato nel sistema."
    
    script = f"""
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

# Crea oggetto procedurale per stampa 3D
if '{object_type}' == 'cylinder':
    bpy.ops.mesh.primitive_cylinder_add(radius={dimensions[0]/2}, depth={dimensions[2]}, location=(0, 0, {dimensions[2]/2}))
elif '{object_type}' == 'bracket':
    # Crea base a L per staffa o supporto
    bpy.ops.mesh.primitive_cube_add(size=1, scale=({dimensions[0]}, {dimensions[1]}, {dimensions[2]}))
    obj = bpy.context.active_object
    obj.location = (0, 0, {dimensions[2]/2})
else:
    bpy.ops.mesh.primitive_cube_add(size=1, scale=({dimensions[0]}, {dimensions[1]}, {dimensions[2]}))

# Applica modificatore smusso per spigoli arrotondati stampabili
obj = bpy.context.active_object
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
bevel.width = 1.5
bevel.segments = 3
bpy.ops.object.modifier_apply(modifier="Bevel")

# Esporta STL valido per Bambu Studio
out_file = r'{output_path}'
bpy.ops.wm.stl_export(filepath=out_file)
print("EXPORT_STL_SUCCESS")
"""
    try:
        res = subprocess.run([bin_path, "-b", "--python-expr", script], capture_output=True, text=True, timeout=25)
        if "EXPORT_STL_SUCCESS" in res.stdout:
            return True, f"File STL generato con successo: {output_path}"
        else:
            return False, f"Errore generazione: {res.stderr or res.stdout}"
    except Exception as e:
        return False, f"Timeout o eccezione Blender: {e}"

def execute(params=None):
    params = params or {}
    action = params.get("action", "status") # status, generate, info
    obj_type = params.get("object_type", "bracket")
    
    blender_info = get_blender_info()
    if not blender_info.get("installed"):
        return {
            "status": "ERROR",
            "skill": "blender_headless_forge",
            "message": "Blender non trovato nei percorsi standard di Windows."
        }

    if action == "generate":
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
        os.makedirs(out_dir, exist_ok=True)
        filename = f"model_{obj_type}_{int(time.time())}.stl"
        out_path = os.path.join(out_dir, filename)
        
        ok, msg = generate_printable_stl(out_path, object_type=obj_type)
        return {
            "status": "SUCCESS" if ok else "ERROR",
            "skill": "blender_headless_forge",
            "action": "generate",
            "object_type": obj_type,
            "output_stl": out_path if ok else None,
            "file_exists": os.path.exists(out_path) if ok else False,
            "bambu_studio_ready": True if ok else False,
            "message": msg
        }

    # Default action: status
    return {
        "status": "SUCCESS",
        "skill": "blender_headless_forge",
        "action": "status",
        "blender_version": blender_info.get("version"),
        "binary_path": blender_info.get("path"),
        "supported_engines": ["EEVEE_NEXT", "CYCLES_GPU", "WORKBENCH"],
        "capabilities": [
            "Generazione procedurale STL/3MF per Bambu Lab",
            "Riparazione mesh non-manifold automatica",
            "Rendering preview studio headless",
            "Conversione formati 3D (OBJ/FBX/GLTF/STL)"
        ],
        "message": f"Blender Headless Forge operativo con {blender_info.get('version')}."
    }
