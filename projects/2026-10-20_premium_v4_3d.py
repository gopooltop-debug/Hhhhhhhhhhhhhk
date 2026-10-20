"""«Премиум» v4 — 3D: кошелёк смоделирован в Blender (bpy 5.2, Cycles) по кадрам исходника
и снят «камерой» по сценарию референса «iPhone 17 Pro — 3D Animation #blender».

Модель: скруглённый брусок 9,6×11,2×1,6 см, на лицевой и обратной стороне — кожа с кадра 891 с
(перспектива выпрямлена, свет выровнен), рельеф чешуи из той же картинки, прострочка по краю, гладкая кромка.

  0,00–1,20  чёрный, маленький кошелёк; на 0,65 включается оранжевый контровой свет
  1,20–3,65  наезд: камера вплотную у ребра, медленный облёт, тёплый контур
  3,70–7,45  угол с прострочкой крупно, кошелёк поворачивается, белый софтбокс проходит по коже, свет гаснет
  7,50–11,25 два кошелька, свет поднимается снизу, вспышка, гаснет
  11,28–16,40 студия: серый фон, каменный пол; кошелёк стоит в воздухе, оборот 360°, сзади выезжает второй
  16,43–17,53 знак на чёрном (2D)

Звук — дорожка референса (по просьбе заказчика).

Запуск (по шагам, рендер долгий — можно частями):
  python3 projects/2026-10-20_premium_v4_3d.py prep IMG_7542.MOV            # текстуры
  python3 projects/2026-10-20_premium_v4_3d.py render [с_кадра] [по_кадр] [--preview]
  python3 projects/2026-10-20_premium_v4_3d.py compose референс.mp4         # титры, звук, сборка
"""
import math
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = "output"
NAME = "2026-10-20_премиум_v4_3d"
WORK = os.path.join(OUT_DIR, "_work", "premium_v4")
FR = os.path.join(WORK, "frames")
W, H, FPS = 1080, 1920, 30
TOTAL, LOGO_T = 17.53, 16.43
N_FRAMES = int(round(TOTAL * FPS))

# размеры кошелька (дм — Blender любит величины порядка единицы)
WW, WH, WT = 0.96, 1.12, 0.16
FACE_T = 891.0                         # кадр с лицевой стороной
FACE_QUAD = [[112, 602], [634, 548], [790, 1140], [176, 1250]]   # углы лица (по часовой с левого верхнего)
GROUND_T = 365.0                       # кадр с пустым гранитом


def clamp01(x):
    return float(min(1.0, max(0.0, x)))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    return 1 - (1 - clamp01(x)) ** 3


def ramp(t, t0, t1):
    return smooth((t - t0) / (t1 - t0))


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ шаг 1: текстуры
def prep(src):
    import cv2
    os.makedirs(WORK, exist_ok=True)

    def grab(t):
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1",
                            "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True)
        return np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3).copy()

    TW, TH = 960, 1120
    M = cv2.getPerspectiveTransform(np.float32(FACE_QUAD), np.float32([[0, 0], [TW, 0], [TW, TH], [0, TH]]))
    face = cv2.warpPerspective(grab(FACE_T), M, (TW, TH), flags=cv2.INTER_CUBIC)
    y = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    flat = np.clip(y / (cv2.GaussianBlur(y, (0, 0), 45) + 0.02), 0, 4)          # свет выровнен
    band = cv2.GaussianBlur(flat, (0, 0), 2.2) - cv2.GaussianBlur(flat, (0, 0), 22)
    band = band / (cv2.GaussianBlur(np.abs(band), (0, 0), 40) * 3 + 1e-4)
    groove = np.clip(band, 0, 1)                                                 # бороздки — светлые линии
    h = cv2.GaussianBlur(1 - groove, (0, 0), 1.8)                                # чешуйки выпуклые, бороздки ниже
    h = (h - h.min()) / (h.max() - h.min())
    cv2.imwrite(os.path.join(WORK, "height.png"), (h * 65535).astype(np.uint16))
    alb = np.clip(0.035 + 0.05 * np.clip(flat * 0.12, 0, 1) + 0.02 * (1 - h), 0, 1)
    cv2.imwrite(os.path.join(WORK, "albedo.png"), (np.dstack([alb, alb, alb * 1.03]) * 255).astype(np.uint8))
    stone = cv2.cvtColor(grab(GROUND_T), cv2.COLOR_BGR2GRAY)[300:1700, :]
    cv2.imwrite(os.path.join(WORK, "stone.png"), stone)
    print("текстуры готовы:", WORK)


