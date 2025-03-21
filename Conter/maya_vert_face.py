

import bpy
import gpu
import bmesh
from bpy.types import Operator, Panel
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
        self.active_objects = None  # 修改为存储多个对象
        self.draw_data = None
        self.vertex_data = None

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

def draw_callback_px(context): # 修改函数参数
    data = VertexFaceDisplayData.get()
    if not data.draw_data and not data.vertex_data:  # 修改条件
        return

    shader.bind()
    shader.uniform_float("ModelViewProjectionMatrix", context.region_data.perspective_matrix)

    # 启用深度测试
    gpu.state.depth_test_set('LESS_EQUAL')

    for obj in data.active_objects: # 遍历所有活动对象
        if obj.name in data.draw_data: # 判断是否在字典中
            wireframe_coords, wireframe_colors, fill_coords, fill_colors = data.draw_data[obj.name]

            if fill_coords:
                batch = batch_for_shader(shader, 'TRIS', {"position": fill_coords, "color": fill_colors})
                batch.draw(shader)

            if wireframe_coords:
                batch = batch_for_shader(shader, 'LINES', {"position": wireframe_coords, "color": wireframe_colors})
                batch.draw(shader)

        if obj.name in data.vertex_data: # 判断是否在字典中
            vertex_coords, vertex_colors = data.vertex_data[obj.name]
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

        if context.mode == 'EDIT_MESH':
            # 在编辑模式下，获取场景中所有的网格对象
            all_mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
            if not all_mesh_objects:
                self.report({'WARNING'}, "场景中没有网格对象")
                return {'CANCELLED'}
            selected_objects = all_mesh_objects
        else:
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

        data.draw_data = {} # 修改为字典存储
        data.vertex_data = {} # 修改为字典存储

        for obj in selected_objects: # 遍历所有对象
            if obj.type == 'MESH':
                draw_data = get_face_draw_data(context, obj)
                vertex_data = get_vertex_draw_data(context, obj)
                if draw_data:
                    data.draw_data[obj.name] = draw_data
                if vertex_data:
                    data.vertex_data[obj.name] = vertex_data

        if data.draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(data.draw_handler, 'WINDOW')

        if data.draw_data or data.vertex_data:  # 修改条件
            args = (context,)  # 修改参数
            data.draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_VIEW')

            context.window_manager.modal_handler_add(self)
            context.scene.vertex_face_display_enabled = True # 启用场景属性
            return {'RUNNING_MODAL'}
        else:
            return {'CANCELLED'}

    def cancel(self, context):
        data = VertexFaceDisplayData.get()
        if data.draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(data.draw_handler, 'WINDOW')
        data.reset()

        # 显示原始对象
        if hasattr(self, 'original_hide_viewports'):
            for obj, hide_viewport in self.original_hide_viewports.items():
                obj.hide_viewport = hide_viewport
        # 选中显示的对象
        if data.active_objects:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in data.active_objects:
                obj.select_set(True)
        context.scene.vertex_face_display_enabled = False # 关闭场景属性
        return {'CANCELLED'}

    def modal(self, context, event):
        if not context.scene.vertex_face_display_enabled: # 检查场景属性
            return self.cancel(context)

        if event.type == 'ESC':
            return self.cancel(context)
        return {'PASS_THROUGH'}
        
    ########layout.prop(context.scene, "vertex_face_display_enabled", text="启用顶点/面显示")退出模态操作




# 快捷键映射
addon_keymaps = []

def register():
    bpy.utils.register_class(OBJECT_OT_vertex_face_display)

    bpy.types.Scene.vertex_face_display_enabled = bpy.props.BoolProperty(name="顶点/面显示启用", default=False) # 添加场景属性

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(OBJECT_OT_vertex_face_display.bl_idname, 'B', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_vertex_face_display)

    del bpy.types.Scene.vertex_face_display_enabled # 移除场景属性

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()