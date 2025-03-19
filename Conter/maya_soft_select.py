import bpy, bmesh, math
from mathutils import Vector
import gpu, bgl
from gpu_extras.batch import batch_for_shader

# ----------------------- ¹²ÏíÊý¾Ý -----------------------
class SoftSelectionData:
    _instance = None
    def __init__(self):
        self.reset()
    def reset(self):
        self.drag_start_pos = None
        self.initial_radius = 0.0
        self.is_dragging = False
        self.b_pressed = False
        self.mmb_pressed = False
        self.ring_handler = None
        self.overlay_handler = None
        self.draw_mode = 'VERT'  # 'VERT', 'EDGE' »ò 'FACE'
        self.locked_selection = None
        self.update_draw = True
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SoftSelectionData()
        return cls._instance

# ----------------------- ×ÅÉ«Æ÷ÅäÖÃ -----------------------
vert_shader = '''
uniform mat4 ModelViewProjectionMatrix;
in vec3 position;
in vec4 color;
out vec4 vColor;
void main(){
    gl_Position = ModelViewProjectionMatrix * vec4(position, 1.0);
    vColor = color;
}
'''
frag_shader = '''
in vec4 vColor;
out vec4 FragColor;
void main(){
    FragColor = vColor;
}
'''
shader = gpu.types.GPUShader(vert_shader, frag_shader)

# ----------------------- ¹¤¾ßº¯Êý -----------------------
def get_selection_center(bm):
    verts = [v for v in bm.verts if v.select]
    if not verts: return None, 0.0
    center = sum((v.co for v in verts), Vector()) / len(verts)
    max_d = max((v.co - center).length for v in verts)
    return center, max_d

def calculate_falloff(d, r):
    t = d / r
    if t < 0.25:
        # ºì -> ³È
        color = (1, t * 4, 0, 0.8 + 0.2 * (1 - t))
    elif t < 0.5:
        # ³È -> »Æ
        color = (1 - (t - 0.25) * 4, 1, 0, 0.8 + 0.2 * (1 - t))
    elif t < 0.75:
        # »Æ -> ÂÌ
        color = (0, 1 - (t - 0.5) * 4, 0, 0.8 + 0.2 * (1 - t))
    else:
        # ÂÌ -> °µÂÌ»ÒÉ«
        gray = 1 - (t - 0.75) * 4
        color = (gray * 0.2, gray * 0.3, gray * 0.2, 0.8 + 0.2 * (1 - t))
    return color

def get_draw_data(bm, center, eff_r, mode):
    coords, colors = [], []
    if mode == 'VERT':
        for v in bm.verts:
            if (v.co - center).length_squared <= eff_r**2:
                d = (v.co - center).length
                coords.append(v.co)
                colors.append(calculate_falloff(d, eff_r))
        bt = 'POINTS'
    elif mode == 'EDGE':
        for e in bm.edges:
            v1, v2 = e.verts
            if (v1.co - center).length_squared <= eff_r**2 or (v2.co - center).length_squared <= eff_r**2:
                d1 = min((v1.co - center).length, eff_r)
                d2 = min((v2.co - center).length, eff_r)
                coords.extend([v1.co, v2.co])
                colors.extend([calculate_falloff(d1, eff_r), calculate_falloff(d2, eff_r)])
        bt = 'LINES'
    elif mode == 'FACE':
        # 实时计算面的偏移顶点数据
        face_data = {}
        for f in bm.faces:
            if any((v.co - center).length_squared <= eff_r**2 for v in f.verts):
                face_center = sum((v.co for v in f.verts), Vector()) / len(f.verts)
                moved_verts = [v.co + (face_center - v.co) * 0.05 for v in f.verts]
                face_data[f] = (face_center, moved_verts)

        for f, (face_center, moved_verts) in face_data.items():
            if len(moved_verts) == 3:
                for v_moved in moved_verts:
                    d = min((v_moved - center).length, eff_r)
                    coords.append(v_moved)
                    colors.append(calculate_falloff(d, eff_r))
            elif len(moved_verts) == 4:
                v1, v2, v3, v4 = moved_verts
                d1 = min((v1 - center).length, eff_r)
                d2 = min((v2 - center).length, eff_r)
                d3 = min((v3 - center).length, eff_r)
                d4 = min((v4 - center).length, eff_r)
                coords.extend([v1, v2, v3, v1, v3, v4])
                colors.extend([calculate_falloff(d1, eff_r), calculate_falloff(d2, eff_r), 
                             calculate_falloff(d3, eff_r), calculate_falloff(d1, eff_r),
                             calculate_falloff(d3, eff_r), calculate_falloff(d4, eff_r)])
            else:
                for i in range(1, len(moved_verts) - 1):
                    v1, v2, v3 = moved_verts[0], moved_verts[i], moved_verts[i+1]
                    d1 = min((v1 - center).length, eff_r)
                    d2 = min((v2 - center).length, eff_r)
                    d3 = min((v3 - center).length, eff_r)
                    coords.extend([v1, v2, v3])
                    colors.extend([calculate_falloff(d1, eff_r), calculate_falloff(d2, eff_r), 
                                 calculate_falloff(d3, eff_r)])
        bt = 'TRIS'
    else:
        return None, None, None
    return coords, colors, bt

