import bpy
from . import bl_info
from bpy.types import Panel, UIList, Operator

from . import preferences

from .utils import LoggerFactory
logger = LoggerFactory.get_logger()

class UI_UL_CustomPath_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.25)
        icon_value = 'FILE_SCRIPT' if item.from_json else 'FILE_FOLDER'
        split.prop(item, "name", text="", emboss=False, icon=icon_value)
        split.prop(item, "file_path", text="")

class BlendFilePanel(Panel):
    bl_label = "Look Assigner" 
    bl_label = f"The Line - Look Assigner v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
    bl_idname = "OBJECT_PT_look_assigner"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Look Assigner'

    def draw(self, context):

        prefs = preferences.get(context)
        lookProps = context.scene.LookAssigner_Properties

        layout = self.layout
        box = layout.box()
        box.label(text='Create Pipelined Look Shaders', icon='SCENE_DATA')

        row = box.row()
        row.operator( "object.build_pipelined_shader_file_operator", text="Create Look from Scene", icon="BRUSH_DATA")          
        row.operator( "object.custom_export_blend", text="Export Selected To Blend", icon="BLENDER")

        row = box.row()
        icon = 'TRIA_DOWN' if lookProps.create_look_help_subpanel else 'TRIA_RIGHT'
        row.prop(lookProps, 'create_look_help_subpanel', icon=icon, icon_only=True)
        row.label(text='Help')

        if lookProps.create_look_help_subpanel:
            col_flow = box.column_flow(columns=1, align=True)
            col_flow.label(text='Run "Create Look From Scene" in your 3d_look master file.')
            col_flow.label(text='It will create a new scene with all shaders inside.')
            col_flow.label(text='You can then choose to publish this scene as a')
            col_flow.label(text='blend file into a per asset, or global look task.')

        box = layout.box()

        if prefs.paths and len(prefs.paths) > 0:

            if lookProps.selected_path_enum:
                box.label(text=f'Full Path : {prefs.paths[int(lookProps.selected_path_enum)].file_path}', icon='FILE_FOLDER')        
                enum_count = len(prefs.path_items(context))

                if enum_count > 4:
                    tab_count = 4
                else:
                    tab_count = enum_count

                col_flow = box.column_flow(columns=tab_count, align=True)        
                col_flow.prop(lookProps, "selected_path_enum", text="Asset Folder Root",expand=True)
                
                # Calculate the number of blend files
                blend_files_count = len(lookProps.blend_files)
                
                # Determine the number of rows based on the count, up to a maximum of 20
                num_rows = min(blend_files_count, 10)

                if num_rows == 1:
                    display_str = "Blend Shader file" 
                else:
                    display_str = "Blend Shader files"
            else:
                display_str = "Select a folder root to view any stored shader files."
   
        else:
            display_str = "Add a folder root in the addon preferences."
            box.operator("object.open_addon_preferences") 
            num_rows = 0
        
        # Set the panel size dynamically based on the number of blend files
        # Adjust the height depending on the number of blend files found
        if num_rows > 0:
            row_height = 10  # Height per row (adjust as needed)
            # panel_height = num_rows * row_height + 14
            layout.label(text=f"Found {blend_files_count} {display_str}:")


            layout.template_list("BLEND_UL_file_list", "", lookProps, "blend_files", lookProps, "blend_file_index", type='DEFAULT', columns=1, rows=num_rows+1)
        
            box = layout.box()
            box.label(text='Load Filters')
            grid = box.grid_flow(columns=2, align=True)   


            grid.prop( lookProps, "list_all_materials", text="Bypass Material Filters", icon="EMPTY_SINGLE_ARROW")
            grid.prop( lookProps, 'selected_objects_only', icon='FILE_3D', text="Assign to Selection Only")        
            grid.prop( lookProps, 'force_assign', text="Force Assignment", icon="PLUS")
            grid.operator("object.purge_unused_materials", text="Remove Unused Materials", icon="GHOST_ENABLED") 

        # else:
        #     box.label(text="Add a folder root in the addon preferences.", icon='SETTINGS')
        #     box.operator("object.open_addon_preferences") 
        
        # Optionally, add other UI elements below the list
        # layout.operator("object.look_assigner", text="Scan for Blend Files")

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='FILE_BLEND')

    @classmethod
    def poll(cls, context):
        return True

