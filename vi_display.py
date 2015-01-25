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


import bpy, blf, colorsys, bgl, mathutils, bmesh
from math import pi
from numpy import digitize, array
try:
    import matplotlib
    mp = 1
except:
    mp = 0

from . import livi_export
from .vi_func import cmap, clearscene, skframe, selobj, retobjs, framerange, viewdesc, drawloop, drawpoly, draw_index, drawfont, skfpos, objmode

def ss_display():
    pass

def li_display(simnode, connode, geonode):
    scene, obreslist, obcalclist = bpy.context.scene, [], []
    (rcol, mtype) =  ('hot', 'livi') if 'LiVi' in simnode.bl_label else ('grey', 'shad')
    cmap(rcol)

    for geo in scene.objects:
        scene.objects.active = geo
        if getattr(geo, 'mode') != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')

    bpy.ops.object.select_all(action = 'DESELECT')

    if len(bpy.app.handlers.frame_change_pre) == 0:
        bpy.app.handlers.frame_change_pre.append(livi_export.cyfc1)
        
    for o in scene.objects:
        if geo.type == "MESH" and geo.get('licalc') and geo.hide == False:
            bpy.ops.object.select_all(action = 'DESELECT')
            obcalclist.append(o)

    scene.frame_set(scene.fs)
    scene.objects.active = None
    
    for i, o in enumerate([scene.objects[oname] for oname in scene['{}c'.format(mtype)]]):
        me = bpy.data.meshes.new(o.name+"res") 
        ores = bpy.data.objects.new(o.name+"res", me) 
        cv = ores.cycles_visibility
        cv.diffuse, cv.glossy, cv.transmission, cv.scatter, cv.shadow = 0, 0, 0, 0, 0
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        
        if scene['liparams']['cp'] == '0':  
            cindex = bm.faces.layers.int['cindex']
            for f in [f for f in bm.faces if f[cindex] < 1]:
                bm.faces.remove(f)
            [bm.verts.remove(v) for v in bm.verts if not v.link_faces]

        elif scene['liparams']['cp'] == '1':
            cindex =  bm.verts.layers.int['cindex']
            for v in [v for v in bm.verts if v[cindex] < 1]:
                bm.verts.remove(v)
        while bm.verts.layers.shape:
            bm.verts.layers.shape.remove(bm.verts.layers.shape[-1])
        
        for v in bm.verts:
            v.co += v.normal * geonode.offset if geonode else v.normal * simnode.offset
            
        bpy.context.scene.objects.link(ores)  
        
        obreslist.append(ores)
        ores['omax'], ores['omin'], ores['oave'], ores['lires']  = {}, {}, {}, 1 
        if connode and connode.bl_label == 'LiVi Compliance':
            for c in ('compmat', 'comps', 'crit', 'ecrit', 'ecomps'):
                ores[c] = o[c]
        selobj(scene, ores)
        

        for matname in ['{}#{}'.format(mtype, i) for i in range(20)]:
            if bpy.data.materials[matname] not in ores.data.materials[:]:
                bpy.ops.object.material_slot_add()
                ores.material_slots[-1].material = bpy.data.materials[matname]
        
        for fr, frame in enumerate(range(scene.fs, scene.fe + 1)):  
            if fr == 0:
                if scene.vi_disp_3d == 1 and scene['liparams']['cp'] == '0':
                    for face in bmesh.ops.extrude_discrete_faces(bm, faces = bm.faces)['faces']:
                        face.select = True
                bm.to_mesh(ores.data)
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            
            if connode and connode.bl_label == 'LiVi Compliance' and scene.vi_disp_sk:
                sv = bm.faces.layers.float['sv{}'.format(frame)] if scene['liparams']['cp'] == '0' else bm.verts.layers.float['sv{}'.format(frame)]
                for fi, f in enumerate(ores.data.polygons):
                    if scene['liparams']['cp'] == '0':
                        f.material_index = 11 if bm.faces[fi][sv] > 0 else 19
                    if scene['liparams']['cp'] == '1':
                        faceres = sum([v[sv] for v in bm.verts])/len(f.vertices)
                        f.material_index = 11 if faceres > 0 else 19
                oreslist = [f[sv] for f in bm.faces] if scene['liparams']['cp'] == '0' else [v[sv] for v in bm.verts]
            else:
                livires = bm.faces.layers.float['res{}'.format(frame)] if scene['liparams']['cp'] == '0' else bm.verts.layers.float['res{}'.format(frame)]
                try:
                    vals = array([(f[livires] - min(simnode['minres'].values()))/(max(simnode['maxres'].values()) - min(simnode['minres'].values())) for f in bm.faces]) if scene['liparams']['cp'] == '0' else \
                ([(sum([vert[livires] for vert in f.verts])/len(f.verts) - min(simnode['minres'].values()))/(max(simnode['maxres'].values()) - min(simnode['minres'].values())) for f in bm.faces])
                except:
                    vals = array([0 for f in bm.faces])
                bins = array([0.05*i for i in range(1, 20)])
                nmatis = digitize(vals, bins)
                for fi, f in enumerate(ores.data.polygons):
                    f.material_index = nmatis[fi]
                oreslist = [f[livires] for f in bm.faces] if scene['liparams']['cp'] == '0' else [v[livires] for v in bm.verts]

            if scene.fe - scene.fs > 0:
                [ores.data.polygons[fi].keyframe_insert('material_index', frame=frame) for fi in range(len(bm.faces))] 
            ores['omax'][str(frame)], ores['omin'][str(frame)], ores['oave'][str(frame)] = max(oreslist), min(oreslist), sum(oreslist)/len(oreslist)
        
        bm.free()
        if scene.vi_disp_3d == 1:
            selobj(scene, ores)
            bpy.ops.object.shape_key_add(from_mix = False)
            for frame in framerange(scene, simnode['Animation']):
                bpy.ops.object.shape_key_add(from_mix = False)
                ores.active_shape_key.name, ores.active_shape_key.value = str(frame), 1
                
    skframe('', scene, obreslist, simnode['Animation'])                                   
    bpy.ops.wm.save_mainfile(check_existing = False)
    scene.frame_set(scene.fs)
    rendview(1)

