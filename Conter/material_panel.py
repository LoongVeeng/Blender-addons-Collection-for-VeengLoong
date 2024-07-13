import bpy
from bpy.props import BoolProperty, StringProperty, CollectionProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup
import os

#

# 定义一个属性组用于纹理插槽
class TextureSlotPropertyGroup(PropertyGroup):
    # 更新纹理时调用的回调函数
    def update_texture(self, context):
        bpy.ops.quick_sword_texture.update_texture_file()  # 调用操作符以应用节点更新

    
    basecolor_texture: PointerProperty(
        type=bpy.types.Image,
        name="BaseColor Texture",
        description="用于 BaseColor 的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    metallic_texture: PointerProperty(
        type=bpy.types.Image,
        name="Metallic Texture",
        description="用于金属度贴图的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    roughness_texture: PointerProperty(
        type=bpy.types.Image,
        name="Roughness Texture",
        description="用于粗糙度贴图的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    specular_texture: PointerProperty(
        type=bpy.types.Image,
        name="Specular Texture",
        description="用于高光的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    sss_texture: PointerProperty(
        type=bpy.types.Image,
        name="SSS Texture",
        description="用于通透的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    emission_texture: PointerProperty(
        type=bpy.types.Image,
        name="Emission Texture",
        description="用于自发光贴图的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    displacement_height_texture: PointerProperty(
        type=bpy.types.Image,
        name="Displacement Texture",
        description="用于置换高度的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    ao_texture: PointerProperty(
        type=bpy.types.Image,
        name="AO Texture",
        description="用于环境光遮蔽的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    normal_texture: PointerProperty(
        type=bpy.types.Image,
        name="Normal Texture",
        description="用于法线贴图的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    opacity_texture: PointerProperty(
        type=bpy.types.Image,
        name="Opacity Texture",
        description="用于透明度的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    bump_texture: PointerProperty(
        type=bpy.types.Image,
        name="Bump Texture",
        description="用于凹凸贴图的纹理",
        update=update_texture  # 当纹理更新时调用回调函数
    )
    use_udim: BoolProperty(
        name="UDIM",
        description="勾选以使用UDIM平铺贴图",
        default=False,
        update=update_texture#????????????????????
    )
    use_ao: BoolProperty(
        name="使用AO节点",
        description="切换添加或移除AO节点",
        default=False,
        update=update_texture  # 当布尔值更新时调用回调函数
    )
    use_sss: BoolProperty(
        name="使用SSS节点",
        description="切换添加或移除通透节点",
        default=False,
        update=update_texture  # 当布尔值更新时调用回调函数
    )
    use_specular: BoolProperty(
        name="使用S高光节点",
        description="切换添加或移除高光节点",
        default=False,
        update=update_texture  # 当布尔值更新时调用回调函数
    )
    use_emission: BoolProperty(
        name="使用发光节点",
        description="切换添加或移除发光节点",
        default=False,
        update=update_texture  # 当布尔值更新时调用回调函数
    )
    use_displacement_height: BoolProperty(
        name="使用置换或高度节点",
        description="勾选以使用置换或高度贴图",
        default=False,
        update=update_texture  # 当布尔值更新时调用回调函数
    )
    use_directx: BoolProperty(
        name="使用DirectX法线",
        description="切换使用 DirectX 法线贴图",
        default=False,
        update=update_texture  # 当布尔值更新时调用回调函数
    )
    use_opacity: BoolProperty(
        name="使用不透明度",
        description="切换添加或移除不透明度节点",
        default=False,
        update=update_texture  # 当布尔值更新时调用回调函数
    )
    use_bump: BoolProperty(
        name="使用Bump",
        description="切换添加或移除Bump节点",
        default=False,
        update=update_texture  # 当布尔值更新时调用回调函数
    )
    use_bump_disp: BoolProperty(
        name="使用Bump和Disp混合",
        description="切换混合",
        default=False,
        update=update_texture  # 当布尔值更新时调用回调函数
    )

######################################


######################################