class MaterialPanel(bpy.types.Panel):
    bl_label = "Shader List"
    bl_idname = "OBJECT_PT_material_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Look Assigner'

            
    def text_row(self, parent, text, icon, label, factor):
        split = parent.split(factor=factor)
        split.label(text=text , icon=icon)
        split.label(text=label)

    def draw(self, context):
        layout = self.layout
        lookProps = context.scene.LookAssigner_Properties
        prefs = preferences.get(context)

        # the material layout area
        box = layout.box()

        fancy_grammar = "Shaders"
        display_icon='MATERIAL'
        col_width = 2

        if prefs.paths and len(prefs.paths) > 0:
            # there are root folders! 
            if len(lookProps.blend_files) > 0:
                if lookProps.blend_file_index > -1:
                    num_mats = len(lookProps.materials)
                    if num_mats == 0:
                        box_label = ''
                    elif num_mats == 1:                        
                        box_label = 'Published Shaders - '
                        fancy_grammar = "Shader"
                        col_width = 1
                    else:
                        box_label = 'Published Shaders - '
                else:
                    box_label = 'Highlight the shader file to view the stored materials - '
                    
            else:
                box_label = 'Click a folder root above to show any shader files. - '
                display_icon = "TRIA_UP"
 
        else:
            box_label = "There are no shader root paths set - Please check the addon preferences. - "
            display_icon='SETTINGS'

        if lookProps.materials_filtered > 0:
            extra_text = f"({lookProps.materials_filtered} removed by material filter)"
        else:
            extra_text = ""

        box.label(text=f'{box_label}{len(lookProps.materials)} {fancy_grammar} Found {extra_text}', icon=display_icon)

        col = box.column()

        if len(lookProps.materials) > 0:
            split = col.split(factor=0.8)
            split.label( text="")
            col_flow = split.column_flow(columns=3, align=True)
            col_flow.operator("object.check_all_materials_operator", text="", icon="CHECKBOX_HLT")
            col_flow.operator("object.uncheck_all_materials_operator", text="", icon="CHECKBOX_DEHLT")
            col_flow.operator("object.invert_check_state_operator", text="", icon="ARROW_LEFTRIGHT")

            col_flow = box.column_flow(columns=col_width, align=True)

            for index, material in enumerate(lookProps.materials):
                row = col_flow.row()
                row.prop(material, "use", text="")
                row.operator("object.toggle_material_use", text=material.name, icon='MATERIAL').material_index = index

        col = layout.column()
        col.scale_y = 1.5           
        col.operator("object.load_materials_operator", text="Load Selected Materials")


"""
These operators are buttons on Material Panel, hence why they are included here 
"""

class InvertCheckStateOperator(Operator):
    bl_idname = "object.invert_check_state_operator"
    bl_label = "Invert Check State"

    @classmethod
    def poll(cls, context):
        return ("LookAssigner_Properties" in context.scene and "materials" in context.scene.LookAssigner_Properties)

    def execute(self, context):
        for material in context.scene.LookAssigner_Properties.materials:
            material.use = not material.use
        return {'FINISHED'}

class CheckAllMaterialsOperator(Operator):
    bl_idname = "object.check_all_materials_operator"
    bl_label = "Check All Materials"

    @classmethod
    def poll(cls, context):
        return("LookAssigner_Properties" in context.scene and "materials" in context.scene.LookAssigner_Properties)

    def execute(self, context):
        for material in context.scene.LookAssigner_Properties.materials:
            material.use = True
        return {'FINISHED'}

class UncheckAllMaterialsOperator(Operator):
    bl_idname = "object.uncheck_all_materials_operator"
    bl_label = "Uncheck All Materials"

    @classmethod
    def poll(cls, context):
        return ("LookAssigner_Properties" in context.scene and "materials" in context.scene.LookAssigner_Properties)

    def execute(self, context):
        for material in context.scene.LookAssigner_Properties.materials:
            material.use = False
        return {'FINISHED'}

class BLEND_UL_file_list(UIList):
    """Custom UI list to show blend files with icons"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        blend_file = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=blend_file.name, icon='BLENDER')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='BLENDER')

class_list = [
    UI_UL_CustomPath_List,
    BlendFilePanel,
    MaterialPanel,
    InvertCheckStateOperator,
    CheckAllMaterialsOperator,
    UncheckAllMaterialsOperator,
    BLEND_UL_file_list,
]

def register():    

    for cls in class_list:
        bpy.utils.register_class(cls)

def unregister():

    for cls in class_list:
        bpy.utils.unregister_class(cls)