def spnumdisplay(disp_op, context, simnode):
    scene = context.scene
    leg = 0 if simnode.bl_label == 'VI Sun Path' else 1
    if bpy.data.objects.get('SPathMesh'):
        ob = bpy.data.objects['SPathMesh']    
        if scene.hourdisp == True:
            blf.enable(0, 4)
            blf.shadow(0, 5,scene.vi_display_rp_fsh[0], scene.vi_display_rp_fsh[1], scene.vi_display_rp_fsh[2], scene.vi_display_rp_fsh[3])
            bgl.glColor4f(scene.vi_display_rp_fc[0], scene.vi_display_rp_fc[1], scene.vi_display_rp_fc[2], scene.vi_display_rp_fc[3])
            blf.size(0, scene.vi_display_rp_fs, 72)
            mid_x, mid_y, width, height = viewdesc(context)
            view_mat = context.space_data.region_3d.perspective_matrix
            view_pivot = bpy.context.active_object.location if bpy.context.active_object and context.user_preferences.view.use_rotate_around_active else context.region_data.view_location

            if context.space_data.region_3d.is_perspective:
                vw = mathutils.Vector((-view_mat[3][0], -view_mat[3][1], -view_mat[3][2])).normalized()
                view_location = view_pivot + vw.normalized() * bpy.context.region_data.view_distance        
            else:
                vw =  mathutils.Vector((0.0, 0.0, 1.0))
                vw.rotate(bpy.context.region_data.view_rotation)
                view_location = view_pivot + vw.normalized()*bpy.context.region_data.view_distance*10 

            ob_mat = ob.matrix_world
            total_mat = view_mat * ob_mat
            posis = [total_mat*mathutils.Vector(co).to_4d() for co in ob['numpos'].values() if mathutils.Vector.angle(vw, view_location - ob_mat*mathutils.Vector(co)) < pi * 0.5 and not scene.ray_cast(0.95*ob_mat*mathutils.Vector(co), view_location)[0]]
            hs = [int(t.split('-')[1]) for t in ob['numpos'].keys() if total_mat*mathutils.Vector(ob['numpos'][t]).to_4d() in posis]
            draw_index(context, leg, mid_x, mid_y, width, height, posis, hs)
            blf.disable(0, 4)
    else:
        return

