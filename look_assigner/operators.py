import bpy
import os
from bpy.types import Operator
from bpy.props import IntProperty
import math
import re

from . import utils
from . import preferences

from .utils import LoggerFactory
logger = LoggerFactory.get_logger()

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

class OT_toggle_material_use(bpy.types.Operator):
    bl_idname = "object.toggle_material_use"
    bl_label = "Toggle Material Use"

    material_index: IntProperty()

    def execute(self, context):
        material = context.scene.LookAssigner_Properties.materials[self.material_index]
        material.use = not material.use
        return {'FINISHED'}
    
class OT_open_addon_preferences(bpy.types.Operator):
    bl_idname = "object.open_addon_preferences"
    bl_label = "Open Addon Preferences"

    def execute(self, context):
        package = "look_assigner"
        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        bpy.context.preferences.active_section  = "ADDONS"
        bpy.ops.preferences.addon_expand(module=package)
        bpy.ops.preferences.addon_show(module=package)
        return {'FINISHED'}

class BuildPipelinedShaderFileOperator(Operator):
    bl_idname = "object.build_pipelined_shader_file_operator"
    bl_label = "Build Pipeline Shader File"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        prefs = preferences.get(context)     
        # context.preferences.addons[__name__].preferences
        lookProps = context.scene.LookAssigner_Properties

        # Step 1: Collect materials and the objects they are applied to
        material_dict = {}

        for obj in bpy.data.objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:  # Checking types that can have materials
                for slot in obj.material_slots:
                    if slot.material:
                        mat_name = slot.material.name
                        if mat_name not in material_dict:
                            material_dict[mat_name] = []
                        material_dict[mat_name].append(obj.name)

        # Step 2: Add custom property to each material
        for mat_name, objects in material_dict.items():
            mat = bpy.data.materials[mat_name]
            mat[prefs.pipeline_attribute_name] = ", ".join(objects)

        # Step 3: Create a new scene called PUBLISH_SHADERS
        new_scene_name = "PUBLISH_SHADERS"
        if new_scene_name in bpy.data.scenes:
            bpy.data.scenes.remove(bpy.data.scenes[new_scene_name])
        new_scene = bpy.data.scenes.new(new_scene_name)
        bpy.context.window.scene = new_scene

        # Create a new collection in the new scene
        new_collection_name = "PUBLISH_SHADERS"
        new_collection = bpy.data.collections.new(new_collection_name)
        new_scene.collection.children.link(new_collection)

        # Change the collection's color in the outliner
        new_collection.color_tag = 'COLOR_04'  # This sets the color to green

        # Step 4: Create spheres for each material in the new scene and assign the materials
        # Calculate the grid size
        num_materials = len(material_dict)
        grid_size = math.ceil(math.sqrt(num_materials))

        # Offset for the spheres in the grid
        offset = 2.5

        # Iterate over materials and create spheres
        x = 0
        y = 0
        for i, (mat_name, objects) in enumerate(material_dict.items()):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x * offset, y * offset, 0))
            sphere = bpy.context.object
            sphere.name = f"{mat_name}"
            sphere.data.materials.append(bpy.data.materials[mat_name])
            
            # Link the sphere to the new collection
            new_collection.objects.link(sphere)
            new_scene.collection.objects.unlink(sphere)
            
            x += 1
            if x >= grid_size:
                x = 0
                y += 1

        logger.info (f"Created {num_materials} spheres in the scene '{new_scene_name}' with assigned materials and added to the collection '{new_collection_name}'.")
        bpy.ops.view3d.view_all(center=False)
        return {'FINISHED'}

class OBJECT_OT_custom_export_blend(bpy.types.Operator):
    """Custom Export Blend Operator"""
    bl_idname = "object.custom_export_blend"
    bl_label = "Custom Export Blend"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Check if the export_scene.blend operator is available
        return hasattr(bpy.ops.export_scene, 'blend')

    def execute(self, context):
        # Call the export_scene.blend operator
        bpy.ops.export_scene.blend('INVOKE_DEFAULT')
        return {'FINISHED'}


