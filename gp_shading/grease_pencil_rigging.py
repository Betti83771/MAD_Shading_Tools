import bpy
from mathutils import Vector

#TODO: remove all unused stuff

"""
For usage in FWP module turn on/off:
NO_PREF = False
PREF_TEXT = 'Grease Pencil Autorig'
PREF_DESCRIPTION = "Activate feature: 'Grease Pencil Autorig'"""

class GPSettingsBonePropPropertyGroup(bpy.types.PropertyGroup):
    prop_name: bpy.props.StringProperty()
    prop_type: bpy.props.EnumProperty(items=[("float","Float",""), ("int", "Int", ""), ("color", "Color", "")],
                                        default="float")
    default_value_float: bpy.props.FloatProperty()
    default_value_int: bpy.props.IntProperty()
    default_value_color: bpy.props.FloatVectorProperty()
    prop_index: bpy.props.IntProperty()
   # modifier_name: bpy.props.StringProperty(description="The name of the modifier")
    modifier_type: bpy.props.StringProperty(description="The type blend id of the modifier")
    modifier_data_path: bpy.props.StringProperty(description="TThe data path after the modifier")

class GPSettingsBoneProp():
    def __init__(self, default,prop_name="", prop_index=0, subtype=None, modifier_type="", data_path=""):
        self.default = default
        self.prop_name = prop_name
        self.prop_index= prop_index
        self.subtype = subtype
        self.modifier_type = modifier_type
        self.data_path = data_path # The data path after the modifier, ExampleModifier.thisdatapath, ex: ColorModifier.hue

    def make_prop(self, rig_obj:bpy.types.Object, bone_name:str):
        pose_bones = rig_obj.pose.bones
        prop_name = str(self.prop_index).zfill(2) + '-' + self.prop_name
        if prop_name in pose_bones.keys():
            return
        pose_bones[bone_name][prop_name] = self.default
        id_props = pose_bones[bone_name].id_properties_ui(prop_name)
        id_props.update(default = self.default,
                        description = prop_name)
        if self.subtype:
            id_props.update(subtype=self.subtype)


def make_default_properties_table():
    hue = GPSettingsBoneProp(0.5, prop_name="Hue", prop_index=1, modifier_type='GP_COLOR',data_path="hue" )
    saturation = GPSettingsBoneProp(1.0, prop_name="Saturation", prop_index=2,modifier_type='GP_COLOR', data_path="saturation")
    value = GPSettingsBoneProp(1.0, prop_name="Value", prop_index=3, modifier_type='GP_COLOR',data_path= "value")
    strength = GPSettingsBoneProp(0.0, prop_name="Strength", prop_index=4, modifier_type='GP_TINT',data_path= "factor")
    color = GPSettingsBoneProp(Vector((1.0,1.0,1.0)), prop_name="Color", prop_index=5, subtype="COLOR", modifier_type='GP_TINT',data_path="color")
    return (hue, saturation, value, strength, color)

def create_metarig_bone(context:bpy.types.Context, rig_obj:bpy.types.Object, bone_name="GP-settings", use_default_properties=True):
    """Add a bone in edit mode, to be included in a rigify metarig that would later generate a rig"""
    if context.mode != 'EDIT_ARMATURE': return
    assert rig_obj.type == 'ARMATURE'
    save_mat = None
    if bone_name in rig_obj.data.edit_bones.keys():
        save_mat = rig_obj.data.edit_bones[bone_name].matrix
        rig_obj.data.edit_bones.remove(rig_obj.data.edit_bones[bone_name])
    new_bone = rig_obj.data.edit_bones.new(bone_name)
    new_bone.tail = Vector((0.0, 0.0, 1.0))

    if save_mat:
        new_bone.matrix = save_mat
    context_copy = context.copy()
    with bpy.context.temp_override(**context_copy):
        bpy.ops.object.mode_set(mode='POSE')
    if use_default_properties:
        prop_table  = make_default_properties_table()
    else:
        pass #TODO
    for prop in prop_table:
        prop.make_prop(rig_obj, bone_name)
    new_bone_pose = rig_obj.pose.bones[bone_name]
    new_bone_pose.rigify_type = "basic.raw_copy"
    new_bone_pose.rigify_parameters.relink_constraints = True;
    new_bone_pose.rigify_parameters.parent_bone = "root"
    new_bone_pose.rigify_parameters.optional_widget_type = "gear"
    with bpy.context.temp_override(**context_copy):
        bpy.ops.object.mode_set(mode='EDIT')

