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
 # -*- coding: utf-8 -*-
#from __future__ import unicode_literals
import bpy, blf, colorsys, bgl, mathutils, bmesh, datetime, os, inspect
from bpy_extras import view3d_utils
from math import pi, sin, cos, atan2, log10, ceil
from numpy import array, where, arange
from numpy import sum as nsum
from numpy import min as nmin
from numpy import max as nmax
try:
    import matplotlib.pyplot as plt
    import matplotlib.cm as mcm    
    mp = 1
except:
    mp = 0

from . import livi_export
from .vi_func import cmap, skframe, selobj, retvpvloc, viewdesc, drawloop, drawpoly, draw_index, drawfont, blf_props, blf_unprops
from .vi_func import retdp, objmode, drawcircle, drawtri, setscenelivivals, draw_time, retcols, draw_index_distance
from .envi_func import retenvires, retenresdict, recalculate_text

nh = 768
enunitdict = {'Heating (W)': 'Watts (W)', 'Cooling (W)': 'Watts (W)', 'CO2 (ppm)': 'PPM', 'Solar gain (W)': 'Watts (W)', 'Temperature (degC)': u'Temperature (\u00B0C)', 'PMV': 'PMV', 'PPD (%)': '%', 'Air heating (W)': 'W', 
              'Air cooling (W)': 'W', 'HR heating (W)': 'W', 'Heat balance (W)': 'W', 'Occupancy': 'Persons', 'Humidity (%)': '(%)', 'Infiltration (m3/s)': 'm3/s', 'Infiltration (ACH)': 'ACH'}
entitledict = {'Heating (W)': 'Heating Consumption', 'Cooling (W)': 'Cooling Consumption', 'CO2 (ppm)': r'CO$_2$ Concentration', 'Solar gain (W)': 'Solar Gain', 'Temperature (degC)': 'Temperature', 'PMV': 'Predicted Mean Vote', 
               'PPD (%)': 'Predicted Percentage of Dissatisfied', 'Air heating (W)': 'Air Heating', 'Air cooling (W)': 'Air Cooling', 'HR heating (W)': 'Heat recovery', 'Heat balance (W)': 'Heat Balance', 'Occupancy': 'Occupancy',
                'Humidity (%)': 'Humidity', 'Infiltration (m3/s)': 'Infiltration', 'Infiltration (ACH)': 'Infiltration'}

#envaldict = {'Heating (W)': 'Watts (W)', 'Cooling (W)': 'Watts (W)', 'CO2 (ppm)': 'PPM', 'Solar gain (W)': 'Watts (W)', 'Temperature (degC)': (scene.en_temp_min, scene.en_temp_max)}

def envals(unit, scene, data):
    envaldict = {'Heating (W)': (scene.en_heat_min, scene.en_heat_max), 'Cooling (W)': (scene.en_cool_min, scene.en_cool_max), 'CO2 (ppm)': (scene.en_co2_min, scene.en_co2_max), 
    'Solar gain (W)': (scene.en_shg_min, scene.en_shg_max), 'Temperature (degC)': (scene.en_temp_min, scene.en_temp_max), 'PMV': (scene.en_pmv_min, scene.en_pmv_max), 'PPD (%)': (scene.en_ppd_min, scene.en_ppd_max),
    'Air heating (W)': (scene.en_aheat_min, scene.en_aheat_max), 'Air cooling (W)': (scene.en_acool_min, scene.en_acool_max), 'HR heating (W)': (scene.en_hrheat_min, scene.en_hrheat_max), 
    'Heat balance (W)': (scene.en_heatb_min, scene.en_heatb_max),  'Occupancy': (scene.en_occ_min, scene.en_occ_max),'Humidity (%)': (scene.en_hum_min, scene.en_hum_max),'Infiltration (ACH)': (scene.en_iach_min, scene.en_iach_max),
    'Infiltration (m3/s)': (scene.en_im3s_min, scene.en_im3s_max)}
    if unit in envaldict:
        return envaldict[unit]
    else:
        return (nmin(data), nmax(data))

def ss_display():
    pass

def li_display(disp_op, simnode):
    scene, obreslist, obcalclist = bpy.context.scene, [], []
    setscenelivivals(scene)
    try:
        scene.display_settings.display_device = 'None'
    except:
        pass
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
        bm.normal_update()
                 
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
            disp_op.report({'ERROR'},"No display object. If in local view switch to global view and/or re-export the geometry")
            return 'CANCELLED'
            
        ores = bpy.context.active_object
        ores.name, ores.show_wire, ores.draw_type = o.name+"res", 1, 'SOLID'
        
        while ores.material_slots:
            bpy.ops.object.material_slot_remove()
        
        while ores.data.shape_keys:
            bpy.context.object.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove(all=True)
            
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
            bm.faces.layers.int.new('extrude')
            extrude = bm.faces.layers.int['extrude']
            for face in bmesh.ops.extrude_discrete_faces(bm, faces = bm.faces)['faces']:
                face.select = True
                face[extrude] = 1
                
        bm.transform(o.matrix_world.inverted())
        bm.to_mesh(ores.data)
        bm.free()
        bpy.ops.object.shade_flat()
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

    if bpy.data.objects.get('SPathMesh'):
        spob = bpy.data.objects['SPathMesh'] 
        ob_mat = spob.matrix_world
        mid_x, mid_y, width, height = viewdesc(context)
        vl = retvpvloc(context)
        blf_props(scene, width, height)
        
        if scene.hourdisp:
            pvecs = [ob_mat * mathutils.Vector(p[:]) for p in spob['numpos'].values()]
            pvals = [int(p.split('-')[1]) for p in spob['numpos'].keys()]
            p2ds = [view3d_utils.location_3d_to_region_2d(context.region, context.region_data, p) for p in pvecs]
            vispoints = [pi for pi, p in enumerate(pvals) if p2ds[pi] and 0 < p2ds[pi][0] < width and 0 < p2ds[pi][1] < height and scene.ray_cast(vl, pvecs[pi] - vl, (pvecs[pi] - vl).length)[4] == spob]
            
            if vispoints:
                hs = [pvals[pi] for pi in vispoints]
                posis = [p2ds[pi] for pi in vispoints]                
                draw_index(posis, hs, scene.vi_display_rp_fs, scene.vi_display_rp_fc, scene.vi_display_rp_fsh)
                
        if [ob.get('VIType') == 'Sun' for ob in bpy.data.objects]:
            sobs = [ob for ob in bpy.data.objects if ob.get('VIType') == 'Sun']
            if sobs and scene.timedisp:
                sunloc = ob_mat * sobs[0].location
                solpos = view3d_utils.location_3d_to_region_2d(context.region, context.region_data, sunloc)
                try:
                    if 0 < solpos[0] < width and 0 < solpos[1] < height and not scene.ray_cast(sobs[0].location + 0.05 * (vl - sunloc), vl- sunloc)[0]:
                        soltime = datetime.datetime.fromordinal(scene.solday)
                        soltime += datetime.timedelta(hours = scene.solhour)
                        sre = sobs[0].rotation_euler
                        blf_props(scene, width, height)
                        draw_time(solpos, soltime.strftime('  %d %b %X') + ' alt: {:.1f} azi: {:.1f}'.format(90 - sre[0]*180/pi, (180, -180)[sre[2] < -pi] - sre[2]*180/pi), 
                                   scene.vi_display_rp_fs, scene.vi_display_rp_fc, scene.vi_display_rp_fsh)
                        
                except:
                    pass
        blf.disable(0, 4)
    else:
        return