class LoadMaterialsOperator(Operator):
    bl_idname = "object.load_materials_operator"
    bl_label = "Assign Shaders"
    bl_description = "Assigns Shaders to Objects, pipeline data or not."
    bl_options = {'REGISTER', 'UNDO'}

    """
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)    

    # Force update the scene
    bpy.context.view_layer.update()


    """

    def append_materials_from_file(self, filepath, material_names):
        imported_materials = []  # List to store imported material data

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            for material_name in material_names:
                if material_name in data_from.materials:
                    data_to.materials.append(material_name)
                    logger.info(f"Appending material: {material_name}")
                else:
                    logger.debug(f"Material {material_name} not found in {filepath}")
        
        # Collect the imported materials immediately after loading them
        for material_name in material_names:
            mat = bpy.data.materials.get(material_name)
            if mat:
                imported_materials.append(mat)

        return imported_materials
    

    def create_regex_pattern(self, object_name):
        """
        Create a regex pattern for the given object name to match optional namespace and .### suffix.
        """
        # Escape any special characters in the object name
        escaped_name = re.escape(object_name)
        
        # Pattern to match optional namespace prefix and optional .### suffix
        pattern = re.compile(r'([a-zA-Z0-9_]+:)?' + escaped_name + r'(\.\d{3})?$')

        return pattern


    def fuzzy_search_objects(self,objects, object_names):
        """
        Check if the object names (with optional .### suffix) are in the scene.
        Returns a flat list of matched object names.
        """
        # Get all object names in the current scene
        scene_object_names = [obj.name for obj in objects]
        
        # List to store all matched scene object names
        matched_object_names = []
        
        # Iterate through each object name and check for matches
        for name in object_names:
            pattern = self.create_regex_pattern(name)
            matches = [scene_name for scene_name in scene_object_names if pattern.match(scene_name)]
            
            if matches:
                matched_object_names.extend(matches)
        
        return matched_object_names

    def assign_materials_from_pipeline_data(self, pipeline_attr, objects, shader_list):

        for mat in shader_list:
            if pipeline_attr in mat:
                obj_names = mat[pipeline_attr].split(", ")

                # handle namespaces and blender's .### naming issue
                
                validated_object_list = self.fuzzy_search_objects(objects, obj_names)
                logger.info (f'Validated object list - {validated_object_list}')

                for obj_name in validated_object_list:
                    obj = bpy.data.objects.get(obj_name)

                    if obj and obj in objects:
                        # look at how this is done - if there are already materials, it should clear them
                        if obj.data.materials:
                            obj.data.materials[0] = mat
                        else:
                            # Create a new material slot and assign
                            # CLEAR MATERIALS FIRST                         
                            obj.data.materials.clear()
                            obj.data.materials.append(mat)
                        # Update the object to ensure the material assignment takes effect
                            logger.info (f'Shader {mat.name} assigned to : {obj.name}')
                        obj.update_tag(refresh={'DATA'})
                    else:
                        logger.info(f"Stored Geometry Object : {obj_name} not found in scene")

        # Redraw all areas to ensure the viewport is updated
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    @classmethod
    def poll(cls, context):
        return "LookAssigner_Properties" in context.scene and "materials" in context.scene.LookAssigner_Properties.materials

    def execute(self, context):
        prefs = context.preferences.addons["look_assigner"].preferences
        lookProps = context.scene.LookAssigner_Properties    
        selected_objects_only =  lookProps.selected_objects_only

        materials = [mat.name for mat in lookProps.materials if mat.use]
        current_shader_file = lookProps.blend_files[lookProps.blend_file_index].path

        if len(materials) == 0:
            self.report({"WARNING"}, "No Shaders Marked. Please enable the Shaders you want to assign")

        if len(materials) > 1 and lookProps.force_assign:
            self.report({"WARNING"}, "You can only force assign a single shader to the scene or selection")
        else:

            logger.debug (f'Shader File : {current_shader_file}')
            logger.debug (f'Material Load Buffer :{materials}')
            
            if selected_objects_only:
                objects = [obj for obj in context.selected_objects if obj.type == 'MESH']            
            else:
                # need to filter the scene objects to meshes or whatever
                objects = [obj for obj in context.scene.objects if obj.type == 'MESH']  

            logger.debug (f'Viable Object Buffer {objects}')

            # step1 - Import the shaders into the current blend file        
            imported_shaders = self.append_materials_from_file(current_shader_file, materials)
            logger.debug (f'imported_shaders {imported_shaders}')


            #step 2 = need to check if it's a pipeline assignment scenario

            pipelined_shaders = []
            standard_shaders = []
            
            for shader in imported_shaders:
                geo_attr = preferences.pipeline_attribute_name
                if geo_attr in shader:
                    logger.debug (f'Pipeline Data {shader.name}  {shader[geo_attr]}')
                    pipelined_shaders.append(shader)
                else:
                    logger.debug (f'Pipeline Data {shader.name}  No pipeline data attribute found')
                    standard_shaders.append(shader)

            # step 3 we've already filtered everything by this point, we just need to check if it needs to be forced onto the objects
            for obj in objects:
                for mat_name in materials:
                    if mat_name not in obj.data.materials:
                        if lookProps.force_assign:
                            mat = bpy.data.materials.get(mat_name)
                            logger.debug (f'Material : {mat}')
                            if mat:
                                obj.data.materials.clear()
                                obj.data.materials.append(mat)
                        # if we are not force assigning, we can grab the published data to see what needs to be assigned where
                        else:                      
                            if pipelined_shaders:
                                self.assign_materials_from_pipeline_data( prefs.pipeline_attribute_name, objects, pipelined_shaders )
 
        bpy.context.view_layer.update()
        return {'FINISHED'}
 
