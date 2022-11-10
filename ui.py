import bpy

classes = [
    # operator classes here
]

def ui_register():
    # ui property definitions here (window_manager props)
    
    for cls in classes:
        bpy.utils.register_class(cls)

def ui_unregister():
    # ui property deletions here 
    
    for cls in reversed(classes):
        bpy.utils.register_class(cls)