def linumdisplay(disp_op, context, simnode, connode, geonode):
    scene = context.scene    
    if not scene.vi_display:
        return
    if scene.frame_current not in range(scene.fs, scene.fe + 1):
        disp_op.report({'INFO'},"Outside result frame range")
        return

    obreslist = [ob for ob in scene.objects if ob.type == 'MESH'  and 'lightarray' not in ob.name and ob.hide == False and ob.layers[scene.active_layer] == True and ob.get('lires')]
                    
    if (scene.li_disp_panel != 2 and scene.ss_disp_panel != 2) or scene.vi_display_rp != True \
         or (bpy.context.active_object not in obreslist and scene.vi_display_sel_only == True)  \
         or (bpy.context.active_object and bpy.context.active_object.mode == 'EDIT'):
        return
        
    objmode()    
    blf.enable(0, 4)
    blf.shadow(0, 5, scene.vi_display_rp_fsh[0], scene.vi_display_rp_fsh[1], scene.vi_display_rp_fsh[2], scene.vi_display_rp_fsh[3])
    bgl.glColor4f(*scene.vi_display_rp_fc[:])
    blf.size(0, scene.vi_display_rp_fs, 72)
    bgl.glColor3f = scene.vi_display_rp_fc
    fn = context.scene.frame_current - scene.fs
    mid_x, mid_y, width, height = viewdesc(context)
    view_mat = context.space_data.region_3d.perspective_matrix
#    view_pivot = context.region_data.view_location bpy.context.active_object.location if bpy.context.active_object and context.user_preferences.view.use_rotate_around_active else context.region_data.view_location
    view_pivot = context.region_data.view_location

    if context.space_data.region_3d.is_perspective:
        vw = mathutils.Vector((-view_mat[3][0], -view_mat[3][1], -view_mat[3][2])).normalized()
        view_location = view_pivot + (vw * bpy.context.region_data.view_distance)    
    else:
        vw =  mathutils.Vector((0.0, 0.0, 1.0))
        vw.rotate(bpy.context.region_data.view_rotation)
        view_location = view_pivot + vw.normalized()*bpy.context.region_data.view_distance * 100       

    if scene.vi_display_sel_only == False:
        obd = obreslist
    else:
        obd = [context.active_object] if context.active_object in obreslist else []

    for ob in obd:
        if ob.data.shape_keys and str(fn) in [sk.name for sk in ob.data.shape_keys.key_blocks] and ob.active_shape_key.name != str(fn):
            ob.active_shape_key_index = [sk.name for sk in ob.data.shape_keys.key_blocks].index(str(fn))

        obm = ob.data
        omw = ob.matrix_world
        total_mat = view_mat * omw
        bm = bmesh.new()
        bm.from_mesh(obm)
        bm.transform(omw)

        if scene['liparams']['cp'] == "0":
            livires = bm.faces.layers.float['res{}'.format(scene.frame_current)]
            if not scene.vi_disp_3d:
                faces = [f for f in bm.faces if not f.hide and mathutils.Vector.angle(vw, view_location - f.calc_center_median()) < pi * 0.5]
                faces = [f for f in faces if not scene.ray_cast(f.calc_center_median() + scene.vi_display_rp_off * f.normal, view_location)[0]] if scene.vi_display_vis_only else faces
                fcs = [view_mat*f.calc_center_bounds().to_4d() for f in faces]
            else:
                sk = bm.verts.layers.shape[scene.frame_current]
                faces = [f for f in bm.faces if f.select and not f.hide]
                fpos = [skfpos(ob, scene.frame_current, [v.index for v in f.verts]) for f in faces]
                faces = [f for fi, f in enumerate(faces) if mathutils.Vector.angle(vw, view_location - f.calc_center_median()) < pi * 0.5]
                fpos = [skfpos(ob, scene.frame_current, [v.index for v in f.verts]) for f in faces]
                faces = [f for fi, f in enumerate(faces) if not scene.ray_cast(fpos[fi] + scene.vi_display_rp_off * f.normal, view_location)[0]] if scene.vi_display_vis_only else faces
                fpos = [skfpos(ob, scene.frame_current, [v.index for v in f.verts]) for f in faces]
                fcs = [view_mat*fpos[fi].to_4d() for fi, f in enumerate(faces)]
            res = [f[livires] for f in faces]
            draw_index(context, scene.vi_leg_display, mid_x, mid_y, width, height, fcs, res)
        else:
            livires = bm.verts.layers.float['res{}'.format(scene.frame_current)]              
            if not scene.vi_disp_3d:
                verts = [v for v in bm.verts if not v.hide and mathutils.Vector.angle(vw, view_location - v.co) < pi * 0.5]
                verts = [v for v in verts if not scene.ray_cast(v.co + scene.vi_display_rp_off * v.normal, view_location)[0]] if scene.vi_display_vis_only else verts
                vcs = [view_mat*v.co.to_4d() for v in verts]                
            else:
                verts = [v for v in bm.verts if not v.hide and mathutils.Vector.angle(vw, view_location - omw*(ob.data.shape_keys.key_blocks[str(scene.frame_current)].data[v.index].co)) < pi * 0.5]
                verts = [v for v in verts if not scene.ray_cast(omw*(ob.data.shape_keys.key_blocks[str(scene.frame_current)].data[v.index].co) + scene.vi_display_rp_off * v.normal, view_location)[0]] if scene.vi_display_vis_only else verts
                vcs = [total_mat*ob.data.shape_keys.key_blocks[str(scene.frame_current)].data[v.index].co.to_4d() for v in verts]
            res = [v[livires] for v in verts]
            draw_index(context, scene.vi_leg_display, mid_x, mid_y, width, height, vcs, res)

        bm.free()
    blf.disable(0, 4)