def make_prop(self, rig_obj:bpy.types.Object, bone_name:str, default, prop_name:str, prop_index:int):
    """DEprecated""" 
    pose_bones = rig_obj.pose.bones
    prop_name = str(prop_index).zfill(2) + '-' + prop_name
    if prop_name in pose_bones.keys():
        return
    pose_bones[bone_name][prop_name] = default
   # prop = rna_idprop_ui_prop_get(pose_bones[bone_name], prop_name)
   #prop["default"] = default
   # prop["description"] = prop_name

def mst_importbones_exec(context):
    file_path = "//" + "vfx_GP_rig_ast_prp.blend"
    # importing gradient empty and metarig extra bones
    try:
        with bpy.data.libraries.load(file_path) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name.startswith("metarig")]
    except OSError:
        return "not_found"
    report = ""
    # linking to scene collection
    for obj in data_to.objects:
            if obj is not None:
                context.scene.collection.objects.link(obj)
                report = report + obj.name + " "
    return report     

def make_driver(data, data_target:str, var_target_data:bpy.types.Object, var_target_prop:str, expr='var', drv_index=-1):
    print(data_target)
    drv = data.driver_add(data_target, drv_index).driver
    drv.type = 'SCRIPTED'
    drv.expression = expr
    
    for variable in drv.variables:
        drv.variables.remove(variable)
    var = drv.variables.new()
    var.name = 'var'
    var.type = "SINGLE_PROP"
    var.targets[0].id = var_target_data
    var.targets[0].data_path = var_target_prop
    return drv

def rig_gp_func(gp:bpy.types.Object, rig_obj:bpy.types.Object, bone_name:str, use_default_table=True):
    if use_default_table:
        prop_table = make_default_properties_table()
    else:
        pass #TODO
    for prop in prop_table:
        mod_name = "mst_gprig_" + prop.modifier_type
        full_prop_name = str(prop.prop_index).zfill(2) + '-' + prop.prop_name
        if mod_name in gp.grease_pencil_modifiers.keys():
            mod = gp.grease_pencil_modifiers[mod_name]
        else:
            mod = gp.grease_pencil_modifiers.new(name=mod_name, type=prop.modifier_type)
        if prop.subtype:
            
            for i in range(len(prop.default)):
                
                var_target_prop = f'pose.bones["{bone_name}"]["{full_prop_name}"][{i}]'
                
                print(prop.subtype, prop.default, var_target_prop)
                make_driver(mod, prop.data_path, rig_obj, var_target_prop, drv_index=i)
        else:
            var_target_prop = f'pose.bones["{bone_name}"]["{full_prop_name}"]'
            make_driver(mod, prop.data_path, rig_obj, var_target_prop)
    
    if False: #Opacity stuff, might be useful
        gp_layers = gp.data.layers
        if "gprig_master" in gp_layers.keys():
            gp_layers.remove(gp_layers["gprig_master"])
        master_layer = gp_layers.new(name="gprig_master")
        for j in range(len(gp_layers)): 
            gp_layers.move(master_layer, 'UP')
        frame_strokes_dict = {}
        """{ frame:
                { "stroke_000":
                    { "points": {"vector": "", "pressure": 1.0, "strength": 1.0},
                      "line_width": int
                    },
                    ...
                },
                ...
            }
                      """
        n = 0
        m = 0
        for layer in gp_layers:
       #     print(layer.info)
            if layer == master_layer: continue
            #gp_layers.active = layer
            #bpy.ops.gpencil.layer_duplicate()
            #new_layer = gp_layers.active
            #for j in range(i):
            #    gp_layers.move(new_layer, 'UP')
            #layer.hide = True
            #gp_layers.active = master_layer 
            #bpy.ops.gpencil.layer_merge()
            #gp_layers.active.info = "gprig_master"
            #master_layer = gp_layers.active
            for frame in layer.frames:
                frame_strokes_dict[frame.frame_number] = {}
                for stroke in frame.strokes:
                    stroke_dict = frame_strokes_dict[frame.frame_number].setdefault(f"stroke{f'{n}'.zfill(2)}", {})
                    n += 1
                    stroke_dict["points"] = {}
                    for point in stroke.points:
                        point_name = f"point{f'{m}'.zfill(2)}"
                        stroke_dict["points"][point_name] = {"vector": "", "pressure": 1.0, "strength": 1.0}
                        stroke_dict["points"][point_name]["vector"] = point.co
                        stroke_dict["points"][point_name]["pressure"] = point.pressure
                        stroke_dict["points"][point_name]["strength"] = point.strength
                        m +=1
                    stroke_dict["line_width"] = stroke.line_width
            layer.hide = True
        for frame_n, frame_dict in frame_strokes_dict.items():
            frame = next((frame for frame in master_layer.frames if frame.frame_number == frame_n), master_layer.frames.new(frame_n))
            for stroke_dict in frame_dict.values():
                new_stroke = frame.strokes.new()
                print(stroke_dict["points"])
                new_stroke.points.add(len(stroke_dict["points"].keys()))
                for point_from, point_to in zip(stroke_dict["points"], new_stroke.points):
                    point_to.co = stroke_dict["points"][point_from]["vector"]
                    point_to.pressure = stroke_dict["points"][point_from]["pressure"]
                    point_to.strength = stroke_dict["points"][point_from]["strength"]
                new_stroke.line_width = stroke_dict["line_width"]
        make_prop(rig_obj, bone_name, 1.0, "Opacity", 7)   
        make_driver(master_layer, "opacity", rig_obj, f'pose.bones["{bone_name}"]["07-Opacity"]')
    return


