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


import bpy, blf, colorsys, bgl, mathutils, bmesh, datetime
from bpy_extras import view3d_utils
from math import pi, sin, cos, atan2, log10, ceil
from numpy import sum as nsum
try:
    import matplotlib
    mp = 1
except:
    mp = 0

from . import livi_export
from .vi_func import cmap, skframe, selobj, retvpvloc, viewdesc, drawloop, drawpoly, draw_index, drawfont 
from .vi_func import retdp, objmode, drawcircle, drawtri, setscenelivivals, draw_time, retcols, draw_index_distance

nh = 768

def ss_display():
    pass

def li_display(simnode):
    scene, obreslist, obcalclist = bpy.context.scene, [], []
    setscenelivivals(scene)
    
    (rcol, mtype) =  ('hot', 'livi') if 'LiVi' in simnode.bl_label else ('grey', 'shad')
    cmap(scene)

    for geo in scene.objects:
        scene.objects.active = geo
        if getattr(geo, 'mode') != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')

    bpy.ops.object.select_all(action = 'DESELECT')

    if not bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(livi_export.cyfc1)
        
    for o in scene.objects:
        if o.type == "MESH" and o.get('licalc') and o.hide == False:
            bpy.ops.object.select_all(action = 'DESELECT')
            obcalclist.append(o)
    
    scene.frame_set(scene['liparams']['fs'])
    scene.objects.active = None
    
    for i, o in enumerate([scene.objects[oname] for oname in scene['liparams']['{}c'.format(mtype)]]):        
        bm = bmesh.new()
        bm.from_mesh(o.data)  
        bm.transform(o.matrix_world)
#        bm.normal_update() 
        
        if scene['liparams']['cp'] == '0':  
            cindex = bm.faces.layers.int['cindex']
            for f in [f for f in bm.faces if f[cindex] < 1]:
                bm.faces.remove(f)
            [bm.verts.remove(v) for v in bm.verts if not v.link_faces]

        elif scene['liparams']['cp'] == '1':
            cindex =  bm.verts.layers.int['cindex']
            for v in [v for v in bm.verts if v[cindex] < 1]:
                bm.verts.remove(v)
            for v in bm.verts:
                v.select = True
        
        while bm.verts.layers.shape:
            bm.verts.layers.shape.remove(bm.verts.layers.shape[-1])
        
        for v in bm.verts:
            v.co += mathutils.Vector((nsum([f.normal for f in v.link_faces], axis = 0))).normalized()  * simnode['goptions']['offset']
        
        selobj(scene, o)
        bpy.ops.object.duplicate() 
        if not bpy.context.active_object:
            bpy.ops.view3d.localview()
        ores = bpy.context.active_object
        ores.name, ores.show_wire, ores.draw_type = o.name+"res", 1, 'SOLID'
        while ores.material_slots:
            bpy.ops.object.material_slot_remove()

        cv = ores.cycles_visibility
        cv.diffuse, cv.glossy, cv.transmission, cv.scatter, cv.shadow = 0, 0, 0, 0, 0        
        obreslist.append(ores)
        ores['omax'], ores['omin'], ores['oave'], ores['lires']  = o['omax'], o['omin'], o['oave'], 1 
        if scene['viparams']['visimcontext'] == 'LiVi Compliance':
            for c in ('compmat', 'comps', 'crit', 'ecrit', 'ecomps'):
                ores[c] = o[c]
        selobj(scene, ores)
        
        for matname in ['{}#{}'.format('vi-suite', i) for i in range(20)]:
            if bpy.data.materials[matname] not in ores.data.materials[:]:
                bpy.ops.object.material_slot_add()
                ores.material_slots[-1].material = bpy.data.materials[matname]
        
        if scene.vi_disp_3d == 1 and scene['liparams']['cp'] == '0':
            for face in bmesh.ops.extrude_discrete_faces(bm, faces = bm.faces)['faces']:
                face.select = True
                        
        bm.transform(o.matrix_world.inverted())
        bm.to_mesh(ores.data)
        bm.free()
        ores.lividisplay(scene)
                
        if scene.vi_disp_3d == 1 and ores.data.shape_keys == None:
            selobj(scene, ores)
            bpy.ops.object.shape_key_add(from_mix = False)
            for frame in range(scene['liparams']['fs'], scene['liparams']['fe'] + 1):
                bpy.ops.object.shape_key_add(from_mix = False)
                ores.active_shape_key.name, ores.active_shape_key.value = str(frame), 1
                
    skframe('', scene, obreslist)                                   
    bpy.ops.wm.save_mainfile(check_existing = False)
    scene.frame_set(scene['liparams']['fs'])
    rendview(1)

def spnumdisplay(disp_op, context, simnode):
    scene = context.scene
#    leg = 0 if simnode.bl_label == 'VI Sun Path' else 1
    if bpy.data.objects.get('SPathMesh'):
        spob = bpy.data.objects['SPathMesh'] 
        ob_mat = spob.matrix_world
        mid_x, mid_y, width, height = viewdesc(context)
        vl = retvpvloc(context)
                
        if scene.hourdisp:
            pvecs = [ob_mat * mathutils.Vector(p[:]) for p in spob['numpos'].values()]
            pvals = [int(p.split('-')[1]) for p in spob['numpos'].keys()]
            p2ds = [view3d_utils.location_3d_to_region_2d(context.region, context.region_data, p) for p in pvecs]
            
            try:
                (hs, posis) = map(list, zip(*[[p, p2ds[pi]] for pi, p in enumerate(pvals) if p2ds[pi] and 0 < p2ds[pi][0] < width and 0 < p2ds[pi][1] < height and not scene.ray_cast(pvecs[pi] - 0.05 * (pvecs[pi] - vl), vl - 0.95 * pvecs[pi])[0]]))
                draw_index(posis, hs, scene.vi_display_rp_fs, scene.vi_display_rp_fc, scene.vi_display_rp_fsh)
            except Exception as E:
                print(E)
            blf.disable(0, 4)

        if [ob.get('VIType') == 'Sun' for ob in bpy.data.objects]:
            sobs = [ob for ob in bpy.data.objects if ob.get('VIType') == 'Sun']
            if sobs and scene.timedisp:
                sunloc = ob_mat * sobs[0].location
                solpos = view3d_utils.location_3d_to_region_2d(context.region, context.region_data, sunloc)
                try:
                    if 0 < solpos[0] < width and 0 < solpos[1] < height and not scene.ray_cast(sobs[0].location + 0.05 * (vl - sunloc), vl- sunloc)[0]:
                        blf.enable(0, 4)
                        blf.shadow(0, 5, *scene.vi_display_rp_fsh)
                        bgl.glColor4f(*scene.vi_display_rp_fc)