# ------------------------------------------------------------------ шаг 2: сцена Blender
def build():
    import bpy
    import bmesh

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 0
    sc.cycles.transparent_max_bounces = 0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.use_persistent_data = False   # с True после ~100 кадров кожа рендерится чёрной
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.image_settings.file_format = "PNG"
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    sc.world = world

    def img(name, noncolor=False):
        im = bpy.data.images.load(os.path.abspath(os.path.join(WORK, name)))
        if noncolor:
            im.colorspace_settings.name = "Non-Color"
        return im

    # --- материал кожи: лицо/оборот — чешуя по координатам объекта, бока — гладкая кромка
    mat = bpy.data.materials.new("croc")
    mat.use_nodes = True
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    mp.inputs["Scale"].default_value = (1 / WW, 1 / WH, 1)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    t_alb = N.new("ShaderNodeTexImage")
    t_alb.image = img("albedo.png")
    t_alb.extension = "EXTEND"
    t_h = N.new("ShaderNodeTexImage")
    t_h.image = img("height.png", True)
    t_h.extension = "EXTEND"
    for t in (t_alb, t_h):
        L.new(mp.outputs["Vector"], t.inputs["Vector"])
    # мелкие поры поверх
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 900
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    hmix = N.new("ShaderNodeMath")
    hmix.operation = "MULTIPLY_ADD"
    hmix.inputs[1].default_value = 0.015
    L.new(nz.outputs["Fac"], hmix.inputs[0])
    L.new(t_h.outputs["Color"], hmix.inputs[2])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.004
    L.new(hmix.outputs["Value"], bump.inputs["Height"])
    face = N.new("ShaderNodeBsdfPrincipled")
    L.new(t_alb.outputs["Color"], face.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.42
    rr.inputs["To Max"].default_value = 0.20
    L.new(t_h.outputs["Color"], rr.inputs["Value"])
    L.new(rr.outputs["Result"], face.inputs["Roughness"])
    face.inputs["Coat Weight"].default_value = 0.35
    face.inputs["Coat Roughness"].default_value = 0.12
    L.new(bump.outputs["Normal"], face.inputs["Normal"])
    L.new(bump.outputs["Normal"], face.inputs["Coat Normal"])
    edge = N.new("ShaderNodeBsdfPrincipled")
    edge.inputs["Base Color"].default_value = (0.018, 0.017, 0.017, 1)
    edge.inputs["Roughness"].default_value = 0.30
    edge.inputs["Coat Weight"].default_value = 0.2
    geo = N.new("ShaderNodeNewGeometry")
    vt = N.new("ShaderNodeVectorTransform")
    vt.vector_type = "NORMAL"
    vt.convert_from = "WORLD"
    vt.convert_to = "OBJECT"
    L.new(geo.outputs["Normal"], vt.inputs["Vector"])
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(vt.outputs["Vector"], sep.inputs["Vector"])
    ab = N.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    L.new(sep.outputs["Z"], ab.inputs[0])
    fac = N.new("ShaderNodeMapRange")
    fac.inputs["From Min"].default_value = 0.55
    fac.inputs["From Max"].default_value = 0.85
    L.new(ab.outputs["Value"], fac.inputs["Value"])
    mix = N.new("ShaderNodeMixShader")
    L.new(fac.outputs["Result"], mix.inputs["Fac"])
    L.new(edge.outputs["BSDF"], mix.inputs[1])
    L.new(face.outputs["BSDF"], mix.inputs[2])
    L.new(mix.outputs["Shader"], out.inputs["Surface"])

    thread = bpy.data.materials.new("thread")
    thread.use_nodes = True
    p = thread.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1)
    p.inputs["Roughness"].default_value = 0.35

    def make_wallet(name):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= WW
            v.co.y *= WH
            v.co.z *= WT
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width = 0.055
        bv.segments = 8
        bv.limit_method = "NONE"
        ob.data.materials.append(mat)
        for poly in ob.data.polygons:
            poly.use_smooth = True
        # прострочка: ряд «стежков» по периметру лица и оборота
        sm = bpy.data.meshes.new(name + "_st")
        bm = bmesh.new()
        inset = 0.036
        ax, ay = WW / 2 - inset, WH / 2 - inset
        per = 4 * (ax + ay)
        n = int(per / 0.017)
        for zs in (1, -1):
            for i in range(n):
                s = i / n * per
                if s < 2 * ax:
                    x, y, ang = -ax + s, ay, 0
                elif s < 2 * ax + 2 * ay:
                    x, y, ang = ax, ay - (s - 2 * ax), math.pi / 2
                elif s < 4 * ax + 2 * ay:
                    x, y, ang = ax - (s - 2 * ax - 2 * ay), -ay, 0
                else:
                    x, y, ang = -ax, -ay + (s - 4 * ax - 2 * ay), math.pi / 2
                r = bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=1.0)
                vs = r["verts"]
                ca, sa = math.cos(ang), math.sin(ang)
                for v in vs:
                    lx, ly, lz = v.co.x * 0.0062, v.co.y * 0.0022, v.co.z * 0.0014
                    v.co.x = x + lx * ca - ly * sa
                    v.co.y = y + lx * sa + ly * ca
                    v.co.z = zs * (WT / 2 + 0.0005) + lz
        bm.to_mesh(sm)
        bm.free()
        st = bpy.data.objects.new(name + "_st", sm)
        sc.collection.objects.link(st)
        st.parent = ob
        st.data.materials.append(thread)
        return ob, st

    w1 = make_wallet("w1")
    w2 = make_wallet("w2")

    def area(name, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.size = size
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        ob.visible_camera = False   # обратная сторона плоской лампы в кадре — чёрная полоса
        sc.collection.objects.link(ob)
        return ob

    lights = {
        "key": area("key", 2.5),
        "rimL": area("rimL", 1.2, (1.0, 0.36, 0.08)),
        "rimR": area("rimR", 1.2, (1.0, 0.36, 0.08)),
        "fill": area("fill", 3.0),
        "under": area("under", 4.0),
        "sweep": area("sweep", 0.5),
    }
    lights["sweep"].data.shape = "RECTANGLE"
    lights["sweep"].data.size = 6.0
    lights["sweep"].data.size_y = 0.35

    # студия: светящийся серый фон и каменный пол
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 14, 6), rotation=(math.radians(90), 0, 0))
    back = bpy.context.object
    bm_ = bpy.data.materials.new("back")
    bm_.use_nodes = True
    n2, l2 = bm_.node_tree.nodes, bm_.node_tree.links
    n2.clear()
    o2 = n2.new("ShaderNodeOutputMaterial")
    em = n2.new("ShaderNodeEmission")
    tc2 = n2.new("ShaderNodeTexCoord")
    sx = n2.new("ShaderNodeSeparateXYZ")
    l2.new(tc2.outputs["Generated"], sx.inputs["Vector"])
    # пятно света в центре фона
    gr = n2.new("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    mp2 = n2.new("ShaderNodeMapping")
    mp2.inputs["Location"].default_value = (-0.5 * 7, -0.39 * 9, 0)   # пятно на уровне кошелька
    mp2.inputs["Scale"].default_value = (7, 9, 1)
    l2.new(tc2.outputs["Generated"], mp2.inputs["Vector"])
    l2.new(mp2.outputs["Vector"], gr.inputs["Vector"])
    cr = n2.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.10, 0.10, 0.10, 1)
    cr.color_ramp.elements[1].color = (2.4, 2.4, 2.45, 1)
    l2.new(gr.outputs["Fac"], cr.inputs["Fac"])
    l2.new(cr.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    l2.new(em.outputs["Emission"], o2.inputs["Surface"])
    back.data.materials.append(bm_)

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=260, y_subdivisions=260, size=24, location=(0, 4, -2.2))
    floor = bpy.context.object
    tex = bpy.data.textures.new("rocks", "CLOUDS")
    tex.noise_scale = 0.45
    tex.noise_depth = 4
    dsp = floor.modifiers.new("disp", "DISPLACE")
    dsp.texture = tex
    dsp.strength = 0.55
    dsp.mid_level = 0.3
    for poly in floor.data.polygons:
        poly.use_smooth = True
    fm = bpy.data.materials.new("stone")
    fm.use_nodes = True
    n3, l3 = fm.node_tree.nodes, fm.node_tree.links
    pb = n3["Principled BSDF"]
    tc3 = n3.new("ShaderNodeTexCoord")
    vo = n3.new("ShaderNodeTexVoronoi")          # зерно гранита
    vo.inputs["Scale"].default_value = 40
    nz3 = n3.new("ShaderNodeTexNoise")
    nz3.inputs["Scale"].default_value = 3
    nz3.inputs["Detail"].default_value = 8
    l3.new(tc3.outputs["Object"], vo.inputs["Vector"])
    l3.new(tc3.outputs["Object"], nz3.inputs["Vector"])
    mx = n3.new("ShaderNodeMath")
    mx.operation = "MULTIPLY"
    l3.new(vo.outputs["Distance"], mx.inputs[0])
    l3.new(nz3.outputs["Fac"], mx.inputs[1])
    cr3 = n3.new("ShaderNodeMapRange")
    cr3.inputs["To Min"].default_value = 0.03
    cr3.inputs["To Max"].default_value = 0.30
    cr3.inputs["From Max"].default_value = 0.6
    l3.new(mx.outputs["Value"], cr3.inputs["Value"])
    l3.new(cr3.outputs["Result"], pb.inputs["Base Color"])
    pb.inputs["Roughness"].default_value = 0.8
    bp3 = n3.new("ShaderNodeBump")
    bp3.inputs["Strength"].default_value = 0.4
    l3.new(nz3.outputs["Fac"], bp3.inputs["Height"])
    l3.new(bp3.outputs["Normal"], pb.inputs["Normal"])
    floor.data.materials.append(fm)

    cam_d = bpy.data.cameras.new("cam")
    cam_d.sensor_fit = "VERTICAL"
    cam = bpy.data.objects.new("cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    target = bpy.data.objects.new("target", None)
    sc.collection.objects.link(target)
    tr = cam.constraints.new("TRACK_TO")
    tr.target = target
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    return dict(sc=sc, w1=w1, w2=w2, L=lights, back=back, floor=floor, cam=cam, target=target)


# ------------------------------------------------------------------ шаг 3: анимация по кадрам
def look_at(cam, target, pos, aim, lens, roll=0.0):
    cam.location = pos
    target.location = aim
    cam.data.lens = lens
    cam.rotation_mode = "XYZ"


ORANGE = (1.0, 0.36, 0.08)


def set_light(ob, pos, aim, energy, color=(1, 1, 1)):
    from mathutils import Vector
    ob.data.color = color
    ob.location = pos
    d = Vector(aim) - Vector(pos)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    ob.data.energy = max(0.0, energy)
    ob.hide_render = energy <= 0.0


def pose(ob, loc, rot_deg):
    ob.location = loc
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = tuple(math.radians(a) for a in rot_deg)


def show(obj, on):
    obj.hide_render = not on
    for c in obj.children:
        c.hide_render = not on


def setup_frame(S, t):
    """Расставляет камеру, свет и объекты на момент t. Возвращает False, если кадр — чёрный."""
    sc, w1, w2, L, cam, tg = S["sc"], S["w1"][0], S["w2"][0], S["L"], S["cam"], S["target"]
    for k in L.values():
        set_light(k, (0, 0, 5), (0, 0, 0), 0)
    show(w1, True)
    show(w2, False)
    S["back"].hide_render = True
    S["floor"].hide_render = True
    if t < 1.20:                                         # 1
        on = ramp(t, 0.62, 0.82)
        pose(w1, (0, 0, 0), (62, 0, lerp(-28, -22, t / 1.2)))
        look_at(cam, tg, (0, -9.5, 1.2), (0, 0, 0.05), 85)
        set_light(L["key"], (-2, -3, 4), (0, 0, 0), lerp(15, 60, on))
        set_light(L["rimL"], (-2.2, 2.0, 0.6), (0, 0, 0), 900 * on, ORANGE)
        set_light(L["rimR"], (2.2, 2.0, 0.9), (0, 0, 0), 700 * on, ORANGE)
        return True
    if t < 3.65:                                         # 2: ребро вплотную, облёт
        u = smooth((t - 1.20) / 2.45)
        pose(w1, (0, 0, 0), (90, 0, 0))                 # стоит, лицом к камере
        a = math.radians(lerp(-58, -30, u))
        r = lerp(2.5, 2.1, ease_out((t - 1.2) / 0.6)) - 0.15 * u
        pos = (-0.30 + math.sin(a) * r, -math.cos(a) * r, lerp(0.55, 0.35, u))
        look_at(cam, tg, pos, (-0.30, 0, lerp(0.25, 0.10, u)), 55)
        dim = 1 - ramp(t, 3.40, 3.65)
        set_light(L["rimL"], (-1.8, 1.0, 0.8), (-0.45, 0, 0), 380 * dim, ORANGE)
        set_light(L["rimR"], (0.8, 1.5, 1.4), (0, 0, 0), 180 * dim, ORANGE)
        set_light(L["key"], (-0.6, -1.6, 2.2), (-0.4, 0, 0), 60 * dim)
        return dim > 0.001
    if t < 3.70:
        return False
    if t < 7.45:                                         # 3: угол крупно, поворот, софтбокс
        u = smooth((t - 3.70) / 3.75)
        lvl = ramp(t, 3.70, 4.0) * (1 - ramp(t, 6.75, 7.42))
        pose(w1, (0, 0, 0), (90, 0, lerp(-24, 14, u)))
        look_at(cam, tg, (0.75, -lerp(2.3, 1.95, u), 0.85), (0.22, 0, 0.30), 50)
        sx = lerp(-2.5, 2.5, u)
        set_light(L["sweep"], (sx, -1.6, 2.2), (sx * 0.4, 0, 0.4), 900 * lvl)
        set_light(L["key"], (2.0, -1.5, 3.0), (0.3, 0, 0.3), 120 * lvl)
        set_light(L["rimL"], (-1.5, 1.5, 1.0), (0, 0, 0), 120 * lvl, ORANGE)
        return lvl > 0.001
    if t < 7.50:
        return False
    if t < 11.25:                                        # 4: два кошелька, свет снизу
        u = smooth((t - 7.50) / 3.75)
        show(w2, True)
        up = lerp(-0.25, 0.25, u)
        pose(w1, (0.62, 0, 0.20 + up), (90, -8, -18))
        pose(w2, (-0.62, 0.25, -0.15 + up), (90, 6, 160))
        look_at(cam, tg, (0, -5.6, 0.3), (0, 0, 0.05 + up), 50)
        lift = lerp(-3.0, 3.2, ramp(t, 7.6, 10.2))
        wash = math.exp(-((t - 9.8) / 0.55) ** 2)
        dim = 1 - ramp(t, 10.80, 11.22)
        set_light(L["under"], (0, -2.2, lift), (0, 0, lift + 0.6), (500 + 700 * wash) * dim)
        set_light(L["fill"], (0, -3, 3), (0, 0, 0), 120 * wash * dim)
        set_light(L["rimL"], (-2.5, 1.5, 1), (0, 0, 0), 150 * dim)
        set_light(L["rimR"], (2.5, 1.5, 1), (0, 0, 0), 150 * dim)
        return dim > 0.001
    if t < LOGO_T:                                       # 5: студия, оборот
        u = smooth((t - 11.28) / (LOGO_T - 11.28))
        S["back"].hide_render = False
        S["floor"].hide_render = False
        bob = math.sin((t - 11.28) * 1.6) * 0.05
        spin = 360 * smooth((t - 11.95) / 1.40) if t >= 11.95 else 0.0
        pose(w1, (0.10, 0, 0.55 + bob), (90, -6, -20 + spin + lerp(0, -10, u)))
        k2 = ease_out((t - 14.1) / 0.9)
        if k2 > 0:
            show(w2, True)
            pose(w2, (lerp(0.05, -0.62, k2), 0.65, 0.48 + bob * 0.6), (90, 4, lerp(-20, 25, k2)))
        look_at(cam, tg, (0.0, -lerp(7.6, 7.0, u), 0.85), (0, 0, lerp(0.38, 0.44, u)), 58)
        fade = ramp(t, 11.28, 11.45)
        set_light(L["key"], (-2.5, -2.5, 3.5), (0, 0, 0.5), 260 * fade)
        set_light(L["fill"], (3, -3, 1.5), (0, 0, 0.5), 60 * fade)
        set_light(L["rimL"], (-2, 2, 1.5), (0, 0, 0.5), 220 * fade)
        set_light(L["rimR"], (2, 2, 1.8), (0, 0, 0.5), 180 * fade * (0.4 + math.exp(-((t - 15.2) / 0.6) ** 2)))
        sx = lerp(-3, 3, ramp(t, 13.3, 14.4))
        set_light(L["sweep"], (sx, -2.2, 2.2), (sx * 0.3, 0, 0.6), 500 * math.sin(math.pi * ramp(t, 13.3, 14.4)))
        S["back"].data.materials[0].node_tree.nodes["Emission"].inputs["Strength"].default_value = 1.0 * fade
        return True
    return False


def render(f0, f1, preview=False):
    import bpy
    S = build()
    sc = S["sc"]
    if preview:
        sc.render.resolution_percentage = 25
        sc.cycles.samples = 12
    else:
        sc.cycles.samples = 24
        sc.cycles.adaptive_threshold = 0.04
        sc.render.resolution_percentage = 75     # 810×1440, при сборке — до 1080×1920
    os.makedirs(FR, exist_ok=True)
    black = None
    for fi in range(f0, min(f1, N_FRAMES)):
        path = os.path.join(FR, f"{fi:04d}.png")
        if os.path.exists(path) and not preview:
            continue
        t = fi / FPS
        if t >= LOGO_T or not setup_frame(S, t):
            if black is None:
                import cv2
                rw = int(W * sc.render.resolution_percentage / 100)
                rh = int(H * sc.render.resolution_percentage / 100)
                black = np.zeros((rh, rw, 3), np.uint8)
                cv2.imwrite(path, black)
            else:
                import cv2
                cv2.imwrite(path, black)
            continue
        sc.render.filepath = os.path.abspath(path)
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"кадр {fi} ({t:.2f} с) — {time.time() - t0:.1f} с", flush=True)


