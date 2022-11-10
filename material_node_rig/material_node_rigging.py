import bpy

def error(self, string):
    self.report({'WARNING'}, string)
    

def get_node_input(self, node):
    node_inputs_dict = {
        'VALUE': [],
        'RGBA': [],
        'VECTOR': []
    }
    if node.type.startswith('OUTPUT'):
        error(self, "The active node is a output node.")
        return None
    i = 0
    for input in node.inputs:
        if bpy.context.window_manager.use_ignore_linked_input:
            if  input.is_linked:
                continue
        if '--' in input.name:
                i += 1
        node_inputs_dict[input.type].append((input, i))
   # print(node_inputs_dict)
    return node_inputs_dict


def rig_node(node_inputs_dict, obj, bone=None, use_index_prefix=False):
    """inputs: node RNA (object), target object (bpy.types.Object), bone name (string) if armature"""
    if not node_inputs_dict:
        return

    remove_target_properties(obj, bone=bone)

    if bone:
        pose_bones = obj.pose.bones

    def driver_prop(default, tuple_inpu):
        i = tuple_inpu[1]
        inpu = tuple_inpu[0]
        prop_name = inpu.name
        prop_name_unspaced = prop_name.replace(' ', '_')
        if use_index_prefix == True:
            prop_name = str(i).zfill(2) + ' - ' + prop_name
        

        if bone:
            pose_bones[bone][prop_name] = default
            id_props = pose_bones[bone].id_properties_ui(prop_name)
        
        else:
            obj[prop_name] = default
            id_props = obj.id_properties_ui(prop_name)

        id_props.update(subtype= inpu.bl_rna.properties["default_value"].subtype,
                        min=inpu.bl_rna.properties["default_value"].hard_min,
                        max=inpu.bl_rna.properties["default_value"].hard_max,
                        soft_min=inpu.bl_rna.properties["default_value"].soft_min,
                        soft_max=inpu.bl_rna.properties["default_value"].soft_max,
                        default= default,
                        description=prop_name
                        )
        if bpy.context.window_manager.use_lib_overridable_props:
            if bone:
                pose_bones[bone].property_overridable_library_set('["{0}"]'.format(prop_name), True)
            else:
                obj.property_overridable_library_set('["{0}"]'.format(prop_name), True)
        raw_drv = inpu.driver_add('default_value')
        drv_list = []
        if isinstance(raw_drv, list):
            drv_list = [driv.driver for driv in raw_drv]
        else:
            drv_list = [raw_drv.driver]
        for drv in drv_list:
           #print("driv_list", drv)
            drv.type = 'SUM'
            
            #delete all variables if already exist
            for variable in drv.variables:
                drv.variables.remove(variable)
            var = drv.variables.new()
            var.name = prop_name_unspaced
            var.type = "SINGLE_PROP"
            var.targets[0].id = obj
            if bone:
                path_start = pose_bones[bone].path_from_id()
            else:
                path_start = ''
            if isinstance(raw_drv, list):
                data_path = path_start + '[' + '"' + prop_name + '"' + ']' + '['  + str(drv_list.index(drv))  + ']'
            else:
                data_path = path_start + '[' + '"' + prop_name + '"' + ']'
            var.targets[0].data_path = data_path
        
           
           

    for inpu in node_inputs_dict['VALUE']:
        value = inpu[0].default_value
        #print(value, "value")

        driver_prop(value, inpu)

    for inpu in node_inputs_dict['VECTOR']:
        vector_tuple = tuple(value for value in inpu[0].default_value)
        #print(color_tuple, "value")

        driver_prop(vector_tuple, inpu)
        
        
    for inpu in node_inputs_dict['RGBA']:
        color_tuple = tuple(value for value in inpu[0].default_value)
        #print(color_tuple, "value")

        driver_prop(color_tuple, inpu)
        
        #driver_prop((0.0, 0.0, 0.0, 0.0), inpu)
    
    #REFRESH
    if bone:
        curr_act = bpy.context.view_layer.objects.active
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='POSE')
        obj.data.bones.active = obj.data.bones[bone]
        bpy.ops.object.refresh_drivers(selected_only=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = curr_act
        
    else:
        obj.update_tag()
    
def remove_node_drivers(self, active_node:bpy.types.Node):

  
    for i, input in enumerate(active_node.inputs):
        input.driver_remove('default_value')
        if hasattr(active_node, "node_tree"):
            input.default_value = active_node.node_tree.inputs[i].default_value


   
    return

def remove_target_properties(target, bone=None):
    # wipe existing properties 
    if bone:
            pose_bones = target.pose.bones
            for prop in pose_bones[bone].keys():
                del pose_bones[bone][prop]
    else:
        for prop in target.keys():
            #print("removing", prop)
            del target[prop]
    return

if __name__ == "__main__":
    node_tree = bpy.context.object.active_material.node_tree
    for node in node_tree.nodes:
        node_inputs_dict = get_node_input('ff', node)
        if node_inputs_dict:
            rig_node(node_inputs_dict, 'eye.L', bpy.data.objects[bpy.data.armatures[1].name])
            print(node.name, "done!")
            #update the drivers
           # if node_tree.animation_data:
             #   node_tree.animation_data.drivers[0].driver.variables[0].targets[0].data_path += ' '
              #  node_tree.animation_data.drivers[0].driver.variables[0].targets[0].data_path = node_tree.animation_data.drivers[0].driver.variables[0].targets[0].data_path[:-1]
            
             #   print("drivers updated")