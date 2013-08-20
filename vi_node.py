# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import bpy, bpy_extras, glob, os, inspect, sys, multiprocessing
from nodeitems_utils import NodeCategory, NodeItem
#from . import vi_operators
from .vi_func import nodeinit

class ViNetwork(bpy.types.NodeTree):
    '''A node tree for VI-Suite analysis.'''
    bl_idname = 'ViN'
    bl_label = 'Vi Network'
    bl_icon = 'LAMP_SUN'
    
    def __init__(self):
        self.name = 'VI Network'
        print(self.name)

class ViNodes:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ViN'

class ViGExLiNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite export type'''
    bl_idname = 'ViGExLiNode'
    bl_label = 'VI lighting geometry export'
    bl_icon = 'LAMP' 
    
    filepath = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    filedir = bpy.props.StringProperty()
    newdir = bpy.props.StringProperty()
    filebase = bpy.props.StringProperty()
    objfilebase = bpy.props.StringProperty()
    reslen = bpy.props.IntProperty()
    exported = bpy.props.BoolProperty()
    
    def nodeexported(self, context):
        self.exported = False
#        if self.outputs[0].is_linked:
#            link = self.outputs[0].links[0]
#            bpy.data.node_groups['VI Network'].links.remove(link)
#        self.outputs[0].hide = True
    
    animtype = [('Static', "Static", "Simple static analysis"), ('Geometry', "Geometry", "Animated geometry analysis"), ('Material', "Material", "Animated material analysis"), ('Lights', "Lights", "Animated artificial lighting analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeexported)
    cpoint = bpy.props.EnumProperty(items=[("0", "Faces", "Export faces for calculation points"),("1", "Vertices", "Export vertices for calculation points"), ],
            name="", description="Specify the calculation point geometry", default="1", update = nodeexported)
    radfiles = []
    
    def init(self, context):
        nodeinit(self)
        self.outputs.new('ViLiGOut', 'Geometry out')
        self.outputs[0].hide = True

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('Animation:')
        row.prop(self, 'animmenu')
        row = layout.row()
        row.label('Calculation point:')
        row.prop(self, 'cpoint')
        row = layout.row()
        row.operator("node.ligexport", text = "Export").nodename = self.name
     
    def update(self):
        if self.outputs[0].is_linked:
            if self.outputs[0].links[0].to_socket.color() != self.outputs[0].color():
                link = self.outputs[0].links[0]
                bpy.data.node_groups['VI Network'].links.remove(link)
        
       
class ViLiNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite analysis type'''
    bl_idname = 'ViLiNode'
    bl_label = 'VI Lighting Analysis'
    bl_icon = 'LAMP'
    
    analysistype = [('0', "Illuminance", "Lux Calculation"), ('1', "Irradiance", "W/m"+ u'\u00b2' + " Calculation"), ('2', "Daylight Factor", "DF (%) Calculation"),]  
    
    unit = bpy.props.StringProperty()

    animtype = [('Static', "Static", "Simple static analysis"), ('Time', "Time", "Animated time analysis")]

    skylist = [    ("0", "Sunny", "CIE Sunny Sky description"),
                   ("1", "Partly Coudy", "CIE Sunny Sky description"),
                   ("2", "Coudy", "CIE Partly Cloudy Sky description"),
                   ("3", "DF Sky", "Daylight Factor Sky description"),
                   ("4", "HDR Sky", "HDR file sky"),
                   ("5", "Radiance Sky", "Radiance file sky"),
                   ("6", "None", "No Sky")]
    
    def nodeexported(self, context):
        self.exported = False
        self.bl_label = '*VI Lighting Analysis'
        
    analysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = analysistype, default = '0', update = nodeexported)
    simalg = bpy.props.StringProperty(name="", description="Name of the HDR image file", default="")
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeexported)
    skymenu = bpy.props.EnumProperty(items=skylist, name="", description="Specify the type of sky for the simulation", default="0", update = nodeexported)
    shour = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=24, default=12, update = nodeexported)
    sdoy = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=365, default=1, update = nodeexported)
    ehour = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=24, default=12, update = nodeexported)
    edoy = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=365, default=1, update = nodeexported)
    daysav = bpy.props.BoolProperty(name="", description="Enable daylight saving clock", default=False, update = nodeexported)
    lati = bpy.props.FloatProperty(name="", description="Site Latitude", min=-90, max=90, default=52, update = nodeexported)
    longi = bpy.props.FloatProperty(name="", description="Site Longitude relative to local meridian", min=-15, max=15, default=0, update = nodeexported) 
    
    stamer = bpy.props.EnumProperty(
            items=[("0", "YST", ""),("1", "PST", ""),("2", "MST", ""),("3", "CST", ""),("4", "EST", ""),("GMT", "GMT", ""),("6", "CET", ""),("7", "EET", ""),
                   ("8", "AST", ""),("9", "GST", ""),("10", "IST", ""),("11", "JST", ""),("12", "NZST", ""), ],
            name="", description="Specify the local meridian", default="GMT")
    
    summer = bpy.props.EnumProperty(
            items=[("0", "YDT", ""),("1", "PDT", ""),("2", "MDT", ""),("3", "CDT", ""),("4", "EDT", ""),("BST", "BST", ""),("6", "CEST", ""),
                   ("7", "EEST", ""),("8", "ADT", ""),("9", "GDT", ""),("10", "IDT", ""),("11", "JDT", ""),("12", "NZDT", ""),],
            name="", description="Specify the local Summertime meridian", default="BST")
    
    simacc = bpy.props.EnumProperty(items=[("0", "Low", "Low accuracy and high speed (preview)"),("1", "Medium", "Medium speed and accuracy"), ("2", "High", "High but slow accuracy"),("3", "Custom", "Edit Radiance parameters"), ],
            name="", description="Simulation accuracy", default="0")
    

    cusacc = bpy.props.StringProperty(
            name="", description="Custom Radiance simulation parameters", default="", update = nodeexported)
            
    interval = bpy.props.FloatProperty(name="", description="Site Latitude", min=0.25, max=24, default=1, update = nodeexported)
    exported = bpy.props.BoolProperty(default=False)
    hdr = bpy.props.BoolProperty(name="HDR", description="Export HDR panoramas", default=False, update = nodeexported)
    disp_leg = bpy.props.BoolProperty(default=False)
    hdrname = bpy.props.StringProperty(name="", description="Name of the HDR image file", default="", update = nodeexported)
    skyname = bpy.props.StringProperty(name="", description="Name of the Radiance sky file", default="", update = nodeexported)
    skynum = bpy.props.IntProperty()
    timetype = bpy.props.StringProperty()
    TZ = bpy.props.StringProperty()
    resname = bpy.props.StringProperty()
    rp_display = bpy.props.BoolProperty(default = False)
    
    def init(self, context):
        self.inputs.new('ViLiGIn', 'Geometry in')
        
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Analysis type:")
        row.prop(self, 'analysismenu')
        row = layout.row()
        if self.analysismenu in ('0', '1'):
            row.label("Sky type:")
            row.prop(self, 'skymenu')
            if self.skymenu in ('0', '1', '2'):
                row = layout.row()
                row.label("Animation:")
                row.prop(self, 'animmenu')
                row = layout.row() 
                row.label("Daylight saving:")
                row.prop(self, 'daysav')
                row = layout.row() 
                row.label("Local meridian:")
                row.prop(self, 'stamer') if self.daysav == False else row.prop(self, 'summer')
                row = layout.row() 
                row.label("Latitude:")
                row.prop(self, 'lati')
                row = layout.row() 
                row.label("Longitude:")
                row.prop(self, 'longi')
                row = layout.row() 
                row.label("Start hour:")
                row.prop(self, 'shour')
                row = layout.row() 
                row.label("Start day of year:")
                row.prop(self, 'sdoy')
                if self.animmenu == 'Time':
                    row = layout.row() 
                    row.label("End hour:")
                    row.prop(self, 'ehour')
                    row = layout.row() 
                    row.label("End day of year:")
                    row.prop(self, 'edoy')
                    if self.edoy < self.sdoy:
                        self.edoy = self.sdoy
                    if self.edoy == self.sdoy and self.ehour < self.shour: 
                        self.ehour = self.shour
                    row = layout.row() 
                    row.label("Interval (hours):")
                    row.prop(self, 'interval')
            elif self.skymenu == '4':
                row = layout.row() 
                row.label("HDR file:")
                row.operator('node.hdrselect', text = 'HDR select') 
                row = layout.row() 
                row.prop(self, 'hdrname') 
            elif self.skymenu == '5':
                row = layout.row() 
                row.label("Radiance file:")
                row.operator('node.skyselect', text = 'Sky select') 
                row = layout.row() 
                row.prop(self, 'skyname') 
        row = layout.row()
        row.prop(self, 'hdr')
        row.operator("node.liexport", text = "Export").nodename = self.name
        if self.inputs['Geometry in'].is_linked and self.exported == True and self.inputs[0].links[0].from_node.exported == True:
            row = layout.row()
            row.label("Accuracy:")
            row.prop(self, 'simacc')
            if self.simacc == '3':
               row = layout.row()
               row.label("Radiance parameters:")
               row.prop(self, 'cusacc') 
            row = layout.row()
            row.operator("node.radpreview", text = 'Preview').nodename = self.name
            row.operator("node.calculate", text = 'Calculate').nodename = self.name
      

class ViLiCBNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite climate based lighting node'''
    bl_idname = 'ViLiCBNode'
    bl_label = 'VI Climate Based Daylighting Analysis'
    bl_icon = 'LAMP'
    
    def nodeexported(self, context):
        self.exported = False
    
    analysistype = [('0', "Annual Light Exposure", "LuxHours Calculation"), ('1', "Annual Radiation Exposure", "kWh/m"+ u'\u00b2' + " Calculation"), ('2', "Daylight Availability", "DA (%) Calculation"), ('3', "Hourly irradiance", "Irradiance for each simulation time step")]
    analysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = analysistype, default = '0', update = nodeexported)
    animtype = [('0', "Static", "Simple static analysis"), ('1', "Geometry", "Animated time analysis"), ('2', "Material", "Animated time analysis"), ('3', "Lights", "Animated time analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = '0', update = nodeexported)
    
    simacc = bpy.props.EnumProperty(items=[("0", "Low", "Low accuracy and high speed (preview)"),("1", "Medium", "Medium speed and accuracy"), ("2", "High", "High but slow accuracy"),("3", "Custom", "Edit Radiance parameters"), ],
            name="", description="Simulation accuracy", default="0", update = nodeexported)
    cusacc = bpy.props.StringProperty(
            name="", description="Custom Radiance simulation parameters", default="", update = nodeexported)
    epwname = bpy.props.StringProperty(
            name="", description="Name of the EnergyPlus weather file", default="", update = nodeexported)
    
    exported = bpy.props.BoolProperty(default=False)    
    
    def init(self, context):
        self.outputs.new('ViLiWResOut', 'Data out')
        self.inputs.new('ViLiGIn', 'Geometry in')

    def update(self):
        if self.outputs['Data out'].is_linked:
            self.analysismenu = '3'
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Analysis Type:")
        row.prop(self, 'analysismenu')
        row = layout.row()
        row.label('EPW file:')
        row.operator('node.epwselect', text = 'Select EPW').nodename = self.name
        row = layout.row()
        row.prop(self, "epwname")        
        row = layout.row()
        row.label('Animation:')
        row.prop(self, "animmenu")
        row = layout.row()
        row.operator("node.liexport", text = "Export").nodename = self.name
        row = layout.row()
        row.label("Accuracy:")
        row.prop(self, 'simacc')
        if self.simacc == '3':
           row = layout.row()
           row.label("Radiance parameters:")
           row.prop(self, 'cusacc') 
        if self.exported == True:
            row = layout.row()
            row.operator("node.radpreview", text = 'Preview').nodename = self.name
            row.operator("node.calculate", text = 'Calculate').nodename = self.name

class ViLiCNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite lighting compliance node'''
    bl_idname = 'ViLiCNode'
    bl_label = 'VI Lighting Compliance'
    bl_icon = 'LAMP'
    
    analysistype = [('0', "BREEAM", "BREEAM HEA1 calculation"), ('1', "LEED", "LEED EQ8.1 calculation"), ('2', "Green Star", "Green Star Calculation")]  
    buildtype = [('0', "School", "School lighting standard"), ('1', "Residential", "Residential lighting standard")]
    animtype = [('0', "Static", "Simple static analysis"), ('1', "Geometry", "Animated time analysis"), ('2', "Material", "Animated time analysis"), ('3', "Lights", "Animated time analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = '0')

    analysismenu = bpy.props.EnumProperty(name="", description="Type of analysis", items = analysistype, default = '0')
    buildmenu = bpy.props.EnumProperty(name="", description="Type of building", items=buildtype, default = '0')  
    simacc = bpy.props.EnumProperty(items=[("0", "Standard", "Standard accuracy for this metric"),("1", "Custom", "Edit Radiance parameters"), ],
            name="", description="Simulation accuracy", default="0")        
    cusacc = bpy.props.StringProperty(
            name="", description="Custom Radiance simulation parameters", default="")
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Compliance standard:")
        row.prop(self, 'analysismenu')
        if self.analysismenu == '0':
         row = layout.row()
        row.label("Building type:")
        row.prop(self, 'buildmenu')   
        row = layout.row()
        row.label('Animation:')
        row.prop(self, "animmenu")
        row = layout.row()
        row.label("Accuracy:")
        row.prop(self, 'simacc')
        if self.simacc == '1':
           row = layout.row()
           row.label("Radiance parameters:")
           row.prop(self, 'cusacc') 
        row = layout.row()
        row.operator("node.radpreview", text = 'Preview')
        row.operator("node.calculate", text = 'Calculate')
        
class ViSPNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite sun path'''
    bl_idname = 'ViSPNode'
    bl_label = 'VI Sun Path'
    bl_icon = 'LAMP'
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate') 


class ViSSNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite sun path'''
    bl_idname = 'ViSPNode'
    bl_label = 'VI Sun Path'
    bl_icon = 'LAMP'
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate')

class ViWRNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite wind rose generator'''
    bl_idname = 'ViWRNode'
    bl_label = 'VI Wind Rose'
    bl_icon = 'LAMP'

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate')
        
class ViGNode(bpy.types.Node, ViNodes):
    '''Node describing a glare analysis'''
    bl_idname = 'ViGNode'
    bl_label = 'VI Glare'
    bl_icon = 'LAMP'

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate')
        
class ViGExEnNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite export type'''
    bl_idname = 'ViGExEnNode'
    bl_label = 'VI EP geometry conversion'

    exported = bpy.props.BoolProperty()
    
    def nodeexported(self, context):
        self.exported = False
    
    animtype = [('Static', "Static", "Simple static analysis"), ('Geometry', "Geometry", "Animated geometry analysis"), ('Material', "Material", "Animated material analysis"), ('Lights', "Lights", "Animated artificial lighting analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeexported)
    epfiles = []
    
    def init(self, context):
        self.outputs.new('ViEnGOut', 'Geometry out')
        self.outputs[0].hide = True

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('Animation:')
        row.prop(self, 'animmenu')
        row = layout.row()
        row.operator("node.engexport", text = "Export").nodename = self.name
     
    def update(self):
        if self.outputs[0].is_linked:
            if self.outputs[0].links[0].to_socket.color() != self.outputs[0].color():
                link = self.outputs[0].links[0]
                bpy.data.node_groups['VI Network'].links.remove(link)

class ViExEnNode(bpy.types.Node, ViNodes):
    '''Node describing an EnergyPlus export'''
    bl_idname = 'ViExEnNode'
    bl_label = 'VI EnergyPLus analysis'
    bl_icon = 'LAMP'    
            
    nproc = bpy.props.StringProperty()
    rm = bpy.props.StringProperty()
    cat = bpy.props.StringProperty()
    fold = bpy.props.StringProperty()
    cp = bpy.props.StringProperty() 
    filepath = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    filedir = bpy.props.StringProperty()
    newdir = bpy.props.StringProperty()
    filebase = bpy.props.StringProperty()
    idf_file = bpy.props.StringProperty()
    exported = bpy.props.BoolProperty()
    resname = bpy.props.StringProperty(name="Results Name", description="Base name for the results files", default="results")
    dsdoy = bpy.props.IntProperty()
    dedoy = bpy.props.IntProperty()
    
    def nodeexported(self, context):
        self.exported = False
        self.bl_label = '*VI EnergyPLus analysis'
        
 
    loc = bpy.props.StringProperty(name="", description="Identifier for this project", default="", update = nodeexported)
    terrain = bpy.props.EnumProperty(items=[("0", "City", "Towns, city outskirts, centre of large cities"),
                   ("1", "Urban", "Urban, Industrial, Forest"),("2", "Suburbs", "Rough, Wooded Country, Suburbs"),
                    ("3", "Country", "Flat, Open Country"),("4", "Ocean", "Ocean, very flat country")], 
                    name="", description="Specify the surrounding terrain", default="0", update = nodeexported)
    
    addonpath = os.path.dirname(inspect.getfile(inspect.currentframe()))
    matpath = addonpath+'/EPFiles/Materials/Materials.data'
    epwpath = addonpath+'/EPFiles/Weather/'
    weatherlist = [((wfile, os.path.basename(wfile).strip('.epw').split(".")[0], 'Weather Location')) for wfile in glob.glob(epwpath+"/*.epw")]
    weather = bpy.props.EnumProperty(items = weatherlist, name="", description="Weather for this project")
    sdoy = bpy.props.IntProperty(name = "", description = "Day of simulation", min = 1, max = 365, default = 1, update = nodeexported) 
    edoy = bpy.props.IntProperty(name = "", description = "Day of simulation", min = 1, max = 365, default = 365, update = nodeexported)
    timesteps = bpy.props.IntProperty(name = "", description = "Time steps per hour", min = 1, max = 4, default = 1, update = nodeexported)
    resfilename = bpy.props.StringProperty(name = "", default = 'results')    
    restype= bpy.props.EnumProperty(items = [("0", "Ambient", "Ambient Conditions"), ("1", "Zone Thermal", "Thermal Results"), ("2", "Comfort", "Comfort Results"), ("3", "Ventilation", "Ventilation Results")],
                                   name="", description="Specify the EnVi results catagory", default="0", update = nodeexported)
        
    resat = bpy.props.BoolProperty(name = "Temperature", description = "Ambient Temperature (K)", default = False, update = nodeexported)
    resaws = bpy.props.BoolProperty(name = "Wind Speed", description = "Ambient Wind Speed (m/s)", default = False, update = nodeexported)
    resawd = bpy.props.BoolProperty(name = "Wind Direction", description = "Ambient Wind Direction (degrees from North)", default = False, update = nodeexported)
    resah = bpy.props.BoolProperty(name = "Humidity", description = "Ambient Humidity", default = False, update = nodeexported)
    resasb = bpy.props.BoolProperty(name = "Direct Solar", description = "Direct Solar Radiation (W/m^2K)", default = False, update = nodeexported)
    resasd = bpy.props.BoolProperty(name = "Diffuse Solar", description = "Diffuse Solar Radiation (W/m^2K)", default = False, update = nodeexported)
    restt = bpy.props.BoolProperty(name = "Temperature", description = "Zone Temperatures", default = False, update = nodeexported)
    restwh = bpy.props.BoolProperty(name = "Heating Watts", description = "Zone Heating Requirement (Watts)", default = False, update = nodeexported)
    restwc = bpy.props.BoolProperty(name = "Cooling Watts", description = "Zone Cooling Requirement (Watts)", default = False, update = nodeexported)
    reswsg = bpy.props.BoolProperty(name = "Solar Gain", description = "Window Solar Gain (Watts)", default = False, update = nodeexported)
#    resthm = BoolProperty(name = "kWh/m2 Heating", description = "Zone Heating kilo Watt hours of heating per m2 floor area", default = False)
#    restcm = BoolProperty(name = "kWh/m2 Cooling", description = "Zone Cooling kilo Watt hours of cooling per m2 floor area", default = False)
    rescpp = bpy.props.BoolProperty(name = "PPD", description = "Percentage Proportion Dissatisfied", default = False, update = nodeexported)
    rescpm = bpy.props.BoolProperty(name = "PMV", description = "Predicted Mean Vote", default = False, update = nodeexported)
    resvls = bpy.props.BoolProperty(name = "Ventilation (l/s)", description = "Zone Ventilation rate (l/s)", default = False, update = nodeexported)
    resvmh = bpy.props.BoolProperty(name = "Ventilation (m3/h)", description = "Zone Ventilation rate (m3/h)", default = False, update = nodeexported)
    resims = bpy.props.BoolProperty(name = "Infiltration (m3/s)", description = "Zone Infiltration rate (m3/s)", default = False, update = nodeexported)
    resimh = bpy.props.BoolProperty(name = "Infiltration (m3/h)", description = "Zone Infiltration rate (m3/h)", default = False, update = nodeexported)

    def init(self, context):
        self.inputs.new('ViEnGIn', 'Geometry in')
        nodeinit(self)
        self['xtypes']
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Project name/location")
        row.prop(self, "loc")
        row = layout.row()
        row.label("Weather file:")
        row.prop(self, "weather")
        row = layout.row()
        row.label(text = 'Terrain:')
        col = row.column()
        col.prop(self, "terrain")
        row = layout.row()
        row.label(text = 'Start day:')
        col = row.column()
        col.prop(self, "sdoy")
        row = layout.row()
        row.label(text = 'End day:')
        col = row.column()
        col.prop(self, "edoy")
        row = layout.row()
        row.label(text = 'Time-steps/hour)')
        row.prop(self, "timesteps")
        row = layout.row()
        row.label(text = 'Results Catagory:')
        col = row.column()            
        col.prop(self, "restype")
        if self.restype == "0":
            row = layout.row()
            row.prop(self, "resat")
            row.prop(self, "resaws")
            row = layout.row()
            row.prop(self, "resawd")
            row.prop(self, "resah")
            row = layout.row()
            row.prop(self, "resasb")
            row.prop(self, "resasd") 
        elif self.restype == "1":
            row = layout.row()
            row.prop(self, "restt")
            row.prop(self, "restwh")
            row = layout.row()
            row.prop(self, "restwc")
            row.prop(self, "reswsg")
        elif self.restype == "2":
            row = layout.row()
            row.prop(self, "rescpp")
            row.prop(self, "rescpm")
        elif self.restype == "3":
            row = layout.row()
            row.prop(self, "resims")
        
        if self.inputs[0].is_linked == True:
            row = layout.row()
            row.operator("node.enexport", text = 'Export').nodename = self.name
        
        if self.inputs[0].is_linked == True and self.exported == True and self.inputs[0].links[0].from_node.exported == True:
            row = layout.row()
            row.label(text = 'Results name:')
            row.prop(self, 'resname')
            row = layout.row()
            row.operator("node.ensim", text = 'Calculate').nodename = self.name

class ViEnRFNode(bpy.types.Node, ViNodes):       
    '''Node for EnergyPlus results file selection'''
    bl_idname = 'ViEnRFNode'
    bl_label = 'VI EnergyPLus results file selection'
    
    resfilename = bpy.props.StringProperty(name="", description="Name of the EnVi results file", default="")
    dsdoy = bpy.props.IntProperty()
    dedoy = bpy.props.IntProperty()
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('ESO file:')
        row.operator('node.esoselect', text = 'Select ESO file').nodename = self.name
        row = layout.row()
        row.prop(self, 'resfilename')
        row.operator("node.fileprocess", text = 'Process file').nodename = self.name
    
class ViEnRNode(bpy.types.Node, ViNodes):       
    '''Node for EnergyPlus 2D results analysis'''
    bl_idname = 'ViEnRNode'
    bl_label = 'VI EnergyPLus results'
    
    ctypes = [("0", "Line", "Line Chart"), ("1", "Bar", "Bar Chart")]
    dsh = bpy.props.IntProperty(name = "Start", description = "", min = 1, max = 24, default = 1)
    deh = bpy.props.IntProperty(name = "End", description = "", min = 1, max = 24, default = 24)
    charttype = bpy.props.EnumProperty(items = ctypes, name = "Chart Type", default = "0")
    timemenu = bpy.props.EnumProperty(items=[("0", "Hourly", "Hourly results"),("1", "Daily", "Daily results"), ("2", "Monthly", "Monthly results")],
                                                      name="", description="Results frequency", default="0")     
    def init(self, context):
        self.inputs.new("ViEnRXIn", "X-axis")
        self['Start'] = 1 
        self['End'] = 365
        self.inputs.new("ViEnRY1In", "Y-axis 1")
        self.inputs[1].hide = True
        self.inputs.new("ViEnRY2In", "Y-axis 2")
        self.inputs[2].hide = True
        self.inputs.new("ViEnRY3In", "Y-axis 3")
        self.inputs[3].hide = True
        
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Day:")
        row.prop(self, '["Start"]')
        row.prop(self, '["End"]')
        row = layout.row()
        row.label("Hour:")
        row.prop(self, "dsh")
        row.prop(self, "deh")
        row = layout.row()
        row.prop(self, "charttype")
        row.prop(self, "timemenu")
        if self.inputs['X-axis'].is_linked and self.inputs['Y-axis 1'].is_linked:
            layout.operator("node.chart", text = 'Create plot').nodename = self.name
        
    def update(self):
        if self.inputs['X-axis'].is_linked == True:
            xrtype, xctype, xztype, xzrtype = [], [], [], []
            try:
                innode = self.inputs['X-axis'].links[0].from_node
            except:
                return
            self["_RNA_UI"] = {"Start": {"min":innode.dsdoy, "max":innode.dedoy}, "End": {"min":innode.dsdoy, "max":innode.dedoy}}    
            self['Start'], self['End'] = innode.dsdoy, innode.dedoy
            for restype in innode['rtypes']:
                xrtype.append((restype, restype, "Plot "+restype))
            for clim in innode['ctypes']:
                xctype.append((clim, clim, "Plot "+clim))
            for zone in innode['ztypes']:
                xztype.append((zone, zone, "Plot "+zone))
            for zoner in innode['zrtypes']:
                xzrtype.append((zoner, zoner, "Plot "+zoner))
            self.inputs['Y-axis 1'].hide = False
            
            if self.inputs['Y-axis 1'].is_linked == True:
                y1rtype, y1ctype, y1ztype, y1zrtype = [], [], [], []
                innode = self.inputs[1].links[0].from_node
                for restype in innode['rtypes']:
                    y1rtype.append((restype, restype, "Plot "+restype))
                for clim in innode['ctypes']:
                    y1ctype.append((clim, clim, "Plot "+clim))
                for zone in innode['ztypes']:
                    y1ztype.append((zone, zone, "Plot "+zone))
                for zoner in innode['zrtypes']:
                    y1zrtype.append((zoner, zoner, "Plot "+zoner))
                self.inputs['Y-axis 2'].hide = False 
                
                if self.inputs['Y-axis 2'].is_linked == True:
                    y2rtype, y2ctype, y2ztype, y2zrtype = [], [], [], []
                    innode = self.inputs[2].links[0].from_node
                    for restype in innode['rtypes']:
                        y2rtype.append((restype, restype, "Plot "+restype))
                    for clim in innode['ctypes']:
                        y2ctype.append((clim, clim, "Plot "+clim))
                    for zone in innode['ztypes']:
                        y2ztype.append((zone, zone, "Plot "+zone))
                    for zoner in innode['zrtypes']:
                        y2zrtype.append((zoner, zoner, "Plot "+zoner))
                    self.inputs['Y-axis 3'].hide = False
                    
                    if self.inputs['Y-axis 3'].is_linked == True:
                        y3rtype, y3ctype, y3ztype, y3zrtype = [], [], [], []
                        innode = self.inputs[3].links[0].from_node
                        for restype in innode['rtypes']:
                            y3rtype.append((restype, restype, "Plot "+restype))
                        for clim in innode['ctypes']:
                            y3ctype.append((clim, clim, "Plot "+clim))
                        for zone in innode['ztypes']:
                            y3ztype.append((zone, zone, "Plot "+zone))
                        for zoner in innode['zrtypes']:
                            y3zrtype.append((zoner, zoner, "Plot "+zoner))
            
                    else:
                        y3rtype = y3ctype = y3ztype = y3zrtype = [('0', '', '0')]
                else:
#                    self.inputs[3].hide = True
                    y2rtype = y2ctype = y2ztype = y2zrtype = [('0', '', '0')]
                    y3rtype = y3ctype = y3ztype = y3zrtype = [('0', '', '0')]
            else:
#                self.inputs[2].hide = True
                y1rtype = y1ctype = y1ztype = y1zrtype = [('0', '', '0')]
                y2rtype = y2ctype = y2ztype = y2zrtype = [('0', '', '0')]
                y3rtype = y3ctype = y3ztype = y3zrtype = [('0', '', '0')]
        else:
#            self.inputs[1].hide = True
            xrtype = xctype = xztype = xzrtype = [('0', '', '0')]
            y1rtype = y1ctype = y1ztype = y1zrtype = [('0', '', '0')]
            y2rtype = y2ctype = y2ztype = y2zrtype = [('0', '', '0')]
            y3rtype = y3ctype = y3ztype = y3zrtype = [('0', '', '0')]
        
        class ViEnRXIn(bpy.types.NodeSocket):
            '''Energy geometry out socket'''
            bl_idname = 'ViEnRXIn'
            bl_label = 'X-axis'
            
            rtypemenu = bpy.props.EnumProperty(items=xrtype, name="", description="Data type", default = xrtype[0][0])
            climmenu = bpy.props.EnumProperty(items=xctype, name="", description="Climate type", default = xctype[0][0])
            zonemenu = bpy.props.EnumProperty(items=xztype, name="", description="Zone", default = xztype[0][0])
            zonermenu = bpy.props.EnumProperty(items=xzrtype, name="", description="Zone result", default = xzrtype[0][0])
            statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Result statistic", default = 'Average')
            
            def draw(self, context, layout, node, text):
                row = layout.row()
                row.label('--')
                row = layout.row()
                row.prop(self, "rtypemenu", text = text)
                if self.is_linked == True:
                    row = layout.row()
                    if self.rtypemenu == "Climate":
                        row.prop(self, "climmenu")
                        if self.node.timemenu in ('1', '2'):
                            row.prop(self, "statmenu")
                    elif self.rtypemenu == "Zone":
                        row.prop(self, "zonemenu")
                        row = layout.row()
                        row.prop(self, "zonermenu")
                        if self.node.timemenu in ('1', '2'):
                            row.prop(self, "statmenu")
                row = layout.row()
                row.label('--')
                row = layout.row()
                
            def draw_color(self, context, node):
                return (0.0, 1.0, 0.0, 0.75)
                
            def color(self):
                return (0.0, 1.0, 0.0, 0.75)
        
        class ViEnRY1In(bpy.types.NodeSocket):
            '''Energy geometry out socket'''
            bl_idname = 'ViEnRY1In'
            bl_label = 'Y-axis1'
            
            rtypemenu = bpy.props.EnumProperty(items=y1rtype, name="", description="Simulation accuracy", default = y1rtype[0][0])
            
            climmenu = bpy.props.EnumProperty(items=y1ctype, name="", description="Climate type", default = y1ctype[0][0])
            zonemenu = bpy.props.EnumProperty(items=y1ztype, name="", description="Zone", default = y1ztype[0][0])
            zonermenu = bpy.props.EnumProperty(items=y1zrtype, name="", description="Zone result", default = y1zrtype[0][0])
            statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Zone result", default = 'Average')
            
            def draw(self, context, layout, node, text):
                row = layout.row()
                row.prop(self, "rtypemenu", text = text)
                if self.is_linked:
                    row = layout.row()
                    if self.rtypemenu == "Climate":
                        row.prop(self, "climmenu")
                        if self.node.timemenu in ('1', '2'):
                            row.prop(self, "statmenu")
                    elif self.rtypemenu == "Zone":
                        row.prop(self, "zonemenu")
                        row = layout.row()
                        row.prop(self, "zonermenu")
                        if self.node.timemenu in ('1', '2'):
                            row.prop(self, "statmenu")
                row = layout.row()
                row.label('--')
                row = layout.row()
                
            def draw_color(self, context, node):
                return (0.0, 1.0, 0.0, 0.75)
                
            def color(self):
                return (0.0, 1.0, 0.0, 0.75)
        
        class ViEnRY2In(bpy.types.NodeSocket):
            '''Energy geometry out socket'''
            bl_idname = 'ViEnRY2In'
            bl_label = 'Y-axis2'
            
            rtypemenu = bpy.props.EnumProperty(items=y2rtype, name="", description="Simulation accuracy", default = y2rtype[0][0])
            climmenu = bpy.props.EnumProperty(items=y2ctype, name="", description="Climate type", default = y2ctype[0][0])
            zonemenu = bpy.props.EnumProperty(items=y2ztype, name="", description="Zone", default = y2ztype[0][0])
            zonermenu = bpy.props.EnumProperty(items=y2zrtype, name="", description="Zone result", default = y2zrtype[0][0])
            statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Zone result", default = 'Average')
            
            def draw(self, context, layout, node, text):
                row = layout.row()
                row.prop(self, "rtypemenu", text = text)
                if self.is_linked:
                    row = layout.row()
                    if self.rtypemenu == "Climate":
                        row.prop(self, "climmenu")
                        if self.node.timemenu in ('1', '2'):
                            row.prop(self, "statmenu")
                    elif self.rtypemenu == "Zone":
                        row.prop(self, "zonemenu")
                        row = layout.row()
                        row.prop(self, "zonermenu")
                        if self.node.timemenu in ('1', '2'):
                            row.prop(self, "statmenu")
                row = layout.row()
                row.label('--')
                row = layout.row()
                
            def draw_color(self, context, node):
                return (0.0, 1.0, 0.0, 0.75)
                
            def color(self):
                return (0.0, 1.0, 0.0, 0.75)
                
        class ViEnRY3In(bpy.types.NodeSocket):
            '''Energy geometry out socket'''
            bl_idname = 'ViEnRY3In'
            bl_label = 'Y-axis3'
            
            rtypemenu = bpy.props.EnumProperty(items=y3rtype, name="", description="Simulation accuracy", default = y3rtype[0][0])
            climmenu = bpy.props.EnumProperty(items=y3ctype, name="", description="Climate type", default = y3ctype[0][0])
            zonemenu = bpy.props.EnumProperty(items=y3ztype, name="", description="Zone", default = y3ztype[0][0])
            zonermenu = bpy.props.EnumProperty(items=y3zrtype, name="", description="Zone result", default = y3zrtype[0][0])
            statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Zone result", default = 'Average')
            
            def draw(self, context, layout, node, text):
                row = layout.row()
                row.prop(self, "rtypemenu", text = text)
                if self.is_linked:
                    row = layout.row()
                    if self.rtypemenu == "Climate":
                        row.prop(self, "climmenu")
                        if self.node.timemenu in ('1', '2'):
                            row.prop(self, "statmenu")
                    elif self.rtypemenu == "Zone":
                        row.prop(self, "zonemenu")
                        row = layout.row()
                        row.prop(self, "zonermenu")
                        if self.node.timemenu in ('1', '2'):
                            row.prop(self, "statmenu")
                
            def draw_color(self, context, node):
                return (0.0, 1.0, 0.0, 0.75)
                
            def color(self):
                return (0.0, 1.0, 0.0, 0.75)
        
        bpy.utils.register_class(ViEnRXIn)
        bpy.utils.register_class(ViEnRY1In)
        bpy.utils.register_class(ViEnRY2In)
        bpy.utils.register_class(ViEnRY3In)
        
        #            self.inputs['X-axis'].xrestype = self.inputs['X-axis'].links[0].from_node.xtypes
        
         
class ViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ViN'

class ViLiWResOut(bpy.types.NodeSocket):
    '''LiVi irradiance out socket'''
    bl_idname = 'LiViWOut'
    bl_label = 'LiVi W/m2 out'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class ViLiGIn(bpy.types.NodeSocket):
    '''Lighting geometry in socket'''
    bl_idname = 'ViLiGIn'
    bl_label = 'Geometry in'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (1.0, 1.0, 0.0, 0.75)
        
    def color(self):
        return (1.0, 1.0, 0.0, 0.75)

class ViLiGOut(bpy.types.NodeSocket):
    '''Lighting geometry out socket'''
    bl_idname = 'ViLiGOut'
    bl_label = 'Geometry out'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (1.0, 1.0, 0.0, 0.75)
        
    def color(self):
        return (1.0, 1.0, 0.0, 0.75)
        
class ViEnGOut(bpy.types.NodeSocket):
    '''Energy geometry out socket'''
    bl_idname = 'ViEnGOut'
    bl_label = 'Geometry out'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (0.0, 0.0, 1.0, 0.75)
        
    def color(self):
        return (0.0, 0.0, 1.0, 0.75)

class ViEnROut(bpy.types.NodeSocket):
    '''Energy geometry out socket'''
    bl_idname = 'ViEnROut'
    bl_label = 'results out'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)
        
    def color(self):
        return (0.0, 1.0, 0.0, 0.75)        

#class ViEnRXIn(bpy.types.NodeSocket):
#    '''Energy geometry out socket'''
#    bl_idname = 'ViEnRXIn'
#    bl_label = 'X-axis'
#    
#    xrestype = [('0', "", '0')]
#    xrestypemenu = bpy.props.EnumProperty(items=xrestype, name="", description="Simulation accuracy", default="0")
#    xtimetype = bpy.props.EnumProperty(items=[("0", "", "0")], name="", description="", default="0")
#    
##    def draw(self, context, layout, node, text):
##        row = layout.row()
##        row.prop(self, "xrestypemenu", text = text)
#
#        
#    def draw_color(self, context, node):
#        return (0.0, 1.0, 0.0, 0.75)
#        
#    def color(self):
#        return (0.0, 1.0, 0.0, 0.75)
    
      
class ViEnGIn(bpy.types.NodeSocket):
    '''Energy geometry out socket'''
    bl_idname = 'ViEnGIn'
    bl_label = 'Geometry in'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (0.0, 0.0, 1.0, 0.75)
        
    def color(self):
        return (0.0, 0.0, 1.0, 0.75)
        
class EnViDataIn(bpy.types.NodeSocket):
    '''EnVi data in socket'''
    bl_idname = 'EnViDIn'
    bl_label = 'EnVi data in socket'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)
        
viexnodecat = [NodeItem("ViGExLiNode", label="VI-Suite lighting export"), NodeItem("ViGExEnNode", label="VI-Suite energy export")]

vinodecat = [NodeItem("ViLiNode", label="VI-Suite lighting analysis"), NodeItem("ViLiCNode", label="VI-Suite lighting compliance"), NodeItem("ViLiCBNode", label="VI-Suite climate based lighting"),\
             NodeItem("ViSPNode", label="VI-Suite sun path"), NodeItem("ViSSNode", label="VI-Suite shadow study"), NodeItem("ViWRNode", label="VI-Suite wind rose"), NodeItem("ViGNode", label="VI-Suite glare"), NodeItem("ViExEnNode", label="VI-Suite energy")] 

vidisnodecat = [NodeItem("ViEnRNode", label="VI-Suite chart display"), NodeItem("ViEnRFNode", label="EnergyPlus result file")]

vinode_categories = [ViNodeCategory("Export", "Export Nodes", items=viexnodecat), ViNodeCategory("Analysis", "Analysis Nodes", items=vinodecat), ViNodeCategory("Display", "Display Nodes", items=vidisnodecat)] 


####################### EnVi ventilation network ##############################

class EnViNetwork(bpy.types.NodeTree):
    '''A node tree for the creation of EnVi advanced ventilation networks.'''
    bl_idname = 'EnViN'
    bl_label = 'EnVi Network'
    bl_icon = 'FORCE_WIND'
    nodetypes = {}
    
class EnViNodes:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'EnViN'

class EnViBoundSocket(bpy.types.NodeSocket):
    '''A plain zone boundary socket'''
    bl_idname = 'EnViBoundSocket'
    bl_label = 'Plain zone boundary socket'
    bl_color = (1.0, 1.0, 0.2, 0.5)
      
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (0.8, 0.2, 0.8, 0.75)
        
class EnViSAirSocket(bpy.types.NodeSocket):
    '''A plain zone surface airflow socket'''
    bl_idname = 'EnViSAirSocket'
    bl_label = 'Plain zone surface airflow socket'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (0.1, 1.0, 0.2, 0.75)

class EnViCAirSocket(bpy.types.NodeSocket):
    '''A plain zone airflow component socket'''
    bl_idname = 'EnViCAirSocket'
    bl_label = 'Plain zone airflow component socket'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class EnViZone(bpy.types.Node, EnViNodes):
    '''Node describing a simulation zone'''
    bl_idname = 'EnViZone'
    bl_label = 'Zone'
    bl_icon = 'SOUND'
    
    
    
    def zupdate(self, context):
        obj = bpy.data.objects[self.zone]
        for face in obj.data.polygons:
            if bpy.data.objects[self.zone].data.materials[face.material_index].envi_con_type == 'Aperture':
                self.outputs.new('EnViSAirSocket', bpy.data.objects[self.zone].data.materials[face.material_index].name)
                self.inputs.new('EnViSAirSocket', bpy.data.objects[self.zone].data.materials[face.material_index].name, identifier = obj.name+str(face.index))
        for mat in bpy.data.objects[self.zone].data.materials:
            if mat.envi_boundary == 1:
                self.outputs.new('EnViBoundSocket', mat.name)
                self.inputs.new('EnViBoundSocket', mat.name)
    
    zone = bpy.props.StringProperty(update = zupdate)
    controltype = [("NoVent", "None", "No ventilation control"), ("Temperature", "Temperature", "Temperature control")]
    control = bpy.props.EnumProperty(name="", description="Ventilation control type", items=controltype, default='NoVent')
    vsched = bpy.props.StringProperty(name = "")
    zonevolume = bpy.props.FloatProperty(default=45, name = "")
    
    def init(self, context):
        print('hi', self.zone)
#        obj = bpy.data.objects['en_Cube']
#        for face in obj.data.polygons:
#            if bpy.data.objects['en_Cube'].data.materials[face.material_index].envi_con_type == 'Aperture':
#                self.outputs.new('EnViSAirSocket', bpy.data.objects['en_Cube'].data.materials[face.material_index].name)
#                self.inputs.new('EnViSAirSocket', bpy.data.objects['en_Cube'].data.materials[face.material_index].name, identifier = obj.name+str(face.index))
#        for mat in bpy.data.objects['en_Cube'].data.materials:
#            if mat.envi_boundary == 1:
#                self.outputs.new('EnViBoundSocket', mat.name)
#                self.inputs.new('EnViBoundSocket', mat.name)
        
    def update(self):
        try:
            for inp in self.inputs:
                self.outputs[inp.name].hide = True if inp.is_linked else False
            for outp in self.outputs:
                self.inputs[outp.name].hide = True if outp.is_linked else False
        except:
            pass
    
    def draw_buttons(self, context, layout):
        row=layout.row()
        row.prop(self, "zone")
        row=layout.row()
        row.label("Volume:")
        row.prop(self, "zonevolume")
        row=layout.row()
        row.label("Control type:")
        row.prop(self, "control")
        if self.control == 'Temperature':
            row=layout.row()
            row.label("Vent schedule:")
            row.prop(self, "vsched")

        
class EnViFanNode(bpy.types.Node, EnViNodes):
    '''Node describing a fan component'''
    bl_idname = 'EnViFan'
    bl_label = 'Envi Fan'
    bl_icon = 'SOUND'

    fantype = [("Volume", "Constant Volume", "Constant volume flow fan component")] 
    
    fantypeprop = bpy.props.EnumProperty(name="Type", description="Linkage type", items=fantype, default='Volume')
    
    fname = bpy.props.StringProperty(default = "", name = "")
    feff = bpy.props.FloatProperty(default = 0.7, name = "")
    fpr = bpy.props.FloatProperty(default = 600.0, name = "")
    fmfr = bpy.props.FloatProperty(default = 1.9, name = "")
    fmeff = bpy.props.FloatProperty(default = 0.9, name = "")
    fmaf = bpy.props.FloatProperty(default = 1.0, name = "")
    
    def init(self, context):
        self.inputs.new('EnViCAirSocket', 'Extract from')
        self.inputs.new('EnViCAirSocket', 'Supply to')
        self.outputs.new('NodeSocket', 'Schedule')
        self.outputs.new('EnViCAirSocket', 'Extract from')
        self.outputs.new('EnViCAirSocket', 'Supply to')
            
    def update(self):
        try:
            fsocknames = ('Extract from', 'Supply to')
            for ins in [insock for insock in self.inputs if insock.name in fsocknames]:
                self.outputs[ins.name].hide = True if ins.is_linked else False
            for outs in [outsock for outsock in self.outputs if outsock.name in fsocknames]:
                self.inputs[outs.name].hide = True if outs.is_linked else False
        except:
            pass
                
    def draw_buttons(self, context, layout):
        layout.prop(self, 'fantypeprop')
        if self.fantypeprop == "Volume":
            row = layout.row()
            row.label("Name:")
            row.prop(self, 'fname')
            row = layout.row()
            row.label("Efficiency:")
            row.prop(self, 'feff')
            row = layout.row()
            row.label("Pressure Rise (Pa):")
            row.prop(self, 'fpr')
            row = layout.row()
            row.label("Max flow rate:")
            row.prop(self, 'fmfr')
            row = layout.row()
            row.label("Motor efficiency:")
            row.prop(self, 'fmeff')
            row = layout.row()
            row.label("Airstream fraction:")
            row.prop(self, 'fmaf')
        
class EnViSLinkNode(bpy.types.Node, EnViNodes):
    '''Node describing an airflow surface linkage'''
    bl_idname = 'EnViSLink'
    bl_label = 'Envi Surface Airflow Linkage'
    bl_icon = 'SOUND'

    linktype = [
        ("Crack", "Crack", "Crack aperture used for leakage calculation"),
        ("ELA", "ELA", "Effective leakage area"),
        ("SO", "Simple Opening", "Simple opening element"),
        ("DO", "Detailed Opening", "Detailed opening element"),
        ("HO", "Horizontal Opening", "Horizontal opening element"),
        ("EF", "Exhaust fan", "Exhaust fan")]

    linktypeprop = bpy.props.EnumProperty(name="Type", description="Linkage type", items=linktype, default='Crack')
    
    amfc = bpy.props.FloatProperty(default = 1.0, name = "")
    amfe = bpy.props.FloatProperty(default = 0.6, name = "")
    cf = bpy.props.FloatProperty(default = 0.6, name = "")
    wdof = bpy.props.FloatProperty(default = 1, name = "")

    def init(self, context):
        self.inputs.new('EnViSAirSocket', 'Node 1')
        self.inputs.new('EnViSAirSocket', 'Node 2')
        self.outputs.new('NodeSocket', 'Schedule')
        self.outputs.new('EnViSAirSocket', 'Node 1')
        self.outputs.new('EnViSAirSocket', 'Node 2')
    
    def update(self):
        try:
            lsocknames = ('Node 1', 'Node 2')
            for ins in [insock for insock in self.inputs if insock.name in lsocknames]:
                self.outputs[ins.name].hide = True if ins.is_linked else False
            for outs in [outsock for outsock in self.outputs if outsock.name in lsocknames]:
                self.inputs[outs.name].hide = True if outs.is_linked else False
        except:
            pass
         
    def draw_buttons(self, context, layout):
        layout.prop(self, 'linktypeprop')
        if self.linktypeprop == "Crack":
            row = layout.row()
            row.label("Coefficient:")
            row.prop(self, 'amfc')
            row = layout.row()
            row.label("Exponent:")
            row.prop(self, 'amfe')
            row = layout.row()
            row.label("crack factor:")
            row.prop(self, 'cf')
        if self.linktypeprop in ("SO", "DO"):
            row = layout.row()
            row.label("Opening factor:")
            row.prop(self, 'wdof')
            
        
class EnViCLinkNode(bpy.types.Node, EnViNodes):
    '''Node describing an airflow component'''
    bl_idname = 'EnViCLink'
    bl_label = 'Envi Component'
    bl_icon = 'SOUND'

    linktype = [
        ("Crack", "Crack", "Crack aperture used for leakage calculation"),
        ("Duct", "Ducting", "Ducting for mechanical ventilation systems")] 
    
    linktypeprop = bpy.props.EnumProperty(name="Type", description="Linkage type", items=linktype, default='Crack')
    
    amfc = bpy.props.FloatProperty(default = 1.0, name = "")
    amfe = bpy.props.FloatProperty(default = 0.6, name = "")
    dlen = bpy.props.FloatProperty(default = 2, name = "")
    dhyd = bpy.props.FloatProperty(default = 0.1, name = "")
    dcs = bpy.props.FloatProperty(default = 0.1, name = "")
    dsr = bpy.props.FloatProperty(default = 0.0009, name = "")
    dlc = bpy.props.FloatProperty(default = 1.0, name = "")
    dhtc = bpy.props.FloatProperty(default = 0.772, name = "")
    dmtc = bpy.props.FloatProperty(default = 0.0001, name = "")
    
    def init(self, context):
        self.inputs.new('EnViCAirSocket', 'Node 1')
        self.inputs.new('EnViCAirSocket', 'Node 2')
        self.outputs.new('NodeSocket', 'Schedule')
        self.outputs.new('EnViCAirSocket', 'Node 1')
        self.outputs.new('EnViCAirSocket', 'Node 2')
    
    def update(self):
        try:
            lsocknames = ('Node 1', 'Node 2')
            for ins in [insock for insock in self.inputs if insock.name in lsocknames]:
                self.outputs[ins.name].hide = True if ins.is_linked else False
            for outs in [outsock for outsock in self.outputs if outsock.name in lsocknames]:
                self.inputs[outs.name].hide = True if outs.is_linked else False
        except:
            pass
         
    def draw_buttons(self, context, layout):
        layout.prop(self, 'linktypeprop')
        if self.linktypeprop == "Crack":
            row = layout.row()
            row.label("Coefficient:")
            row.prop(self, 'amfc')
            row = layout.row()
            row.label("Exponent:")
            row.prop(self, 'amfe')
        if self.linktypeprop == "Duct":
            row = layout.row()
            row.label("Length:")
            row.prop(self, 'dlen')
            row = layout.row()
            row.label("Hydraulic diameter:")
            row.prop(self, 'dhyd')
            row = layout.row()
            row.label("Cross Section:")
            row.prop(self, 'dcs')
            row = layout.row()
            row.label("Surface Roughness:")
            row.prop(self, 'dsr')
            row = layout.row()
            row.label("Loss coefficient:")
            row.prop(self, 'dlc')
            row = layout.row()
            row.label("U-Factor:")
            row.prop(self, 'dhtc')
            row = layout.row()
            row.label("Moisture coefficient:")
            row.prop(self, 'dmtc')

class EnViExtNode(bpy.types.Node, EnViNodes):
    '''Node describing a linkage component'''
    bl_idname = 'EnViExt'
    bl_label = 'Envi External Node'
    bl_icon = 'SOUND'

    height = bpy.props.FloatProperty(default = 1.0)
    azimuth = bpy.props.FloatProperty(default = 30)
    
    def init(self, context):
        self.inputs.new('EnViSAirSocket', 'External')
        self.outputs.new('EnViSAirSocket', 'External')    
        
    def draw_buttons(self, context, layout):
        layout.prop(self, 'linktypeprop')
        if self.linktypeprop == "Crack":
            layout.prop(self, 'amfc')
            layout.prop(self, 'amfe')

class EnViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'EnViN'
        
envinode_categories = [
        # identifier, label, items list
        EnViNodeCategory("ZoneNodes", "Zone Nodes", items=[NodeItem("EnViZone", label="Zone Node")]),
        EnViNodeCategory("SLinkNodes", "Surface Link Nodes", items=[
            NodeItem("EnViSLink", label="Surface Link Node")]),
        EnViNodeCategory("CLinkNodes", "Component Link Nodes", items=[
            NodeItem("EnViCLink", label="Component Link Node")]),
        EnViNodeCategory("PlantNodes", "Plant Nodes", items=[
            NodeItem("EnViFan", label="EnVi fan node")])]