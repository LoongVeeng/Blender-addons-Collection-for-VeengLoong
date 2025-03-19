bl_info = {
    "name": "MaYaTools",
    "blender": (2, 80, 0),
    "category": "Material",
    "location": "View3D > Sidebar > Edit Tab / Edit Mode Context Menu",
    "warning": "",
    "description": "小工具",
    "doc_url": "https://github.com/LoongVeeng/Blender-addons-Collection-for-VeengLoong/tree/main/Conter",
    "category": "Mesh",
}

import bpy
from . import material_panel
from . import camera
from . import maya_soft_select,maya_vert_face


def register():
    material_panel.register()
    camera.register()
    maya_soft_select.register()
    maya_vert_face.register()

def unregister():
    material_panel.unregister()
    camera.unregister()
    maya_vert_face.unregister()
    maya_soft_select.unregister()
if __name__ == "__main__":
    register()