class CreateGPShadingMetarigBone(bpy.types.Operator):
    """Add a settings bone with the specified properties"""
    bl_idname = "mst.gprig_make_rig"
    bl_label = "Add GP shading settings bone"

    
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        if context.window_manager.mst_gprig_rigtarget:
            
            case_obj_but_picked = context.window_manager.mst_gprig_rigtarget.type == 'ARMATURE' and context.mode == 'OBJECT'
            
        else: case_obj_but_picked = False
        return context.mode == 'EDIT_ARMATURE' or case_obj_but_picked

    def execute(self, context):
        if context.mode == 'EDIT_ARMATURE':
            create_metarig_bone(context, context.object, 
                                bone_name="GP-settings", 
                                use_default_properties=context.window_manager.mst_gpr_use_default_prop_table)
            context.window_manager.mst_gprig_subtarget = "GP-settings"
            context.window_manager.mst_gprig_rigtarget = context.object
        else:
            context.view_layer.objects.active = context.window_manager.mst_gprig_rigtarget
            if context.window_manager.mst_gprig_subtarget in context.window_manager.mst_gprig_rigtarget.data.bones.keys():
                bone_name = context.window_manager.mst_gprig_subtarget
            else:
                bone_name = "GP-settings"
                context.window_manager.mst_gprig_subtarget = "GP-settings"
            create_metarig_bone(context, context.object, 
                                bone_name=bone_name, 
                                use_default_properties=context.window_manager.mst_gpr_use_default_prop_table)

        return {'FINISHED'}

class WritePropTableOp(bpy.types.Operator): #TODO
    """Write the current custom prop table to the addon code. Please note that 
if you update the addon the changes may be lost, so be sure to keep a blend file with a backup or
contact the developer and ask for a permanet change."""
    bl_idname = "mst.write_prop_table"
    bl_label = "Set current table as default"
    
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
       
        return {'FINISHED'}


class RigGpOperator(bpy.types.Operator):
    """Rig the selected grease pencils on the chosen bone."""
    bl_idname = "mst.rig_gp"
    bl_label = "Generate modifiers on selected"
    
    bl_options = {'REGISTER', 'UNDO'} 


    @classmethod
    def poll(cls, context):
        if context.window_manager.mst_gprig_rigtarget:
            return context.window_manager.mst_gprig_rigtarget.data in bpy.data.armatures.values()
        return False

    def execute(self, context):
        for ob in context.selected_objects:
            if ob.type != 'GPENCIL': continue
            rig_gp_func(ob, 
            context.window_manager.mst_gprig_rigtarget,
            context.window_manager.mst_gprig_subtarget,
            use_default_table=context.window_manager.mst_gpr_use_default_prop_table)
        return {'FINISHED'}

class MST_UL_GPRigPropTableListUI((bpy.types.UIList)): #TODO
    bl_label = "Bibibib"
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        slot = item
        ma = slot.material
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # You should always start your row layout by a label (icon + text), or a non-embossed text field,
            # this will also make the row easily selectable in the list! The later also enables ctrl-click rename.
            # We use icon_value of label, as our given icon is an integer value, not an enum ID.
            # Note "data" names should never be translated!
            if ma:
                layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", translate=False, icon_value=icon)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class RigGpPanel(bpy.types.Panel):
    bl_label = "Grease Pencil autorig"
    bl_idname = "MST_PT_Gprig"
    bl_space_type = 'NODE_EDITOR'
    bl_category = "MAD Shading Tools"
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.window_manager, "mst_gprig_rigtarget")
        if context.window_manager.mst_gprig_rigtarget:
            if context.window_manager.mst_gprig_rigtarget.data in bpy.data.armatures.values():
                row = layout.row()
                row.prop_search(context.window_manager, "mst_gprig_subtarget", context.window_manager.mst_gprig_rigtarget.pose, "bones")
        row = layout.row()
        row.prop(context.window_manager, "mst_gpr_use_default_prop_table")
        row.enabled=False
        if not context.window_manager.mst_gpr_use_default_prop_table:
            row=layout.row()
            row.label(text="Customize custom properties to create:")
            row=layout.row()
            row.template_list("UI_UL_list", "MST_UL_GPRigPropTableListUI",
                            context.window_manager, "mst_gpr_property_table", 
                            context.window_manager, "mst_gpr_property_table_active_idx")
            pass #TODO
        
        row = layout.row()
        row.operator("mst.gprig_make_rig")
        row = layout.row()
        row.operator("mst.rig_gp")
        return

