import bpy

class OtherOperatorsPanel(bpy.types.Panel):
    """Subpanel of the main MAD Shading tool, with additional operators"""
    bl_label = "Other Tools"
    bl_idname = "OBJECT_PT_otheroperators"
    bl_space_type = 'NODE_EDITOR'
    bl_category = "MAD Shading Tools"
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_noderig"
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("object.refresh_drivers")
        row = layout.row()
        row.operator("object.remobe_broken_drivers")

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
