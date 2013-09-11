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

import bpy, os, subprocess, colorsys, sys, datetime
from math import pi
from subprocess import PIPE, Popen, STDOUT
from . import vi_func
from . import livi_export

try:
    import numpy
    np = 1
except:
    np = 0

def radfexport(scene, export_op, node, geonode):
    for frame in range(scene.frame_start, scene.frame_end + 1):
        livi_export.fexport(scene, frame, export_op, node, geonode)

def rad_prev(prev_op, node, geonode):
    scene = bpy.context.scene
    if node.simacc == ("1", "3")[node.name == 'LiVi Basic']:
        params = node.cusacc
    else:
        num = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-ar", 128, 512, 1024), ("-as", 128, 512, 1024), ("-aa", 0.3, 0.15, 0.08), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.01, 0.002))
        params = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(node.simacc)+1] for n in num]))

    if os.path.isfile(geonode.filebase+"-0.rad"):
        cam = scene.camera
        if cam != None:
            cang = 180 if 'VI Glare' in node.name else cam.data.angle*180/pi
            vv = 180 if 'VI Glare' in node.name else cang * scene.render.resolution_y/scene.render.resolution_x
            rvucmd = "rvu -w -n {0} -vv {1:.3f} -vh {2:.3f} -vd {3[0][2]:.3f} {3[1][2]:.3f} {3[2][2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct &".format(geonode.nproc, vv, cang, -1*cam.matrix_world, cam.location, params, geonode.filebase, scene.frame_current)
            rvurun = Popen(rvucmd, shell = True, stdout=PIPE, stderr=STDOUT)
            for l,line in enumerate(rvurun.stdout):
                if 'octree stale?' in line.decode():
                    radfexport(scene, prev_op, node, geonode)
                    rad_prev(prev_op, node, geonode)
                    return
        else:
            prev_op.report({'ERROR'}, "There is no camera in the scene. Radiance preview will not work")
    else:
        prev_op.report({'ERROR'},"Missing export file. Make sure you have exported the scene.")

def li_calc(calc_op, node, geonode):
    scene = bpy.context.scene
    if os.lstat(geonode.filebase+".rtrace").st_size == 0:
        calc_op.report({'ERROR'},"There are no materials with the livi sensor option enabled")
    else:
        if node.simacc == ("0", "3")[node.name == 'LiVi Basic']:
            params = node.cusacc
        else:
            num = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-ar", 128, 512, 1024), ("-as", 128, 512, 1024), ("-aa", 0.3, 0.15, 0.08), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.01, 0.002))
            params = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(node.simacc)+1] for n in num]))

        vi_func.clearscened(scene)
        res = svres = [[0 for p in range(geonode.reslen)] for x in range(scene.frame_end + 1 - scene.frame_start)]
        for frame in range(scene.frame_start, scene.frame_end+1):
            if os.path.isfile("{}-{}.af".format(geonode.filebase, frame)):
                subprocess.call("{} {}-{}.af".format(geonode.rm, geonode.filebase, frame), shell=True)
            rtcmd = "rtrace -n {0} -w {1} -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(geonode.nproc, params, geonode.filebase, frame, node.simalg) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
            rtrun = Popen(rtcmd, shell = True, stdout=PIPE, stderr=STDOUT)
            resfile = open(geonode.newdir+geonode.fold+node.resname+"-"+str(frame)+".res", 'w')
            for l,line in enumerate(rtrun.stdout):
                if 'octree stale?' in line.decode():
                    resfile.close()
                    radfexport(scene, calc_op, node, geonode)
                    li_calc(calc_op, node, geonode)
                    return
                res[frame][l] =float(line.decode())
            resfile.write("{}".format(res[frame]).strip("]").strip("["))
            resfile.close()
            if node.name == 'LiVi Compliance':
                if node.analysismenu == '0':
                    svcmd = "rtrace -n {0} -w {1} -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(geonode.nproc, '-ab 1', geonode.filebase, frame, node.simalg) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                    svrun = Popen(svcmd, shell = True, stdout=PIPE, stderr=STDOUT)
                    svresfile = open(geonode.newdir+geonode.fold+'skyview'+"-"+str(frame)+".res", 'w')
                    for sv,line in enumerate(svrun.stdout):
                        svres[frame][sv] = float(line.decode())
                    svresfile.write("{}".format(svres[frame]).strip("]").strip("["))
                    svresfile.close()
                                

        node['maxres'] = [max(res[i]) for i in range(scene.frame_end + 1 - scene.frame_start)]
        node['minres'] = [min(res[i]) for i in range(scene.frame_end + 1 - scene.frame_start)]
        node['avres'] = [sum(res[i])/len(res[i]) for i in range(scene.frame_end + 1 - scene.frame_start)]
        resapply(res, svres, node, geonode)
        calc_op.report({'INFO'}, "Calculation is finished.")

