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

import bpy, os, subprocess, datetime, bmesh
from subprocess import PIPE, Popen, STDOUT
from .vi_func import mtx2vals, retobjs, selobj, facearea
from . import livi_export
import numpy


def radfexport(scene, export_op, connode, geonode, frames):
    for frame in frames:
        livi_export.fexport(scene, frame, export_op, connode, geonode, pause = 1)

def li_calc(calc_op, simnode, connode, geonode, simacc, **kwargs): 
    scene, prange = bpy.context.scene, range(geonode['reslen'])
    frames = range(scene.fs, scene.fe + 1) if not kwargs.get('genframe') else [kwargs['genframe']]
    os.chdir(scene['viparams']['newdir'])
    if os.lstat("{}.rtrace".format(scene['viparams']['filebase'])).st_size == 0:
        calc_op.report({'ERROR'},"There are no materials with the livi sensor option enabled")
    else:
        (res, svres) = (numpy.zeros([len(frames), geonode['reslen']]), numpy.zeros([len(frames), geonode['reslen']]))
        for frame in frames:            
            findex = frame - scene.fs if not kwargs.get('genframe') else 0
            if connode.bl_label in ('LiVi Basic', 'LiVi Compliance') or (connode.bl_label == 'LiVi CBDM' and int(connode.analysismenu) < 2):
                if os.path.isfile("{}-{}.af".format(scene['viparams']['filebase'], frame)):
                    subprocess.call("{} {}-{}.af".format(scene['viparams']['rm'], scene['viparams']['filebase'], frame), shell=True)
                rtcmd = "rtrace -n {0} -w {1} -faa -h -ov -I {2}-{3}.oct  < {2}.rtrace {4}".format(scene['viparams']['nproc'], simnode['radparams'], scene['viparams']['filebase'], frame, connode['simalg']) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                rtrun = Popen(rtcmd, shell = True, stdout=PIPE, stderr=STDOUT)                
                with open(os.path.join(scene['viparams']['newdir'], connode['resname']+"-{}.res".format(frame)), 'w') as resfile:
                    for l, line in enumerate([line.decode() for line in rtrun.stdout]):
                        res[findex][l] = eval(line)                
                        resfile.write(line)
                
            if connode.bl_label == 'LiVi Compliance' and connode.analysismenu in ('0', '1'):
                svcmd = "rtrace -n {0} -w {1} -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(scene['viparams']['nproc'], '-ab 1 -ad 8192 -aa 0 -ar 512 -as 1024 -lw 0.0002', scene['viparams']['filebase'], frame, connode['simalg']) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                svrun = Popen(svcmd, shell = True, stdout=PIPE, stderr=STDOUT)                  
                with open(os.path.join(scene['viparams']['newdir'],'skyview'+"-"+str(frame)+".res"), 'w') as svresfile:
                    for sv,line in enumerate([line.decode() for line in svrun.stdout]):
                        svres[findex][sv] = eval(line)
                        svresfile.write(line)

            if connode.bl_label == 'LiVi CBDM' and int(connode.analysismenu) > 1:
                if connode.sourcemenu == '1':
                    connode['vecvals'], vals = mtx2vals(open(connode.mtxname, "r").readlines(), datetime.datetime(2010, 1, 1).weekday(), '')
                vecvals = numpy.array(connode['vecvals'])
                
                sensarray = numpy.zeros((len(prange), 146))
                oconvcmd = "oconv -w - > {0}-ws.oct".format(scene['viparams']['filebase'])
                Popen(oconvcmd, shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate(input = (connode['whitesky']+geonode['radfiles'][frame]).encode('utf-8'))
                senscmd = scene['viparams']['cat']+scene['viparams']['filebase']+".rtrace | rcontrib -w  -h -I -fo -bn 146 {} -n {} -f tregenza.cal -b tbin -m sky_glow {}-ws.oct".format(simnode['radparams'], scene['viparams']['nproc'], scene['viparams']['filebase'])
                sensrun = Popen(senscmd, shell = True, stdout=PIPE)
                
                for li, line in enumerate(sensrun.stdout):
                    decline = [float(ld) for ld in line.decode().split('\t') if ld not in ('\n', '\r\n')]
                    if connode.analysismenu in ('2', '4'):
                        sensarray[li] = [179*((decline[v]*0.265)+ (decline[v+1]*0.67) + (decline[v+2]*0.065)) for v in range(0, 438, 3)]
                    elif connode.analysismenu == '3':
                        sensarray[li] = [sum(decline[v:v+3]) for v in range(0, 438, 3)]
                if connode.analysismenu in ('2', '4'):
                    vecvals = numpy.array([vv[2:] for vv in vecvals if connode.cbdm_start_hour <= vv[0] < connode.cbdm_end_hour and vv[1] < connode['wd']])
                    hours = len(vecvals)
                elif connode.analysismenu == '3':
                    vecvals = [vv[2:] for vv in vecvals]
                    hours = len(vecvals)

                finalillu = numpy.array([[numpy.sum(sensarray[f] * vv) for vv in vecvals] for f in prange])
                if connode.analysismenu == '2':
                    res[findex] = [numpy.sum([i >= connode.dalux for i in f])*100/hours for f in finalillu]
                elif connode.analysismenu == '3':
                    res[findex] = finalillu
                elif connode.analysismenu == '4':
                    res[findex] = [numpy.sum([connode.daauto >= i >= connode.dasupp for i in f])*100/hours for f in finalillu]

                if connode.analysismenu in ('2', '4'):
                    with open(os.path.join(scene['viparams']['newdir'], connode['resname']+"-"+str(frame)+".res"), "w") as daresfile:
                        [daresfile.write("{:.2f}\n".format(r)) for r in res[findex]]
          
        resapply(calc_op, res, svres, simnode, connode, geonode, frames)
        print(res)
        return(res[0])
   
def resapply(calc_op, res, svres, simnode, connode, geonode, frames):
    scene = bpy.context.scene  
    simnode['maxres'], simnode['minres'] = {}, {}
    if connode.analysismenu != '3' or connode.bl_label != 'LiVi CBDM':
        for i, f in enumerate(frames):
            simnode['maxres'][str(f)] = numpy.amax(res[i])
            simnode['minres'][str(f)] = numpy.amin(res[i])
            simnode['avres'][str(f)] = numpy.average(res[i])
            scene.vi_leg_max = max(simnode['maxres'].values())
            scene.vi_leg_min = min(simnode['minres'].values())
            
        crits = []
        dfpass = [0 for f in frames]
        edfpass = [0 for f in frames]
        
        for fr, frame in enumerate(frames):
            scene.frame_set(frame)
            dftotarea, dfpassarea, edfpassarea, edftotarea, pstart, sof, eof = 0, 0, 0, 0, 0, 0, 0
        
            if bpy.context.active_object and bpy.context.active_object.hide == 'False':
                bpy.ops.object.mode_set()
        
            for o in [o for o in scene.objects if o.name in scene['livic']]:                
                bpy.ops.object.select_all(action = 'DESELECT')
                scene.objects.active = None
                o['liviresults'], oareas = {}, o['lisenseareas']
                oarea = sum(oareas)
                
                if o.get('wattres'):
                    del o['wattres']
                
                selobj(scene, o)
                bm = bmesh.new()
                bm.from_mesh(o.data)
                pend, passarea = pstart + len(o['lisenseareas']), 0
                mat = [matslot.material for matslot in o.material_slots if matslot.material.mattype == '1'][0]

                if geonode.cpoint == '1':
                    cindex = bm.verts.layers.int['cindex']
                    bm.verts.layers.float.new('res{}'.format(frame))
                    livires = bm.verts.layers.float['res{}'.format(frame)]
                    if connode.bl_label == 'LiVi Compliance':
                        bm.verts.layers.float.new('sv{}'.format(frame))
                        sv = bm.verts.layers.float['sv{}'.format(frame)]
                    for v in [v for v in bm.verts if v[cindex] > 0]:
                        v[livires] = res[fr][v[cindex] - 1]
                        if connode.bl_label == 'LiVi Compliance':
                            v[sv] = svres[fr][v[cindex] - 1]
                    o['liviresults']['Sum'] = sum([v[livires] for v in bm.verts if v[cindex] > 0])
    
                elif geonode.cpoint == '0':
                    cindex = bm.faces.layers.int['cindex']
                    bm.faces.layers.float.new('res{}'.format(frame))
                    livires = bm.faces.layers.float['res{}'.format(frame)]
                    if connode.bl_label == 'LiVi Compliance':
                        bm.faces.layers.float.new('sv{}'.format(frame))
                        sv = bm.faces.layers.float['sv{}'.format(frame)]
                    for f in [f for f in bm.faces if f[cindex] > 0]:
                        f[livires] = res[fr][f[cindex] - 1]
                        if connode.bl_label == 'LiVi Compliance':
                            f[sv] = svres[fr][f[cindex] - 1]
                    o['liviresults']['Sum'] = sum([f[livires] for f in bm.faces if f[cindex] > 0])
                bm.to_mesh(o.data)
                bm.free()
                

                if connode.bl_label == 'LiVi Compliance':
                    o['compmat'] = mat.name
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
                                crit = [['Percent', 80, 'DF', 2, '1']] if mat.hspacemenu == '0' else [['Percent', 80, 'DF', 3, '2']]
                                ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Min', 100, 'PDF', 1.6, '0.75'], ['Min', 100, 'PDF', 1.2, '0.75']]
               
                            elif connode.bambuildmenu == '3':
                                if mat.brspacemenu == '0':
                                    crit = [['Percent', 80, 'DF', 2, '1'], ['Percent', 100, 'Skyview', 1, '0.75']]
                                    ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 1.2, '0.75']]

                                elif mat.brspacemenu == '1':
                                    crit = [['Percent', 80, 'DF', 1.5, '1'], ['Percent', 100, 'Skyview', 1, '0.75']]
                                    ecrit = [['Percent', 80, 'DF', 4, '1'], ['Min', 100, 'PDF', 1.6, '0.75']] if connode.buildstorey == '0' else [['Percent', 80, 'DF', 3, '1'], ['Min', 100, 'PDF', 1.2, '0.75']]

                                elif mat.brspacemenu == '2':
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
                            crit = [['Average', 100, 'DF', 2, '1'], ['Percent', 80, 'Skyview', 1, '0.75']] if mat.crspacemenu == '0' else [['Average', 100, 'DF', 1.5, '1'], ['Percent', 80, 'Skyview', 1, '0.75']]
                            ecrit = []
                        elif connode.analysismenu == '2':
                            crit = [['Percent', 75, 'FC', 108, '1'], ['Percent', 75, 'FC', 5400, '1'], ['Percent', 90, 'FC', 108, '1'], ['Percent', 90, 'FC', 5400, '1']]
                            ecrit = []
                    for c in crit:
                        if c[0] == 'Percent':
                            if c[2] == 'DF':
                                dfpass[frame] = 1
                                dfpassarea = dfpassarea + oarea if sum(res[frame][pstart:pend])/(pend - pstart) > c[3] else dfpassarea
                                comps[frame].append((0, 1)[sum(res[frame][pstart:pend])/(pend - pstart) > c[3]])
                                comps[frame].append(sum(res[frame][pstart:pend])/(pend - pstart))
                                dftotarea += oarea
                                
                            if c[2] == 'PDF':
                                dfpass[frame] = 1
                                dfpassarea = sum([area for p, area in enumerate(oareas) if res[frame][p + pstart] > c[3]])
                                comps[frame].append((0, 1)[dfpassarea > c[1]*oarea/100])
                                comps[frame].append(100*dfpassarea/oarea)
                                dftotarea += oarea

                            elif c[2] == 'Skyview':
                                passarea = sum([area for p, area in enumerate(oareas) if svres[frame][p + pstart] > 0])
                                comps[frame].append((0, 1)[passarea >= c[1]*oarea/100])
                                comps[frame].append(100*passarea/oarea)
                                passarea = 0

                        elif c[0] == 'Min':
                            comps[frame].append((0, 1)[min(res[frame][pstart:pend]) > c[3]])
                            comps[frame].append(min(res[frame][pstart:pend]))

                        elif c[0] == 'Ratio':
                            comps[frame].append((0, 1)[min(res[frame][pstart:pend])/(sum(res[frame][pstart:pend])/(pend - pstart)) >= c[3]])
                            comps[frame].append(min(res[frame][pstart:pend])/(sum(res[frame])/(pend - pstart)))

                        elif c[0] == 'Average':
                            comps[frame].append((0, 1)[sum([area * res[frame][p + pstart] for p, area in enumerate(oareas)])/oarea > c[3]])
                            comps[frame].append(sum([area * res[frame][p + pstart] for p, area in enumerate(oareas)])/oarea)

                    for e in ecrit:
                        if e[0] == 'Percent':
                            if e[2] == 'DF':
                                edfpass[frame] = [1, (0, 1)[sum(res[frame][pstart:pend])/(pend - pstart) > e[3]], sum(res[frame][pstart:pend])/(pend - pstart)]
                                edfpassarea = edfpassarea + oarea if sum(res[frame][pstart:pend])/(pend - pstart) > e[3] else edfpassarea
                                ecomps[frame].append((0, 1)[sum(res[frame][pstart:pend])/(pend - pstart) > e[3]])
                                ecomps[frame].append(sum(res[frame][pstart:pend])/(pend - pstart))
                                edftotarea += oarea
                                
                            if e[2] == 'PDF':
                                edfpass[frame] = 1
                                edfpassarea = sum([area for p, area in enumerate(oareas) if res[frame][p + pstart] > e[3]])      
                                ecomps[frame].append((0, 1)[dfpassarea > e[1]*oarea/100])
                                ecomps[frame].append(100*edfpassarea/oarea)
                                edftotarea += oarea

                            elif e[2] == 'Skyview':
                                passarea = sum([area for p, area in enumerate(oareas) if svres[frame][p] > 0])
                                ecomps[frame].append((0, 1)[passarea >= e[1] * oarea/100])
                                ecomps[frame].append(100*passarea/oarea)
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

                    o['crit'], o['ecrit'], o['comps'], o['ecomps'] = [[c[0], str(c[1]), c[2], str(c[3]), c[4]] for c in crit[:]], [[c[0], str(c[1]), c[2], str(c[3]), c[4]] for c in ecrit[:]], comps, ecomps
                    crits.append(o['crit'])
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
            for geo in retobjs('livic'):
                bpy.ops.object.select_all(action = 'DESELECT')
                eof, eov, hours, scene.objects.active = sof + len(geo['cfaces']), sov + len(geo['cverts']), len(res[0]), None
                oarea = sum(geo['lisenseareas'])
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
