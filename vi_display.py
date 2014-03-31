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


import bpy, blf, colorsys, bgl, mathutils
try:
    import matplotlib
    mp = 1
except:
    mp = 0

from . import livi_export
from . import vi_func

def ss_display():
    pass

def li_display(simnode, connode, geonode):
    cp = '0' if not geonode else geonode.cpoint
    scene = bpy.context.scene
    vi_func.clearscene(scene, '@')
    obreslist = []
    obcalclist = []

    for geo in scene.objects:
            scene.objects.active = geo
            if getattr(geo, 'mode') != 'OBJECT':
                bpy.ops.object.mode_set(mode = 'OBJECT')

    bpy.ops.object.select_all(action = 'DESELECT')

    if len(bpy.app.handlers.frame_change_pre) == 0:
        bpy.app.handlers.frame_change_pre.append(livi_export.cyfc1)
        
    for geo in scene.objects:
        if geo.type == "MESH" and geo.get('licalc') and geo.hide == False:
            bpy.ops.object.select_all(action = 'DESELECT')
            obcalclist.append(geo)

    vi_func.vcframe('', scene, obcalclist, simnode['Animation'])
    scene.frame_set(scene.fs)
    scene.objects.active = None

    if scene.vi_disp_3d == 1:
        for i, geo in enumerate(vi_func.retobjs('livic')):
            vi_func.selobj(scene, geo)
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.context.tool_settings.mesh_select_mode = [False, False, True]
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.object.mode_set(mode = 'OBJECT')

            for cf in geo["cfaces"]:
                geo.data.polygons[int(cf)].select = True

#            if len(geo["cverts"]) > 0:
#                bpy.context.tool_settings.mesh_select_mode = [True, False, False]
#                for cv in geo["cverts"]:
#                    geo.data.vertices[int(cv)].select = True

            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.duplicate()
            bpy.ops.mesh.separate()
            bpy.ops.object.mode_set(mode = 'OBJECT')
            if cp == '1':
                for v, vin in enumerate(geo['cverts']):
                    for resv in scene.objects[0].data.vertices:
                        if resv.co == geo.data.vertices[vin].co:
                            scene.objects[0]['cverts'][v] = resv.index
            for f in scene.objects[0].data.polygons:
                f.select = True
            scene.objects[0].name = geo.name+"res"
            obreslist.append(scene.objects[0])
            scene.objects[0].lires = 1
            
        for obres in obreslist:
            vi_func.selobj(scene, obres)
            if cp == '0' or not geonode:
                if len(obres.data.polygons) > 1:
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.mesh.select_all(action = 'SELECT')
                    bpy.ops.mesh.extrude_faces_move()
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    bpy.ops.object.select_all(action = 'DESELECT')

            bpy.ops.object.shape_key_add(from_mix = False)

            for frame in vi_func.framerange(scene, simnode['Animation']):
                bpy.ops.object.shape_key_add(from_mix = False)
                obres.active_shape_key.name = str(frame)
    
    vi_func.vcframe('', scene, obreslist, simnode['Animation'])                                   
    bpy.ops.wm.save_mainfile(check_existing = False)
    scene.frame_set(scene.fs)
    rendview(1)

def spnumdisplay(disp_op, context, simnode):
    scene = context.scene
    leg = 0 if simnode.bl_label == 'VI Sun Path' else 1
    ob = bpy.data.objects['SPathMesh']

    if scene.hourdisp == True:
        blf.enable(0, 4)
        blf.shadow(0, 5,scene.vi_display_rp_fsh[0], scene.vi_display_rp_fsh[1], scene.vi_display_rp_fsh[2], scene.vi_display_rp_fsh[3])
        bgl.glColor4f(scene.vi_display_rp_fc[0], scene.vi_display_rp_fc[1], scene.vi_display_rp_fc[2], scene.vi_display_rp_fc[3])
        blf.size(0, scene.vi_display_rp_fs, 72)
        mid_x, mid_y, width, height = vi_func.viewdesc(context)
        view_mat = context.space_data.region_3d.perspective_matrix
        view_pos = (view_mat.inverted()[0][3]/5, view_mat.inverted()[1][3]/5, view_mat.inverted()[2][3]/5)
        ob_mat = ob.matrix_world
        total_mat = view_mat*ob_mat
        for np in ob['numpos']:
            if (total_mat*mathutils.Vector(ob['numpos'][np]))[2] > 0 and not scene.ray_cast(0.95*ob_mat*mathutils.Vector(ob['numpos'][np]) ,view_pos)[0]:
                vi_func.draw_index(context, leg, mid_x, mid_y, width, height, np.split('-')[1], total_mat*mathutils.Vector(ob['numpos'][np]).to_4d())
        blf.disable(0, 4)
    else:
        return

