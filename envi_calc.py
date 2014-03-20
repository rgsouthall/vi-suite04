#import bpy, 
import os, glob, bpy, datetime, time
#, subprocess
from subprocess import PIPE, Popen
from os import rename
from os.path import basename
from bpy.props import EnumProperty, IntProperty
from .vi_func import iprop, eprop, processf
from . import vi_node

def envi_sim(calc_op, node, connode):
    node.resfilename = connode.newdir+connode.fold+node.resname+'.eso'
    os.chdir(connode.newdir)
    esimcmd = "EnergyPlus in.idf in.epw" 
    esimrun = Popen(esimcmd, shell = True, stdout = PIPE)
    for line in esimrun.stdout:
        print(line) 
    for fname in os.listdir('.'):
        if fname.split(".")[0] == node.resfilename:
            os.remove(node.newdir+node.fold+fname)
    for fname in os.listdir('.'):
        if fname.split(".")[0] == "eplusout":
            rename(fname, fname.replace("eplusout", node.resfilename.split(".")[0]))
#    scene.envi_sim = True
    processf(calc_op, node)
    node.dsdoy = connode.sdoy # (locnode.startmonthnode.sdoy
    node.dedoy = connode.edoy
    if node.resname+".err" not in [im.name for im in bpy.data.texts]:
        bpy.data.texts.load(connode.newdir+"/"+node.resname+".err")
    calc_op.report({'INFO'}, "Calculation is finished.")  
            
    if node.resname+".err" not in [im.name for im in bpy.data.texts]:
        bpy.data.texts.load(connode.newdir+"/"+node.resname+".err")

#def envi_reslist    