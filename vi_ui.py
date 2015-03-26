import bpy
from collections import OrderedDict
from .vi_func import newrow, enresprops

from .envi_mat import envi_materials, envi_constructions
envi_mats = envi_materials()
envi_cons = envi_constructions()

class Vi3DPanel(bpy.types.Panel):
    '''VI-Suite 3D view panel'''
    bl_label = "VI-Suite Display"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
#        print(self.resat)
        scene = context.scene
#        if scene.vi_display == 1:
        if scene['viparams']['vidisp']:
            view = context.space_data
            layout = self.layout

            if scene['viparams']['vidisp'] == 'wr':            
#            if scene.wr_disp_panel == 1:
                newrow(layout, 'Legend', scene, "vi_leg_display")

#            elif scene.sp_disp_panel == 1:
            elif scene['viparams']['vidisp'] == 'sp':
                for i in (("Day of year:", "solday"), ("Time of day:", "solhour"), ("Sunpath scale:", "soldistance"), ("Display hours:", "hourdisp")):
                    newrow(layout, i[0], scene, i[1])
                if scene.hourdisp:
                    for i in (("Font size:", "vi_display_rp_fs"), ("Font colour:", "vi_display_rp_fc"), ("Font shadow:", "vi_display_rp_fsh")):
                        newrow(layout, i[0], scene, i[1])

#            elif scene.ss_disp_panel in (1,2) or scene.li_disp_panel in (1,2):
            elif scene['viparams']['vidisp'] in ('ss', 'li', 'sspanel', 'lipanel', 'licpanel'):
                row = layout.row()
                row.prop(scene, "vi_disp_3d")
                if scene['viparams']['visimcontext'] == 'LiVi Compliance':
                    newrow(layout, 'Sky view:', scene, 'vi_disp_sk')
                row = layout.row()
                row.operator("view3d.lidisplay", text="Shadow Display") if scene['viparams']['visimcontext'] == 'Shadow' else row.operator("view3d.lidisplay", text="Radiance Display")

#                if scene.ss_disp_panel == 2 or scene.li_disp_panel == 2:
                if scene['viparams']['vidisp'] in ('sspanel', 'lipanel', 'licpanel'):
                    row = layout.row()
                    row.prop(view, "show_only_render")
                    newrow(layout, 'Legend', scene, "vi_leg_display")
                    if scene.vi_leg_display and not scene.ss_disp_panel:
                        newrow(layout, 'Legend max', scene, "vi_leg_max")
                        newrow(layout, 'Legend min.', scene, "vi_leg_min")
                    if context.active_object and context.active_object.type == 'MESH':
                        newrow(layout, 'Draw wire:', scene, 'vi_disp_wire')                    
                    if int(context.scene.vi_disp_3d) == 1:
                        newrow(layout, "3D Level", scene, "vi_disp_3dlevel")                        
                    newrow(layout, "Transparency", scene, "vi_disp_trans")

                    if context.mode != "EDIT":
                        row = layout.row()
                        row.label(text="{:-<48}".format("Point visualisation "))
                        propdict = OrderedDict([('Enable', "vi_display_rp"), ("Selected only:", "vi_display_sel_only"), ("Visible only:", "vi_display_vis_only"), ("Font size:", "vi_display_rp_fs"), ("Font colour:", "vi_display_rp_fc"), ("Font shadow:", "vi_display_rp_fsh"), ("Position offset:", "vi_display_rp_off")])
                        for prop in propdict.items():
                            newrow(layout, prop[0], scene, prop[1])
                        row = layout.row()
                        row.label(text="{:-<60}".format(""))

