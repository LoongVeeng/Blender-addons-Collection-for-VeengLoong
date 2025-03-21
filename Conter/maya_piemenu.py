
import os
import bpy
import time
import bmesh
import bpy_extras.view3d_utils
from bpy.types import (Menu,
    Operator
)
from math import degrees, radians
bpy.types.Scene.hit_obj = bpy.props.PointerProperty(type=bpy.types.Object)

class PIE_OT_ClassObject(Operator):
    bl_idname = "class.object"
    bl_label = "Class Object"
    bl_description = "Edit/Object Mode Switch"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode == "OBJECT":
            bpy.ops.object.mode_set(mode="EDIT")
        else:
            bpy.ops.object.mode_set(mode="OBJECT")
        return {'FINISHED'}
        
        
# Edit Selection Modes
class PIE_OT_ClassVertex(Operator):
    bl_idname = "class.vertex"
    bl_label = "Class Vertex"
    bl_description = "Vert Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "EDGE, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            return {'FINISHED'}

# Set Mode Operator #
class PIE_OT_SetObjectModePie(Operator):
    bl_idname = "object.set_object_mode_pie"
    bl_label = "Set the object interactive mode"
    bl_description = "I set the interactive mode of object"
    bl_options = {'REGISTER'}

    mode: bpy.props.StringProperty(name="Interactive mode", default="OBJECT")

    def execute(self, context):
        if (context.active_object):
            try:
                bpy.ops.object.mode_set(mode=self.mode)
            except TypeError:
                msg = context.active_object.name + " It is not possible to enter into the interactive mode"
                self.report(type={"WARNING"}, message=msg)
        else:
            self.report(type={"WARNING"}, message="There is no active object")
        return {'FINISHED'}


class PIE_OT_ClassEdge(Operator):
    bl_idname = "class.edge"
    bl_label = "Class Edge"
    bl_description = "Edge Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        if bpy.ops.mesh.select_mode != "VERT, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            return {'FINISHED'}

class PIE_OT_ClassFace(Operator):
    bl_idname = "class.face"
    bl_label = "Class Face"
    bl_description = "Face Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        if bpy.ops.mesh.select_mode != "VERT, EDGE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            return {'FINISHED'}

class PIE_OT_VertsEdgesFaces(Operator):
    bl_idname = "verts.edgesfaces"
    bl_label = "Verts Edges Faces"
    bl_description = "Vert/Edge/Face Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}
            
            

# Edit Selection Modes
class PIE_OT_classvertexop(Operator):
    bl_idname = "class.vertexop"
    bl_label = "Class Vertex"
    bl_description = "Vert Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "EDGE, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            return {'FINISHED'}


class PIE_OT_classedgeop(Operator):
    bl_idname = "class.edgeop"
    bl_label = "Class Edge"
    bl_description = "Edge Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        if bpy.ops.mesh.select_mode != "VERT, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            return {'FINISHED'}


class PIE_OT_classfaceop(Operator):
    bl_idname = "class.faceop"
    bl_label = "Class Face"
    bl_description = "Face Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        if bpy.ops.mesh.select_mode != "VERT, EDGE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            return {'FINISHED'}

# Combined Selection Mode
class PIE_OT_vertsfacesop(Operator):
    bl_idname = "verts.facesop"
    bl_label = "Verts  Faces"
    bl_description = "Vert/Face Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}

# Combined Selection Mode
class PIE_OT_vertsedgesfacesop(Operator):
    bl_idname = "verts.edgesfacesop"
    bl_label = "Verts Edges Faces"
    bl_description = "Vert/Edge/Face Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}

#收藏
# 定义一个全局变量，用于存储是否有物体被射线击中的布尔值
global hit_result
hit_result = "None"

