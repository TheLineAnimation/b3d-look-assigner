'''
  _____ _  _ ___   _    ___ _  _ ___            
 |_   _| || | __| | |  |_ _| \| | __|           
 _______________________________________           
   |_| |_||_|___| |____|___|_|\_|___|           
                                                
    _   _  _ ___ __  __   _ _____ ___ ___  _  _ 
   /_\ | \| |_ _|  \/  | /_\_   _|_ _/ _ \| \| |
  / _ \| .` || || |\/| |/ _ \| |  | | (_) | .` |
 /_/ \_\_|\_|___|_|  |_/_/ \_\_| |___\___/|_|\_|
                                                
Look Assigner

A complete system for pipelining and loading Blender shaders

'''

bl_info = {
    "name": "Look Assigner",
    "author": "Pete.Addington",
    "version": (1, 3, 0),
    "blender": (4, 1, 0),
    "location": "3d View > Look Assigner",
    "warning": "", # used for warning icon and text in addons panel
    "description":"A system for pipelining, versioning and loading Blender shaders onto 3d assets",
    "category": "TheLine" 
}

if "bpy" in locals():
    import importlib
    importlib.reload(preferences)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    import bpy
    from . import preferences
    from . import properties
    from . import operators
    from . import ui

def register():

    preferences.register()
    properties.register()
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()
    preferences.unregister()

if __name__ == "__main__":
    register()
    