#####
# 定义一个操作符用于更新纹理文件
class QUICK_SWORD_TEXTURE_OT_update_texture_file(Operator):
    bl_idname = "quick_sword_texture.update_texture_file"
    bl_label = "更新纹理文件"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mat = context.object.active_material  # 获取当前活动材质
        if not mat:
            self.report({'WARNING'}, "无活动材质")
            return {'CANCELLED'}
        
        mat.use_nodes = True  # 启用节点
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        def set_colorspace(node, colorspace):
            """设置纹理节点的色彩空间"""
            if node:
                node.image.colorspace_settings.name = colorspace

        def set_udim(node, use_udim):
            """设置纹理节点的UDIM属性"""
            if node and node.image:
                node.image.source = 'TILED' if use_udim else 'FILE'

        def get_or_create_texture_node(image, label, node_name, location):
            """获取或创建一个纹理节点"""
            texture_node = next((node for node in nodes if node.type == 'TEX_IMAGE' and node.label == label), None)
            if not texture_node:
                texture_node = nodes.new(type='ShaderNodeTexImage')
                texture_node.image = image
                texture_node.label = label
                texture_node.name = node_name
                texture_node.location = location
            return texture_node

        def remove_texture_node(node_name):
            """移除指定名称的纹理节点"""
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.name == node_name:
                    nodes.remove(node)

        def remove_node_by_type(node_type):
            """移除指定类型的节点"""
            for node in nodes:
                if node.type == node_type:
                    nodes.remove(node)
        
        def update_texture(texture, label, node_name, colorspace, input_name, use_udim, location, use_texture=True):
            """更新或移除纹理节点"""
            if texture and use_texture:
                node = get_or_create_texture_node(texture, label, node_name, location)
                set_colorspace(node, colorspace)
                set_udim(node, use_udim)
                links.new(node.outputs['Color'], input_name)
            else:
                remove_texture_node(node_name)
        
        # 清除现有的正片叠底节点
        for node in nodes:
            if node.type == 'MIX_RGB' and node.blend_type == 'MULTIPLY':
                nodes.remove(node)

        # 查找 Principled BSDF 节点
        principled_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)

        if not principled_node:
            self.report({'WARNING'}, "未找到 Principled BSDF 节点")
            return {'CANCELLED'}

        # 更新 BaseColor 纹理节点
        update_texture(
            context.scene.custom_material_props.basecolor_texture,
            "BaseColor", "basecolor_texture_node",
            'sRGB', principled_node.inputs['Base Color'],
            context.scene.custom_material_props.use_udim,
            (-600, 455)
        )

        # 更新 AO 纹理节点
        if context.scene.custom_material_props.use_ao:
            ao_texture = context.scene.custom_material_props.ao_texture
            if ao_texture:
                ao_node = get_or_create_texture_node(ao_texture, "AO", "ao_texture_node", (-860, 500))
                set_colorspace(ao_node, 'Non-Color')
                set_udim(ao_node, context.scene.custom_material_props.use_udim)

                multiply_node = nodes.new(type='ShaderNodeMixRGB')
                multiply_node.blend_type = 'MULTIPLY'
                multiply_node.location = (-275, 600)

                links.new(ao_node.outputs['Color'], multiply_node.inputs[1])
                basecolor_node = get_or_create_texture_node(context.scene.custom_material_props.basecolor_texture, "BaseColor", "basecolor_texture_node", (-600, 455))
                links.new(basecolor_node.outputs['Color'], multiply_node.inputs[2])
                links.new(multiply_node.outputs['Color'], principled_node.inputs['Base Color'])
            else:
                remove_texture_node("ao_texture_node")
        else:
            remove_texture_node("ao_texture_node")

        # 更新 Normal 纹理节点
        normal_texture = context.scene.custom_material_props.normal_texture
        if normal_texture:
            normal_node = get_or_create_texture_node(normal_texture, "Normal", "normal_texture_node", (-860, -365))
            set_colorspace(normal_node, 'Non-Color')
            set_udim(normal_node, context.scene.custom_material_props.use_udim)

            normal_map_node = next((node for node in nodes if node.type == 'NORMAL_MAP'), None)
            if not normal_map_node:
                normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                normal_map_node.location = (-334, -265)

            bump_node = next((node for node in nodes if node.type == 'BUMP'), None)
            if not bump_node:
                bump_node = nodes.new(type='ShaderNodeBump')
                bump_node.location = (-170, -305)

            rgb_curves_node = next((node for node in nodes if node.type == 'CURVE_RGB'), None)
            if context.scene.custom_material_props.use_directx:
                if not rgb_curves_node:
                    rgb_curves_node = nodes.new(type='ShaderNodeRGBCurve')
                    rgb_curves_node.location = (-600, -205)
                for point in rgb_curves_node.mapping.curves[1].points:
                    point.location = (0.0, 1.0) if point.location.x == 0.0 else (1.0, 0.0)
                links.new(rgb_curves_node.outputs['Color'], normal_map_node.inputs['Color'])
                links.new(normal_node.outputs['Color'], rgb_curves_node.inputs['Color'])
            else:
                if rgb_curves_node:
                    nodes.remove(rgb_curves_node)
                links.new(normal_node.outputs['Color'], normal_map_node.inputs['Color'])

            links.new(normal_map_node.outputs['Normal'], bump_node.inputs['Normal'])
            links.new(bump_node.outputs['Normal'], principled_node.inputs['Normal'])
        else:
            remove_texture_node("normal_texture_node")
            remove_node_by_type('NORMAL_MAP')
            remove_node_by_type('BUMP')
            remove_node_by_type('CURVE_RGB')
            links.new(principled_node.outputs['BSDF'], next(node for node in nodes if node.type == 'OUTPUT_MATERIAL').inputs['Surface'])

        # 更新其他纹理节点
        texture_settings = [
            ("metallic_texture", "Metallic", "metallic_texture_node", 'Non-Color', principled_node.inputs['Metallic'], (-600, 80)),
            ("roughness_texture", "Roughness", "roughness_texture_node", 'Non-Color', principled_node.inputs['Roughness'], (-300, 20)),
            ("emission_texture", "Emission", "emission_texture_node", 'sRGB', principled_node.inputs['Emission'], (-600, -205), context.scene.custom_material_props.use_emission),
            ("specular_texture", "Specular", "specular_texture_node", 'Non-Color', principled_node.inputs['Specular'], (-860, -83), context.scene.custom_material_props.use_specular),
            ("sss_texture", "SSS", "sss_texture_node", 'Non-Color', principled_node.inputs['Subsurface'], (-860, 200), context.scene.custom_material_props.use_sss),
            ("opacity_texture", "Opacity", "opacity_texture_node", 'Non-Color', principled_node.inputs['Alpha'], (-50, 850), context.scene.custom_material_props.use_opacity),
        ]
        for texture_attr, label, node_name, colorspace, input_name, location, *use_texture in texture_settings:
            update_texture(
                getattr(context.scene.custom_material_props, texture_attr), label, node_name,
                colorspace, input_name, context.scene.custom_material_props.use_udim,
                location, use_texture[0] if use_texture else True
            )
        # 处理置换贴图纹理节点
        displacement_height_texture = context.scene.custom_material_props.displacement_height_texture
        if displacement_height_texture and context.scene.custom_material_props.use_displacement_height:
            displacement_height_texture_node = get_or_create_texture_node(displacement_height_texture, "Displacement Height", "displacement_height_texture_node", (-230, -562))
            set_colorspace(displacement_height_texture_node, 'Non-Color')
            set_udim(displacement_height_texture_node, context.scene.custom_material_props.use_udim)
            displacement_node = next((node for node in nodes if node.type == 'DISPLACEMENT'), None)
            if not displacement_node:
                displacement_node = nodes.new(type='ShaderNodeDisplacement')
                displacement_node.location = (50, -500)
            links.new(displacement_height_texture_node.outputs['Color'], displacement_node.inputs['Normal'])
            links.new(displacement_node.outputs['Displacement'], next(node for node in nodes if node.type == 'OUTPUT_MATERIAL').inputs['Displacement'])
        else:
            remove_texture_node("displacement_height_texture_node")
            remove_node_by_type('DISPLACEMENT')
        # 处理凹凸贴图纹理节点
        bump_texture = context.scene.custom_material_props.bump_texture
        if bump_texture and context.scene.custom_material_props.use_bump:
            bump_node = get_or_create_texture_node(bump_texture, "Bump", "bump_texture_node", (-600, -500))
            set_colorspace(bump_node, 'Non-Color')
            set_udim(bump_node, context.scene.custom_material_props.use_udim)
            bump_map_node = next((node for node in nodes if node.type == 'BUMP'), None)
            if not bump_map_node:
                bump_map_node = nodes.new(type='ShaderNodeBump')
                bump_map_node.location = (-170, -305)
            links.new(bump_node.outputs['Color'], bump_map_node.inputs['Height'])
            links.new(bump_map_node.outputs['Normal'], principled_node.inputs['Normal'])
        else:
            remove_texture_node("bump_texture_node")
        if bump_texture and context.scene.custom_material_props.use_bump_disp:
        	links.new(bump_node.outputs['Color'], displacement_node.inputs['Height'])
        else:
        	links.remove(links.new(bump_node.outputs['Color'], displacement_node.inputs['Height']))
        return {'FINISHED'}