def li3D_legend(self, context, simnode, connode, geonode):
    scene = context.scene
    fc = str(scene.frame_current)
    try:
        if scene.vi_leg_display != True or scene.vi_display == 0 or (scene.wr_disp_panel != 1 and scene.li_disp_panel != 2 and scene.ss_disp_panel != 2) or scene.frame_current not in range(scene.fs, scene.fe + 1):
            return
        else:
            resvals = [('{:.1f}', '{:.0f}')[scene.vi_leg_max >= 100].format(scene.vi_leg_min+i*(scene.vi_leg_max - scene.vi_leg_min)/19) for i in range(20)]    
            height = context.region.height
            lenres = len(resvals[-1])
            font_id = 0
            drawpoly(20, height - 40, 70 + lenres*8, height - 520)
            drawloop(19, height - 40, 70 + lenres*8, height - 520)
    
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
#            print(connode)
#            cu = connode['unit'] if connode else '% Sunlit'    
            drawfont(scene['liparams']['unit'], font_id, 0, height, 25, 57)
            bgl.glLineWidth(1)
            bgl.glDisable(bgl.GL_BLEND)
            height = context.region.height
            font_id = 0
            bgl.glColor4f(0.0, 0.0, 0.0, 0.8)
            blf.size(font_id, 20, 48)
            if context.active_object and context.active_object.get('lires'):
                drawfont("Ave: {:.1f}".format(context.active_object['oave'][fc]), font_id, 0, height, 22, 480)
                drawfont("Max: {:.1f}".format(context.active_object['omax'][fc]), font_id, 0, height, 22, 495)
                drawfont("Min: {:.1f}".format(context.active_object['omin'][fc]), font_id, 0, height, 22, 510)
            else:
                drawfont("Ave: {:.1f}".format(simnode['avres'][fc]), font_id, 0, height, 22, 480)
                drawfont("Max: {:.1f}".format(simnode['maxres'][fc]), font_id, 0, height, 22, 495)
                drawfont("Min: {:.1f}".format(simnode['minres'][fc]), font_id, 0, height, 22, 510)
    
    except Exception as e:
        print(e, 'Turning off legend display')
        scene.vi_leg_display = 0
        scene.update()
        