#                        blf.size(0, scene.vi_display_rp_fs, 72)
                        soltime = datetime.datetime.fromordinal(scene.solday)
                        soltime += datetime.timedelta(hours = scene.solhour)
                        sre = sobs[0].rotation_euler
                        draw_time(solpos, soltime.strftime('  %d %b %X') + ' alt: {:.1f} azi: {:.1f}'.format(90 - sre[0]*180/pi, (180, -180)[sre[2] < -pi] - sre[2]*180/pi), 
                                   scene.vi_display_rp_fs, scene.vi_display_rp_fc, scene.vi_display_rp_fsh)
                        
                except:
                    pass
    else:
        return

def linumdisplay(disp_op, context, simnode):
    scene = context.scene    
    if not scene.get('viparams') or scene['viparams']['vidisp'] not in ('lipanel', 'sspanel', 'lcpanel'):
        scene.vi_display = 0
        return
    if scene.frame_current not in range(scene['liparams']['fs'], scene['liparams']['fe'] + 1):
        disp_op.report({'INFO'},"Outside result frame range")
        return

    obreslist = [ob for ob in scene.objects if ob.type == 'MESH'  and 'lightarray' not in ob.name and ob.hide == False and ob.layers[scene.active_layer] == True and ob.get('lires')]
                    
    if scene.vi_display_rp != True \
         or (bpy.context.active_object not in obreslist and scene.vi_display_sel_only == True)  \
         or (bpy.context.active_object and bpy.context.active_object.mode == 'EDIT'):
        return
        
    objmode()    
    fn = context.scene.frame_current - scene['liparams']['fs']
    mid_x, mid_y, width, height = viewdesc(context)
    view_location = retvpvloc(context)

    if scene.vi_display_sel_only == False:
        obd = obreslist
    else:
        obd = [context.active_object] if context.active_object in obreslist else []

    for ob in obd:
        if ob.data.shape_keys and str(fn) in [sk.name for sk in ob.data.shape_keys.key_blocks] and ob.active_shape_key.name != str(fn):
            ob.active_shape_key_index = [sk.name for sk in ob.data.shape_keys.key_blocks].index(str(fn))
        try:
            omw = ob.matrix_world
            bm = bmesh.new()
            bm.from_mesh(ob.to_mesh(scene = scene, apply_modifiers = True, settings = 'PREVIEW'))
            bm.transform(omw)
    
            if bm.faces.layers.float.get('res{}'.format(scene.frame_current)): 
                livires = bm.faces.layers.float['res{}'.format(scene.frame_current)]
                faces = [f for f in bm.faces if f.select] if scene.vi_disp_3d else bm.faces
                distances = [(view_location - f.calc_center_bounds() + scene.vi_display_rp_off * f.normal.normalized()).length for f in faces]
                            
                if scene.vi_display_vis_only:
                    fcos = [f.calc_center_bounds() + scene.vi_display_rp_off * f.normal.normalized() for f in faces]
                    direcs = [view_location - f for f in fcos]
#                    distances = [d.length for d in direcs]
                    (faces, distances) = map(list, zip(*[[f, distances[i]] for i, f in enumerate(faces) if not scene.ray_cast(fcos[i], direcs[i], distance=distances[i])[0]]))

                face2d = [view3d_utils.location_3d_to_region_2d(context.region, context.region_data, f.calc_center_bounds()) for f in faces]
                (faces, pcs, depths) = map(list, zip(*[[f, face2d[fi], distances[fi]] for fi, f in enumerate(faces) if face2d[fi] and 0 < face2d[fi][0] < width and 0 < face2d[fi][1] < height]))          
                res = [f[livires] for f in faces]
            
            elif bm.verts.layers.float.get('res{}'.format(scene.frame_current)):            
                livires = bm.verts.layers.float['res{}'.format(scene.frame_current)]                         
                verts = [v for v in bm.verts if not v.hide and v.select]
                distances = [(view_location - v.co + scene.vi_display_rp_off * v.normal.normalized()).length for v in verts]
                
                if scene.vi_display_vis_only:
                    vcos = [v.co + scene.vi_display_rp_off * v.normal.normalized() for v in verts]
                    direcs = [view_location - v for v in vcos]
#                    distances = [d.length for d in direcs]
                    (verts, distances) = map(list, zip(*[[v, distances[i]] for i, v in enumerate(verts) if not scene.ray_cast(vcos[i], direcs[i], distance=distances[i])[0]]))
                    
                vert2d = [view3d_utils.location_3d_to_region_2d(context.region, context.region_data, v.co) for v in verts]
                (verts, pcs, depths) = map(list, zip(*[[v, vert2d[vi], distances[vi]] for vi, v in enumerate(verts) if vert2d[vi] and 0 < vert2d[vi][0] < width and 0 < vert2d[vi][1] < height]))
                res = [v[livires] for v in verts]
            
            draw_index_distance(pcs, res, scene.vi_display_rp_fs, scene.vi_display_rp_fc, scene.vi_display_rp_fsh, depths)    
            bm.free()
            
        except Exception as e:
            print(e)
    blf.disable(0, 4)

