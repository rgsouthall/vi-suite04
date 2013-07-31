bl_info = {
    "name": "VI-Suite",
    "author": "Ryan Southall",
    "version": (0, 1, 0),
    "blender": (2, 6, 8),
    "api":"",
    "location": "Node Editor & 3D View > Properties Panel",
    "description": "Radiance/EnergyPlus exporter and results visualiser",
    "warning": "This is a beta script. Some functionality is buggy",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

if "bpy" in locals():
    import imp
    imp.reload(vi_node)
    imp.reload(vi_operators)
else:
    from . import vi_node, vi_operators

import sys, os, platform, inspect, glob, bpy, nodeitems_utils
from bpy.types import IntProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty

 
epversion = "8-0-0" 
addonpath = os.path.dirname(inspect.getfile(inspect.currentframe()))

if str(sys.platform) == 'darwin':
    if not hasattr(os.environ, 'RAYPATH'):
        if platform.architecture() == "64bit":
            os.environ["PATH"] = os.environ["PATH"] + ":/usr/local/radiance/bin:{}/io_visuite/osx/64:/Applications/EnergyPlus-{}/bin".format(addonpath, epversion)
        else:
             os.environ["PATH"] = os.environ["PATH"] + ":/usr/local/radiance/bin:{}/io_visuite/osx:/Applications/EnergyPlus-{}/bin".format(addonpath, epversion)
        os.environ["RAYPATH"] = "/usr/local/radiance/lib:{}/io_visuite/lib".format(addonpath)

if str(sys.platform) == 'linux':
    if not hasattr(os.environ, 'RAYPATH'):
        os.environ["PATH"] = os.environ["PATH"] + ":/usr/local/radiance/bin:{}/io_visuite/osx:/usr/local/EnergyPlus-{}/bin".format(addonpath, epversion)
        os.environ["RAYPATH"] = "/usr/local/radiance/lib:{}/io_visuite/lib".format(addonpath)

elif str(sys.platform) == 'win32':
    if os.path.isdir(r"C:\Program Files (x86)\Radiance"):
        if r"C:\Program Files (x86)\Radiance\lib;"+sys.path[0]+"\io_visuite\lib" not in os.environ["RAYPATH"]:
            os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files (x86)\Radiance\bin;"+sys.path[0]+"\io_visuite\windows;C:\EnergyPlusV{}".format(epversion)
            os.environ["RAYPATH"] = r"C:\Program Files (x86)\Radiance\lib;"+sys.path[0]+"\io_visuite\lib"
    
    elif os.path.isdir(r"C:\Program Files\Radiance"):
        if r"C:\Program Files\Radiance\lib;"+sys.path[0]+"\io_visuite\lib" not in os.environ["RAYPATH"]:
            os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files\Radiance\bin;"+sys.path[0]+"\io_visuite\windows;C:\EnergyPlusV{}".format(epversion) 
            os.environ["RAYPATH"] = "C:\Program Files\Radiance\lib;"+sys.path[0]+"\io_visuite\lib"
    else:
        print("Cannot find a valid Radiance directory. Please check that you have Radiance installed in either C:\Program Files(x86) (64bit windows) \
or C:\Program Files (32bit windows)")

matpath = addonpath+'/EPFiles/Materials/Materials.data'
epwpath = addonpath+'/EPFiles/Weather/'
               
#bpy.ops.node.new_node_tree(type='ViN', name ="VI-Suite Node Tree")

def register():
    Object = bpy.types.Object    

# Object properties
    Object.licalc = BoolProperty(name="LiVi calc object", description="Boolean for calculation object", default = False)
    Object.lires = BoolProperty(name="LiVi res object", description="Boolean for results object", default= False)
#            
#    Object.livi_merr = IntProperty(
#            name="LiVi simple mesh export", description="Boolean for simple mesh export", default=0)
#            
#    Object.ies_name = StringProperty(name="Path", description="IES File", maxlen=1024, default="")
#
#    Object.ies_strength = FloatProperty(name="Lamp strength:", description="Strength of IES lamp", min = 0, max = 1, default = 1)
#
#    Object.ies_unit = EnumProperty(
#            items=[("m", "Meters", ""),
#                   ("c", "Centimeters", ""),
#                    ("f", "Feet", ""),
#                    ("i", "Inches", ""),
#                    ],
#            name="IES dimension",
#            description="Specify the IES file measurement unit",
#            default="m")
            
    bpy.utils.register_class(vi_operators.NODE_OT_EpwSelect)
    bpy.utils.register_class(vi_operators.NODE_OT_HdrSelect)
    bpy.utils.register_class(vi_operators.NODE_OT_SkySelect)
    bpy.utils.register_class(vi_operators.NODE_OT_RadPreview)
    bpy.utils.register_class(vi_operators.NODE_OT_Calculate)
    bpy.utils.register_class(vi_operators.NODE_OT_GeoExport)
    bpy.utils.register_class(vi_operators.NODE_OT_LiExport)
    bpy.utils.register_class(vi_node.EnViDataIn)
    bpy.utils.register_class(vi_node.ViLiWResOut)
    bpy.utils.register_class(vi_node.ViNetwork)
    bpy.utils.register_class(vi_node.ViLiNode)
    bpy.utils.register_class(vi_node.ViLiCNode)
    bpy.utils.register_class(vi_node.ViLiCBNode)
    bpy.utils.register_class(vi_node.ViSPNode)
    bpy.utils.register_class(vi_node.ViSSNode)
    bpy.utils.register_class(vi_node.ViWRNode)
    bpy.utils.register_class(vi_node.ViGNode)
    bpy.utils.register_class(vi_node.ViEPNode)
    nodeitems_utils.register_node_categories("Vi Nodes", vi_node.vinode_categories)

            
def unregister():
    bpy.utils.unregister_class(vi_operators.NODE_OT_EpwSelect)
    bpy.utils.unregister_class(vi_operators.NODE_OT_HdrSelect)
    bpy.utils.unregister_class(vi_operators.NODE_OT_SkySelect)
    bpy.utils.unregister_class(vi_operators.NODE_OT_RadPreview)
    bpy.utils.unregister_class(vi_operators.NODE_OT_Calculate)
    bpy.utils.unregister_class(vi_operators.NODE_OT_GeoExport)
    bpy.utils.unregister_class(vi_operators.NODE_OT_LiExport)
    bpy.utils.unregister_class(vi_node.EnViDataIn)
    bpy.utils.unregister_class(vi_node.ViLiWResOut)
    bpy.utils.unregister_class(vi_node.ViNetwork)
    bpy.utils.unregister_class(vi_node.ViLiNode)
    bpy.utils.unregister_class(vi_node.ViLiCNode)
    bpy.utils.unregister_class(vi_node.ViLiCBNode)
    bpy.utils.unregister_class(vi_node.ViSPNode)
    bpy.utils.unregister_class(vi_node.ViSSNode)
    bpy.utils.unregister_class(vi_node.ViWRNode)
    bpy.utils.unregister_class(vi_node.ViGNode)
    bpy.utils.unregister_class(vi_node.ViEPNode)
    nodeitems_utils.unregister_node_categories("Vi Nodes", vi_node.vinode_categories)