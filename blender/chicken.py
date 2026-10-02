"""Render a top-down chicken sprite sheet with Blender (headless).

  /Applications/Blender.app/Contents/MacOS/Blender -b --python blender/chicken.py -- out_dir

Produces 8 frames of a hop cycle (walk + bob) seen from a steep camera, with a
soft shadow on a transparent background, plus a splat frame. Eevee, 256px.
"""
import math
import os
import sys

import bpy

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/chicken"
os.makedirs(OUT, exist_ok=True)
FRAMES = 8
SIZE = 256

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.types, "SceneEEVEE") and "BLENDER_EEVEE_NEXT" in [
    e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = SIZE
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.frame_start, scene.frame_end = 1, FRAMES


def mat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def sphere(name, loc, scale, m, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o


def cone(name, loc, rot, scale, m, parent=None):
    bpy.ops.mesh.primitive_cone_add(vertices=24, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o


white = mat("feathers", (0.95, 0.93, 0.88), 0.7)
red = mat("comb", (0.85, 0.08, 0.06), 0.4)
orange = mat("beak", (0.95, 0.55, 0.08), 0.4)
dark = mat("eye", (0.02, 0.02, 0.02), 0.3)

root = bpy.data.objects.new("chicken", None)
scene.collection.objects.link(root)
body = sphere("body", (0, 0, 0.55), (0.55, 0.42, 0.42), white, root)
tail = cone("tail", (-0.55, 0, 0.75), (0, math.radians(-120), 0), (0.22, 0.14, 0.35), white, root)
neck = sphere("neck", (0.45, 0, 0.85), (0.2, 0.2, 0.28), white, root)
head = sphere("head", (0.62, 0, 1.12), (0.24, 0.22, 0.24), white, root)
cone("comb", (0.58, 0, 1.38), (0, math.radians(90), 0), (0.08, 0.06, 0.16), red, root)
cone("wattle", (0.78, 0, 0.95), (math.radians(180), 0, 0), (0.06, 0.05, 0.12), red, root)
cone("beak", (0.9, 0, 1.1), (0, math.radians(90), 0), (0.07, 0.07, 0.16), orange, root)
sphere("eyeL", (0.74, 0.14, 1.18), (0.045, 0.045, 0.045), dark, root)
sphere("eyeR", (0.74, -0.14, 1.18), (0.045, 0.045, 0.045), dark, root)
wingL = sphere("wingL", (0, 0.38, 0.6), (0.38, 0.1, 0.26), white, root)
wingR = sphere("wingR", (0, -0.38, 0.6), (0.38, 0.1, 0.26), white, root)
legL = cone("legL", (0.05, 0.14, 0.15), (0, 0, 0), (0.035, 0.035, 0.18), orange, root)
legR = cone("legR", (0.05, -0.14, 0.15), (0, 0, 0), (0.035, 0.035, 0.18), orange, root)

# camera: steep look-down, like a pole camera, aimed at the bird (shadow is drawn in-game)
bpy.ops.object.camera_add(location=(0.7, -1.3, 4.6))
cam = bpy.context.object
cam.data.lens = 55
tgt = bpy.data.objects.new("target", None)
tgt.location = (0.15, 0, 0.75)
scene.collection.objects.link(tgt)
tr = cam.constraints.new("TRACK_TO")
tr.target = tgt
tr.track_axis, tr.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam
bpy.ops.object.light_add(type="SUN", location=(2, -2, 6), rotation=(math.radians(35), math.radians(10), math.radians(40)))
sun = bpy.context.object
sun.data.energy = 4.0
sun.data.angle = math.radians(6)
bpy.ops.object.light_add(type="AREA", location=(-2, 2, 4))
fill = bpy.context.object
fill.data.energy = 150
fill.data.size = 4

# hop cycle animation
for f in range(1, FRAMES + 1):
    ph = (f - 1) / FRAMES * 2 * math.pi
    root.location.z = max(0, math.sin(ph)) * 0.35
    root.rotation_euler.y = math.radians(-8) * math.sin(ph)
    root.keyframe_insert("location", frame=f)
    root.keyframe_insert("rotation_euler", frame=f)
    legL.rotation_euler.y = math.radians(35) * math.sin(ph)
    legR.rotation_euler.y = -math.radians(35) * math.sin(ph)
    legL.keyframe_insert("rotation_euler", frame=f)
    legR.keyframe_insert("rotation_euler", frame=f)
    for w, s in ((wingL, 1), (wingR, -1)):
        w.rotation_euler.x = s * math.radians(25) * max(0, math.sin(ph))
        w.keyframe_insert("rotation_euler", frame=f)

for f in range(1, FRAMES + 1):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(OUT, f"hop_{f:02d}.png")
    bpy.ops.render.render(write_still=True)

# splat frame: flattened, wings out, feathers
scene.frame_set(1)
root.animation_data_clear()
root.location.z = 0
root.rotation_euler = (0, 0, 0)
root.scale = (1.25, 1.35, 0.3)
for w, s in ((wingL, 1), (wingR, -1)):
    w.animation_data_clear()
    w.rotation_euler = (0, 0, s * math.radians(60))
    w.location.y = s * 0.7
scene.render.filepath = os.path.join(OUT, "splat.png")
bpy.ops.render.render(write_still=True)
print("rendered to", OUT)
