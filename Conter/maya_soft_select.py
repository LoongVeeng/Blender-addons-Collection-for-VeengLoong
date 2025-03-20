import bpy, bmesh, math
import time

from mathutils import Vector

import gpu, bgl

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
        self.b_clicked = False  # 添加 B 键单击状态
        self.ring_handler = None
        self.overlay_handler = None
        self.text_handler = None
        self.draw_mode = 'VERT'  # 'VERT', 'EDGE' 或 'FACE'
        self.locked_selection = None
        self.update_draw = True
        self.state = self.MAIN
        self.center = Vector()
        self.radius = 0.0
        self.prev_radius = 0.0
        self.b_release_time = 0.0

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SoftSelectionData()
        return cls._instance


# ----------------------- 着色器配置 -----------------------

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


# ----------------------- 工具函数 -----------------------

def get_selection_center(bm):
    verts = [v for v in bm.verts if v.select]
    if not verts: return None, 0.0
    center = sum((v.co for v in verts), Vector()) / len(verts)
    max_d = max((v.co - center).length for v in verts)
    return center, max_d


def calculate_falloff(d, r):
    t = d / r
    if t < 0.25:
        # 红 -> 橙
        color = (1, t * 4, 0, 0.8 + 0.2 * (1 - t))
    elif t < 0.5:
        # 橙 -> 黄
        color = (1 - (t - 0.25) * 4, 1, 0, 0.8 + 0.2 * (1 - t))
    elif t < 0.75:
        # 黄 -> 绿
        color = (0, 1 - (t - 0.5) * 4, 0, 0.8 + 0.2 * (1 - t))
    else:
        # 绿 -> 深绿灰色
        gray = 1 - (t - 0.75) * 4
        color = (gray * 0.2, gray * 0.3, gray * 0.2, 0.8 + 0.2 * (1 - t))
    return color


def get_draw_data(bm, center, eff_r, mode):
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
        # 实时计算面的偏移顶点数据
        face_data = {}
        for f in bm.faces:
            if any((v.co - center).length_squared <= eff_r ** 2 for v in f.verts):
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
    if center is None: return None, None, 0.0
    eff_r = max_d + radius
    locked = get_draw_data(bm, center, eff_r, mode)
    return locked, center, max_d


# ----------------------- 绘制功能 -----------------------

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
            if data.state == data.ADJUSTING:
                # 调整时使用圆环半径对应的影响半径
                eff_r = max_d + get_proportional_distance(data.radius)
            else:
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
    # 添加对衰减编辑状态的检查
    if not context.scene.tool_settings.use_proportional_edit or data.state != data.ADJUSTING or data.radius <= 0:
        return
    region = context.region
    rv3d = context.region_data
    center_2d = _3d_to_2d(region, rv3d, data.center)

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

    # 更新衰减编辑范围的大小数值
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
    """将3D坐标转换为2D屏幕坐标（返回Vector）"""
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


# 新增函数，统一控制圆环与衰减编辑之间的映射关系
def get_proportional_distance(radius):
    # 这里可以根据需要调整映射关系
    return radius / 20  # 根据你反馈的比例调整


# ----------------------- 主操作符 -----------------------

