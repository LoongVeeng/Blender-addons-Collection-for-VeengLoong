bl_info = {
    "name": "VeengLoongTools2e",
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

def register():
    material_panel.register()
    camera.register()

def unregister():
    material_panel.unregister()
    camera.unregister()

if __name__ == "__main__":
    register()
