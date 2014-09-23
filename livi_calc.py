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

import bpy, os, subprocess, colorsys, datetime, mathutils
from subprocess import PIPE, Popen, STDOUT
from . import vi_func
from . import livi_export

try:
    import numpy
    np = 1
except:
    np = 0

def radfexport(scene, export_op, connode, geonode, frames):
    for frame in frames:
        livi_export.fexport(scene, frame, export_op, connode, geonode, pause = 1)

def li_calc(calc_op, simnode, connode, geonode, simacc, **kwargs): 
    scene = bpy.context.scene
    frames = range(scene.fs, scene.fe + 1) if not kwargs.get('genframe') else [kwargs['genframe']]
    os.chdir(scene['viparams']['newdir'])
    if os.lstat("{}.rtrace".format(scene['viparams']['filebase'])).st_size == 0:
        calc_op.report({'ERROR'},"There are no materials with the livi sensor option enabled")
    else:
        if np == 1:
            (res, svres) = (numpy.zeros([len(frames), geonode['reslen']]), numpy.zeros([len(frames), geonode['reslen']])) if np == 1 else ([[[0 for p in range(geonode['reslen'])] for x in range(len(frames))] for x in range(2)])

        for frame in frames:            
            findex = frame - scene.fs if not kwargs.get('genframe') else 0
            if connode.bl_label in ('LiVi Basic', 'LiVi Compliance') or (connode.bl_label == 'LiVi CBDM' and int(connode.analysismenu) < 2):
                if os.path.isfile("{}-{}.af".format(scene['viparams']['filebase'], frame)):
                    subprocess.call("{} {}-{}.af".format(scene['viparams']['rm'], scene['viparams']['filebase'], frame), shell=True)
                rtcmd = "rtrace -n {0} -w {1} -faa -h -ov -I {2}-{3}.oct  < {2}.rtrace {4}".format(scene['viparams']['nproc'], simnode['radparams'], scene['viparams']['filebase'], frame, connode['simalg']) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                rtrun = Popen(rtcmd, shell = True, stdout=PIPE, stderr=STDOUT)                
                with open(os.path.join(scene['viparams']['newdir'], connode['resname']+"-{}.res".format(frame)), 'w') as resfile:
                    for l,line in enumerate(rtrun.stdout):
                        res[findex][l] = eval(line.decode())                
                        resfile.write(line.decode())
                
            if connode.bl_label == 'LiVi Compliance' and connode.analysismenu in ('0', '1'):
                if connode.analysismenu in ('0', '1'):
                    svcmd = "rtrace -n {0} -w {1} -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(scene['viparams']['nproc'], '-ab 1 -ad 8192 -aa 0 -ar 512 -as 1024 -lw 0.0002', scene['viparams']['filebase'], frame, connode['simalg']) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                    svrun = Popen(svcmd, shell = True, stdout=PIPE, stderr=STDOUT)                  
                    with open(os.path.join(scene['viparams']['newdir'],'skyview'+"-"+str(frame)+".res"), 'w') as svresfile:
                        for sv,line in enumerate(svrun.stdout):
                            svres[findex][sv] = eval(line.decode())
                            svresfile.write(line.decode())

            if connode.bl_label == 'LiVi CBDM' and int(connode.analysismenu) > 1:
                if connode.sourcemenu == '1':
                    connode['vecvals'], vals = vi_func.mtx2vals(open(connode.mtxname, "r").readlines(), datetime.datetime(2010, 1, 1).weekday(), '')
                hours = 0
                sensarray = [[0 for x in range(146)] for y in range(geonode['reslen'])] if np == 0 else numpy.zeros([geonode['reslen'], 146])
                oconvcmd = "oconv -w - > {0}-ws.oct".format(scene['viparams']['filebase'])
                Popen(oconvcmd, shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate(input = (connode['whitesky']+geonode['radfiles'][frame]).encode('utf-8'))
                senscmd = scene['viparams']['cat']+scene['viparams']['filebase']+".rtrace | rcontrib -w  -h -I -fo -bn 146 {} -n {} -f tregenza.cal -b tbin -m sky_glow {}-ws.oct".format(simnode['radparams'], scene['viparams']['nproc'], scene['viparams']['filebase'])
                sensrun = Popen(senscmd, shell = True, stdout=PIPE)
                
                for li, line in enumerate(sensrun.stdout):
                    decline = [float(ld) for ld in line.decode().split('\t') if ld != '\n']
                    if connode.analysismenu in ('2', '4'):
                        sensarray[li] = [179*((decline[v]*0.265)+ (decline[v+1]*0.67) + (decline[v+2]*0.065)) for v in range(0, 438, 3)]
                    elif connode.analysismenu == '3':
                        sensarray[li] = [sum(decline[v:v+3]) for v in range(0, 438, 3)]

                for l, readings in enumerate(connode['vecvals']):
                    if connode.analysismenu == '3' or (connode.cbdm_start_hour <= readings[:][0] < connode.cbdm_end_hour and readings[:][1] < connode['wd']):
                        finalillu = [numpy.sum([numpy.multiply(sensarray[f], readings[2:])]) for f in range(geonode['reslen'])] if np == 1 else [sum([a*b for a,b in zip(sensarray[f],readings[2:])]) for f in range(geonode['reslen'])]
                        hours += 1
                        if connode.analysismenu == '2':
                            res[findex] = numpy.sum([res[findex], [reading >= connode.dalux for reading in finalillu]], axis = 0) if np == 1 else [res[findex][k] + (0, 1)[finalillu[k] >= connode.dalux] for k in range(len(finalillu))]

                        elif connode.analysismenu == '3':
                            if np ==1:
                                if hours == 1:
                                    reswatt = numpy.zeros((len(frames), len(connode['vecvals']), geonode['reslen'])) 
                                reswatt[findex][l] = finalillu
                                [numpy.append(res[findex][i], finalillu[i]) for i in range(len(finalillu))]                                
                            else:
                                res[findex].append(finalillu)             
                        elif connode.analysismenu == '4':
                            res[findex] = numpy.sum([res[findex], [connode.daauto >= reading >= connode.dasupp for reading in finalillu]], axis = 0) if np == 1 else [res[findex][k] + (0, 1)[connode.daauto >= finalillu[k] >= connode.dasupp] for k in range(len(finalillu))]
                
                if connode.analysismenu in ('2', '4'):
                    if hours != 0:
                        res[findex] = res[frame]*100/hours if np == 1 else [rf*100/hours for rf in res[findex][0]]
                    with open(os.path.join(scene['viparams']['newdir'], connode['resname']+"-"+str(frame)+".res"), "w") as daresfile:
                        [daresfile.write("{:.2f}\n".format(r)) for r in res[findex]]
                
                if connode.analysismenu == '3':
                    res = reswatt

            if connode.analysismenu != '3' or connode.bl_label != 'LiVi CBDM':
                fi, vi = 0, 0
                for geo in vi_func.retobjs('livic'):
                    lenv, lenf = len(geo['cverts']), len(geo['cfaces'])
                    sensearea = sum(geo['lisenseareas'])
                    if not sensearea:
                        calc_op.report({'INFO'}, geo.name+" has a livi sensor material associated with, but not assigned to any faces")
                    else: 
                        if geonode.cpoint == '1':
                            weightres = sum([res[findex][ri] * area for ri, area in zip(range(vi, vi+lenv), geo['lisenseareas'])])
                            obres = res[findex][vi:vi+lenv]
                            vi += lenv
                        else:
                            weightres = sum([res[findex][ri] * area for ri, area in zip(range(fi, fi+lenf), geo['lisenseareas'])])
                            obres = res[findex][fi:fi+lenf]
                            fi += lenf
                                                                   
                        if (frame == scene.fs and not kwargs.get('genframe')) or (kwargs.get('genframe') and kwargs['genframe'] == scene.frame_start):
                            geo['oave'], geo['omax'], geo['omin'], geo['oreslist'] = {}, {}, {}, {}
    
                        geo['oave'][str(frame)] = weightres/sensearea
                        geo['omax'][str(frame)] = max(obres)
                        geo['omin'][str(frame)] = min(obres)
                        geo['oreslist'][str(frame)] = obres 
                                   
        if not kwargs:           
            resapply(calc_op, res, svres, simnode, connode, geonode)
            vi_func.vcframe('', scene, [ob for ob in scene.objects if ob.licalc] , simnode['Animation'])
        else:
            return(res[0])
   
def resapply(calc_op, res, svres, simnode, connode, geonode):
    scene = bpy.context.scene    
    if connode.analysismenu != '3' or connode.bl_label != 'LiVi CBDM':
        if np == 1:
            simnode['maxres'] = list([numpy.amax(res[i]) for i in range(scene.fs, scene.fe + 1)])
            simnode['minres'] = [numpy.amin(res[i]) for i in range(scene.fs, scene.fe + 1)]
            simnode['avres'] = [numpy.average(res[i]) for i in range(scene.fs, scene.fe + 1)]
        else:
            simnode['maxres'] = [max(res[i]) for i in range(scene.fs, scene.fe + 1)]
            simnode['minres'] = [min(res[i]) for i in range(scene.fs, scene.fe + 1)]
            simnode['avres'] = [sum(res[i])/len(res[i]) for i in range(scene.fs, scene.fe + 1)]
    
        crits = []
        dfpass = [0 for f in range(scene.fs, scene.fe + 1)]
        edfpass = [0 for f in range(scene.fs, scene.fe + 1)]
        
        for fr, frame in enumerate(range(scene.fs, scene.fe + 1)):
            scene.frame_set(frame)
            fi = 0
            dftotarea, dfpassarea, edfpassarea, edftotarea, mcol_i, pstart, fsv, sof, eof = 0, 0, 0, 0, 0, 0, 0, 0, 0
            rgb, lcol_i = [], []
            if connode.bl_label != 'LiVi CBDM' or connode.analysismenu != '3':
                for i in range(len(res[fr])):
                    h = 0.75*(1-(res[fr][i]-min(simnode['minres']))/(max(simnode['maxres']) + 0.01 - min(simnode['minres'])))
                    rgb.append(colorsys.hsv_to_rgb(h, 1.0, 1.0))
        
            if bpy.context.active_object and bpy.context.active_object.hide == 'False':
                bpy.ops.object.mode_set()
        
            for geo in vi_func.retobjs('livic'):
                bpy.ops.object.select_all(action = 'DESELECT')
                scene.objects.active = None
                geoareas = geo['lisenseareas']
                geoarea = sum(geoareas)
                lenpoints = len(geo['cfaces']) if geonode.cpoint == '0' else len(geo['cverts'])
                geofaces = [face for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense]
                geos = [geo.data.polygons[fi] for fi in geo['cfaces']] if geonode.cpoint == '0' else [geo.data.vertices[vi] for vi in geo['cverts']]

                if geo.get('wattres'):
                    del geo['wattres']
                
                pend, passarea = pstart + lenpoints, 0
                vi_func.selobj(scene, geo)
                bpy.ops.mesh.vertex_color_add()
                geo.data.vertex_colors[-1].name = str(frame)
                vertexColour = geo.data.vertex_colors[str(frame)]
                mat = [matslot.material for matslot in geo.material_slots if matslot.material.livi_sense][0]
                mcol_i = len(tuple(set(lcol_i)))

                for face in geofaces:
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
                            vertexColour.data[loop_index].color = rgb[fi]
                        fi += 1

                if connode.bl_label == 'LiVi Compliance':
                    if connode.analysismenu == '1':
                        bpy.ops.mesh.vertex_color_add()
                        geo.data.vertex_colors[-1].name = '{}sv'.format(frame)
                        vertexColour = geo.data.vertex_colors['{}sv'.format(frame)]
                        for face in geofaces:
                            if geonode.cpoint == '1':
                                cvtup = tuple(geo['cverts'])
                                for loop_index in face.loop_indices:
                                    v = geo.data.loops[loop_index].vertex_index
                                    if v in cvtup:
                                        col_i = cvtup.index(v)
                                    lcol_i.append(col_i)
                                    vertexColour.data[loop_index].color = rgb[col_i+mcol_i]

                            elif geonode.cpoint == '0':
                                for loop_index in face.loop_indices:
                                    vertexColour.data[loop_index].color = (0, 1, 0) if svres[frame][fsv] > 0 else (1, 0, 0)
                                fsv += 1

                    if fr == 0:
                        comps, ecomps =  [[[] * fra for fra in range(scene.fs, scene.fe + 1)] for x in range(2)]
                        if connode.analysismenu == '0':
                            if connode.bambuildmenu in ('0', '5'):
                                if not mat.gl_roof:
                                    crit = [['Percent', 80, 'DF', 2, '1'], ['Ratio', 100, 'Uni', 0.4, '0.5'], ['Min', 100, 'PDF', 0.8, '0.5'], ['Percent', 80, 'Skyview', 1, '0.75']]
                                    ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 1.2, '0.75']] 
                                else:
                                    crit = [['Percent', 80, 'DF', 2, '1'], ['Ratio', 100, 'Uni', 0.7, '0.5'], ['Min', 100, 'PDF', 1.4, '0.5'], ['Percent', 100, 'Skyview', 1, '0.75']]
                                    ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 2.8, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 2.1, '0.75']]

                            elif connode.bambuildmenu == '1':
                                if not mat.gl_roof:
                                    crit = [['Percent', 80, 'DF', 2, '1'], ['Ratio', 100, 'Uni', 0.4, '0.5'], ['Min', 100, 'PDF', 0.8, '0.5'], ['Percent', 80, 'Skyview', 1, '0.75']]
                                    ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 1.2, '0.75']]
                                else:
                                    crit = [['Percent', 80, 'DF', 2, '1'], ['Ratio', 100, 'Uni', 0.7, '0.5'], ['Min', 100, 'PDF', 1.4, '0.5'], ['Percent', 100, 'Skyview', 1, '0.75']]
                                    ecrit= [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 2.8, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 2.1, '0.75']]

                            elif connode.bambuildmenu == '2':
                                crit = [['Percent', 80, 'DF', 2, '1']] if mat.hspacemenu == '0' else ['Percent', 80, 'DF', 3, '2']
                                ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Min', 100, 'PDF', 1.6, '0.75'], ['Min', 100, 'PDF', 1.2, '0.75']]
               
                            elif connode.bambuildmenu == '3':
                                if mat.rspacemenu == '0':
                                    crit = [['Percent', 80, 'DF', 2, '1'], ['Percent', 100, 'Skyview', 1, '0.75']]
                                    ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 1.2, '0.75']]

                                elif mat.rspacemenu == '1':
                                    crit = [['Percent', 80, 'DF', 1.5, '1'], ['Percent', 100, 'Skyview', 1, '0.75']]
                                    ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 1.2, '0.75']]

                                elif mat.rspacemenu == '2':
                                    if not mat.gl_roof:
                                        crit = [['Percent', 80, 'DF', 2, '1'], ['Ratio', 100, 'Uni', 0.4, '0.5'], ['Min', 100, 'PDF', 0.8, '0.5'], ['Percent', 80, 'Skyview', 1, '0.75']]
                                        ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 1.2, '0.75']]
                                    else:
                                        crit = [['Percent', 80, 'DF', 2, '1'], ['Ratio', 100, 'Uni', 0.7, '0.5'],['Min', 100, 'PDF', 1.4, '0.5'], ['Percent', 100, 'Skyview', 1, '0.75']] 
                                        ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 2.8, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 2.1, '0.75']]

                            elif connode.bambuildmenu == '4':
                                if mat.respacemenu == '0':
                                    crit = [['Percent', 35, 'PDF', 2, '1']]
                                    ecrit = [['Percent', 50, 'PDF', 2, '1']]

                                elif mat.respacemenu == '1':
                                    if not mat.gl_roof:
                                        crit = [['Percent', 80, 'DF', 2, '1'], ['Ratio', 100, 'Uni', 0.4, '0.5'], ['Min', 100, 'PDF', 0.8, '0.5'], ['Percent', 80, 'Skyview', 1, '0.75']] 
                                        ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 1.2, '0.75']]
           
                                    else:
                                        crit = [['Percent', 80, 'DF', 2, '1'], ['Ratio', 100, 'Uni', 0.7, '0.5'], ['Min', 100, 'PDF', 1.4, '0.5'], ['Percent', 100, 'Skyview', 1, '0.75']]
                                        ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 2.8, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'],['Min', 100, 'PDF', 2.1, '0.75']] 

                        elif connode.analysismenu == '1':
                            crit = [['Average', 100, 'DF', 2, '1'], ['Percent', 80, 'Skyview', 1, '0.75']] if mat.rspacemenu == '0' else [['Average', 100, 'DF', 1.5, '1'], ['Percent', 80, 'Skyview', 1, '0.75']]
 
                        elif connode.analysismenu == '2':
                            crit = [['Percent', 75, 'FC', 108, '1'], ['Percent', 75, 'FC', 5400, '1'], ['Percent', 90, 'FC', 108, '1'], ['Percent', 90, 'FC', 5400, '1']]

                    for c in crit:
                        if c[0] == 'Percent':
                            if c[2] == 'DF':
                                dfpass[frame] = 1
                                dfpassarea = dfpassarea + geoarea if sum(res[frame][pstart:pend])/(pend - pstart) > c[3] else dfpassarea
                                comps[frame].append((0, 1)[sum(res[frame][pstart:pend])/(pend - pstart) > c[3]])
                                comps[frame].append(sum(res[frame][pstart:pend])/(pend - pstart))
                                dftotarea += geoarea
                                
                            if c[2] == 'PDF':
                                dfpass[frame] = 1
                                dfpassarea = sum([area for p, area in enumerate(geoareas) if res[frame][p + pstart] > c[3]])
                                comps[frame].append((0, 1)[dfpassarea > c[1]*geoarea/100])
                                comps[frame].append(100*dfpassarea/geoarea)
                                dftotarea += geoarea

                            elif c[2] == 'Skyview':
                                passarea = sum([area for p, area in enumerate(geoareas) if svres[frame][p + pstart] > 0])
                                comps[frame].append((0, 1)[passarea >= c[1]*geoarea/100])
                                comps[frame].append(100*passarea/geoarea)
                                passarea = 0

                        elif c[0] == 'Min':
                            comps[frame].append((0, 1)[min(res[frame][pstart:pend]) > c[3]])
                            comps[frame].append(min(res[frame][pstart:pend]))

                        elif c[0] == 'Ratio':
                            comps[frame].append((0, 1)[min(res[frame][pstart:pend])/(sum(res[frame][pstart:pend])/(pend - pstart)) >= c[3]])
                            comps[frame].append(min(res[frame][pstart:pend])/(sum(res[frame])/(pend - pstart)))

                        elif c[0] == 'Average':
                            comps[frame].append((0, 1)[sum([area * res[frame][p + pstart] for p, area in enumerate(geoareas)])/geoarea > c[3]])
                            comps[frame].append(sum([area * res[frame][p + pstart] for p, area in enumerate(geoareas)])/geoarea)

                    for e in ecrit:
                        if e[0] == 'Percent':
                            if e[2] == 'DF':
                                edfpass[frame] = [1, (0, 1)[sum(res[frame][pstart:pend])/(pend - pstart) > e[3]], sum(res[frame][pstart:pend])/(pend - pstart)]
                                edfpassarea = edfpassarea + geoarea if sum(res[frame][pstart:pend])/(pend - pstart) > e[3] else edfpassarea
                                ecomps[frame].append((0, 1)[sum(res[frame][pstart:pend])/(pend - pstart) > e[3]])
                                ecomps[frame].append(sum(res[frame][pstart:pend])/(pend - pstart))
                                edftotarea += geoarea
                                
                            if e[2] == 'PDF':
                                edfpass[frame] = 1
                                edfpassarea = sum([vi_func.facearea(geo, face) for fa, face in enumerate(geofaces) if res[frame][fa + pstart] > e[3]])      
                                ecomps[frame].append((0, 1)[dfpassarea > e[1]*geoarea/100])
                                ecomps[frame].append(100*edfpassarea/geoarea)
                                edftotarea += geoarea

                            elif e[2] == 'Skyview':
                                passarea = sum([vi_func.facearea(geo, face) for fa, face in enumerate(geofaces) if svres[frame][fa] > 0])
                                ecomps[frame].append((0, 1)[passarea >= e[1] * geoarea/100])
                                ecomps[frame].append(100*passarea/geoarea)
                                passarea = 0

                        elif e[0] == 'Min':
                            ecomps[frame].append((0, 1)[min(res[frame][pstart:pend]) > e[3]])
                            ecomps[frame].append(min(res[frame][pstart:pend]))

                        elif e[0] == 'Ratio':
                            ecomps[frame].append((0, 1)[min(res[frame][pstart:pend])/(sum(res[frame][pstart:pend])/(pend - pstart)) >= e[3]])
                            ecomps[frame].append(min(res[frame][pstart:pend])/(sum(res[frame][pstart:pend])/(pend - pstart)))

                        elif e[0] == 'Average':
                            ecomps[frame].append((0, 1)[sum(res[frame][pstart:pend])/(pend - pstart) > e[3]])
                            ecomps[frame].append(sum(res[frame][pstart:pend])/(pend - pstart))

                    geo['crit'], geo['ecrit'], geo['comps'], geo['ecomps'] = [[c[0], str(c[1]), c[2], str(c[3]), c[4]] for c in crit[:]], [[c[0], str(c[1]), c[2], str(c[3]), c[4]] for c in ecrit[:]], comps, ecomps
                    crits.append(geo['crit'])
                    pstart = pend
    
        if connode.bl_label == 'LiVi Compliance': 
            if dfpass[frame] == 1:
                dfpass[frame] = 2 if dfpassarea/dftotarea >= (0.8, 0.35)[connode.analysismenu == '0' and connode.bambuildtype == '4'] else dfpass[frame]
            if edfpass[frame] == 1:
                edfpass[frame] = 2 if edfpassarea/edftotarea >= (0.8, 0.5)[connode.analysismenu == '0' and connode.bambuildtype == '4'] else edfpass[frame]
            scene['crits'], scene['dfpass'] = crits, dfpass
        simnode.outputs['Data out'].hide = True
    else:
        for fr, frame in enumerate(range(scene.fs, scene.fe + 1)):
            scene.frame_set(frame)
            sof, sov = 0, 0
            for geo in vi_func.retobjs('livic'):
                bpy.ops.object.select_all(action = 'DESELECT')
                eof, eov, hours, scene.objects.active = sof + len(geo['cfaces']), sov + len(geo['cverts']), len(res[0]), None
                geoarea = sum(geo['lisenseareas'])
                geofaces = [face for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense]
                geo['wattres'] = {str(frame):[0 for x in range(len(res[0]))]}
                for i in range(hours):
                    if geonode.cpoint == '0':
                        geo['wattres'][str(frame)][i] = sum([res[fr][i][sof:eof][j] * geo['lisenseareas'][j] for j in range(sof, eof)])
                    else:
                        geo['wattres'][str(frame)][i] = sum([res[fr][i][sov:eov][j] * geo['lisenseareas'][j] for j in range(sov, eov)])
                sov, sof = eov, eof

        simnode.outputs['Data out'].hide = False
            
    calc_op.report({'INFO'}, "Calculation is finished.")
    bpy.ops.wm.save_mainfile(check_existing = False)