def resapply(res, svres, node, geonode):
    
    scene = bpy.context.scene

    for frame in range(scene.frame_start, scene.frame_end+1):
        rgb = []
        lcol_i = []
        mcol_i = 0
        f = 0
        for i in range(0, len(res[frame])):
            h = 0.75*(1-(res[frame][i]-min(node['minres']))/(max(node['maxres']) + 0.01 - min(node['minres'])))
            rgb.append(colorsys.hsv_to_rgb(h, 1.0, 1.0))

        for geo in [geo for geo in scene.objects if geo.type == 'MESH']:
            if bpy.context.active_object:
                bpy.ops.object.mode_set()
            bpy.ops.object.select_all(action = 'DESELECT')
            scene.objects.active = None
            if geo.licalc == 1:
                crit = ['foo']
                totarea = 0
                passarea = 0
                scene.objects.active = geo
                geo.select = True
                if frame == 0:
                    while len(geo.data.vertex_colors) > 0:
                        bpy.ops.mesh.vertex_color_remove()

                bpy.ops.mesh.vertex_color_add()
                geo.data.vertex_colors[frame].name = str(frame)
                vertexColour = geo.data.vertex_colors[frame]
                mat = [matslot.material for matslot in geo.material_slots if matslot.material.livi_sense][0]
                
                if mat.livi_compliance:
                    if node.analysismenu == '0':