def calc_locked_selection(context, bm, mode, radius):
    center, max_d = get_selection_center(bm)
    if center is None: return None, None, 0.0
    eff_r = max_d + radius
    locked = get_draw_data(bm, center, eff_r, mode)
    return locked, center, max_d

# ----------------------- »æÖÆ¹¦ÄÜ -----------------------
def draw_soft_selection(context):
    obj = context.edit_object
    if not obj or obj.type != 'MESH' or context.mode != 'EDIT_MESH': return
    bm = bmesh.from_edit_mesh(obj.data)
    data = SoftSelectionData.get()
    
    # 面模式强制实时计算，其他模式使用缓存
    if data.draw_mode == 'FACE' or data.update_draw:
        if data.locked_selection:
            coords, colors, bt = data.locked_selection
        else:
            center, max_d = get_selection_center(bm)
            if center is None: return
            eff_r = max_d + context.scene.tool_settings.proportional_size
            coords, colors, bt = get_draw_data(bm, center, eff_r, data.draw_mode)
        data.draw_data = (coords, colors, bt)
        data.update_draw = False
    else:
        if not hasattr(data, 'draw_data') or data.draw_data is None: return
        coords, colors, bt = data.draw_data

    if coords:
        batch = batch_for_shader(shader, bt, {"position": coords, "color": colors})
        shader.bind()
        shader.uniform_float("ModelViewProjectionMatrix", context.region_data.perspective_matrix)
        batch.draw(shader)

def draw_radius_ring(context):
    data = SoftSelectionData.get()
    if not data.is_dragging: return
    obj = context.edit_object
    if not obj or obj.type != 'MESH' or context.mode != 'EDIT_MESH': return
    rv3d = context.region_data
    view_inv = rv3d.view_matrix.inverted()
    right = view_inv[0].xyz.normalized()
    up = view_inv[1].xyz.normalized()
    bm = bmesh.from_edit_mesh(obj.data)
    center, _ = get_selection_center(bm)
    if center is None: return
    r = context.scene.tool_settings.proportional_size
    seg = 64
    coords = [center + right * math.cos(2*math.pi*i/seg) * r + up * math.sin(2*math.pi*i/seg) * r for i in range(seg)]
    shader_ring = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader_ring, 'LINE_LOOP', {"pos": coords})
    shader_ring.bind()
    shader_ring.uniform_float("color", (1, 1, 1, 0.6))
    bgl.glLineWidth(2)
    batch.draw(shader_ring)
    bgl.glLineWidth(1)

