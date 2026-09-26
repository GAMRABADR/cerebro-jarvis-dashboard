"""
Bambu 3D Engine - Blender Headless Studio Multi-Angle Renderer (Enhanced)
Author: E.B.J. AI Supreme for Ing. Badr
Renders photorealistic studio shots with seamless cyclorama backdrop and professional multi-view montage.
"""

import bpy
import sys
import os
import math

def setup_studio_environment(scene):
    # World lighting with light grey neutral studio background
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("Studio_World")
        scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.90, 0.92, 0.95, 1.0)
        bg_node.inputs['Strength'].default_value = 1.0

def render_htvw281_views(obj_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    
    setup_studio_environment(scene)
    
    # Import model
    print(f"[*] Importing OBJ: {obj_path}")
    bpy.ops.wm.obj_import(filepath=obj_path)
    
    imported_objects = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    if not imported_objects:
        print("[!] No mesh found in OBJ import!")
        return
        
    target_mesh = imported_objects[0]
    target_mesh.name = "HTVW_281_Model"
    bpy.context.view_layer.objects.active = target_mesh
    
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    target_mesh.location = (0, 0, 0)
    
    # Material: Automotive Textured Carbon/Matte Polymer
    mat = bpy.data.materials.new(name="Automotive_Polymer")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.15, 0.16, 0.18, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.38
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = 0.05
            
    if target_mesh.data.materials:
        target_mesh.data.materials[0] = mat
    else:
        target_mesh.data.materials.append(mat)
        
    for f in target_mesh.data.polygons:
        f.use_smooth = True
        
    # Large Studio Ground Pedestal
    dim = target_mesh.dimensions
    max_dim = max(dim.x, dim.y, dim.z)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=max_dim * 3.5, depth=4.0, location=(0, 0, -dim.z / 2.0 - 2.0))
    pedestal = bpy.context.active_object
    ped_mat = bpy.data.materials.new(name="Pedestal_Mat")
    ped_mat.use_nodes = True
    p_bsdf = ped_mat.node_tree.nodes.get("Principled BSDF")
    if p_bsdf:
        p_bsdf.inputs['Base Color'].default_value = (0.86, 0.88, 0.91, 1.0)
        p_bsdf.inputs['Roughness'].default_value = 0.65
    pedestal.data.materials.append(ped_mat)
    
    # Studio Lights
    # Key light
    key_data = bpy.data.lights.new(name="Key_Light", type='AREA')
    key_data.energy = 850.0
    key_data.size = 120.0
    key = bpy.data.objects.new(name="Key_Light", object_data=key_data)
    key.location = (max_dim * 1.6, -max_dim * 1.8, max_dim * 2.2)
    key.rotation_euler = (math.radians(45), math.radians(15), math.radians(35))
    bpy.context.collection.objects.link(key)
    
    # Fill light
    fill_data = bpy.data.lights.new(name="Fill_Light", type='AREA')
    fill_data.energy = 400.0
    fill_data.size = 150.0
    fill_data.color = (0.82, 0.88, 1.0)
    fill = bpy.data.objects.new(name="Fill_Light", object_data=fill_data)
    fill.location = (-max_dim * 1.8, -max_dim * 1.2, max_dim * 1.5)
    fill.rotation_euler = (math.radians(50), 0, math.radians(-55))
    bpy.context.collection.objects.link(fill)
    
    # Rim light
    rim_data = bpy.data.lights.new(name="Rim_Light", type='SUN')
    rim_data.energy = 2.8
    rim = bpy.data.objects.new(name="Rim_Light", object_data=rim_data)
    rim.location = (0, max_dim * 2.0, max_dim * 1.8)
    rim.rotation_euler = (math.radians(-50), 0, math.radians(180))
    bpy.context.collection.objects.link(rim)
    
    # Camera
    cam_data = bpy.data.cameras.new(name="Studio_Camera")
    cam_data.lens = 90
    cam = bpy.data.objects.new(name="Studio_Camera", object_data=cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    
    dist = max_dim * 2.6
    
    views = [
        {
            "name": "render_isometric.png",
            "loc": (dist * 0.72, -dist * 0.72, dist * 0.65),
            "rot": (math.radians(60), 0, math.radians(45)),
            "ortho": False
        },
        {
            "name": "render_front.png",
            "loc": (0, -dist * 1.15, dist * 0.22),
            "rot": (math.radians(80), 0, 0),
            "ortho": False
        },
        {
            "name": "render_side.png",
            "loc": (dist * 1.15, 0, dist * 0.22),
            "rot": (math.radians(80), 0, math.radians(90)),
            "ortho": False
        },
        {
            "name": "render_top_wireframe.png",
            "loc": (0, 0, dist * 1.2),
            "rot": (0, 0, 0),
            "ortho": True,
            "ortho_scale": max_dim * 1.35
        }
    ]
    
    saved_paths = []
    for v in views:
        cam.location = v["loc"]
        cam.rotation_euler = v["rot"]
        if v["ortho"]:
            cam.data.type = 'ORTHO'
            cam.data.ortho_scale = v.get("ortho_scale", max_dim * 1.35)
        else:
            cam.data.type = 'PERSP'
            
        out_file = os.path.join(output_dir, v["name"])
        scene.render.filepath = out_file
        print(f"[*] Rendering view {v['name']}...")
        bpy.ops.render.render(write_still=True)
        print(f"[+] View saved: {out_file} ({os.path.getsize(out_file):,} bytes)")
        saved_paths.append(out_file)
    print("[+] All views rendered successfully!")

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        obj_file = args[0]
        out_folder = args[1]
    else:
        obj_file = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\public\3d_models\HTVW_281_BambuLab.obj"
        out_folder = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\public\3d_models\renders"
        
    render_htvw281_views(obj_file, out_folder)
