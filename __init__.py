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
    imp.reload(vi_ui)
else:
    from . import vi_node, vi_operators, vi_ui

import sys, os, platform, inspect, glob, bpy, nodeitems_utils
from bpy.props import IntProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty, FloatVectorProperty

 
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
#    bpy.utils.register_module(__name__)
    Object = bpy.types.Object   
    Scene = bpy.types.Scene

# Object properties
    Object.livi_merr = BoolProperty(name="LiVi simple mesh export", description="Boolean for simple mesh export", default = False)
            
    Object.ies_name = StringProperty(name="", description="IES File", maxlen=1024, default="")

    Object.ies_strength = FloatProperty(name="", description="Strength of IES lamp", min = 0, max = 1, default = 1)

    Object.ies_unit = EnumProperty(items=[("m", "Meters", ""), ("c", "Centimeters", ""), ("f", "Feet", ""), ("i", "Inches", "")], name="", description="Specify the IES file measurement unit", default="m")

    Object.ies_colour = FloatVectorProperty(name="IES Colour",attr = 'IES Colour', default = [1.0, 1.0, 1.0], subtype = 'COLOR')
    
    Object.licalc = BoolProperty(default = False)
    
    Object.lires = BoolProperty(default= False)   

    Object.limerr = BoolProperty(default= False)         

    Scene.vipath = StringProperty(name="VI Path", description="Path to files included with the VI-Suite ", maxlen=1024, default=addonpath)        

    Scene.li_disp_panel = IntProperty(name="Display Panel", description="Shows the Display Panel", default=0)

    Scene.li_disp_3d = BoolProperty(name="VI 3D display", description="Boolean for 3D results display", default= False)
    
    Scene.li_disp_3dlevel = FloatProperty(name="VI 3D display level:", description="Level of 3D result plane extrusion", min = 0, max = 50, default = 0)
    
    Scene.li_display = BoolProperty(default = False)
    
    Scene.li_display_rp = BoolProperty(name = "", default = False)

    Scene.li_display_sel_only = BoolProperty(name = "", default = False)

    Scene.li_display_rp_fs = IntProperty(name="", description="Point result font size", default=9)
    
    Scene.resnode = StringProperty()
    
    bpy.utils.register_class(vi_operators.NODE_OT_EpwSelect)
    bpy.utils.register_class(vi_operators.NODE_OT_HdrSelect)
    bpy.utils.register_class(vi_operators.NODE_OT_SkySelect)
    bpy.utils.register_class(vi_operators.IES_Select)
    bpy.utils.register_class(vi_operators.NODE_OT_RadPreview)
    bpy.utils.register_class(vi_operators.NODE_OT_Calculate)
    bpy.utils.register_class(vi_operators.NODE_OT_GeoExport)
    bpy.utils.register_class(vi_operators.NODE_OT_LiExport)
    bpy.utils.register_class(vi_operators.NODE_OT_LiGExport)
    bpy.utils.register_class(vi_operators.VIEW3D_OT_LiDisplay)
    bpy.utils.register_class(vi_operators.VIEW3D_OT_LiNumDisplay)
    bpy.utils.register_class(vi_ui.Vi3DPanel)
    bpy.utils.register_class(vi_ui.IESPanel)
    bpy.utils.register_class(vi_ui.RadMatPanel)
    bpy.utils.register_class(vi_node.EnViDataIn)
    bpy.utils.register_class(vi_node.ViLiWResOut)
    bpy.utils.register_class(vi_node.ViLiGIn)
    bpy.utils.register_class(vi_node.ViLiGOut)
    bpy.utils.register_class(vi_node.ViNetwork)
    bpy.utils.register_class(vi_node.ViLiNode)
    bpy.utils.register_class(vi_node.ViGExLiNode)
    bpy.utils.register_class(vi_node.ViLiCNode)
    bpy.utils.register_class(vi_node.ViLiCBNode)
    bpy.utils.register_class(vi_node.ViSPNode)
    bpy.utils.register_class(vi_node.ViSSNode)
    bpy.utils.register_class(vi_node.ViWRNode)
    bpy.utils.register_class(vi_node.ViGNode)
    bpy.utils.register_class(vi_node.ViEPNode)
    nodeitems_utils.register_node_categories("Vi Nodes", vi_node.vinode_categories)

def unregister():
#    bpy.utils.unregister_module(__name__)
    bpy.utils.unregister_class(vi_operators.NODE_OT_EpwSelect)
    bpy.utils.unregister_class(vi_operators.NODE_OT_HdrSelect)
    bpy.utils.unregister_class(vi_operators.NODE_OT_SkySelect)
    bpy.utils.unregister_class(vi_operators.IES_Select)
    bpy.utils.unregister_class(vi_operators.NODE_OT_RadPreview)
    bpy.utils.unregister_class(vi_operators.NODE_OT_LiCalculate)
    bpy.utils.unregister_class(vi_operators.NODE_OT_GeoExport)
    bpy.utils.unregister_class(vi_operators.NODE_OT_LiExport)
    bpy.utils.unregister_class(vi_operators.NODE_OT_LiGExport)
    bpy.utils.unregister_class(vi_operators.VIEW3D_OT_LiDisplay)
    bpy.utils.unregister_class(vi_operators.VIEW3D_OT_LiNumDisplay)
    bpy.utils.unregister_class(vi_ui.Vi3DPanel)
    bpy.utils.unregister_class(vi_ui.IESPanel)
    bpy.utils.unregister_class(vi_ui.RadMatPanel)
    bpy.utils.unregister_class(vi_node.EnViDataIn)
    bpy.utils.unregister_class(vi_node.ViLiWResOut)
    bpy.utils.unregister_class(vi_node.ViLiGIn)
    bpy.utils.unregister_class(vi_node.ViLiGOut)
    bpy.utils.unregister_class(vi_node.ViNetwork)
    bpy.utils.unregister_class(vi_node.ViLiNode)
    bpy.utils.unregister_class(vi_node.ViGExLiNode)
    bpy.utils.unregister_class(vi_node.ViLiCNode)
    bpy.utils.unregister_class(vi_node.ViLiCBNode)
    bpy.utils.unregister_class(vi_node.ViSPNode)
    bpy.utils.unregister_class(vi_node.ViSSNode)
    bpy.utils.unregister_class(vi_node.ViWRNode)
    bpy.utils.unregister_class(vi_node.ViGNode)
    bpy.utils.unregister_class(vi_node.ViEPNode)
    nodeitems_utils.unregister_node_categories("Vi Nodes", vi_node.vinode_categories)
    