##################################################

##################################################
class QUICK_SWORD_TEXTURE_OT_update_texture_file4(Operator):
    bl_idname = "quick_sword_texture.update_texture_file"
    bl_label = "更新纹理文件"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        mat = context.object.active_material  # 获取当前活动材质
        if not mat:
            self.report({'WARNING'}, "无活动材质")
            return {'CANCELLED'}
        
        mat.use_nodes = True  # 启用节点
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        def set_colorspace(node, colorspace):
            """设置纹理节点的色彩空间"""
            if node:
                node.image.colorspace_settings.name = colorspace

        def set_udim(node, use_udim):
            """设置纹理节点的UDIM属性"""
            if node and node.image:
                node.image.source = 'TILED' if use_udim else 'FILE'

        def get_or_create_texture_node(image, label, node_name):
            """获取或创建一个纹理节点"""
            texture_node = None
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.label == label:
                    texture_node = node
                    break
            if not texture_node:
                texture_node = nodes.new(type='ShaderNodeTexImage')
                texture_node.image = image
                texture_node.label = label
                texture_node.name = node_name
                
                # 设置节点位置
                if texture_node.name == "basecolor_texture_node":
                    texture_node.location = (-600, 455)
                elif texture_node.name == "ao_texture_node":
                    texture_node.location = (-860, 500)
                elif texture_node.name == "metallic_texture_node":
                    texture_node.location = (-600, 80)
                elif texture_node.name == "roughness_texture_node":
                    texture_node.location = (-300, 20)
                elif texture_node.name == "sss_texture_node":
                    texture_node.location = (-860, 200)
                elif texture_node.name == "specular_texture_node":
                    texture_node.location = (-860, -83)
                elif texture_node.name == "emission_texture_node":
                    texture_node.location = (-600, -205)
                elif texture_node.name == "opacity_texture_node":
                    texture_node.location = (-50, 850)
                elif texture_node.name == "displacement_height_texture_node":
                    texture_node.location = (-230, -562)
                elif texture_node.name == "bump_texture_node":
                    texture_node.location = (-600, -500)
                elif texture_node.name == "normal_texture_node":
                    texture_node.location = (-860, -365)
                

            return texture_node
        def remove_texture_node(node_name):
            """移除指定名称的纹理节点"""
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.name == node_name:
                    nodes.remove(node)
        def remove_node_by_type(node_type):
            """移除指定类型的节点"""
            for node in nodes:
                if node.type == node_type:
                    nodes.remove(node)
        
        # 清除现有的正片叠底节点
        for node in nodes:
            if node.type == 'MIX_RGB' and node.blend_type == 'MULTIPLY':
                nodes.remove(node)

        # 查找 Principled BSDF 节点
        principled_node = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled_node = node
                break

        if not principled_node:
            self.report({'WARNING'}, "未找到 Principled BSDF 节点")
            return {'CANCELLED'}

        # 处理 BaseColor 纹理节点
        basecolor_texture = context.scene.custom_material_props.basecolor_texture
        if basecolor_texture:
            basecolor_node = get_or_create_texture_node(basecolor_texture, "BaseColor", "basecolor_texture_node")
            set_colorspace(basecolor_node, 'sRGB')
            set_udim(basecolor_node, context.scene.custom_material_props.use_udim)
            links.new(basecolor_node.outputs['Color'], principled_node.inputs['Base Color'])
            
        else:
            remove_texture_node("basecolor_texture_node")
        # 根据 use_ao 属性处理 AO 节点
        if context.scene.custom_material_props.use_ao:
            ao_texture = context.scene.custom_material_props.ao_texture
            if ao_texture:
                ao_node = get_or_create_texture_node(ao_texture, "AO", "ao_texture_node")
                set_colorspace(ao_node, 'Non-Color')
                set_udim(ao_node, context.scene.custom_material_props.use_udim)
                # 创建正片叠底节点
                multiply_node = nodes.new(type='ShaderNodeMixRGB')
                multiply_node.blend_type = 'MULTIPLY'
                multiply_node.location = (-275, 600)
                # 连接节点
                links.new(ao_node.outputs['Color'], multiply_node.inputs[1])
                if basecolor_texture:
                    basecolor_node = get_or_create_texture_node(basecolor_texture, "BaseColor", "basecolor_texture_node")
                    links.new(basecolor_node.outputs['Color'], multiply_node.inputs[2])
                links.new(multiply_node.outputs['Color'], principled_node.inputs['Base Color'])
            else:
            	remove_texture_node("ao_texture_node")
        else:
            remove_texture_node("ao_texture_node")
        # 处理 Normal 纹理节点
        normal_texture = context.scene.custom_material_props.normal_texture
        if normal_texture:
            normal_node = get_or_create_texture_node(normal_texture, "Normal", "normal_texture_node")
            set_colorspace(normal_node, 'Non-Color')
            set_udim(normal_node, context.scene.custom_material_props.use_udim)
            normal_map_node = None
            bump_node = None
            rgb_curves_node = None
            # 查找现有节点
            for node in nodes:
                if node.type == 'NORMAL_MAP':
                    normal_map_node = node
                elif node.type == 'BUMP':
                    bump_node = node
                elif node.type == 'CURVE_RGB':
                    rgb_curves_node = node
            # 如果没有 Normal Map 节点，则创建一个
            if not normal_map_node:
                normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                normal_map_node.location = (-334, -265)
            # 如果没有 Bump 节点，则创建一个
            if not bump_node:
                bump_node = nodes.new(type='ShaderNodeBump')
                bump_node.location = (-170, -305)
            # 根据 use_directx 属性处理 RGB 曲线节点
            if context.scene.custom_material_props.use_directx:
                if not rgb_curves_node:
                    rgb_curves_node = nodes.new(type='ShaderNodeRGBCurve')
                    rgb_curves_node.location = (-600, -205)
                # 设置 RGB 曲线节点的数据
                for point in rgb_curves_node.mapping.curves[1].points:
                    if point.location.x == 0.0:
                        point.location = (0.0, 1.0)
                    elif point.location.x == 1.0:
                        point.location = (1.0, 0.0)
                links.new(rgb_curves_node.outputs['Color'], normal_map_node.inputs['Color'])
                links.new(normal_node.outputs['Color'], rgb_curves_node.inputs['Color'])
            else:
                # 移除 RGB 曲线节点
                if rgb_curves_node:
                    nodes.remove(rgb_curves_node)
                links.new(normal_node.outputs['Color'], normal_map_node.inputs['Color'])
            links.new(normal_map_node.outputs['Normal'], bump_node.inputs['Normal'])
            links.new(bump_node.outputs['Normal'], principled_node.inputs['Normal'])
        else:
            # 移除 Normal 相关节点
            remove_texture_node("normal_texture_node")
            # 移除 Normal Map 节点
            for node in nodes:
                if node.type == 'NORMAL_MAP':
                    nodes.remove(node)
            # 移除 Bump 节点
            for node in nodes:
                if node.type == 'BUMP':
                    nodes.remove(node)
            # 移除 RGB 曲线节点
            for node in nodes:
                if node.type == 'CURVE_RGB':
                    nodes.remove(node)
            # 重新连接 Principled BSDF
            for node in nodes:
                if node.type == 'OUTPUT_MATERIAL':
                    material_output_node = node
                    break
            links.new(principled_node.outputs['BSDF'], material_output_node.inputs['Surface'])

        # 处理 Metallic 纹理节点
        metallic_texture = context.scene.custom_material_props.metallic_texture
        if metallic_texture:
            metallic_node = get_or_create_texture_node(metallic_texture, "Metallic", "metallic_texture_node")
            set_colorspace(metallic_node, 'Non-Color')
            set_udim(metallic_node, context.scene.custom_material_props.use_udim)
            links.new(metallic_node.outputs['Color'], principled_node.inputs['Metallic'])
        else:
            remove_texture_node("metallic_texture_node")

        # 处理 Roughness 纹理节点
        roughness_texture = context.scene.custom_material_props.roughness_texture
        if roughness_texture:
            roughness_node = get_or_create_texture_node(roughness_texture, "Roughness", "roughness_texture_node")
            set_colorspace(roughness_node, 'Non-Color')
            set_udim(roughness_node, context.scene.custom_material_props.use_udim)
            links.new(roughness_node.outputs['Color'], principled_node.inputs['Roughness'])
        else:
            remove_texture_node("roughness_texture_node")

        # 处理 Emission 纹理节点
        emission_texture = context.scene.custom_material_props.emission_texture
        if emission_texture and context.scene.custom_material_props.use_emission:
            emission_node = get_or_create_texture_node(emission_texture, "Emission", "emission_texture_node")
            set_colorspace(emission_node, 'sRGB')
            set_udim(emission_node, context.scene.custom_material_props.use_udim)
            links.new(emission_node.outputs['Color'], principled_node.inputs['Emission Color'])
            principled_node.inputs['Emission Strength'].default_value = 1  # 设置 Emission Strength 为 1
        else:
            remove_texture_node("emission_texture_node")
            principled_node.inputs['Emission Strength'].default_value = 0  # 设置 Emission Strength 为 0

        # Processing Specular Texture
        specular_texture = context.scene.custom_material_props.specular_texture
        if specular_texture and context.scene.custom_material_props.use_specular:
            specular_node = get_or_create_texture_node(specular_texture, "Specular", "specular_texture_node")
            set_colorspace(specular_node, 'Non-Color')
            set_udim(specular_node, context.scene.custom_material_props.use_udim)
            links.new(specular_node.outputs['Color'], principled_node.inputs['Specular IOR Level'])
        else:
            remove_texture_node("specular_texture_node")

        # Processing SSS Texture
        sss_texture = context.scene.custom_material_props.sss_texture
        if sss_texture and context.scene.custom_material_props.use_sss:
            sss_node = get_or_create_texture_node(sss_texture, "SSS", "sss_texture_node")
            set_colorspace(sss_node, 'Non-Color')
            set_udim(sss_node, context.scene.custom_material_props.use_udim)
            links.new(sss_node.outputs['Color'], principled_node.inputs['Subsurface Weight'])##次表明颜色还是次表面灰度
        else:
            remove_texture_node("sss_texture_node")

        # 处理 Opacity 纹理节点和 Transparent BSDF 节点
        opacity_texture = context.scene.custom_material_props.opacity_texture
        if context.scene.custom_material_props.use_opacity and opacity_texture:
            opacity_node = get_or_create_texture_node(opacity_texture, "Opacity", "opacity_texture_node")
            set_colorspace(opacity_node, 'Non-Color')
            set_udim(opacity_node, context.scene.custom_material_props.use_udim)
            links.new(opacity_node.outputs['Color'], principled_node.inputs['Alpha'])##
        else :
        	remove_texture_node("opacity_texture_node")


        # Processing 置换 Texture
        displacement_height_texture = context.scene.custom_material_props.displacement_height_texture
        displacement_node = None
        material_output_node = None

        # 查找现有的 Displacement 和 Output Material 节点
        for node in nodes:
            if node.type == 'DISPLACEMENT':
                displacement_node = node
            elif node.type == 'OUTPUT_MATERIAL':
                material_output_node = node
            if displacement_node and material_output_node:
                break

        if displacement_height_texture and context.scene.custom_material_props.use_displacement_height:
            displacement_height_texture_node = get_or_create_texture_node(displacement_height_texture, "Displacement Height", "displacement_height_texture_node")
            set_colorspace(displacement_height_texture_node, 'Non-Color')
            set_udim(displacement_height_texture_node, context.scene.custom_material_props.use_udim)
            
            # 如果没有 displacement_node 节点，则创建一个
            if not displacement_node:
                displacement_node = nodes.new(type='ShaderNodeDisplacement')
                displacement_node.location = (110, -436)
            
            # 清除现有链接，防止重复链接
            for link in displacement_node.inputs['Height'].links:
                links.remove(link)
            for link in material_output_node.inputs['Displacement'].links:
                links.remove(link)
            
            links.new(displacement_height_texture_node.outputs['Color'], displacement_node.inputs['Normal'])
            links.new(displacement_node.outputs['Displacement'], material_output_node.inputs['Displacement'])
        else:
            remove_texture_node("displacement_height_texture_node")
            if displacement_node:
                nodes.remove(displacement_node)

        # 处理凹凸贴图纹理节点
        bump_texture = context.scene.custom_material_props.bump_texture
        bump_map_node = None

        # 查找现有的 Bump 节点
        for node in nodes:
            if node.type == 'BUMP':
                bump_map_node = node
                break

        if context.scene.custom_material_props.use_bump:
            if bump_texture:
                bump_node = get_or_create_texture_node(bump_texture, "Bump", "bump_texture_node")
                set_colorspace(bump_node, 'Non-Color')
                set_udim(bump_node, context.scene.custom_material_props.use_udim)
                
                # 如果没有 bump_map_node 节点，则创建一个
                if not bump_map_node:
                    bump_map_node = nodes.new(type='ShaderNodeBump')
                    bump_map_node.location = (-170, -305)
                
                # 清除现有链接，防止重复链接
                for link in bump_map_node.inputs['Height'].links:
                    links.remove(link)
                for link in principled_node.inputs['Normal'].links:
                    links.remove(link)
                
                links.new(bump_node.outputs['Color'], bump_map_node.inputs['Height'])
                links.new(bump_map_node.outputs['Normal'], principled_node.inputs['Normal'])
            else:
                remove_texture_node("bump_texture_node")
        else:
            remove_texture_node("bump_texture_node")
            if not context.scene.custom_material_props.use_normal:
                if bump_map_node:
                    nodes.remove(bump_map_node)
