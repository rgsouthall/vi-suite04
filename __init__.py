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
else:
    from . import vi_node 

import sys, os, platform, inspect, glob, bpy

epversion = "8-0-0" 
addonpath = os.path.dirname(inspect.getfile(inspect.currentframe()))

if str(sys.platform) == 'darwin':
    if "/usr/local/radiance/lib:{}/io_visuite/lib".format(addonpath) not in os.environ["RAYPATH"]:
        if platform.architecture() == "64bit":
            os.environ["PATH"] = os.environ["PATH"] + ":/usr/local/radiance/bin:{}/io_visuite/osx/64:/Applications/EnergyPlus-{}/bin".format(addonpath, epversion)
        else:
             os.environ["PATH"] = os.environ["PATH"] + ":/usr/local/radiance/bin:{}/io_visuite/osx:/Applications/EnergyPlus-{}/bin".format(addonpath, epversion)
        os.environ["RAYPATH"] = "/usr/local/radiance/lib:{}/io_visuite/lib".format(addonpath)

if str(sys.platform) == 'linux':
    if "/usr/local/radiance/lib:{}/io_visuite/lib".format(addonpath) not in os.environ["RAYPATH"]:
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

matpath = os.path.dirname(inspect.getfile(inspect.currentframe()))+'/EPFiles/Materials/Materials.data'
epwpath = os.path.dirname(inspect.getfile(inspect.currentframe()))+'/EPFiles/Weather/'
matpath = sys.path[0]+'/EPFiles/Materials/Materials.data'
epwpath = sys.path[0]+'/EPFiles/Weather/'
weatherlist = [((filename, os.path.basename(filename).strip('.epw').split(".")[0], 'Weather Location')) for filename in glob.glob(epwpath+"/*.epw")]


bpy.ops.node.new_node_tree(type='ViN', name ="VI-Suite Node Tree")

def register():
    vinode_categories = [
        # identifier, label, items list
        ViNodeCategory("Analysis", "Analysis Node", items=[
            NodeItem("ViNode", label="VI-Suite analysis node")
            ]),]
    bpy.utils.register_module(__name__)

    