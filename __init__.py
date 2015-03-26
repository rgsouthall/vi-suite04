bl_info = {
    "name": "VI-Suite v03",
    "author": "Ryan Southall",
    "version": (0, 3, 0),
    "blender": (2, 7, 3),
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
    from .vi_func import iprop, bprop, eprop, fprop, sprop, fvprop, sunpath1, fvmat, radmat, resnameunits
    from .vi_operators import *
    from .vi_ui import *

import sys, os, inspect, bpy, nodeitems_utils, bmesh, shutil
from numpy import array, digitize

epversion = "8-2-0"
addonpath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
matpath, epwpath, envi_mats, envi_cons, conlayers  = addonpath+'/EPFiles/Materials/Materials.data', addonpath+'/EPFiles/Weather/', envi_materials(), envi_constructions(), 5

rplatbdict = {'linux': ('/usr/share/radiance/bin', '/usr/local/radiance/bin'), 'win32': (r"C:\Program Files (x86)\Radiance\bin", r"C:\Program Files\Radiance\bin"), 'darwin': ['/usr/local/radiance/bin']}
rplatldict = {'linux': ('/usr/share/radiance/lib', '/usr/local/radiance/lib'), 'win32': (r"C:\Program Files (x86)\Radiance\lib", r"C:\Program Files\Radiance\lib"), 'darwin': ['/usr/local/radiance/lib']}
eplatbdict = {'linux': ('/usr/local/EnergyPlus-{}'.format(epversion)), 'win32': 'C:\EnergyPlusV{}'.format(epversion), 'darwin': '/Applications/EnergyPlus-{}'.format(epversion)}
platdict = {'linux': 'linux', 'win32': 'windows', 'darwin': 'osx'}
evsep = {'linux': ':', 'darwin': ':', 'win32': ';'}


if 'RAYPATH' not in os.environ:
    radldir = [d for d in rplatldict[str(sys.platform)] if os.path.isdir(d)]
    radbdir = [d for d in rplatbdict[str(sys.platform)] if os.path.isdir(d)]
    epdir = eplatbdict[str(sys.platform)] if os.path.isdir(eplatbdict[str(sys.platform)]) else os.path.join('{}'.format(addonpath), 'EPFiles', 'bin',  platdict[str(sys.platform)])
    if epdir == eplatbdict[str(sys.platform)] and os.path.isfile(os.path.join(eplatbdict[str(sys.platform)], 'Energy+.idd')):
        shutil.copyfile(os.path.join(eplatbdict[str(sys.platform)], 'Energy+.idd'), os.path.join('{}'.format(addonpath), 'EPFiles', 'Energy+.idd'))            
    if not radldir:
        radbdir, radldir = [os.path.join('{}'.format(addonpath), 'Radfiles', 'bin', platdict[str(sys.platform)])], [os.path.join('{}'.format(addonpath), 'Radfiles', 'lib')]
    os.environ["RAYPATH"] = '{0}{1}{2}'.format(radldir[0], evsep[str(sys.platform)], os.path.join(addonpath, 'lib'))        
    os.environ["PATH"] = os.environ["PATH"] + "{0}{1}{0}{2}".format(evsep[str(sys.platform)], radbdir[0], epdir)    
else:
    os.environ["RAYPATH"] += '{0}{1}'.format(evsep[str(sys.platform)], os.path.join(addonpath, 'lib'))

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
            maxo, mino = max(o['omax'].values()), min(o['omin'].values())
            bm = bmesh.new()
            bm.from_mesh(o.data)  
            bm.transform(o.matrix_world)
            if str(frame) in o['omax']:
                if bm.faces.layers.float.get('res{}'.format(frame)):
                    res = bm.faces.layers.float['res{}'.format(frame)] #if context.scene['cp'] == '0' else bm.verts.layers.float['res{}'.format(frame)]                
                    for f in [f for f in bm.faces if f.select]:
                        vplus = context.scene.vi_disp_3dlevel * (abs(inv - (f[res]-mino)/(maxo - mino)) * f.normal)
                        for v in f.verts:
                            o.data.shape_keys.key_blocks[str(frame)].data[v.index].co = o.data.shape_keys.key_blocks['Basis'].data[v.index].co + vplus
                elif bm.verts.layers.float.get('res{}'.format(frame)):
                    res = bm.verts.layers.float['res{}'.format(frame)]
                    for v in bm.verts:
                        o.data.shape_keys.key_blocks[str(frame)].data[v.index].co = o.data.shape_keys.key_blocks['Basis'].data[v.index].co + context.scene.vi_disp_3dlevel * (abs(inv - (v[res]-mino)/(maxo - mino)) * v.normal)
                o.data.update()
            bm.free()

def tupdate(self, context):
    for o in [o for o in context.scene.objects if o.type == 'MESH'  and 'lightarray' not in o.name and o.hide == False and o.layers[context.scene.active_layer] == True and o.get('lires')]:
        o.show_transparent = 1
    for mat in [bpy.data.materials['{}#{}'.format(('livi', 'shad')['Shadow' in context.scene.resnode], index)] for index in range(20)]:
        mat.use_transparency, mat.transparency_method, mat.alpha = 1, 'MASK', context.scene.vi_disp_trans
        
def wupdate(self, context):
    o = context.active_object
    if o and o.type == 'MESH':
        (o.show_wire, o.show_all_edges) = (1, 1) if context.scene.vi_disp_wire else (0, 0)
        
def legupdate(self, context):
    scene = context.scene
    for frame in range(scene.fs, scene.fe + 1):
        for o in [o for o in scene.objects if o.get('lires')]:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            livires = bm.faces.layers.float['res{}'.format(frame)] if bm.faces.layers.float.get('res{}'.format(frame)) else bm.verts.layers.float['res{}'.format(frame)]
            try:
                vals = array([(f[livires] - scene.vi_leg_min)/(scene.vi_leg_max - scene.vi_leg_min) for f in bm.faces]) if scene['liparams']['cp'] == '0' else \
            ([(sum([vert[livires] for vert in f.verts])/len(f.verts) - scene.vi_leg_min)/(scene.vi_leg_max - scene.vi_leg_min) for f in bm.faces])
            except:
                vals = array([0 for f in bm.faces])
            bm.free()
            bins = array([0.05*i for i in range(1, 20)])
            nmatis = digitize(vals, bins)
            for fi, f in enumerate(o.data.polygons):
                f.material_index = nmatis[fi]
                f.keyframe_insert('material_index', frame=frame)
    scene.frame_set(scene.frame_current)
            
def register():
    bpy.utils.register_module(__name__)
    Object, Scene, Material = bpy.types.Object, bpy.types.Scene, bpy.types.Material

# VI-Suite object definitions
    Object.vi_type = eprop([("0", "None", "Not a VI-Suite zone"), ("1", "EnVi Zone", "Designates an EnVi Thermal zone"), 
                            ("2", "CFD Domain", "Specifies an OpenFoam BlockMesh"), ("3", "CFD Geometry", "Specifies an OpenFoam geometry")], 
                            "", "Specify the type of VI-Suite zone", "0")

# LiVi object properties
    Object.livi_merr = bprop("LiVi simple mesh export", "Boolean for simple mesh export", False)
    Object.ies_name = sprop("", "IES File", 1024, "")
    Object.ies_strength = fprop("", "Strength of IES lamp", 0, 1, 1)
    Object.ies_unit = eprop([("m", "Meters", ""), ("c", "Centimeters", ""), ("f", "Feet", ""), ("i", "Inches", "")], "", "Specify the IES file measurement unit", "m")
    Object.ies_colour = fvprop(3, "IES Colour",'IES Colour', [1.0, 1.0, 1.0], 'COLOR', 0, 1)
    (Object.licalc, Object.lires, Object.limerr, Object.manip, Object.lila) = [bprop("", "", False)] * 5

# EnVi zone definitions
    Object.envi_type = eprop([("0", "Thermal", "Thermal Zone"), ("1", "Shading", "Shading Object")], "EnVi object type", "Specify the EnVi object type", "0")
    
# EnVi HVAC Template definitions
    Object.envi_hvacsched = bprop("", "Create a system level schedule", False)
    Object.envi_hvact = bprop("", "", False)
    Object.envi_hvacht = fprop("", "Heating temperature:", 1, 99, 50)
    Object.envi_hvacct = fprop("", "Cooling temperature:", -10, 20, 13)
    Object.envi_hvachlt = eprop([('0', 'LimitFlowRate', 'LimitFlowRate'), ('1', 'LimitCapacity', 'LimitCapacity'), ('2', 'LimitFlowRateAndCapacity', 'LimitFlowRateAndCapacity'), ('3', 'NoLimit', 'NoLimit'), ('4', 'None', 'No heating')], '', "Heating limit type", '4')    
    Object.envi_hvachaf = fprop("", "Heating air flow rate", 0, 60, 1)
    Object.envi_hvacshc = fprop("", "Sensible heating capacity", 0, 10000, 1000)
    Object.envi_hvacclt = eprop([('0', 'LimitFlowRate', 'LimitFlowRate'), ('1', 'LimitCapacity', 'LimitCapacity'), ('2', 'LimitFlowRateAndCapacity', 'LimitFlowRateAndCapacity'), ('3', 'NoLimit', 'NoLimit'), ('4', 'None', 'No cooling')], '', "Cooling limit type", '4')
    Object.envi_hvaccaf = fprop("", "Heating air flow rate", 0, 60, 1)
    Object.envi_hvacscc = fprop("", "Sensible cooling capacity", 0, 10000, 1000)
    Object.envi_hvacoam = eprop([('0', 'None', 'None'), ('1', 'Flow/Zone', 'Flow/Zone'), ('2', 'Flow/Person', 'Flow/Person'), ('3', 'Flow/Area', 'Flow/Area'), ('4', 'Sum', 'Sum'), ('5', 'Maximum ', 'Maximum'), ('6', 'ACH/Detailed', 'ACH/Detailed')], '', "Cooling limit type", '2')
    Object.envi_hvacfrp = fprop("", "Flow rate per person", 0, 1, 0.008)
    Object.envi_hvacfrzfa = fprop("", "Flow rate per zone area", 0, 1, 0.008)
    Object.envi_hvacfrz = fprop('m{}/s'.format(u'\u00b3'), "Flow rate per zone", 0, 100, 0.1)
    Object.envi_hvacfach = fprop("", "ACH", 0, 10, 1)
    (Object.hvacu1, Object.hvacu2, Object.hvacu3, Object.hvacu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.hvacf1, Object.hvacf2, Object.hvacf3, Object.hvacf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.hvact1, Object.hvact2, Object.hvact3, Object.hvact4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4

# Heating defintions
    Object.envi_heat = bprop("Heating", 'Turn on zone heating', 0)
    Object.envi_htsp = fprop(u'\u00b0'+"C", "Temperature", 0, 50, 20)
    Object.envi_htspsched = bprop("Schedule", "Create a thermostat level schedule", False)
    (Object.htspu1, Object.htspu2, Object.htspu3, Object.htspu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.htspf1, Object.htspf2, Object.htspf3, Object.htspf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.htspt1, Object.htspt2, Object.htspt3, Object.htspt4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
# Cooling definitions
    Object.envi_cool = bprop("Cooling", "Turn on zone cooling", 0)
    Object.envi_ctsp = fprop(u'\u00b0'+"C", "Temperature", 0, 50, 20)
    Object.envi_ctspsched = bprop("Schedule", "Create a thermostat level schedule", False)
    (Object.ctspu1, Object.ctspu2, Object.ctspu3, Object.ctspu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.ctspf1, Object.ctspf2, Object.ctspf3, Object.ctspf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.ctspt1, Object.ctspt2, Object.ctspt3, Object.ctspt4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
#Occupancy definitions
    Object.envi_occsched = bprop("Schedule", "Create an occupancy level schedule", False)
    (Object.occu1, Object.occu2, Object.occu3, Object.occu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.occf1, Object.occf2, Object.occf3, Object.occf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.occt1, Object.occt2, Object.occt3, Object.occt4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_occwatts = iprop("W/p", "Watts per person", 1, 800, 90)
    Object.envi_asched = bprop("Schedule", "Create an activity level schedule", False)
    (Object.aoccu1, Object.aoccu2, Object.aoccu3, Object.aoccu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.aoccf1, Object.aoccf2, Object.aoccf3, Object.aoccf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.aocct1, Object.aocct2, Object.aocct3, Object.aocct4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_weff = fprop("Efficiency", "Work efficiency", 0, 1, 0.0)
    Object.envi_wsched = bprop("Schedule", "Create a work efficiency schedule", False)
    (Object.woccu1, Object.woccu2, Object.woccu3, Object.woccu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.woccf1, Object.woccf2, Object.woccf3, Object.woccf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.wocct1, Object.wocct2, Object.wocct3, Object.wocct4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_airv = fprop("Air velocity", "Average air velocity", 0, 1, 0.1)
    Object.envi_avsched = bprop("Schedule", "Create an air velocity schedule", False)
    (Object.avoccu1, Object.avoccu2, Object.avoccu3, Object.avoccu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.avoccf1, Object.avoccf2, Object.avoccf3, Object.avoccf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.avocct1, Object.avocct2, Object.avocct3, Object.avocct4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_cloth = fprop("Clothing", "Clothing level", 0, 10, 0.5)
    Object.envi_clsched = bprop("Schedule", "Create an clothing level schedule", False)
    (Object.coccu1, Object.coccu2, Object.coccu3, Object.coccu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.coccf1, Object.coccf2, Object.coccf3, Object.coccf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.cocct1, Object.cocct2, Object.cocct3, Object.cocct4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_occtype = eprop([("0", "None", "No occupancy"),("1", "Occupants", "Actual number of people"), ("2", "Person/m"+ u'\u00b2', "Number of people per squared metre floor area"),
                                              ("3", "m"+ u'\u00b2'+"/Person", "Floor area per person")], "", "The type of zone occupancy specification", "0")
    Object.envi_occsmax = fprop("Max", "Maximum level of occupancy that will occur in this schedule", 1, 500, 1)
    Object.envi_comfort = bprop("Comfort", "Enable comfort calculations for this space", False)
    Object.envi_co2 = bprop("C02", "Enable CO2 concentration calculations", False)
    
# Equipment definitions
    Object.envi_equiptype = eprop([("0", "None", "No equipment"),("1", "EquipmentLevel", "Overall equpiment gains"), ("2", "Watts/Area", "Equipment gains per square metre floor area"),
                                              ("3", "Watts/Person", "Equipment gains per occupant")], "", "The type of zone equipment gain specification", "0")
    Object.envi_equipmax = fprop("Max", "Maximum level of equipment gain", 1, 50000, 1)

    Object.envi_equipsched = bprop("Schedule", "Create an equipment gains schedule", False)
    (Object.equipu1, Object.equipu2, Object.equipu3, Object.equipu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.equipf1, Object.equipf2, Object.equipf3, Object.equipf4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.equipt1, Object.equipt2, Object.equipt3, Object.equipt4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4

    
# Infiltration definitions
    Object.envi_inftype = eprop([("0", "None", "No infiltration"), ("1", 'Flow/Zone', "Absolute flow rate in m{}/s".format(u'\u00b3')), ("2", "Flow/Area", 'Flow in m{}/s per m{} floor area'.format(u'\u00b3', u'\u00b2')), 
                                 ("3", "Flow/ExteriorArea", 'Flow in m{}/s per m{} external surface area'.format(u'\u00b3', u'\u00b2')), ("4", "Flow/ExteriorWallArea", 'Flow in m{}/s per m{} external wall surface area'.format(u'\u00b3', u'\u00b2')), 
                                 ("4", "ACH", "ACH flow rate")], "", "The type of zone infiltration specification", "0")
    Object.envi_inflevel = fprop("Level", "Level of Infiltration", 0, 500, 0.001)
    Object.envi_infsched = bprop("Schedule", "Create an infiltration schedule", False)
    (Object.infu1, Object.infu2, Object.infu3, Object.infu4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for hour range, space separated for each time value pair)")] * 4
    (Object.inff1, Object.inff2, Object.inff3, Object.inff4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")] * 4
    (Object.inft1, Object.inft2, Object.inft3, Object.inft4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365)] * 4
    Object.envi_occinftype = eprop([("0", "None", "No infiltration"), ("1", 'Flow/Zone', "Absolute flow rate in m{}/s".format(u'\u00b3')), ("2", "Flow/Area", 'Flow in m{}/s per m{} floor area'.format(u'\u00b3', u'\u00b2')), 
                                 ("3", "Flow/ExteriorArea", 'Flow in m{}/s per m{} external surface area'.format(u'\u00b3', u'\u00b2')), ("4", "Flow/ExteriorWallArea", 'Flow in m{}/s per m{} external wall surface area'.format(u'\u00b3', u'\u00b2')), 
                                 ("5", "ACH", "ACH flow rate"), ("6", "l/s/p", 'Litres per second per person')], "", "The type of zone infiltration specification", "0")
# FloVi object definitions
              
# Vi_suite material definitions
    Material.mattype = eprop([("0", "Geometry", "Geometry"), ("1", 'LiVi sensor', "LiVi sensing material".format(u'\u00b3')), ("2", "Shadow sensor", 'Shadow sensing material'), ("3", "FloVi boundary", 'FloVi blockmesh boundary')], "", "VI-Suite material type", "0")
                                 
# LiVi material definitions
                                 
    Material.radmat = radmat
    Material.radmatdict = {'0': ['radcolour', 0, 'radrough', 'radspec'], '1': ['radcolour'], '2': ['radcolour', 0, 'radior'], '3': ['radcolour', 0, 'radspec', 'radrough', 0, 'radtrans',  'radtranspec'], '4': ['radcolour'], '5': ['radcolour', 0, 'radintensity'], '6': ['radcolour', 0, 'radrough', 'radspec'], '7': []}

    radtypes = [('0', 'Plastic', 'Plastic Radiance material'), ('1', 'Glass', 'Glass Radiance material'), ('2', 'Dielectric', 'Dialectric Radiance material'),
                ('3', 'Translucent', 'Translucent Radiance material'), ('4', 'Mirror', 'Mirror Radiance material'), ('5', 'Light', 'Emission Radiance material'),
                ('6', 'Metal', 'Metal Radiance material'), ('7', 'Anti-matter', 'Antimatter Radiance material')]
    Material.radmatmenu = eprop(radtypes, "", "Type of Radiance material", '0')
    Material.radcolour = fvprop(3, "Material Colour",'Material Colour', [1.0, 1.0, 1.0], 'COLOR', 0, 1)
    Material.radrough = fprop("Roughness", "Material roughness", 0, 1, 0.1)
    Material.radspec = fprop("Specularity", "Material specularity", 0, 1, 0.1)
    Material.radtrans = fprop("Transmission", "Material transmissivity", 0, 1, 0.1)
    Material.radtranspec  = fprop("Trans spec", "Material specular transmission", 0, 1, 0.1)
    Material.radior  = fprop("IOR", "Material index of refractionn", 0, 5, 1.5)
    Material.radintensity = fprop("Intensity", u"Material radiance (W/sr/m\u00b2)", 0, 100, 1)    
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
    (Material.envi_export_lo_rough, Material.envi_export_l1_rough, Material.envi_export_l2_rough, Material.envi_export_l3_rough, Material.envi_export_l4_rough) = \
    [eprop([("VeryRough", "VeryRough", "Roughness"), ("Rough", "Rough", "Roughness"), ("MediumRough", "MediumRough", "Roughness"),
                                                        ("MediumSmooth", "MediumSmooth", "Roughness"), ("Smooth", "Smooth", "Roughness"), ("VerySmooth", "VerySmooth", "Roughness")],
                                                        "Material surface roughness", "specify the material rughness for convection calculations", "Rough")] * conlayers

    (Material.envi_export_lo_rho, Material.envi_export_l1_rho, Material.envi_export_l2_rho, Material.envi_export_l3_rho, Material.envi_export_l4_rho) = \
    [fprop("Density", "Density (kg/m3)", 0, 10000, 1000)] * conlayers
    (Material.envi_export_lo_shc, Material.envi_export_l1_shc, Material.envi_export_l2_shc, Material.envi_export_l3_shc, Material.envi_export_l4_shc) = \
    [fprop("SHC", "Specific Heat Capacity (J/kgK)", 0, 10000, 1000)] * conlayers
    (Material.envi_export_lo_thi, Material.envi_export_l1_thi, Material.envi_export_l2_thi, Material.envi_export_l3_thi, Material.envi_export_l4_thi) = \
    [fprop("mm", "Thickness (mm)", 1, 10000, 100)] * conlayers
    (Material.envi_export_lo_tab, Material.envi_export_l1_tab, Material.envi_export_l2_tab, Material.envi_export_l3_tab, Material.envi_export_l4_tab) = \
    [fprop("TA", "Thermal Absorptance", 0.001, 1, 0.8)] * conlayers
    (Material.envi_export_lo_sab, Material.envi_export_l1_sab, Material.envi_export_l2_sab, Material.envi_export_l3_sab, Material.envi_export_l4_sab) = \
    [fprop("SA", "Solar Absorptance", 0.001, 1, 0.6)] * conlayers
    (Material.envi_export_lo_vab, Material.envi_export_l1_vab, Material.envi_export_l2_vab, Material.envi_export_l3_vab, Material.envi_export_l4_vab) = \
    [fprop("VA", "Visible Absorptance", 0.001, 1, 0.6)] * conlayers
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

# FloVi material definitions
    Material.fvmat = fvmat
    Material.flovi_bmb_type = eprop([("0", "Wall", "Wall boundary"), ("1", "Inlet", "Inlet boundary"), ("2", "Outlet", "Outlet boundary"), ("3", "Symmetry", "Symmetry boundary"), ("4", "Empty", "Empty boundary")], "", "FloVi blockmesh boundary type", "0")
    Material.flovi_bmwp_type = eprop([("zeroGradient", "Zero Gradient", "Zero gradient boundary")], "", "FloVi wall boundary type", "zeroGradient")
    Material.flovi_bmwu_type = eprop([("fixedValue", "Fixed", "Fixed value boundary"), ("slip", "Slip", "Slip boundary")], "", "FloVi wall boundary type", "fixedValue")
    Material.flovi_bmwnutilda_type = eprop([("fixedValue", "Fixed", "Fixed value boundary")], "", "FloVi wall boundary type", "fixedValue")
    Material.flovi_bmwnut_type = eprop([("nutUSpaldingWallFunction", "SpaldingWF", "Fixed value boundary"), ("nutkWallFunction", "k wall function", "Fixed value boundary")], "", "FloVi wall boundary type", "nutUSpaldingWallFunction")
    Material.flovi_bmwk_type = eprop([("kqRWallFunction", "kqRWallFunction", "Fixed value boundary")], "", "FloVi wall boundary type", "kqRWallFunction")
    Material.flovi_bmwe_type = eprop([("epsilonWallFunction", "epsilonWallFunction", "Fixed value boundary")], "", "FloVi wall boundary type", "epsilonWallFunction")
    Material.flovi_bmwo_type = eprop([("omegaWallFunction", "omegaWallFunction", "Fixed value boundary")], "", "FloVi wall boundary type", "omegaWallFunction")

    Material.flovi_bmu_x = fprop("X", "Value in the X-direction", -1000, 1000, 0.0)
    Material.flovi_bmu_y = fprop("Y", "Value in the Y-direction", -1000, 1000, 0.0)
    Material.flovi_bmu_z = fprop("Z", "Value in the Z-direction", -1000, 1000, 0.0)
    
#    Material.flovi_bmwnut_y = fprop("Y", "Value in the Y-direction", -1000, 1000, 0.0)
#    Material.flovi_bmwnut_z = fprop("Z", "Value in the Z-direction", -1000, 1000, 0.0) 
    Material.flovi_bmip_type = eprop([("zeroGradient", "Zero Gradient", "Zero gradient pressure boundary"), ("freestreamPressure", "Freestream Pressure", "Free stream pressure gradient boundary")], "", "FloVi wall boundary type", "zeroGradient")
    Material.flovi_bmiop_val = fprop("X", "Pressure value", -1000, 1000, 0.0)
    Material.flovi_bmop_type = eprop([("zeroGradient", "Zero Gradient", "Zero gradient pressure boundary"), ("freestreamPressure", "Freestream Pressure", "Free stream pressure gradient boundary"), ("fixedValue", "FixedValue", "Fixed value pressure boundary")], "", "FloVi wall boundary type", "zeroGradient")
    Material.flovi_bmiu_type = eprop([("freestream", "Freestream velocity", "Freestream velocity boundary"), ("fixedValue", "Fixed Value", "Fixed velocity boundary")], "", "FloVi wall boundary type", "fixedValue")
    Material.flovi_bmou_type = eprop([("freestream", "Freestream velocity", "Freestream velocity boundary"), ("zeroGradient", "Zero Gradient", "Zero gradient  boundary"), ("fixedValue", "Fixed Value", "Fixed velocity boundary")], "", "FloVi wall boundary type", "zeroGradient")
    Material.flovi_bminut_type = eprop([("calculated", "Calculated", "Calculated value boundary")], "", "FloVi wall boundary type", "calculated")
    Material.flovi_bmonut_type = eprop([("calculated", "Calculated", "Calculated value boundary")], "", "FloVi wall boundary type", "calculated")
    Material.flovi_bminutilda_type = eprop([("freeStream", "Freestream", "Free stream value boundary")], "", "FloVi wall boundary type", "freeStream")    
    Material.flovi_bmonutilda_type = eprop([("freeStream", "Freestream", "Free stream value boundary")], "", "FloVi wall boundary type", "freeStream") 
    Material.flovi_bmik_type = eprop([("fixedValue", "Fixed Value", "Fixed value boundary")], "", "FloVi wall boundary type", "fixedValue")
    Material.flovi_bmok_type = eprop([("inletOutlet", "Inlet/outlet", "Inlet/outlet boundary")], "", "FloVi wall boundary type", "inletOutlet")
    Material.flovi_bmie_type = eprop([("fixedValue", "Fixed Value", "Fixed value boundary")], "", "FloVi wall boundary type", "fixedValue")
    Material.flovi_bmoe_type = eprop([("inletOutlet", "Inlet/outlet", "Inlet/outlet boundary")], "", "FloVi wall boundary type", "inletOutlet")
    Material.flovi_bmio_type = eprop([("zeroGradient", "Zero Gradient", "Zero gradient boundary")], "", "FloVi wall boundary type", "zeroGradient")
    Material.flovi_bmoo_type = eprop([("fixedValue", "Fixed", "Fixed value boundary")], "", "FloVi wall boundary type", "fixedValue")
    Material.flovi_bmiu_x = fprop("X", "Value in the X-direction", -1000, 1000, 0.0)
    Material.flovi_bmiu_y = fprop("Y", "Value in the Y-direction", -1000, 1000, 0.0)
    Material.flovi_bmiu_z = fprop("Z", "Value in the Z-direction", -1000, 1000, 0.0)
    Material.flovi_bmou_x = fprop("X", "Value in the X-direction", -1000, 1000, 0.0)
    Material.flovi_bmou_y = fprop("Y", "Value in the Y-direction", -1000, 1000, 0.0)
    Material.flovi_bmou_z = fprop("Z", "Value in the Z-direction", -1000, 1000, 0.0)
    Material.flovi_bmnut = fprop("", "nuTilda value", -1000, 1000, 0.0)
    Material.flovi_bmk = fprop("", "k value", 0, 1000, 0.0)
    Material.flovi_bme = fprop("", "Epsilon value", 0, 1000, 0.0)
    Material.flovi_bmo = fprop("", "Omega value", 0, 1000, 0.0) 
    Material.flovi_ground = bprop("", "Ground material", False)
    Material.flovi_b_sval = fprop("", "Scalar value", -500, 500, 0.0) 
    Material.flovi_b_vval = fvprop(3, '', 'Vector value', [0, 0, 0], 'VELOCITY', -100, 100)
    Material.flovi_p_field = bprop("", "Take boundary velocity from the field velocity", False)
    Material.flovi_u_field = bprop("", "Take boundary velocity from the field velocity", False)
#    Material.flovi_bmionut = fprop("Value", "nuTilda value", -1000, 1000, 0.0)
#    Material.flovi_bmionut_y = fprop("Y", "Value in the Y-direction", -1000, 1000, 0.0)
#    Material.flovi_bmionut_z = fprop("Z", "Value in the Z-direction", -1000, 1000, 0.0)   
    
# Scene parameters
#    Scene.fs = iprop("Frame start", "Starting frame",0, 1000, 0)
#    (Scene.fe, Scene.gfe, Scene.cfe) = [iprop("Frame start", "End frame",0, 50000, 0)] * 3
    Scene.vipath = sprop("VI Path", "Path to files included with the VI-Suite ", 1024, addonpath)
    Scene.solday = bpy.props.IntProperty(name = "", description = "Day of year", min = 1, max = 365, default = 1, update=sunpath1)
    Scene.solhour = bpy.props.FloatProperty(name = "", description = "Time of day", min = 0, max = 24, default = 12, update=sunpath1)
    Scene.soldistance = bpy.props.IntProperty(name = "", description = "Sun path scale", min = 1, max = 5000, default = 100, update=sunpath1)
    (Scene.hourdisp, Scene.spupdate) = [bprop("", "",0)] * 2
    Scene.li_disp_panel = iprop("Display Panel", "Shows the Display Panel", -1, 2, 0)
    Scene.li_disp_count = iprop("", "", 0, 1000, 0)
    Scene.vi_disp_3d = bprop("VI 3D display", "Boolean for 3D results display",  False)
    Scene.vi_disp_3dlevel = bpy.props.FloatProperty(name = "", description = "Level of 3D result plane extrusion", min = 0, max = 500, default = 0, update = eupdate)
    Scene.ss_disp_panel = iprop("Display Panel", "Shows the Display Panel", -1, 2, 0)
    (Scene.lic_disp_panel, Scene.vi_display, Scene.sp_disp_panel, Scene.wr_disp_panel, Scene.ss_leg_display, Scene.en_disp_panel, Scene.li_compliance, Scene.vi_display_rp, Scene.vi_leg_display, 
     Scene.vi_display_sel_only, Scene.vi_display_vis_only) = [bprop("", "", False)] * 11
    Scene.vi_leg_max = bpy.props.FloatProperty(name = "", description = "Legend maximum", min = 0, max = 1000000, default = 1000, update=legupdate)
    Scene.vi_leg_min = bpy.props.FloatProperty(name = "", description = "Legend minimum", min = 0, max = 1000000, default = 0, update=legupdate)
    Scene.vi_display_rp_fs = iprop("", "Point result font size", 4, 48, 9)
    Scene.vi_display_rp_fc = fvprop(4, "", "Font colour", [0.0, 0.0, 0.0, 1.0], 'COLOR', 0, 1)
    Scene.vi_display_rp_fsh = fvprop(4, "", "Font shadow", [0.0, 0.0, 0.0, 1.0], 'COLOR', 0, 1)
    Scene.vi_display_rp_off = fprop("", "Surface offset for number display", 0, 1, 0.001)
    Scene.vi_disp_trans = bpy.props.FloatProperty(name = "", description = "Sensing material transparency", min = 0, max = 1, default = 1, update = tupdate)
    Scene.vi_disp_wire = bpy.props.BoolProperty(name = "", description = "Draw wire frame", default = 0, update=wupdate)
    Scene.vi_disp_sk = bprop("", "Boolean for skyview display",  False)
    Scene.li_projname = sprop("", "Name of the building project", 1024, '')
    Scene.li_assorg = sprop("", "Name of the assessing organisation", 1024, '')
    Scene.li_assind = sprop("", "Name of the assessing individual", 1024, '')
    Scene.li_jobno = sprop("", "Project job number", 1024, '')
    (Scene.resat_disp, Scene.resaws_disp, Scene.resawd_disp, Scene.resah_disp, Scene.resasb_disp, Scene.resasd_disp, Scene.reszt_disp, Scene.reszh_disp, Scene.reszc_disp, reswsg, rescpp, rescpm, resvls, resvmh, resim, resiach, resco2, resihl, resl12ms,
     reslof, resmrt, resocc, resh, resfhb, ressah, ressac) = resnameunits() 
#    Scene.resnode = sprop("", "", 0, "")
#    Scene.restree = sprop("", "", 0, "") 
#    Scene.epversion = sprop("", "EnergyPlus version", 1024, epversion.replace('-', '.'))

    nodeitems_utils.register_node_categories("Vi Nodes", vinode_categories)
    nodeitems_utils.register_node_categories("EnVi Nodes", envinode_categories)

def unregister():
    bpy.utils.unregister_module(__name__)
    nodeitems_utils.unregister_node_categories("Vi Nodes")
    nodeitems_utils.unregister_node_categories("EnVi Nodes")