def linumdisplay(disp_op, context, simnode, connode, geonode):
    scene = context.scene
    if not scene.vi_display:
        return
    try:
        if obcalclist:
            pass
    except:
        obreslist = [ob for ob in scene.objects if ob.type == 'MESH'  and 'lightarray' not in ob.name and ob.hide == False and ob.layers[scene.active_layer] == True and ob.get('licalc') == 1 and ob.lires == 1]
        obcalclist = [ob for ob in scene.objects if ob.type == 'MESH' and 'lightarray' not in ob.name and ob.hide == False and ob.layers[scene.active_layer] == True and ob.get('licalc') == 1 and ob.lires == 0]

    if (scene.li_disp_panel != 2 and scene.ss_disp_panel != 2) or scene.vi_display_rp != True \
         or (bpy.context.active_object not in (obcalclist+obreslist) and scene.vi_display_sel_only == True)  \
         or scene.frame_current not in range(scene.fs, scene.fe + 1) or (bpy.context.active_object and bpy.context.active_object.mode == 'EDIT'):
        return
        
    if bpy.context.active_object:
        if bpy.context.active_object.type == 'MESH' and bpy.context.active_object.mode != 'OBJECT':
             bpy.context.active_object.mode = 'OBJECT'

    blf.enable(0, 4)
    blf.shadow(0, 5, scene.vi_display_rp_fsh[0], scene.vi_display_rp_fsh[1], scene.vi_display_rp_fsh[2], scene.vi_display_rp_fsh[3])
    bgl.glColor4f(*scene.vi_display_rp_fc[:])
    blf.size(0, scene.vi_display_rp_fs, 72)
    bgl.glColor3f = scene.vi_display_rp_fc
    cp = geonode.cpoint if geonode else simnode.cpoint
    fn = context.scene.frame_current - scene.fs
    mid_x, mid_y, width, height = vi_func.viewdesc(context)

    if scene.vi_display_sel_only == False:
        obd = obreslist if len(obreslist) > 0 else obcalclist
    else:
        oblist = obreslist if len(obreslist) > 0 else obcalclist
        obd = [context.active_object] if context.active_object in oblist else []

    for ob in obd:
        if ob.active_shape_key_index != fn+1:
            ob.active_shape_key_index = fn+1
        obm = ob.data
        ob_mat = ob.matrix_world
        view_mat = context.space_data.region_3d.perspective_matrix
        view_pos = (view_mat.inverted()[0][3]/5, view_mat.inverted()[1][3]/5, view_mat.inverted()[2][3]/5)

        if cp == "0" or not geonode:
            faces = [f for f in ob.data.polygons if f.select == True] if ob.lires else [f for f in ob.data.polygons if ob.data.materials[f.material_index].vi_shadow] if simnode.bl_label == 'VI Shadow Study' else [f for f in ob.data.polygons if f.select == True] if ob.lires else [f for f in ob.data.polygons if ob.data.materials[f.material_index].livi_sense]
            if scene.vi_display_vis_only:
                faces = [f for f in faces if not scene.ray_cast(ob_mat*((vi_func.face_centre(ob, len(obreslist), f)))+ 0.01*ob_mat*f.normal, view_pos)[0]]
        else:
            fverts = set(sum([list(f.vertices[:]) for f in ob.data.polygons if f.select], []))
            verts = [ob.data.vertices[v] for v in fverts if not scene.ray_cast(ob_mat*vi_func.v_pos(ob, v) + 0.01*ob_mat*ob.data.vertices[v].normal,view_pos)[0]] if scene.vi_display_vis_only else [ob.data.vertices[v] for v in fverts] 
            loops = []
            for v in verts:
                for f in [f for f in ob.data.polygons if f.select == True]:
                    if v.index in f.vertices:
                        loops.append(f.loop_indices[list(f.vertices).index(v.index)])
                        break

        total_mat = view_mat*ob_mat
        if cp == "0" or not geonode:
            for f in faces:
                vsum = mathutils.Vector((0, 0, 0))
                for v in f.vertices:
                    vsum = ob.active_shape_key.data[v].co + vsum if len(obreslist) > 0 else ob.data.vertices[v].co + vsum
                fc = vsum/len(f.vertices)
                if not f.hide:
                    loop_index = f.loop_indices[0]
                    if len(set(obm.vertex_colors[fn].data[loop_index].color[:])) > 0:
                        if (total_mat*fc)[2] > 0:
                            col, maxval, minval = obm.vertex_colors[fn].data[loop_index].color, max(simnode['maxres']), min(simnode['minres'])
                            if geonode:
                                val = abs(min(simnode['minres']) + (1 - (1.333333*colorsys.rgb_to_hsv(*[col[i]/255 for i in range(3)])[0]))*(maxval - minval))
                                vi_func.draw_index(context, scene.vi_leg_display, mid_x, mid_y, width, height, ('{:.1f}', '{:.0f}')[val > 100].format(val), total_mat*fc.to_4d())
                            else:
                                vi_func.draw_index(context, scene.vi_leg_display, mid_x, mid_y, width, height, '{:.0f}'.format(abs(minval + (col[0])*(maxval - minval))), total_mat*fc.to_4d())
        elif cp == "1":
            for v, vert in enumerate(verts):
                vpos = ob.active_shape_key.data[vert.index].co if len(obreslist) > 0 else vert.co
                if len(set(obm.vertex_colors[fn].data[vert.index].color[:])) > 0:
                    if (total_mat*vpos)[2] > 0:
                        vi_func.draw_index(context, scene.vi_leg_display, mid_x, mid_y, width, height, int((1 - (1.333333*colorsys.rgb_to_hsv(obm.vertex_colors[fn].data[loops[v]].color[0]/255, obm.vertex_colors[fn].data[loops[v]].color[1]/255, obm.vertex_colors[fn].data[loops[v]].color[2]/255)[0]))*max(simnode['maxres'])), total_mat*vpos.to_4d())
    blf.disable(0, 4)

