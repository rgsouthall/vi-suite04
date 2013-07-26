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


import bpy, nodeitems_utils 
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
        
class ViNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite analysis type'''
    bl_idname = 'ViNode'
    bl_label = 'VI Analysis'
    bl_icon = 'LAMP'
    
    analysistype = [('0', "Lighting", "LiVi Radiance Calculation"), ('1', "Energy", "EnVi EnergyPlus Calculation"), ('2', "Solar", "Sun Path Visualisation"), ('3', "Wind", "Wind Rose Visualisation"), ('4', "Shadow", "Shadow Study")]
    lanalysistype = [('0', "Illuminance", "Lux Calculation"), ('1', "Irradiance", "W/m"+ u'\u00b2' + " Calculation"), \
    ('2', "daylight Factor", "DF (%) Calculation"), ('3', "Annual Light Exposure", "LuxHours Calculation"), ('4', "Annual Radiation Exposure", "kWh/m"+ u'\u00b2' + " Calculation"), ('5', "Daylight Availability", "DA (%) Calculation"), \
    ('6', "Glare", "Glare Calculation"), ('7', "BREEAM", "BREEAM HEA1 calculation"), ('8', "LEED", "LEED EQ8.1 calculation"), ('9', "Green Star", "Green Star Calculation")] 
    
    buildtype = [('0', "School", "School lighting standard"), ('1', "Residential", "Residential lighting standard")]
    animtype = [('0', "Static", "Simple static analysis"), ('1', "Animated", "Animated analysis")]
    skytype = [    ("0", "Sunny", "CIE Sunny Sky description"),
                   ("1", "Partly Coudy", "CIE Sunny Sky description"),
                   ("2", "Coudy", "CIE Partly Cloudy Sky description"),
                   ("3", "DF Sky", "Daylight Factor Sky description"),
                   ("4", "HDR Sky", "HDR file sky"),
                   ("5", "Radiance Sky", "Radiance file sky"),
                   ("6", "None", "No Sky")]
    
    analysismenu = bpy.props.EnumProperty(name="", description="Type of VI-Suite analysis", items = analysistype, default = '0')
    lanalysismenu = bpy.props.EnumProperty(name="", description="Type of Lighting analysis", items = lanalysistype, default = '0')
    buildmenu = bpy.props.EnumProperty(name="", description="Type of building", items=buildtype, default = '0')
    animmenu = bpy.props.EnumProperty(name="", description="Type of building", items=animtype, default = '0')
    skymenu = bpy.props.EnumProperty(items=skytype, name="", description="Specify the type of sky for the simulation", default="0")
    shour = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=24, default=12)
    sdoy = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=365, default=1)
    daysav = bpy.props.BoolProperty(name="", description="Enable daylight saving clock", default=False)
    lati = bpy.props.FloatProperty(name="", description="Site Latitude", min=-90, max=90, default=52)
    longi = bpy.props.FloatProperty(name="", description="Site Longitude relative to local meridian", min=-15, max=15, default=0) 
    cpoint = bpy.props.EnumProperty(items=[("0", "Faces", "Export faces for calculation points"),("1", "Vertices", "Export vertices for calculation points"), ],
            name="", description="Specify the calculation point geometry", default="1")
    
    stamer = bpy.props.EnumProperty(
            items=[("0", "YST", ""),("1", "PST", ""),("2", "MST", ""),("3", "CST", ""),("4", "EST", ""),("GMT", "GMT", ""),("6", "CET", ""),("7", "EET", ""),
                   ("8", "AST", ""),("9", "GST", ""),("10", "IST", ""),("11", "JST", ""),("12", "NZST", ""), ],
            name="Meridian", description="Specify the local meridian", default="GMT")
    
    summer = bpy.props.EnumProperty(
            items=[("0", "YDT", ""),("1", "PDT", ""),("2", "MDT", ""),("3", "CDT", ""),("4", "EDT", ""),("BST", "BST", ""),("6", "CEST", ""),
                   ("7", "EEST", ""),("8", "ADT", ""),("9", "GDT", ""),("10", "IDT", ""),("11", "JDT", ""),("12", "NZDT", ""),],
            name="", description="Specify the local Summertime meridian", default="BST")

#    sday28 = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=28, default=1)
#    sday30 = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=30, default=1)
#    sday31 = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=31, default=1)
#    smonth = bpy.props.IntProperty(name="", description="Month of simulation", min=1, max=12, default=1)
    
#    def init(self, context):
#        print('hi')
                
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Analysis type:")
        row.prop(self, 'analysismenu')
        if self.analysismenu == '0':
            row = layout.row()
            row.label("Lighting analysis type:")
            row.prop(self, 'lanalysismenu')
            row = layout.row()
            if self.lanalysismenu in ('0', '1'):
                row.label("Animation:")
                row.prop(self, 'animmenu')
                if self.animmenu == '0':
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
                    
            elif self.lanalysismenu == '7':
                row = layout.row()
                row.label("Build type:")
                row.prop(self, 'buildmenu')
            
            if self.lanalysismenu in ('0', '1', '2', '3', '4', '5'):
                row = layout.row()
                row.label("Calculation points:")
                row.prop(self, 'cpoint')
                
class ViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ViN'

vinode_categories = [
        # identifier, label, items list
        ViNodeCategory("Analysis", "Analysis Node", items=[
            NodeItem("ViNode", label="VI-Suite analysis node")
            ]),]        

def vinodegen():
    if not hasattr(bpy.types, 'ViN'):
        bpy.utils.register_class(ViNetwork)
        bpy.utils.register_class(ViNode)
        bpy.ops.node.new_node_tree(type = 'ViN', name = 'Vi Network')
        
        
        
        try:
            nodeitems_utils.unregister_node_categories("Vi Nodes")
            nodeitems_utils.register_node_categories("Vi Nodes", vinode_categories)
        except:
            nodeitems_utils.register_node_categories("Vi Nodes", vinode_categories)