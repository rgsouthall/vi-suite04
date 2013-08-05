import bpy

#from . import vi_operators
#scene = bpy.context.scene

#class ViNodeGen(bpy.types.Operator):
#    '''Initial node network registration and creation'''
#    bl_idname = "scene.ving"
#    bl_label = "Generate VI Nodes"
#    bl_options = {'REGISTER', 'UNDO'}
#    bl_register = True
#    bl_undo = True
#    
#    def invoke(self, context, event):
#        vi_node.vinodegen()
#        return{'FINISHED'}
    
class Vi3DPanel(bpy.types.Panel):
    '''VI-Suite 3D view panel'''
    bl_label = "VI-Suite"    
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"    

    def draw(self, context):
        view = context.space_data
        scene = context.scene
          
        if scene.li_disp_panel == 1:
            layout = self.layout
            row = layout.row()
            row.operator("view3d.lidisplay", text="Radiance Display")
            row.prop(view, "show_only_render")
            row.prop(scene, "li_disp_3d")
            if int(context.scene.li_disp_3d) == 1:
                row = layout.row()
                row.prop(scene, "li_disp_3dlevel")
#            try:
#                if lexport.node.rp_display == False:
#                    pass
#                else:
            if context.mode == "OBJECT":
                row = layout.row()
                row.label(text="{:-<48}".format("Point visualisation "))
                row = layout.row()
                row.prop(scene, "li_display_respoints")
                row.prop(scene, "li_display_sel_only")
                row.prop(scene, "li_display_rp_fs")
                row = layout.row()
                row.label(text="{:-<60}".format(""))
#            except:
#                pass
      
class IESPanel(bpy.types.Panel):
    bl_label = "LiVi IES file"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        if context.lamp or 'lightarray' in context.object.name:
            return True

    def draw(self, context):
        layout = self.layout
        lamp = bpy.context.active_object
        row = layout.row()
        row.operator("livi.ies_select") 
        row.prop(lamp, "ies_name")
        row = layout.row()
        row.label('IES Dimension:')
        row.prop(lamp, "ies_unit")
        row = layout.row()
        row.label('IES Strength:')
        row.prop(lamp, "ies_strength")
        row = layout.row()
        row.prop(lamp, "ies_colour")
        
