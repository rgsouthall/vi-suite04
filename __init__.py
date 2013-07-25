bl_info = {
    "name": "VI-Suite",
    "author": "Ryan Southall",
    "version": (0, 1, 0),
    "blender": (2, 6, 7),
    "api":"",
    "location": "3D View > Properties Panel",
    "description": "Radiance/EnergyPlus exporter and results visualiser",
    "warning": "This is a beta script. Some functionality is buggy",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

if "bpy" in locals():
    import imp
    imp.reload(visuite_ui)
#else:
#    from .io_visuite_dev import visuite_ui 

import sys, os, platform, inspect, glob, boy

if str(sys.platform) == 'darwin':
    if platform.architecture() == "64bit":
        os.environ["PATH"] = os.environ["PATH"] + ":/usr/local/radiance/bin:"+sys.path[0]+"/io_visuite/osx/64:/Applications/EnergyPlus-8-0-0/bin"
    else:
         os.environ["PATH"] = os.environ["PATH"] + ":/usr/local/radiance/bin:"+sys.path[0]+"/io_visuite/osx:/Applications/EnergyPlus-8-0-0/bin"
    os.environ["RAYPATH"] = "/usr/local/radiance/lib:"+sys.path[0]+"/io_visuite/lib"

elif str(sys.platform) == 'win32':
    if os.path.isdir(r"C:\Program Files (x86)\Radiance"):
        os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files (x86)\Radiance\bin;"+sys.path[0]+"\io_visuite\windows;C:\EnergyPlusV8-0-0" 
        os.environ["RAYPATH"] = r"C:\Program Files (x86)\Radiance\lib;"+sys.path[0]+"\io_visuite\lib"
    elif os.path.isdir(r"C:\Program Files\Radiance"):
        os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files\Radiance\bin;"+sys.path[0]+"\io_visuite\windows;C:\EnergyPlusV8-0-0" 
        os.environ["RAYPATH"] = "C:\Program Files\Radiance\lib;"+sys.path[0]+"\io_visuite\lib"
    else:
        print("Cannot find a valid Radiance directory. Please check that you have Radiance installed in either C:\Program Files(x86) (64bit windows) \
or C:\Program Files (32bit windows)")

matpath = os.path.dirname(inspect.getfile(inspect.currentframe()))+'/EPFiles/Materials/Materials.data'
epwpath = os.path.dirname(inspect.getfile(inspect.currentframe()))+'/EPFiles/Weather/'
matpath = sys.path[0]+'/EPFiles/Materials/Materials.data'
epwpath = sys.path[0]+'/EPFiles/Weather/'
weatherlist = [((filename, os.path.basename(filename).strip('.epw').split(".")[0], 'Weather Location')) for filename in glob.glob(epwpath+"/*.epw")]

print(epwpath,weatherlist)

def register():
    Scene = bpy.types.Scene
    Scene.visuite_analysis = EnumProperty(
            items=[(0, "Lighting", "Static geometry export"),
                   (1, "Thermal", "Static geometry export"),
                   (2, "Combined", "Static geometry export"),
                   (3, "Wind Visualisation", "Dynamic geometry export"),
                   (4, "Solar Visualisation", "Dynamic geometry export"),
                   ],
            name="",
            description="Specify the type of analysis to be conducted",
            default=0)
    