###########################################
        # Processing Bump Texture for Displacement
        use_bump_disp = context.scene.custom_material_props.use_bump_disp
        if bump_texture and use_bump_disp and context.scene.custom_material_props.use_displacement_height:
            bump_node = get_or_create_texture_node(bump_texture, "Bump", "bump_texture_node")
            for node in nodes:   # 查找现有节点
                if node.type == 'DISPLACEMENT':
                    displacement_node = node
            if displacement_node:
                links.new(bump_node.outputs['Color'], displacement_node.inputs['Height'])
            else: 
	            pass
        else:
            # Disconnect bump texture from displacement node if conditions are not met
            bump_node = nodes.get('bump_texture_node')
            for node in nodes:   # 查找现有节点
                if node.type == 'DISPLACEMENT':
                    displacement_node = node
            if bump_node and displacement_node:
                # 查找并删除连接线
                links_to_remove = []
                for link in links:
                    if link.from_node == bump_node and link.to_socket == displacement_node.inputs['Height']:
                        links_to_remove.append(link)
                for link in links_to_remove:
                    links.remove(link)
        return {'FINISHED'}
##################################################

# 定义导入纹理图片操作器
class QUICK_SWORD_TEXTURE_OT_import_images(Operator):
    bl_idname = "quickswordtexture.import_images"
    bl_label = "Import Images"
    bl_options = {'REGISTER', 'UNDO'}
    filter_glob: bpy.props.StringProperty(default="*.png;*.jpg;*.jpeg;*.tga;*.bmp", options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    )

    def execute(self, context):
        import os

        props = context.scene.custom_material_props
        for file_elem in self.files:
            filepath = os.path.join(self.directory, file_elem.name)
            image = bpy.data.images.load(filepath)

            # 检查文件名并分配到正确的插槽
            if any(key in file_elem.name.lower() for key in ["_n_", "_nor", "nor_", "_normal", "normal_", " normal", "normal "]):
                props.normal_texture = image
            elif any(key in file_elem.name.lower() for key in ["_bc", "bc_","_col", "col_", "_basecolor", "basecolor_"," basecolor", "basecolor ", "_base_color", "base_color_"," base_color", "base_color "," base color", "base color ", "_albedo", "albedo_"]):
                props.basecolor_texture = image
            elif any(key in file_elem.name.lower() for key in ["_ao", "ao_", "_ambientocclusion", "ambientocclusion_", "_ambient_occlusion", "ambient_occlusion_", " ambientocclusion", "ambientocclusion ", "_ambient occlusion", " ambient occlusion", "ambient occlusion ", "ambient occlusion_"]):
                if props.use_ao:
                    props.ao_texture = image
            elif any(key in file_elem.name.lower() for key in ["_metal", "metal_", " metallic", "metallic ", "_metallic", "metallic_"]):
                props.metallic_texture = image
            elif any(key in file_elem.name.lower() for key in ["_rough", "rough_", " roughness", "roughness ", "_roughness", "roughness_"]):
                props.roughness_texture = image
            elif any(key in file_elem.name.lower() for key in ["_spec", "spec_", " spec", "spec ", "_specular", "specular_", "specular ", " specular"]):
                if props.use_specular:
                    props.specular_texture = image
            elif any(key in file_elem.name.lower() for key in ["_sss", "sss_", " sss", "sss "]):
                if props.use_sss:
                    props.sss_texture = image
            elif any(key in file_elem.name.lower() for key in ["_opacity", "opacity_", " opacity", "opacity ", "_op", "op_", "_opac", "opac_"]):
                if props.use_opacity:
                    props.opacity_texture = image
            elif any(key in file_elem.name.lower() for key in ["_bump", "bump_", "bump ", " bump"]):
                if props.use_bump:
                    props.bump_texture = image
            elif any(key in file_elem.name.lower() for key in ["_disp", "disp_", " disp", "disp ", "_displacement", "displacement_", "displacement ", " displacement","_h", "h_", " h", "h ", "_height", "height_", "height ", " height"]):
                if props.use_displacement_height:
                    props.displacement_height_texture = image
            elif any(key in file_elem.name.lower() for key in ["emis","emis_","Emiss","_emissive","emissive_"]):
                if props.use_emission:
                    props.emissions_texture = image

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}



