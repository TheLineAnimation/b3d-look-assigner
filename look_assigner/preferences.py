import bpy
from bpy.types import Operator, AddonPreferences, PropertyGroup
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty

import os
import json
import logging

from .utils import LoggerFactory
logger = LoggerFactory.get_logger()

class BlendFilePathItem(PropertyGroup):
    name: StringProperty(
        name="Name",  
        description="If this has been loaded from an external file, it will have a Python logo instead of a folder."
        )
    file_path: StringProperty(
        name="File Path", 
        subtype='DIR_PATH', 
        default=""
        )
    from_json: BoolProperty(
        name="From JSON", 
        default=False
        )

class LookAssignerPreferences(AddonPreferences):
    bl_idname = "look_assigner"

    material_filter: StringProperty(name="Material Filter", default="")
    task_filter: StringProperty(name="Task Filter", default="3d_look")
    ignore_filter: StringProperty(
        name="Ignore Specific Names", 
        default="Dots Stroke", 
        description="Enter the names of specific shaders you might want to omit from the search",)
    # pipeline_attribute_name is kind of a read only property
    pipeline_attribute_name: StringProperty(
        name="Pipeline Attribute Name", 
        default="LOOK_ASSIGNER_NODE_LIST"
    )
    paths: CollectionProperty(type=BlendFilePathItem)
    path_index: IntProperty(name="Path Index", default=0)
    debug_mode: BoolProperty(
        name="Debugging Mode",
        default=False,
        update=lambda self, context: self.update_logging_level()
    )

    def update_logging_level(self):
        if self.debug_mode:
            LoggerFactory.set_level(logging.DEBUG)
            logger.debug("Debug Logger Enabled")
        else:
            LoggerFactory.set_level(logging.INFO)

    def path_items(self, context):
        items = [(str(index), item.name, "") for index, item in enumerate(self.paths)]
        return items

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Published Shader File Search Paths:" , icon="MATERIAL")
        row = layout.row()
        row.template_list("UI_UL_CustomPath_List", "", self, "paths", self, "path_index")  
        col = row.column(align=True)
        col.operator("wm.add_path_operator", icon='ADD', text="")
        col.operator("wm.remove_path_operator", icon='REMOVE', text="")

        row = layout.row()
        row.label(text="Search Filter Preferences:" , icon="QUESTION")

        layout.prop(self, "material_filter", text="Material Filter")
        layout.prop(self, "task_filter", text="Task Filter")
        layout.prop(self, "ignore_filter", text="Ignore specific materials")

        layout.prop(self, "debug_mode", text="Enable Debugging Mode (Check system console for extra messages)")

def get(context: bpy.types.Context) -> LookAssignerPreferences:
    """Return the add-on preferences."""
    prefs = context.preferences.addons["look_assigner"].preferences
    assert isinstance(
        prefs, LookAssignerPreferences
    ), "Expected LookAssignerPreferences, got %s instead" % (type(prefs))
    return prefs

def get_ayon_project_path():
    return "./"

def load_paths_from_json(prefs):
    """

    """

    json_path = os.path.join(get_ayon_project_path(), "look_assigner_paths.json")
    
    if not os.path.exists(json_path):
        return

    with open(json_path, 'r') as file:
        data = json.load(file)

    existing_paths = {item.file_path for item in prefs.paths}
    existing_names = {item.name for item in prefs.paths}

    for key, value in data.items():
        if value not in existing_paths:
            name = key
            if name in existing_names:
                base_name = name
                count = 1
                while name in existing_names:
                    name = f"{base_name}_{count:02}"
                    count += 1

            new_item = prefs.paths.add()
            new_item.name = name
            new_item.file_path = value
            new_item.from_json = True
            logger.debug (f'Added path from JSON template {json_path} {name} {value}')

class AddPathOperator(Operator):
    bl_idname = "wm.add_path_operator"
    bl_label = "Add Path"
    bl_description="Click to add a path entry."
    def execute(self, context):
        # prefs = context.preferences.addons["look_assigner"].preferences
        prefs = get(context)
        new_item = prefs.paths.add()
        new_item.name = "Folder Name"
        new_item.file_path = ""
        prefs.path_index = len(prefs.paths) - 1
        return {'FINISHED'}

class RemovePathOperator(Operator):
    bl_idname = "wm.remove_path_operator"
    bl_label = "Remove Path"
    bl_description="Click to remove a path entry."
    def execute(self, context):
        # prefs = context.preferences.addons["look_assigner"].preferences
        prefs = get(context)
        if prefs.path_index >= 0 and prefs.path_index < len(prefs.paths):
            prefs.paths.remove(prefs.path_index)
            prefs.path_index = min(max(0, prefs.path_index - 1), len(prefs.paths) - 1)
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(BlendFilePathItem)
    bpy.utils.register_class(LookAssignerPreferences)
    bpy.utils.register_class(AddPathOperator)
    bpy.utils.register_class(RemovePathOperator)

    # Load paths from JSON on add-on registration
    prefs = bpy.context.preferences.addons["look_assigner"].preferences
    load_paths_from_json(prefs)

def unregister():
    bpy.utils.unregister_class(LookAssignerPreferences)
    bpy.utils.unregister_class(BlendFilePathItem)
    bpy.utils.unregister_class(AddPathOperator)
    bpy.utils.unregister_class(RemovePathOperator)

# if __name__ == "__main__":
#     register()