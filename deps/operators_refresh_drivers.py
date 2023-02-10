import bpy
from bpy.props import BoolProperty

PREF_TEXT = 'Refresh Drivers'
PREF_DESCRIPTION = "Activate feature: 'Refresh Drivers'"

def refresh_drivers(datablock):
	if not datablock: return
	if not hasattr(datablock, "animation_data"): return
	if not datablock.animation_data: return
	datablock.update_tag()
	for d in datablock.animation_data.drivers:
		d.driver.type = d.driver.type
	bpy.context.view_layer.update()

def remove_broken_drivers(datablock):
	if not datablock: return
	if not hasattr(datablock, "animation_data"): return
	if not datablock.animation_data: return
	datablock.update_tag()
	removed_count = 0
	for d in datablock.animation_data.drivers:
		broken = False
		try:
			eval("datablock." + d.data_path)
			if d.driver.type != 'SCRIPTED':
				for v in d.driver.variables:
					for tar in v.targets:
						tar_id = tar.id
						eval(f"tar_id.{tar.data_path}")
			
		except (KeyError, AttributeError):
			broken = True
		if not len(d.driver.variables): broken = True
		if broken:
			datablock.animation_data.drivers.remove(d)
			print("Remove broken Drivers: removed", d)
			removed_count += 1
	return removed_count

class RefreshDrivers(bpy.types.Operator):
	"""Refresh drivers, ensuring no valid drivers are marked as invalid"""

	bl_idname = "object.refresh_drivers"
	bl_label = "Refresh Drivers"
	bl_options = {'REGISTER', 'UNDO'}

	other_buttons = True

	selected_only: BoolProperty(name="Only Selected Objects", default=False)

	def execute(self, context):
		objs = context.selected_objects if self.selected_only else bpy.data.objects

		for o in objs:
			
			refresh_drivers(o)
			if hasattr(o, "data") and o.data:
				refresh_drivers(o.data)
			if o.type=='MESH':
				refresh_drivers(o.data.shape_keys)
			
			for ms in o.material_slots:
				if ms.material:
					refresh_drivers(ms.material)
					refresh_drivers(ms.material.node_tree)

		return { 'FINISHED' }

class RemoveBrokenDrivers(bpy.types.Operator):
	"""Remove broven drivers drivers, ensuring no drivers are marked as invalid -- we can hope"""

	bl_idname = "object.remobe_broken_drivers"
	bl_label = "Remove broken Drivers"
	bl_options = {'REGISTER', 'UNDO'}

	other_buttons = True

	selected_only: BoolProperty(name="Only Selected Objects", default=False)

	def execute(self, context):
		objs = context.selected_objects if self.selected_only else bpy.data.objects

		for o in objs:
			
			rem_count = remove_broken_drivers(o)
			if rem_count: self.report({'INFO'}, f"Object {o.name}: removed {rem_count} drivers")
			if hasattr(o, "data") and o.data:
				rem_count = remove_broken_drivers(o.data)
				if rem_count: self.report({'INFO'}, f"Data {o.data.name}: removed {rem_count} drivers")
			if o.type=='MESH':
				rem_count = remove_broken_drivers(o.data.shape_keys)
				if rem_count: self.report({'INFO'}, f"Shape Keys {o.name}: removed {rem_count} drivers")
			
			for ms in o.material_slots:
				if ms.material:
					rem_count = remove_broken_drivers(ms.material)
					if rem_count: self.report({'INFO'},  f"Material {ms.material.name}: removed {rem_count} drivers")
					rem_count = remove_broken_drivers(ms.material.node_tree)
					if rem_count: self.report({'INFO'}, f"Material node tree {ms.material.name}: removed {rem_count} drivers")

		return { 'FINISHED' }

def driv_menu_func(self, context):
    self.layout.operator(RefreshDrivers.bl_idname, icon='DRIVER')
	


def refr_drvs_register():
	from bpy.utils import register_class
	bpy.types.WindowManager.rd_selected_only = bpy.props.BoolProperty(name="Only Selected Objects", default=True)
	bpy.types.VIEW3D_MT_object.append(driv_menu_func)
	register_class(RefreshDrivers)
	register_class(RemoveBrokenDrivers)

def refr_drvs_unregister():
	from bpy.utils import unregister_class
	bpy.types.VIEW3D_MT_object.remove(driv_menu_func)
	unregister_class(RemoveBrokenDrivers)
	unregister_class(RefreshDrivers)
	del bpy.types.WindowManager.rd_selected_only

if __name__ == '__main__':
	refr_drvs_register()