class VIEW3D_OT_MaYa_soft_selection(bpy.types.Operator):
    bl_idname = "view3d.maya_soft_selection"
    bl_label = "Maya Soft Selection"
    _timer = None
    db_time = 1.0  # 添加 db_time 参数

    def __init__(self):
        self.data = SoftSelectionData.get()

    def update_header(self, context):
        state_text = "主状态" if self.data.state == self.data.MAIN else "调整状态"
        header = f"Maya软选择 | 状态：{state_text} | 模式：{'选择'} | 网格模式：{self.data.draw_mode} | [1]点 [2]边 [3]面"
        context.area.header_text_set(header)

    def _init_adjustment(self, context, event, reset_radius=True):
        """初始化调整参数（正确获取鼠标位置）"""
        obj = context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)
        self.data.center = get_selection_center(bm)[0]
        if not self.data.center:
            return False

        self.data.drag_start_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        if reset_radius:
            self.data.radius = 0.0
            self.data.prev_radius = 0.0
            # 初始化时，将当前比例编辑距离设为 0
            bpy.context.scene.tool_settings.proportional_distance = 0
        self.data.update_draw = True  # 标记需要更新绘制数据
        context.area.tag_redraw()  # 强制刷新视图
        return True

    def _update_radius(self, context, event):
        """更新半径值（确保Vector类型）"""
        region = context.region
        rv3d = context.region_data
        center_2d = _3d_to_2d(region, rv3d, self.data.center)

        if not center_2d:
            print("Warning: Failed to calculate 2D center for radius update.")
            return

        current_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        delta = current_pos - center_2d

        scale_factor = context.space_data.overlay.grid_scale * 0.1
        new_radius = delta.length * scale_factor

        # 避免半径瞬间变大，平滑过渡
        if new_radius < self.data.radius:
            self.data.radius = new_radius
        else:
            min_increase = 0.1  # 最小增长值
            if new_radius - self.data.radius < min_increase:
                new_radius = self.data.radius + min_increase
            self.data.radius += (new_radius - self.data.radius) * 0.1

        self.data.update_draw = True  # 标记需要更新绘制数据
        context.area.tag_redraw()  # 强制刷新视图

    def _finalize_adjustment(self, context):
        """完成半径调整，应用软选择，同时隐藏圆环"""
        bpy.context.scene.tool_settings.proportional_distance = get_proportional_distance(self.data.radius)
        self.data.radius = 0.0
        if self.data.ring_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.data.ring_handler, 'WINDOW')
            self.data.ring_handler = None
        if self.data.text_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.data.text_handler, 'WINDOW')
            self.data.text_handler = None
        self.data.state = self.data.MAIN
        self.data.update_draw = True  # 标记需要更新绘制数据
        context.area.tag_redraw()  # 强制刷新视图
        self.update_header(context)  # 更新状态文本

    def _update_data_state(self, context, event):
        if event.type == 'B':
            if event.value == 'PRESS':
                current_time = time.time()
                if self.data.b_released and current_time - self.data.b_release_time < self.db_time:
                    self.data.b_double_clicked = True
                    self.cancel(context)
                    return {'CANCELLED'}
                else:
                    self.data.b_clicked = True  # 标记 B 键单击
                    self.data.b_pressed = True
                    self.data.b_released = False
            elif event.value == 'RELEASE':
                self.data.b_pressed = False
                self.data.b_released = True
                self.data.b_release_time = time.time()
                self.data.b_double_clicked = False  # 重置双击状态
                self.data.b_clicked = False  # 重置单击状态
        if event.type == 'MIDDLEMOUSE':
            if event.value == 'PRESS':
                self.data.mmb_pressed = True
                self.data.mmb_released = False
            elif event.value == 'RELEASE':
                self.data.mmb_pressed = False
                self.data.mmb_released = True

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

        # 更新数据状态
        result = self._update_data_state(context, event)
        if result:
            return result

        # Alt 按键处理
        if event.alt and self.data.mmb_pressed:
            return {'PASS_THROUGH'}

        # B 按下状态下的 MMB 处理
        if self.data.b_pressed:
            if self.data.mmb_pressed:
                if self.data.state == self.data.MAIN:
                    if self._init_adjustment(context, event):
                        self.data.state = self.data.ADJUSTING
                        self.data.ring_handler = bpy.types.SpaceView3D.draw_handler_add(draw_radius_ring, (context,),
                                                                                        'WINDOW', 'POST_PIXEL')
                        self.data.text_handler = bpy.types.SpaceView3D.draw_handler_add(draw_text_callback, (context,),
                                                                                        'WINDOW', 'POST_PIXEL')
                        self.update_header(context)  # 更新状态文本
                        return {'RUNNING_MODAL'}
                elif self.data.state == self.data.ADJUSTING:
                    self._update_radius(context, event)
                    return {'RUNNING_MODAL'}
            elif self.data.mmb_released and self.data.state == self.data.ADJUSTING:
                self._finalize_adjustment(context)
                return {'RUNNING_MODAL'}

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'LEFTMOUSE', 'RIGHTMOUSE'}:
            return {'PASS_THROUGH'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        context.scene.tool_settings.use_proportional_edit = True
        if not self.data.overlay_handler:
            self.data.overlay_handler = bpy.types.SpaceView3D.draw_handler_add(draw_soft_selection, (context,),
                                                                               'WINDOW', 'POST_VIEW')
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
        if self.data.text_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.data.text_handler, 'WINDOW')
            self.data.text_handler = None
        self.data.reset()
        context.area.header_text_set(None)
        context.area.tag_redraw()


# ----------------------- 注册 -----------------------

def register():
    bpy.utils.register_class(VIEW3D_OT_MaYa_soft_selection)
    bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Mesh", space_type='EMPTY', region_type='WINDOW',
                                                            modal=False).keymap_items.new("view3d.maya_soft_selection",
                                                                                          type="B", value="CLICK")


def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_MaYa_soft_selection)

    for km in bpy.context.window_manager.keyconfigs.addon.keymaps:
        for kmi in km.keymap_items:
            if kmi.idname == "view3d.maya_soft_selection" and kmi.type == 'B':
                km.keymap_items.remove(kmi)
                break


if __name__ == "__main__":
    register()
    