# 操作器，用于清空所有插槽的纹理
class QUICK_SWORD_TEXTURE_OT_clear_images(Operator):
    bl_idname = "quickswordtexture.clear_images"
    bl_label = "Clear Images"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.custom_material_props
        material = context.object.active_material

        if not material or not material.use_nodes:
            return {'FINISHED'}

        nodes = material.node_tree.nodes

        slot_names = [
            "normal_texture", "basecolor_texture", "metallic_texture",
            "roughness_texture","ao_texture", "sss_texture", "specular_texture", "emission_texture", "opacity_texture",
            "bump_texture", "displacement_height_texture"
        ]

        for slot_name in slot_names:
            setattr(props, slot_name, None)
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.name == slot_name:
                    node.image = None
                    break

        return {'FINISHED'}

# 操作器，用于移除插槽中的纹理
class QUICK_SWORD_TEXTURE_OT_remove_images(Operator):
    bl_idname = "quickswordtexture.remove_images"
    bl_label = "Remove Images"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.custom_material_props
        if props.normal_texture:
            bpy.data.images.remove(props.normal_texture, do_unlink=True)
            props.normal_texture = None
        if props.basecolor_texture:
            bpy.data.images.remove(props.basecolor_texture, do_unlink=True)
            props.basecolor_texture = None
        if props.ao_texture:
            bpy.data.images.remove(props.ao_texture, do_unlink=True)
            props.ao_texture = None
        if props.metallic_texture:
            bpy.data.images.remove(props.metallic_texture, do_unlink=True)
            props.metallic_texture = None
        if props.roughness_texture:
            bpy.data.images.remove(props.roughness_texture, do_unlink=True)
            props.roughness_texture = None
        if props.specular_texture:
            bpy.data.images.remove(props.specular_texture, do_unlink=True)
            props.specular_texture = None
        if props.sss_texture:
            bpy.data.images.remove(props.sss_texture, do_unlink=True)
            props.sss_texture = None
        if props.emission_texture:
            bpy.data.images.remove(props.emission_texture, do_unlink=True)
            props.emission_texture = None
        if props.opacity_texture:
            bpy.data.images.remove(props.opacity_texture, do_unlink=True)
            props.opacity_texture = None
        if props.bump_texture:
            bpy.data.images.remove(props.bump_texture, do_unlink=True)
            props.bump_texture = None
        if props.displacement_height_texture:
            bpy.data.images.remove(props.displacement_height_texture, do_unlink=True)
            props.displacement_height_texture = None
        
        
        return {'FINISHED'}

