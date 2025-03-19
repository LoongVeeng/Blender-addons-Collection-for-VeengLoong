import bpy
import gpu
import bmesh
from bpy.types import Operator
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix

bl_info = {
    "name": "顶点面显示 (Vertex Face Display)",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D视图 > Shift+B",
    "description": "使用GPU绘制着色顶点和面，模仿Maya的顶点面功能",
    "warning": "",
    "doc_url": "",
    "category": "对象",
}

# 数据存储
class VertexFaceDisplayData:
    _instance = None

    def __init__(self):
        self.reset()

    def reset(self):
        self.draw_handler = None
        self.active_object = None
        self.draw_data = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = VertexFaceDisplayData()
        return cls._instance

# 着色器配置
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

# 工具函数
def get_vertex_draw_data(context, obj):
    if not obj or obj.type != 'MESH':
        return None

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    coords, colors = [], []
    for v in bm.verts:
        edges = v.link_edges
        edge_count = len(edges)

        if edge_count == 3:
            colors.append((0.68, 0.85, 0.9, 1.0))  # 明亮浅蓝色
        elif edge_count == 4:
            colors.append((0.0, 1.0, 0.0, 1.0))  # 绿色
        elif edge_count >= 5:
            # 橙色到红色的渐变色
            ratio = min((edge_count - 5) / 5.0, 1.0)
            colors.append((1.0, 1.0 - ratio, 0.0, 1.0))
        else:
            colors.append((1.0, 1.0, 1.0, 1.0))  # 白色（默认）

        coords.append(obj.matrix_world @ v.co)

    bm.free()
    return coords, colors
    
def get_face_draw_data(context, obj):
    if not obj or obj.type != 'MESH':
        return None

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    wireframe_coords, wireframe_colors = [], []
    fill_coords, fill_colors = [], []

    scale_factor = 0.9  # 缩放倍数

    for f in bm.faces:
        face_verts = [obj.matrix_world @ v.co for v in f.verts]
        face_center = sum(face_verts, Vector()) / len(face_verts)

        # 以面中心为中心进行缩放
        scaled_verts = []
        for v in face_verts:
            direction = (v - face_center).normalized()
            scaled_verts.append(face_center + direction * (v - face_center).length * scale_factor)

        # 添加单独的线框
        for i in range(len(scaled_verts)):
            v1 = scaled_verts[i]
            v2 = scaled_verts[(i + 1) % len(scaled_verts)]
            wireframe_coords.extend([v1, v2])
            wireframe_colors.extend([(0.8, 0.8, 0.7, 1.0)] * 2)  # 浅黄灰色线框

        # 添加填充区域
        if len(scaled_verts) == 3:
            fill_coords.extend(scaled_verts)
            fill_colors.extend([(0.5, 0.5, 0.5, 0.5)] * 3)  # 半透明灰色填充
        elif len(scaled_verts) == 4:
            fill_coords.extend([scaled_verts[0], scaled_verts[1], scaled_verts[2],
                                scaled_verts[0], scaled_verts[2], scaled_verts[3]])
            fill_colors.extend([(0.5, 0.5, 0.5, 0.5)] * 6)
        else:
            for i in range(1, len(scaled_verts) - 1):
                fill_coords.extend([scaled_verts[0], scaled_verts[i], scaled_verts[i + 1]])
                fill_colors.extend([(0.5, 0.5, 0.5, 0.5)] * 3)

    bm.free()
    return wireframe_coords, wireframe_colors, fill_coords, fill_colors

def draw_callback_px(context, obj):
    data = VertexFaceDisplayData.get()
    if not data.draw_data and not data.vertex_data:  # 修改条件
        return

    shader.bind()
    shader.uniform_float("ModelViewProjectionMatrix", context.region_data.perspective_matrix)

    # 启用深度测试
    gpu.state.depth_test_set('LESS_EQUAL')

    if data.draw_data:
        wireframe_coords, wireframe_colors, fill_coords, fill_colors = data.draw_data

        if fill_coords:
            batch = batch_for_shader(shader, 'TRIS', {"position": fill_coords, "color": fill_colors})
            batch.draw(shader)

        if wireframe_coords:
            batch = batch_for_shader(shader, 'LINES', {"position": wireframe_coords, "color": wireframe_colors})
            batch.draw(shader)

    if data.vertex_data:
        vertex_coords, vertex_colors = data.vertex_data
        batch = batch_for_shader(shader, 'POINTS', {"position": vertex_coords, "color": vertex_colors})
        batch.draw(shader)

# 操作符
class OBJECT_OT_vertex_face_display(Operator):
    bl_idname = "object.vertex_face_display"
    bl_label = "顶点/面显示"
    bl_description = "使用GPU绘制顶点和面，模仿Maya的顶点面功能"

    def execute(self, context):
        data = VertexFaceDisplayData.get()
        selected_objects = context.selected_objects  # 获取选定的对象

        if not selected_objects:
            self.report({'WARNING'}, "请选择一个或多个对象")
            return {'CANCELLED'}

        data.reset()
        data.active_objects = selected_objects  # 存储选定的对象

        # 隐藏原始对象
        self.original_hide_viewports = {}
        for obj in selected_objects:
            self.original_hide_viewports[obj] = obj.hide_viewport
            obj.hide_viewport = True

        if context.mode == 'EDIT_MESH' and len(selected_objects) == 1 and selected_objects[0].type == 'MESH':
            data.draw_data = get_face_draw_data(context, selected_objects[0])
            data.vertex_data = get_vertex_draw_data(context, selected_objects[0])  # 添加顶点数据
        elif len(selected_objects) == 1 and selected_objects[0].type == 'MESH':
            data.draw_data = get_face_draw_data(context, selected_objects[0])
            data.vertex_data = get_vertex_draw_data(context, selected_objects[0])  # 添加顶点数据
        else:
            data.draw_data = None
            data.vertex_data = None  # 如果选定的对象不是单个网格，则不绘制

        if data.draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(data.draw_handler, 'WINDOW')

        if data.draw_data or data.vertex_data:  # 修改条件
            args = (context, selected_objects[0])  # 仅使用第一个选定的对象进行绘制
            data.draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_VIEW')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            return {'CANCELLED'}

    def modal(self, context, event):
        if event.type == 'ESC':
            data = VertexFaceDisplayData.get()
            if data.draw_handler:
                bpy.types.SpaceView3D.draw_handler_remove(data.draw_handler, 'WINDOW')
            data.reset()

            # 显示原始对象
            if hasattr(self, 'original_hide_viewports'):
                for obj, hide_viewport in self.original_hide_viewports.items():
                    obj.hide_viewport = hide_viewport

            return {'CANCELLED'}
        return {'PASS_THROUGH'}

# 快捷键映射
addon_keymaps = []

def register():
    bpy.utils.register_class(OBJECT_OT_vertex_face_display)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(OBJECT_OT_vertex_face_display.bl_idname, 'B', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_vertex_face_display)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