def li3D_legend(self, context, simnode, connode, geonode):
    scene = context.scene
    try:
        if scene.vi_leg_display != True or scene.vi_display == 0 or (scene.wr_disp_panel != 1 and scene.li_disp_panel != 2 and scene.ss_disp_panel != 2) or scene.frame_current not in range(scene.fs, scene.fe + 1):
            return
        else:
            if not connode or (connode and connode.bl_label == 'LiVi CBDM'):
                resvals = ['{:.1f}'.format(min(simnode['minres'])+i*(max(simnode['maxres'])-min(simnode['minres']))/19) for i in range(20)]
            else:
                resvals = [('{:.0f}', '{:.0f}', '{:.1f}')[int(connode.analysismenu)].format(min(simnode['minres'])+i*(max(simnode['maxres'])-min(simnode['minres']))/19) for i in range(20)]
    
            height = context.region.height
            lenres = len(resvals[-1])
            font_id = 0
            vi_func.drawpoly(20, height - 40, 70 + lenres*8, height - 520)
            vi_func.drawloop(19, height - 40, 70 + lenres*8, height - 520)
    
            for i in range(20):
                h = 0.75 - 0.75*(i/19)
                if connode:
                    bgl.glColor4f(colorsys.hsv_to_rgb(h, 1.0, 1.0)[0], colorsys.hsv_to_rgb(h, 1.0, 1.0)[1], colorsys.hsv_to_rgb(h, 1.0, 1.0)[2], 1.0)
                else:
                    bgl.glColor4f(i/19, i/19, i/19, 1)
                bgl.glBegin(bgl.GL_POLYGON)
                bgl.glVertex2i(20, (i*20)+height - 460)
                bgl.glVertex2i(60, (i*20)+height - 460)
                bgl.glVertex2i(60, (i*20)+height - 440)
                bgl.glVertex2i(20, (i*20)+height - 440)
                bgl.glEnd()
                blf.size(font_id, 20, 48)
                bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                blf.position(font_id, 65, (i*20)+height - 455, 0)
                blf.draw(font_id, "  "*(lenres - len(resvals[i]) ) + resvals[i])
    
            blf.size(font_id, 20, 56)
            if connode:
                if connode.bl_label == 'LiVi CBDM':
                    unit = ('kLuxHours', 'kWh', 'DA (%)', '', 'UDI-a (%)')[int(connode.analysismenu)]
                elif connode.bl_label == 'LiVi Basic':
                    unit = ("Lux", "W/m"+ u'\u00b2', "DF %")[int(connode.analysismenu)]
                elif connode.bl_label == 'LiVi Compliance':
                    unit = "DF %"
                else:
                    unit = 'unit'
    
            cu = unit if connode else '% Sunlit'
    
            vi_func.drawfont(cu, font_id, 0, height, 25, 57)
            bgl.glLineWidth(1)
            bgl.glDisable(bgl.GL_BLEND)
            height = context.region.height
            font_id = 0
            if scene.frame_current in range(scene.fs, scene.fe + 1):
                findex = scene.frame_current - scene.frame_start if simnode['Animation'] != 'Static' else 0
                bgl.glColor4f(0.0, 0.0, 0.0, 0.8)
                blf.size(font_id, 20, 48)
                if context.active_object:
                    if context.active_object.get('lires') == 1 or context.active_object.get('licalc'):
                        vi_func.drawfont("Ave: {:.1f}".format(context.active_object['oave'][str(scene.frame_current)]), font_id, 0, height, 22, 480)
                        vi_func.drawfont("Max: {:.1f}".format(context.active_object['omax'][str(scene.frame_current)]), font_id, 0, height, 22, 495)
                        vi_func.drawfont("Min: {:.1f}".format(context.active_object['omin'][str(scene.frame_current)]), font_id, 0, height, 22, 510)
                else:
                    vi_func.drawfont("Ave: {:.1f}".format(simnode['avres'][findex]), font_id, 0, height, 22, 480)
                    vi_func.drawfont("Max: {:.1f}".format(simnode['maxres'][findex]), font_id, 0, height, 22, 495)
                    vi_func.drawfont("Min: {:.1f}".format(simnode['minres'][findex]), font_id, 0, height, 22, 510)
    except Exception as e:
        print(e, 'Turning off legend display')
        scene.vi_leg_display = 0
        scene.update()
        
