from . import(
    maya_soft_select,
    maya_vert_face,
    maya_from_object,
    maya_piemenu,
    camera,
    material_panel,
    keycore
    )

bl_info = {
    "name": "Maya Tool",
    "description": "An interactive tool for merging vertices.",
    "author": "VeengLoong/騳虤",
    "version": (1, 6, 9),
    "blender": (3, 6, 5),
    "location": "View3D > TOOLS > Merge Tool",
    "warning": "",
    "wiki_url": "https://github.com/Stromberg90/Scripts/tree/master/Blender",
    "tracker_url": "https://github.com/Stromberg90/Scripts/issues",
    "category": "Tool"
}

def register():
    maya_soft_select.register()

    maya_vert_face.register()
    
    maya_from_object.register()
    maya_piemenu.register()
    
    camera.register()
    material_panel.register()
    
    keycore.disable_default_keymaps()
    keycore.register_keymaps()



def unregister():
    keycore.unregister_keymaps()
    keycore.enable_default_keymaps()
    
    material_panel.unregister()
    camera.unregister()
    maya_piemenu.unregister()
    maya_from_object.unregister()
    maya_vert_face.unregister()
    maya_soft_select.unregister()




if __name__ == "__main__":
    register()
