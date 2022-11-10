import bpy
from  . import material_node_rigging

from importlib import reload
reload(material_node_rigging)

from .material_node_rigging import *

PREF_TEXT = 'Material-Node Rigging'
PREF_DESCRIPTION = "Activate feature: 'Material-Node Rigging'"


class NodeRigOperator(bpy.types.Operator):
    """Create properties corresponding to deafult values of the active node inputs, 
    on the target. Attention: wipes previous custom properties from the target"""
    bl_idname = "node.rig_material_nodes"
    bl_label = "Rig Inputs"
    
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if isinstance(bpy.context.space_data, bpy.types.SpaceNodeEditor):
            node_editor = bpy.context.space_data 
            if node_editor.edit_tree:
                return node_editor.edit_tree.nodes.active != None and context.window_manager.main_target != None
            else:
                return False
        if context.object.active_material:
            return context.object.active_material.node_tree.nodes.active != None and context.window_manager.main_target != None
        else:
            return False

    def execute(self, context):
        rig_node(
            get_node_input(self, bpy.context.space_data.edit_tree.nodes.active),
            bpy.context.window_manager.main_target,
            bone=bpy.context.window_manager.subtarget, 
            use_index_prefix=bpy.context.window_manager.use_index_prefix
        )
        return {'FINISHED'}

class ClearDriversOperator(bpy.types.Operator):
    """Clear all drivers from the current node"""
    bl_idname = "node.noderig_cleardrivers"
    bl_label = "Clear drivers"

    @classmethod
    def poll(cls, context):
        if isinstance(bpy.context.space_data, bpy.types.SpaceNodeEditor):
            node_editor = bpy.context.space_data 
            if node_editor.edit_tree:
                return node_editor.edit_tree.nodes.active != None
            else:
                return False
        if context.object.active_material:
            return context.object.active_material.node_tree.nodes.active != None
        else:
            return False

    def execute(self, context):
        remove_node_drivers(self, context.space_data.edit_tree.nodes.active)
        return {'FINISHED'}

class ClearPropsOperator(bpy.types.Operator):
    """Clear all custom properties from the target"""
    bl_idname = "object.noderig_clearprops"
    bl_label = "Clear properties from target"

    @classmethod
    def poll(cls, context):
        return context.window_manager.main_target != None

    def execute(self, context):
        if context.window_manager.subtarget != "":
            remove_target_properties(context.window_manager.main_target, bone=context.window_manager.subtarget)
        else:
            remove_target_properties(context.window_manager.main_target)
        return {'FINISHED'}

class AddEmptyOperator(bpy.types.Operator):
    """Create an empty and use it as target for rigging nodes"""
    bl_idname = "object.noderig_empty"
    bl_label = "Create new"

    @classmethod
    def poll(cls, context):
        if context.object:
            return context.object.active_material != None
        else:
            return context.object != None

    def execute(self, context):
        current_active = context.view_layer.objects.active
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        context.active_object.name = 'ShaderEmpty'
        context.window_manager.main_target = context.active_object #Objects constructed with bpy.ops.mesh.primitive_* are automatically active.
        context.view_layer.objects.active = current_active
        return {'FINISHED'}

class NodeRigPanel(bpy.types.Panel):
    """Creates a Panel in the Shader Editor 'Item' section
    for the usage of the material node rigging to bone/object functions"""
    bl_label = "Node inputs to target"
    bl_idname = "OBJECT_PT_noderig"
    bl_space_type = 'NODE_EDITOR'
    bl_category = "Item"
    bl_region_type = 'UI'


    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("node.noderig_cleardrivers")
        row = layout.row()
        row.operator("object.noderig_clearprops")
        row = layout.row()
        row.separator()
        row = layout.row()
        row.separator()
        row = layout.row()
        row.prop(context.window_manager, 'main_target', text='')
        if bones("2 argomenti", "a caso"):
            row = layout.row()
            #row.prop(context.window_manager, 'subtarget', text='')#amma fa sta lista
            row.prop_search(context.window_manager, "subtarget", context.window_manager.main_target.data, "bones", text="")
        row = layout.row()
        row.operator("node.rig_material_nodes")
        row = layout.row()
        row.prop(context.window_manager, 'use_index_prefix')
        row = layout.row()
        row.prop(context.window_manager, 'use_ignore_linked_input')
        row = layout.row()
        row.prop(context.window_manager, 'use_lib_overridable_props')
        row = layout.row()
        row.operator("object.noderig_empty", icon='EMPTY_AXIS')
        
        

def bones(self, context):
    armature = bpy.context.window_manager.main_target
    if armature == None:
        return
    if armature.data in bpy.data.armatures.values():
        enum_list = []
        for bone in armature.data.bones.values():
            enum_list.append((bone.name, bone.name, "", armature.data.bones.values().index(bone)))
        return enum_list
    else:
        return 

def fw_register():
    bpy.utils.register_class(NodeRigPanel)
    bpy.utils.register_class(NodeRigOperator)
    bpy.utils.register_class(AddEmptyOperator)
    bpy.utils.register_class(ClearDriversOperator)
    bpy.utils.register_class(ClearPropsOperator)
    bpy.types.WindowManager.main_target = bpy.props.PointerProperty(type=bpy.types.Object,
                                                name='main target', 
                                                description="object on which create the custom properties")
    bpy.types.WindowManager.subtarget = bpy.props.StringProperty(default="",
                                                name='subtarget', 
                                                description="bone if armature")
    bpy.types.WindowManager.use_index_prefix = bpy.props.BoolProperty(default=True,
                                                name='Use index prefix on "--"', 
                                                description="""Check to order the properties with a number prefix using node sockets starting with "--" as separators""" )
    bpy.types.WindowManager.use_ignore_linked_input = bpy.props.BoolProperty(default=True,
                                                name='Ignore linked inputs', 
                                                description="""Check to ignore linked node inputs and not put any drivers on them or properies about them""" )
    bpy.types.WindowManager.use_lib_overridable_props = bpy.props.BoolProperty(default=True,
                                                name='Library overridable properties', 
                                                description="""Check to make the generated properties on target library overridable""" )
    bpy.types.WindowManager.intlist = bpy.props.IntProperty(default=0,
                                                name='intlist', 
                                                description="intprop for list")                                                           
                    

def fw_unregister():
    bpy.utils.unregister_class(ClearPropsOperator)
    bpy.utils.unregister_class(ClearDriversOperator)
    bpy.utils.unregister_class(AddEmptyOperator)
    bpy.utils.unregister_class(NodeRigOperator)
    bpy.utils.unregister_class(NodeRigPanel)
    del bpy.types.WindowManager.main_target
    del bpy.types.WindowManager.subtarget
    del bpy.types.WindowManager.use_index_prefix
    del bpy.types.WindowManager.use_ignore_linked_input
    del bpy.types.WindowManager.use_lib_overridable_props
    del bpy.types.WindowManager.intlist


if __name__ == '__main__':
    fw_register()