class linumdisplay():
    def __init__(self, disp_op, context, simnode):
        self.scene = context.scene  
        self.fn = self.scene.frame_current - self.scene['liparams']['fs']
        self.level = self.scene.vi_disp_3dlevel
        self.disp_op = disp_op
        self.scene.vi_display_rp = 0
        self.fs = self.scene.vi_display_rp_fs
        self.fontmult = 1
        self.obreslist = [ob for ob in self.scene.objects if ob.type == 'MESH'  and 'lightarray' not in ob.name and ob.hide == False and ob.layers[self.scene.active_layer] == True and ob.get('lires')]
        if self.scene.vi_display_sel_only == False:
            self.obd = self.obreslist
        else:
            self.obd = [context.active_object] if context.active_object in self.obreslist else []
        self.omws = [o.matrix_world for o in self.obd] 
        mid_x, mid_y, self.width, self.height = viewdesc(context)
        self.view_location = retvpvloc(context)
        objmode()
        self.update(context)
        
    def draw(self, context):
        self.u = 0
        self.scene = context.scene
        self.fontmult = 2 if context.space_data.region_3d.is_perspective else 500
        
        if not self.scene.get('viparams') or self.scene['viparams']['vidisp'] not in ('lipanel', 'sspanel', 'lcpanel'):
            self.scene.vi_display = 0
            return
        if self.scene.frame_current not in range(self.scene['liparams']['fs'], self.scene['liparams']['fe'] + 1):
            self.disp_op.report({'INFO'},"Outside result frame range")
            return
        if self.scene.vi_display_rp != True \
             or (bpy.context.active_object not in self.obreslist and self.scene.vi_display_sel_only == True)  \
             or (bpy.context.active_object and bpy.context.active_object.mode == 'EDIT'):
             return
        
        if (self.width, self.height) != viewdesc(context)[2:]:
            mid_x, mid_y, self.width, self.height = viewdesc(context)
            self.u = 1
            
        if self.view_location != retvpvloc(context):
            self.view_location = retvpvloc(context)
            self.u = 1
            
        if self.scene.vi_display_sel_only == False:
            obd = self.obreslist
        else:
            obd = [context.active_object] if context.active_object in self.obreslist else []
        
        if self.obd != obd:
            self.obd = obd
            self.u = 1
        
        if self.fn != self.scene.frame_current - self.scene['liparams']['fs']:
            self.fn = self.scene.frame_current - self.scene['liparams']['fs']
            self.u = 1
            
        if self.level != self.scene.vi_disp_3dlevel:
            self.level = self.scene.vi_disp_3dlevel
            self.u = 1
        
        blf_props(self.scene, self.width, self.height)
        if self.u:            
            self.update(context)
        else:              
            draw_index_distance(self.allpcs, self.allres, self.fontmult * self.scene.vi_display_rp_fs, self.scene.vi_display_rp_fc, self.scene.vi_display_rp_fsh, self.alldepths)    
        
        if self.scene.vi_display_rp_fs != self.fs:
            self.fs = self.scene.vi_display_rp_fs
            bpy.context.user_preferences.system.window_draw_method = bpy.context.user_preferences.system.window_draw_method
           
    def update(self, context):
        self.allpcs, self.alldepths, self.allres = [], [], []
        try:
            for ob in self.obd:
                if ob.data.get('shape_keys') and str(self.fn) in [sk.name for sk in ob.data.shape_keys.key_blocks] and ob.active_shape_key.name != str(self.fn):
                    ob.active_shape_key_index = [sk.name for sk in ob.data.shape_keys.key_blocks].index(str(self.fn))
                try:
                    omw = ob.matrix_world
                    bm = bmesh.new()
                    tempmesh = ob.to_mesh(scene = context.scene, apply_modifiers = True, settings = 'PREVIEW')
                    bm.from_mesh(tempmesh)
                    bpy.data.meshes.remove(tempmesh)
                    bm.transform(omw)
                    bm.normal_update()
                    geom = bm.faces if bm.faces.layers.float.get('res{}'.format(self.scene.frame_current)) else bm.verts
                    geom.ensure_lookup_table()
                    livires = geom.layers.float['res{}'.format(self.scene.frame_current)]
            
                    if bm.faces.layers.float.get('res{}'.format(self.scene.frame_current)):
                        if self.scene.vi_disp_3d:
                            extrude = geom.layers.int['extrude']                                
                            faces = [f for f in geom if f.select and f[extrude]]
                        else:
                            faces = [f for f in geom if f.select]

                        distances = [(self.view_location - f.calc_center_median_weighted() + self.scene.vi_display_rp_off * f.normal.normalized()).length for f in faces]
           
                        if self.scene.vi_display_vis_only:
                            fcos = [f.calc_center_median_weighted() + self.scene.vi_display_rp_off * f.normal.normalized() for f in faces]
                            direcs = [self.view_location - f for f in fcos]
                            (faces, distances) = map(list, zip(*[[f, distances[i]] for i, f in enumerate(faces) if not self.scene.ray_cast(fcos[i], direcs[i], distance=distances[i])[0]]))
        
                        face2d = [view3d_utils.location_3d_to_region_2d(context.region, context.region_data, f.calc_center_median_weighted()) for f in faces]
                        (faces, self.pcs, self.depths) = map(list, zip(*[[f, face2d[fi], distances[fi]] for fi, f in enumerate(faces) if face2d[fi] and 0 < face2d[fi][0] < self.width and 0 < face2d[fi][1] < self.height]))          
                        self.res = [f[livires] for f in faces]
                    
                    elif bm.verts.layers.float.get('res{}'.format(self.scene.frame_current)):                        
                        verts = [v for v in geom if not v.hide and v.select and (context.space_data.region_3d.view_location - self.view_location).dot(v.co + self.scene.vi_display_rp_off * v.normal.normalized() - self.view_location)/((context.space_data.region_3d.view_location-self.view_location).length * (v.co + self.scene.vi_display_rp_off * v.normal.normalized() - self.view_location).length) > 0]
                        distances = [(self.view_location - v.co + self.scene.vi_display_rp_off * v.normal.normalized()).length for v in verts]
                        
                        if self.scene.vi_display_vis_only:
                            vcos = [v.co + self.scene.vi_display_rp_off * v.normal.normalized() for v in verts]
                            direcs = [self.view_location - v for v in vcos]
                            (verts, distances) = map(list, zip(*[[v, distances[i]] for i, v in enumerate(verts) if not self.scene.ray_cast(vcos[i], direcs[i], distance=distances[i])[0]]))
                            
                        vert2d = [view3d_utils.location_3d_to_region_2d(context.region, context.region_data, v.co) for v in verts]
                        (verts, self.pcs, self.depths) = map(list, zip(*[[v, vert2d[vi], distances[vi]] for vi, v in enumerate(verts) if vert2d[vi] and 0 < vert2d[vi][0] < self.width and 0 < vert2d[vi][1] < self.height]))
                        self.res = [v[livires] for v in verts]
                    
                    bm.free()
                
                except Exception as e:
                    self.pcs, self.depths, self.res = [], [], []
                    
                self.allpcs += self.pcs
                self.alldepths += self.depths
                self.allres += self.res
            self.allpcs  = array(self.allpcs)
            self.alldepths = array(self.alldepths)
            self.allres = array(self.allres)            
            draw_index_distance(self.allpcs, self.allres, self.fontmult * self.scene.vi_display_rp_fs, self.scene.vi_display_rp_fc, self.scene.vi_display_rp_fsh, self.alldepths)    

        except Exception as e:
            print('I am excepting', e)

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
        
class Base_Display():
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        self.pos = pos
        self.spos = [int(self.pos[0] - 0.025 * width), int(self.pos[1] - 0.0125 * height)]
        self.epos = [int(self.pos[0] + 0.025 * width), int(self.pos[1] + 0.0125 * height)]        
        self.lspos = [self.spos[0], self.spos[1] - ydiff]
        self.lepos = [self.spos[0] + xdiff, self.spos[1]]
        self.lpos = (self.pos[0] + 0.2 * width, self.pos[1] - 0.2 * height)
        self.resize = 0
        self.press = 0
        self.move = 0
        self.expand = 0
        if iname not in bpy.data.images:
            bpy.data.images.load(os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))), 'images', iname))
        self.image = iname
        self.hl = [1, 1, 1, 1]
        self.cao = None
        self.xdiff, self.ydiff = xdiff, ydiff
        
    def draw(self, context, width, height):
        self.width, self.height = context.region.width, context.region.height
        if self.pos[1] > height:
            self.pos[1] = height
        self.spos = (int(self.pos[0] - 25), int(self.pos[1] - 15))
        self.epos = (int(self.pos[0] + 25), int(self.pos[1] + 15))
        if self.expand == 0:
            self.drawclosed()
        if self.expand == 1:
            self.drawopen(context)
    
    def drawclosed(self):
        draw_icon(self)       