def li3D_legend(self, context, simnode):
    scene = context.scene
    fc = str(scene.frame_current)
    dplaces = retdp(context, scene.vi_leg_max)
    
    if not scene.get('liparams'):
        scene.vi_display = 0
        return

    try:
        if scene.frame_current not in range(scene['liparams']['fs'], scene['liparams']['fe'] + 1) or not scene.vi_leg_display  or not any([o.lires for o in scene.objects]) or scene['liparams']['unit'] == 'Sky View':
            return
        else:
            mid_x, mid_y, width, height = viewdesc(context)
            bgl.glLineWidth(1)
            resvals = [format(scene.vi_leg_min + i*(scene.vi_leg_max - scene.vi_leg_min)/19, '.{}f'.format(dplaces)) for i in range(20)] if scene.vi_leg_scale == '0' else \
                        [format(scene.vi_leg_min + (1 -log10(i)/log10(20))*(scene.vi_leg_max - scene.vi_leg_min), '.{}f'.format(dplaces)) for i in range(1, 21)[::-1]]
            lenres = len(resvals[-1])
            font_id = 0
            drawpoly(20, height - 40, 70 + lenres*8, height - 520, 1, 1, 1, 0.9)
            drawloop(19, height - 40, 70 + lenres*8, height - 520)
            blf.enable(0, blf.SHADOW)
            blf.enable(0, blf.KERNING_DEFAULT)
            blf.shadow(0, 5, 0, 0, 0, 0.7)
            cols = retcols(scene)
            for i in range(20):
                rgba = cols[i]
                drawpoly(20, (i*20)+height - 440, 60, (i*20)+height - 460, *rgba)    
                blf.size(font_id, 20, 48)
                bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                blf.position(font_id, 65, (i*20)+height - 455, 0)
                blf.draw(font_id, "  "*(lenres - len(resvals[i]) ) + resvals[i])    
            
            blf.size(font_id, 20, 56)    
            drawfont(scene['liparams']['unit'], font_id, 0, height, 25, 57)
            bgl.glDisable(bgl.GL_BLEND)
            font_id = 0
            bgl.glColor4f(0.0, 0.0, 0.0, 0.8)
            blf.size(font_id, 20, 48)
            
            if context.active_object and context.active_object.get('lires'):
                drawfont("Ave: {}".format(format(context.active_object['oave'][fc], '.{}f'.format(dplaces))), font_id, 0, height, 22, 480)
                drawfont("Max: {}".format(format(context.active_object['omax'][fc], '.{}f'.format(dplaces))), font_id, 0, height, 22, 495)
                drawfont("Min: {}".format(format(context.active_object['omin'][fc], '.{}f'.format(dplaces))), font_id, 0, height, 22, 510)
            else:
                drawfont("Ave: {}".format(format(scene['liparams']['avres'][fc], '.{}f'.format(dplaces))), font_id, 0, height, 22, 480)
                drawfont("Max: {}".format(format(scene['liparams']['maxres'][fc], '.{}f'.format(dplaces))), font_id, 0, height, 22, 495)
                drawfont("Min: {}".format(format(scene['liparams']['minres'][fc], '.{}f'.format(dplaces))), font_id, 0, height, 22, 510)
            
            blf.disable(0, blf.KERNING_DEFAULT)
            blf.disable(0, blf.SHADOW)
            
    except Exception as e:
        print(e, 'Turning off legend display')
        scene.vi_leg_display = 0
        scene.update()

def en_air(self, context, temp, ws, wd, hu):
    scene = context.scene

    if not scene.resaa_disp or scene['viparams']['vidisp'] not in ('en', 'enpanel'):
        return
    else:
        height, width, font_id = context.region.height, context.region.width, 0
        hscale, tmar, rmar = height/nh, 20, 20
        bheight, bwidth = hscale * 250, hscale * 350
        topheight = height - tmar
        leftwidth = width - int(rmar + bwidth)
        botheight = height - int(tmar + bheight)
        rightwidth = width - rmar
        drawpoly(leftwidth, topheight, rightwidth, botheight, 0.7, 1, 1, 1)
        drawloop(leftwidth - 1, topheight, rightwidth, botheight)
        blf.enable(0, 4)
        blf.size(font_id, 20, int(height/14))
        blf.shadow(0, 3, 0, 0, 0, 0.5)
        
        # Temperature
        maxval, minval = max(temp), min(temp)
        maxval, minval = max(temp), min(temp)
        reslevel = (temp[scene.frame_current] - minval)/(maxval - minval)
        blf.size(font_id, 20, int(height/14))
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        blf.position(font_id, int(leftwidth + hscale*5), int(topheight - hscale * 20), 0)
        blf.draw(font_id, u"T: {:.1f}\u00b0C".format(temp[scene.frame_current]))
        drawpoly(int(leftwidth + hscale * 10), botheight + int(0.9 * bheight * reslevel), int(leftwidth + hscale * 60), botheight, 1, *colorsys.hsv_to_rgb(1 - reslevel, 1.0, 1.0))
        drawloop(int(leftwidth + hscale * 10 - 1), botheight + int(0.9 * bheight * reslevel), int(leftwidth + hscale * 60), botheight)
        
        # Wind
        direcs = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
        if context.space_data.region_3d.is_perspective:
            view_mat = context.space_data.region_3d.perspective_matrix
            vw = mathutils.Vector((view_mat[3][0], view_mat[3][1], 0)).normalized()
        else:
            vw =  mathutils.Vector((0.0, 0.0, -1.0))
            vw.rotate(bpy.context.region_data.view_rotation)
        orot = atan2(vw[1],vw[0]) - atan2(1,0)
    
        scene, font_id, height = context.scene, 0, context.region.height
        maxws = max(ws)
        radius, hscale = 110, height/nh
        posx, posy = int(rightwidth - radius * hscale), int(topheight - hscale * radius * 1.2)
        blf.position(font_id, int(leftwidth + hscale * 160), int(topheight - hscale * 20), 0)
        blf.draw(font_id, "S: {:.1f}(m/s)".format(ws[scene.frame_current]))
        blf.position(font_id, int(leftwidth + hscale * 255), int(topheight - hscale * 20), 0)
        blf.draw(font_id, "D: {:.0f}deg".format(wd[scene.frame_current]))
        blf.disable(0, 4)
        for i in range(1, 6):
            drawcircle(mathutils.Vector((posx, posy)), 0.15 * hscale * radius * i, 36, 0, 0.7, 0, 0, 0) 

        blf.enable(0, 1)
        blf.enable(0, 4)
        blf.shadow(0, 3, 0, 0, 0, 0.5)

        for d in range(8):
            bgl.glEnable(bgl.GL_LINE_SMOOTH)
            bgl.glEnable(bgl.GL_BLEND);
            bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
            bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
            bgl.glLineWidth (2)
            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex2i(posx, posy)
            bgl.glVertex2i(int(posx + 0.8 * hscale * radius*sin(orot + d*pi/4)), int(posy + 0.8 * hscale * radius * cos(orot + d*pi/4)))
            bgl.glEnd()
            fdims = blf.dimensions(font_id, direcs[d])
            ang = orot + d*pi/4
            fwidth = fdims[0]*0.5
            blf.position(font_id, int(posx - fwidth*cos(ang) + hscale *0.825 * radius*sin(ang)), int(posy + fwidth*sin(ang) + hscale * 0.825 * radius * cos(ang)), 0)
            blf.rotation(font_id, - orot - d*pi*0.25)
            blf.draw(font_id, direcs[d])
        blf.disable(0, 4)
        blf.disable(0, 1)   
        drawtri(posx, posy, ws[scene.frame_current]/maxws, wd[scene.frame_current] + orot*180/pi, hscale, radius)
        
        # Humidity
        blf.enable(0, 4)
        maxval, minval = 100, 0
        reslevel = (hu[scene.frame_current] - minval)/(maxval - minval)
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glLoadIdentity()
        bgl.gluOrtho2D(0, width, 0, height)
        bgl.glMatrixMode(bgl.GL_MODELVIEW)
        bgl.glLoadIdentity()
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        blf.position(font_id, int(leftwidth + hscale * 75), int(topheight - hscale * 20), 0)
        blf.draw(font_id, "H: {:.1f}%".format(hu[scene.frame_current]))
        drawpoly(int(leftwidth + hscale * 80), botheight + int(0.9 * bheight * reslevel), int(leftwidth + hscale * 130), botheight, 1, *colorsys.hsv_to_rgb(1 - reslevel, 1.0, 1.0))
        drawloop(int(leftwidth + hscale * 80 - 1), botheight + int(0.9 * bheight * reslevel), int(leftwidth + hscale * 130), botheight)      
        blf.disable(0, 4)
    
