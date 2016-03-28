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

import bpy, os, datetime
from subprocess import Popen, PIPE
from . import livi_export
from .vi_func import retpmap, selobj, progressbar, progressfile

def radfexport(scene, export_op, connode, geonode, frames):
    for frame in frames:
        livi_export.fexport(scene, frame, export_op, connode, geonode, pause = 1)

def li_calc(calc_op, simnode, simacc, **kwargs): 
    scene = bpy.context.scene
    context = simnode['coptions']['Context']
    subcontext = simnode['coptions']['Type']
    scene['liparams']['maxres'], scene['liparams']['minres'], scene['liparams']['avres'] = {}, {}, {}
    frames = range(scene['liparams']['fs'], scene['liparams']['fe'] + 1) if not kwargs.get('genframe') else [kwargs['genframe']]
    os.chdir(scene['viparams']['newdir'])
    rtcmds, rccmds = [], []
    simnode['resdictnew'] = {}
    progressfile(scene, datetime.datetime.now(), [int(i * 100/20) for i in range(0, 21)], 5, 'clear')
    kivyrun = progressbar(os.path.join(scene['viparams']['newdir'], 'viprogress'))
    
    for f, frame in enumerate(frames):
        simnode['resdictnew'][str(frame)] = {}
        if context == 'Basic' or (context == 'CBDM' and subcontext == '0') or (context == 'Compliance' and int(subcontext) < 3):
#        if context == 'Basic' or (context == 'Compliance' and int(subcontext) < 3):

            if os.path.isfile("{}-{}.af".format(scene['viparams']['filebase'], frame)):
                os.remove("{}-{}.af".format(scene['viparams']['filebase'], frame))
            if simnode.pmap:
                errdict = {'fatal - too many prepasses, no global photons stored\n': "Too many prepasses have ocurred. Make sure light sources can see your geometry",
                'fatal - too many prepasses, no global photons stored, no caustic photons stored\n': "Too many prepasses have ocurred. Turn off caustic photons and encompass the scene",
               'fatal - zero flux from light sources\n': "No light flux, make sure there is a light source and that photon port normals point inwards",
               'fatal - no light sources\n': "No light sources. Photon mapping does not work with HDR skies"}
                amentry, pportentry, cpentry, cpfileentry = retpmap(simnode, frame, scene)
                pmcmd = ('mkpmap -bv+ +fo -apD 0.001 {0} -apg {1}-{2}.gpm {3} {4} {5} {1}-{2}.oct'.format(pportentry, scene['viparams']['filebase'], frame, simnode.pmapgno, cpentry, amentry))                   
                pmrun = Popen(pmcmd.split(), stderr = PIPE)
                for line in pmrun.stderr: 
                    print(line)
                    if line.decode() in errdict:
                        calc_op.report({'ERROR'}, errdict[line.decode()])
                        return 
                rtcmds.append("rtrace -n {0} -w {1} -ap {2}-{3}.gpm 50 {4} -faa -h -ov -I {2}-{3}.oct".format(scene['viparams']['nproc'], simnode['radparams'], scene['viparams']['filebase'], frame, cpfileentry)) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
            else:
#                if context == 'Compliance':
#                    rtcmds.append("rcontrib -w -n {} {} -m sky_glow -I+ -V+ {}-{}.oct ".format(scene['viparams']['nproc'], simnode['radparams'], scene['viparams']['filebase'], frame))    
#
#                else:
                rtcmds.append("rtrace -n {0} -w {1} -faa -h -ov -I {2}-{3}.oct".format(scene['viparams']['nproc'], simnode['radparams'], scene['viparams']['filebase'], frame)) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
        else:
            rccmds.append("rcontrib -w  -h -I -fo -bn 146 {} -n {} -f tregenza.cal -b tbin -m sky_glow {}-{}.oct".format(simnode['radparams'], scene['viparams']['nproc'], scene['viparams']['filebase'], frame))
#            rccmds.append("rcontrib -w  -h -I- -fo -bn 146 {} -n {} -f tregenza.cal -b tbin -m env_glow {}-{}.oct".format(simnode['radparams'], scene['viparams']['nproc'], scene['viparams']['filebase'], frame))

    tpoints = sum([bpy.data.objects[lc]['rtpnum'] for lc in scene['liparams']['livic']])
    calcsteps = tpoints * len(frames)
    starttime = datetime.datetime.now()
    startstep = 0

    for oi, o in enumerate([scene.objects[on] for on in scene['liparams']['livic']]):
        selobj(scene, o)
        o['omax'], o['omin'], o['oave'] = {}, {}, {}
        if context == 'Basic':
            if o.basiccalcapply(scene, frames, rtcmds, simnode, oi, starttime, len(scene['liparams']['livic']), calcsteps, startstep) == 'CANCELLED':
                return 'CANCELLED'
        elif context == 'CBDM' and subcontext == '0':
            if o.lhcalcapply(scene, frames, rtcmds, simnode, oi, starttime, len(scene['liparams']['livic']), calcsteps, startstep) == 'CANCELLED':
                return 'CANCELLED'
        elif (context == 'CBDM' and subcontext in ('1', '2')) or (context == 'Compliance' and subcontext == '3'):
            o.udidacalcapply(scene, frames, rccmds, simnode, starttime, calcsteps)
        elif context == 'Compliance':
            o.compcalcapply(scene, frames, rtcmds, simnode, starttime, calcsteps)   
        startstep += o['rtpnum']
        
    if kivyrun.poll() is None:
        kivyrun.kill()
            