def viwr_legend(self, context, simnode):
    scene = context.scene
    if scene.vi_leg_display != True or scene.vi_display == 0:
        return
    else:
        try:
            resvals = ['{0:.0f} to {1:.0f}'.format(2*i, 2*(i+1)) for i in range(simnode['nbins'])]
            resvals[-1] = resvals[-1][:-int(len('{:.0f}'.format(simnode['maxres'])))] + u"\u221E"
            height, lenres, font_id = context.region.height, len(resvals[-1]), 0
            drawpoly(20, height - 40, 70 + lenres*8, height - (simnode['nbins']+6)*20)
            drawloop(19, height - 40, 70 + lenres*8, height - (simnode['nbins']+6)*20)
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
            drawfont(cu, font_id, 0, height, 25, 57)
            bgl.glLineWidth(1)
            bgl.glDisable(bgl.GL_BLEND)
            height = context.region.height
            font_id = 0
            bgl.glColor4f(0.0, 0.0, 0.0, 0.8)
            blf.size(font_id, 20, 48)
            drawfont("Ave: {:.1f}".format(simnode['avres']), font_id, 0, height, 22, simnode['nbins']*20 + 85)
            drawfont("Max: {:.1f}".format(simnode['maxres']), font_id, 0, height, 22, simnode['nbins']*20 + 100)
            drawfont("Min: {:.1f}".format(simnode['minres']), font_id, 0, height, 22, simnode['nbins']*20 + 115)
        except:
            scene.vi_display = 0
            