class en_temp_panel():
    metrics = []
    location = (0,0)
    hum_location = (0,0)
    co2_location = (0,0)
    heat_location = (0,0)
    cool_location = (0,0)

    def __init__(self):
        self.expand = 0

    def xyminmax(self):
        return (self.location[0] - 50, self.location[1] - 50, self.location[0] + 50, self.location[1] + 50)
                
    def metrics(scene, resnode):
        rl = resnode['reslists']
        zrl = list(zip(*rl))
        reszones = [o.name.upper() for o in bpy.data.objects if o.name.upper() in zrl[2]]
        if not bpy.context.active_object or 'EN_'+bpy.context.active_object.name.upper() not in reszones:
            return
        height, font_id = context.region.height, 0
        hscale = height/nh
        startx, starty, rowheight, totwidth = 20, height - 20, 20, 200
        resstart = 24 * (resnode['Start'] - resnode.dsdoy)
        resend = resstart + 24 * (1 + resnode['End'] - resnode['Start'])
        eznames = ['EN_{}'.format(o.name.upper()) for o in bpy.context.selected_objects]
        for ezname in eznames:
            tdata = [t.split()[resstart:resend] for ti, t in enumerate(zrl[4]) if zrl[3][ti] == 'Temperature (degC)' and zrl[2][ti] == ezname]
            metrics += [rl[ri][3] for ri in range(len(rl)) if rl[ri][2] == ezname]
        if 'Temperature (degC)' in set(metrics):
            tp = temp_panel()
            tp.location = (startx, starty)
    