def switch_mode_common(context, mode_type):
    # 获取当前悬停对象并立即清除
    hit_obj = context.scene.hit_obj
    context.scene.hit_obj = None
    global hit_result
    hit_result = "None"

    # 处理悬停对象（使用 Blender 标准属性检查）
    if hit_obj:
        # 检查物体是否在视图中可见且可选
        if not hit_obj.hide_viewport and not hit_obj.hide_select:
            # 添加悬停对象到选择集
            hit_obj.select_set(True)
            # 设置悬停对象为活动对象
            context.view_layer.objects.active = hit_obj

    # 获取当前活动对象
    active_obj = context.view_layer.objects.active

    # 如果没有活动对象则取消操作
    if not active_obj:
        return False

    # 确保所有选中对象都处于对象模式
    for obj in context.selected_objects:
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

    try:
        # 进入编辑模式（只对活动对象有效）
        bpy.ops.object.mode_set(mode='EDIT')
        # 设置选择模式
        bpy.ops.mesh.select_mode(type=mode_type)
        # 执行附加操作
        bpy.ops.object.msm_from_object(mode=mode_type.lower())
    except Exception as e:
        print(f"Error switching mode: {str(e)}")
        return False

    return True




class SelectAndSwitchToObjectMode(bpy.types.Operator):
    bl_idname = "object.select_switch_object_mode"
    bl_label = "Select and Switch to object Mode"

    def execute(self, context):
        try:
            context.scene.vertex_face_display_enabled = False
        except AttributeError:
            self.report({'ERROR'}, "The 'vertex_face_display_enabled' attribute does not exist.")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"An unexpected error occurred: {str(e)}")
            return {'CANCELLED'}

        # 检查当前是否有活动对象
        active_obj = context.active_object
        if not active_obj:
            # 若没有活动对象，尝试从选中对象中找一个
            selected_objs = [obj for obj in context.selected_objects if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'LATTICE', 'EMPTY', 'GPENCIL', 'CAMERA', 'LIGHT', 'SPEAKER'}]
            if selected_objs:
                # 选择第一个合适的选中对象作为活动对象
                context.view_layer.objects.active = selected_objs[0]
                active_obj = context.active_object
            else:
                # 若既没有活动对象也没有合适的选中对象，报告警告并取消操作
                self.report({'WARNING'}, "No valid active or selected object available.")
                return {'CANCELLED'}

        try:
            # 尝试切换到物体模式
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            # 若切换模式失败，报告错误并取消操作
            self.report({'ERROR'}, f"Failed to switch to object mode: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

class SelectAndSwitchToVertexMode(bpy.types.Operator):
    bl_idname = "object.select_switch_vertex_mode"
    bl_label = "Select and Switch to Vertex Mode"

    def execute(self, context):
        try:
            context.scene.vertex_face_display_enabled = False
        except AttributeError:
            self.report({'ERROR'}, "The 'vertex_face_display_enabled' attribute does not exist.")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"An unexpected error occurred: {str(e)}")
            return {'CANCELLED'}
        if not switch_mode_common(context, 'VERT'):
            self.report({'WARNING'}, "No active object available")
            return {'CANCELLED'}
        return {'FINISHED'}


class SelectAndSwitchToEdgeMode(bpy.types.Operator):
    bl_idname = "object.select_switch_edge_mode"
    bl_label = "Select and Switch to Edge Mode"

    def execute(self, context):
        try:
            context.scene.vertex_face_display_enabled = False
        except AttributeError:
            self.report({'ERROR'}, "The 'vertex_face_display_enabled' attribute does not exist.")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"An unexpected error occurred: {str(e)}")
            return {'CANCELLED'}
        if not switch_mode_common(context, 'EDGE'):
            self.report({'WARNING'}, "No active object available")
            return {'CANCELLED'}
        return {'FINISHED'}


class SelectAndSwitchToFaceMode(bpy.types.Operator):
    bl_idname = "object.select_switch_face_mode"
    bl_label = "Select and Switch to Face Mode"

    def execute(self, context):
        try:
            context.scene.vertex_face_display_enabled = False
        except AttributeError:
            self.report({'ERROR'}, "The 'vertex_face_display_enabled' attribute does not exist.")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"An unexpected error occurred: {str(e)}")
            return {'CANCELLED'}
        if not switch_mode_common(context, 'FACE'):
            self.report({'WARNING'}, "No active object available")
            return {'CANCELLED'}
        return {'FINISHED'}
            
            