def li_compliance(self, context, connode):
    height, scene = context.region.height, context.scene
    if not scene.get('li_compliance') or scene.frame_current not in range(scene.fs, scene.fe + 1) or scene.li_disp_panel < 2:
        return
    if connode.analysismenu == '0':
        buildtype = ('School', 'Higher Education', 'Healthcare', 'Residential', 'Retail', 'Office & Other')[int(connode.bambuildmenu)]
    elif connode.analysismenu == '1':
        buildtype = 'Residential'
        cfshpfsdict = {'totkit': 0, 'kitdf': 0, 'kitsv': 0, 'totliv': 0, 'livdf': 0, 'livsv': 0}

    drawpoly(100, height - 40, 900, height - 65)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    horpos, widths = (100, 317, 633, 900), (100, 450, 600, 750, 900)

    for p in range(3):
        drawloop(horpos[p], height - 40, horpos[p+1], height - 65)

    font_id = 0
    blf.size(font_id, 20, 54)
    drawfont('Standard: '+('BREEAM HEA1', 'CfSH', 'LEED EQ8.1', 'Green Star')[int(connode.analysismenu)], font_id, 0, height, 110, 58)
    drawfont('Project Name: '+scene.li_projname, font_id, 0, height, 643, 58)
    blf.size(font_id, 20, 40)

    def space_compliance(os):
        frame, buildspace, pfs, epfs, lencrit = scene.frame_current, '', [], [], 0
        for o in os:
            mat = bpy.data.materials[o['compmat']]
            o['cr4'] = [('fail', 'pass')[int(com)] for com in o['comps'][frame][:][::2]]
            o['cr6'] = [cri[4] for cri in o['crit']]
            if 'fail' in [c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '1'] or bpy.context.scene['dfpass'][frame] == 1:
                pf = 'FAIL'
            elif 'pass' not in [c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.75'] and len([c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.75']) > 0:
                if 'pass' not in [c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.5'] and len([c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.5']) > 0:
                    pf = 'FAIL'
                else:
                    pf = 'PASS'
            else:
                pf = 'PASS'
            pfs.append(pf)

            if connode.analysismenu == '1':
                cfshpfsdict[('totkit', 'totliv')[mat.crspacemenu == '1']] += 1
                if o['cr4'][0] == 'pass':
                    cfshpfsdict[('kitdf', 'livdf')[mat.crspacemenu == '1']] += 1
                if o['cr4'][1] == 'pass':
                    cfshpfsdict[('kitsv', 'livsv')[mat.crspacemenu == '1']] += 1

            if connode.analysismenu == '0':
                ecrit = o['ecrit']
                o['ecr4'] = [('fail', 'pass')[int(com)] for com in o['ecomps'][frame][:][::2]]
                o['ecr6'] = [ecri[4] for ecri in ecrit]
                if 'fail' in [c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '1'] or bpy.context.scene['dfpass'][frame] == 1:
                    epf = 'FAIL'
                elif 'pass' not in [c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '0.75'] and len([c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '0.75']) > 0:
                    if 'pass' not in [c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '0.5'] and len([c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '0.5']) > 0:
                        epf = 'FAIL'
                    else:
                        epf = 'EXEMPLARY'
                else:
                    epf = 'EXEMPLARY'
                epfs.append(epf)

        if bpy.context.active_object in os:
            o = bpy.context.active_object
            lencrit = 1 + len(o['crit'])
            drawpoly(100, height - 70, 900, height - 70  - (lencrit)*25)
            drawloop(100, height - 70, 900, height - 70  - (lencrit)*25)
            mat = bpy.data.materials[o['compmat']]
            if connode.analysismenu == '0':
                buildspace = ('', '', (' - Public/Staff', ' - Patient')[int(mat.hspacemenu)], (' - Kitchen', ' - Living/Dining/Study', ' - Communal')[int(mat.brspacemenu)], (' - Sales', ' - Office')[int(mat.respacemenu)], '')[int(connode.bambuildmenu)]
            elif connode.analysismenu == '1':
                buildspace = (' - Kitchen', ' - Living/Dining/Study')[int(mat.crspacemenu)]

            titles = ('Zone Metric', 'Target', 'Achieved', 'PASS/FAIL')
            tables = [[] for c in range(lencrit -1)]
            etables = [[] for e in range(len(o['ecrit']))]
            
            for c, cr in enumerate(o['crit']):
                if cr[0] == 'Percent':
                    if cr[2] == 'Skyview':
                        tables[c] = ('Percentage area with Skyview (%)', cr[1], '{:.2f}'.format(o['comps'][frame][:][c*2 + 1]), o['cr4'][c].upper())
                    elif cr[2] == 'DF':  
                        tables[c] = ('Average Daylight Factor (%)', cr[3], '{:.2f}'.format(o['comps'][frame][:][c*2 + 1]), o['cr4'][c].upper())
                    elif cr[2] == 'PDF':    
                        tables[c] = ('Area with point Daylight Factor above {}'.format(cr[3]), cr[1], '{:.2f}'.format(o['comps'][frame][:][c*2 + 1]), o['cr4'][c].upper())
                elif cr[0] == 'Ratio':
                    tables[c] = ('Uniformity ratio', cr[3], '{:.2f}'.format(o['comps'][frame][:][c*2 + 1]), o['cr4'][c].upper())
                elif cr[0] == 'Min':
                    tables[c] = ('Minimum {} (%)'.format('Point Daylight Factor'), cr[3], '{:.2f}'.format(o['comps'][frame][:][c*2 + 1]), o['cr4'][c].upper())
                elif cr[0] == 'Average':
                    tables[c] = ('Average {} (%)'.format('Daylight Factor'), cr[3], '{:.2f}'.format(o['comps'][frame][:][c*2 + 1]), o['cr4'][c].upper())

            if connode.analysismenu == '0':
                for e, ecr in enumerate(ecrit):
                    if ecr[0] == 'Percent':
                        if ecr[2] == 'skyview':
                            etables[e] = ('Percentage area with Skyview (%)', ecr[1], '{:.2f}'.format(o['ecomps'][frame][:][e*2 + 1]), o['ecr4'][e].upper())
                        elif ecr[2] == 'DF':  
                            etables[e] = ('Average Daylight Factor (%)', ecr[3], '{:.2f}'.format(o['ecomps'][frame][:][e*2 + 1]), o['ecr4'][e].upper())
                        elif ecr[2] == 'PDF':    
                            etables[e] = ('Area with point Daylight Factor above {}'.format(ecr[3]), ecr[1], '{:.2f}'.format(o['ecomps'][frame][:][e*2 + 1]), o['ecr4'][e].upper())
                    elif ecr[0] == 'Min':
                        etables[e] = ('Minimum {} (%)'.format('Point Daylight Factor'), ecr[3], '{:.2f}'.format(o['ecomps'][frame][:][e*2 + 1]), o['ecr4'][e].upper())

            for j in range(4):
                drawloop(widths[j], height - 70, widths[j+1], height - 95)

            bgl.glEnable(bgl.GL_LINE_STIPPLE)
            for t, tab in enumerate(tables):
                for j in range(4):
                    drawloop(widths[j], height - 95 - t*25, widths[j+1], height - 120 - t*25)
                    if tab[j] == 'FAIL':
                        bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
                    elif tab[j] == 'PASS':
                        bgl.glColor4f(0.0, 0.7, 0.0, 1.0)
                    blf.size(font_id, 20, 44)
                    drawfont(tab[j], 0, 0, height, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], 113 + t*25)
                    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                    if t == 0:
                        blf.size(font_id, 20, 48)
                        drawfont(titles[j], 0, 0, height, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], 88)
            bgl.glDisable(bgl.GL_LINE_STIPPLE)
        else:
            etables = []
            lencrit = 0

        tpf = 'FAIL' if 'FAIL' in pfs or 'FAIL*' in pfs else 'PASS'
        if connode.analysismenu == '0':            
            (tpf, lencrit) = ('EXEMPLARY', lencrit + len(o['ecrit'])) if tpf == 'PASS' and ('FAIL' not in epfs and 'FAIL*' not in epfs) else (tpf, lencrit)

        return(tpf, lencrit, buildspace, etables)
    
    build_compliance, lencrit, bs, etables = space_compliance([o for o in bpy.data.objects if o.get('lires')])

    if build_compliance == 'EXEMPLARY':
        for t, tab in enumerate(etables):
            if t == 0:
                drawpoly(100, height - 70 - (lencrit * 25), 900, height - 70 - ((lencrit - len(etables)) * 25))
                drawloop(100, height - 70 - (lencrit * 25), 900, height - 70 - ((lencrit - len(etables)) * 25))
            for j in range(4):
                bgl.glEnable(bgl.GL_LINE_STIPPLE)
                drawloop(widths[j], height - 95 - (lencrit - len(etables) + t - 1) * 25, widths[j+1], height - 120 - (lencrit - len(etables) + t - 1) * 25)
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
        drawpoly(100, height - 70 - lencrit*26, 525, height - 95 - lencrit*26)
        drawloop(100, height - 70 - lencrit*26, 350, height - 95 - lencrit*26)
        drawloop(100, height - 70 - lencrit*26, 350, height - 95 - lencrit*26)
        drawloop(350, height - 70 - lencrit*26, 525, height - 95 - lencrit*26)
        blf.draw(font_id, 'Building Compliance:')
        drawfont(build_compliance, 0, lencrit, height, 250, 87)
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
        drawpoly(100, height - 70 - lencrit*26, 300, height - 95 - lencrit*26)
        drawloop(100, height - 70 - lencrit*26, 300, height - 95 - lencrit*26)
        drawfont('Credits achieved:', 0, lencrit, height, 110, 87)
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
    drawpoly(100, 50, 500 + aolen*sw + ailen*sw + jnlen*sw, 25)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    drawloop(100, 50, 260 + aolen*sw, 25)
    drawloop(260 + aolen*sw, 50, 400 + aolen*sw + ailen*sw, 25)
    drawloop(400 + aolen*sw + ailen*sw, 50, 500 + aolen*sw + ailen*sw + jnlen*sw, 25)
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
                            space.clip_start = 0.1
                            bpy.context.scene['cs'] = space.clip_start