#                    if scene.lic_disp_panel == 1:  
                    if scene['viparams']['vidisp'] == 'licpanel':
                        propdict = OrderedDict([("Compliance Panel", "li_compliance"), ("Asessment organisation:", "li_assorg"), ("Assesment individiual:", "li_assind"), ("Job number:", "li_jobno"), ("Project name:", "li_projname")])
                        for prop in propdict.items():
                            newrow(layout, prop[0], scene, prop[1])
            
            elif scene['viparams']['vidisp'] in ('en', 'enpanel'):
                resnode = bpy.data.node_groups[scene['viparams']['resnode'].split('@')[1]].nodes[scene['viparams']['resnode'].split('@')[0]]
                aresdict = {"Temperature (degC)": "resat_disp", 'Wind Speed (m/s)': 'resaws_disp', 'Wind Direction (deg)': 'resawd_disp', 
                            'Humidity (%)': 'resah_disp', 'Direct Solar (W/m^2)': 'resasb_disp', 'Diffuse Solar (W/m^2)': 'resasd_disp'}
                zresdict = {"Temperature (degC)": "reszt_disp", 'Humidity (%)': 'reszh_disp', 'Heating (W)': 'reszh_disp', 'Cooling (W)': 'reszc_disp'}
                for ri, rname in enumerate([rname[1] for rname in resnode['resdict'].values() if rname[0] == 'Climate']):
                    if ri == 0:                    
                        row = layout.row()
                        row.label(text = 'Ambient')                    
                    if not ri%2:
                        row = layout.row()                            
                    if rname in aresdict:
                        row.prop(scene, aresdict[rname])
                
                for ri, rname in enumerate(set([rname[1] for rname in resnode['resdict'].values() if rname[0][:3] == 'EN_' and rname[0][3:] in [o.name.upper() for o in bpy.data.objects]])):
                    if ri == 0:                    
                        row = layout.row()
                        row.label(text = 'Zone')                    
                    if not ri%2:
                        row = layout.row()                            
                    if rname in zresdict:
                        row.prop(scene, zresdict[rname])
                row = layout.row()    
                row.operator("view3d.endisplay", text="EnVi Display")
            
            newrow(layout, 'Display active', scene, 'vi_display')