class PIE_MO_R(Operator):
    bl_idname = "wm.modal_operator_pie_r"
    bl_label = "RightMouse Pie"

    def modal(self, context, event):
        global hit_result

        if event.type == 'TIMER':
            elapsed_time = time.time() - self.start_time
            if elapsed_time >= 0.3:
                context.window_manager.event_timer_remove(self.timer)
                bpy.ops.wm.call_menu_pie(name="MaYaPieMenu_R")
                
                return {'FINISHED'}

        if event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                self.start_time = time.time()
                self.timer = context.window_manager.event_timer_add(0.01, window=context.window)
                return {'RUNNING_MODAL'}
            elif event.value == 'RELEASE':
                elapsed_time = time.time() - self.start_time
                if elapsed_time >= 0.3:
                    context.window_manager.event_timer_remove(self.timer)
                    bpy.ops.wm.call_menu_pie(name="MaYaPieMenu_R")
                    
                    return {'FINISHED'}
                else:
                    context.window_manager.event_timer_remove(self.timer)
                    
                    return {'CANCELLED'}

        if event.type == 'MOUSEMOVE':
            dx = abs(event.mouse_x - self.mouse_x)
            dy = abs(event.mouse_y - self.mouse_y)
            if dx > 10 or dy > 10:
                context.window_manager.event_timer_remove(self.timer)
                bpy.ops.wm.call_menu_pie(name="MaYaPieMenu_R")
                
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global hit_result

        region = context.region
        rv3d = context.region_data
        coord = (event.mouse_region_x, event.mouse_region_y)
        view_vector = bpy_extras.view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = bpy_extras.view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + view_vector

        hit, location, normal, index, obj, matrix = context.scene.ray_cast(context.view_layer.depsgraph, ray_origin, view_vector)

        if hit:
            # 检查对象类型并设置hit_result
            if obj.type == 'MESH':
                hit_result = 'MESH'
            elif obj.type == 'CURVE':
                hit_result = 'CURVE'
            elif obj.type == 'CAMERA':
                hit_result = 'CAMERA'
            elif obj.type == 'LIGHT':
                hit_result = 'LIGHT'
            elif obj.type == 'SURFACE':
                hit_result = 'SURFACE'
            else:
                hit_result = obj.type  # 默认情况下使用对象的类型
            bpy.context.scene.hit_obj = obj
        else:
            hit_result = "None"

        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            self.start_time = time.time()
            self.mouse_x = event.mouse_x
            self.mouse_y = event.mouse_y
            self.timer = context.window_manager.event_timer_add(0.01, window=context.window)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        return {'CANCELLED'}
        

class SubPieMenu_ChangeTo(Menu):
    bl_label = "SubPieMenu_ChangeTo"
    bl_idname = "Pie.Menu_ChangeTo"
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("object.convert", text="转换成网格", icon='MESH_DATA').target = 'MESH'
        pie.operator("gpencil.convert", text="蜡笔转换成多边形", icon='GP_SELECT_STROKES').type = 'POLY'
        pie.operator("object.convert", text="转换成蜡笔", icon='GREASEPENCIL').target = 'GPENCIL'
        pie.operator("object.convert", text="转换成毛发曲线", icon='CURVE_BEZCURVE').target = 'CURVES'
        pie.operator("object.convert", text="转换成曲线", icon='CURVE_DATA').target = 'CURVE'
        pie.operator("gpencil.convert", text="蜡笔转换成曲线", icon='GP_SELECT_STROKES').type = 'CURVE'
        pie.separator()
        pie.operator("gpencil.convert", text="蜡笔转换成路径", icon='GP_SELECT_STROKES').type = 'PATH'

class SubPieMenu_Armature(Menu):
    bl_label = "SubPieMenu_Armature"
    bl_idname = "Pie.Menu_Armature"
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("armature.subdivide", text="Subdivide Bone", icon="MOD_SUBSURF")
        pie.operator("armature.delete", text="Delete Bone", icon="CANCEL")
        pie.separator()
        pie.operator("armature.extrude_move", text="Extrude Bone", icon="BONE_DATA")
        pie.separator()
        pie.separator()
        pie.separator()
        pie.separator()

class SubPieMenu_R_E_UV(Menu):
    bl_label = "SubPieMenu_R_E_UV"
    bl_idname = "Pie.Sub_Menu_R_E_UV"
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.separator()
        pie.operator("uv.maya_uvs", text = "UV", icon = "MOD_SMOOTH")
        pie.operator("mesh.select_linked", text = "UV壳", icon = "MOD_SMOOTH").delimit = {'SEAM'}
        pie.separator()
        pie.separator()
        pie.separator()
        pie.separator()
        pie.separator()

