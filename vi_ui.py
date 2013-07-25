import bpy
scene = bpy.context.scene

class SCENE_LiVi_Export_UI(bpy.types.Panel):
    bl_label = "VI-Suite"    
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context): 
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.label(text = 'Analysis:')
        row.prop(scene, "vi_suite_analysis") 
        row = layout.row()
        
        if scene.visuite_analysis == 0:
            if scene.livi_anim != 1:
                col = row.column()
                col.label(text = 'Period Type:')
                row.prop(scene, "livi_export_time_type")
            
                if scene.livi_export_time_type == "0":
                    row = layout.row()
                    col = row.column()
                    col.label(text = 'Sky type:')
                   
                    row.prop(scene, "livi_export_sky_type")
                    sky_type = int(scene.livi_export_sky_type)
                   
                    if sky_type < 3:
                        row = layout.row()
                        row.prop(scene, "visuite_export_latitude")
                        row.prop(scene, "visuite_export_longitude")
                        row = layout.row()
                        row.prop(scene, "livi_export_standard_meridian")
                        row = layout.row()
                        if int(scene.livi_anim) != "1":
                            row.label(text = 'Time:')
                        else:
                            row.label(text = 'Start:')
                        row.prop(scene, "livi_export_start_hour")
                        if scene.livi_export_start_month == "2":
                            row.prop(scene, "livi_export_start_day28")
                        elif scene.livi_export_start_month in (4, 6, 9, 11):
                            row.prop(scene, "livi_export_start_day30")
                        else:
                            row.prop(scene, "livi_export_start_day")
                        row.prop(scene, "livi_export_start_month")    
                        
                    elif sky_type == 4:
                        row = layout.row()
                        row.operator(SCENE_VISuite_HDR_Select.bl_idname, text="Select HDR File")
                        row.prop(scene, "visuite_export_hdr_name")
                else:
                    row = layout.row()
                    row.operator(SCENE_LiVi_EPW_Select.bl_idname, text="Select EPW File")
                    row.prop(scene, "visuite_export_epw_name")
        
        if scene.visuite_analysis in (1, 2):
            
        if scene.visuite_analysis == 3:
            
        if scene.visuite_analysis == 4:
            
        