def viwr_legend(self, context, simnode):
    scene = context.scene
    if scene.vi_leg_display != True or scene.vi_display == 0:
        return
    else:
        resvals = ['{0:.0f} to {1:.0f}'.format(2*i, 2*(i+1)) for i in range(simnode['nbins'])]
        resvals[-1] = resvals[-1][:-int(len('{:.0f}'.format(simnode['maxres'])))] + u"\u221E"
        height, lenres, font_id = context.region.height, len(resvals[-1]), 0
        vi_func.drawpoly(20, height - 40, 70 + lenres*8, height - (simnode['nbins']+6)*20)
        vi_func.drawloop(19, height - 40, 70 + lenres*8, height - (simnode['nbins']+6)*20)
        cm = matplotlib.cm.jet if simnode.wrtype in ('0', '1') else matplotlib.cm.hot
        for i in range(simnode['nbins']):
            bgl.glColor4f(*cm(i * 1/(simnode['nbins']-1), 1))
            bgl.glBegin(bgl.GL_POLYGON)
            bgl.glVertex2i(20, height - 70 - (simnode['nbins'] * 20) + (i*20))
            bgl.glVertex2i(60, height - 70 - (simnode['nbins'] * 20) + (i*20))
            bgl.glVertex2i(60, height - 50 - (simnode['nbins'] * 20) + (i*20))
            bgl.glVertex2i(20, height - 50 - (simnode['nbins'] * 20) + (i*20))
            bgl.glEnd()
            blf.size(font_id, 20, 48)
            bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
            blf.position(font_id, 65, height - 65 - (simnode['nbins'] * 20) + (i*20), 0)
            blf.draw(font_id, "  "*(lenres - len(resvals[i]) ) + resvals[i])

        blf.size(font_id, 20, 56)
        cu = 'Speed (m/s)'

        vi_func.drawfont(cu, font_id, 0, height, 25, 57)
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        height = context.region.height
        font_id = 0

        if context.scene.frame_current in range(scene.fs, scene.fe + 1):
            bgl.glColor4f(0.0, 0.0, 0.0, 0.8)
            blf.size(font_id, 20, 48)
            vi_func.drawfont("Ave: {:.1f}".format(simnode['avres']), font_id, 0, height, 22, simnode['nbins']*20 + 85)
            vi_func.drawfont("Max: {:.1f}".format(simnode['maxres']), font_id, 0, height, 22, simnode['nbins']*20 + 100)
            vi_func.drawfont("Min: {:.1f}".format(simnode['minres']), font_id, 0, height, 22, simnode['nbins']*20 + 115)