class OT_Look_Shader_to_Collection(bpy.types.Operator):
    bl_idname = "object.look_shader_to_collection"
    bl_description  = "Assigns the current shader to the complete collection"
    bl_label = "Shader to Collection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) == 1
    
    def select_objects_in_collection(self,collection_name):    
    #    collection_name = bpy.context.collection.name
        # Iterate through all collections to find the one with the given name
        for collection in bpy.data.collections:
            if collection.name == collection_name:
                # Deselect all objects
                bpy.ops.object.select_all(action='DESELECT')
                # Select objects in the collection
                for obj in collection.objects:
                    obj.select_set(True)        
                bpy.ops.object.material_slot_copy()
    
    def execute(self, context):
        try:       
            obj = bpy.context.object
            cn = obj.users_collection
            self.select_objects_in_collection(cn[0].name_full)         
        except:
            utils.ShowMessageBox(message="There was an issue applying the shaders.",  
                                 title = "Shader To Collection", 
                                 icon='MATERIAL'
                                 )
        return {'FINISHED'} 
    
class OBJECT_OT_purge_unused_materials(bpy.types.Operator):
    """Purge Unused Materials"""
    bl_idname = "object.purge_unused_materials"
    bl_label = "Purge Unused Materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        # Iterate over all materials and remove those with no users
        materials_to_remove = [mat for mat in bpy.data.materials if mat.users == 0]

        for mat in materials_to_remove:
            bpy.data.materials.remove(mat)
        
        self.report({'INFO'}, f"Removed {len(materials_to_remove)} unused materials.")
        return {'FINISHED'}
    
def menu_func(self, context):
    self.layout.operator(OBJECT_OT_purge_unused_materials.bl_idname)

class_list = [
    OT_toggle_material_use, 
    LoadMaterialsOperator,
    BuildPipelinedShaderFileOperator,
    OT_Look_Shader_to_Collection,
    OBJECT_OT_custom_export_blend,
    OBJECT_OT_purge_unused_materials,
    OT_open_addon_preferences,
]

def register():    
    for cls in class_list:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    for cls in class_list:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
