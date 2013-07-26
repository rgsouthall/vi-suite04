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
    
    analysismenu = bpy.props.EnumProperty(name="", description="Type of VI-Suite analysis", items = analysistype, default = '0')
    lanalysismenu = bpy.props.EnumProperty(name="", description="Type of Lighting analysis", items = lanalysistype, default = '0')
    buildmenu = bpy.props.EnumProperty(name="", description="Type of building", items=buildtype, default = '0')
    animmenu = bpy.props.EnumProperty(name="", description="Type of building", items=animtype, default = '0')
    
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
                row.prop(self, 'animmenu')
                if self.animmenu == '0':
                    row = layout.row()    
            elif self.lanalysismenu == '7':
                row = layout.row()
                row.label("Build type:")
                row.prop(self, 'buildmenu')
            
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