class VIMatPanel(bpy.types.Panel):
    bl_label = "VI-Suite Material"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.material

    def draw(self, context):
        cm, scene = context.material, context.scene
        layout = self.layout
        newrow(layout, 'Material type', cm, "mattype")
        if cm.mattype != '3':
            if scene.get('liparams') and scene['liparams'].get('compnode'):
                connode = bpy.data.node_groups[scene['liparams']['compnode'].split('@')[1]].nodes[scene['liparams']['compnode'].split('@')[0]]
                if cm.mattype == '1':
                    if connode.analysismenu == '0':
                        if connode.bambuildmenu == '2':
                            newrow(layout, "Space type:", cm, 'hspacemenu')
                        elif connode.bambuildmenu == '3':
                            newrow(layout, "Space type:", cm, 'brspacemenu')
                            if cm.brspacemenu == '2':
                                row = layout.row()
                                row.prop(cm, 'gl_roof')
                        elif connode.bambuildmenu == '4':
                            newrow(layout, "Space type:", cm, 'respacemenu')
                    elif connode.analysismenu == '1':
                        newrow(layout, "Space type:", cm, 'crspacemenu')
    
            row = layout.row()
            row.label('LiVi Radiance type:')
            row.prop(cm, 'radmatmenu')
            row = layout.row()
            for prop in cm.radmatdict[cm.radmatmenu]:
                if prop:
                     row.prop(cm, prop)
                else:
                    row = layout.row()
            row = layout.row()
            row.label("-----------------------------------------")
            newrow(layout, "EnVi Construction Type:", cm, "envi_con_type")
            row = layout.row()
            if cm.envi_con_type not in ("Aperture", "Shading", "None"):
                newrow(layout, 'Intrazone Boundary', cm, "envi_boundary")
                newrow(layout, 'Airflow surface:', cm, "envi_afsurface")
                if not cm.envi_boundary and not cm.envi_afsurface:
                    newrow(layout, 'Thermal mass:', cm, "envi_thermalmass")
                newrow(layout, "Construction Make-up:", cm, "envi_con_makeup")
                if cm.envi_con_makeup == '1':
                    newrow(layout, "Outside layer:", cm, "envi_layero")
                    row = layout.row()
                    if cm.envi_layero == '1':
                        if cm.envi_con_type == "Window":
                            newrow(layout, "Glass Type:", cm, "envi_export_glasslist_lo")
                        elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                            newrow(layout, "Outer layer type:", cm, "envi_layeroto")
                            newrow(layout, "Outer layer material:", cm, ("envi_export_bricklist_lo", "envi_export_claddinglist_lo", "envi_export_concretelist_lo", "envi_export_metallist_lo", "envi_export_stonelist_lo", "envi_export_woodlist_lo", "envi_export_gaslist_lo", "envi_export_insulationlist_lo")[int(cm.envi_layeroto)])
                            newrow(layout, "Outer layer thickness:", cm, "envi_export_lo_thi")
    
                    elif cm.envi_layero == '2' and cm.envi_con_type != 'Window':
                        for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                            if end:
                                row.prop(cm, '{}{}'.format("envi_export_lo_", end))
                            else:
                                row = layout.row()
    
                    elif cm.envi_layero == '2' and cm.envi_con_type == 'Window':
                        newrow(layout, "Name:", cm, "envi_export_lo_name")
                        newrow(layout, "Optical data type:", cm, "envi_export_lo_odt")
                        newrow(layout, "Construction Make-up:", cm, "envi_export_lo_sds")
                        newrow(layout, "Translucent:", cm, "envi_export_lo_sdiff")
                        for end in (0, 'thi', 'tc', 0, 'stn', 'fsn', 'bsn', 0, 'vtn', 'fvrn', 'bvrn', 0, 'itn', 'fie', 'bie'):
                            if end:
                                row.prop(cm, '{}{}'.format("envi_export_lo_", end))
                            else:
                                row = layout.row()
    
                    if cm.envi_layero != '0':
                        row = layout.row()
                        row.label("----------------")
                        newrow(layout, "2nd layer:", cm, "envi_layer1")
                        row = layout.row()
                        if cm.envi_layer1 == '1':
                            if cm.envi_con_type == "Window":
                                row.label("Gas Type:")
                                row.prop(cm, ("envi_export_wgaslist_l1"))
                                row.prop(cm, "envi_export_l1_thi")
                            elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                row.label("2nd layer type:")
                                row.prop(cm, "envi_layer1to")
                                newrow(layout, "2nd layer material:", cm, ("envi_export_bricklist_l1", "envi_export_claddinglist_l1", "envi_export_concretelist_l1", "envi_export_metallist_l1", "envi_export_stonelist_l1", "envi_export_woodlist_l1", "envi_export_gaslist_l1", "envi_export_insulationlist_l1")[int(cm.envi_layer1to)])
                                newrow(layout, "2nd layer thickness:", cm, "envi_export_l1_thi")
                        
                        elif cm.envi_layer1 == '2' and cm.envi_con_type != 'Window':
                            for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                if end:
                                    row.prop(cm, '{}{}'.format("envi_export_l1_", end))
                                else:
                                    row = layout.row()
    
                        elif cm.envi_layer1 == '2' and cm.envi_con_type == 'Window':
                            newrow(layout, "Name:", cm, "envi_export_l1_name")
                            newrow(layout, "Gas Type:", cm, "envi_export_wgaslist_l1")
                            newrow(layout, "Gas thickness:", cm, "envi_export_l1_thi")
    
                        if cm.envi_layer1 != '0':
                            row = layout.row()
                            row.label("----------------")
                            row = layout.row()
                            row.label("3rd layer:")
                            row.prop(cm, "envi_layer2")
                            if cm.envi_layer2 == '1':
                                if cm.envi_con_type == "Window":
                                    newrow(layout, "Glass Type:", cm, ("envi_export_glasslist_l2"))
                                elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                    newrow(layout, "3rd layer type:", cm, "envi_layer2to")
                                    newrow(layout, "3rd layer material:", cm, ("envi_export_bricklist_l2", "envi_export_claddinglist_l2", "envi_export_concretelist_l2", "envi_export_metallist_l2", "envi_export_stonelist_l2", "envi_export_woodlist_l2", "envi_export_gaslist_l2", "envi_export_insulationlist_l2")[int(cm.envi_layer2to)])
                                    newrow(layout, "3rd layer thickness:", cm, "envi_export_l2_thi")
    
                            elif cm.envi_layer2 == '2'and cm.envi_con_type != 'Window':
                                for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                    if end:
                                        row.prop(cm, '{}{}'.format("envi_export_l2_", end))
                                    else:
                                        row = layout.row()
    
                            elif cm.envi_layer2 == '2' and cm.envi_con_type == 'Window':
                                newrow(layout, "Name:", cm, "envi_export_l2_name")
                                newrow(layout, "Optical data type:", cm, "envi_export_l2_odt")
                                newrow(layout, "Construction Make-up:", cm, "envi_export_l2_sds")
                                newrow(layout, "Translucent:", cm, "envi_export_l2_sdiff")
                                for end in (0, 'thi', 'tc', 0, 'stn', 'fsn', 'bsn', 0, 'vtn', 'fvrn', 'bvrn', 0, 'itn', 'fie', 'bie'):
                                    if end:
                                        row.prop(cm, '{}{}'.format("envi_export_l2_", end))
                                    else:
                                        row = layout.row()
    
                            if cm.envi_layer2 != '0':
                                row = layout.row()
                                row.label("----------------")
                                row = layout.row()
                                row.label("4th layer:")
                                row.prop(cm, "envi_layer3")
                                row = layout.row()
                                if cm.envi_layer3 == '1':
                                    if cm.envi_con_type == "Window":
                                        row.label("Gas Type:")
                                        row.prop(cm, ("envi_export_wgaslist_l3"))
                                        row.prop(cm, "envi_export_l3_thi")
                                    elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                        row.label("4th layer type:")
                                        row.prop(cm, "envi_layer3to")
                                        row = layout.row()
                                        row.label("4th layer material:")
                                        row.prop(cm, ("envi_export_bricklist_l3", "envi_export_claddinglist_l3", "envi_export_concretelist_l3", "envi_export_metallist_l3", "envi_export_stonelist_l3", "envi_export_woodlist_l3", "envi_export_gaslist_l3", "envi_export_insulationlist_l3")[int(cm.envi_layer3to)])
                                        newrow(layout, "3rd layer thickness:", cm, "envi_export_l3_thi")
    
                                elif cm.envi_layer3 == '2'and cm.envi_con_type != 'Window':
                                    for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                        if end:
                                            row.prop(cm, '{}{}'.format("envi_export_l3_", end))
                                        else:
                                            row = layout.row()
    
                                elif cm.envi_layer3 == '2' and cm.envi_con_type == 'Window':
                                    newrow(layout, "Name:", cm, "envi_export_l3_name")
                                    row = layout.row()
                                    row.label("Gas Type:")
                                    row.prop(cm, "envi_export_wgaslist_l3")
                                    newrow(layout, "3rd layer thickness:", cm, "envi_export_l3_thi")
    
                                if cm.envi_layer3 != '0':
                                    row = layout.row()
                                    row.label("----------------")
                                    row = layout.row()
                                    row.label("5th layer:")
                                    row.prop(cm, "envi_layer4")
                                    row = layout.row()
                                    if cm.envi_layer4 == '1':
                                        if cm.envi_con_type == "Window":
                                            row.label("Glass Type:")
                                            row.prop(cm, ("envi_export_glasslist_l4"))
                                        elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                            row.label("5th layer type:")
                                            row.prop(cm, "envi_layer4to")
                                            row = layout.row()
                                            row.label("5th layer material:")
                                            row.prop(cm, ("envi_export_bricklist_l4", "envi_export_claddinglist_l4", "envi_export_concretelist_l4", "envi_export_metallist_l4", "envi_export_stonelist_l4", "envi_export_woodlist_l4", "envi_export_gaslist_l4", "envi_export_insulationlist_l4")[int(cm.envi_layer4to)])
                                            newrow(layout, "4th layer thickness:", cm, "envi_export_l4_thi")
    
                                    elif cm.envi_layer4 == '2' and cm.envi_con_type != 'Window':
                                        for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                            if end:
                                                row.prop(cm, '{}{}'.format("envi_export_l4_", end))
                                            else:
                                                row = layout.row()
    
                                    elif cm.envi_layer4 == '2' and cm.envi_con_type == 'Window':
                                        newrow(layout, "Name:", cm, "envi_export_l4_name")
                                        newrow(layout, "Optical data type:", cm, "envi_export_l4_odt")
                                        newrow(layout, "Construction Make-up:", cm, "envi_export_l4_sds")
                                        newrow(layout, "Translucent:", cm, "envi_export_l4_sdiff")
                                        for end in (0, 'thi', 'tc', 0, 'stn', 'fsn', 'bsn', 0, 'vtn', 'fvrn', 'bvrn', 0, 'itn', 'fie', 'bie'):
                                            if end:
                                                row.prop(cm, '{}{}'.format("envi_export_l4_", end))
                                            else:
                                                row = layout.row()
    
                elif cm.envi_con_makeup == '0':
                    thicklist = ("envi_export_lo_thi", "envi_export_l1_thi", "envi_export_l2_thi", "envi_export_l3_thi", "envi_export_l4_thi")
                    propdict = {'Wall': (envi_cons.wall_con, 'envi_export_wallconlist', cm.envi_export_wallconlist), 'Floor': (envi_cons.floor_con, 'envi_export_floorconlist', cm.envi_export_floorconlist), 
                    'Roof': (envi_cons.roof_con, 'envi_export_roofconlist', cm.envi_export_roofconlist), 'Door': (envi_cons.door_con, 'envi_export_doorconlist', cm.envi_export_doorconlist), 'Window': (envi_cons.glaze_con, 'envi_export_glazeconlist', cm.envi_export_glazeconlist)} 
                    
                    row = layout.row()                
                    row.prop(cm, propdict[cm.envi_con_type][1])
                    
                    for l, layername in enumerate(propdict[cm.envi_con_type][0][propdict[cm.envi_con_type][2]]):
                        row = layout.row()
                        row.label(text = layername)
                        if layername in envi_mats.wgas_dat:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: 14mm")
                        elif layername in envi_mats.gas_dat:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: 20-50mm")
                        elif layername in envi_mats.glass_dat:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: "+str(float(envi_mats.matdat[layername][3])*1000)+"mm")
                        else:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
        
        elif cm.mattype == '3':
            fvsimnode = bpy.data.node_groups[scene['viparams']['fvsimnode'].split('@')[1]].nodes[scene['viparams']['fvsimnode'].split('@')[0]] if 'fvsimnode' in scene['viparams'] else 0
            newrow(layout, "Type:", cm, "flovi_bmb_type")
            if cm.flovi_bmb_type == '0':
                newrow(layout, "Pressure type:", cm, "flovi_bmwp_type")
                if cm.flovi_bmwp_type == 'fixedValue':
                    newrow(layout, "Pressure value:", cm, "flovi_b_sval")
                    
                newrow(layout, "Velocity type:", cm, "flovi_bmwu_type")
                newrow(layout, "Field value:", cm, "flovi_u_field")
                if not cm.flovi_u_field:
                    newrow(layout, 'Velocity:', cm, 'flovi_b_vval')
