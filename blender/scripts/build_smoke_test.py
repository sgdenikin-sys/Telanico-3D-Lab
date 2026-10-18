"""Build an editable, road-free tabletop island for the Telanico 3D Lab.

Usage, from the repository root:
    blender --background --python blender/scripts/build_smoke_test.py

Works without third-party assets, add-ons, or a GPU. Generated files are ignored
by Git: Blender source in blender/generated/, GLB in godot/assets/generated/.
"""
from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
BLEND_FILE = ROOT / "blender" / "generated" / "smoke_test.blend"
GLB_FILE = ROOT / "godot" / "assets" / "generated" / "smoke_test.glb"


def material(name, color, roughness=0.78):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Roughness"].default_value = roughness
    return mat


def cube(name, location, dimensions, mat, radius=0.05):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if radius > 0:
        modifier = obj.modifiers.new("Soft edges", "BEVEL")
        modifier.width = radius
        modifier.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        normal = obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def cylinder(name, location, radius, depth, mat, vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def sphere(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    stone = material("warm boardgame stone", (0.38, 0.37, 0.34))
    earth = material("island soil", (0.49, 0.42, 0.33))
    grass = material("muted sage grass", (0.43, 0.56, 0.43))
    wall = material("warm ivory office", (0.76, 0.72, 0.62))
    roof = material("slate teal roof", (0.20, 0.35, 0.38))
    accents = material("bronze trim", (0.57, 0.43, 0.25), roughness=0.55)
    window = material("dark blue glass", (0.17, 0.30, 0.38), roughness=0.32)
    wood = material("tree bark", (0.39, 0.31, 0.24))
    leaves = material("soft forest green", (0.28, 0.44, 0.34))

    # Small circular raised diorama. This is NOT a road network.
    cylinder("Boardgame display base", (0, 0, -0.18), 4.7, 0.36, stone)
    cylinder("Island earth", (0, 0, 0.02), 4.5, 0.28, earth)
    cylinder("Island grass top", (0, 0, 0.18), 4.4, 0.10, grass)

    # A single office: abstract blocks will be replaced with curated assets.
    cube("Settlements Hall body", (0.0, 0.20, 1.10), (2.70, 2.0, 1.70), wall)
    cube("Settlements Hall roof", (0.0, 0.20, 2.04), (3.05, 2.30, 0.28), roof, 0.09)
    cube("Main door", (0.0, -0.825, 0.73), (0.55, 0.08, 0.98), wood, 0.02)
    cube("Office left window", (-0.85, -0.83, 1.18), (0.47, 0.08, 0.57), window, 0.03)
    cube("Office right window", (0.85, -0.83, 1.18), (0.47, 0.08, 0.57), window, 0.03)
    cube("Entrance canopy", (0, -1.02, 1.36), (0.96, 0.6, 0.10), accents, 0.03)
    cube("Hall signboard", (0, -0.84, 1.73), (1.35, 0.09, 0.18), accents, 0.02)

    # Smaller companion office, set forward/right with a clear gap to the hall.
    cube("Trade Office body", (2.25, -1.15, 0.83), (1.30, 1.20, 1.20), wall)
    cube("Trade Office roof", (2.25, -1.15, 1.52), (1.52, 1.42, 0.20), roof, 0.07)
    cube("Trade Office door", (2.04, -1.78, 0.61), (0.36, 0.07, 0.76), wood, 0.02)
    cube("Trade Office window", (2.60, -1.78, 0.97), (0.34, 0.07, 0.40), window, 0.025)
    cube("Trade Office canopy", (2.04, -1.91, 1.06), (0.60, 0.40, 0.08), accents, 0.025)
    cube("Trade Office signboard", (2.25, -1.78, 1.31), (0.80, 0.07, 0.12), accents, 0.02)

    # Uncluttered background landscaping.
    for number, (x, y, height) in enumerate(
        [(-3.10, -1.2, 1.15), (-2.8, 2.1, 0.9),
         (2.8, 1.65, 1.22), (0.95, -3.15, 0.82)], start=1
    ):
        cylinder(f"Tree {number:02d} trunk", (x, y, 0.47), 0.13, 0.49, wood, 10)
        sphere(
            f"Tree {number:02d} foliage", (x, y, 0.77 + height * 0.35),
            (0.45 * height, 0.45 * height, 0.58 * height), leaves
        )

    # Camera/lighting remain editable in Blender; they are omitted from GLB.
    bpy.ops.object.camera_add(location=(7.3, -9.5, 8.5))
    camera = bpy.context.object
    camera.name = "Diorama preview camera"
    camera.rotation_euler = (
        Vector((0, 0, 0.95)) - camera.location
    ).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 11.5
    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(-3, -4, 9))
    key = bpy.context.object
    key.name = "Warm studio key"
    key.data.energy = 1100
    key.data.shape = "DISK"
    key.data.size = 8

    BLEND_FILE.parent.mkdir(parents=True, exist_ok=True)
    GLB_FILE.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_FILE))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB_FILE),
        export_format="GLB",
        export_cameras=False,
        export_lights=False,
    )
    assert BLEND_FILE.is_file() and BLEND_FILE.stat().st_size > 1000
    assert GLB_FILE.is_file() and GLB_FILE.stat().st_size > 1000
    print(f"TELANICO_OK blend={BLEND_FILE}")
    print(f"TELANICO_OK glb={GLB_FILE}")


if __name__ == "__main__":
    main()
