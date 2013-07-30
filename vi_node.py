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


import bpy, bpy_extras, glob, os, inspect
from nodeitems_utils import NodeCategory, NodeItem



class ViNetwork(bpy.types.NodeTree):
    '''A node tree for VI-Suite analysis.'''
    bl_idname = 'ViN'
    bl_label = 'Vi Network'
    bl_icon = 'NODETREE'
    
class ViNodes:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ViN'
        
class ViLiNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite analysis type'''
    bl_idname = 'ViLiNode'
    bl_label = 'VI Lighting Analysis'
    bl_icon = 'LAMP'
    
#    analysistype = [('0', "Lighting", "LiVi Radiance Calculation"), ('1', "Energy", "EnVi EnergyPlus Calculation"), ('2', "Solar", "Sun Path Visualisation"), ('3', "Wind", "Wind Rose Visualisation"), ('4', "Shadow", "Shadow Study")]
    analysistype = [('0', "Illuminance", "Lux Calculation"), ('1', "Irradiance", "W/m"+ u'\u00b2' + " Calculation"), ('2', "Daylight Factor", "DF (%) Calculation"),]     

    animtype = [('0', "Static", "Simple static analysis"), ('1', "Time", "Animated time analysis"), ('2', "Geometry", "Animated time analysis"), ('3', "Material", "Animated time analysis"), ('4', "Lights", "Animated time analysis")]
    dfanimtype = [('0', "Static", "Simple static analysis"), ('1', "Geometry", "Animated time analysis"), ('2', "Material", "Animated time analysis"), ('3', "Lights", "Animated time analysis")]

    skytype = [    ("0", "Sunny", "CIE Sunny Sky description"),
                   ("1", "Partly Coudy", "CIE Sunny Sky description"),
                   ("2", "Coudy", "CIE Partly Cloudy Sky description"),
                   ("3", "DF Sky", "Daylight Factor Sky description"),
                   ("4", "HDR Sky", "HDR file sky"),
                   ("5", "Radiance Sky", "Radiance file sky"),
                   ("6", "None", "No Sky")]
    
#    analysismenu = bpy.props.EnumProperty(name="", description="Type of VI-Suite analysis", items = analysistype, default = '0')
    analysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = analysistype, default = '0')
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = '0')
    dfanimmenu = bpy.props.EnumProperty(name="", description="Animation type", items=dfanimtype, default = '0')
    skymenu = bpy.props.EnumProperty(items=skytype, name="", description="Specify the type of sky for the simulation", default="0")
    shour = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=24, default=12)
    sdoy = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=365, default=1)
    ehour = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=24, default=12)
    edoy = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=365, default=1)
    daysav = bpy.props.BoolProperty(name="", description="Enable daylight saving clock", default=False)
    lati = bpy.props.FloatProperty(name="", description="Site Latitude", min=-90, max=90, default=52)
    longi = bpy.props.FloatProperty(name="", description="Site Longitude relative to local meridian", min=-15, max=15, default=0) 
    cpoint = bpy.props.EnumProperty(items=[("0", "Faces", "Export faces for calculation points"),("1", "Vertices", "Export vertices for calculation points"), ],
            name="", description="Specify the calculation point geometry", default="1")
    
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
            name="", description="Custom Radiance simulation parameters", default="")
            
    interval = bpy.props.FloatProperty(name="", description="Site Latitude", min=0.25, max=24, default=1)
#    sday28 = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=28, default=1)
#    sday30 = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=30, default=1)
#    sday31 = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=31, default=1)
#    smonth = bpy.props.IntProperty(name="", description="Month of simulation", min=1, max=12, default=1)
    
    def init(self, context):
        self.outputs.new('ViLiWResOut', 'Out')
    
    def update(self):
            if self.outputs['Out'].is_linked:
                self.analysismenu = '1'
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Analysis type:")
        row.prop(self, 'analysismenu')
        row = layout.row()
        if self.analysismenu in ('0', '1'):
            row.label("Animation:")
            row.prop(self, 'animmenu')
            if self.animmenu in ('0', '2', '3', '4'):
                row = layout.row() 
                row.label("Sky type:")
                row.prop(self, 'skymenu')
                if self.skymenu in ('0', '1', '2'):
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
                    row.label("Hour:")
                    row.prop(self, 'shour')
                    row = layout.row() 
                    row.label("Day of year:")
                    row.prop(self, 'sdoy')
            else:
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
                row = layout.row() 
                row.label("End hour:")
                row.prop(self, 'ehour')
                row = layout.row() 
                row.label("End day of year:")
                row.prop(self, 'edoy')
                row = layout.row() 
                row.label("Interval (hours):")
                row.prop(self, 'interval')
        else:
            row = layout.row() 
            row.label("Animation:")
            row.prop(self, 'dfanimmenu')
        
        row = layout.row()
        row.label("Calculation points:")
        row.prop(self, 'cpoint')
        row = layout.row()
        row.label("Accuracy:")
        row.prop(self, 'simacc')
        if self.simacc == '3':
           row = layout.row()
           row.label("Radiance parameters:")
           row.prop(self, 'cusacc') 
        row = layout.row()
        row.operator("node.preview", text = 'Preview')
        row.operator("node.calculate", text = 'Calculate')
        
        

class ViLiCBNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite climate based lighting node'''
    bl_idname = 'ViLiCBNode'
    bl_label = 'VI Climate Based Daylighting Analysis'
    bl_icon = 'LAMP'

    analysistype = [('0', "Annual Light Exposure", "LuxHours Calculation"), ('1', "Annual Radiation Exposure", "kWh/m"+ u'\u00b2' + " Calculation"), ('2', "Daylight Availability", "DA (%) Calculation")]
    analysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = analysistype, default = '0')
    animtype = [('0', "Static", "Simple static analysis"), ('1', "Geometry", "Animated time analysis"), ('2', "Material", "Animated time analysis"), ('3', "Lights", "Animated time analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = '0')

    simacc = bpy.props.EnumProperty(items=[("0", "Low", "Low accuracy and high speed (preview)"),("1", "Medium", "Medium speed and accuracy"), ("2", "High", "High but slow accuracy"),("3", "Custom", "Edit Radiance parameters"), ],
            name="", description="Simulation accuracy", default="0")
    cusacc = bpy.props.StringProperty(
            name="", description="Custom Radiance simulation parameters", default="")
    epwname = bpy.props.StringProperty(
            name="", description="Name of the EnergyPlus weather file", default="")
#    epwsel = EPWSelect()
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Analysis Type:")
        row.prop(self, 'analysismenu')
        row = layout.row()
        row.label('EPW file:')
        row.operator(NODE_OT_epwselect.bl_idname, text = 'Select EPW').nodename = self.name
        row = layout.row()
        row.prop(self, "epwname")        
        row = layout.row()
        row.label('Animation:')
        row.prop(self, "animmenu")
        row = layout.row()
        row.label("Accuracy:")
        row.prop(self, 'simacc')
        if self.simacc == '3':
           row = layout.row()
           row.label("Radiance parameters:")
           row.prop(self, 'cusacc') 
        row = layout.row()
        row.operator("node.preview", text = 'Preview')
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
        row.operator("node.preview", text = 'Preview')
        row.operator("node.calculate", text = 'Calculate').nodename = self.name
        
class ViSPNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite sun path'''
    bl_idname = 'ViSPNode'
    bl_label = 'VI Sun Path'
    bl_icon = 'LAMP'
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate').nodename = self.name    


class ViSSNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite sun path'''
    bl_idname = 'ViSPNode'
    bl_label = 'VI Sun Path'
    bl_icon = 'LAMP'
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate').nodename = self.name

class ViWRNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite wind rose generator'''
    bl_idname = 'ViWRNode'
    bl_label = 'VI Wind Rose'
    bl_icon = 'LAMP'

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate').nodename = self.name
        
class ViGNode(bpy.types.Node, ViNodes):
    '''Node describing a glare analysis'''
    bl_idname = 'ViGNode'
    bl_label = 'VI Glare'
    bl_icon = 'LAMP'

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate').nodename = self.name
        
class ViEPNode(bpy.types.Node, ViNodes):
    '''Node describing a glare analysis'''
    bl_idname = 'ViEPNode'
    bl_label = 'VI EnergyPLus analysis'
    bl_icon = 'LAMP'    
    
    envi_pregeo = bpy.props.BoolProperty(name="Export geometry", description="EnVi geometry export flag", default = True)
    envi_location = bpy.props.StringProperty(name="Project name/location", description="Identifier for this project", default="")
    envi_terrain = bpy.props.EnumProperty(
            items=[("0", "City", "Towns, city outskirts, centre of large cities"),
                   ("1", "Urban", "Urban, Industrial, Forest"),
                    ("2", "Suburbs", "Rough, Wooded Country, Suburbs"),
                    ("3", "Country", "Flat, Open Country"),
                    ("4", "Ocean", "Ocean, very flat country"),
                   ],
            name="",
            description="Specify the surrounding terrain",
            default="0")

    addonpath = os.path.dirname(inspect.getfile(inspect.currentframe()))
    matpath = addonpath+'/EPFiles/Materials/Materials.data'
    epwpath = addonpath+'/EPFiles/Weather/'
    weatherlist = [((filename, os.path.basename(filename).strip('.epw').split(".")[0], 'Weather Location')) for filename in glob.glob(epwpath+"/*.epw")]
    envi_weather = bpy.props.EnumProperty(items = weatherlist, name="Weather location", description="Weather for this project")
    
    def init(self, context):
        pass
    
    
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.geoexport", text="Geometry Export")
        if self.envi_pregeo == True:
            row = layout.row()
            row.prop(self, "envi_location")
            row = layout.row()
            row.prop(self, "envi_weather")
            row = layout.row()
            row.label(text = 'Terrain:')
            col = row.column()
            col.prop(self, "envi_terrain")
        row = layout.row()

        row.operator("node.calculate", text = 'Calculate').nodename = self.name
        
class ViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ViN'

vinodecat = [NodeItem("ViLiNode", label="VI-Suite lighting analysis"), NodeItem("ViLiCNode", label="VI-Suite lighting compliance"), NodeItem("ViLiCBNode", label="VI-Suite climate based lighting"),\
             NodeItem("ViSPNode", label="VI-Suite sun path"), NodeItem("ViSSNode", label="VI-Suite shadow study"), NodeItem("ViWRNode", label="VI-Suite wind rose"), NodeItem("ViGNode", label="VI-Suite glare"), NodeItem("ViEPNode", label="VI-Suite energy")] 

# identifier, label, items list
vinode_categories = [ViNodeCategory("Analysis", "Analysis Nodes", items=vinodecat)] 
        
               
class ViLiWResOut(bpy.types.NodeSocket):
    '''LiVi irradiance out socket'''
    bl_idname = 'LiViWOut'
    bl_label = 'LiVi W/m2 out'
    
    def draw(self, context, layout, node, text):
        layout.label(text)
        
    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class NODE_OT_preview(bpy.types.Operator):
    bl_idname = "node.preview"
    bl_label = "Radiance Preview"
    
    def execute(self, context):
        return {'FINISHED'}

class NODE_OT_calculate(bpy.types.Operator):
    bl_idname = "node.calculate"
    bl_label = "Radiance Export and Simulation"
    nodename = bpy.props.StringProperty()
    
    def execute(self, context):
        return {'FINISHED'}

class NODE_OT_geoexport(bpy.types.Operator):
    bl_idname = "node.geoexport"
    bl_label = "Radiance Export and Simulation"
    nodename = bpy.props.StringProperty()
    
    def execute(self, context):
        return {'FINISHED'}
        
class NODE_OT_epwselect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "node.epwselect"
    bl_label = "Select EPW file"
    bl_description = "Select the EnergyPlus weather file"
    filename = ""
    filename_ext = ".HDR;.hdr;.epw;.EPW;"
    filter_glob = bpy.props.StringProperty(default="*.HDR;*.hdr;*.epw;*.EPW;", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodename = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import EPW File with FileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("epw", "EPW", "HDR", "hdr"):
            bpy.data.node_groups['NodeTree'].nodes[self.nodename].epwname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the EPW filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}