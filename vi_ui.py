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
            row.prop(view, "show_only_render")
            row = layout.row()
            row.prop(scene, "li_disp_3d")
            if int(context.scene.li_disp_3d) == 1:
                row.prop(scene, "li_disp_3dlevel")
            row = layout.row()
            row.operator("view3d.lidisplay", text="Radiance Display")
#            try:
#                if lexport.node.rp_display == False:
#                    pass
#                else:
            if context.mode == "OBJECT":
                row = layout.row()
                row.label(text="{:-<48}".format("Point visualisation "))
                row = layout.row()
                row.label(text = "Enable:")
                row.prop(scene, "li_display_rp")
                row = layout.row()
                row.label(text = "Selected only:")
                row.prop(scene, "li_display_sel_only")
                row = layout.row()
                row.label(text = "Font size:")
                row.prop(scene, "li_display_rp_fs")
                row = layout.row()
                row.label(text="{:-<60}".format(""))
#            except:
#                pass

class RadMatPanel(bpy.types.Panel):
    bl_label = "LiVi Radiance material"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    
    @classmethod 
    def poll(cls, context): 
        return context.material 

    def draw(self, context):
        cm = context.material
        layout = self.layout
        row = layout.row()
        row.label('Radiance type:')
        if cm.use_shadeless == True:
            row.label('Shadeless')
        elif cm.emit > 0:
            row.label('Emission')
            row = layout.row()
            row.label('RGB emission:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(cm.emit * cm.diffuse_color[0], cm.emit * cm.diffuse_color[1], cm.emit * cm.diffuse_color[2]))
        elif cm.raytrace_mirror.use == True and cm.raytrace_mirror.reflect_factor > 0.99:
            row.label('Mirror')
            row = layout.row()
            row.label('RGB refelectance:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(*cm.mirror_color))
        elif cm.use_transparency == True and cm.transparency_method == 'RAYTRACE' and cm.alpha < 1.0 and cm.translucency == 0:
            row.label('Glass')
            row = layout.row()
            row.label('RGB transparency:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format((1.0 - cm.alpha)*cm.diffuse_color[0], (1.0 - cm.alpha)*cm.diffuse_color[1], (1.0 - cm.alpha)*cm.diffuse_color[2]))
            row = layout.row()
            row.label('IOR:')
            row.label('{:.2f}'.format(cm.raytrace_transparency.ior))
        elif cm.use_transparency == True and cm.transparency_method == 'RAYTRACE' and cm.alpha < 1.0 and cm.translucency > 0:
            row.label('Translucent')
            row = layout.row()
            row.label('RGB transmission:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(*cm.diffuse_color))
            row = layout.row()
            row.label('Specularity')
            row.label('{:.2f}'.format(cm.specular_intensity))
            row = layout.row()
            row.label('Roughness:') 
            row.label('{:.2f}'.format(1.0 - cm.specular_hardness/511.0))
            row = layout.row()
            row.label('Transmissivity')
            row.label('{:.2f}'.format(1.0 - cm.alpha))
            row = layout.row()
            row.label('Transmitted Specular')
            row.label('{:.2f}'.format(1.0 - cm.translucency))
        elif cm.raytrace_mirror.use == True and cm.raytrace_mirror.reflect_factor <= 0.99:
            row.label('Metal')
            row = layout.row()
            row.label('RGB refelectance:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(*cm.diffuse_color))
            row = layout.row()
            row.label('Specularity:')
            row.label('{:.2f}'.format(cm.specular_intensity))
            row = layout.row()
            row.label('Roughness:')
            row.label('{:.2f}'.format(1.0-cm.specular_hardness/511.0))
        else:
            row.label('Plastic')
            row = layout.row()
            row.label('RGB refelectance:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(*cm.diffuse_color))
            row = layout.row()
            row.label('Specularity:')
            row.label('{:.2f}'.format(cm.specular_intensity))
            row = layout.row()
            row.label('Roughness:')
            row.label('{:.2f}'.format(1.0-cm.specular_hardness/511.0))
            
     
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
        