def li_compliance(self, context, connode):
    height, scene = context.region.height, context.scene
    if not scene.get('li_compliance') or scene.frame_current not in range(scene.fs, scene.fe + 1) or scene.vi_display == 0:
        return
    if connode.analysismenu == '0':
        buildtype = ('School', 'Higher Education', 'Healthcare', 'Residential', 'Retail', 'Office & Other')[int(connode.bambuildmenu)]
    elif connode.analysismenu == '1':
        buildtype = 'Residential'
        cfshpfsdict = {'totkit': 0, 'kitdf': 0, 'kitsv': 0, 'totliv': 0, 'livdf': 0, 'livsv': 0}

    vi_func.drawpoly(100, height - 40, 900, height - 65)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    horpos, widths = (100, 317, 633, 900), (100, 450, 600, 750, 900)

    for p in range(3):
        vi_func.drawloop(horpos[p], height - 40, horpos[p+1], height - 65)

    font_id = 0
    blf.size(font_id, 20, 54)
    vi_func.drawfont('Standard: '+('BREEAM HEA1', 'CfSH', 'LEED EQ8.1', 'Green Star')[int(connode.analysismenu)], font_id, 0, height, 110, 58)
    vi_func.drawfont('Project Name: '+scene.li_projname, font_id, 0, height, 643, 58)
    blf.size(font_id, 20, 40)

    def space_compliance(geos):
        frame, buildspace, pfs, epfs, lencrit = scene.frame_current, '', [], [], 0
        for geo in geos:
            mat = [m for m in geo.data.materials if m.livi_sense][0]
            geo['cr4'] = [('fail', 'pass')[int(com)] for com in geo['comps'][frame][:][::2]]
            geo['cr6'] = [cri[4] for cri in geo['crit']]
            if 'fail' in [c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '1'] or bpy.context.scene['dfpass'][frame] == 1:
                pf = 'FAIL'
            elif 'pass' not in [c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '0.75'] and len([c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '0.75']) > 0:
                if 'pass' not in [c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '0.5'] and len([c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '0.5']) > 0:
                    pf = 'FAIL'
                else:
                    pf = 'PASS'
            else:
                pf = 'PASS'
            pfs.append(pf)

            if connode.analysismenu == '1':
                cfshpfsdict[('totkit', 'totliv')[mat.rspacemenu == '1']] += 1
                if geo['cr4'][0] == 'pass':
                    cfshpfsdict[('kitdf', 'livdf')[mat.rspacemenu == '1']] += 1
                if geo['cr4'][1] == 'pass':
                    cfshpfsdict[('kitsv', 'livsv')[mat.rspacemenu == '1']] += 1

            if connode.analysismenu == '0':
                ecrit = geo['ecrit']
                geo['ecr4'] = [('fail', 'pass')[int(com)] for com in geo['ecomps'][frame][:][::2]]
                geo['ecr6'] = [ecri[4] for ecri in ecrit]
                if 'fail' in [c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '1'] or bpy.context.scene['dfpass'][frame] == 1:
                    epf = 'FAIL'
                elif 'pass' not in [c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '0.75'] and len([c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '0.75']) > 0:
                    if 'pass' not in [c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '0.5'] and len([c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '0.5']) > 0:
                        epf = 'FAIL'
                    else:
                        epf = 'EXEMPLARY'
                else:
                    epf = 'EXEMPLARY'
                epfs.append(epf)

        if bpy.context.active_object in geos:
            geo = bpy.context.active_object
            lencrit = 1 + len(geo['crit'])
            vi_func.drawpoly(100, height - 70, 900, height - 70  - (lencrit)*25)
            vi_func.drawloop(100, height - 70, 900, height - 70  - (lencrit)*25)
            mat = [m for m in bpy.context.active_object.data.materials if m.livi_sense][0]
            if connode.analysismenu == '0':
                buildspace = ('', '', (' - Public/Staff', ' - Patient')[int(mat.hspacemenu)], (' - Kitchen', ' - Living/Dining/Study', ' - Communal')[int(mat.rspacemenu)], (' - Sales', ' - Office')[int(mat.respacemenu)])[int(connode.bambuildmenu)]
            elif connode.analysismenu == '1':
                buildspace = (' - Kitchen', ' - Living/Dining/Study')[int(mat.rspacemenu)]

            titles = ('Zone Metric', 'Target', 'Achieved', 'PASS/FAIL')
            tables = [[] for c in range(lencrit -1)]
            etables = [[] for e in range(len(geo['ecrit']))]
            for c, cr in enumerate(geo['crit']):
                if cr[0] == 'Percent':
                    tables[c] = ('{} (%)'.format(('Percentage area with Skyview', 'Average{}Daylight Factor'.format((' ', ' Point ')[cr[2] == 'PDF']))[cr[2] in ('DF', 'PDF')]), (cr[1],cr[3])[cr[2] in ('PDF','DF')], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), geo['cr4'][c].upper())
                elif cr[0] == 'Ratio':
                    tables[c] = ('Uniformity ratio', cr[3], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), geo['cr4'][c].upper())
                elif cr[0] == 'Min':
                    tables[c] = ('Minimum {} (%)'.format('Point Daylight Factor'), cr[3], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), geo['cr4'][c].upper())
                elif cr[0] == 'Average':
                    tables[c] = ('Average {} (%)'.format('Daylight Factor'), cr[3], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), geo['cr4'][c].upper())
            if connode.analysismenu == '0':
                for e, ecr in enumerate(ecrit):
                    if ecr[0] == 'Percent':
                        etables[e] = ('{} (%)'.format('Average Daylight Factor'), ecr[3], '{:.2f}'.format(geo['ecomps'][frame][:][e*2 + 1]), geo['ecr4'][e].upper())
                    elif ecr[0] == 'Min':
                        etables[e] = ('Minimum {} (%)'.format('Point Daylight Factor'), ecr[3], '{:.2f}'.format(geo['ecomps'][frame][:][e*2 + 1]), geo['ecr4'][e].upper())

            for j in range(4):
                vi_func.drawloop(widths[j], height - 70, widths[j+1], height - 95)

            bgl.glEnable(bgl.GL_LINE_STIPPLE)
            for t, tab in enumerate(tables):
                for j in range(4):
                    vi_func.drawloop(widths[j], height - 95 - t*25, widths[j+1], height - 120 - t*25)
                    if tab[j] == 'FAIL':
                        bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
                    elif tab[j] == 'PASS':
                        bgl.glColor4f(0.0, 0.7, 0.0, 1.0)
                    blf.size(font_id, 20, 44)
                    vi_func.drawfont(tab[j], 0, 0, height, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], 113 + t*25)
                    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                    if t == 0:
                        blf.size(font_id, 20, 48)
                        vi_func.drawfont(titles[j], 0, 0, height, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], 88)
            bgl.glDisable(bgl.GL_LINE_STIPPLE)
        else:
            etables = []
            lencrit = 0

        tpf = 'FAIL' if 'FAIL' in pfs or 'FAIL*' in pfs else 'PASS'
        if connode.analysismenu == '0':
            (tpf, lencrit) = ('EXEMPLARY', lencrit + len(geo['ecrit'])) if tpf == 'PASS' and ('FAIL' not in epfs and 'FAIL*' not in epfs) else (tpf, lencrit)

        return(tpf, lencrit, buildspace, etables)
    
    build_compliance, lencrit, bs, etables = space_compliance(vi_func.retobjs('livir'))

    if build_compliance == 'EXEMPLARY':
        for t, tab in enumerate(etables):
            if t == 0:
                vi_func.drawpoly(100, height - 70 - (lencrit * 25), 900, height - 70 - ((lencrit - len(etables)) * 25))
                vi_func.drawloop(100, height - 70 - (lencrit * 25), 900, height - 70 - ((lencrit - len(etables)) * 25))
            for j in range(4):
                bgl.glEnable(bgl.GL_LINE_STIPPLE)
                vi_func.drawloop(widths[j], height - 95 - (lencrit - len(etables) + t - 1) * 25, widths[j+1], height - 120 - (lencrit - len(etables) + t - 1) * 25)
                if tab[j] == 'FAIL':
                    bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
                elif tab[j] == 'PASS':
                    bgl.glColor4f(0.0, 1.0, 0.0, 1.0)
                blf.size(font_id, 20, 44)
                blf.position(font_id, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], height - 113 - (lencrit - len(etables) + t - 1) * 25, 0)
                blf.draw(font_id, tab[j])
                bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                bgl.glDisable(bgl.GL_LINE_STIPPLE)

    blf.position(font_id, 327, height - 58, 0)
    blf.size(font_id, 20, 54)
    blf.draw(font_id, 'Buildtype: '+buildtype+bs)

    blf.size(font_id, 20, 52)
    blf.position(font_id, 110, height - 87 - lencrit*26, 0)
    if connode.analysismenu == '0':
        vi_func.drawpoly(100, height - 70 - lencrit*26, 525, height - 95 - lencrit*26)
        vi_func.drawloop(100, height - 70 - lencrit*26, 350, height - 95 - lencrit*26)
        vi_func.drawloop(100, height - 70 - lencrit*26, 350, height - 95 - lencrit*26)
        vi_func.drawloop(350, height - 70 - lencrit*26, 525, height - 95 - lencrit*26)
        blf.draw(font_id, 'Building Compliance:')
        vi_func.drawfont(build_compliance, 0, lencrit, height, 250, 87)
        blf.position(font_id, 360, height - 87 - lencrit*26, 0)
        blf.draw(font_id, 'Credits achieved:')
        blf.position(font_id, 480, height - 87 - lencrit*26, 0)
        if build_compliance == 'PASS':
           blf.draw(font_id,  ('1', '2', '2', '1', '1', '1')[int(connode.bambuildmenu)])
        elif build_compliance == 'EXEMPLARY':
            blf.draw(font_id,  ('2', '3', '3', '2', '2', '2')[int(connode.bambuildmenu)])
        else:
            blf.draw(font_id, '0')

    elif connode.analysismenu == '1':
        vi_func.drawpoly(100, height - 70 - lencrit*26, 300, height - 95 - lencrit*26)
        vi_func.drawloop(100, height - 70 - lencrit*26, 300, height - 95 - lencrit*26)
        vi_func.drawfont('Credits achieved:', 0, lencrit, height, 110, 87)
        cfshcred = 0
        if cfshpfsdict['kitdf'] == cfshpfsdict['totkit'] and cfshpfsdict['totkit'] != 0:
            cfshcred += 1
        if cfshpfsdict['livdf'] == cfshpfsdict['totliv'] and cfshpfsdict['totliv'] != 0:
            cfshcred += 1
        if (cfshpfsdict['kitsv'] == cfshpfsdict['totkit'] and  cfshpfsdict['totkit'] != 0) or (cfshpfsdict['livsv'] == cfshpfsdict['totliv'] and cfshpfsdict['totliv'] != 0):
            cfshcred += 1
        blf.position(font_id, 250, height - 87 - lencrit*26, 0)
        blf.draw(font_id, '{} of {}'.format(cfshcred, '3' if 0 not in (cfshpfsdict['totkit'], cfshpfsdict['totliv']) else '2'))

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
    bgl.glLineWidth(1)
    sw = 8

    aolen, ailen, jnlen = len(scene.li_assorg), len(scene.li_assind), len(scene.li_jobno)
    vi_func.drawpoly(100, 50, 500 + aolen*sw + ailen*sw + jnlen*sw, 25)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    vi_func.drawloop(100, 50, 260 + aolen*sw, 25)
    vi_func.drawloop(260 + aolen*sw, 50, 400 + aolen*sw + ailen*sw, 25)
    vi_func.drawloop(400 + aolen*sw + ailen*sw, 50, 500 + aolen*sw + ailen*sw + jnlen*sw, 25)
    blf.size(font_id, 20, 44)
    blf.position(font_id, 110, 32, 0)
    blf.draw(font_id, 'Assessing Organisation:')
    blf.position(font_id, 250, 32, 0)
    blf.draw(font_id, scene.li_assorg)
    blf.position(font_id, 270 + aolen*sw, 32, 0)
    blf.draw(font_id, 'Assessing Individual:')
    blf.position(font_id, 395 + aolen*sw, 32, 0)
    blf.draw(font_id, scene.li_assind)
    blf.position(font_id, 410 + aolen*sw + ailen*sw, 32, 0)
    blf.draw(font_id, 'Job Number:')
    blf.position(font_id, 490 + aolen*sw + ailen*sw, 32, 0)
    blf.draw(font_id, scene.li_jobno)

def rendview(i):
    for scrn in bpy.data.screens:
        if scrn.name == 'Default':
            bpy.context.window.screen = scrn
            for area in scrn.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.viewport_shade = 'SOLID'
                            if i ==  1:
                                space.show_textured_solid = 1
                            else:
                                space.show_textured_solid = 0