#                split = layout.split()
#                col = split.column(align=True)
#                col.label(text="Velocity:")
#                col.prop(cm, "flovi_bmu_x")
#                col.prop(cm, "flovi_bmu_y")
#                col.prop(cm, "flovi_bmu_z")
                
                if fvsimnode and fvsimnode.solver != 'icoFoam':
                    newrow(layout, "nut type:", cm, "flovi_bmwnut_type")
                    if fvsimnode.turbulence == 'SpalartAllmaras':                        
                        newrow(layout, "nuTilda type:", cm, "flovi_bmwnutilda_type")
                    elif fvsimnode.turbulence == 'kEpsilon':
                        newrow(layout, "k type:", cm, "flovi_bmwk_type")
                        newrow(layout, "Epsilon type:", cm, "flovi_bmwe_type")
                    elif fvsimnode.turbulence == 'komega':
                        newrow(layout, "k type:", cm, "flovi_bmwk_type")
                        newrow(layout, "Omega type:", cm, "flovi_bmwe_type")
                    if fvsimnode.bouyancy:
                        newrow(layout, "Temperature:", cm, "temperature")
#                newrow(layout, "nuTilda:", cm, "flovi_bmnutilda")
#                split = layout.split()
#                col = split.column(align=True)
#                col.label(text="nuTilda:")
#                col.prop(cm, "flovi_bmnut")
#                col.prop(cm, "flovi_bmwnut_y")
#                col.prop(cm, "flovi_bmwnut_z")
            elif cm.flovi_bmb_type == '1':
                newrow(layout, "Pressure sub-type:", cm, "flovi_bmip_type")
                if cm.flovi_bmip_type == 'fixedValue':
                    newrow(layout, "Pressure value:", cm, "flovi_b_sval")
                newrow(layout, "Velocity sub-type:", cm, "flovi_bmiu_type")
                newrow(layout, "Field value:", cm, "flovi_u_field")
                if not cm.flovi_u_field:
                    newrow(layout, 'Velocity:', cm, 'flovi_b_vval')
                if fvsimnode and fvsimnode.solver != 'icoFoam':
                    newrow(layout, "nut type:", cm, "flovi_bminut_type")
                    if fvsimnode.turbulence == 'SpalartAllmaras':                        
                        newrow(layout, "nuTilda type:", cm, "flovi_bminutilda_type")
                    elif fvsimnode.turbulence == 'kEpsilon':
                        newrow(layout, "k type:", cm, "flovi_bmik_type")
                        newrow(layout, "Epsilon type:", cm, "flovi_bmie_type")
                    elif fvsimnode.turbulence == 'kOmega':
                        newrow(layout, "k type:", cm, "flovi_bmik_type")
                        newrow(layout, "Omega type:", cm, "flovi_bmio_type")
            elif cm.flovi_bmb_type == '2':
                newrow(layout, "Pressure sub-type:", cm, "flovi_bmop_type")
                if cm.flovi_bmop_type == 'fixedValue':
                    newrow(layout, "Pressure value:", cm, "flovi_b_sval")
                newrow(layout, "Velocity sub-type:", cm, "flovi_bmou_type")
                newrow(layout, "Field value:", cm, "flovi_u_field")
                if not cm.flovi_u_field:
                    newrow(layout, 'Velocity:', cm, 'flovi_b_vval')
                if fvsimnode and fvsimnode.solver != 'icoFoam':
                    newrow(layout, "nut type:", cm, "flovi_bmonut_type")
                    if fvsimnode.turbulence == 'SpalartAllmaras':                        
                        newrow(layout, "nuTilda type:", cm, "flovi_bmonutilda_type")
                    elif fvsimnode.turbulence == 'kEpsilon':
                        newrow(layout, "k type:", cm, "flovi_bmok_type")
                        newrow(layout, "Epsilon type:", cm, "flovi_bmoe_type")
                    elif fvsimnode.turbulence == 'kOmega':
                        newrow(layout, "k type:", cm, "flovi_bmok_type")
                        newrow(layout, "Omega type:", cm, "flovi_bmoo_type")
                
