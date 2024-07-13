import bpy
import blf
import bgl
import mathutils
from bpy_extras import view3d_utils

######################
#######################基本
#####overlay
class DrawText:
    def __init__(self,context,scale=1,x_offset=0,fontcolor=(1,0,1,0.8),y_offset=0,inputString="",):
        self.fontcolor = fontcolor
        self.inputString = inputString
        self.scale = scale
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.handle = bpy.types.SpaceView3D.draw_handler_add(
                   self.draw_text_callback,(context,),
                   'WINDOW', 'POST_PIXEL')
    def draw_text_callback(self, context):
        font_id = 0
        blf.size(font_id, int(0.6 * self.scale))
        x = int(self.x_offset)
        y = int(50 + self.y_offset)
        blf.color(font_id,self.fontcolor[0],self.fontcolor[1],self.fontcolor[2],self.fontcolor[3])
        
        blf.position(font_id, x,y,0)
        blf.draw(font_id, (self.inputString))
    def remove_handle(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')

def HubColors():
    HubColrs = { "BrandName":(0,0.7,1,1),
                "TopText":(0.83,0.85,0.9,0.8),
                "LowerText":(0.83,0.85,0.9,0.3),
                "HelpText":(1,1,1,1),
                "HelpDescr":(.8,.8,.8,1),}
    return HubColrs

def remove_hud(context):
    Hud = bpy.app.driver_namespace
    for key in ["HudCamera_BrandName", "HudCamera_TopText", "HudCamera_LowerText","HudCamera_HelpText","HudCamera_HelpDescr","HudTransform_BrandName","HudTransform_TopText"]:
        if key in Hud:
            Hud[key].remove_handle()
            del Hud[key]
    context.area.tag_redraw()
    # 强制刷新视图区域
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

###########################基本
###########################实例
def draw_Hud_Camera(self,context):

    HudCamera = bpy.app.driver_namespace
    EndX = context.area.width
    MidX = EndX * 0.5
    HubColrs = HubColors()
    HudCamera["HudCamera_BrandName"] = DrawText(context,40,(MidX-110),HubColrs["BrandName"],20,     "Camera             "  ,)
    HudCamera["HudCamera_TopText"]   = DrawText(context,40,(MidX-50),HubColrs["TopText"],20,        "             Control",)                                                
    HudCamera["HudCamera_LowerText"] = DrawText(context,32,(MidX-115),HubColrs["LowerText"] ,0,  "TAB, RMB, ESC tool to Exit",)
    HudCamera["HudCamera_HelpText"] = DrawText(context,32,(MidX-115),HubColrs["HelpText"] ,-20,  "W, A, S,D is Moving",)
    HudCamera["HudCamera_HelpDescr"] = DrawText(context,32,(MidX-115),HubColrs["HelpDescr"] ,-40,  "MMB is Rotation, Weel is Zoom",)

    context.area.tag_redraw()

def draw_Hud_Transform(self,context):

    HudTransform = bpy.app.driver_namespace
    EndX = context.area.width
    MidX = EndX * 0.5
    HubColrs = HubColors()
    HudTransform["HudTransform_BrandName"] = DrawText(context,40,(MidX-110),HubColrs["BrandName"],0,     "Maya             "  ,)
    HudTransform["HudTransform_TopText"]   = DrawText(context,40,(MidX-50),HubColrs["TopText"],0,        "             TransformComponents",)                                                


    context.area.tag_redraw()
######################

class MayaTransformComponents(bpy.types.Operator):
    bl_idname = "object.maya_transform_components"
    bl_label = "Maya Smart Transform Components"

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC', 'Q'}:
            context.window.cursor_modal_restore()
            self.restore_transform_orientation(context)
            remove_hud(context)
            return {'CANCELLED'}
        
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'MIDDLEMOUSE', 'LEFTMOUSE'} and event.alt:
            return {'PASS_THROUGH'}

        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            draw_Hud_Transform(self, context)
            self.store_transform_orientation(context)
#            context.window.cursor_modal_set('HAND')
            context.scene.transform_orientation_slots[0].type = 'NORMAL'
            
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            remove_hud(context)
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
    
    def store_transform_orientation(self, context):
        self.previous_orientation = context.scene.transform_orientation_slots[0].type
    
    def restore_transform_orientation(self, context):
        context.scene.transform_orientation_slots[0].type = self.previous_orientation

######################