class wr_legend(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        
    def update(self, context):
        simnode = bpy.data.node_groups[context.scene['viparams']['restree']].nodes[context.scene['viparams']['resnode']]        
        self.cao = context.active_object
        if self.cao and self.cao.get('VIType') and self.cao['VIType'] == 'Wind_Plane':
            scene = context.scene
            levels = self.cao['nbins']
            maxres = self.cao['maxres']
        else:
            levels = simnode['nbins']
            maxres = simnode['maxres']
        self.cols = retcols(context.scene, levels)
        
        if not context.scene.get('liparams'):
            scene.vi_display = 0
            return

        self.resvals = ['{0:.0f} - {1:.0f}'.format(2*i, 2*(i+1)) for i in range(simnode['nbins'])]
        self.resvals[-1] = self.resvals[-1][:-int(len('{:.0f}'.format(maxres)))] + u"\u221E"  
        
    def drawopen(self, context):
        draw_legend(self, context.scene, 'Speed (m/s)')
        
class wr_scatter(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        self.unit = '0'
        
    def update(self, context):
        self.cao = context.active_object
        if self.cao and self.cao.get('ws'):
            self.unit = context.scene.wind_type 
#            zdata = array(self.cao['ws']) if self.type_select else array(self.cao['wd'])  
            zdata = array(self.cao['ws']) if context.scene.wind_type == '0' else array(self.cao['wd'])
#            (title, cbtitle) = ('Wind Speed', 'Speed (m/s)') if self.type_select else ('Wind Direction', u'Direction (\u00B0)')
            (title, cbtitle) = ('Wind Speed', 'Speed (m/s)') if context.scene.wind_type == '0' else ('Wind Direction', u'Direction (\u00B0)')
            self.plt = plt
            draw_dhscatter(self, context.scene, self.cao['days'], self.cao['hours'], zdata, title, 'Days', 'Hours', cbtitle, nmin(zdata), nmax(zdata))  
            save_plot(self, context.scene, 'scatter.png')
        
    def drawopen(self, context):
#        draw_image(self, self.ydiff * 0.1)
        draw_image(self, 0)
##        butcents = [[int(self.lspos[0] + 0.07 * self.xdiff), int(self.lepos[1] - self.ydiff * 0.05)], [int(self.lspos[0] + 0.93 * self.xdiff), int(self.lepos[1] - self.ydiff * 0.05)]]
#        butcent = [int(self.lspos[0] + 30), int(self.lepos[1] - self.ydiff * 0.05)]
#        if self.type_select:
#            drawpoly(int(butcent[0] - 10), int(self.lepos[1] - self.ydiff * 0.03), int(butcent[0] + 10), int(self.lepos[1] - self.ydiff * 0.07), 0.5, 0.5, 0.5, 1)
#
#        drawloop(int(butcent[0] - 10), int(self.lepos[1] - self.ydiff * 0.03), int(butcent[0] + 10), int(self.lepos[1] - self.ydiff * 0.07))
##        drawloop(int(butcents[1][0] - 10), int(self.lepos[1] - self.ydiff * 0.03), int(self.lepos[0] - 20), int(self.lepos[1] - self.ydiff * 0.07))
#        self.buttons = {'Speed/Direction': butcent}
#        blf.size(0, 44, int(self.ydiff * 0.075))
#        blf.position(0, butcent[0]  + 10 + self.xdiff * 0.01, butcent[1] - 0.3 * blf.dimensions(0, 'Speed/Direction')[1], 0)
#        blf.draw(0, 'Speed/Direction')
        
    def show_plot(self):
        show_plot(self)
        
class leed_scatter(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        self.unitdict = {'ASE (hrs)': 'asearea', 'sDA (%)': 'sdaarea'}
        self.unit = 'sDA (%)'

    def update(self, context):
        self.cao = context.active_object
        self.unit = context.scene['liparams']['unit']
        self.frame = context.scene.frame_current
        if self.cao and self.cao.get('livires') and self.cao['livires'].get('{}{}'.format(self.unitdict[context.scene['liparams']['unit']], context.scene.frame_current)):
            zdata = array(self.cao['livires']['{}{}'.format(self.unitdict[context.scene['liparams']['unit']], context.scene.frame_current)])
            (title, cbtitle) = ('% area with Illuminance above 1000 lux', 'Area (%)') if context.scene['liparams']['unit'] == 'ASE (hrs)' else ('% area with Illuminance above 300 lux', 'Area (%)')
            self.plt = plt
            draw_dhscatter(self, context.scene, self.cao['livires']['cbdm_days'], self.cao['livires']['cbdm_hours'], zdata, title, 'Days', 'Hours', cbtitle, 0, 100)  
            save_plot(self, context.scene, 'scatter.png')
        
    def drawopen(self, context):
        draw_image(self, 0)
        
    def show_plot(self):
        show_plot(self)
        
class cbdm_scatter(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        self.unitdict = {'ASE (hrs)': 'asearea', 'sDA (%)': 'sdaarea', 'DA (%)': 'daarea', 'UDI-f (%)': 'udilarea', 'UDI-s (%)': 'udisarea', 'UDI-a (%)': 'udiaarea', 'UDI-e (%)': 'udiharea', 'Max lux': 'dhillumax', 'Ave lux': 'dhilluave', 'Min lux': 'dhillumin', 'kWh': 'kW', 'kWh/m2': 'kW/m2'}
        self.titledict = {'ASE (hrs)': 'ASE Area', 'sDA (%)': 'sDa Area', 'DA (%)': 'DA Area', 'UDI-f (%)': 'UDI-f Area', 'UDI-s (%)': 'UDI-s Area', 'UDI-a (%)': 'UDI-a Area', 'UDI-e (%)': 'UDI-e Area', 'Max lux': 'Maximum Object Illuminance', 'Ave lux': 'Average Object Illuminance', 
        'Min lux': 'Minimum Object Illuminance', 'kWh': 'Object Irradiance', 'kWh/m2': 'Object Irradiance Density'}
        self.cbtitledict = {'ASE (hrs)': 'Area (%)', 'sDA (%)': 'Area (%)', 'DA (%)': 'Area (%)', 'UDI-f (%)': 'Area (%)', 'UDI-s (%)': 'Area (%)', 'UDI-a (%)': 'Area (%)', 'UDI-e (%)': 'Area (%)', 'Max lux': 'Lux', 'Ave lux': 'Lux', 
        'Min lux': 'Lux', 'kWh': 'kW', 'kWh/m2': u'kW/m\u00b2'}

    def update(self, context):
        self.cao = context.active_object
        self.unit = context.scene['liparams']['unit']
        self.frame = context.scene.frame_current

        if self.cao and self.cao.get('livires') and self.cao['livires'].get('{}{}'.format(self.unitdict[context.scene['liparams']['unit']], context.scene.frame_current)):
            zdata = array(self.cao['livires']['{}{}'.format(self.unitdict[context.scene['liparams']['unit']], context.scene.frame_current)])
            (self.vmax, self.vmin) = (context.scene.vi_scatter_max, context.scene.vi_scatter_min) if context.scene['liparams']['unit'] in ('Max lux', 'Min lux', 'Ave lux', 'kWh', 'kWh/m2') else (100, 0)
            (title, cbtitle) = (self.titledict[context.scene['liparams']['unit']], self.cbtitledict[context.scene['liparams']['unit']])
            self.plt = plt
            draw_dhscatter(self, context.scene, self.cao['livires']['cbdm_days'], self.cao['livires']['cbdm_hours'], zdata, title, 'Days', 'Hours', cbtitle, self.vmin, self.vmax)  
            save_plot(self, context.scene, 'scatter.png')
        
    def drawopen(self, context):
        draw_image(self, 0)
        
    def show_plot(self):
        show_plot(self)
        
class en_scatter(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        
    def update(self, context):
        self.cao = context.active_object
        scene = context.scene
        self.resstring = retenvires(scene)
        self.unit = scene.en_disp_unit if scene.en_disp_unit else 0
        self.col = scene.vi_leg_col
        self.minmax = [0, 100]
        self.gimage = 'scatter.png'

        try:
            if self.unit:
                zdata, hours, days = array(self.cao[self.resstring][self.unit]).reshape(len(self.cao['days']), 24).T, self.cao['hours'], self.cao['days']        
                title = self.cao.name
                self.minmax = envals(self.unit, scene, zdata)    
                cbtitle = enunitdict[self.unit]
                self.plt = plt
                self.plt.rcParams['font.family']='Noto Sans'
                draw_dhscatter(self, scene, days, hours, zdata, '{} {}'.format(title, entitledict[self.unit]), 'Days', 'Hours', cbtitle, self.minmax[0], self.minmax[1])  
                save_plot(self, scene, 'scatter.png')

        except Exception as e:  
            print('e', e)
        
    def drawopen(self, context):
        draw_image(self, 0)
        
    def show_plot(self):
        show_plot(self)
        
class en_barchart(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        
    def quickupdate(self, scene):
        pass
#        self.rangedict = {'Max temp (C)': (scene.en_maxtemp_min, scene.en_maxtemp_max), 'Ave temp (C)': (scene.en_avetemp_min, scene.en_avetemp_max),
#                            'Min temp (C)': (scene.en_mintemp_min, scene.en_mintemp_max), 'Max heating (W)': (scene.en_maxheat_min, scene.en_maxheat_max),
#                            'Ave heating (W)': (scene.en_aveheat_min, scene.en_aveheat_max), 'Min heating (W)': (scene.en_minheat_min, scene.en_minheat_max),
#                            'Total heating (kWh/m2)': (scene.en_tothkwhm2_min, scene.en_tothkwhm2_max), 'Total heating (kWh)': (scene.en_tothkwh_min, scene.en_tothkwh_max),
#                            'Max cooling (W)': (scene.en_maxcool_min, scene.en_maxcool_max), 'Min cooling (W)': (scene.en_mincool_min, scene.en_mincool_max),
#                            'Ave cooling (W)': (scene.en_avecool_min, scene.en_avecool_max), 'Total cooling (kWh/m2)': (scene.en_totckwhm2_min, scene.en_totckwhm2_max),
#                            'Total cooling (kWh)': (scene.en_totckwh_min, scene.en_totckwh_max), 'Max SHG (W)': (scene.en_maxshg_min, scene.en_maxshg_max),
#                            'Ave SHG (W)': (scene.en_aveshg_min, scene.en_aveshg_max), 'Min SHG (W)': (scene.en_minshg_min, scene.en_minshg_max),
#                            'Total SHG (kWh)':  (scene.en_totshgkwh_min, scene.en_totshgkwh_max), 'Total SHG (kWh/m2)':  (scene.en_totshgkwhm2_min, scene.en_totshgkwhm2_max)}

    
    def update(self, context):
        scene = context.scene
        resnode = bpy.data.node_groups[scene['viparams']['resnode'].split('@')[1]].nodes[scene['viparams']['resnode'].split('@')[0]]
        self.cao = context.active_object
        self.unit = scene.en_disp_punit if scene.en_disp_punit else '' #resnode[self.resstring].keys()[0] 
        self.resstring = retenvires(scene)
        self.col = scene.vi_leg_col
        self.plt = plt
        self.minmax = (scene.bar_min, scene.bar_max)
        if self.cao and self.cao.get(self.resstring) and self.cao[self.resstring].get(self.unit):
            x = arange(resnode['AStart'], resnode['AEnd'] + 1)
            y = array(self.cao[self.resstring][self.unit])
#            self.minmax = self.rangedict[self.unit] if self.unit in self.rangedict else (0, 30)
            
            title = self.cao.name
            draw_barchart(self, scene, x, y, title, 'Frame', self.unit, self.minmax[0], self.minmax[1])  
            save_plot(self, scene, 'barchart.png')
        else:
            self.gimage = 'stats.png'
        
    def drawopen(self, context):
        draw_image(self, 0)
        
    def show_plot(self):
        show_plot(self)
     
class ss_scatter(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        self.type_select = 1
        
    def update(self, context):
        self.cao = context.active_object
        self.frame = context.scene.frame_current
        self.col = context.scene.vi_leg_col        
        self.gimage = 'stats.png'

        if self.cao and self.cao.get('dhres{}'.format(context.scene.frame_current)): 
            self.plt = plt
            draw_dhscatter(self, context.scene, self.cao['days'], self.cao['hours'], self.cao['dhres{}'.format(self.frame)], '% Area Sunlit', 'Days', 'Hours', 'Area (%)', 0, 100)  
            save_plot(self, context.scene, 'scatter.png')
        
    def drawopen(self, context):
        draw_image(self, 0)
        
    def show_plot(self):
        show_plot(self)

class wr_table(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        self.fontdpi = int(0.15 * ydiff)
        
    def update(self, context):
        self.cao = context.active_object
        if self.cao and self.cao.get('ws'):
            self.rcarray = array(self.cao['table'])  
        
    def drawopen(self, context):
        draw_table(self)
        
class basic_table(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        self.fontdpi = int(0.15 * ydiff)
        self.unitdict = {'Lux': 'illu', 'DF (%)': 'df', u'W/m\u00b2 (v)': 'vi', u'W/m\u00b2 (f)': 'fi', 'Sky View': 'sv', 'sDA (%)': 'sda', 'ASE (hrs)': 'ase',
                         'Mlxh': 'mlxh', u'kWh/m\u00b2 (f)': 'fi', u'kWh/m\u00b2 (v)': 'vi', 'DA (%)': 'da', 'UDI-f (%)': 'udil', 'UDI-s (%)': 'udis', 
                         'UDI-a (%)': 'udia', 'UDI-e (%)': 'udie', 'Max lux': 'illu', 'Ave lux': 'illu', 'Min lux': 'illu', 'kWh': 'kwh', 'kWh/m2': 'kwhm2'}
        
    def update(self, context):
        self.unit = context.scene['liparams']['unit']
        self.cao = context.active_object

        if self.cao and self.cao.get('table{}{}'.format(self.unitdict[context.scene['liparams']['unit']], context.scene.frame_current)):
            self.rcarray = array(self.cao['table{}{}'.format(self.unitdict[context.scene['liparams']['unit']], context.scene.frame_current)])
        else:
            self.rcarray = array([['Invalid object']])
    def drawopen(self, context):
        draw_table(self)
        
class comp_table(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        self.fontdpi = int(0.15 * ydiff)
        self.unitdict = {'DF (%)': 'df', 'Sky View': 'sv'}
        
    def update(self, context):
        self.unit = context.scene['liparams']['unit']
        self.cao = context.active_object
        resnode = bpy.data.node_groups[context.scene['viparams']['restree']].nodes[context.scene['viparams']['resnode']]
        if self.cao and self.cao.get('tablecomp{}'.format(context.scene.frame_current)):
            self.rcarray = array((self.cao['tablecomp{}'.format(context.scene.frame_current)]))  
        else:
            self.rcarray = array((resnode['tablecomp{}'.format(context.scene.frame_current)]))
        
    def drawopen(self, context):
        draw_table(self)

class en_table(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        self.fontdpi = int(0.15 * ydiff)
        self.unitdict = {'Temperature (degC)': 'Temperature (C)', 'Sky View': 'sv'}
        
    def update(self, context):
        scene = context.scene
        self.cao = context.active_object
        rcarray = [['', 'Minimum', 'Average', 'Maximum']] if scene.en_disp_type == '1' else [['', 'Minimum', 'Average', 'Maximum', '% time under lower threshold', '% time over upper threshold']]
        resstring = retenvires(scene)

        if self.cao and self.cao.get(resstring): 
            resdict = self.cao[resstring]
            for res in sorted(resdict.keys()):
                resarray = array(resdict[res])
                self.unit = res
                (minv, maxv) = envals(self.unit, scene, resarray)
                if scene.en_disp_type == '1':
                    rcarray.append([res, '{:.1f}'.format(nmin(resarray)), '{:.1f}'.format(nsum(resarray)/resarray.size), '{:.1f}'.format(nmax(resarray))])
                else:
                    rcarray.append([res, '{:.1f}'.format(nmin(resarray)), '{:.1f}'.format(nsum(resarray)/resarray.size), '{:.1f}'.format(nmax(resarray)), '{:.1f}'.format(100 * nsum(resarray < minv)/resarray.size), '{:.1f}'.format(100 * nsum(resarray > maxv)/resarray.size)])
                
            if 'Heating (W)' in resdict or 'Cooling (W)' in resdict or 'Air heating (W)' in resdict or 'Air cooling (W)' in resdict or 'HR heating (W)' in resdict:
                rcarray.append(['', '', '', '', '', ''])
                rcarray.append(['', 'kWh', 'kWh/m2', '', '', ''])
                if 'Heating (W)' in resdict:
                    hkwh = nsum(array(resdict['Heating (W)'])) * 0.001
                    rcarray.append(['Total heating', '{:.1f}'.format(hkwh), '{:.1f}'.format(hkwh/self.cao['floorarea']), '', '', ''])

                if 'Cooling (W)' in resdict:
                    ckwh = nsum(array(resdict['Cooling (W)'])) * 0.001
                    rcarray.append(['Total cooling', '{:.1f}'.format(ckwh), '{:.1f}'.format(ckwh/self.cao['floorarea']), '', '', ''])
                
                if 'Heating (W)' in resdict and 'Cooling (W)' in resdict:
                    rcarray.append(['Total conditioning', '{:.1f}'.format(hkwh + ckwh), '{:.1f}'.format((hkwh + ckwh)/self.cao['floorarea']), '', '', ''])

                if 'Air heating (W)' in resdict:
                    ahkwh = nsum(array(resdict['Air heating (W)'])) * 0.001
                    rcarray.append(['Total air heating', '{:.1f}'.format(ahkwh), '{:.1f}'.format(ahkwh/self.cao['floorarea']), '', '', ''])

                if 'Air cooling (W)' in resdict:
                    ackwh = nsum(array(resdict['Air cooling (W)'])) * 0.001
                    rcarray.append(['Total air cooling', '{:.1f}'.format(ackwh), '{:.1f}'.format(ackwh/self.cao['floorarea']), '', '', ''])
                
                if 'Air heating (W)' in resdict and 'Air cooling (W)' in resdict:
                    rcarray.append(['Total air conditioning', '{:.1f}'.format(ahkwh + ackwh), '{:.1f}'.format((ahkwh + ackwh)/self.cao['floorarea']), '', '', ''])
                
                if 'HR heating (W)' in resdict:
                    hrkwh = nsum(array(resdict['HR heating (W)'])) * 0.001
                    rcarray.append(['Total heat recovery', '{:.1f}'.format(hrkwh), '{:.1f}'.format(hrkwh/self.cao['floorarea']), '', '', ''])

            self.rcarray = array(rcarray) 
        else:
            self.rcarray = array([['Invalid object']])

    def drawopen(self, context):
        draw_table(self)
            
def wr_disp(self, context, simnode):
    if self._handle_wr_disp:
        width, height = context.region.width, context.region.height
        self.legend.draw(context, width, height)
        self.dhscatter.draw(context, width, height)
        self.table.draw(context, width, height)
    
def basic_disp(self, context, simnode):
    if self._handle_disp:
        width, height = context.region.width, context.region.height
        self.legend.draw(context, width, height)
        self.table.draw(context, width, height)
    
def comp_disp(self, context, simnode):
    try:
        if self._handle_disp:
            width, height = context.region.width, context.region.height
            self.legend.draw(context, width, height)
            self.table.draw(context, width, height)
            self.tablecomp.draw(context, width, height)
    except:
        pass
    
    if context.scene['liparams']['unit'] in ('ASE (hrs)', 'sDA (%)'):
        self.dhscatter.draw(context, width, height)

def cbdm_disp(self, context, simnode):
    if self._handle_disp:
        width, height = context.region.width, context.region.height
        self.legend.draw(context, width, height)
        self.table.draw(context, width, height)
    
        if context.scene['liparams']['unit'] in ('DA (%)', 'sDA (%)', 'UDI-f (%)', 'UDI-s (%)', 'UDI-a (%)', 'UDI-e (%)', 'ASE (hrs)', 'Max lux', 'Ave lux', 'Min lux', 'kWh', 'kWh/m2'):
            self.dhscatter.draw(context, width, height)
        
def en_disp(self, context, simnode):
    try:
        if self._handle_en_disp:
            width, height = context.region.width, context.region.height
            self.dhscatter.draw(context, width, height)
            self.table.draw(context, width, height)
    except:
        pass

def en_pdisp(self, context, simnode):
    try:
        if self._handle_en_pdisp:
            width, height = context.region.width, context.region.height
            self.barchart.draw(context, width, height)
            self.table.draw(context, width, height)
    except:
        pass
    
class ss_legend(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        
    def update(self, context):
        scene = context.scene
        self.cao = context.active_object        
        self.cols = retcols(context.scene, 20)
        self.col, self.maxres, self.minres, self.scale = scene.vi_leg_col, scene.vi_leg_max, scene.vi_leg_min, scene.vi_leg_scale
        dplaces = retdp(self.maxres, 1)
        resdiff = self.maxres - self.minres
        
        if not context.scene.get('liparams'):
            scene.vi_display = 0
            return

        self.resvals = [format(self.minres + i*(resdiff)/20, '.{}f'.format(dplaces)) for i in range(21)] if self.scale == '0' else \
                        [format(self.minres + (1 - log10(i)/log10(21))*(resdiff), '.{}f'.format(dplaces)) for i in range(1, 22)[::-1]]

        self.resvals = ['{0} - {1}'.format(self.resvals[i], self.resvals[i+1]) for i in range(20)]
        
    def drawopen(self, context):
        draw_legend(self, context.scene, 'Sunlit Time (%)')
    
class basic_legend(Base_Display):
    def __init__(self, pos, width, height, iname, xdiff, ydiff):
        Base_Display.__init__(self, pos, width, height, iname, xdiff, ydiff)
        
    def update(self, context):
        scene = context.scene
        self.cao = context.active_object        
        self.cols = retcols(context.scene, 20)
        self.col, self.maxres, self.minres, self.scale = scene.vi_leg_col, scene.vi_leg_max, scene.vi_leg_min, scene.vi_leg_scale
        dplaces = retdp(self.maxres, 1)
        resdiff = self.maxres - self.minres
        
        if not context.scene.get('liparams'):
            scene.vi_display = 0
            return

        self.resvals = [format(self.minres + i*(resdiff)/20, '.{}f'.format(dplaces)) for i in range(21)] if self.scale == '0' else \
                        [format(self.minres + (1 - log10(i)/log10(21))*(resdiff), '.{}f'.format(dplaces)) for i in range(1, 22)[::-1]]

        self.resvals = ['{0} - {1}'.format(self.resvals[i], self.resvals[i+1]) for i in range(20)]
        
    def drawopen(self, context):
        draw_legend(self, context.scene, context.scene['liparams']['unit'])
    
def ss_disp(self, context, simnode):
    try:
        width, height = context.region.width, context.region.height
        self.legend.draw(context, width, height)
        self.dhscatter.draw(context, width, height)
    except:
        pass
#    self.dhscatter.draw(context, width, height)

def lipanel():
    pass
            
#def li_compliance(self, context, simnode):
#    height, scene, swidth, ewidth = context.region.height, context.scene, 120, 920
#    if not scene.get('li_compliance') or scene.frame_current not in range(scene['liparams']['fs'], scene['liparams']['fe'] + 1) or scene['viparams']['vidisp'] != 'lcpanel':
#        return
#    if simnode['coptions']['canalysis'] == '0':
#        buildtype = ('School', 'Higher Education', 'Healthcare', 'Residential', 'Retail', 'Office & Other')[int(simnode['coptions']['buildtype'])]
#    elif simnode['coptions']['canalysis'] == '1':
#        buildtype = 'Residential'
#        cfshpfsdict = {'totkit': 0, 'kitdf': 0, 'kitsv': 0, 'totliv': 0, 'livdf': 0, 'livsv': 0}
#    if simnode['coptions']['canalysis'] == '3':
#        buildtype = ('School/Office/Commercial', 'Healthcare')[int(simnode['coptions']['buildtype'])]
#        
#    blf.enable(0, blf.KERNING_DEFAULT)
#    blf.shadow(0, 3, 0, 0, 0, 0.5)
#    drawpoly(swidth, height - 40, ewidth, height - 65, 0.7, 1, 1, 1)
#    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#    bgl.glLineWidth(1)
#    horpos, widths = (swidth, 337, 653, ewidth), (swidth, 480, 620, 770, ewidth)
#
#    for p in range(3):
#        drawloop(horpos[p], height - 40, horpos[p+1], height - 65)
#
#    font_id = 0
#    blf.size(font_id, 20, 54)
#    drawfont('Standard: '+('BREEAM HEA1', 'CfSH', 'Green Star', 'LEED EQ8.1')[int(simnode['coptions']['Type'])], font_id, 0, height, 130, 58)
#    drawfont('Project Name: '+scene.li_projname, font_id, 0, height, 663, 58)
#    blf.size(font_id, 20, 40)
#    os = [o for o in bpy.data.objects if o.get('lires')]
#    
#    def space_compliance(os):
#        frame, buildspace, pfs, epfs, lencrit = scene.frame_current, '', [], [], 0
#        for o in os:
#            mat = bpy.data.materials[o['compmat']]
#            o['cr4'] = [('fail', 'pass')[int(com)] for com in o['comps'][str(frame)][:][::2]]
#            o['cr6'] = [cri[4] for cri in o['crit']]
#            if 'fail' in [c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '1'] or bpy.context.scene['liparams']['dfpass'][str(frame)] == 1:
#                pf = 'FAIL'
#            elif 'pass' not in [c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.75'] and len([c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.75']) > 0:
#                if 'pass' not in [c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.5'] and len([c for i, c in enumerate(o['cr4']) if o['cr6'][i] == '0.5']) > 0:
#                    pf = 'FAIL'
#                else:
#                    pf = 'PASS'
#            else:
#                pf = 'PASS'
#            pfs.append(pf)
#
#            if simnode['coptions']['canalysis'] == '1':
#                cfshpfsdict[('totkit', 'totliv')[mat.crspacemenu == '1']] += 1
#                if o['cr4'][0] == 'pass':
#                    cfshpfsdict[('kitdf', 'livdf')[mat.crspacemenu == '1']] += 1
#                if o['cr4'][1] == 'pass':
#                    cfshpfsdict[('kitsv', 'livsv')[mat.crspacemenu == '1']] += 1
#
#            if simnode['coptions']['canalysis'] == '0':
#                ecrit = o['ecrit']
#                o['ecr4'] = [('fail', 'pass')[int(com)] for com in o['ecomps'][str(frame)][:][::2]]
#                o['ecr6'] = [ecri[4] for ecri in ecrit]
#                if 'fail' in [c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '1'] or bpy.context.scene['liparams']['dfpass'][str(frame)] == 1:
#                    epf = 'FAIL'
#                elif 'pass' not in [c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '0.75'] and len([c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '0.75']) > 0:
#                    if 'pass' not in [c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '0.5'] and len([c for i, c in enumerate(o['ecr4']) if o['ecr6'][i] == '0.5']) > 0:
#                        epf = 'FAIL'
#                    else:
#                        epf = 'EXEMPLARY'
#                else:
#                    epf = 'EXEMPLARY'
#                epfs.append(epf)
#
#        if bpy.context.active_object in os:
#            o = bpy.context.active_object
#            lencrit = 1 + len(o['crit'])
#            drawpoly(swidth, height - 70, ewidth, height - 70  - (lencrit)*25, 0.7, 1, 1, 1)
#            drawloop(swidth, height - 70, ewidth, height - 70  - (lencrit)*25)
#            mat = bpy.data.materials[o['compmat']]
#            if simnode['coptions']['canalysis'] == '0':
#                buildspace = ('', '', (' - Public/Staff', ' - Patient')[int(mat.hspacemenu)], (' - Kitchen', ' - Living/Dining/Study', ' - Communal')[int(mat.brspacemenu)], (' - Sales', ' - Office')[int(mat.respacemenu)], '')[int(simnode['coptions']['buildtype'])]
#            elif simnode['coptions']['canalysis'] == '1':
#                buildspace = (' - Kitchen', ' - Living/Dining/Study')[int(mat.crspacemenu)]
#
#            titles = ('Zone Metric', 'Target', 'Achieved', 'PASS/FAIL')
#            tables = [[] for c in range(lencrit -1)]
#            etables = [[] for e in range(len(o['ecrit']))]
#            
#            for c, cr in enumerate(o['crit']):
#                if cr[0] == 'Percent':
#                    if cr[2] == 'Skyview':
#                        tables[c] = ('Percentage area with Skyview (%)', cr[1], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
#                    elif cr[2] == 'DF':  
#                        tables[c] = ('Average Daylight Factor (%)', cr[3], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
#                    elif cr[2] == 'PDF':    
#                        tables[c] = ('Area with point Daylight Factor above {}'.format(cr[3]), cr[1], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
#                    elif cr[2] == 'SDA':    
#                        tables[c] = ('% area achieving sDA300/50%', cr[1], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
#                    elif cr[2] == 'ASE':    
#                        tables[c] = ('% area achieving ASE1000,250'.format(cr[3]), cr[1], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
#   
#                elif cr[0] == 'Ratio':
#                    tables[c] = ('Uniformity ratio', cr[3], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
#                elif cr[0] == 'Min':
#                    tables[c] = ('Minimum {} (%)'.format('Point Daylight Factor'), cr[3], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
#                elif cr[0] == 'Average':
#                    tables[c] = ('Average {} (%)'.format('Daylight Factor'), cr[3], '{:.2f}'.format(o['comps'][str(frame)][:][c*2 + 1]), o['cr4'][c].upper())
#
#            if simnode['coptions']['canalysis'] == '0':
#                for e, ecr in enumerate(ecrit):
#                    if ecr[0] == 'Percent':
#                        if ecr[2] == 'skyview':
#                            etables[e] = ('Percentage area with Skyview (%)', ecr[1], '{:.2f}'.format(o['ecomps'][str(frame)][:][e*2 + 1]), o['ecr4'][e].upper())
#                        elif ecr[2] == 'DF':  
#                            etables[e] = ('Average Daylight Factor (%)', ecr[3], '{:.2f}'.format(o['ecomps'][str(frame)][:][e*2 + 1]), o['ecr4'][e].upper())
#                        elif ecr[2] == 'PDF':    
#                            etables[e] = ('Area with point Daylight Factor above {}'.format(ecr[3]), ecr[1], '{:.2f}'.format(o['ecomps'][str(frame)][:][e*2 + 1]), o['ecr4'][e].upper())
#                    elif ecr[0] == 'Min':
#                        etables[e] = ('Minimum {} (%)'.format('Point Daylight Factor'), ecr[3], '{:.2f}'.format(o['ecomps'][str(frame)][:][e*2 + 1]), o['ecr4'][e].upper())
#
#            for j in range(4):
#                drawloop(widths[j], height - 70, widths[j+1], height - 95)
#
#            bgl.glEnable(bgl.GL_LINE_STIPPLE)
#            for t, tab in enumerate(tables):
#                for j in range(4):
#                    drawloop(widths[j], height - 95 - t*25, widths[j+1], height - 120 - t*25)
#                    if tab[j] == 'FAIL':
#                        bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
#                    elif tab[j] == 'PASS':
#                        bgl.glColor4f(0.0, 0.7, 0.0, 1.0)
#                    blf.size(font_id, 20, 44)
#                    drawfont(tab[j], 0, 0, height, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], 113 + t*25)
#                    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#                    if t == 0:
#                        blf.size(font_id, 20, 48)
#                        drawfont(titles[j], 0, 0, height, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], 88)
#            bgl.glDisable(bgl.GL_LINE_STIPPLE)
#        else:
#            etables = []
#            lencrit = 0
#        
#        tpf = 'FAIL' if 'FAIL' in pfs or 'FAIL*' in pfs else 'PASS'
#        if simnode['coptions']['canalysis'] == '0': 
#            tpf = 'EXEMPLARY' if tpf == 'PASS' and ('FAIL' not in epfs and 'FAIL*' not in epfs) else tpf
#            erows = len(etables) if  tpf == 'EXEMPLARY' else 0
#            lencrit = lencrit + erows if bpy.context.active_object in os else 0
#
#        return(tpf, lencrit, buildspace, etables)
#
#    
#    build_compliance, lencrit, bs, etables = space_compliance(os)
#
#    if build_compliance == 'EXEMPLARY':
#        for t, tab in enumerate(etables):
#            if t == 0:
#                drawpoly(swidth, height - 70 - (lencrit * 25), ewidth, height - 70 - ((lencrit - len(etables)) * 25), 0.7, 1, 1, 1)
#                drawloop(swidth, height - 70 - (lencrit * 25), ewidth, height - 70 - ((lencrit - len(etables)) * 25))
#            for j in range(4):
#                bgl.glEnable(bgl.GL_LINE_STIPPLE)
#                drawloop(widths[j], height - 95 - (lencrit - len(etables) + t - 1) * 25, widths[j+1], height - 120 - (lencrit - len(etables) + t - 1) * 25)
#                if tab[j] == 'FAIL':
#                    bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
#                elif tab[j] == 'PASS':
#                    bgl.glColor4f(0.0, 1.0, 0.0, 1.0)
#                blf.size(font_id, 20, 44)
#                blf.position(font_id, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], height - 113 - (lencrit - len(etables) + t - 1) * 25, 0)
#                blf.draw(font_id, tab[j])
#                bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#                bgl.glDisable(bgl.GL_LINE_STIPPLE)
#
#    blf.position(font_id, 347, height - 58, 0)
#    blf.size(font_id, 20, 54)
#    blf.draw(font_id, 'Buildtype: '+buildtype+bs)
#
#    blf.size(font_id, 20, 52)
#    blf.position(font_id, 130, height - 87 - lencrit*26, 0)
#    if simnode['coptions']['canalysis'] == '0':
#        drawpoly(swidth, height - 70 - lencrit*26, 525, height - 95 - lencrit*26, 0.7, 1, 1, 1)
#        drawloop(swidth, height - 70 - lencrit*26, 370, height - 95 - lencrit*26)
#        drawloop(swidth, height - 70 - lencrit*26, 370, height - 95 - lencrit*26)
#        drawloop(370, height - 70 - lencrit*26, 525, height - 95 - lencrit*26)
#        blf.draw(font_id, 'Building Compliance:')
#        drawfont(build_compliance, 0, lencrit, height, swidth + 150, 87)
#        drawfont('Credits achieved:', 0, lencrit, height, 380, 87)
#        blf.position(font_id, 500, height - 87 - lencrit*26, 0)
#        if build_compliance == 'PASS':
#           blf.draw(font_id,  ('1', '2', '2', '1', '1', '1')[int(simnode['coptions']['buildtype'])])
#        elif build_compliance == 'EXEMPLARY':
#            blf.draw(font_id,  ('2', '3', '3', '2', '2', '2')[int(simnode['coptions']['buildtype'])])
#        else:
#            blf.draw(font_id, '0')
#
#    elif simnode['coptions']['canalysis'] == '1':
#        drawpoly(swidth, height - 70 - lencrit*26, 320, height - 95 - lencrit*26, 0.7, 1, 1, 1)
#        drawloop(swidth, height - 70 - lencrit*26, 320, height - 95 - lencrit*26)
#        drawfont('Credits achieved:', 0, lencrit, height, swidth + 10, 87)
#        cfshcred = 0
#        if cfshpfsdict['kitdf'] == cfshpfsdict['totkit'] and cfshpfsdict['totkit'] != 0:
#            cfshcred += 1
#        if cfshpfsdict['livdf'] == cfshpfsdict['totliv'] and cfshpfsdict['totliv'] != 0:
#            cfshcred += 1
#        if (cfshpfsdict['kitsv'] == cfshpfsdict['totkit'] and  cfshpfsdict['totkit'] != 0) or (cfshpfsdict['livsv'] == cfshpfsdict['totliv'] and cfshpfsdict['totliv'] != 0):
#            cfshcred += 1
#        blf.position(font_id, 270, height - 87 - lencrit*26, 0)
#        blf.draw(font_id, '{} of {}'.format(cfshcred, '3' if 0 not in (cfshpfsdict['totkit'], cfshpfsdict['totliv']) else '2'))
#
#    elif simnode['coptions']['canalysis'] == '3':
#        drawpoly(swidth, height - 70 - lencrit*26, 320, height - 95 - lencrit*26, 0.7, 1, 1, 1)
#        drawloop(swidth, height - 70 - lencrit*26, 320, height - 95 - lencrit*26)
#        drawfont('Credits achieved:', 0, lencrit, height, swidth + 10, 87)
#        totarea = sum([o['oarea'] for o in os])
#        totsdaarea = sum([o['sdapassarea'] for o in os])
#        totasearea = sum([o['asepassarea'] for o in os])
#        leedcred = 0
#        if simnode['coptions']['buildtype'] == '0':
#            if totsdaarea/totarea > 0.55:
#                leedcred += 2
#            if totsdaarea/totarea > 0.75:
#                leedcred += 1
#        if totasearea/totarea > 0.1:
#            leedcred = 0
#        blf.position(font_id, 270, height - 87 - lencrit*26, 0)
#        blf.draw(font_id, '{} of {}'.format(leedcred, ('2', '3')[simnode['coptions']['buildtype'] == '0']))
        
#    bgl.glEnable(bgl.GL_BLEND)
#    bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
#    bgl.glLineWidth(1)
#    sw = 8
#
#    aolen, ailen, jnlen = len(scene.li_assorg), len(scene.li_assind), len(scene.li_jobno)
#    drawpoly(100, 50, 500 + aolen*sw + ailen*sw + jnlen*sw, 25, 0.7, 1, 1, 1)
#    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#    drawloop(100, 50, 260 + aolen*sw, 25)
#    drawloop(260 + aolen*sw, 50, 400 + aolen*sw + ailen*sw, 25)
#    drawloop(400 + aolen*sw + ailen*sw, 50, 500 + aolen*sw + ailen*sw + jnlen*sw, 25)
#    blf.size(font_id, 20, 44)
#    blf.position(font_id, 110, 32, 0)
#    blf.draw(font_id, 'Assessing Organisation:')
#    blf.position(font_id, 250, 32, 0)
#    blf.draw(font_id, scene.li_assorg)
#    blf.position(font_id, 270 + aolen*sw, 32, 0)
#    blf.draw(font_id, 'Assessing Individual:')
#    blf.position(font_id, 395 + aolen*sw, 32, 0)
#    blf.draw(font_id, scene.li_assind)
#    blf.position(font_id, 410 + aolen*sw + ailen*sw, 32, 0)
#    blf.draw(font_id, 'Job Number:')
#    blf.position(font_id, 490 + aolen*sw + ailen*sw, 32, 0)
#    blf.draw(font_id, scene.li_jobno)
#    blf.disable(0, blf.KERNING_DEFAULT)

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

def draw_icon(self):
    drawpoly(self.spos[0], self.spos[1], self.epos[0], self.epos[1], *self.hl)        
    drawloop(self.spos[0], self.spos[1], self.epos[0], self.epos[1])
    bgl.glEnable(bgl.GL_BLEND)
    bpy.data.images[self.image].gl_load(bgl.GL_NEAREST, bgl.GL_NEAREST)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, bpy.data.images[self.image].bindcode[0])
    bgl.glTexParameteri(bgl.GL_TEXTURE_2D,
                            bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
    bgl.glTexParameteri(bgl.GL_TEXTURE_2D,
                            bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
    bgl.glEnable(bgl.GL_TEXTURE_2D)
    bgl.glColor4f(1, 1, 1, 1)
    bgl.glBegin(bgl.GL_QUADS)
    bgl.glTexCoord2i(0, 0)
    bgl.glVertex2f(self.spos[0] + 5, self.spos[1] + 5)
    bgl.glTexCoord2i(1, 0)
    bgl.glVertex2f(self.epos[0] - 5, self.spos[1] + 5)
    bgl.glTexCoord2i(1, 1)
    bgl.glVertex2f(self.epos[0] - 5, self.epos[1] - 5)
    bgl.glTexCoord2i(0, 1)
    bgl.glVertex2f(self.spos[0] + 5, self.epos[1] - 5)
    bgl.glEnd()
    bgl.glDisable(bgl.GL_TEXTURE_2D)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glFlush()
    
def draw_legend(self, scene, unit):
    draw_icon(self)
    font_id = 0
    blf.enable(0, 4)
    blf.enable(0, 8)
    blf.shadow(font_id, 5, 0.7, 0.7, 0.7, 1)    
    levels = len(self.resvals)
    xdiff = self.lepos[0] - self.lspos[0]
    ydiff = self.lepos[1] - self.lspos[1]
    lh = ydiff/(levels + 1)    
    blf.size(font_id, 12, 300)
    titxdimen = blf.dimensions(font_id, unit)[0]
    resxdimen = blf.dimensions(font_id, self.resvals[-1])[0]
    mydimen = blf.dimensions(font_id, unit)[1]
    fontscale = max(titxdimen/(xdiff * 0.9), resxdimen/(xdiff * 0.6), mydimen * 1.25/lh)
    blf.size(font_id, 12, int(300/fontscale))
    if not self.resize:
        self.lspos = [self.spos[0], self.spos[1] - ydiff]
        self.lepos = [self.lspos[0] + xdiff, self.spos[1]]            
    else:
        self.lspos = [self.spos[0], self.lspos[1]]
        self.lepos = [self.lepos[0], self.spos[1]]
    
    bgl.glLineWidth(1)
    drawpoly(self.lspos[0], self.lspos[1], self.lepos[0], self.lepos[1], 1, 1, 1, 1)
    drawloop(self.lspos[0], self.lspos[1], self.lepos[0], self.lepos[1])
    blf.position(font_id, self.lspos[0] + (xdiff - blf.dimensions(font_id, unit)[0]) * 0.45, self.spos[1] - 0.5 * lh - blf.dimensions(font_id, unit)[1] * 0.4, 0)       
    blf.draw(font_id, unit)
#    blf.enable(0, blf.SHADOW)
#    blf.enable(0, blf.KERNING_DEFAULT)
#    blf.shadow(0, 5, 0, 0, 0, 0.7)
    
#    bgl.glColor4f(*scene.vi_display_rp_fc)

    blf.shadow(font_id, 5, 0.8, 0.8, 0.8, 1)
    lh = ydiff/(levels + 1)
    blf.size(font_id, 12, int(250/fontscale))
    bgl.glDisable(bgl.GL_BLEND)
    
    for i in range(levels):
        num = self.resvals[i]
        rgba = self.cols[i]
        bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
        drawpoly(self.lspos[0], int(self.lspos[1] + i * lh), int(self.lspos[0] + xdiff * 0.4), int(self.lspos[1] + (i + 1) * lh), *rgba)    
        drawloop(self.lspos[0], int(self.lspos[1] + i * lh), int(self.lspos[0] + xdiff * 0.4), int(self.lspos[1] + (i + 1) * lh))
        drawloop(int(self.lspos[0] + xdiff * 0.4), int(self.lspos[1] + i * lh), self.lepos[0], int(self.lspos[1] + (i + 1) * lh))
        
        ndimen = blf.dimensions(font_id, "{}".format(num))
        blf.position(font_id, int(self.lepos[0] - xdiff * 0.05 - ndimen[0]), int(self.lspos[1] + i * lh) + int((lh - ndimen[1])*0.5), 0)
        bgl.glColor4f(0, 0, 0, 1)
        blf.draw(font_id, "{}".format(self.resvals[i]))
    
    bgl.glLineWidth(1)
    bgl.glColor4f(0, 0, 0, 1)
    blf.disable(0, 8)  
    blf.disable(0, 4)
    
def draw_dhscatter(self, scene, x, y, z, tit, xlab, ylab, zlab, valmin, valmax):
    self.plt.close()
    self.col = scene.vi_leg_col
    x = [x[0] - 0.5] + [xval + 0.5 for xval in x] 
    y = [y[0] - 0.5] + [yval + 0.5 for yval in y]
    self.plt.figure(figsize=(6 + len(x)/len(y), 6))
    
    self.plt.title(tit, size = 18).set_position([.5, 1.025])
    self.plt.xlabel(xlab, size = 18)
    self.plt.ylabel(ylab, size = 18)
    self.plt.pcolor(x, y, z, cmap=self.col, vmin=valmin, vmax=valmax)#, norm=plt.matplotlib.colors.LogNorm())#, edgecolors='b', linewidths=1, vmin = 0, vmax = 4000)
    self.plt.colorbar(use_gridspec=True).set_label(label=zlab,size=20)
    self.plt.axis([min(x),max(x),min(y),max(y)], size = 19)
    self.plt.tight_layout(rect=[0, 0, 1 + ((len(x)/len(y)) - 1) * 0.005, 1])

def draw_barchart(self, scene, x, y, tit, xlab, ylab, ymin, ymax):
    self.plt.close()
    self.plt.figure(figsize=(6 + len(x)/len(y), 6))    
    self.plt.title(tit, size = 18).set_position([.5, 1.025])
    self.plt.xlabel(xlab, size = 18)
    self.plt.ylabel(ylab, size = 18)
    cols = [(yval - ymin)/(ymax - ymin) for yval in y]
    self.plt.bar(x, y, align='center', color = [mcm.get_cmap(self.col)(i) for i in cols])
    self.plt.tight_layout(rect=[0, 0, 1 + ((len(x)/len(y)) - 1) * 0.005, 1])
    
def save_plot(self, scene, filename):
    fileloc = os.path.join(scene['viparams']['newdir'], 'images', filename)
    self.plt.savefig(fileloc, pad_inches = 0.1)
    
    if filename not in [i.name for i in bpy.data.images]:
        self.gimage = filename
        bpy.data.images.load(fileloc)
    else:
        self.gimage = filename
        bpy.data.images[filename].reload()
        
    bpy.data.images[self.gimage].user_clear()

def show_plot(self):
    try:
        self.plt.show()
    except:
        pass
        
def draw_image(self, topgap):
    draw_icon(self)
    self.xdiff = self.lepos[0] - self.lspos[0]
    self.ydiff = self.lepos[1] - self.lspos[1]
    if not self.resize:
        self.lspos = [self.spos[0], self.spos[1] - self.ydiff]
        self.lepos = [self.lspos[0] + self.xdiff, self.spos[1]]            
    else:
        self.lspos = [self.spos[0], self.lspos[1]]
        self.lepos = [self.lepos[0], self.spos[1]]

    bpy.data.images[self.gimage].reload()
    drawpoly(self.lspos[0], self.lspos[1], self.lepos[0], self.lepos[1], 1, 1, 1, 1)        
    drawloop(self.lspos[0], self.lspos[1], self.lepos[0], self.lepos[1])
    bgl.glEnable(bgl.GL_BLEND)
    bpy.data.images[self.gimage].gl_load(bgl.GL_NEAREST, bgl.GL_NEAREST)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, bpy.data.images[self.gimage].bindcode[0])
    bgl.glTexParameteri(bgl.GL_TEXTURE_2D,
                            bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
    bgl.glTexParameteri(bgl.GL_TEXTURE_2D,
                            bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
    bgl.glEnable(bgl.GL_TEXTURE_2D)
    bgl.glColor4f(1, 1, 1, 1)
    bgl.glBegin(bgl.GL_QUADS)
    bgl.glTexCoord2i(0, 0)
    bgl.glVertex2f(self.lspos[0] + 5, self.lspos[1] + 5)
    bgl.glTexCoord2i(1, 0)
    bgl.glVertex2f(self.lepos[0] - 5, self.lspos[1] + 5)
    bgl.glTexCoord2i(1, 1)
    bgl.glVertex2f(self.lepos[0] - 5, self.lepos[1] - topgap)
    bgl.glTexCoord2i(0, 1)
    bgl.glVertex2f(self.lspos[0] + 5, self.lepos[1] - topgap)
    bgl.glEnd()
    bgl.glDisable(bgl.GL_TEXTURE_2D)
    bgl.glFlush()
    
def draw_table(self):
    draw_icon(self) 
    font_id = 0
    blf.enable(0, 4)
    blf.enable(0, 8)
    blf.shadow(font_id, 5, 0.9, 0.9, 0.9, 1)
    blf.size(font_id, 44, self.fontdpi)
    rcshape = self.rcarray.shape
    [rowno, colno] = self.rcarray.shape
    
    self.xdiff = self.lepos[0] - self.lspos[0]
    self.ydiff = self.lepos[1] - self.lspos[1]
    colpos = [int(0.01 * self.xdiff)]
    
    if not self.resize:
        self.lspos = [self.spos[0], self.spos[1] - self.ydiff]
        self.lepos = [self.lspos[0] + self.xdiff, self.spos[1]]            
    else:
        self.lspos = [self.spos[0], self.lspos[1]]
        self.lepos = [self.lepos[0], self.spos[1]]
        
    coltextwidths = array([int(max([blf.dimensions(font_id, '{}'.format(e))[0] for e in entry]) + 0.05 * self.xdiff) for entry in self.rcarray.T])
    colscale = sum(coltextwidths)/(self.xdiff * 0.98)
    colwidths = (coltextwidths/colscale).astype(int)
   
    for cw in colwidths:
        colpos.append(cw + colpos[-1])

    maxrowtextheight = max([max([blf.dimensions(font_id, '{}'.format(e))[1] for e in entry if e])  for entry in self.rcarray.T])
    rowtextheight = maxrowtextheight + 0.1 * self.ydiff/rowno
    rowscale = (rowno * rowtextheight)/(self.ydiff - self.xdiff * 0.05)
    rowheight = int((self.ydiff - self.xdiff * 0.01)/rowno)
#    rowoffset = 0.5 * maxrowtextheight
    rowtops = [int(self.lepos[1]  - self.xdiff * 0.005 - r * rowheight) for r in range(rowno)]
    rowbots = [int(self.lepos[1]  - self.xdiff * 0.005 - (r + 1) * rowheight) for r in range(rowno)]
    rowmids = [0.5 * (rowtops[r] + rowbots[r]) for r in range(rowno)]
    
    if abs(max(colscale, rowscale) - 1) > 0.05:
        self.fontdpi = int(self.fontdpi/max(colscale, rowscale))
   
    blf.size(font_id, 44, self.fontdpi)
    drawpoly(self.lspos[0], self.lspos[1], self.lepos[0], self.lepos[1], 1, 1, 1, 1)        
    drawloop(self.lspos[0], self.lspos[1], self.lepos[0], self.lepos[1])       
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    
    for r in range(rcshape[0]):
        for c in range(rcshape[1]):
            if self.rcarray[r][c]:                
                if c == 0:
                    blf.position(font_id, self.lspos[0] + colpos[c] + 0.005 * self.xdiff, int(rowmids[r] - 0.5 * blf.dimensions(font_id, 'H')[1]), 0)#.format(self.rcarray[r][c]))[1])), 0)#int(self.lepos[1] - rowoffset - rowheight * (r + 0.5)), 0)
                else:
                    blf.position(font_id, self.lspos[0] + colpos[c] + colwidths[c] * 0.5 - int(blf.dimensions(font_id, '{}'.format(self.rcarray[r][c]))[0] * 0.5), int(rowmids[r] - 0.5 * blf.dimensions(font_id, 'H')[1]), 0)
                drawloop(int(self.lspos[0] + colpos[c]), rowtops[r], self.lspos[0] + colpos[c + 1], rowbots[r])                
                if self.rcarray[r][c] == 'Pass':
                    bgl.glColor3f(0.0, 0.6, 0.0)
                elif self.rcarray[r][c] == 'Fail':
                    bgl.glColor3f(0.6, 0.0, 0.0)
                else:
                    bgl.glColor3f(0.0, 0.0, 0.0)
                blf.draw(font_id, '{}'.format(self.rcarray[r][c]))
#    else:
#        for r in range(rcshape[0]):
#            for c in range(rcshape[1]):
#                if self.rcarray[r][c]:
#                    if c == 0:
#                        blf.position(font_id, self.lspos[0] + colpos[c] + 0.01 * self.xdiff, self.lepos[1] -  0.01 * self.xdiff - int(rowheight * (r + 0.25)) - int(blf.dimensions(font_id, '{}'.format(self.rcarray[1][1]))[1]), 0)
#                    else:
#                        blf.position(font_id, self.lspos[0] + colpos[c] + colwidths[c] * 0.5 - int(blf.dimensions(font_id, '{}'.format(self.rcarray[r][c]))[0] * 0.5), self.lepos[1] -  0.01 * self.xdiff - int(rowheight * (r + 0.25)) - int(blf.dimensions(font_id, '{}'.format(self.rcarray[1][1]))[1]), 0)
#                    drawloop(int(self.lspos[0] + colpos[c]), int(self.lepos[1] - 0.01 * self.xdiff - r * rowheight), self.lspos[0] + colpos[c + 1], int(self.lepos[1] - 0.01 * self.xdiff - (r + 1) * rowheight))                
#                    blf.draw(font_id, '{}'.format(self.rcarray[r][c]))
    bgl.glDisable(bgl.GL_BLEND) 
    blf.disable(0, 8)
    blf.disable(0, 4)
    bgl.glEnd()
    bgl.glFlush()
    
def setcols(self, context):
    scene = context.scene
    bpy.app.handlers.frame_change_pre.clear()
    fc = scene.frame_current
    rdict = {'envi_temp': 'Temp', 'envi_hum': 'Hum', 'envi_heat': 'Heat', 'envi_cool': 'Cool', 'envi_co2': 'CO2', 'envi_pmv': 'PMV', 'envi_ppd': 'PPD', 'envi_aheat': 'AHeat', 
    'envi_acool': 'ACool', 'envi_hrheat': 'HRheat', 'envi_shg': 'SHG'}
    mmdict = {'envi_temp': (scene.en_temp_max, scene.en_temp_min), 'envi_hum': (scene.en_hum_max, scene.en_hum_min), 'envi_heat': (scene.en_heat_max, scene.en_heat_min), 
    'envi_cool': (scene.en_cool_max, scene.en_cool_min), 'envi_co2': (scene.en_co2_max, scene.en_co2_min), 'envi_ppd': (scene.en_ppd_max, scene.en_ppd_min),
    'envi_pmv': (scene.en_pmv_max, scene.en_pmv_min), 'envi_aheat': (scene.en_aheat_max, scene.en_aheat_min), 'envi_acool': (scene.en_acool_max, scene.en_acool_min),
    'envi_hrheat': (scene.en_hrheat_max, scene.en_hrheat_min), 'envi_shg': (scene.en_shg_max, scene.en_shg_min)}
    resstring = retenvires(scene)
    cmap = mcm.get_cmap(scene.vi_leg_col)
    
    for o in [o for o in bpy.data.objects if o.get('VIType') and o['VIType'] in ('envi_temp', 'envi_hum', 'envi_heat', 'envi_cool', 'envi_co2', 'envi_pmv', 'envi_ppd', 'envi_aheat', 'envi_acool', 'envi_hrheat', 'envi_shg') and o.get(resstring)]:
        if (o['max'], o['min']) != mmdict[o['VIType']] or o['cmap'] != scene.vi_leg_col:
#            (rmax, rmin) = mmdict[o['VIType']]    
            (o['max'], o['min']) = mmdict[o['VIType']]  
            o['cmap'] = scene.vi_leg_col
            rdiff = o['max'] - o['min']
            mat = o.material_slots[0].material
            mfcs = mat.animation_data.action.fcurves
            dclist = []
    
            for mfc in mfcs:
                if mfc.data_path == 'diffuse_color':
                    dclist.append(mfc)
    
            frames = range(scene.frame_start, scene.frame_end + 1)

            for frame in frames:
                col = cmap((o[resstring][rdict[o['VIType']]][frame] - o['min'])/(rdiff))
                dclist[0].keyframe_points[frame].co = frame, col[0]
                dclist[1].keyframe_points[frame].co = frame, col[1]
                dclist[2].keyframe_points[frame].co = frame, col[2]

    scene.frame_set(fc)
    if recalculate_text not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(recalculate_text) 
     