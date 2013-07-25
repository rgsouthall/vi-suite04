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
from bpy_types import NodeTree, Node, NodeSocket

class ViNetwork(NodeTree):
    '''A node tree for the creation of EnVi advanced ventilation networks.'''
    bl_idname = 'ViN'
    bl_label = 'Vi Network'
    bl_icon = 'NODETREE'
    nodetypes = {}
    
class ViNodes:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ViN'
        
class ViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ViN'
        
class ViNode(Node, ViNodes):
    '''Node describing a LiVi lighting analysis'''
    bl_idname = 'LiViN'
    bl_label = 'LiVi Analysis'
    bl_icon = 'LAMP'
    
    analysistype = [(0, "Lighting", "LiVi Radiance Calculation"), (1, "Energy", "EnVi EnergyPlus Calculation"), (2, "Solar", "Sun Path Visualisation"), (3, "Wind", "Wind Rose Visualisation"), (4, "Shadow", "Shadow Study")]
    lanalysistype = [(0, "Illuminance", "Lux Calculation"), (1, "Irradiance", "W/m"+ u'\u00b2' + " Calculation"), \
    (2, "daylight Factor", "DF (%) Calculation"), (3, "Annual Light Exposure", "LuxHours Calculation"), (4, "Annual Radiation Exposure", "kWh/m"+ u'\u00b2' + " Calculation"), (5, "Daylight Availability", "DA (%) Calculation"), \
    (6, "Glare", "Glare Calculation"), (7, "BREEAM", "BREEAM HEA1 calculation"), (8, "LEED", "LEED EQ8.1 calculation"), (9, "Green Star", "Green Star Calculation")] 
    
    buildtype = [(0, "School", "School lighting standard"), (1, "Residential", "Residential lighting standard")]
    
    analysismenu = bpy.props.EnumProperty(name="Analysis Type", description="Type of VI-Suite analysis", items=analysistype, default=0)
    buildmenu = bpy.props.EnumProperty(name="Build Type", description="Type of building", items=buildtype, default=0)
    
#    fname = bpy.props.StringProperty(default = "", name = "")
#    feff = bpy.props.FloatProperty(default = 0.7, name = "")
#    fpr = bpy.props.FloatProperty(default = 600.0, name = "")
#    fmfr = bpy.props.FloatProperty(default = 1.9, name = "")
#    fmeff = bpy.props.FloatProperty(default = 0.9, name = "")
#    fmaf = bpy.props.FloatProperty(default = 1.0, name = "")
    
    def init(self, context):
        pass
#        self.inputs.new('EnViCAirSocket', 'Extract from')
#        self.inputs.new('EnViCAirSocket', 'Supply to')
#        self.outputs.new('NodeSocket', 'Schedule')
#        self.outputs.new('EnViCAirSocket', 'Extract from')
#        self.outputs.new('EnViCAirSocket', 'Supply to')
            
#    def update(self):
#        try:
#            fsocknames = ('Extract from', 'Supply to')
#            for ins in [insock for insock in self.inputs if insock.name in fsocknames]:
#                self.outputs[ins.name].hide = True if ins.is_linked else False
#            for outs in [outsock for outsock in self.outputs if outsock.name in fsocknames]:
#                self.inputs[outs.name].hide = True if outs.is_linked else False
#        except:
#            pass
                
    def draw_buttons(self, context, layout):
        layout.prop(self, 'analysismenu')
        if self.analysismenu == 7:
            row = layout.row()
            row.label("Name:")
            row.prop(self, 'buildtype')