class OBJECT_OT_camera_pan(bpy.types.Operator):
    """Pan and Rotate Camera in Camera View"""
    bl_idname = "object.camera_pan"
    bl_label = "Camera Pan"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.keymap = {
            'W': False,
            'S': False,
            'A': False,
            'D': False,
            'MIDDLEMOUSE': False
        }
        self.direction = mathutils.Vector((0.0, 0.0, 0.0))
        self.mouse_init_pos = (0, 0)
        self.default_cursor = 'DEFAULT'
        self.zoom_speed = 0.1
        self._handle = None

    def modal(self, context, event):
        camera = context.scene.camera
        

        # Check for exit keys
        if event.type in {'RIGHTMOUSE', 'ESC', 'Q'}:
            context.window.cursor_modal_restore()
            if self._handle:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.tag_redraw()
            remove_hud(context)
            return {'CANCELLED'}

        # Update keymap state
        if event.type in self.keymap.keys():
            if event.value == 'PRESS':
                self.keymap[event.type] = True
                if event.type == 'MIDDLEMOUSE':
                    self.mouse_init_pos = (event.mouse_x, event.mouse_y)
            elif event.value == 'RELEASE':
                self.keymap[event.type] = False
                if event.type == 'MIDDLEMOUSE':
                    self.mouse_init_pos = (event.mouse_x, event.mouse_y)  # Reset mouse initial position

        # Calculate direction based on keymap state
        self.direction = mathutils.Vector((0.0, 0.0, 0.0))
        if self.keymap['W']:
            self.direction += mathutils.Vector((0, 0.1, 0))
        if self.keymap['S']:
            self.direction += mathutils.Vector((0, -0.1, 0))
        if self.keymap['A']:
            self.direction += mathutils.Vector((-0.1, 0, 0))
        if self.keymap['D']:
            self.direction += mathutils.Vector((0.1, 0, 0))

        # Smooth transition to new location
        if self.direction.length > 0:
            new_location = camera.location + camera.matrix_world.to_quaternion() @ self.direction
            camera.location = camera.location.lerp(new_location, 0.2)

        # Handle camera rotation and cursor
        if self.keymap['MIDDLEMOUSE']:
            delta_x = event.mouse_x - self.mouse_init_pos[0]
            delta_y = event.mouse_y - self.mouse_init_pos[1]
            abs_delta_x = abs(delta_x)
            abs_delta_y = abs(delta_y)

            if abs_delta_x > abs_delta_y:
                rotation_angle_x = -delta_x * 0.002  # Adjust this multiplier for sensitivity
                rotation_quat_x = mathutils.Quaternion((0, 0, 1), rotation_angle_x)
                camera.rotation_euler.rotate(rotation_quat_x)
                context.window.cursor_modal_set('SCROLL_X')
            else:
                rotation_angle_y = -delta_y * 0.002 / 3  # Y-axis rotation is 1/3 of X-axis rotation
                rotation_quat_y = mathutils.Quaternion((1, 0, 0), rotation_angle_y)
                camera.rotation_euler.rotate(rotation_quat_y)
                context.window.cursor_modal_set('SCROLL_Y')
                
            self.mouse_init_pos = (event.mouse_x, event.mouse_y)  # Update initial mouse position
        else:
            context.window.cursor_modal_set('HAND')

        # Zoom camera with mouse scroll wheel
        if event.type == 'WHEELUPMOUSE':
            camera.location -= camera.matrix_world.to_quaternion().to_matrix().col[2] * self.zoom_speed
        elif event.type == 'WHEELDOWNMOUSE':
            camera.location += camera.matrix_world.to_quaternion().to_matrix().col[2] * self.zoom_speed

        # Force redraw to update the viewport
        context.area.tag_redraw()

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        draw_Hud_Camera(self, context)
        if context.space_data.type == 'VIEW_3D':
            self.mouse_init_pos = (context.region.width // 2, context.region.height // 2)
            self.default_cursor = context.window.cursor_set('HAND')
            
            # Ensure the operator starts in camera view
            if context.space_data.region_3d.view_perspective != 'CAMERA':
                bpy.ops.view3d.view_camera()

            context.window_manager.modal_handler_add(self)
            # Comment out the draw handler since we're removing the text display
            # self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (context,), 'WINDOW', 'POST_PIXEL')
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a 3D View")
            return {'CANCELLED'}
######################################

######################################
class OBJECT_OT_aim_camera_at_target(bpy.types.Operator):
    """Aim Camera at Target"""
    bl_idname = "object.aim_camera_at_target"
    bl_label = "Aim Camera at Target"
    bl_options = {'REGISTER', 'UNDO'}
    
    _target_obj = None
    _default_cursor = None
    _handle = None

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'LEFTMOUSE', 'ESC', 'RIGHTMOUSE'}:
            # Restore cursor and end modal
            context.window.cursor_modal_restore()
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if event.type == 'LEFTMOUSE' and self._target_obj:
                self.aim_camera(context)
                return {'FINISHED'}
            return {'CANCELLED'}

        if event.type == 'MOUSEMOVE':
            region = context.region
            rv3d = context.region_data
            coord = event.mouse_region_x, event.mouse_region_y
            self._target_obj = self.pick_object(context, region, rv3d, coord)
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            self._default_cursor = context.window.cursor_set('EYEDROPPER')
            context.window_manager.modal_handler_add(self)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (context,), 'WINDOW', 'POST_PIXEL')
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a 3D View")
            return {'CANCELLED'}

    def pick_object(self, context, region, rv3d, coord):
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + view_vector

        def visible_objects_and_duplis():
            for obj in context.visible_objects:
                if obj.type not in {'CAMERA', 'LIGHT'}:
                    yield (obj, obj.matrix_world.copy())

        def obj_ray_cast(obj, matrix):
            matrix_inv = matrix.inverted()
            ray_origin_obj = matrix_inv @ ray_origin
            ray_target_obj = matrix_inv @ ray_target
            ray_direction_obj = ray_target_obj - ray_origin_obj
            if obj.type == 'MESH':
                success, location, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj)
                if success:
                    return location, normal, face_index
            return None, None, None

        best_length_squared = -1.0
        best_obj = None

        for obj, matrix in visible_objects_and_duplis():
            hit, normal, face_index = obj_ray_cast(obj, matrix)
            if hit is not None:
                hit_world = matrix @ hit
                length_squared = (hit_world - ray_origin).length_squared
                if best_obj is None or length_squared < best_length_squared:
                    best_length_squared = length_squared
                    best_obj = obj

        return best_obj

    def aim_camera(self, context):
        camera = context.active_object
        if not camera or camera.type != 'CAMERA':
            self.report({'WARNING'}, "Active object is not a camera")
            return
        
        if self._target_obj:
            direction = self._target_obj.location - camera.location
            rot_quat = direction.to_track_quat('-Z', 'Y')
            camera.rotation_euler = rot_quat.to_euler()
        else:
            self.report({'WARNING'}, "No target selected")

    def draw_callback_px(self, context):
        if self._target_obj:
            font_id = 0
            blf.position(font_id, 15, 15, 0)
            blf.size(font_id, 20, 72)
            blf.draw(font_id, f"Target: {self._target_obj.name}")
