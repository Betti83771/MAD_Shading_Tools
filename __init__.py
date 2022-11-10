# ====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ======================= END GPL LICENSE BLOCK ========================


bl_info = {
    "name": "production_name_here",
    "author": "Betti",
    "version": (0, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > production_name_here",
    "description": """Addons for the production_name_here production""",
    "warning": "",
    "doc_url": "",
    "category": "production-specific",
}


import bpy
import os
import importlib 
from sys import modules


def import_and_reload_all_modules(modules_names:list):
    """Detects the modules with a .py extension and without a special name thaa are part of the addon;
    imports and reloads them, so when adding a new module I don't have to remember to add it to __init__.py
    to be imported and reloaded, in order to be updated correctly by Blender upon making changes to it."""
    
    addon_path = os.path.split(__file__)[0]
    for root, dirs, files in os.walk(addon_path, topdown=False):
        if ".git" in root: continue
        if ".vscode" in root: continue
        if "__" in root: continue
        root2 = root.replace(addon_path, ".").replace(os.sep, ".")
        for file in files:
            if file.startswith("."): continue
            if not file.endswith(".py"): continue
            if "__" in file: continue
            file2 = file.replace(".py", "")
            modules_names.append((root2 + "." + file2)[1:])

    for module_name in modules_names:
        importlib.import_module(__name__ + module_name)
        actual_module = modules[__name__ + module_name]
        importlib.reload(actual_module)



from .addon_updater_ops import *
from .ui import *
from .preferences_ui import Prefs




def register():
    import_and_reload_all_modules([])
    addon_update_register(bl_info)
    bpy.utils.register_class(Prefs)
    ui_register()
    
    


def unregister():
    ui_unregister()
    bpy.utils.unregister_class(Prefs)
    addon_update_unregister()