def en_panel(self, context, resnode):
    scene = context.scene
    rl = resnode['reslists']
    zrl = list(zip(*rl))
    reszones = [o.name.upper() for o in bpy.data.objects if o.name.upper() in zrl[2]]
    if not bpy.context.active_object or 'EN_'+bpy.context.active_object.name.upper() not in reszones:
        return
    height, font_id = context.region.height, 0
    hscale = height/nh
    startx, starty, rowheight, totwidth = 20, height - 20, 20, 200
    resstart = 24 * (resnode['Start'] - resnode.dsdoy)
    resend = resstart + 24 * (1 + resnode['End'] - resnode['Start'])
    ezname = 'EN_'+bpy.context.active_object.name.upper()
    metrics = set([rl[ri][3] for ri in range(len(rl)) if rl[ri][2] == ezname])
    metricno = 6 * (0, 1)['Temperature (degC)' in metrics] + 6 * (0, 1)['Humidity (%)' in metrics] + 8 * (0, 1)['Heating (W)' in metrics] + 8 * (0, 1)['Zone air heating (W)' in metrics] + 8 * (0, 1)['Cooling (W)' in metrics] + 6 * (0, 1)['CO2 (ppm)' in metrics]
    rowno = 1
    if metricno:
        drawpoly(startx, starty, startx + int(hscale*totwidth), starty - int(hscale*rowheight*(1 + metricno)), 0.7, 1, 1, 1)
        drawloop(startx, starty, startx + int(hscale*totwidth), starty - int(hscale*rowheight*(1 + metricno)))
        blf.enable(0, 4)
        blf.shadow(0, 3, 0, 0, 0, 0.5)
        blf.size(font_id, 20, int(height/14))
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        
        if 'Temperature (degC)' in metrics:
            tdata = [t.split()[resstart:resend] for ti, t in enumerate(zrl[4]) if zrl[3][ti] == 'Temperature (degC)' and zrl[2][ti] == ezname]
            vals = [float(t) for t in tdata[0]]
            avval, maxval, minval, percenta, percentb = sum(vals)/len(vals), max(vals), min(vals), 100 * sum([val > scene.en_temp_max for val in vals])/len(vals), 100 * sum([val < scene.en_temp_min for val in vals])/len(vals) 
            blf.position(font_id, int(startx + hscale * 10), int(starty - hscale * rowheight * rowno), 0)
            blf.draw(font_id, 'Temperatures:')
            for tt, text in enumerate(('Average:', 'Maximum:', 'Minimum:', '% above {:.1f}'.format(scene.en_temp_max), '% below {:.1f}'.format(scene.en_temp_min))):
                blf.position(font_id, int(startx + hscale*10), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, text)
            for tt, text in enumerate((avval, maxval, minval, percenta, percentb)):
                blf.position(font_id, int(startx +  hscale*(totwidth * 0.6 + 10)), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, '{:.1f}'.format(text))
            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex2i(startx + int(hscale * totwidth * 0.2), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glVertex2i(startx + int(hscale*totwidth * 0.8), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glEnd()
            rowno += tt + 2
        
        if 'Humidity (%)' in metrics:
            hdata = [h.split()[resstart:resend] for hi, h in enumerate(zrl[4]) if zrl[3][hi] == 'Humidity (%)' and zrl[2][hi] == ezname]
            vals = [float(h) for h in hdata[0]]
            avval, maxval, minval, percenta, percentb = sum(vals)/len(vals), max(vals), min(vals), 100 * sum([val > scene.en_hum_max for val in vals])/len(vals), 100 * sum([val < scene.en_hum_min for val in vals])/len(vals) 
            blf.position(font_id, int(startx + hscale * 10), int(starty - hscale * rowheight * rowno), 0)
            blf.draw(font_id, 'Humidities:')
            for tt, text in enumerate(('Average:', 'Maximum:', 'Minimum:', '% above {:.1f}'.format(scene.en_hum_max), '% below {:.1f}'.format(scene.en_hum_min))):
                blf.position(font_id, int(startx + hscale*10), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, text)
            for tt, text in enumerate((avval, maxval, minval, percenta, percentb)):
                blf.position(font_id, int(startx +  hscale*(totwidth * 0.6 + 10)), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, '{:.1f}'.format(text))
            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex2i(startx + int(hscale * totwidth * 0.2), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glVertex2i(startx + int(hscale*totwidth * 0.8), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glEnd()
            rowno += tt + 2
        
        if 'Heating (W)' in metrics:
            hdata = [h.split()[resstart:resend] for hi, h in enumerate(zrl[4]) if zrl[3][hi] == 'Heating (W)' and zrl[2][hi] == ezname]
            vals = [float(h) for h in hdata[0]]
            avval, maxval, minval, percenta, percentb, kwh, kwhm2 = sum(vals)/len(vals), max(vals), min(vals), 100 * sum([val >= scene.en_heat_max for val in vals])/len(vals), 100 * sum([val <= scene.en_heat_min for val in vals])/len(vals), 0.001 * sum(vals), 0.001 * sum(vals)/bpy.data.objects['en_'+bpy.context.active_object.name]['floorarea'] 
            blf.position(font_id, int(startx + hscale * 10), int(starty - hscale * rowheight * rowno), 0)
            blf.draw(font_id, 'Heating (W):')
            for tt, text in enumerate(('Average:', 'Maximum:', 'Minimum:', '% above {:.1f}'.format(scene.en_heat_max), '% at min {:.1f}'.format(scene.en_heat_min), 'kWh', 'kWh/m^2')):
                blf.position(font_id, int(startx + hscale*10), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, text)
            for tt, text in enumerate((avval, maxval, minval, percenta, percentb, kwh, kwhm2)):
                blf.position(font_id, int(startx +  hscale*(totwidth * 0.6 + 10)), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, '{:.0f}'.format(text))
            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex2i(startx + int(hscale * totwidth * 0.2), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glVertex2i(startx + int(hscale*totwidth * 0.8), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glEnd()
            rowno += tt + 2
            
        if 'Zone air heating (W)' in metrics:
            hdata = [h.split()[resstart:resend] for hi, h in enumerate(zrl[4]) if zrl[3][hi] == 'Zone air heating (W)' and zrl[2][hi] == ezname]
            vals = [float(h) for h in hdata[0]]
            avval, maxval, minval, percenta, percentb, kwh, kwhm2 = sum(vals)/len(vals), max(vals), min(vals), 100 * sum([val >= scene.en_heat_max for val in vals])/len(vals), 100 * sum([val <= scene.en_heat_min for val in vals])/len(vals), 0.001 * sum(vals), 0.001 * sum(vals)/bpy.data.objects['en_'+bpy.context.active_object.name]['floorarea'] 
            blf.position(font_id, int(startx + hscale * 10), int(starty - hscale * rowheight * rowno), 0)
            blf.draw(font_id, 'Air heating (W):')
            for tt, text in enumerate(('Average:', 'Maximum:', 'Minimum:', '% above {:.0f}'.format(scene.en_heat_max), '% at min {:.0f}'.format(scene.en_heat_min), 'kWh', 'kWh/m^2')):
                blf.position(font_id, int(startx + hscale*10), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, text)
            for tt, text in enumerate((avval, maxval, minval, percenta, percentb, kwh, kwhm2)):
                blf.position(font_id, int(startx +  hscale*(totwidth * 0.6 + 10)), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, '{:.1f}'.format(text))
            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex2i(startx + int(hscale * totwidth * 0.2), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glVertex2i(startx + int(hscale*totwidth * 0.8), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glEnd()
            rowno += tt + 2
            
        if 'Cooling (W)' in metrics:
            cdata = [c.split()[resstart:resend] for ci, c in enumerate(zrl[4]) if zrl[3][ci] == 'Cooling (W)' and zrl[2][ci] == ezname]
            vals = [float(c) for c in cdata[0]]                
            avval, maxval, minval, percenta, percentb, kwh, kwhm2 = sum(vals)/len(vals), max(vals), min(vals), 100 * sum([val >= scene.en_heat_max for val in vals])/len(vals), 100 * sum([val <= scene.en_heat_min for val in vals])/len(vals), 0.001 * sum(vals), 0.001 * sum(vals)/bpy.data.objects['en_'+bpy.context.active_object.name]['floorarea'] 
            blf.position(font_id, int(startx + hscale * 10), int(starty - hscale * rowheight * rowno), 0)
            blf.draw(font_id, 'Cooling (W):')
            for tt, text in enumerate(('Average:', 'Maximum:', 'Minimum:', '% above {:.0f}'.format(scene.en_heat_max), '% at min {:.0f}'.format(scene.en_heat_min), 'kWh', 'kWh/m^2')):
                blf.position(font_id, int(startx + hscale*10), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, text)
            for tt, text in enumerate((avval, maxval, minval, percenta, percentb, kwh, kwhm2)):
                blf.position(font_id, int(startx +  hscale*(totwidth * 0.6 + 10)), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, '{:.1f}'.format(text))
            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex2i(startx + int(hscale * totwidth * 0.2), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glVertex2i(startx + int(hscale*totwidth * 0.8), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glEnd()
            rowno += tt + 2
        
        if 'CO2 (ppm)' in metrics:
            cdata = [c.split()[resstart:resend] for ci, c in enumerate(zrl[4]) if zrl[3][ci] == 'CO2 (ppm)' and zrl[2][ci] == ezname]
            vals = [float(c) for c in cdata[0]] 
            avval, maxval, minval, percenta, percentb = sum(vals)/len(vals), max(vals), min(vals), 100 * sum([val >= scene.en_co2_max for val in vals])/len(vals), 100 * sum([val <= scene.en_co2_min for val in vals])/len(vals) 
            blf.position(font_id, int(startx + hscale * 10), int(starty - hscale * rowheight * rowno), 0)
            blf.draw(font_id, 'CO2 (ppm):')
            for tt, text in enumerate(('Average:', 'Maximum:', 'Minimum:', '% above {:.0f}'.format(scene.en_co2_max), '% at min {:.0f}'.format(scene.en_co2_min))):
                blf.position(font_id, int(startx + hscale*10), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, text)
            for tt, text in enumerate((avval, maxval, minval, percenta, percentb)):
                blf.position(font_id, int(startx +  hscale*(totwidth * 0.6 + 10)), int(starty - hscale * rowheight * (rowno + tt + 1)), 0)
                blf.draw(font_id, '{:.0f}'.format(text))
            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex2i(startx + int(hscale * totwidth * 0.2), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glVertex2i(startx + int(hscale*totwidth * 0.8), int(starty - hscale * rowheight * (rowno + tt + 1.25)))
            bgl.glEnd()
            rowno += tt + 2    
        
        blf.disable(0, 4)        
    return
        
def viwr_legend(self, context, simnode):
    scene = context.scene
    if scene.vi_leg_display != True or scene.vi_display == 0:
        return
    else:
        blf.enable(0, 4)
        blf.shadow(0, 3, 0, 0, 0, 0.5)
        resvals = ['{0:.0f} to {1:.0f}'.format(2*i, 2*(i+1)) for i in range(simnode['nbins'])]
        resvals[-1] = resvals[-1][:-int(len('{:.0f}'.format(simnode['maxres'])))] + u"\u221E"
        height, lenres, font_id = context.region.height, len(resvals[-1]) + 1 , 0
        hscale, newheight, newwidth = height/nh, height-50, 20     
        drawpoly(newwidth, newheight, newwidth + int(hscale*(45 + lenres*8)), int((newheight - hscale*(simnode['nbins']+3.5)*20)), 0.7, 1, 1, 1)
        drawloop(newwidth - 1, newheight, newwidth + int(hscale*(45 + lenres*8)), int((newheight - hscale*(simnode['nbins']+3.5)*20)))
        cm = matplotlib.cm.jet if simnode.wrtype in ('0', '1') else matplotlib.cm.hot

        for i in range(simnode['nbins']):
            bgl.glColor4f(*cm(i * 1/(simnode['nbins']-1), 1))
            bgl.glBegin(bgl.GL_POLYGON)
            bgl.glVertex2i(newwidth, int(newheight - hscale*(simnode['nbins'] * 20 - (i*20) + 20)))
            bgl.glVertex2i(int(newwidth + hscale*40), int(newheight - hscale*(simnode['nbins'] * 20 - (i*20) + 20)))
            bgl.glVertex2i(int(newwidth + hscale*40), int(newheight - hscale*(simnode['nbins'] * 20 - (i*20))))
            bgl.glVertex2i(newwidth, int(newheight - hscale*(simnode['nbins'] * 20 - (i*20))))
            bgl.glEnd()
            blf.size(font_id, 20, int(height/14))
            bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
            blf.position(font_id, int(newwidth + hscale*45), int(newheight - hscale*(simnode['nbins'] * 20 - i*20 + 15)), 0)
            blf.draw(font_id, "  "*(lenres - len(resvals[i]) ) + resvals[i])

        blf.size(font_id, 20, int(hscale*64))
        cu = 'Speed (m/s)'
        drawfont(cu, font_id, 0, newheight, newwidth + 5 * hscale, 17 * hscale)
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        font_id = 0
        bgl.glColor4f(0.0, 0.0, 0.0, 1)
        blf.size(font_id, 20, int(hscale*48))
        datasource = context.active_object if context.active_object and bpy.context.active_object.get('VIType') == 'Wind_Plane' else simnode                
        drawfont("Ave: {:.1f}".format(datasource['avres']), font_id, 0, newheight , newwidth + hscale * 2, int(hscale*(simnode['nbins']*20 + 35)))
        drawfont("Max: {:.1f}".format(datasource['maxres']), font_id, 0, newheight, newwidth + hscale * 2, int(hscale*(simnode['nbins']*20 + 50)))
        drawfont("Min: {:.1f}".format(datasource['minres']), font_id, 0, newheight, newwidth + hscale * 2, int(hscale*(simnode['nbins']*20 + 65)))
        blf.disable(0, 4)

def lipanel():
    pass
            
def li_compliance(self, context, simnode):
    height, scene, swidth, ewidth = context.region.height, context.scene, 120, 920
    if not scene.get('li_compliance') or scene.frame_current not in range(scene['liparams']['fs'], scene['liparams']['fe'] + 1) or scene['viparams']['vidisp'] != 'lcpanel':
        return
    if simnode['coptions']['canalysis'] == '0':
        buildtype = ('School', 'Higher Education', 'Healthcare', 'Residential', 'Retail', 'Office & Other')[int(simnode['coptions']['buildtype'])]
    elif simnode['coptions']['canalysis'] == '1':
        buildtype = 'Residential'
        cfshpfsdict = {'totkit': 0, 'kitdf': 0, 'kitsv': 0, 'totliv': 0, 'livdf': 0, 'livsv': 0}
    if simnode['coptions']['canalysis'] == '3':
        buildtype = ('School/Office/Commercial', 'Healthcare')[int(simnode['coptions']['buildtype'])]
        
    blf.enable(0, blf.KERNING_DEFAULT)
    blf.shadow(0, 3, 0, 0, 0, 0.5)
    drawpoly(swidth, height - 40, ewidth, height - 65, 0.7, 1, 1, 1)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    bgl.glLineWidth(1)
    horpos, widths = (swidth, 337, 653, ewidth), (swidth, 480, 620, 770, ewidth)

    for p in range(3):
        drawloop(horpos[p], height - 40, horpos[p+1], height - 65)

    font_id = 0
    blf.size(font_id, 20, 54)
    drawfont('Standard: '+('BREEAM HEA1', 'CfSH', 'Green Star', 'LEED EQ8.1')[int(simnode['coptions']['Type'])], font_id, 0, height, 130, 58)
    drawfont('Project Name: '+scene.li_projname, font_id, 0, height, 663, 58)
    blf.size(font_id, 20, 40)
    os = [o for o in bpy.data.objects if o.get('lires')]
    
    def space_compliance(os):
        frame, buildspace, pfs, epfs, lencrit = scene.frame_current, '', [], [], 0
        for o in os:
            mat = bpy.data.materials[o['compmat']]
            o['cr4'] = [('fail', 'pass')[int(com)] for com in o['comps'][str(frame)][:][::2]]
            o['cr6'] = [cri[4] for cri in o['crit']]
            if 'fail' in [c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '1'] or bpy.context.scene['liparams']['dfpass'][str(frame)] == 1:
                pf = 'FAIL'
            elif 'pass' not in [c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.75'] and len([c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.75']) > 0:
                if 'pass' not in [c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.5'] and len([c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.5']) > 0:
                    pf = 'FAIL'
                else:
                    pf = 'PASS'
            else:
                pf = 'PASS'
            pfs.append(pf)

            if simnode['coptions']['canalysis'] == '1':
                cfshpfsdict[('totkit', 'totliv')[mat.crspacemenu == '1']] += 1
                if o['cr4'][0] == 'pass':
                    cfshpfsdict[('kitdf', 'livdf')[mat.crspacemenu == '1']] += 1
                if o['cr4'][1] == 'pass':
                    cfshpfsdict[('kitsv', 'livsv')[mat.crspacemenu == '1']] += 1

            if simnode['coptions']['canalysis'] == '0':
                ecrit = o['ecrit']
                o['ecr4'] = [('fail', 'pass')[int(com)] for com in o['ecomps'][str(frame)][:][::2]]
                o['ecr6'] = [ecri[4] for ecri in ecrit]
                if 'fail' in [c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '1'] or bpy.context.scene['liparams']['dfpass'][str(frame)] == 1:
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
            drawpoly(swidth, height - 70, ewidth, height - 70  - (lencrit)*25, 0.7, 1, 1, 1)
            drawloop(swidth, height - 70, ewidth, height - 70  - (lencrit)*25)
            mat = bpy.data.materials[o['compmat']]
            if simnode['coptions']['canalysis'] == '0':
                buildspace = ('', '', (' - Public/Staff', ' - Patient')[int(mat.hspacemenu)], (' - Kitchen', ' - Living/Dining/Study', ' - Communal')[int(mat.brspacemenu)], (' - Sales', ' - Office')[int(mat.respacemenu)], '')[int(simnode['coptions']['buildtype'])]
            elif simnode['coptions']['canalysis'] == '1':
                buildspace = (' - Kitchen', ' - Living/Dining/Study')[int(mat.crspacemenu)]

            titles = ('Zone Metric', 'Target', 'Achieved', 'PASS/FAIL')
            tables = [[] for c in range(lencrit -1)]
            etables = [[] for e in range(len(o['ecrit']))]
            
            for c, cr in enumerate(o['crit']):
                if cr[0] == 'Percent':
                    if cr[2] == 'Skyview':
                        tables[c] = ('Percentage area with Skyview (%)', cr[1], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
                    elif cr[2] == 'DF':  
                        tables[c] = ('Average Daylight Factor (%)', cr[3], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
                    elif cr[2] == 'PDF':    
                        tables[c] = ('Area with point Daylight Factor above {}'.format(cr[3]), cr[1], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
                    elif cr[2] == 'SDA':    
                        tables[c] = ('% area achieving sDA300/50%', cr[1], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
                    elif cr[2] == 'ASE':    
                        tables[c] = ('% area achieving ASE1000,250'.format(cr[3]), cr[1], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
   
                elif cr[0] == 'Ratio':
                    tables[c] = ('Uniformity ratio', cr[3], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
                elif cr[0] == 'Min':
                    tables[c] = ('Minimum {} (%)'.format('Point Daylight Factor'), cr[3], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
                elif cr[0] == 'Average':
                    tables[c] = ('Average {} (%)'.format('Daylight Factor'), cr[3], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())

            if simnode['coptions']['canalysis'] == '0':
                for e, ecr in enumerate(ecrit):
                    if ecr[0] == 'Percent':
                        if ecr[2] == 'skyview':
                            etables[e] = ('Percentage area with Skyview (%)', ecr[1], '{:.2f}'.format(o['ecomps'][str(frame)][:][e*2 + 1]), o['ecr4'][e].upper())
                        elif ecr[2] == 'DF':  
                            etables[e] = ('Average Daylight Factor (%)', ecr[3], '{:.2f}'.format(o['ecomps'][str(frame)][:][e*2 + 1]), o['ecr4'][e].upper())
                        elif ecr[2] == 'PDF':    
                            etables[e] = ('Area with point Daylight Factor above {}'.format(ecr[3]), ecr[1], '{:.2f}'.format(o['ecomps'][str(frame)][:][e*2 + 1]), o['ecr4'][e].upper())
                    elif ecr[0] == 'Min':
                        etables[e] = ('Minimum {} (%)'.format('Point Daylight Factor'), ecr[3], '{:.2f}'.format(o['ecomps'][str(frame)][:][e*2 + 1]), o['ecr4'][e].upper())

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
        if simnode['coptions']['canalysis'] == '0': 
            tpf = 'EXEMPLARY' if tpf == 'PASS' and ('FAIL' not in epfs and 'FAIL*' not in epfs) else tpf
            erows = len(etables) if  tpf == 'EXEMPLARY' else 0
            lencrit = lencrit + erows if bpy.context.active_object in os else 0

        return(tpf, lencrit, buildspace, etables)

    
    build_compliance, lencrit, bs, etables = space_compliance(os)

    if build_compliance == 'EXEMPLARY':
        for t, tab in enumerate(etables):
            if t == 0:
                drawpoly(swidth, height - 70 - (lencrit * 25), ewidth, height - 70 - ((lencrit - len(etables)) * 25), 0.7, 1, 1, 1)
                drawloop(swidth, height - 70 - (lencrit * 25), ewidth, height - 70 - ((lencrit - len(etables)) * 25))
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

    blf.position(font_id, 347, height - 58, 0)
    blf.size(font_id, 20, 54)
    blf.draw(font_id, 'Buildtype: '+buildtype+bs)

    blf.size(font_id, 20, 52)
    blf.position(font_id, 130, height - 87 - lencrit*26, 0)
    if simnode['coptions']['canalysis'] == '0':
        drawpoly(swidth, height - 70 - lencrit*26, 525, height - 95 - lencrit*26, 0.7, 1, 1, 1)
        drawloop(swidth, height - 70 - lencrit*26, 370, height - 95 - lencrit*26)
        drawloop(swidth, height - 70 - lencrit*26, 370, height - 95 - lencrit*26)
        drawloop(370, height - 70 - lencrit*26, 525, height - 95 - lencrit*26)
        blf.draw(font_id, 'Building Compliance:')
        drawfont(build_compliance, 0, lencrit, height, swidth + 150, 87)
        drawfont('Credits achieved:', 0, lencrit, height, 380, 87)
        blf.position(font_id, 500, height - 87 - lencrit*26, 0)
        if build_compliance == 'PASS':
           blf.draw(font_id,  ('1', '2', '2', '1', '1', '1')[int(simnode['coptions']['buildtype'])])
        elif build_compliance == 'EXEMPLARY':
            blf.draw(font_id,  ('2', '3', '3', '2', '2', '2')[int(simnode['coptions']['buildtype'])])
        else:
            blf.draw(font_id, '0')

    elif simnode['coptions']['canalysis'] == '1':
        drawpoly(swidth, height - 70 - lencrit*26, 320, height - 95 - lencrit*26, 0.7, 1, 1, 1)
        drawloop(swidth, height - 70 - lencrit*26, 320, height - 95 - lencrit*26)
        drawfont('Credits achieved:', 0, lencrit, height, swidth + 10, 87)
        cfshcred = 0
        if cfshpfsdict['kitdf'] == cfshpfsdict['totkit'] and cfshpfsdict['totkit'] != 0:
            cfshcred += 1
        if cfshpfsdict['livdf'] == cfshpfsdict['totliv'] and cfshpfsdict['totliv'] != 0:
            cfshcred += 1
        if (cfshpfsdict['kitsv'] == cfshpfsdict['totkit'] and  cfshpfsdict['totkit'] != 0) or (cfshpfsdict['livsv'] == cfshpfsdict['totliv'] and cfshpfsdict['totliv'] != 0):
            cfshcred += 1
        blf.position(font_id, 270, height - 87 - lencrit*26, 0)
        blf.draw(font_id, '{} of {}'.format(cfshcred, '3' if 0 not in (cfshpfsdict['totkit'], cfshpfsdict['totliv']) else '2'))

    elif simnode['coptions']['canalysis'] == '3':
        drawpoly(swidth, height - 70 - lencrit*26, 320, height - 95 - lencrit*26, 0.7, 1, 1, 1)
        drawloop(swidth, height - 70 - lencrit*26, 320, height - 95 - lencrit*26)
        drawfont('Credits achieved:', 0, lencrit, height, swidth + 10, 87)
        totarea = sum([o['oarea'] for o in os])
        totsdaarea = sum([o['sdapassarea'] for o in os])
        totasearea = sum([o['asepassarea'] for o in os])
        leedcred = 0
        if simnode['coptions']['buildtype'] == '0':
            if totsdaarea/totarea > 0.55:
                leedcred += 2
            if totsdaarea/totarea > 0.75:
                leedcred += 1
        if totasearea/totarea > 0.1:
            leedcred = 0
        blf.position(font_id, 270, height - 87 - lencrit*26, 0)
        blf.draw(font_id, '{} of {}'.format(leedcred, ('2', '3')[simnode['coptions']['buildtype'] == '0']))
        
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
    bgl.glLineWidth(1)
    sw = 8

    aolen, ailen, jnlen = len(scene.li_assorg), len(scene.li_assind), len(scene.li_jobno)
    drawpoly(100, 50, 500 + aolen*sw + ailen*sw + jnlen*sw, 25, 0.7, 1, 1, 1)
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
    blf.disable(0, blf.KERNING_DEFAULT)

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