# 操作器，用于移除插槽以外的所有纹理
class QUICK_SWORD_TEXTURE_OT_remove_all_images_except_slots(Operator):
    bl_idname = "quickswordtexture.remove_all_images_except_slots"
    bl_label = "Remove All Images Except Slots"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.custom_material_props
        images_to_keep = [
            props.normal_texture,
            props.basecolor_texture,
            props.ao_texture,
            props.metallic_texture,
            props.roughness_texture,
            props.sss_texture,
            props.specular_texture,
            props.emission_texture,
            props.opacity_texture,
            props.bump_texture,
            props.displacement_height_texture
        ]
        
        # Collect all images that are not in the slots
        images_to_remove = [img for img in bpy.data.images if img not in images_to_keep]
        
        # Remove them from the blend file
        for img in images_to_remove:
            bpy.data.images.remove(img, do_unlink=True)
        
        return {'FINISHED'}

# 定义一个面板以在 UI 中显示纹理插槽
class QUICK_SWORD_TEXTURE_PT_panel(Panel):
    bl_idname = "QUICK_SWORD_TEXTURE_PT_panel"
    bl_label = "Quick Sword Texture"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = context.scene.custom_material_props

        # 添加导入图片按钮及标签
        row = layout.row(align=True)
        row.operator("quickswordtexture.import_images", text="Import Images", icon='ADD')

        row = layout.row(align=True)
        row.operator("quickswordtexture.clear_images", text="", icon='X')
        row.label(text="清空插槽中纹理")
        row.operator("quickswordtexture.remove_images", text="", icon='REMOVE')
        row.label(text="移除插槽中包括文件")
        row.operator("quickswordtexture.remove_all_images_except_slots", text="", icon='REMOVE')
        row.label(text="移除插槽外包括文件")

        # 显示UDIM开关按钮
        row = layout.row(align=True)
        row.prop(props, "use_udim", text="更新UDIM", icon='FILE_REFRESH')
        
        # 颜色贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()
        col_left.label(text="BaseColor")  # 只显示文本
        col_right = split.column()
        col_right.prop(props, "basecolor_texture", text="")
        
        # 金属贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()
        col_left.label(text="Metallic")  # 只显示文本
        col_right = split.column()
        col_right.prop(props, "metallic_texture", text="")
        
        # 粗糙贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.label(text="Roughness")  # 只显示文本
        col_right = split.column()        # 右侧列
        col_right.prop(props, "roughness_texture", text="")
        
        # 法线贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()       # 左侧列
        split_left = col_left.split(factor=0.5)     # 左侧列再分割成多部分
        col_ll1 = split_left.column()    # 左侧第一部分
        col_ll1.label(text="Normal")  # 只显示文本
        col_ll2 = split_left.column()        # 左侧第二部分
        col_ll2.prop(props, "use_directx", text="DirectX")
        col_right = split.column()      # 右侧列
        col_right.prop(props, "normal_texture", text="")
        
        # AO贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_ao", text="Use AO")
        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_ao  # 根据 use_x启用或禁用
        col_right.prop(props, "ao_texture", text="")

        # 自发光贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_emission", text="Emission")
        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_emission  # 根据 use_x启用或禁用
        col_right.prop(props, "emission_texture", text="")

        # 高光贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_specular", text="Specular")
        col_right3 = split.column()        # 右侧列
        col_right3.enabled = props.use_specular  # 根据 use_x启用或禁用
        col_right3.prop(props, "specular_texture", text="")
        
        # 通透贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_sss", text="SSS")
        col_right4 = split.column()        # 右侧列
        col_right4.enabled = props.use_sss  # 根据 use_x启用或禁用
        col_right4.prop(props, "sss_texture", text="")

        # 透明贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        split_left = col_left.split(factor=0.45)
        col_ll1 = split_left.column()
        col_ll1.prop(props, "use_opacity", text="Opacity")

        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_opacity  # 根据 use_x启用或禁用
        col_right.prop(props, "opacity_texture", text="")

        # 置换高度贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_displacement_height", text="Disp&Height")
        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_displacement_height  # 根据 use_x启用或禁用
        col_right.prop(props, "displacement_height_texture", text="")
        
        # 凹凸贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        split_left = col_left.split(factor=0.45)
        col_ll1 = split_left.column()
        col_ll1.prop(props, "use_bump", text="Bump")
        col_ll2 = split_left.column()
        col_ll2.enabled = props.use_bump and props.use_displacement_height  # 根据 use_x启用或禁用
        col_ll2.prop(props, "use_bump_disp", text="置换凹凸混合")
        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_bump  # 根据 use_x启用或禁用
        col_right.prop(props, "bump_texture", text="")