class IESPanel(bpy.types.Panel):
    bl_label = "LiVi IES file"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        if context.lamp or context.mesh:
            return True

    def draw(self, context):
        layout, lamp = self.layout, context.active_object
        if lamp.type != 'LAMP': 
            newrow(layout, 'Light Array', lamp, 'lila')
        if (lamp.type == 'LAMP' and lamp.data.type != 'SUN') or lamp.lila: 
            row = layout.row()
            row.operator("livi.iesselect")
            row.prop(lamp, "ies_name")
            newrow(layout, 'IES Dimension:', lamp, "ies_unit")
            newrow(layout, 'IES Strength:', lamp, "ies_strength")
            row = layout.row()
            row.prop(lamp, "ies_colour")
                
class VIZonePanel(bpy.types.Panel):
    bl_label = "VI-Suite Zone Definition"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        if context.object and context.object.type == 'MESH':
            return True

    def draw(self, context):
        obj = bpy.context.active_object
        layout = self.layout
        row = layout.row()
        row.prop(obj, "vi_type")
        if obj.vi_type == '1':
            row = layout.row()
            row.prop(obj, "envi_type")
            row = layout.row()
            if obj.envi_type == '1':
                row = layout.row()
                row.label('HVAC Template:')
                row.prop(obj, 'envi_hvact')            
                row = layout.row()
                newrow(layout, 'HVAC schedule:', obj, 'envi_hvacsched')
                if obj.envi_hvacsched:
                    uvals, u = (1, obj.hvacu1, obj.hvacu2, obj.hvacu3, obj.hvacu4), 0
                    tvals = (0, obj.hvact1, obj.hvact2, obj.hvact3, obj.hvact4)
                    while uvals[u] and tvals[u] < 365:
                        [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'hvact'+str(u+1)), ('Fors:', 'hvacf'+str(u+1)), ('Untils:', 'hvacu'+str(u+1)))]
                        u += 1
                row = layout.row()
                row.label('Heating -----------')
                newrow(layout, 'Heating limit:', obj, 'envi_hvachlt')
                if obj.envi_hvachlt != '4':
                    newrow(layout, 'Heating temp:', obj, 'envi_hvacht')
                    if obj.envi_hvachlt in ('0', '2',):
                        newrow(layout, 'Heating airflow:', obj, 'envi_hvachaf')
                    if obj.envi_hvachlt in ('1', '2'):
                        newrow(layout, 'Heating capacity:', obj, 'envi_hvacshc')
                    newrow(layout, 'Thermostat schedule:', obj, 'envi_htspsched')
                    if not obj.envi_htspsched:
                        newrow(layout, 'Thermostat level:', obj, 'envi_htsp')
                    else:
                        uvals, u = (1, obj.htspu1, obj.htspu2, obj.htspu3, obj.htspu4), 0
                        tvals = (0, obj.htspt1, obj.htspt2, obj.htspt3, obj.htspt4)
                        while uvals[u] and tvals[u] < 365:
                            [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'htspt'+str(u+1)), ('Fors:', 'htspf'+str(u+1)), ('Untils:', 'htspu'+str(u+1)))]
                            u += 1
    
                row = layout.row()
                row.label('Cooling ------------')
                newrow(layout, 'Cooling limit:', obj, 'envi_hvacclt')
                if obj.envi_hvacclt != '4':
                    newrow(layout, 'Cooling temp:', obj, 'envi_hvacct')
                    if obj.envi_hvacclt in ('0', '2'):
                        newrow(layout, 'Cooling airflow:', obj, 'envi_hvaccaf')
                    if obj.envi_hvacclt in ('1', '2'):
                        newrow(layout, 'Cooling capacity:', obj, 'envi_hvacscc')
                    newrow(layout, 'Thermostat schedule:', obj, 'envi_ctspsched')
                    if not obj.envi_ctspsched:
                        newrow(layout, 'Thermostat level:', obj, 'envi_ctsp')
                    else:
                        uvals, u = (1, obj.ctspu1, obj.ctspu2, obj.ctspu3, obj.ctspu4), 0
                        tvals = (0, obj.ctspt1, obj.ctspt2, obj.ctspt3, obj.ctspt4)
                        while uvals[u] and tvals[u] < 365:
                            [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'ctspt'+str(u+1)), ('Fors:', 'ctspf'+str(u+1)), ('Untils:', 'ctspu'+str(u+1)))]
                            u += 1
    
                if (obj.envi_hvachlt, obj.envi_hvacclt) != ('4', '4'):
                    row = layout.row()
                    row.label('Outdoor air --------------')
                    newrow(layout, 'Outdoor air:', obj, 'envi_hvacoam')
                    if obj.envi_hvacoam in ('2', '4', '5'):
                        newrow(layout, 'Flow/person (m3/s.p:', obj, 'envi_hvacfrp')
                    if obj.envi_hvacoam in ('1', '4', '5'):
                        newrow(layout, 'Zone flow (m3/s):', obj, 'envi_hvacfrz')
                    if obj.envi_hvacoam in ('3', '4', '5'):
                        newrow(layout, 'Flow/area (m3/s.a):', obj, 'envi_hvacfrzfa')
                    if obj.envi_hvacoam in ('4', '5', '6') and not obj.envi_hvact:
                        newrow(layout, 'ACH', obj, 'envi_hvacfach')
    
                row = layout.row()
                row.label('-------------------------------------')
                row = layout.row()
                row.label('Occupancy:')
                row.prop(obj, "envi_occtype")
                if obj.envi_occtype != '0':
                    row.prop(obj, "envi_occsmax")
                    newrow(layout, 'Schedule:', obj, 'envi_occsched')
                    if obj.envi_occsched:
                        uvals, u = (1, obj.occu1, obj.occu2, obj.occu3, obj.occu4), 0
                        tvals = (0, obj.occt1, obj.occt2, obj.occt3, obj.occt4)
                        while uvals[u] and tvals[u] < 365:
                            [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'occt'+str(u+1)), ('Fors:', 'occf'+str(u+1)), ('Untils:', 'occu'+str(u+1)))]
                            u += 1
                    newrow(layout, 'Activity schedule:', obj, 'envi_asched')
                    if not obj.envi_asched:
                        newrow(layout, 'Activity level:', obj, 'envi_occwatts')
                    else:
                        uvals, u = (1, obj.aoccu1, obj.aoccu2, obj.aoccu3, obj.aoccu4), 0
                        tvals = (0, obj.aocct1, obj.aocct2, obj.aocct3, obj.aocct4)
                        while uvals[u] and tvals[u] < 365:
                            [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'aocct'+str(u+1)), ('Fors:', 'aoccf'+str(u+1)), ('Untils:', 'aoccu'+str(u+1)))]
                            u += 1
                    newrow(layout, 'Comfort calc:', obj, 'envi_comfort')
                    if obj.envi_comfort:
                        newrow(layout, 'WE schedule:', obj, 'envi_wsched')
                        if not obj.envi_wsched:
                            newrow(layout, 'Work efficiency:', obj, 'envi_weff')
                        else:
                            uvals, u = (1, obj.woccu1, obj.woccu2, obj.woccu3, obj.woccu4), 0
                            tvals = (0, obj.wocct1, obj.wocct2, obj.wocct3, obj.wocct4)
                            while uvals[u] and tvals[u] < 365:
                                [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'wocct'+str(u+1)), ('Fors:', 'woccf'+str(u+1)), ('Untils:', 'woccu'+str(u+1)))]
                                u += 1
                        newrow(layout, 'AV schedule:', obj, 'envi_avsched')
                        if not obj.envi_avsched:
                            newrow(layout, 'Air velocity:', obj, 'envi_airv')
                        else:
                            uvals, u = (1, obj.avoccu1, obj.avoccu2, obj.avoccu3, obj.avoccu4), 0
                            tvals = (0, obj.avocct1, obj.avocct2, obj.avocct3, obj.avocct4)
                            while uvals[u] and tvals[u] < 365:
                                [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'avocct'+str(u+1)), ('Fors:', 'avoccf'+str(u+1)), ('Untils:', 'avoccu'+str(u+1)))]
                                u += 1
                        newrow(layout, 'Cl schedule:', obj, 'envi_clsched')
                        if not obj.envi_clsched:
                            newrow(layout, 'Clothing:', obj, 'envi_cloth')
                        else:
                            uvals, u = (1, obj.coccu1, obj.coccu2, obj.coccu3, obj.coccu4), 0
                            tvals = (0, obj.cocct1, obj.cocct2, obj.cocct3, obj.cocct4)
                            while uvals[u] and tvals[u] < 365:
                                [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'cocct'+str(u+1)), ('Fors:', 'coccf'+str(u+1)), ('Untils:', 'coccu'+str(u+1)))]
                                u += 1
                        newrow(layout, 'CO2:', obj, 'envi_co2')
                
                row = layout.row()
                row.label('-------------------------------------')
                row = layout.row()
                row.label('Equipment:')
                row.prop(obj, "envi_equiptype")
                if obj.envi_equiptype != '0':
                    row = layout.row()
                    row.label('Level:')
                    row.prop(obj, "envi_equipmax")
                    newrow(layout, 'Schedule:', obj, 'envi_equipsched')
                    if obj.envi_equipsched:
                        uvals, u = (1, obj.equipu1, obj.equipu2, obj.occu3, obj.equipu4), 0
                        tvals = (0, obj.equipt1, obj.equipt2, obj.equipt3, obj.equipt4)
                        while uvals[u] and tvals[u] < 365:
                            [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'equipt'+str(u+1)), ('Fors:', 'equipf'+str(u+1)), ('Untils:', 'equipu'+str(u+1)))]
                            u += 1
                            
                row = layout.row()
                row.label('---------------------------------------')
    
                if obj.envi_occtype != "0":
                    newrow(layout, 'Infiltration:', obj, "envi_occinftype")
                else:
                    newrow(layout, 'Infiltration:', obj, "envi_inftype")
    
                if obj.envi_occtype != "0" and obj.envi_occinftype == '6':
                    newrow(layout, 'Level:', obj, "envi_inflevel")
                if (obj.envi_occtype == "0" and obj.envi_inftype != '0') or (obj.envi_occtype == "1" and obj.envi_occinftype not in ('0', '6')):
                    newrow(layout, 'Level:', obj, "envi_inflevel")
                    newrow(layout, 'Schedule:', obj, 'envi_infsched')
                    if obj.envi_infsched:
                        uvals, u = (1, obj.infu1, obj.infu2, obj.infu3, obj.infu4), 0
                        tvals = (0, obj.inft1, obj.inft2, obj.inft3, obj.inft4)
                        while uvals[u] and tvals[u] < 365:
                            [newrow(layout, v[0], obj, v[1]) for v in (('End day {}:'.format(u+1), 'inft'+str(u+1)), ('Fors:', 'inff'+str(u+1)), ('Untils:', 'infu'+str(u+1)))]
                            u += 1