#                            standard = 'BREEAM HEA 1'
#                            buildtype = ('School', 'Higher Education', 'Healthcare', 'Residential', 'Retails')[int(node.bambuildtype)]
                        if node.bambuildmenu == '0':
                            crit.append('')
                        elif node.bambuildmenu == '1':
                            crit.append('')
                        elif node.bambuildmenu == '2':
                            if node.hspacemenu == '0':
                                crit.append('')
                            elif node.hspacemenu == '1':
                                crit.append('')
                        elif node.bambuildmenu == '3':
                            if mat.rspacemenu == '0':
                                crit.append(['Percent', 80, 'DF', 2])
                                crit.append(['Percent', 80, 'Skyview', 1])
                            elif mat.rspacemenu == '1':
                                crit.append(['Percent', 80, 'DF', 1.5])
                                crit.append(['Percent', 80, 'Skyview', 1])  
                            elif mat.rspacemenu == '2':
                                if not mat.gl_roof:
                                    crit.append(['Percent', 80, 'DF', 2]) 
                                    crit.append(['Ratio', 100, 'Uni', 0.4]) 
                                    crit.append(['Min', 100, 'DF', 0.8]) 
                                    crit.append(['Percent', 80, 'Skyview', 1])
                                else:
                                    crit.append(['Percent', 80, 'DF', 2])
                                    crit.append(['Ratio', 100, 'Uni', 0.7])
                                    crit.append(['Min', 100, 'DF', 1.4])
                                    crit.append(['Percent', 80, 'Skyview', 1])
                        elif node.bambuildmenu == '4':
                            if mat.respacemenu == '0':
                                crit.append('')
                            if mat.respacemenu == '1':
                                crit.append('')
  
                for c in crit:  
                    
                    for face in geo.data.polygons:
                        if geo.data.materials[face.material_index].livi_sense:
                            if geonode.cpoint == '1':
                                if c == 'foo':
                                    for loop_index in face.loop_indices:
                                        v = geo.data.loops[loop_index].vertex_index
                                        col_i = [vi for vi, vval in enumerate(geo['cverts']) if v == geo['cverts'][vi]][0]
                                        lcol_i.append(col_i)
                                        vertexColour.data[loop_index].color = rgb[col_i+mcol_i]
                                    
                            if geonode.cpoint == '0':
                                if c == 'foo':
                                    for loop_index in face.loop_indices:
                                        vertexColour.data[loop_index].color = rgb[f]
                                else:
                                    if geo.data.materials[face.material_index].livi_compliance:
                                        if c[2] == 'DF':
                                            if c[0] == 'Percent':
                                                totarea += vi_func.triarea(geo, face)
                                                if res[frame][f] > c[3]:
                                                    passarea += vi_func.triarea(geo, face)
                                        
                                        if c[2] == 'Skyview':
                                            totarea += vi_func.triarea(geo, face)
                                            if svres[frame][f] > 0:
                                                passarea += vi_func.triarea(geo, face)
                                        
                                        
                                        
                        f += 1
                    
                    if c != 'foo' and c[0] == 'Percent':
                        
                        if passarea > c[1]*0.01*totarea:
                            c.append('pass')
                        else:
                            c.append('fail')
                        c.append(100*passarea/totarea)
                        
                        passarea, totarea = 0, 0
                    
                    if c[0] == 'Min':
                        if min(res[frame]) > c[3]:
                            c.append('pass')
                        else:
                            c.append('fail')
                        c.append(min(res[frame]))
                        
                    if c[2] == 'Uni':
                        if min(res[frame])/(sum(res[frame])/len(res[frame])) >= c[3]:
                            c.append('pass')
                        else:
                            c.append('fail')
                        c.append(min(res[frame])/(sum(res[frame])/len(res[frame])))
                    
                    f = 0    
                mcol_i = len(tuple(set(lcol_i)))
                print(crit)
           
            
#            except Exception as e:
#                print(e)

            if geo.licalc == 1:
                scene.objects.active = geo
                geo.select = True
                if frame == 0:
                    while len(geo.data.vertex_colors) > 0:
                        bpy.ops.mesh.vertex_color_remove()

                bpy.ops.mesh.vertex_color_add()
                geo.data.vertex_colors[frame].name = str(frame)
                vertexColour = geo.data.vertex_colors[frame]

                for face in geo.data.polygons:
                    if geo.data.materials[face.material_index].livi_sense:
                        if geonode.cpoint == '1':
                            cvtup = tuple(geo['cverts'])
                            for loop_index in face.loop_indices:
                                v = geo.data.loops[loop_index].vertex_index
                                if v in cvtup:
                                    col_i = cvtup.index(v)
                                lcol_i.append(col_i)
                                vertexColour.data[loop_index].color = rgb[col_i+mcol_i]

                        if geonode.cpoint == '0':
                            for loop_index in face.loop_indices:
                                vertexColour.data[loop_index].color = rgb[f]
                            f += 1
                mcol_i = len(list(set(lcol_i)))


    for frame in range(scene.frame_start, scene.frame_end+1):
        scene.frame_set(frame)
        for geo in scene.objects:
            if geo.licalc == 1:
                for vc in geo.data.vertex_colors:
                    if frame == int(vc.name):
                        vc.active = 1
                        vc.active_render = 1
                        vc.keyframe_insert("active")
                        vc.keyframe_insert("active_render")
                    else:
                        vc.active = 0
                        vc.active_render = 0
                        vc.keyframe_insert("active")
                        vc.keyframe_insert("active_render")

    bpy.ops.wm.save_mainfile(check_existing = False)

