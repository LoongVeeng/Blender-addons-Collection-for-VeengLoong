import bpy
import bmesh
import math
import time
from mathutils import Vector
import gpu
import bgl
from gpu_extras.batch import batch_for_shader
import blf


# ----------------------- 全局数据 -----------------------

class SoftSelectionData:
    _instance = None
    MAIN = 0
    ADJUSTING = 1
    HOLD_B_AFTER_ADJUST = 2

    def __init__(self):
        self.reset()

    def reset(self):
        self.drag_start_pos = None
        self.initial_radius = 0.0
        self.is_dragging = False
        self.b_pressed = False
        self.b_double_clicked = False
        self.mmb_pressed = False
        self.mmb_released = False
        self.b_released = False
        self.b_clicked = False
        self.ring_handler = None
        self.overlay_handler = None
        self.text_handler = None
        self.draw_mode = 'VERT'
        self.locked_selection = None
        self.update_draw = True
        self.state = self.MAIN
        self.center = Vector()
        self.radius = 0.0
        self.prev_radius = 0.0
        self.b_release_time = 0.0
        self.affected_faces = []
        self.last_draw_time = 0
        self.prev_viewport_matrix = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SoftSelectionData()
        return cls._instance


# ----------------------- 着色器配置 -----------------------

vert_shader = '''
uniform mat4 ModelViewProjectionMatrix;
uniform mat4 ObjectMatrix;
in vec3 position;
in vec4 color;
out vec4 vColor;
void main(){
    gl_Position = ModelViewProjectionMatrix * ObjectMatrix * vec4(position, 1.0);
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


# ----------------------- 工具函数 -----------------------

def get_selection_center(bm):
    verts = [v for v in bm.verts if v.select]
    if not verts:
        return None, 0.0
    center = sum((v.co for v in verts), Vector()) / len(verts)
    max_d = max((v.co - center).length for v in verts)
    return center, max_d


def calculate_falloff(d, r):
    t = d / r
    if t < 0.25:
        color = (1, t * 4, 0, 0.8 + 0.2 * (1 - t))
    elif t < 0.5:
        color = (1 - (t - 0.25) * 4, 1, 0, 0.8 + 0.2 * (1 - t))
    elif t < 0.75:
        color = (0, 1 - (t - 0.5) * 4, 0, 0.8 + 0.2 * (1 - t))
    else:
        gray = 1 - (t - 0.75) * 4
        color = (gray * 0.2, gray * 0.3, gray * 0.2, 0.8 + 0.2 * (1 - t))
    return color


def get_draw_data(bm, center, eff_r, mode, data):
    coords, colors = [], []
    if mode == 'VERT':
        for v in bm.verts:
            if (v.co - center).length_squared <= eff_r ** 2:
                d = (v.co - center).length
                coords.append(v.co)
                colors.append(calculate_falloff(d, eff_r))
        bt = 'POINTS'
    elif mode == 'EDGE':
        for e in bm.edges:
            v1, v2 = e.verts
            if (v1.co - center).length_squared <= eff_r ** 2 or (v2.co - center).length_squared <= eff_r ** 2:
                d1 = min((v1.co - center).length, eff_r)
                d2 = min((v2.co - center).length, eff_r)
                coords.extend([v1.co, v2.co])
                colors.extend([calculate_falloff(d1, eff_r), calculate_falloff(d2, eff_r)])
        bt = 'LINES'
    elif mode == 'FACE':
        data.affected_faces = []
        for f in bm.faces:
            if any((v.co - center).length_squared <= eff_r ** 2 for v in f.verts):
                data.affected_faces.append(f)

        face_data = {}
        for f in data.affected_faces:
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
                    v1, v2, v3 = moved_verts[0], moved_verts[i], moved_verts[i + 1]
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
    if center is None:
        return None, None, 0.0
    eff_r = max_d + radius
    data = SoftSelectionData.get()
    locked = get_draw_data(bm, center, eff_r, mode, data)
    return locked, center, max_d


# ----------------------- 绘制功能 -----------------------

def draw_soft_selection(context):
    obj = context.edit_object
    if not obj or obj.type != 'MESH' or context.mode != 'EDIT_MESH':
        return
    bm = bmesh.from_edit_mesh(obj.data)
    data = SoftSelectionData.get()

    select_mode = context.tool_settings.mesh_select_mode
    if select_mode[0]:
        data.draw_mode = 'VERT'
    elif select_mode[1]:
        data.draw_mode = 'EDGE'
    elif select_mode[2]:
        data.draw_mode = 'FACE'

    current_viewport_matrix = context.region_data.perspective_matrix.copy()
    if data.prev_viewport_matrix is None or current_viewport_matrix != data.prev_viewport_matrix:
        data.update_draw = True
        data.prev_viewport_matrix = current_viewport_matrix

    current_time = time.time()
    if data.draw_mode == 'FACE' or (data.update_draw and current_time - data.last_draw_time > 0.1):
        center, max_d = get_selection_center(bm)
        if center is None:
            return
        if data.state == data.ADJUSTING:
            eff_r = max_d + get_proportional_distance(data.radius)
        else:
            eff_r = max_d + context.scene.tool_settings.proportional_size
        coords, colors, bt = get_draw_data(bm, center, eff_r, data.draw_mode, data)
        data.draw_data = (coords, colors, bt)
        data.update_draw = False
        data.last_draw_time = current_time
    else:
        if not hasattr(data, 'draw_data') or data.draw_data is None:
            return
        coords, colors, bt = data.draw_data

    if coords:
        batch = batch_for_shader(shader, bt, {"position": coords, "color": colors})
        shader.bind()
        shader.uniform_float("ModelViewProjectionMatrix", context.region_data.perspective_matrix)
        shader.uniform_float("ObjectMatrix", obj.matrix_world)
        batch.draw(shader)


def draw_radius_ring(context):
    data = SoftSelectionData.get()
    if not context.scene.tool_settings.use_proportional_edit or data.state != data.ADJUSTING or data.radius <= 0:
        return
    region = context.region
    rv3d = context.region_data
    obj = context.edit_object
    center_3d = data.center
    center_3d = obj.matrix_world @ center_3d
    center_2d = _3d_to_2d(region, rv3d, center_3d)

    if not center_2d:
        return

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINE_LOOP', {
        "pos": _generate_circle_points(center_2d, data.radius, context.space_data.overlay.grid_scale)
    })

    gpu.state.blend_set('ALPHA')
    shader.bind()
    shader.uniform_float("color", (1.0, 0.7, 0.2, 0.6))
    batch.draw(shader)
    gpu.state.blend_set('NONE')

    bpy.context.scene.tool_settings.proportional_distance = get_proportional_distance(data.radius)


def draw_text_callback(context):
    data = SoftSelectionData.get()
    region = context.region
    font_id = 0
    text = "主状态" if data.state == data.MAIN else "调整状态"

    bgl.glColor4f(1, 1, 1, 1)
    blf.size(font_id, 20, 72)
    text_width, _ = blf.dimensions(font_id, text)
    x = (region.width - text_width) // 2
    y = 20
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, text)


def _3d_to_2d(region, rv3d, point):
    prj = rv3d.perspective_matrix @ Vector((*point, 1))
    if prj.w <= 0:
        return None
    return Vector((
        region.width / 2 * (1 + prj.x / prj.w),
        region.height / 2 * (1 + prj.y / prj.w)
    ))


def _generate_circle_points(center_2d, radius, grid_scale, segments=64):
    radius_px = radius / (0.1 * grid_scale)
    return [
        (center_2d.x + radius_px * math.cos(math.radians(ang)),
         center_2d.y + radius_px * math.sin(math.radians(ang)))
        for ang in range(0, 360, 360 // segments)
    ]


def get_proportional_distance(radius):
    return radius / 20


# ----------------------- 操作符辅助函数 -----------------------

def update_header(context, data):
    state_text = "主状态" if data.state == data.MAIN else "调整状态"
    header = f"Maya软选择 | 状态：{state_text} | 模式：{'选择'} | 网格模式：{data.draw_mode} | [1]点 [2]边 [3]面"
    context.area.header_text_set(header)


def init_adjustment(context, event, data, reset_radius=True):
    obj = context.edit_object
    bm = bmesh.from_edit_mesh(obj.data)
    data.center = get_selection_center(bm)[0]
    if not data.center:
        return False

    data.drag_start_pos = Vector((event.mouse_region_x, event.mouse_region_y))
    if reset_radius:
        data.radius = 0.0
        data.prev_radius = 0.0
        bpy.context.scene.tool_settings.proportional_distance = 0
    data.update_draw = True
    context.area.tag_redraw()
    return True


def update_radius(context, event, data):
    region = context.region
    rv3d = context.region_data
    obj = context.edit_object
    center_3d = data.center
    center_3d = obj.matrix_world @ center_3d
    center_2d = _3d_to_2d(region, rv3d, center_3d)

    if not center_2d:
        print("Warning: Failed to calculate 2D center for radius update.")
        return

    current_pos = Vector((event.mouse_region_x, event.mouse_region_y))
    delta = current_pos - center_2d

    scale_factor = context.space_data.overlay.grid_scale * 0.1
    new_radius = delta.length * scale_factor

    if new_radius < data.radius:
        data.radius = new_radius
    else:
        min_increase = 0.1
        if new_radius - data.radius < min_increase:
            new_radius = data.radius + min_increase
        data.radius += (new_radius - data.radius) * 0.1

    data.update_draw = True
    context.area.tag_redraw()


def finalize_adjustment(context, data):
    bpy.context.scene.tool_settings.proportional_distance = get_proportional_distance(data.radius)
    data.radius = 0.0
    if data.ring_handler:
        bpy.types.SpaceView3D.draw_handler_remove(data.ring_handler, 'WINDOW')
        data.ring_handler = None
    if data.text_handler:
        bpy.types.SpaceView3D.draw_handler_remove(data.text_handler, 'WINDOW')
        data.text_handler = None
    data.state = data.MAIN
    data.update_draw = True
    context.area.tag_redraw()
    update_header(context, data)


def update_data_state(context, event, data, db_time):
    if event.type == 'B':
        if event.value == 'PRESS':
            current_time = time.time()
            if data.b_released and current_time - data.b_release_time < db_time:
                data.b_double_clicked = True
                return {'CANCELLED'}
            else:
                data.b_clicked = True
                data.b_pressed = True
                data.b_released = False
        elif event.value == 'RELEASE':
            data.b_pressed = False
            data.b_released = True
            data.b_release_time = time.time()
            data.b_double_clicked = False
            data.b_clicked = False
    if event.type == 'MIDDLEMOUSE':
        if event.value == 'PRESS':
            data.mmb_pressed = True
            data.mmb_released = False
        elif event.value == 'RELEASE':
            data.mmb_pressed = False
            data.mmb_released = True
    return None


# ----------------------- 主操作符 -----------------------

class VIEW3D_OT_MaYa_soft_selection(bpy.types.Operator):
    bl_idname = "view3d.maya_soft_selection"
    bl_label = "Maya Soft Selection"
    _timer = None
    db_time = 1.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # 关键修正：调用父类构造函数
        self.data = SoftSelectionData.get()
        print("操作符实例已创建")

    def modal(self, context, event):
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}
        if event.value == 'PRESS':
            if event.type == 'ONE':
                self.data.draw_mode = 'VERT'
                self.data.locked_selection = None
                context.tool_settings.mesh_select_mode = (True, False, False)
                self.data.update_draw = True
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            elif event.type == 'TWO':
                self.data.draw_mode = 'EDGE'
                self.data.locked_selection = None
                context.tool_settings.mesh_select_mode = (False, True, False)
                self.data.update_draw = True
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            elif event.type == 'THREE':
                self.data.draw_mode = 'FACE'
                self.data.locked_selection = None
                context.tool_settings.mesh_select_mode = (False, False, True)
                self.data.update_draw = True
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
        if event.type in {'LEFTMOUSE', 'SELECT'}:
            self.data.update_draw = True
            return {'PASS_THROUGH'}

        result = update_data_state(context, event, self.data, self.db_time)
        if result:
            return result

        if event.alt and self.data.mmb_pressed:
            return {'PASS_THROUGH'}

        if self.data.b_pressed:
            if self.data.mmb_pressed:
                if self.data.state == self.data.MAIN:
                    if init_adjustment(context, event, self.data):
                        self.data.state = self.data.ADJUSTING
                        self.data.ring_handler = bpy.types.SpaceView3D.draw_handler_add(draw_radius_ring, (context,),
                                                                                        'WINDOW', 'POST_PIXEL')
                        self.data.text_handler = bpy.types.SpaceView3D.draw_handler_add(draw_text_callback, (context,),
                                                                                        'WINDOW', 'POST_PIXEL')
                        update_header(context, self.data)
                        return {'RUNNING_MODAL'}
                elif self.data.state == self.data.ADJUSTING:
                    update_radius(context, event, self.data)
                    return {'RUNNING_MODAL'}
            elif self.data.mmb_released and self.data.state == self.data.ADJUSTING:
                finalize_adjustment(context, self.data)
                return {'RUNNING_MODAL'}

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'LEFTMOUSE', 'RIGHTMOUSE'}:
            return {'PASS_THROUGH'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        try:
            print("开始执行 execute 方法")
            context.scene.tool_settings.use_proportional_edit = True
            select_mode = context.tool_settings.mesh_select_mode
            if select_mode[0]:
                self.data.draw_mode = 'VERT'
            elif select_mode[1]:
                self.data.draw_mode = 'EDGE'
            elif select_mode[2]:
                self.data.draw_mode = 'FACE'

            if not self.data.overlay_handler:
                self.data.overlay_handler = bpy.types.SpaceView3D.draw_handler_add(draw_soft_selection, (context,),
                                                                                   'WINDOW', 'POST_VIEW')
            update_header(context, self.data)
            context.window_manager.modal_handler_add(self)
            print("execute 方法执行成功")
            return {'RUNNING_MODAL'}
        except Exception as e:
            print(f"执行 execute 方法时出错: {e}")
            return {'CANCELLED'}

    def cancel(self, context):
        context.scene.tool_settings.use_proportional_edit = False
        if self.data.overlay_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.data.overlay_handler, 'WINDOW')
            self.data.overlay_handler = None
        if self.data.ring_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.data.ring_handler, 'WINDOW')
            self.data.ring_handler = None
        if self.data.text_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.data.text_handler, 'WINDOW')
            self.data.text_handler = None
        self.data.reset()
        context.area.header_text_set(None)
        context.area.tag_redraw()


# ----------------------- 注册 -----------------------

def register():
    try:
        bpy.utils.register_class(VIEW3D_OT_MaYa_soft_selection)
        print("操作符注册成功")
    except Exception as e:
        print(f"操作符注册失败: {e}")


def unregister():
    try:
        bpy.utils.unregister_class(VIEW3D_OT_MaYa_soft_selection)
        print("操作符注销成功")
    except Exception as e:
        print(f"操作符注销失败: {e}")


if __name__ == "__main__":
    register()