class MaYaPieMenuR(Menu):
    bl_label = "MaYaMarking Menu"
    bl_idname = "MaYaPieMenu_R" 
    def draw(self, context):
        layout = self.layout
        ob = context.object
        
        if context.scene.vertex_face_display_enabled:
                self.draw_mesh_mode(layout)
        else :
                

                if not ob.select_get() :
                        if hit_result == "None" :
                                self.draw_ok_mode(layout)
                        elif hit_result == "MESH" :
                                self.draw_mesh_mode(layout)
                        elif hit_result == "SURFACE" :
                                self.draw_surface_mode(layout)
                        elif hit_result == "CURVE" :
                                self.draw_curve_object_mode(layout)
                        elif hit_result == "ARMATURE" :
                                self.draw_armature_mode(layout)
                        elif hit_result == "FONT" :
                                self.draw_font_mode(layout)
                        elif hit_result == "LIGHT" :
                                self.draw_light_mode(layout)
                        elif hit_result == "GPENCIL" :
                                self.draw_gpencil_mode(layout)
                        elif hit_result == "EMPTY" :
                                self.draw_empty_mode(layout)
                        elif hit_result == "SPEAKER" :
                                self.draw_speaker_mode(layout)

                        else :
                                return #self.draw_ok_mode(layout)
                
                else :
                        if ob.type == 'MESH' and ob.mode in {'OBJECT','EDIT'} :
                                if not bpy.context.scene.tool_settings.use_transform_data_origin == True :
                                        if hit_result == "MESH" :
                                                self.draw_mesh_mode(layout)
                                        elif hit_result == "SURFACE" :
                                                self.draw_surface_mode(layout)
                                        else :
                                                self.draw_mesh_mode(layout)
                                else :
                                        self.draw_axisorigin_mode(layout)

                        if ob and ob.type == 'MESH' and ob.mode in {'SCULPT'}:
                                self.draw_mesh_sculpt_mode(layout)


                        if ob.type == 'SURFACE' and ob.mode in {'OBJECT','EDIT'}:
                                if not bpy.context.scene.tool_settings.use_transform_data_origin == True :
                                        if hit_result == "SURFACE" :
                                                self.draw_surface_mode(layout)
                                        elif hit_result == "MESH" :
                                                self.draw_mesh_mode(layout)
                                        else :
                                                self.draw_surface_mode(layout)
                                else :
                                        self.draw_axisorigin_mode(layout)

                        if ob.type == 'CURVE':
                                if not bpy.context.scene.tool_settings.use_transform_data_origin == True :
                                        if ob.mode in {'OBJECT'}:
                                                self.draw_curve_object_mode(layout)
                                        elif ob.mode in {'EDIT'}:
                                                self.draw_curve_edit_mode(layout)
                                else :
                                        self.draw_axisorigin_mode(layout)

                        elif ob.type == 'GPENCIL' and ob.mode in {'OBJECT','EDIT'} :
                                if not bpy.context.scene.tool_settings.use_transform_data_origin == True :
                                        if hit_result == "MESH" :
                                                self.draw_mesh_mode(layout)
                                        elif hit_result == "SURFACE" :
                                                self.draw_surface_mode(layout)
                                        elif hit_result == "GPENCIL" :
                                                self.draw_gpencil_mode(layout)
                                        else :
                                                self.draw_gpencil_mode(layout)
                                else :
                                        self.draw_axisorigin_mode(layout)

                        elif ob.type == 'LIGHT' and ob.mode in {'OBJECT','EDIT'} :
                                if not bpy.context.scene.tool_settings.use_transform_data_origin == True :
                                        if hit_result == "MESH" :
                                                self.draw_mesh_mode(layout)
                                        elif hit_result == "SURFACE" :
                                                self.draw_surface_mode(layout)
                                        elif hit_result == "GPENCIL" :
                                                self.draw_gpencil_mode(layout)
                                        elif hit_result == "ARMATURE" :
                                                self.draw_armature_mode(layout)
                                        elif hit_result == "LIGHT" :
                                                self.draw_light_mode(layout)
                                        else :
                                                self.draw_light_mode(layout)
                                else :
                                        self.draw_axisorigin_mode(layout)

                        elif ob.type == 'CAMERA' and ob.mode in {'OBJECT','EDIT'} :
                                if not bpy.context.scene.tool_settings.use_transform_data_origin == True :
                                        if hit_result == "MESH" :
                                                self.draw_mesh_mode(layout)
                                        elif hit_result == "SURFACE" :
                                                self.draw_surface_mode(layout)
                                        elif hit_result == "GPENCIL" :
                                                self.draw_gpencil_mode(layout)
                                        elif hit_result == "ARMATURE" :
                                                self.draw_armature_mode(layout)
                                        elif hit_result == "LIGHT" :
                                                self.draw_light_mode(layout)
                                        elif hit_result == "CAMERA" :
                                                self.draw_camera_mode(layout)
                                        else :
                                                self.draw_camera_mode(layout)
                                else :
                                        self.draw_axisorigin_mode(layout)

                        elif ob.type == 'FONT' and ob.mode in {'OBJECT','EDIT'} :
                                if not bpy.context.scene.tool_settings.use_transform_data_origin == True :
                                        if hit_result == "MESH" :
                                                self.draw_mesh_mode(layout)
                                        elif hit_result == "SURFACE" :
                                                self.draw_surface_mode(layout)
                                        elif hit_result == "GPENCIL" :
                                                self.draw_gpencil_mode(layout)
                                        elif hit_result == "ARMATURE" :
                                                self.draw_armature_mode(layout)
                                        elif hit_result == "LIGHT" :
                                                self.draw_light_mode(layout)
                                        elif hit_result == "CAMERA" :
                                                self.draw_camera_mode(layout)
                                        elif hit_result == "FONT" :
                                                self.draw_font_mode(layout)
                                        else :
                                                self.draw_font_mode(layout)
                                else :
                                        self.draw_axisorigin_mode(layout)

                        elif ob.type == 'META' and ob.mode in {'OBJECT','EDIT'} :
                                if not bpy.context.scene.tool_settings.use_transform_data_origin == True :
                                        if hit_result == "MESH" :
                                                self.draw_mesh_mode(layout)
                                        elif hit_result == "SURFACE" :
                                                self.draw_surface_mode(layout)
                                        elif hit_result == "GPENCIL" :
                                                self.draw_gpencil_mode(layout)
                                        elif hit_result == "ARMATURE" :
                                                self.draw_armature_mode(layout)
                                        elif hit_result == "LIGHT" :
                                                self.draw_light_mode(layout)
                                        elif hit_result == "CAMERA" :
                                                self.draw_camera_mode(layout)
                                        elif hit_result == "FONT" :
                                                self.draw_font_mode(layout)
                                        elif hit_result == "META" :
                                                self.draw_meta_mode(layout)
                                        else :
                                                self.draw_meta_mode(layout)
                                else :
                                        self.draw_axisorigin_mode(layout)

                        elif ob.type == 'ARMATURE' :
                                if ob.mode in {'OBJECT'} :
                                
                                        if not bpy.context.scene.tool_settings.use_transform_data_origin == True :
                                                if hit_result == "MESH" :
                                                        self.draw_mesh_mode(layout)
                                                elif hit_result == "SURFACE" :
                                                        self.draw_surface_mode(layout)
                                                elif hit_result == "GPENCIL" :
                                                        self.draw_gpencil_mode(layout)
                                                elif hit_result == "ARMATURE" :
                                                        self.draw_armature_object_mode(layout)
                                                else :
                                                        self.draw_armature_object_mode(layout)
                                        else :
                                                self.draw_axisorigin_mode(layout)
                                
                                elif ob.mode in {'EDIT'} :
                                        self.draw_armature_edit_mode(layout)
                                        

                        

                        else :
                                return

    def draw_ok_mode(self, layout):
        message = "No Active Object Selected"
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.separator()
        # 6 - RIGHT
        pie.separator()
        # 2 - BOTTOM
        pie.operator("object.select_all", text = "All Selection", icon ="UV_SYNC_SELECT").action="SELECT"
        # 8 - TOP
        pie.operator("object.select_all", text = "OK Tool", icon ="UV_SYNC_SELECT").action="SELECT"
        # 7 - TOP - LEFT
        pie.separator()
        # 9 - TOP - RIGHT
        pie.separator()
        # 1 - BOTTOM - LEFT
        pie.separator()
        # 3 - BOTTOM - RIGHT
        pie.separator()

    def draw_mesh_mode(self, layout):
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("object.select_switch_vertex_mode", text = "Vertex", icon = 'VERTEXSEL')
        # 6 - RIGHT
        op = pie.operator("wm.call_menu_pie", text="UV   ▶")
        op.name="Pie.Sub_Menu_R_E_UV"
        # 2 - BOTTOM
        pie.operator("object.select_switch_face_mode", text = "Face", icon = 'FACESEL')
        # 8 - TOP
        pie.operator("object.select_switch_edge_mode", text = "Edge", icon = 'EDGESEL')
        # 7 - TOP - LEFT
        pie.operator("view3d.localview", text = "Isolate", icon = "BORDERMOVE")
        # 9 - TOP - RIGHT
        pie.operator("object.select_switch_object_mode", text = "Object", icon = "OBJECT_DATA") #object.mode_set
        # 1 - BOTTOM - LEFT
        pie.operator("object.vertex_face_display", text = "顶点面", icon = "MOD_WIREFRAME") #verts.facesop
        # 3 - BOTTOM - RIGHT
        pie.operator("verts.edgesfacesop", text="多重", icon='OBJECT_DATAMODE')

        pie.separator()
        pie.separator()
        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.scale_y = 7
        other_menu = other.box().column()
        other_menu.scale_y=1.3
        other_menu.operator("mesh.select_all", text = "Invert Selection", icon ="UV_SYNC_SELECT").action="INVERT"
        other_menu.operator("screen.screen_full_area", text = "Max Screen",icon = "FULLSCREEN_ENTER")
        other_menu.menu('SubmenuCreateObject', icon='RIGHTARROW_THIN',  text='Mesh Objects')
        other_menu.menu('SubmenuLight', icon='RIGHTARROW_THIN',  text='Lights')
        other_menu.menu('SubmenuHistory', icon='RIGHTARROW_THIN',  text='History')
        other_menu.operator("object.qol_grid_cut", text="细分")


    def draw_mesh_sculpt_mode(self, layout):
        global brush_icons
        pie = layout.menu_pie()
        # 添加相应的操作符
        # 4 - LEFT
        pie.operator("class.pieweightpaint", text="Weight Paint", icon='WPAINT_HLT')
        # 6 - RIGHT
        pie.operator("class.pietexturepaint", text="Texture Paint", icon='TPAINT_HLT')
        # 2 - BOTTOM
        pie.operator("object.mode_set", text = "退出雕刻", icon = "OBJECT_DATA")
        # 8 - TOP
        pie.operator("class.object", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')
        # 7 - TOP - LEFT
        op = pie.operator("wm.call_menu_pie", text="Symmetry   ▶")
        op.name="Pie.Sub_Menu_R_S_Symmetry"
        # 9 - TOP - RIGHT
        pie.separator()
        # 1 - BOTTOM - LEFT
        op = pie.operator("wm.call_menu_pie", text="DropoffType   ▶")
        op.name="Pie.Sub_Menu_R_S_DropoffLike"
        # 3 - BOTTOM - RIGHT
        pie.operator("paint.brush_select",text='   抓取Grab', icon_value=brush_icons["grab"]).sculpt_tool = 'GRAB'

    def draw_curve_object_mode(self, layout):
        pie = layout.menu_pie()
        # 添加相应的操作符
        # 4 - LEFT
        pie.operator("object.editmode_toggle", text="Edit Curve", icon='OBJECT_DATAMODE')
        # 6 - RIGHT
        pie.separator()
        # 2 - BOTTOM
        op = pie.operator("wm.call_menu_pie", text="ChangeTo   ▶")
        op.name="Pie.Menu_ChangeTo"
        # 8 - TOP
        pie.separator()
        # 7 - TOP - LEFT
        pie.separator()
        # 9 - TOP - RIGHT
        pie.operator(PIE_OT_SetObjectModePie.bl_idname, text="Object", icon="OBJECT_DATAMODE").mode = "OBJECT"
        # 1 - BOTTOM - LEFT
        pie.separator()
        # 3 - BOTTOM - RIGHT
        pie.separator()

    def draw_curve_edit_mode(self, layout):
        pie = layout.menu_pie()
        # 添加相应的操作符
        # 4 - LEFT
        pie.operator("object.editmode_toggle", text="Edit Curve", icon='OBJECT_DATAMODE')
        # 6 - RIGHT
        pie.separator()
        # 2 - BOTTOM
        pie.operator("curve.extrude_move", text="挤出曲线并移动", icon='OBJECT_DATAMODE')
        # 8 - TOP
        pie.operator("curve.subdivide", text="细分曲线", icon='OBJECT_DATAMODE')
        # 7 - TOP - LEFT
        pie.separator()
        # 9 - TOP - RIGHT
        pie.operator("object.mode_set", text = "Object", icon = "OBJECT_DATA")
        # 1 - BOTTOM - LEFT
        pie.operator("curve.delete", text="删除曲线顶点", icon='OBJECT_DATAMODE').type = 'VERT'
        # 3 - BOTTOM - RIGHT
        pie.separator()

    def draw_surface_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.editmode_toggle", text="Edit Surface", icon='OBJECT_DATAMODE')
        pie.separator()
        op = pie.operator("wm.call_menu_pie", text="ChangeTo   ▶")
        op.name="Pie.Menu_ChangeTo"
        pie.separator()
        pie.separator()
        pie.operator("object.mode_set", text = "Object", icon = "OBJECT_DATA")
        pie.separator()
        pie.separator()

    def draw_axisorigin_mode(self, layout):
        pie = layout.menu_pie()
        # 添加相应的操作符
        # 4 - LEFT
        # 动态更改按钮的图标和文本
        current_tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname
        if current_tool == 'builtin.move':
            icon = 'CHECKBOX_DEHLT'
        elif current_tool == 'builtin.rotate':
            icon = 'CHECKBOX_HLT'
        pie.operator("object.origin_axis_show_direction_handles", text="显示方向控制柄", icon=icon)
###
        # 6 - RIGHT
        pie.operator("object.maya_origin_mode", text = "退出", icon = 'VERTEXSEL')
        # 2 - BOTTOM
        pie.operator("object.origin_axis_reset", text = "重置枢轴", icon = 'EDGESEL')##正常来说这个操作是重置枢轴的位置以及方向
        # 8 - TOP
        pie.operator("object.select_switch_face_mode", text = "固定组件枢轴", icon = 'FACESEL')
        # 7 - TOP - LEFT
        pie.operator("view3d.localview", text = "捕捉枢轴方向", icon = "BORDERMOVE")
        # 9 - TOP - RIGHT
        pie.operator("object.mode_set", text = "捕捉枢轴位置", icon = "OBJECT_DATA")
        # 1 - BOTTOM - LEFT
        pie.operator("object.rotation_clear", text="重置枢轴方向").clear_delta = False##########pie.operator("object.rotation_clear", text="重置枢轴方向").clear_delta = False
        # 3 - BOTTOM - RIGHT
        pie.operator("object.origin_set", text="重置枢轴位置").type = 'ORIGIN_CENTER_OF_VOLUME'###("object.origin_set", text="重置枢轴位置").type = 'ORIGIN_GEOMETRY'是集合中心

        
    def draw_gpencil_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.mode_set", text="编辑模式", icon='EDITMODE_HLT').mode = 'EDIT_GPENCIL'
        pie.separator()
        op = pie.operator("wm.call_menu_pie", text="ChangeTo   ▶")
        op.name="Pie.Menu_ChangeTo"
        pie.operator("object.mode_set", text="顶点绘制模式", icon='VPAINT_HLT').mode = 'VERTEX_GPENCIL'
        pie.operator("object.mode_set", text="雕刻模式", icon='SCULPTMODE_HLT').mode = 'SCULPT_GPENCIL'
        pie.operator("object.mode_set", text = "Object", icon = "OBJECT_DATA")
        pie.operator("object.mode_set", text="绘制模式", icon='GREASEPENCIL').mode = 'PAINT_GPENCIL'
        pie.operator("object.mode_set", text="权重模式", icon='WPAINT_HLT').mode = 'WEIGHT_GPENCIL'

    def draw_meta_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.editmode_toggle", text="Edit Meta", icon='OBJECT_DATAMODE')
        pie.separator()
        op = pie.operator("wm.call_menu_pie", text="ChangeTo   ▶")
        op.name="Pie.Menu_ChangeTo"
        pie.separator()
        pie.separator()
        pie.operator("object.mode_set", text = "Object", icon = "OBJECT_DATA")
        pie.separator()
        pie.separator()

    def draw_armature_object_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.editmode_toggle", text="Edit Armature", icon='OBJECT_DATAMODE')
        pie.separator()
        pie.separator()
        pie.separator()
        pie.operator("object.mode_set", text="姿态模式", icon='POSE_HLT').mode = 'POSE'
        pie.operator("object.mode_set", text = "Object", icon = "OBJECT_DATA")
        pie.separator()
        pie.separator()

    def draw_armature_edit_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.editmode_toggle", text="Edit Armature", icon='OBJECT_DATAMODE')
        pie.separator()
        pie.separator()
        op = pie.operator("wm.call_menu_pie", text="Edit Armature   ▶")
        op.name="Pie.Menu_Armature"
        pie.operator("object.mode_set", text="姿态模式", icon='POSE_HLT').mode = 'POSE'
        pie.operator("object.mode_set", text = "Object", icon = "OBJECT_DATA")
        pie.separator()
        pie.separator()

    def draw_light_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.editmode_toggle", text="Edit Light", icon='OBJECT_DATAMODE')
        pie.separator()
        op = pie.operator("wm.call_menu_pie", text="ChangeTo   ▶")
        op.name="Pie.Menu_ChangeTo"
        pie.separator()
        pie.separator()
        pie.operator("object.mode_set", text = "Object", icon = "OBJECT_DATA")
        pie.separator()
        pie.separator()

    def draw_camera_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.camera_pan", text="Edit Camera", icon='OBJECT_DATAMODE')
        pie.operator("object.rendering_camera_cycles", text="Quick Rending Cycles 8k")
        pie.operator("view3d.view_camera", text="Exit Camera View")
        pie.operator("object.aim_camera_at_target", text = "Aim Target", icon = "OBJECT_DATA")
        pie.separator()
        pie.operator("object.create_camera_from_view", text = "Creat Camera form View", icon = "OBJECT_DATA")
        pie.separator()
        pie.separator()

    def draw_font_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.editmode_toggle", text="Edit Font", icon='OBJECT_DATAMODE')
        pie.separator()
        op = pie.operator("wm.call_menu_pie", text="ChangeTo   ▶")
        op.name="Pie.Menu_ChangeTo"
        pie.separator()
        pie.separator()
        pie.operator("object.mode_set", text = "Object Font", icon = "OBJECT_DATA")
        pie.separator()
        pie.separator()

    def draw_empty_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.editmode_toggle", text="Edit Font", icon='OBJECT_DATAMODE')
        pie.separator()
        op = pie.operator("wm.call_menu_pie", text="ChangeTo   ▶")
        op.name="Pie.Menu_ChangeTo"
        pie.separator()
        pie.separator()
        pie.operator("object.mode_set", text = "Object empty", icon = "OBJECT_DATA")
        pie.separator()
        pie.separator()

    def draw_speaker_mode(self, layout):
        # 添加相应的操作符
        pie = layout.menu_pie()
        pie.operator("object.editmode_toggle", text="Edit Font", icon='OBJECT_DATAMODE')
        pie.separator()
        op = pie.operator("wm.call_menu_pie", text="ChangeTo   ▶")
        op.name="Pie.Menu_ChangeTo"
        pie.separator()
        pie.separator()
        pie.operator("object.mode_set", text = "Object Speaker", icon = "OBJECT_DATA")
        pie.separator()
        pie.separator()
        
classes = [PIE_OT_ClassObject,
PIE_OT_SetObjectModePie,PIE_OT_ClassVertex,PIE_OT_ClassEdge,PIE_OT_ClassFace,PIE_OT_VertsEdgesFaces,PIE_OT_classvertexop,PIE_OT_classedgeop,PIE_OT_vertsfacesop,PIE_OT_classfaceop,PIE_OT_vertsedgesfacesop,
SelectAndSwitchToVertexMode,SelectAndSwitchToEdgeMode,SelectAndSwitchToFaceMode,
SelectAndSwitchToObjectMode,

SubPieMenu_ChangeTo,SubPieMenu_Armature,SubPieMenu_R_E_UV,

PIE_MO_R,
MaYaPieMenuR,

]
#以上都是classes里的名称,而注册和反注册里一般不需要改动,除非有新的按键功能


def register():
    for cls in classes:
        bpy.utils.register_class(cls)



def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)



if __name__ == "__main__":
    register()