# ------------------------------------------------------------------ шаг 4: титры, звук, сборка
def compose(ref):
    import cv2
    from PIL import Image
    sys.path.insert(0, os.path.join(HERE, "..", "engine"))
    sys.path.insert(0, HERE)
    import montage as m
    import importlib.util
    spec = importlib.util.spec_from_file_location("v3", os.path.join(HERE, "2026-10-20_premium_v3.py"))
    v3 = importlib.util.module_from_spec(spec)
    argv = sys.argv
    sys.argv = ["x"]
    spec.loader.exec_module(v3)       # берём оттуда титры и знак — те же, что в v3
    sys.argv = argv
    v = os.path.join(WORK, NAME + "_video.mp4")
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", v], stdin=subprocess.PIPE)
    for fi in range(N_FRAMES):
        t = fi / FPS
        f = cv2.imread(os.path.join(FR, f"{fi:04d}.png"))
        if f.shape[:2] != (H, W):
            f = cv2.resize(f, (W, H), interpolation=cv2.INTER_LANCZOS4)
        f = f.astype(np.float32) / 255
        if 11.28 <= t < LOGO_T:
            # студия: фон серый, а не белый — прижимаем света, края темнее (как в референсе)
            f = np.where(f < 0.5, f, 0.5 + (f - 0.5) * 0.5)
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            d = ((xx - W * 0.5) / (W * 0.75)) ** 2 + ((yy - H * 0.36) / (H * 0.62)) ** 2
            f = f * (1 - 0.45 * np.clip(d, 0, 1) ** 1.2)[..., None]
        else:
            glow = cv2.GaussianBlur(np.clip(f - 0.55, 0, 1), (0, 0), 24)
            f = f + glow * 0.5                               # свечение светов, как в рендере референса
        f = v3.overlay(f, v3.text_layer(t))
        enc.stdin.write(np.clip(f * 255, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    raw = os.path.join(WORK, "ref_audio.wav")
    a = os.path.join(WORK, "audio.wav")
    m.run(["ffmpeg", "-v", "error", "-y", "-i", ref, "-vn", "-ac", "2", "-ar", "48000", raw])
    m.loudnorm(raw, a)
    out = os.path.join(OUT_DIR, NAME + ".mp4")
    m.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", out])
    print(out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prep":
        prep(sys.argv[2])
    elif cmd == "render":
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        f0 = int(args[0]) if args else 0
        f1 = int(args[1]) if len(args) > 1 else N_FRAMES
        render(f0, f1, preview="--preview" in sys.argv)
    elif cmd == "stills":   # пробные кадры: stills 0.9 2.0 ... → _work/premium_v4/stills.jpg
        import bpy
        import cv2
        S = build()
        S["sc"].render.resolution_percentage = 25
        S["sc"].cycles.samples = 16
        tiles = []
        for ts in sys.argv[2:]:
            t = float(ts)
            p = os.path.abspath(os.path.join(WORK, f"still_{t:.2f}.png"))
            if setup_frame(S, t):
                S["sc"].render.filepath = p
                t0 = time.time()
                bpy.ops.render.render(write_still=True)
                print(f"{t} — {time.time() - t0:.1f} с", flush=True)
                tiles.append(cv2.imread(p))
            else:
                tiles.append(np.zeros((H // 4, W // 4, 3), np.uint8))
        cv2.imwrite(os.path.join(WORK, "stills.jpg"), np.hstack(tiles))
    elif cmd == "compose":
        compose(sys.argv[2])
