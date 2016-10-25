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

import os, bpy, subprocess
from subprocess import PIPE, Popen
from os import rename
from .vi_func import processf

def envi_sim(calc_op, node, connode):
    scene, err = bpy.context.scene, 0
    os.chdir(scene['viparams']['newdir'])
    expand = "-x" if scene['viparams'].get('hvactemplate') else ""
    eidd = os.path.join(os.path.dirname(os.path.abspath(os.path.realpath( __file__ ))), "EPFiles", "Energy+.idd")    
    
    for frame in range(scene['enparams']['fs'], scene['enparams']['fe'] + 1):
        esimcmd = "EnergyPlus {0} -w in{1}.epw -i {2} -p {3} in{1}.idf".format(expand, frame, eidd, ('{}{}'.format(node.resname, frame), 'eplus{}'.format(frame))[node.resname == '']) 
        esimrun = Popen(esimcmd, shell = True, stdout = PIPE, stderr = PIPE)
        for line in esimrun.stderr:
            if 'EnergyPlus Terminated--Error(s) Detected' in line.decode():
                print(line) 
                calc_op.report({'ERROR'}, "There was an error in the input IDF file. Chect the *.err file in Blender's text editor.")
                err = 1
        with open(os.path.join(scene['viparams']['newdir'], node.resname+".err")) as errfile:
            for line in errfile.readlines():
                if '**  Fatal  **' in line:
                    calc_op.report({'ERROR'}, "There was an error in the input IDF file. Check the *.err file in Blender's text editor. Message")
                    err = 1
                    break
        for fname in os.listdir('.'):
            if fname.split(".")[0] == node.resname:
                os.remove(os.path.join(scene['viparams']['newdir'], fname))
        for fname in os.listdir('.'):
            if fname.split(".")[0] == "eplusout":
                rename(os.path.join(scene['viparams']['newdir'], fname), os.path.join(scene['viparams']['newdir'],fname.replace("eplusout", node.resname)))
        if err:
            return
        processf(calc_op, node)
        
    node.dsdoy = connode.sdoy # (locnode.startmonthnode.sdoy
    node.dedoy = connode.edoy
    
    if node.resname+".err" not in [im.name for im in bpy.data.texts]:
        bpy.data.texts.load(os.path.join(scene['viparams']['newdir'], node.resname+".err"))
    else:
        bpy.data.texts[node.resname+".err"].filepath = os.path.join(scene['viparams']['newdir'], node.resname+".err")

    calc_op.report({'INFO'}, "Calculation is finished.")  
            
   