# ----------------------- Ö÷²Ù×÷·û -----------------------
class VIEW3D_OT_MaYa_soft_selection(bpy.types.Operator):
    bl_idname = "view3d.maya_soft_selection"
    bl_label = "Maya Soft Selection"
    _timer = None
    def __init__(self):
        self.data = SoftSelectionData.get()
    def update_header(self, context):
        header = f"Maya软选择 | 模式：{'选择'} | 网格模式：{self.data.draw_mode} | [1]点 [2]边 [3]面"
        context.area.header_text_set(header)
    def modal(self, context, event):
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}
        if event.value == 'PRESS':
            if event.type == 'ONE':
                self.data.draw_mode = 'VERT'
                self.data.locked_selection = None
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                self.data.update_draw = True
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            elif event.type == 'TWO':
                self.data.draw_mode = 'EDGE'
                self.data.locked_selection = None
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
                self.data.update_draw = True
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            elif event.type == 'THREE':
                self.data.draw_mode = 'FACE'
                self.data.locked_selection = None
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
                self.data.update_draw = True
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
        if event.type in {'LEFTMOUSE', 'SELECT'}:
            self.data.update_draw = True
            return {'PASS_THROUGH'}
        # B Óë MMB ÍÏ×§´¦Àí
        if event.type == 'B':
            self.data.b_pressed = (event.value == 'PRESS')
            if event.value == 'RELEASE':
                self.data.locked_selection = None
            return {'RUNNING_MODAL'}
        if event.type == 'MIDDLEMOUSE':
            self.data.mmb_pressed = (event.value == 'PRESS')
            if event.value == 'RELEASE':
                self.data.locked_selection = None
            return {'RUNNING_MODAL'}
        if self.data.b_pressed and self.data.mmb_pressed:
            if not self.data.is_dragging:
                self.data.is_dragging = True
                self.data.drag_start_pos = Vector((event.mouse_x, event.mouse_y))
                self.data.initial_radius = context.scene.tool_settings.proportional_size
                bm = bmesh.from_edit_mesh(context.edit_object.data)
                self.data.locked_selection, _, _ = calc_locked_selection(context, bm, self.data.draw_mode, context.scene.tool_settings.proportional_size)
                self.data.ring_handler = bpy.types.SpaceView3D.draw_handler_add(draw_radius_ring, (context,), 'WINDOW', 'POST_VIEW')
                self.data.update_draw = True
            if event.type == 'MOUSEMOVE':
                delta = (Vector((event.mouse_x, event.mouse_y)) - self.data.drag_start_pos).length
                scale = context.scene.unit_settings.scale_length
                context.scene.tool_settings.proportional_size = max(0.001, self.data.initial_radius + delta * 0.0001 / scale)
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            else:
                if self.data.is_dragging:
                    self.data.is_dragging = False
                    if self.data.ring_handler:
                        bpy.types.SpaceView3D.draw_handler_remove(self.data.ring_handler, 'WINDOW')
                        self.data.ring_handler = None
                return {'RUNNING_MODAL'}
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'LEFTMOUSE', 'RIGHTMOUSE'}:
            return {'PASS_THROUGH'}
        return {'PASS_THROUGH'}
    def execute(self, context):
        context.scene.tool_settings.use_proportional_edit = True
        if not self.data.overlay_handler:
            self.data.overlay_handler = bpy.types.SpaceView3D.draw_handler_add(draw_soft_selection, (context,), 'WINDOW', 'POST_VIEW')
        self.update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    def cancel(self, context):
        context.scene.tool_settings.use_proportional_edit = False
        if self.data.overlay_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.data.overlay_handler, 'WINDOW')
            self.data.overlay_handler = None
        if self.data.ring_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.data.ring_handler, 'WINDOW')
            self.data.ring_handler = None
        self.data.reset()
        context.area.header_text_set(None)
        context.area.tag_redraw()

# ----------------------- ×¢²á -----------------------
def register():
    bpy.utils.register_class(VIEW3D_OT_MaYa_soft_selection)
def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_MaYa_soft_selection)

if __name__ == "__main__":
    register()