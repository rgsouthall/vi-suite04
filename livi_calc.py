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
from .vi_func import mtx2vals, retobjs, selobj
from . import livi_export
import numpy


def radfexport(scene, export_op, connode, geonode, frames):
    for frame in frames:
        livi_export.fexport(scene, frame, export_op, connode, geonode, pause = 1)

def li_calc(calc_op, simnode, simacc, **kwargs): 
    scene = bpy.context.scene
    context = simnode['coptions']['Context']
    subcontext = simnode['coptions']['Type']
    scene['liparams']['maxres'], scene['liparams']['minres'], scene['liparams']['avres'] = {}, {}, {}
#    rtos = [o for o in bpy.data.objects if o.get('rtpoints')]
    for o in [scene.objects[on] for on in scene['liparams']['livic']]:
        o['omax'], o['omin'], o['oave'] = {}, {}, {}
        rtcmds, rccmds = [], []
        frames = range(scene['liparams']['fs'], scene['liparams']['fe'] + 1) if not kwargs.get('genframe') else [kwargs['genframe']]
        os.chdir(scene['viparams']['newdir'])

        for frame in frames:
#            findex = frame - scene['liparams']['fs'] if not kwargs.get('genframe') else 0
            if context in ('Basic', 'Compliance') or (context == 'CBDM' and int(subcontext) < 2):
                if os.path.isfile("{}-{}.af".format(scene['viparams']['filebase'], frame)):
                    os.remove("{}-{}.af".format(scene['viparams']['filebase'], frame))
                if simnode.pmap:
                    pmcmd = ('mkpmap -bv+ +fo -apD 0.001 -apo {0} -apg {1}-{2}.gpm {3} -apc {1}-{2}.cpm {4} -aps {5} {1}-{2}.oct'.format(' '.join([mat.name.replace(" ", "_") for mat in bpy.data.materials if mat.pport]), scene['viparams']['filebase'], frame, simnode.pmapgno, simnode.pmapcno, ' '.join([mat.name.replace(" ", "_") for mat in bpy.data.materials if mat.mattype == '1' and mat.radmatmenu == '7'])))
                    print(pmcmd)                    
                    subprocess.call(pmcmd.split())
                    rtcmds.append("rtrace -n {0} -w {1} -ap {2}-{3}.gpm 50 -faa -h -ov -I {2}-{3}.oct".format(scene['viparams']['nproc'], simnode['radparams'], scene['viparams']['filebase'], frame)) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                else: 
                    rtcmds.append("rtrace -n {0} -w {1} -faa -h -ov -I {2}-{3}.oct".format(scene['viparams']['nproc'], simnode['radparams'], scene['viparams']['filebase'], frame)) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
            else:
                rccmds.append("rcontrib -w  -h -I -fo -bn 146 {} -n {} -f tregenza.cal -b tbin -m sky_glow {}-{}.oct".format(simnode['radparams'], scene['viparams']['nproc'], scene['viparams']['filebase'], frame))
                
        if context == 'Basic':
            o.basiccalcapply(scene, frames, rtcmds)
        elif context == 'CBDM' and int(subcontext) < 2:
            o.lhcalcapply(scene, frames, rtcmds)
        elif context == 'CBDM' and int(subcontext) > 1:
            o.udidacalcapply(scene, frames, rccmds, simnode)
        elif context == 'Compliance':
            o.compcalcapply(scene, frames, rtcmds, simnode)     
            

