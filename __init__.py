bl_info = {
    "name": "VI-Suite Test",
    "author": "Ryan Southall",
    "version": (0, 2, 0),
    "blender": (2, 7, 1),
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
    imp.reload(vi_func)
    imp.reload(envi_mat)
else:
    from .vi_node import vinode_categories, envinode_categories
    from .envi_mat import envi_materials, envi_constructions
    from .vi_func import iprop, bprop, eprop, fprop, sprop, fvprop, sunpath1
    from .vi_operators import *
    from .vi_ui import *

import sys, os, platform, inspect, bpy, nodeitems_utils

epversion = "8-1-0"
addonpath = os.path.dirname(inspect.getfile(inspect.currentframe()))
matpath, epwpath, envi_mats, envi_cons, conlayers  = addonpath+'/EPFiles/Materials/Materials.data', addonpath+'/EPFiles/Weather/', envi_materials(), envi_constructions(), 5

if str(sys.platform) == 'darwin':
    if not hasattr(os.environ, 'RAYPATH'):
        os.environ["PATH"] = os.environ["PATH"] + (":/usr/local/radiance/bin:{}/osx:/Applications/EnergyPlus-{}/bin".format(addonpath, epversion), ":/usr/local/radiance/bin:{}/osx/64:/Applications/EnergyPlus-{}/bin".format(addonpath, epversion))[platform.architecture() == "64bit"] 
        os.environ["RAYPATH"] = "/usr/local/radiance/lib:{}/lib".format(addonpath)

if str(sys.platform) == 'linux':
    if not hasattr(os.environ, 'RAYPATH'):
        raddir =  '/usr/share/radiance' if os.path.isdir('/usr/share/radiance') else '/usr/local/radiance'
        os.environ["PATH"] = os.environ["PATH"] + ":{}/bin:{}/linux:/usr/local/EnergyPlus-{}".format(raddir, addonpath, epversion)
        os.environ["RAYPATH"] = "{}/lib:{}/lib".format(raddir, addonpath)

elif str(sys.platform) == 'win32':
    if not hasattr(os.environ, 'RAYPATH'):
        if os.path.isdir(r"C:\Program Files (x86)\Radiance"):
            os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files (x86)\Radiance\bin;{}\windows;C:\EnergyPlusV{}".format(addonpath,epversion)
            os.environ["RAYPATH"] = r"C:\Program Files (x86)\Radiance\lib;{}\lib".format(addonpath)
        elif os.path.isdir(r"C:\Program Files\Radiance"):
            os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files\Radiance\bin;{}\windows;C:\EnergyPlusV{}".format(addonpath, epversion)
            os.environ["RAYPATH"] = "C:\Program Files\Radiance\lib;{}\lib".format(addonpath)
        else:
            print("Cannot find a valid Radiance directory. Please check that you have Radiance installed in either C:\Program Files(x86) (64bit windows) \
or C:\Program Files (32bit windows)")

def matfunc(i):
    matfuncdict = {'0': envi_mats.brick_dat.keys(), '1': envi_mats.stone_dat.keys(), '2': envi_mats.metal_dat.keys(), '3': envi_mats.wood_dat.keys(), '4': envi_mats.gas_dat.keys(),
                   '5': envi_mats.glass_dat.keys(), '6': envi_mats.concrete_dat.keys(), '7': envi_mats.insulation_dat.keys(), '8': envi_mats.wgas_dat.keys(), '9': envi_mats.cladding_dat.keys()}
    return [((mat, mat, 'Contruction type')) for mat in list(matfuncdict[str(i)])]

def confunc(i):
    confuncdict = {'0': envi_cons.wall_con.keys(), '1': envi_cons.floor_con.keys(), '2': envi_cons.roof_con.keys(), 
    '3': envi_cons.door_con.keys(), '4': envi_cons.glaze_con.keys()}
    return [((con, con, 'Contruction type')) for con in list(confuncdict[str(i)])]

(bricklist, stonelist, metallist, woodlist, gaslist, glasslist, concretelist, insullist, wgaslist, claddinglist) = [matfunc(i) for i in range(10)]
(wallconlist, floorconlist, roofconlist, doorconlist, glazeconlist) = [confunc(i) for i in range(5)]

def eupdate(self, context):
    inv = 0        
    for frame in range(context.scene.frame_start, context.scene.frame_end + 1):
        for o in [obj for obj in bpy.data.objects if obj.lires == 1]:
            if str(frame) in o['omax'].keys():
                maxo, mino = max(o['omax'].values()), min(o['omin'].values())
                if len(o['cverts']) == 0:
                    for i, fli in enumerate([(face, face.loop_indices) for face in o.data.polygons if face.select == True]):
                        for li in fli[1]:
                            vi = o.data.loops[li].vertex_index
                            o.data.shape_keys.key_blocks[str(frame)].data[vi].co = o.data.shape_keys.key_blocks['Basis'].data[vi].co + context.scene.vi_disp_3dlevel * (abs(inv - (o['oreslist'][str(frame)][i]-mino)/(maxo - mino)) * fli[0].normal)
                for vn, v in enumerate(o['cverts']):
                    o.data.shape_keys.key_blocks[str(frame)].data[v].co = o.data.shape_keys.key_blocks['Basis'].data[v].co + context.scene.vi_disp_3dlevel * (abs(inv - (o['oreslist'][str(frame)][vn]-mino)/(maxo - mino)) * o.data.vertices[v].normal)
                o.data.update()

def register():
    bpy.utils.register_module(__name__)
    Object, Scene, Material = bpy.types.Object, bpy.types.Scene, bpy.types.Material

# LiVi object properties
    Object.livi_merr = bprop("LiVi simple mesh export", "Boolean for simple mesh export", False)
    Object.ies_name = sprop("", "IES File", 1024, "")
    Object.ies_strength = fprop("", "Strength of IES lamp", 0, 1, 1)
    Object.ies_unit = eprop([("m", "Meters", ""), ("c", "Centimeters", ""), ("f", "Feet", ""), ("i", "Inches", "")], "", "Specify the IES file measurement unit", "m")
    Object.ies_colour = fvprop(3, "IES Colour",'IES Colour', [1.0, 1.0, 1.0], 'COLOR', 0, 1)
    (Object.licalc, Object.lires, Object.limerr, Object.manip, Object.lila) = [bprop("", "", False)] * 5

# EnVi zone definitions
    Object.envi_type = eprop([("0", "None", "None"), ("1", "Thermal", "Thermal Zone"), ("2", "Shading", "Shading Object")], "EnVi object type", "Specify the EnVi object type", "0")
    
# EnVi HVAC Template definitions
    Object.envi_hvact = bprop("Template:", "", False)
    Object.envi_hvacht = fprop("", "Heating temperature:", 1, 99, 50)
    Object.envi_hvacct = fprop("", "Cooling temperature:", -10, 20, 13)
    Object.envi_hvachlt = eprop([('0', 'LimitFlowRate', 'LimitFlowRate'), ('1', 'LimitCapacity', 'LimitCapacity'), ('2', 'LimitFlowRateAndCapacity', 'LimitFlowRateAndCapacity'), ('3', 'NoLimit', 'NoLimit'), ('4', 'None', 'No heating')], '', "Heating limit type", '4')    
    Object.envi_hvachaf = fprop("", "Heating air flow rate", 0, 60, 1)
    Object.envi_hvacshc = fprop("", "Sensible heating capacity", 0, 10000, 1000)
    Object.envi_hvacclt = eprop([('0', 'LimitFlowRate', 'LimitFlowRate'), ('1', 'LimitCapacity', 'LimitCapacity'), ('2', 'LimitFlowRateAndCapacity', 'LimitFlowRateAndCapacity'), ('3', 'NoLimit', 'NoLimit'), ('4', 'None', 'No cooling')], '', "Cooling limit type", '4')
    Object.envi_hvaccaf = fprop("", "Heating air flow rate", 0, 60, 1)
    Object.envi_hvacscc = fprop("", "Sensible cooling capacity", 0, 10000, 1000)
    Object.envi_hvacoam = eprop([('0', 'None', 'None'), ('1', 'Flow/Zone', 'Flow/Zone'), ('2', 'Flow/Person', 'Flow/Person'), ('3', 'Flow/Area', 'Flow/Area'), ('4', 'Sum', 'Sum'), ('5', 'Maximum ', 'Maximum'), ('6', 'ACH/Detailed', 'ACH/Detailed')], '', "Cooling limit type", '2')
#    Object.envi_hvacof = fprop("", "Outdoor air flow rate", 0, 10, 0.008)
    Object.envi_hvacfrp = fprop("", "Flow rate per person", 0, 1, 0.008)
    Object.envi_hvacfrzfa = fprop("", "Flow rate per zone area", 0, 1, 0.008)
    Object.envi_hvacfrz = fprop("", "Flow rate per zone", 0, 100, 0.1)
    Object.envi_hvacfach = fprop("", "ACH", 0, 10, 1)
# Heating defintions
    Object.envi_heat = bprop("Heating", 'Turn on zone heating', 0)
    Object.envi_htsp = iprop(u'\u00b0'+"C", "Temperature", 0, 50, 20)
    Object.envi_htspsched = bprop("Schedule", "Create a thermostat level schedule", False)
    (Object.htspu1, Object.htspu2, Object.htspu3, Object.htspu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for each day, space separated for each time value pair)")] * 4
    (Object.htspf1, Object.htspf2, Object.htspf3, Object.htspf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.htspt1, Object.htspt2, Object.htspt3, Object.htspt4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
# Cooling definitions
    Object.envi_cool = bprop("Cooling", "Turn on zone cooling", 0)
    Object.envi_ctsp = iprop(u'\u00b0'+"C", "Temperature", 0, 50, 20)
    Object.envi_ctspsched = bprop("Schedule", "Create a thermostat level schedule", False)
    (Object.ctspu1, Object.ctspu2, Object.ctspu3, Object.ctspu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for each day, space separated for each time value pair)")] * 4
    (Object.ctspf1, Object.ctspf2, Object.ctspf3, Object.ctspf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.ctspt1, Object.ctspt2, Object.ctspt3, Object.ctspt4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
#Occupancy definitions
    Object.envi_occsched = bprop("Schedule", "Create an occupancy level schedule", False)
    (Object.occu1, Object.occu2, Object.occu3, Object.occu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for each day, space separated for each time value pair)")] * 4
    (Object.occf1, Object.occf2, Object.occf3, Object.occf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.occt1, Object.occt2, Object.occt3, Object.occt4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_occwatts = iprop("W/p", "Watts per person", 1, 800, 90)
    Object.envi_asched = bprop("Schedule", "Create an activity level schedule", False)
    (Object.aoccu1, Object.aoccu2, Object.aoccu3, Object.aoccu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for each day, space separated for each time value pair)")] * 4
    (Object.aoccf1, Object.aoccf2, Object.aoccf3, Object.aoccf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.aocct1, Object.aocct2, Object.aocct3, Object.aocct4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_weff = fprop("Efficiency", "Work efficiency", 0, 1, 0.0)
    Object.envi_wsched = bprop("Schedule", "Create a work efficiency schedule", False)
    (Object.woccu1, Object.woccu2, Object.woccu3, Object.woccu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for each day, space separated for each time value pair)")] * 4
    (Object.woccf1, Object.woccf2, Object.woccf3, Object.woccf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.wocct1, Object.wocct2, Object.wocct3, Object.wocct4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_airv = fprop("Air velocity", "Average air velocity", 0, 1, 0.1)
    Object.envi_avsched = bprop("Schedule", "Create an air velocity schedule", False)
    (Object.avoccu1, Object.avoccu2, Object.avoccu3, Object.avoccu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for each day, space separated for each time value pair)")] * 4
    (Object.avoccf1, Object.avoccf2, Object.avoccf3, Object.avoccf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.avocct1, Object.avocct2, Object.avocct3, Object.avocct4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_cloth = fprop("Clothing", "Clothing level", 0, 10, 0.5)
    Object.envi_clsched = bprop("Schedule", "Create an clothing level schedule", False)
    (Object.coccu1, Object.coccu2, Object.coccu3, Object.coccu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for each day, space separated for each time value pair)")] * 4
    (Object.coccf1, Object.coccf2, Object.coccf3, Object.coccf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.cocct1, Object.cocct2, Object.cocct3, Object.cocct4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_occtype = eprop([("0", "None", "No occupancy"),("1", "Occupants", "Actual number of people"), ("2", "Person/m"+ u'\u00b2', "Number of people per squared metre floor area"),
                                              ("3", "m"+ u'\u00b2'+"/Person", "Floor area per person")], "", "The type of zone occupancy specification", "0")
    Object.envi_occsmax = fprop("Max", "Maximum level of occupancy that will occur in this schedule", 1, 500, 1)
    Object.envi_comfort = bprop("Comfort", "Enable comfort calculations for this space", False)
    Object.envi_co2 = bprop("C02", "Enable CO2 concentration calculations", False)
    
# Infiltration definitions
    Object.envi_inftype = eprop([("0", "None", "No infiltration"), ("1", 'Flow/Zone', "Absolute flow rate in m{}/s".format(u'\u00b3')), ("2", "Flow/Area", 'Flow in m{}/s per m{} floor area'.format(u'\u00b3', u'\u00b2')), 
                                 ("3", "Flow/ExteriorArea", 'Flow in m{}/s per m{} external surface area'.format(u'\u00b3', u'\u00b2')), ("4", "Flow/ExteriorWallArea", 'Flow in m{}/s per m{} external wall surface area'.format(u'\u00b3', u'\u00b2')), 
                                 ("4", "ACH", "ACH flow rate")], "", "The type of zone infiltration specification", "0")
    Object.envi_inflevel = fprop("Level", "Level of Infiltration", 0, 500, 0.001)
    Object.envi_infsched = bprop("Schedule", "Create an infiltration schedule", False)
    (Object.infu1, Object.infu2, Object.infu3, Object.infu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for each day, space separated for each time value pair)")] * 4
    (Object.inff1, Object.inff2, Object.inff3, Object.inff4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.inft1, Object.inft2, Object.inft3, Object.inft4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_occinftype = eprop([("0", "None", "No infiltration"), ("1", 'Flow/Zone', "Absolute flow rate in m{}/s".format(u'\u00b3')), ("2", "Flow/Area", 'Flow in m{}/s per m{} floor area'.format(u'\u00b3', u'\u00b2')), 
                                 ("3", "Flow/ExteriorArea", 'Flow in m{}/s per m{} external surface area'.format(u'\u00b3', u'\u00b2')), ("4", "Flow/ExteriorWallArea", 'Flow in m{}/s per m{} external wall surface area'.format(u'\u00b3', u'\u00b2')), 
                                 ("5", "ACH", "ACH flow rate"), ("6", "l/s/p", 'Litres per second per person')], "", "The type of zone infiltration specification", "0")

# LiVi material definitions
    Material.radmat = vi_func.radmat
    Material.radmatdict = {'0': ['radcolour', 0, 'radrough', 'radspec'], '1': ['radcolour'], '2': ['radcolour', 0, 'ior'], '3': ['radcolour', 0, 'radspec', 'radrough', 0, 'radtrans',  'radtranspec'], '4': ['radcolour'], '5': ['radcolour'], '6': ['radcolour', 0, 'radrough', 'radspec'], '7': []}

    radtypes = [('0', 'Plastic', 'Plastic Radiance material'), ('1', 'Glass', 'Glass Radiance material'), ('2', 'Dielectric', 'Dialectric Radiance material'),
                ('3', 'Translucent', 'Translucent Radiance material'), ('4', 'Mirror', 'Mirror Radiance material'), ('5', 'Light', 'Emission Radiance material'),
                ('6', 'Metal', 'Metal Radiance material'), ('7', 'Anti-matter', 'Antimatter Radiance material')]
    Material.radmatmenu = eprop(radtypes, "", "Type of Radiance material", '0')
    Material.radcolour = fvprop(3, "Material Colour",'Material Colour', [1.0, 1.0, 1.0], 'COLOR', 0, 1)
    Material.radrough = fprop("Roughness", "Material roughness", 0, 1, 0.1)
    Material.radspec = fprop("Specularity", "Material specularity", 0, 1, 0.1)
#    Material.radspec = fprop("Transmissivity", "Material specularity", 0, 1, 0.1)
    Material.radtrans = fprop("Specular trans.", "Material transmissivity", 0, 1, 0.1)
    Material.radtranspec  = fprop("Specularity", "Material specular transmission", 0, 1, 0.1)
    Material.radior  = fprop("IOR", "Material index of refractionn", 0, 5, 1.5)
    Material.vi_shadow = bprop("VI Shadow", "Flag to signify whether the material represents a VI Shadow sensing surface", False)
    Material.livi_sense = bprop("LiVi Sensor", "Flag to signify whether the material represents a LiVi sensing surface", False)
    Material.livi_compliance = bprop("LiVi Compliance Surface", "Flag to siginify whether the material represents a LiVi compliance surface", False)
    Material.gl_roof = bprop("Glazed Roof", "Flag to siginify whether the communal area has a glazed roof", False)
    hspacetype = [('0', 'Public/Staff', 'Public/Staff area'), ('1', 'Patient', 'Patient area')]
    rspacetype = [('0', "Kitchen", "Kitchen space"), ('1', "Living/Dining/Study", "Living/Dining/Study area"), ('2', "Communal", "Non-residential or communal area")]
    respacetype = [('0', "Sales", "Sales space"), ('1', "Occupied", "Occupied space")]
    Material.hspacemenu = eprop(hspacetype, "", "Type of healthcare space", '0')
    Material.brspacemenu = eprop(rspacetype, "", "Type of residential space", '0')
    Material.crspacemenu = eprop(rspacetype[:2], "", "Type of residential space", '0')
    Material.respacemenu = eprop(respacetype, "", "Type of retail space", '0')

# EnVi material definitions
    Material.envi_con_type = eprop([("Wall", "Wall", "Wall construction"),("Floor", "Floor", "Floor construction"),("Roof", "Roof", "Roof construction"),("Window", "Window", "Window construction"), ("Door", "Door", "Door construction"),
                    ("Shading", "Shading", "Shading material"),("Aperture", "Aperture", "Airflow Aperture"),("None", "None", "Surface to be ignored")], "", "Specify the construction type", "None")
    Material.envi_boundary = bprop("", "Flag to siginify whether the material represents a zone boundary", False)
    Material.envi_afsurface = bprop("", "Flag to siginify whether the material represents an airflow surface", False)
    Material.envi_thermalmass = bprop("", "Flag to siginify whether the material represents thermal mass", False)
    Material.envi_aperture = eprop([("0", "External", "External facade airflow component", 0), ("1", "Internal", "Zone boundary airflow component", 1),], "", "Position of the airflow component", "0")
    Material.envi_con_makeup = eprop([("0", "Pre-set", "Construction pre-set"),("1", "Layers", "Custom layers"),("2", "Dummy", "Adiabatic")], "", "Pre-set construction of custom layers", "0")
    Material.envi_layero = eprop([("0", "None", "Not present"), ("1", "Database", "Select from databse"), ("2", "Custom", "Define custom material properties")], "", "Composition of the outer layer", "0")
    Material.envi_layerott = Material.envi_layer1tt = Material.envi_layer2tt = Material.envi_layer3tt = Material.envi_layer4tt = eprop(
                    [("0", "Glass", "Choose a material from the glass database"),("1", "Gas", "Choose a material from the gas database")], "", "Composition of the outer layer", "0")
    Material.envi_layeroto = Material.envi_layer1to = Material.envi_layer2to = Material.envi_layer3to = Material.envi_layer4to = eprop(
            [("0", "Brick", "Choose a material from the brick database"),("1", "Cladding", "Choose a material from the cladding database"), ("2", "Concrete", "Choose a material from the concrete database"),("3", "Metal", "Choose a material from the metal database"),
                   ("4", "Stone", "Choose a material from the stone database"),("5", "Wood", "Choose a material from the wood database"),
                   ("6", "Gas", "Choose a material from the gas database"),("7", "Insulation", "Choose a material from the insulation database")],"","Composition of the outer layer","0")
    (Material.envi_layer1, Material.envi_layer2, Material.envi_layer3, Material.envi_layer4) = \
    [eprop([("0", "None", "Not present"),("1", "Database", "Select from databse"), ("2", "Custom", "Define custom material properties")], "", "Composition of the next layer", "0")] * (conlayers - 1)
    Material.envi_export = bprop("Material Export", "Flag to tell EnVi to export this material", False)
    Material.envi_export_wallconlist = eprop(wallconlist, "Wall Constructions", "", wallconlist[0][0])
    Material.envi_export_floorconlist = eprop(floorconlist, "Floor Constructions",  "", floorconlist[0][0])
    Material.envi_export_roofconlist = eprop(roofconlist, "Roof Constructions",  "", roofconlist[0][0])
    Material.envi_export_doorconlist = eprop(doorconlist, "Door Constructions",  "", doorconlist[0][0])
    Material.envi_export_glazeconlist = eprop(glazeconlist, "Window Constructions",  "", glazeconlist[0][0])
    (Material.envi_export_bricklist_lo, Material.envi_export_bricklist_l1, Material.envi_export_bricklist_l2, Material.envi_export_bricklist_l3, Material.envi_export_bricklist_l4) = \
    [eprop(bricklist, "", "", bricklist[0][0])] * conlayers
    (Material.envi_export_claddinglist_lo, Material.envi_export_claddinglist_l1, Material.envi_export_claddinglist_l2, Material.envi_export_claddinglist_l3, Material.envi_export_claddinglist_l4) = \
    [eprop(claddinglist, "", "", claddinglist[0][0])] * conlayers
    (Material.envi_export_stonelist_lo, Material.envi_export_stonelist_l1, Material.envi_export_stonelist_l2, Material.envi_export_stonelist_l3, Material.envi_export_stonelist_l4) =\
    [eprop(stonelist, "", "", stonelist[0][0])] * conlayers
    (Material.envi_export_woodlist_lo, Material.envi_export_woodlist_l1, Material.envi_export_woodlist_l2, Material.envi_export_woodlist_l3, Material.envi_export_woodlist_l4) = \
    [eprop(woodlist, "", "", woodlist[0][0])] * conlayers
    (Material.envi_export_metallist_lo, Material.envi_export_metallist_l1, Material.envi_export_metallist_l2, Material.envi_export_metallist_l3, Material.envi_export_metallist_l4) = \
    [eprop(metallist, "", "", metallist[0][0])] * conlayers
    (Material.envi_export_gaslist_lo, Material.envi_export_gaslist_l1, Material.envi_export_gaslist_l2, Material.envi_export_gaslist_l3, Material.envi_export_gaslist_l4) = \
    [eprop(gaslist, "", "", gaslist[0][0])] * conlayers
    (Material.envi_export_glasslist_lo, Material.envi_export_glasslist_l1, Material.envi_export_glasslist_l2, Material.envi_export_glasslist_l3, Material.envi_export_glasslist_l4) = \
    [eprop(glasslist, "", "", glasslist[0][0])] * conlayers
    (Material.envi_export_concretelist_lo, Material.envi_export_concretelist_l1, Material.envi_export_concretelist_l2, Material.envi_export_concretelist_l3, Material.envi_export_concretelist_l4) = \
    [eprop(concretelist, "", "", concretelist[0][0])] * conlayers
    (Material.envi_export_insulationlist_lo, Material.envi_export_insulationlist_l1, Material.envi_export_insulationlist_l2, Material.envi_export_insulationlist_l3, Material.envi_export_insulationlist_l4) = \
    [eprop(insullist, "", "", insullist[0][0])] * conlayers
    (Material.envi_export_wgaslist_lo, Material.envi_export_wgaslist_l1, Material.envi_export_wgaslist_l2, Material.envi_export_wgaslist_l3, Material.envi_export_wgaslist_l4) = \
    [eprop(wgaslist, "", "", wgaslist[0][0])] * conlayers
    (Material.envi_export_lo_name, Material.envi_export_l1_name, Material.envi_export_l2_name, Material.envi_export_l3_name, Material.envi_export_l4_name) = \
    [sprop("", "Layer name", 0, "")] * conlayers    
    (Material.envi_export_lo_tc, Material.envi_export_l1_tc, Material.envi_export_l2_tc, Material.envi_export_l3_tc, Material.envi_export_l4_tc) = \
    [fprop("Conductivity", "Thermal Conductivity", 0, 10, 0.5)] * conlayers
    (Material.envi_export_lo_rough, Material.envi_export_l1_rough, Material.envi_export_l2_rough, Material.envi_export_l3_rough, Material.envi_export_l1_rough) = \
    [eprop([("VeryRough", "VeryRough", "Roughness"), ("Rough", "Rough", "Roughness"), ("MediumRough", "MediumRough", "Roughness"),
                                                        ("MediumSmooth", "MediumSmooth", "Roughness"), ("Smooth", "Smooth", "Roughness"), ("VerySmooth", "VerySmooth", "Roughness")],
                                                        "Material surface roughness", "specify the material rughness for convection calculations", "Rough")] * conlayers

    (Material.envi_export_lo_rho, Material.envi_export_l1_rho, Material.envi_export_l2_rho, Material.envi_export_l3_rho, Material.envi_export_l4_rho) = \
    [fprop("Density", "Density (kg/m3)", 0, 10000, 1000)] * conlayers
    (Material.envi_export_lo_shc, Material.envi_export_l1_shc, Material.envi_export_l2_shc, Material.envi_export_l3_shc, Material.envi_export_l4_shc) = \
    [fprop("SHC", "Specific Heat Capacity (J/kgK)", 0, 10000, 1000)] * conlayers
    (Material.envi_export_lo_thi, Material.envi_export_l1_thi, Material.envi_export_l2_thi, Material.envi_export_l3_thi, Material.envi_export_l4_thi) = \
    [fprop("Thickness", "Thickness (mm)", 0, 10000, 100)] * conlayers
    (Material.envi_export_lo_tab, Material.envi_export_l1_tab, Material.envi_export_l2_tab, Material.envi_export_l3_tab, Material.envi_export_l4_tab) = \
    [fprop("TA", "Thermal Absorptance", 0, 1, 0.8)] * conlayers
    (Material.envi_export_lo_sab, Material.envi_export_l1_sab, Material.envi_export_l2_sab, Material.envi_export_l3_sab, Material.envi_export_l4_sab) = \
    [fprop("SA", "Solar Absorptance", 0, 1, 0.6)] * conlayers
    (Material.envi_export_lo_vab, Material.envi_export_l1_vab, Material.envi_export_l2_vab, Material.envi_export_l3_vab, Material.envi_export_l4_vab) = \
    [fprop("VA", "Visible Absorptance", 0, 1, 0.6)] * conlayers
    (Material.envi_export_lo_odt, Material.envi_export_l1_odt, Material.envi_export_l2_odt, Material.envi_export_l3_odt, Material.envi_export_l4_odt) = \
    [eprop([("SpectralAverage", "SpectralAverage", "Optical Data Type")], "", "Optical Data Type", "SpectralAverage")] * conlayers
    (Material.envi_export_lo_sds, Material.envi_export_l1_sds, Material.envi_export_l2_sds, Material.envi_export_l3_sds, Material.envi_export_l4_sds) = \
    [eprop([("0", "", "Window Glass Spectral Data Set Name")], "", "Window Glass Spectral Data Set Name", "0")] * conlayers
    (Material.envi_export_lo_stn, Material.envi_export_l1_stn, Material.envi_export_l2_stn, Material.envi_export_l3_stn, Material.envi_export_l4_stn) = \
    [fprop("STN", "Solar Transmittance at Normal Incidence", 0, 1, 0.9)] * conlayers
    (Material.envi_export_lo_fsn, Material.envi_export_l1_fsn, Material.envi_export_l2_fsn, Material.envi_export_l3_fsn, Material.envi_export_l4_fsn) = \
    [fprop("FSN", "Front Side Solar Reflectance at Normal Incidence", 0, 1, 0.075)] * conlayers
    (Material.envi_export_lo_bsn, Material.envi_export_l1_bsn, Material.envi_export_l2_bsn, Material.envi_export_l3_bsn, Material.envi_export_l4_bsn) = \
    [fprop("BSN", "Back Side Solar Reflectance at Normal Incidence", 0, 1, 0.075)] * conlayers
    (Material.envi_export_lo_vtn, Material.envi_export_l1_vtn, Material.envi_export_l2_vtn, Material.envi_export_l3_vtn, Material.envi_export_l4_vtn) = \
    [fprop("VTN", "Visible Transmittance at Normal Incidence", 0, 1, 0.9)] * conlayers
    (Material.envi_export_lo_fvrn, Material.envi_export_l1_fvrn, Material.envi_export_l2_fvrn, Material.envi_export_l3_fvrn, Material.envi_export_l4_fvrn) = \
    [fprop("FVRN", "Front Side Visible Reflectance at Normal Incidence", 0, 1, 0.08)] * conlayers
    (Material.envi_export_lo_bvrn, Material.envi_export_l1_bvrn, Material.envi_export_l2_bvrn, Material.envi_export_l3_bvrn, Material.envi_export_l4_bvrn) = \
    [fprop("BVRN", "Back Side Visible Reflectance at Normal Incidence", 0, 1, 0.08)] * conlayers
    (Material.envi_export_lo_itn, Material.envi_export_l1_itn, Material.envi_export_l2_itn, Material.envi_export_l3_itn, Material.envi_export_l4_itn) = \
    [fprop("ITN", "Infrared Transmittance at Normal Incidence", 0, 1, 0.0)] * conlayers
    (Material.envi_export_lo_fie, Material.envi_export_l1_fie, Material.envi_export_l2_fie, Material.envi_export_l3_fie, Material.envi_export_l4_fie) = \
    [fprop("FIE", "Front Side Infrared Hemispherical Emissivity", 0, 1, 0.84)] * conlayers
    (Material.envi_export_lo_bie, Material.envi_export_l1_bie, Material.envi_export_l2_bie, Material.envi_export_l3_bie, Material.envi_export_l4_bie) = \
    [fprop("BIE", "Back Side Infrared Hemispherical Emissivity", 0, 1, 0.84)] * conlayers
    (Material.envi_export_lo_sdiff, Material.envi_export_l1_sdiff, Material.envi_export_l2_sdiff, Material.envi_export_l3_sdiff, Material.envi_export_l4_sdiff) = \
    [bprop("", "", 0)] * conlayers
    Material.envi_shad_att = bprop("Attached", "Flag to specify shading attached to the building",False)

    # Scene parameters
    Scene.fs = iprop("Frame start", "Starting frame",0, 1000, 0)
    (Scene.fe, Scene.gfe, Scene.cfe) = [iprop("Frame start", "End frame",0, 50000, 0)] * 3
    Scene.vipath = sprop("VI Path", "Path to files included with the VI-Suite ", 1024, addonpath)
    Scene.solday = bpy.props.IntProperty(name = "", description = "Day of year", min = 1, max = 365, default = 1, update=sunpath1)
    Scene.solhour = bpy.props.FloatProperty(name = "", description = "Time of day", min = 0, max = 24, default = 12, update=sunpath1)
    Scene.soldistance = bpy.props.IntProperty(name = "", description = "Sun path scale", min = 1, max = 5000, default = 100, update=sunpath1)
    (Scene.hourdisp, Scene.spupdate) = [bprop("", "",0)] * 2
#    Scene.latitude = bpy.props.FloatProperty(name="Latitude", description="Site Latitude", min=-90, max=90, default=52)
#    Scene.longitude = bpy.props.FloatProperty(name="Longitude", description="Site Longitude", min=-180, max=180, default=0)
    Scene.li_disp_panel = iprop("Display Panel", "Shows the Display Panel", -1, 2, 0)
    Scene.li_disp_count = iprop("", "", 0, 1000, 0)
    Scene.vi_disp_3d = bprop("VI 3D display", "Boolean for 3D results display",  False)
    Scene.vi_disp_3dlevel = bpy.props.FloatProperty(name = "", description = "Level of 3D result plane extrusion", min = 0, max = 500, default = 0, update = eupdate)
    Scene.ss_disp_panel = iprop("Display Panel", "Shows the Display Panel", -1, 2, 0)
    (Scene.lic_disp_panel, Scene.vi_display, Scene.sp_disp_panel, Scene.wr_disp_panel, Scene.ss_leg_display, Scene.en_disp_panel, Scene.li_compliance, Scene.vi_display_rp, Scene.vi_leg_display, 
     Scene.vi_display_sel_only, Scene.vi_display_vis_only) = [bprop("", "", False)] * 11
    Scene.vi_display_rp_fs = iprop("", "Point result font size", 4, 48, 9)
    Scene.vi_display_rp_fc = fvprop(4, "", "Font colour", [0.0, 0.0, 0.0, 1.0], 'COLOR', 0, 1)
    Scene.vi_display_rp_fsh = fvprop(4, "", "Font shadow", [0.0, 0.0, 0.0, 1.0], 'COLOR', 0, 1)
    Scene.vi_display_rp_off = fprop("", "Surface offset for number display", 0, 1, 0.001)
    Scene.li_projname = sprop("", "Name of the building project", 1024, '')
    Scene.li_assorg = sprop("", "Name of the assessing organisation", 1024, '')
    Scene.li_assind = sprop("", "Name of the assessing individual", 1024, '')
    Scene.li_jobno = sprop("", "Project job number", 1024, '')
    Scene.resnode = sprop("", "", 0, "")
    Scene.restree = sprop("", "", 0, "")   

    nodeitems_utils.register_node_categories("Vi Nodes", vinode_categories)
    nodeitems_utils.register_node_categories("EnVi Nodes", envinode_categories)

def unregister():
    bpy.utils.unregister_module(__name__)
    nodeitems_utils.unregister_node_categories("Vi Nodes")
    nodeitems_utils.unregister_node_categories("EnVi Nodes")

