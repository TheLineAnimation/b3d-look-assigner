
import bpy
import os
from bpy.types import PropertyGroup, Operator
from bpy.props import StringProperty, BoolProperty, CollectionProperty, IntProperty, EnumProperty, PointerProperty

from .utils import LoggerFactory
logger = LoggerFactory.get_logger()

class ScanForBlendFilesOperator(Operator):
    bl_idname = "object.scan_for_blend_files"
    bl_label = "Scan for Blend Files"
    
    def scan_for_blend_files(self, directory, context):

        lookProps = context.scene.LookAssigner_Properties    
        lookProps.blend_files.clear()

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".blend"):
                    logger.debug (f'ScanForBlendFilesOperator - File Found:{root} {file}')
                    item = lookProps.blend_files.add()
                    item.name = file
                    item.path = os.path.join(root, file)
            
        lookProps.blend_file_index = -1
        lookProps.materials.clear()    

    def execute(self, context):
        preferences = context.preferences.addons["look_assigner"].preferences
        lookProps = context.scene.LookAssigner_Properties    
        selected_path_index = int(lookProps.selected_path_enum)

        if selected_path_index < len(preferences.paths):
            selected_path = preferences.paths[selected_path_index].file_path
            self.scan_for_blend_files(selected_path, context)
        return {'FINISHED'}


def update_path_enum(self, context):
    bpy.ops.object.scan_for_blend_files()

def update_materials( self, context):
    prefs = context.preferences.addons["look_assigner"].preferences
    lookProps = context.scene.LookAssigner_Properties

    lookProps.materials_filtered = 0 
    lookProps.materials.clear()

    blend_file_index = lookProps.blend_file_index
    if blend_file_index >= 0 and blend_file_index < len(lookProps.blend_files):
        blend_file_path = lookProps.blend_files[blend_file_index].path
        material_filter = prefs.material_filter.lower()

        logger.debug (f'Filtering to include materials containing {prefs.material_filter}, Ignoring materials named : {prefs.ignore_filter}')
        ignore_filter_list = [item.strip() for item in prefs.ignore_filter.lower().split(",")]
        materials = get_materials_from_blend( blend_file_path)
        for material_name in materials:
            if lookProps.list_all_materials:
                material_item = lookProps.materials.add()
                material_item.name = material_name
            elif (material_filter in material_name.lower()) and (material_name.lower() not in ignore_filter_list):
                material_item = lookProps.materials.add()
                material_item.name = material_name
            else:
                lookProps.materials_filtered+=1

def get_materials_from_blend( filepath ):
    """
    this is to retrieve the contents of the blend file's materials, without actually loading them into the scene
    
    """
    material_names = []
    # Load the blend file
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        # Check if materials are present in the blend file
        if data_from.materials:
            # Append each material name to the list
            for mat_name in data_from.materials:
                material_names.append(mat_name)
    return material_names


class BlendFileItem(PropertyGroup):
    name: StringProperty(name="File Name",default="")
    path: StringProperty(name="File Path",default="")

class MaterialItem(PropertyGroup):
    name: StringProperty(name="Material Name",default="")
    use: BoolProperty(name="Use Material", default=False)


class LookAssignerProperties(PropertyGroup):
    blend_files : CollectionProperty(type=BlendFileItem )
    blend_file_index : IntProperty(name="Index for blend_files", default=-1, update=update_materials)
    materials : CollectionProperty(type=MaterialItem)
    materials_filtered : IntProperty(name="Materials Filtered", default=0)
    selected_objects_only : BoolProperty(name="Selected Objects Only", default=False)
    force_assign : BoolProperty(name="Force Material Assignment", default=False)
    purge_material_datablocks : BoolProperty(name="Purge Unused Datablocks", default=False)
    expand_to_collection : IntProperty(name="Expand To Collection", default=False)
    list_all_materials : BoolProperty(name="Ignore naming filters", default=False, update=update_materials)
    selected_path_enum : EnumProperty(
        name="Scan Path",
        items=lambda self, context: context.preferences.addons["look_assigner"].preferences.path_items(context),
        update=update_path_enum,
    )
    create_look_help_subpanel: bpy.props.BoolProperty(
        name="Help Subpanel",
        description="UI Toggle for the help subpanel",
        default=False
    )

def register():
    bpy.utils.register_class(ScanForBlendFilesOperator)
    bpy.utils.register_class(BlendFileItem)
    bpy.utils.register_class(MaterialItem)
    bpy.utils.register_class(LookAssignerProperties)
    bpy.types.Scene.LookAssigner_Properties = PointerProperty(type=LookAssignerProperties)

def unregister():
    
    bpy.utils.unregister_class(ScanForBlendFilesOperator)
    bpy.utils.unregister_class(BlendFileItem)
    bpy.utils.unregister_class(MaterialItem)
    bpy.utils.unregister_class(LookAssignerProperties)
    del bpy.types.Scene.LookAssigner_Properties


