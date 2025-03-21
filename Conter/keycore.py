import bpy

disabled_kmis = []

# 禁用和启用自带的键位映射
def get_active_kmi(space: str, **kwargs) -> bpy.types.KeyMapItem:
    kc = bpy.context.window_manager.keyconfigs.active
    km = kc.keymaps.get(space)
    if km:
        for kmi in km.keymap_items:
            for key, val in kwargs.items():
                if getattr(kmi, key) != val and val is not None:
                    break
            else:
                return kmi

def disable_keymap_item(space, idname, type, shift=False, ctrl=False, alt=False, properties=None):
    traits = {
        "idname": idname,
        "type": type,
        "shift": shift,
        "ctrl": ctrl,
        "alt": alt,
    }
    if properties:
        traits["properties"] = properties

    kmi = get_active_kmi(space, **traits)
    if kmi is not None:
        kmi.active = False
        disabled_kmis.append(kmi)

to_disable = {

    "Mesh": [
        {"idname": "wm.call_menu", "type": 'RIGHTMOUSE'},
        {"idname": "wm.context_toggle", "type": 'B'},
            
    ],

    "Object Mode": [
        {"idname": "wm.call_menu", "type": 'RIGHTMOUSE'},
    ],

    "Armature": [
        {"idname": "wm.call_menu", "type": 'RIGHTMOUSE'},
    ],
}

def disable_default_keymaps():
    keymaps = bpy.context.window_manager.keyconfigs.active.keymaps
    if not all(km in keymaps and get_active_kmi(km, **traits)
               for (km, traits_list) in to_disable.items()
               for traits in traits_list):

        disable_default_keymaps.retries = getattr(disable_default_keymaps, "retries", 0) + 1
        if disable_default_keymaps.retries < 20:
            return bpy.app.timers.register(disable_default_keymaps, first_interval=0.1)

    for space, traits_list in to_disable.items():
        for traits in traits_list:
            disable_keymap_item(space, **traits)

def enable_default_keymaps():
    for kmi in disabled_kmis:
        kmi.active = True

addon_keymaps = []

def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    #3D View
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    if kc:

        kmi = km.keymap_items.new('wm.modal_operator_pie_r', 'RIGHTMOUSE', 'PRESS')
        addon_keymaps.append((km, kmi))

    # Mesh
    km = kc.keymaps.new(name="Mesh", space_type="EMPTY")
    if kc:


        #软选择
        kmi = km.keymap_items.new('view3d.maya_soft_selection', 'B', 'CLICK')
        addon_keymaps.append((km, kmi))



def unregister_keymaps():
    for (km, kmi) in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    