def use_default_prop_table_update(self, context):
    if not self.mst_gpr_use_default_prop_table:
        def_prop_tab = make_default_properties_table()
        for def_prop in def_prop_tab:
            prop_in_coll = context.window_manager.mst_gpr_property_table.add()
            prop_in_coll.name=def_prop.prop_name
            prop_in_coll.prop_name = def_prop.prop_name
            if isinstance(def_prop.default, float):
                prop_in_coll.default_value_float = def_prop.default
                prop_in_coll.prop_type = "float"
            if isinstance(def_prop.default, int):
                prop_in_coll.default_value_int = def_prop.default
                prop_in_coll.prop_type = "int"
            if isinstance(def_prop.default, Vector):
                prop_in_coll.default_value_color = def_prop.default
                prop_in_coll.prop_type = "color"
            prop_in_coll.prop_index = def_prop.prop_index
            prop_in_coll.modifier_type = def_prop.modifier_type
            prop_in_coll.modifier_data_path = def_prop.data_path

    else:
        context.window_manager.mst_gpr_property_table.clear()

gpr_classes =[
    GPSettingsBonePropPropertyGroup,
]


def gprig_register_properties():
    bpy.types.WindowManager.mst_gprig_rigtarget = bpy.props.PointerProperty(type=bpy.types.Object,
                                                                            name="Rig")
    bpy.types.WindowManager.mst_gprig_subtarget = bpy.props.StringProperty(name="Bone")
    bpy.types.WindowManager.mst_gprig_hue_saturation = bpy.props.BoolProperty(name="Hue / Saturation")
    bpy.types.WindowManager.mst_gprig_tint = bpy.props.BoolProperty(name="Tint")
    bpy.types.WindowManager.mst_gprig_time_offset = bpy.props.BoolProperty(name="Time offset")
    bpy.types.WindowManager.mst_gprig_opacity = bpy.props.BoolProperty(name="Opacity")
    bpy.types.WindowManager.mst_gprig_bone_name = bpy.props.StringProperty(name="New bone name:", default="GP-settings")
    bpy.types.WindowManager.mst_gpr_property_table_active_idx = bpy.props.IntProperty()
    bpy.types.WindowManager.mst_gpr_property_table = bpy.props.CollectionProperty(type=GPSettingsBonePropPropertyGroup)
    bpy.types.WindowManager.mst_gpr_use_default_prop_table = bpy.props.BoolProperty(
                            default=True,
                            update=use_default_prop_table_update,
                            name="Use default property table",
                            description="""The deafult property table is:
01-Hue
02-Saturation
03-Value
04-Strength
05-Color"""
                             )           

def gprig_unregister_properties():
    del bpy.types.WindowManager.mst_gpr_use_default_prop_table
    del bpy.types.WindowManager.mst_gpr_property_table
    del bpy.types.WindowManager.mst_gpr_property_table_active_idx 
    del bpy.types.WindowManager.mst_gprig_bone_name
    del bpy.types.WindowManager.mst_gprig_rigtarget 
    del bpy.types.WindowManager.mst_gprig_subtarget
    del bpy.types.WindowManager.mst_gprig_hue_saturation 
    del bpy.types.WindowManager.mst_gprig_tint
    del bpy.types.WindowManager.mst_gprig_time_offset 
    del bpy.types.WindowManager.mst_gprig_opacity 


def gpr_register():
    for cl in gpr_classes: 
        bpy.utils.register_class(cl)
    gprig_register_properties()
    bpy.utils.register_class(CreateGPShadingMetarigBone)
    bpy.utils.register_class(RigGpOperator)
    bpy.utils.register_class(RigGpPanel)
    
    
            
def gpr_unregister():
    bpy.utils.unregister_class(RigGpPanel)
    bpy.utils.unregister_class(CreateGPShadingMetarigBone)
    bpy.utils.unregister_class(RigGpOperator)
    gprig_unregister_properties()
    
    for cl in reversed(gpr_classes): 
        bpy.utils.unregister_class(cl)
            
if __name__ == "__main__":
    gpr_register()