# 定义一个面板以在 UI 中显示纹理插槽
class QUICK_SWORD_TEXTURE_Tool_PT_panel(Panel):
    bl_idname = "QUICK_SWORD_TEXTURE_Tool_PT_panel"
    bl_label = "Quick Sword Texture Mat"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "materialtool"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = context.scene.custom_material_props

        # 添加导入图片按钮及标签
        row = layout.row(align=True)
        row.operator("quickswordtexture.import_images", text="Import Images", icon='ADD')
        

        row = layout.row(align=True)
        row.operator("quickswordtexture.clear_images", text="", icon='X')
        row.label(text="清空插槽中纹理")
        row.operator("quickswordtexture.remove_images", text="", icon='REMOVE')
        row.label(text="移除插槽中包括文件")
        row.operator("quickswordtexture.remove_all_images_except_slots", text="", icon='REMOVE')
        row.label(text="移除插槽外包括文件")

        # 显示UDIM开关按钮
        row = layout.row(align=True)
        row.prop(props, "use_udim", text="更新UDIM", icon='FILE_REFRESH')
        
        # 颜色贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()
        col_left.label(text="BaseColor")  # 只显示文本
        col_right = split.column()
        col_right.prop(props, "basecolor_texture", text="")
        
        # 金属贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()
        col_left.label(text="Metallic")  # 只显示文本
        col_right = split.column()
        col_right.prop(props, "metallic_texture", text="")
        
        # 粗糙贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.label(text="Roughness")  # 只显示文本
        col_right = split.column()        # 右侧列
        col_right.prop(props, "roughness_texture", text="")
        
        # 法线贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()       # 左侧列
        split_left = col_left.split(factor=0.5)     # 左侧列再分割成多部分
        col_ll1 = split_left.column()    # 左侧第一部分
        col_ll1.label(text="Normal")  # 只显示文本
        col_ll2 = split_left.column()        # 左侧第二部分
        col_ll2.prop(props, "use_directx", text="DirectX")
        col_right = split.column()      # 右侧列
        col_right.prop(props, "normal_texture", text="")
        
        # AO贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_ao", text="Use AO")
        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_ao  # 根据 use_x启用或禁用
        col_right.prop(props, "ao_texture", text="")

        # 自发光贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_emission", text="Emission")
        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_emission  # 根据 use_x启用或禁用
        col_right.prop(props, "emission_texture", text="")

        # 高光贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_specular", text="Specular")
        col_right3 = split.column()        # 右侧列
        col_right3.enabled = props.use_specular  # 根据 use_x启用或禁用
        col_right3.prop(props, "specular_texture", text="")
        
        # 通透贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_sss", text="SSS")
        col_right4 = split.column()        # 右侧列
        col_right4.enabled = props.use_sss  # 根据 use_x启用或禁用
        col_right4.prop(props, "sss_texture", text="")

        # 透明贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        split_left = col_left.split(factor=0.45)
        col_ll1 = split_left.column()
        col_ll1.prop(props, "use_opacity", text="Opacity")
        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_opacity  # 根据 use_x启用或禁用
        col_right.prop(props, "opacity_texture", text="")

        # 置换高度贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        col_left.prop(props, "use_displacement_height", text="Disp&Height")
        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_displacement_height  # 根据 use_x启用或禁用
        col_right.prop(props, "displacement_height_texture", text="")
        
        # 凹凸贴图一行 整行分为左右两部分，右侧占一半
        split = layout.split(factor=0.5)
        col_left = split.column()     # 左侧列
        split_left = col_left.split(factor=0.45)
        col_ll1 = split_left.column()
        col_ll1.prop(props, "use_bump", text="Bump")
        col_ll2 = split_left.column()
        col_ll2.enabled = props.use_bump and props.use_displacement_height  # 根据 use_x启用或禁用
        col_ll2.prop(props, "use_bump_disp", text="置换凹凸混合")
        col_right = split.column()        # 右侧列
        col_right.enabled = props.use_bump  # 根据 use_x启用或禁用
        col_right.prop(props, "bump_texture", text="")

# 注册类和属性
classes = [
    TextureSlotPropertyGroup,

    QUICK_SWORD_TEXTURE_OT_import_images,
    QUICK_SWORD_TEXTURE_OT_clear_images,
    QUICK_SWORD_TEXTURE_OT_remove_images,
    QUICK_SWORD_TEXTURE_OT_remove_all_images_except_slots,
    QUICK_SWORD_TEXTURE_PT_panel,
    QUICK_SWORD_TEXTURE_Tool_PT_panel
]



def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    if bpy.app.version < (4, 0, 0):
        bpy.utils.register_class(QUICK_SWORD_TEXTURE_OT_update_texture_file)
    else:
        bpy.utils.register_class(QUICK_SWORD_TEXTURE_OT_update_texture_file4)
    bpy.types.Scene.custom_material_props = PointerProperty(type=TextureSlotPropertyGroup)

def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)

    if bpy.app.version < (4, 0, 0):
        bpy.utils.unregister_class(QUICK_SWORD_TEXTURE_OT_update_texture_file)
    else:
        bpy.utils.unregister_class(QUICK_SWORD_TEXTURE_OT_update_texture_file4)
    del bpy.types.Scene.custom_material_props

if __name__ == "__main__":
    register()