#`````````````````````````````````````````

class OBJECT_OT_create_camera_from_view(bpy.types.Operator):
    """Create Camera from Current View"""
    bl_idname = "object.create_camera_from_view"
    bl_label = "Create Camera from View"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 获取当前视图矩阵
        region = context.region
        rv3d = context.region_data
        space_data = context.space_data
        
        if rv3d is None or not isinstance(space_data, bpy.types.SpaceView3D):
            self.report({'WARNING'}, "Active space must be a 3D View")
            return {'CANCELLED'}
        
        # 创建一个新摄像机对象
        bpy.ops.object.camera_add()
        camera = context.active_object
        
        # 设置摄像机位置和旋转
        camera.location = rv3d.view_matrix.inverted().translation
        camera.rotation_euler = rv3d.view_rotation.to_euler()
        
        # 设置摄像机透视和剪切面
        camera.data.lens = space_data.lens
        camera.data.clip_start = space_data.clip_start
        camera.data.clip_end = space_data.clip_end
        
        # 将新创建的摄像机设置为活动摄像机
        context.scene.camera = camera
        
        return {'FINISHED'}

#
class OBJECT_OT_RendingCameraCycles(bpy.types.Operator):
    """Render with Cycles Settings"""
    bl_idname = "object.rendering_camera_cycles"
    bl_label = "Rendering Camera Cycles"

    def execute(self, context):
        scene = context.scene

        # 设置渲染引擎为Cycles
        scene.render.engine = 'CYCLES'

        # 选择GPU设备
        preferences = bpy.context.preferences
        cycles_preferences = preferences.addons['cycles'].preferences
        cycles_preferences.compute_device_type = 'CUDA'
        bpy.context.scene.cycles.device = 'GPU'

        # 设置渲染采样
        scene.cycles.samples = 8192
        scene.cycles.preview_samples = 512

        # 进入渲染菜单并渲染图像
        bpy.ops.render.render("INVOKE_DEFAULT")

        return {'FINISHED'}


    

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_camera_pan.bl_idname)
    self.layout.operator(OBJECT_OT_create_camera_from_view.bl_idname)

    self.layout.operator(OBJECT_OT_aim_camera_at_target.bl_idname)
    
    self.layout.operator(OBJECT_OT_RendingCameraCycles.bl_idname)
    
    self.layout.operator(MayaTransformComponents.bl_idname)

Maya_menu_func = (lambda self, context: self.layout.operator(MayaTransformComponents.bl_idname))

def register():
    bpy.utils.register_class(OBJECT_OT_camera_pan)
    bpy.utils.register_class(OBJECT_OT_create_camera_from_view)

    bpy.utils.register_class(OBJECT_OT_aim_camera_at_target)
    bpy.utils.register_class(OBJECT_OT_RendingCameraCycles)
    
    bpy.utils.register_class(MayaTransformComponents)

    
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh.append(Maya_menu_func)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_camera_pan)
    bpy.utils.unregister_class(OBJECT_OT_create_camera_from_view)

    bpy.utils.unregister_class(OBJECT_OT_aim_camera_at_target)
    bpy.utils.unregister_class(OBJECT_OT_RendingCameraCycles)
    
    bpy.utils.unregister_class(MayaTransformComponents)

    
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh.remove(Maya_menu_func)


if __name__ == "__main__":
    register()