import bpy, datetime, mathutils, os, bmesh, shutil
from os import rename
import numpy
from numpy import arange, histogram
import bpy_extras.io_utils as io_utils
from subprocess import Popen, PIPE, call
from collections import OrderedDict
from datetime import datetime as dt
from math import cos, sin, pi, ceil, tan, modf

try:
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    mp = 1
except Exception as e:
    print('Matplotlib problem:', e)    
    mp = 0

from .livi_export import radgexport, cyfc1, createoconv, createradfile, genbsdf
from .livi_calc  import li_calc
from .vi_display import li_display, li_compliance, linumdisplay, spnumdisplay, li3D_legend, viwr_legend, en_air, en_panel
from .envi_export import enpolymatexport, pregeo
from .envi_mat import envi_materials, envi_constructions
from .vi_func import processf, selobj, livisimacc, solarPosition, wr_axes, clearscene, clearfiles, viparams, objmode, nodecolour, cmap, wind_rose, compass, windnum, envizres, envilres
from .vi_func import fvcdwrite, fvbmwrite, fvblbmgen, fvvarwrite, fvsolwrite, fvschwrite, fvtppwrite, fvraswrite, fvshmwrite, fvmqwrite, fvsfewrite, fvobjwrite, sunposenvi, recalculate_text, clearlayers
from .vi_func import retobjs, rettree, retpmap, progressbar, spathrange, objoin, progressfile
from .vi_chart import chart_disp
#from .vi_gen import vigen

envi_mats = envi_materials()
envi_cons = envi_constructions()

class NODE_OT_LiGExport(bpy.types.Operator):
    bl_idname = "node.ligexport"
    bl_label = "LiVi geometry export"
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        if viparams(self, scene):
            return {'CANCELLED'}
        scene['viparams']['vidisp'] = ''
        objmode()
        clearfiles(scene['liparams']['objfilebase'])
        clearfiles(scene['liparams']['lightfilebase'])
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        node.preexport(scene)
        radgexport(self, node)
        node.postexport(scene)
        return {'FINISHED'}
        
class MATERIAL_GenBSDF(bpy.types.Operator):
    bl_idname = "material.gen_bsdf"
    bl_label = "Gen BSDF"
    bl_description = "Generate a BSDF for the current selected object"
    bl_register = True
    bl_undo = True
    
    def execute(self, context):
        o = context.active_object
        genbsdf(context.scene, self, o)
        return {'FINISHED'}
        
class MATERIAL_LoadBSDF(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "material.load_bsdf"
    bl_label = "Select BSDF file"
    filename_ext = ".XML;.xml;"
    filter_glob = bpy.props.StringProperty(default="*.XML;*.xml;", options={'HIDDEN'})
    filepath = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    
    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import BSDF XML file with the file browser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        context.material['bsdf'] = {}
        context.material['bsdf']['xml'] = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
class MATERIAL_DelBSDF(bpy.types.Operator):
    bl_idname = "material.del_bsdf"
    bl_label = "Del BSDF"
    bl_description = "Delete a BSDF for the current selected object"
    bl_register = True
    bl_undo = True
    
    def execute(self, context):
        o = context.active_object
        del o['bsdf']
        return {'FINISHED'}

class NODE_OT_FileSelect(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "node.fileselect"
    bl_label = "Select file"
    filename = ""
    bl_register = True
    bl_undo = True

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import {} file with the file browser".format(self.filename), icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        if self.filepath.split(".")[-1] in self.fextlist:
            if self.nodeprop == 'epwname':
                node.epwname = self.filepath
            elif self.nodeprop == 'hdrname':
                node.hdrname = self.filepath
            elif self.nodeprop == 'skyname':
                node.skyname = self.filepath
            elif self.nodeprop == 'mtxname':
                node.mtxname = self.filepath
            elif self.nodeprop == 'resfilename':
                node.resfilename = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_HdrSelect(NODE_OT_FileSelect):
    bl_idname = "node.hdrselect"
    bl_label = "Select HDR/VEC file"
    bl_description = "Select the HDR sky image or vector file"
    filename_ext = ".HDR;.hdr;"
    filter_glob = bpy.props.StringProperty(default="*.HDR;*.hdr;", options={'HIDDEN'})
    nodeprop = 'hdrname'
    filepath = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    fextlist = ("HDR", "hdr")
    nodeid = bpy.props.StringProperty()

class NODE_OT_SkySelect(NODE_OT_FileSelect):
    bl_idname = "node.skyselect"
    bl_label = "Select RAD file"
    bl_description = "Select the Radiance sky file"
    filename_ext = ".rad;.RAD;"
    filter_glob = bpy.props.StringProperty(default="*.RAD;*.rad;", options={'HIDDEN'})
    nodeprop = 'skyname'
    filepath = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    fextlist = ("RAD", "rad")
    nodeid = bpy.props.StringProperty()

class NODE_OT_MtxSelect(NODE_OT_FileSelect):
    bl_idname = "node.mtxselect"
    bl_label = "Select MTX file"
    bl_description = "Select the matrix file"
    filename_ext = ".MTX;.mtx;"
    filter_glob = bpy.props.StringProperty(default="*.MTX;*.mtx;", options={'HIDDEN'})
    nodeprop = 'mtxname'
    filepath = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    fextlist = ("MTX", "mtx")
    nodeid = bpy.props.StringProperty()

class NODE_OT_EpwSelect(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "node.epwselect"
    bl_label = "Select EPW file"
    bl_description = "Select the EnergyPlus weather file"
    filename_ext = ".HDR;.hdr;.epw;.EPW;"
    filter_glob = bpy.props.StringProperty(default="*.HDR;*.hdr;*.epw;*.EPW;", options={'HIDDEN'})
    nodeprop = 'epwname'
    filepath = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    fextlist = ("epw", "EPW", "HDR", "hdr")
    nodeid = bpy.props.StringProperty()

class NODE_OT_LiExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.liexport"
    bl_label = "LiVi context export"
    bl_description = "Export the scene to the Radiance file format"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        if viparams(self, scene):
            return {'CANCELLED'}
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        scene['viparams']['vidisp'] = ''
              
        if bpy.data.filepath:
            objmode()
            node.preexport()
            node.export(scene, self)
            node.postexport()
            return {'FINISHED'}

class NODE_OT_RadPreview(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.radpreview"
    bl_label = "LiVi preview"
    bl_description = "Prevew the scene with Radiance"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        if viparams(self, scene):
            return {'CANCELLED'}
        objmode()
        simnode, frame = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]], scene.frame_current
        simnode.preexport()
        scene['liparams']['fs'] = min([c['fs'] for c in (simnode['goptions'], simnode['coptions'])])
        scene['liparams']['fe'] = max([c['fe'] for c in (simnode['goptions'], simnode['coptions'])])

        if frame not in range(scene['liparams']['fs'], scene['liparams']['fe'] + 1):
            self.report({'ERROR'}, "Current frame is not within the exported frame range")
            return {'CANCELLED'}
    
        createradfile(scene, frame, self, simnode)
        createoconv(scene, frame, self, simnode)
        cam = scene.camera
        
        if cam:
            cang = '180 -vth ' if simnode['coptions']['Context'] == 'Basic' and simnode['coptions']['Type'] == '1' else cam.data.angle*180/pi
            vv = 180 if simnode['coptions']['Context'] == 'Basic' and simnode['coptions']['Type'] == '1' else cang * scene.render.resolution_y/scene.render.resolution_x
            vd = (0.001, 0, -1*cam.matrix_world[2][2]) if (round(-1*cam.matrix_world[0][2], 3), round(-1*cam.matrix_world[1][2], 3)) == (0.0, 0.0) else [-1*cam.matrix_world[i][2] for i in range(3)]
            if simnode.pmap:
                errdict = {'fatal - too many prepasses, no global photons stored\n': "Too many prepasses have ocurred. Make sure light sources can see your geometry",
                'fatal - too many prepasses, no global photons stored, no caustic photons stored\n': "Too many prepasses have ocurred. Turn off caustic photons and encompass the scene",
               'fatal - zero flux from light sources\n': "No light flux, make sure there is a light source and that photon port normals point inwards",
               'fatal - no light sources\n': "No light sources. Photon mapping does not work with HDR skies"}
                amentry, pportentry, cpentry, cpfileentry = retpmap(simnode, frame, scene)
                pmcmd = 'mkpmap -fo+ -bv+ -apD 0.001 {0} -apg {1}-{2}.gpm {3} {4} {5} {1}-{2}.oct'.format(pportentry, scene['viparams']['filebase'], frame, simnode.pmapgno, cpentry, amentry)
                pmrun = Popen(pmcmd.split(), stderr = PIPE)
                for line in pmrun.stderr: 
                    if line.decode() in errdict:
                        self.report({'ERROR'}, errdict[line.decode()])
                        return {'CANCELLED'}
                
                rvucmd = "rvu -w -ap {8} 50 {9} -n {0} -vv {1:.3f} -vh {2} -vd {3[0]:.3f} {3[1]:.3f} {3[2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct".format(scene['viparams']['wnproc'], vv, cang, vd, cam.location, simnode['radparams'], scene['viparams']['filebase'], scene.frame_current, '{}-{}.gpm'.format(scene['viparams']['filebase'], frame), cpfileentry)
            else:
                rvucmd = "rvu -w -n {0} -vv {1} -vh {2} -vd {3[0]:.3f} {3[1]:.3f} {3[2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct".format(scene['viparams']['wnproc'], vv, cang, vd, cam.location, simnode['radparams'], scene['viparams']['filebase'], scene.frame_current)

            rvurun = Popen(rvucmd.split(), stdout = PIPE, stderr = PIPE)
            for line in rvurun.stderr:
                if 'view up parallel to view direction' in line.decode():
                    self.report({'ERROR'}, "Camera cannot point directly upwards")
                    return {'CANCELLED'}
                elif 'X11' in line.decode():
                    self.report({'ERROR'}, "No X11 display server found. You may need to install XQuartz")
                    return {'CANCELLED'}
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "There is no camera in the scene. Radiance preview will not work")
            return {'CANCELLED'}

class NODE_OT_LiViCalc(bpy.types.Operator):
    bl_idname = "node.livicalc"
    bl_label = "LiVi simulation"
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        if viparams(self, scene):
            return {'CANCELLED'}
                    
        objmode()
        clearscene(scene, self)
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        simnode.preexport()
        contextdict = {'Basic': 'LiVi Basic', 'Compliance': 'LiVi Compliance', 'CBDM': 'LiVi CBDM'}        
        
        # Set scene parameters
        scene['viparams']['visimcontext'] = contextdict[simnode['coptions']['Context']]
        scene['liparams']['fs'] = min((simnode['coptions']['fs'], simnode['goptions']['fs'])) 
        scene['liparams']['fe'] = max((simnode['coptions']['fe'], simnode['goptions']['fe'])) 
        scene['liparams']['cp'] = simnode['goptions']['cp']
        scene['liparams']['unit'] = simnode['coptions']['unit']
        scene['liparams']['type'] = simnode['coptions']['Type']
        scene.frame_start, scene.frame_end = scene['liparams']['fs'], scene['liparams']['fe']

        for frame in range(scene['liparams']['fs'], scene['liparams']['fe'] + 1):
            createradfile(scene, frame, self, simnode)
            createoconv(scene, frame, self, simnode)

        if li_calc(self, simnode, livisimacc(simnode)) == 'CANCELLED':
            return {'CANCELLED'}
        if simnode['coptions']['Context'] != 'CBDM' and simnode['coptions']['Context'] != '3':
            scene.vi_display = 1

        scene['viparams']['vidisp'] = 'li'
        scene['viparams']['resnode'] = simnode.name
        scene['viparams']['restree'] = self.nodeid.split('@')[1]
        simnode.postexport()
        self.report({'INFO'},"Simulation is finished")
        return {'FINISHED'}
        
class NODE_OT_LiVIGlare(bpy.types.Operator):
    bl_idname = "node.liviglare"
    bl_label = "LiVi glare"
    bl_description = "Create a glare fisheye image from the Blender camera perspective"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self.egrun.poll() is not None:
                if self.frame > self.frameold:
                    self.frameold = self.frame
                    if self.simnode.pmap:
                        amentry, pportentry, cpentry, cpfileentry = retpmap(self.simnode, self.frame, self.scene)
                        pmcmd = ('mkpmap -bv+ +fo -apD 0.001 {0} -apg {1}-{2}.gpm {3} {4} {5} {1}-{2}.oct'.format(pportentry, self.scene['viparams']['filebase'], self.frame, self.simnode.pmapgno, cpentry, amentry))                   
                        pmrun = Popen(pmcmd.split(), stderr = PIPE)
                        for line in pmrun.stderr: 
                            print(line)
                            if line.decode() in self.errdict:
                                self.report({'ERROR'}, self.errdict[line.decode()])
                                return 
                        rpictcmd = "rpict -w -vth -vh 180 -vv 180 -x 800 -y 800 -vd {0[0][2]:.3f} {0[1][2]} {0[2][2]} -vp {1[0]} {1[1]} {1[2]} {2} -ap {5} 50 {6} {3}-{4}.oct".format(-1*self.cam.matrix_world, self.cam.location, self.simnode['radparams'], self.scene['viparams']['filebase'], self.frame, '{}-{}.gpm'.format(self.scene['viparams']['filebase'], self.frame), cpfileentry)
                    else:
                        rpictcmd = "rpict -w -vth -vh 180 -vv 180 -x 800 -y 800 -vd {0[0][2]} {0[1][2]} {0[2][2]} -vp {1[0]} {1[1]} {1[2]} {2} {3}-{4}.oct".format(-1*self.cam.matrix_world, self.cam.location, self.simnode['radparams'], self.scene['viparams']['filebase'], self.frame)
                    self.rprun = Popen(rpictcmd.split(), stdout = PIPE)                    
                    self.egcmd = 'evalglare -c {}'.format(os.path.join(self.scene['viparams']['newdir'], 'glare{}.hdr'.format(self.frame)))                    
                    self.egrun = Popen(self.egcmd.split(), stdin = self.rprun.stdout, stdout = PIPE)
                    return {'RUNNING_MODAL'}

                time = datetime.datetime(2014, 1, 1, self.simnode['coptions']['shour'], 0) + datetime.timedelta(self.simnode['coptions']['sdoy'] - 1) if self.simnode['coptions']['anim'] == '0' else \
                    datetime.datetime(2014, 1, 1, int(self.simnode['coptions']['shour']), int(60*(self.simnode['coptions']['shour'] - int(self.simnode['coptions']['shour'])))) + datetime.timedelta(self.simnode['coptions']['sdoy'] - 1) + datetime.timedelta(hours = int(self.simnode['coptions']['interval']*(self.frame-self.scene['liparams']['fs'])), seconds = int(60*(self.simnode['coptions']['interval']*(self.frame-self.scene['liparams']['fs']) - int(self.simnode['coptions']['interval']*(self.frame-self.scene['liparams']['fs'])))))
                with open(self.scene['viparams']['filebase']+".glare", "w") as glaretf:
                    for line in self.egrun.stdout:
                        if line.decode().split(",")[0] == 'dgp':
                            glaretext = line.decode().replace(',', ' ').replace("#INF", "").split(' ')
                            glaretf.write("{0:0>2d}/{1:0>2d} {2:0>2d}:{3:0>2d}\ndgp: {4:.2f}\ndgi: {5:.2f}\nugr: {6:.2f}\nvcp: {7:.2f}\ncgi: {8:.2f}\nLv: {9:.0f}\n".format(time.day, time.month, time.hour, time.minute, *[float(x) for x in glaretext[6:12]]))
                pcondcmd = "pcond -u 300 {0}.hdr".format(os.path.join(self.scene['viparams']['newdir'], 'glare'+str(self.frame)))
                with open('{}.temphdr'.format(os.path.join(self.scene['viparams']['newdir'], 'glare'+str(self.frame))), 'w') as temphdr:
                    Popen(pcondcmd.split(), stdout = temphdr).communicate()
                catcmd = "{0} {1}.glare".format(self.scene['viparams']['cat'], self.scene['viparams']['filebase'])
                catrun = Popen(catcmd, stdout = PIPE, shell = True)
                psigncmd = "psign -h 32 -cb 0 0 0 -cf 40 40 40"
                psignrun = Popen(psigncmd.split(), stdin = catrun.stdout, stdout = PIPE)
                pcompcmd = "pcompos {0}.temphdr 0 0 - 800 550".format(os.path.join(self.scene['viparams']['newdir'], 'glare'+str(self.frame)))
                with open("{}.hdr".format(os.path.join(self.scene['viparams']['newdir'], 'glare'+str(self.frame))), 'w') as ghdr:
                    Popen(pcompcmd.split(), stdin = psignrun.stdout, stdout = ghdr).communicate()
                os.remove(os.path.join(self.scene['viparams']['newdir'], 'glare{}.temphdr'.format(self.frame)))

                if  'glare{}.hdr'.format(self.frame) in bpy.data.images:
                    bpy.data.images['glare{}.hdr'.format(self.frame)].reload()
                else:
                    bpy.data.images.load(os.path.join(self.scene['viparams']['newdir'], 'glare{}.hdr'.format(self.frame)))

                self.frame += 1
                if self.frame > self.scene['liparams']['fe']:
                    nodecolour(self.simnode, 0)
                    self.simnode.run = 0
                    self.simnode.postexport()
                    return {'FINISHED'}
                else:
                    return {'RUNNING_MODAL'}
            else:
                nodecolour(self.simnode, 1)
                self.simnode.run += 1
                return {'PASS_THROUGH'}
        else:
            return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(1, context.window)
        wm.modal_handler_add(self)
        self.scene = bpy.context.scene
        self.cam = self.scene.camera
        if self.cam:
            self.simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
            self.simnode.preexport()
            nodecolour(self.simnode, 1)
            self.simnode.run = 1
            self.scene['liparams']['fs'] = min([c['fs'] for c in (self.simnode['goptions'], self.simnode['coptions'])])
            self.scene['liparams']['fe'] = max([c['fe'] for c in (self.simnode['goptions'], self.simnode['coptions'])])
            self.frame = self.scene['liparams']['fs']
            self.frameold = self.frame
            for frame in range(self.scene['liparams']['fs'], self.scene['liparams']['fe'] + 1):
                createradfile(self.scene, frame, self, self.simnode)
                createoconv(self.scene, frame, self, self.simnode)
            if self.simnode.pmap:
                self.errdict = {'fatal - too many prepasses, no global photons stored\n': "Too many prepasses have ocurred. Make sure light sources can see your geometry",
                'fatal - too many prepasses, no global photons stored, no caustic photons stored\n': "Too many prepasses have ocurred. Turn off caustic photons and encompass the scene",
               'fatal - zero flux from light sources\n': "No light flux, make sure there is a light source and that photon port normals point inwards",
               'fatal - no light sources\n': "No light sources. Photon mapping does not work with HDR skies"}
                amentry, pportentry, cpentry, cpfileentry = retpmap(self.simnode, self.frame, self.scene)
                pmcmd = ('mkpmap -bv+ +fo -apD 0.001 {0} -apg {1}-{2}.gpm {3} {4} {5} {1}-{2}.oct'.format(pportentry, self.scene['viparams']['filebase'], self.frame, self.simnode.pmapgno, cpentry, amentry))                   
                pmrun = Popen(pmcmd.split(), stderr = PIPE)
                for line in pmrun.stderr: 
                    print(line)
                    if line.decode() in self.errdict:
                        self.report({'ERROR'}, self.errdict[line.decode()])
                        return 
                rpictcmd = "rpict -w -vth -vh 180 -vv 180 -x 800 -y 800 -vd {0[0][2]:.3f} {0[1][2]} {0[2][2]} -vp {1[0]} {1[1]} {1[2]} {2} -ap {5} 50 {6} {3}-{4}.oct".format(-1*self.cam.matrix_world, self.cam.location, self.simnode['radparams'], self.scene['viparams']['filebase'], self.frame, '{}-{}.gpm'.format(self.scene['viparams']['filebase'], self.frame), cpfileentry)
            else:
                rpictcmd = "rpict -w -vth -vh 180 -vv 180 -x 800 -y 800 -vd {0[0][2]:.3f} {0[1][2]} {0[2][2]} -vp {1[0]} {1[1]} {1[2]} {2} {3}-{4}.oct".format(-1*self.cam.matrix_world, self.cam.location, self.simnode['radparams'], self.scene['viparams']['filebase'], self.frame)
            self.rprun = Popen(rpictcmd.split(), stdout=PIPE)
            egcmd = "evalglare -c {}".format(os.path.join(self.scene['viparams']['newdir'], 'glare{}.hdr'.format(self.frame)))
            self.egrun = Popen(egcmd.split(), stdin = self.rprun.stdout, stdout=PIPE)
            return {'RUNNING_MODAL'}
        else:
            self.report({'ERROR'}, "There is no camera in the scene. Create one for glare analysis")
            return {'FINISHED'}

class VIEW3D_OT_LiDisplay(bpy.types.Operator):
    bl_idname = "view3d.lidisplay"
    bl_label = "LiVi display"
    bl_description = "Display the results on the sensor surfaces"
    bl_register = True
    bl_undo = True
    _handle = None
    disp =  bpy.props.IntProperty(default = 1)

    def modal(self, context, event):
        scene = context.scene
        if context.region:
            height = context.region.height
            if event.mouse_region_x in range(100) and event.mouse_region_y in range(height - 100, height):
                if event.type == 'WHEELUPMOUSE':
                    scene.vi_leg_max += scene.vi_leg_max * 0.05
                    return {'RUNNING_MODAL'}
                if event.type == 'WHEELDOWNMOUSE':
                    scene.vi_leg_max -= (scene.vi_leg_max - scene.vi_leg_min) * 0.05
                    return {'RUNNING_MODAL'}
            elif event.mouse_region_x in range(100) and event.mouse_region_y in range(height - 520, height - 420):
                if event.type == 'WHEELUPMOUSE':
                    scene.vi_leg_min += (scene.vi_leg_max - scene.vi_leg_min) * 0.05
                    return {'RUNNING_MODAL'}
                if event.type == 'WHEELDOWNMOUSE':
                    scene.vi_leg_min -= scene.vi_leg_min * 0.05
                    return {'RUNNING_MODAL'}

        if scene['viparams']['vidisp'] not in ('lipanel', 'sspanel', 'lcpanel') or not scene.vi_display or self.disp != scene['liparams']['disp_count']:              
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_leg, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_pointres, 'WINDOW')
            if scene['liparams']['type'] == 'LiVi Compliance':
                try:
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle_comp, 'WINDOW')
                except:
                    pass
                scene.li_compliance = 0

            if scene['viparams']['vidisp'] not in ('lipanel', 'sspanel', 'lcpanel') or not scene.vi_display: 
                 scene['viparams']['vidisp'] = scene['viparams']['vidisp'][0:2]
                 [scene.objects.unlink(o) for o in scene.objects if o.lires]

            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        dispdict = {'LiVi Compliance': 'lcpanel', 'LiVi Basic': 'lipanel', 'LiVi CBDM': 'lipanel', 'Shadow': 'sspanel'}
        scene = context.scene
        scene['liparams']['disp_count'] = scene['liparams']['disp_count'] + 1 if scene['liparams']['disp_count'] < 10 else 0 
        self.disp = scene['liparams']['disp_count']
        clearscene(scene, self)
        self.simnode = bpy.data.node_groups[scene['viparams']['restree']].nodes[scene['viparams']['resnode']]
        scene['viparams']['vidisp'] = dispdict[scene['viparams']['visimcontext']]
        li_display(self.simnode)
        scene.vi_disp_wire, scene.vi_display = 1, 1
        self._handle_pointres = bpy.types.SpaceView3D.draw_handler_add(linumdisplay, (self, context, self.simnode), 'WINDOW', 'POST_PIXEL')
        self._handle_leg = bpy.types.SpaceView3D.draw_handler_add(li3D_legend, (self, context, self.simnode), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        if scene['viparams']['visimcontext'] == 'LiVi Compliance':
            self._handle_comp = bpy.types.SpaceView3D.draw_handler_add(li_compliance, (self, context, self.simnode), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}

class IES_Select(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "livi.ies_select"
    bl_label = "Select IES file"
    bl_description = "Select the lamp IES file"
    filename = ""
    filename_ext = ".ies; .IES"
    filter_glob = bpy.props.StringProperty(default="*.ies; *.IES", options={'HIDDEN'})
    bl_register = True
    bl_undo = True

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Open an IES File with the file browser", icon='WORLD_DATA')

    def execute(self, context):
        lamp = bpy.context.active_object
        if " " not in self.filepath:
            lamp['ies_name'] = self.filepath
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "There is a space either in the IES filename or directory location. Rename or move the file.")
            return {'CANCELLED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_ESOSelect(NODE_OT_FileSelect):
    bl_idname = "node.esoselect"
    bl_label = "Select EnVi results file"
    bl_description = "Select the EnVi results file to process"
    filename_ext = ".eso"
    filter_glob = bpy.props.StringProperty(default="*.eso", options={'HIDDEN'})
    nodeprop = 'resfilename'
    filepath = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    fextlist = ("eso")
    nodeid = bpy.props.StringProperty()

class NODE_OT_IDFSelect(NODE_OT_FileSelect):
    bl_idname = "node.idfselect"
    bl_label = "Select EnergyPlus input file"
    bl_description = "Select the EnVi input file to process"
    filename_ext = ".idf"
    filter_glob = bpy.props.StringProperty(default="*.idf", options={'HIDDEN'})
    nodeprop = 'idffilename'
    filepath = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    fextlist = ("idf")
    nodeid = bpy.props.StringProperty()

class NODE_OT_ASCImport(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "node.ascimport"
    bl_label = "Select ESRI Grid file"
    bl_description = "Select the ESRI Grid file to process"
    filename = ""
    filename_ext = ".asc"
    filter_glob = bpy.props.StringProperty(default="*.asc", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Open an asc file with the file browser", icon='WORLD_DATA')

    def execute(self, context):
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        startxs, startys, vpos, faces, vlen = [], [], [], [], 0
        ascfiles = [self.filepath] if node.single else [os.path.join(os.path.dirname(os.path.realpath(self.filepath)), file) for file in os.listdir(os.path.dirname(os.path.realpath(self.filepath))) if file.endswith('.asc')]

        for file in ascfiles:
            with open(file, 'r') as ascfile:
                lines = ascfile.readlines()
                [startx, starty] = [eval(lines[i].split()[1]) for i in (2, 3)]
                startxs.append(startx)
                startys.append(starty)
        minstartx,  minstarty = min(startxs), min(startys)

        bpy.context.user_preferences.edit.use_global_undo = False
        for file in ascfiles:
            with open(file, 'r') as ascfile:
                lines = ascfile.readlines()
                (vpos, faces) = [[], []] if node.splitmesh else [vpos, faces]
                xy = [eval(lines[i].split()[1]) for i in (2, 3)]
                [ostartx, ostarty] = xy
                [mstartx, mstarty] = [0, 0] if node.splitmesh else xy
                [cols, rows, size, nodat] = [eval(lines[i].split()[1]) for i in (0, 1, 4, 5)]
                vpos += [(mstartx + (size * ci), mstarty + (size * (rows - ri)), (float(h), 0)[h == nodat]) for ri, height in enumerate([line.split() for line in lines[6:]]) for ci, h in enumerate(height)]
                faces += [(i+1, i, i+rows, i+rows + 1) for i in range((vlen, 0)[node.splitmesh], len(vpos)-cols) if (i+1)%cols]
                vlen += cols*rows

                if node.splitmesh or file == ascfiles[-1]:
                    (basename, vpos) = (file.split(os.sep)[-1].split('.')[0], vpos) if node.splitmesh else ('Terrain', [(v[0] - minstartx, v[1] - minstarty, v[2]) for v in vpos])
                    me = bpy.data.meshes.new("{} mesh".format(basename))
                    bm = bmesh.new()
                    [bm.verts.new(vco) for vco in vpos]
                    bm.verts.ensure_lookup_table()
                    [bm.faces.new([bm.verts[fv] for fv in face]) for face in faces]
                    bm.to_mesh(me)
                    ob = bpy.data.objects.new(basename, me)
                    ob.location = (ostartx - minstartx, ostarty - minstarty, 0) if node.splitmesh else (0, 0, 0)   # position object at 3d-cursor
                    bpy.context.scene.objects.link(ob)
                    bm.free()
        bpy.context.user_preferences.edit.use_global_undo = True
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_CSVExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.csvexport"
    bl_label = "Export a CSV file"
    bl_description = "Select the CSV file to export"
    filename = "results"
    filename_ext = ".csv"
    filter_glob = bpy.props.StringProperty(default="*.csv", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Specify the CSV export file with the file browser", icon='WORLD_DATA')

    def execute(self, context):
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        resstring = ''
        resnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].inputs['Results in'].links[0].from_node
        rl = resnode['reslists']
        rzl = list(zip(*rl))
        if node.animated:
            resstring = ''.join(['{} {},'.format(r[2], r[3]) for r in rl if r[0] == 'All']) + '\n'
            metriclist = list(zip(*[r.split() for ri, r in enumerate(rzl[4]) if rzl[0][ri] == 'All']))
        else:
            resstring = ''.join(['{} {} {},'.format(r[0], r[2], r[3]) for r in rl if r[0] != 'All']) + '\n'
            metriclist = list(zip(*[r.split() for ri, r in enumerate(rzl[4]) if rzl[0][ri] != 'All']))

        for ml in metriclist:
            resstring += ''.join(['{},'.format(m) for m in ml]) + '\n'

        resstring += '\n'
        with open(self.filepath, 'w') as csvfile:
            csvfile.write(resstring)
        return {'FINISHED'}

    def invoke(self,context,event):
        if self.filepath.split('.')[-1] not in ('csv', 'CSV'):
            self.filepath = os.path.join(context.scene['viparams']['newdir'], context.scene['viparams']['filebase'] + '.csv')            
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_TextUpdate(bpy.types.Operator):
    bl_idname = "node.textupdate"
    bl_label = "Update a text file"
    bl_description = "Update a text file"

    nodeid = bpy.props.StringProperty()

    def execute(self, context):
        tenode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        tenode.textupdate(tenode['bt'])
        return {'FINISHED'}

class NODE_OT_TextExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.textexport"
    bl_label = "Export a text file"
    bl_description = "Select the text file to export"
    filename = ""
    filename_ext = ".txt"
    filter_glob = bpy.props.StringProperty(default="*.txt", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Specify the Text export file with the file browser", icon='WORLD_DATA')

    def execute(self, context):
        hostnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        textsocket = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].inputs['Text in'].links[0].from_socket
        resstring = '\n'.join(textsocket['Text'])
        with open(self.filepath, 'w') as textfile:
            textfile.write(resstring)
        if hostnode.etoggle:
            if self.filepath not in [im.filepath for im in bpy.data.texts]:
                bpy.data.texts.load(self.filepath)

            imname = [im.name for im in bpy.data.texts if im.filepath == self.filepath][0]
            text = bpy.data.texts[imname]
            for area in bpy.context.screen.areas:
                if area.type == 'TEXT_EDITOR':
                    area.spaces.active.text = text
                    ctx = bpy.context.copy()
                    ctx['edit_text'] = text
                    ctx['area'] = area
                    ctx['region'] = area.regions[-1]
                    bpy.ops.text.resolve_conflict(ctx, resolution = 'RELOAD')

        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_EnGExport(bpy.types.Operator):
    bl_idname = "node.engexport"
    bl_label = "VI-Suite export"
    bl_context = "scene"
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        if viparams(self, scene):
            return {'CANCELLED'}
        scene['viparams']['vidisp'] = ''
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        node.preexport(scene)
        pregeo(self)
        node.postexport()
        return {'FINISHED'}

class NODE_OT_EnExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.enexport"
    bl_label = "Export"
    bl_description = "Export the scene to the EnergyPlus file format"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        if viparams(self, scene):
            return {'CANCELLED'}
        scene['viparams']['vidisp'] = ''
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        node.sdoy = datetime.datetime(datetime.datetime.now().year, node.startmonth, 1).timetuple().tm_yday
        node.edoy = (datetime.date(datetime.datetime.now().year, node.endmonth + (1, -11)[node.endmonth == 12], 1) - datetime.timedelta(days = 1)).timetuple().tm_yday
        (scene['enparams']['fs'], scene['enparams']['fe']) = (node.fs, node.fe) if node.animated else (scene.frame_current, scene.frame_current)
        locnode = node.inputs['Location in'].links[0].from_node
        node.preexport(scene)
        
        for frame in range(node.fs, node.fe + 1):
#            scene.frame_set(frame)
            shutil.copyfile(locnode.weather, os.path.join(scene['viparams']['newdir'], "in{}.epw".format(frame)))

        shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(os.path.realpath( __file__ ))), "EPFiles", "Energy+.idd"), os.path.join(scene['viparams']['newdir'], "Energy+.idd"))

        if bpy.context.active_object and not bpy.context.active_object.hide:
            if bpy.context.active_object.type == 'MESH':
                bpy.ops.object.mode_set(mode = 'OBJECT')

        enpolymatexport(self, node, locnode, envi_mats, envi_cons)
        node.bl_label = node.bl_label[1:] if node.bl_label[0] == '*' else node.bl_label
        node.exported, node.outputs['Context out'].hide = True, False
        node.postexport()
        return {'FINISHED'}

class NODE_OT_EnSim(bpy.types.Operator):
    bl_idname = "node.ensim"
    bl_label = "Simulate"
    bl_description = "Run EnergyPlus"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def modal(self, context, event):
        if event.type == 'TIMER':
            scene = context.scene
            if self.esimrun.poll() is None:
                nodecolour(self.simnode, 1)
                try:
                    with open(os.path.join(scene['viparams']['newdir'], '{}{}out.eso'.format(self.resname, self.frame)), 'r') as resfile:
                        for resline in [line for line in resfile.readlines()[::-1] if line.split(',')[0] == '2' and len(line.split(',')) == 9]:
                            self.simnode.run = int((100/self.lenframes) * (self.frame - scene['enparams']['fs'])) + int((100/self.lenframes) * int(resline.split(',')[1])/(self.simnode.dedoy - self.simnode.dsdoy))
                            break
                    return {'PASS_THROUGH'}
                except:
                    return {'PASS_THROUGH'}
            elif self.frame < scene['enparams']['fe']:
                self.frame += 1
                esimcmd = "energyplus {0} -w in{1}.epw -i {2} -p {3} in{1}.idf".format(self.expand, self.frame, self.eidd, ('{}{}'.format(self.resname, self.frame))) 
                self.esimrun = Popen(esimcmd.split(), stderr = PIPE)
                return {'PASS_THROUGH'}
            else:
                self.simnode.run = -1
                for fname in [fname for fname in os.listdir('.') if fname.split(".")[0] == self.simnode.resname]:
                    os.remove(os.path.join(scene['viparams']['newdir'], fname))

                nfns = [fname for fname in os.listdir('.') if fname.split(".")[0] == "{}{}out".format(self.resname, self.frame)]
                for fname in nfns:
                    rename(os.path.join(scene['viparams']['newdir'], fname), os.path.join(scene['viparams']['newdir'],fname.replace("eplusout", self.simnode.resname)))

                if "{}{}out.err".format(self.resname, self.frame) not in [im.name for im in bpy.data.texts]:
                    bpy.data.texts.load(os.path.join(scene['viparams']['newdir'], "{}{}out.err".format(self.resname, self.frame)))

                if 'EnergyPlus Terminated--Error(s) Detected' in self.esimrun.stderr.read().decode() or not [f for f in nfns if f.split(".")[1] == "eso"] or self.simnode.run == 0:
                    errtext = "There is no results file. Check you have selected results outputs and that there are no errors in the .err file in the Blender text editor." if not [f for f in nfns if f.split(".")[1] == "eso"] else "There was an error in the input IDF file. Check the *.err file in Blender's text editor."
                    self.report({'ERROR'}, errtext)
                    self.simnode.run = -1
                    return {'CANCELLED'}
                else:
                    nodecolour(self.simnode, 0)
                    processf(self, scene, self.simnode)
                    self.report({'INFO'}, "Calculation is finished.")
                    scene['viparams']['resnode'], scene['viparams']['connode'], scene['viparams']['vidisp'] = self.nodeid, '{}@{}'.format(self.connode.name, self.nodeid.split('@')[1]), 'en'
                    self.simnode.run = -1
                    return {'FINISHED'}
        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scene = context.scene
        self.frame = scene['enparams']['fs']
        self.lenframes = len(range(scene['enparams']['fs'], scene['enparams']['fe'] + 1)) 
        if viparams(self, scene):
            return {'CANCELLED'}
        context.scene['viparams']['visimcontext'] = 'EnVi'
        wm = context.window_manager
        self._timer = wm.event_timer_add(1, context.window)
        wm.modal_handler_add(self)
        self.simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        self.simnode.sim(context)
        self.connode = self.simnode.inputs['Context in'].links[0].from_node
        self.simnode.resfilename = os.path.join(scene['viparams']['newdir'], self.simnode.resname+'.eso')
        self.expand = "-x" if scene['viparams'].get('hvactemplate') else ""
        self.eidd = os.path.join(os.path.dirname(os.path.abspath(os.path.realpath( __file__ ))), "EPFiles", "Energy+.idd")  
        self.resname = (self.simnode.resname, 'eplus')[self.simnode.resname == '']
        os.chdir(scene['viparams']['newdir'])
        esimcmd = "energyplus {0} -w in{1}.epw -i {2} -p {3} in{1}.idf".format(self.expand, self.frame, self.eidd, ('{}{}'.format(self.resname, self.frame))) 
        self.esimrun = Popen(esimcmd.split(), stderr = PIPE)
        self.simnode.run = 0
        return {'RUNNING_MODAL'}

class VIEW3D_OT_EnDisplay(bpy.types.Operator):
    bl_idname = "view3d.endisplay"
    bl_label = "EnVi display"
    bl_description = "Display the EnVi results"
    bl_register = True
    bl_undo = False
    _handle = None
    disp =  bpy.props.IntProperty(default = 1)

    def modal(self, context, event):
        scene = context.scene
        if scene['viparams']['vidisp'] not in ('en', 'enpanel') or not scene.vi_display:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle_air, 'WINDOW')
            except:
                pass
#            if not scene.vi_display:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_enpanel, 'WINDOW')
            for o in [o for o in scene.objects if o.get('VIType') and o['VIType'] in ('envi_temp', 'envi_hum', 'envi_heat', 'envi_cool', 'envi_co2')]:
                [scene.objects.unlink(oc) for oc in o.children]
                scene.objects.unlink(o)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        scene = context.scene
        scene.en_frame = scene.frame_current
        resnode = bpy.data.node_groups[scene['viparams']['resnode'].split('@')[1]].nodes[scene['viparams']['resnode'].split('@')[0]]
        zrl = list(zip(*resnode['reslists']))
        eresobs = {o.name: o.name.upper() for o in bpy.data.objects if o.name.upper() in zrl[2]}
        resstart, resend = 24 * (resnode['Start'] - 1), 24 * (resnode['End']) - 1
#        scene.frame_start, scene.frame_end = 0, resend - resstart
        scene.frame_start, scene.frame_end = 0, len(zrl[4][0].split()) - 1
        
        if scene.resas_disp:
            suns = [o for o in bpy.data.objects if o.type == 'LAMP' and o.data.type == 'SUN']
            if not suns:
                bpy.ops.object.lamp_add(type='SUN')
                sun = bpy.context.object
            else:
                sun = suns[0]
            
            for mi, metric in enumerate(zrl[3]):
                if metric == 'Direct Solar (W/m^2)':
                    dirsol = [float(ds) for ds in zrl[4][mi].split()[resstart:resend]]
                elif metric == 'Diffuse Solar (W/m^2)':
                    difsol = [float(ds) for ds in zrl[4][mi].split()[resstart:resend]]
                elif metric == 'Month':
                    mdata = [int(m) for m in zrl[4][mi].split()[resstart:resend]]
                elif metric == 'Day':
                    ddata = [int(d) for d in zrl[4][mi].split()[resstart:resend]]
                elif metric == 'Hour':
                    hdata = [int(h) for h in zrl[4][mi].split()[resstart:resend]]

            sunposenvi(scene, sun, dirsol, difsol, mdata, ddata, hdata)

        if scene.resaa_disp:
            for mi, metric in enumerate(zrl[3]):
                if metric == 'Temperature (degC)' and zrl[1][mi] == 'Climate':
                    temp = [float(ds) for ds in zrl[4][mi].split()[24 * resnode['Start']:24 * resnode['End'] + 1]]
                elif metric == 'Wind Speed (m/s)' and zrl[1][mi] == 'Climate':
                    ws = [float(ds) for ds in zrl[4][mi].split()[24 * resnode['Start']:24 * resnode['End'] + 1]]
                elif metric == 'Wind Direction (deg)' and zrl[1][mi] == 'Climate':
                    wd = [float(m) for m in zrl[4][mi].split()[24 * resnode['Start']:24 * resnode['End'] + 1]]
                elif metric == 'Humidity (%)' and zrl[1][mi] == 'Climate':
                    hu = [float(d) for d in zrl[4][mi].split()[24 * resnode['Start']:24 * resnode['End'] + 1]]
            
            self._handle_air = bpy.types.SpaceView3D.draw_handler_add(en_air, (self, context, temp, ws, wd, hu), 'WINDOW', 'POST_PIXEL')

        if scene.reszt_disp:
            envizres(scene, eresobs, resnode, 'Temp')
        if scene.reszh_disp:
            envizres(scene, eresobs, resnode, 'Hum')
        if scene.reszco_disp:
            envizres(scene, eresobs, resnode, 'CO2')
        if scene.reszhw_disp:
            envizres(scene, eresobs, resnode, 'Heat')
        if scene.reszof_disp:
            envilres(scene, resnode)
        if scene.reszlf_disp:
            envilres(scene, resnode)

        scene.frame_set(scene.frame_start)
        bpy.app.handlers.frame_change_pre.clear()
        bpy.app.handlers.frame_change_pre.append(recalculate_text)

        self._handle_enpanel = bpy.types.SpaceView3D.draw_handler_add(en_panel, (self, context, resnode), 'WINDOW', 'POST_PIXEL')
        scene['viparams']['vidisp'] = 'enpanel'
        scene.vi_display = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_Chart(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.chart"
    bl_label = "Chart"
    bl_description = "Create a 2D graph from the results file"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        innodes = list(OrderedDict.fromkeys([inputs.links[0].from_node for inputs in node.inputs if inputs.links]))
        rl = innodes[0]['reslists']
        zrl = list(zip(*rl))
        if node.inputs['X-axis'].framemenu not in zrl[0]:
#        if not len(innodes[0]['reslists'][node.inputs['X-axis'].framemenu]['Time']['Hour']):
            self.report({'ERROR'},"There are no results in the results file. Check the results.err file in Blender's text editor")
            return {'CANCELLED'}
        if not mp:
            self.report({'ERROR'},"Matplotlib cannot be found by the Python installation used by Blender")
            return {'CANCELLED'}

        Sdate = dt.fromordinal(dt(dt.now().year, 1, 1).toordinal() + node['Start'] -1) + datetime.timedelta(hours = node.dsh - 1)
        Edate = dt.fromordinal(dt(dt.now().year, 1, 1).toordinal() + node['End'] -1 ) + datetime.timedelta(hours = node.deh - 1)
        chart_disp(self, plt, node, innodes, Sdate, Edate)
        return {'FINISHED'}

class NODE_OT_FileProcess(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.fileprocess"
    bl_label = "Process"
    bl_description = "Process EnergyPlus results file"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        processf(self, node)
        node.export()
        return {'FINISHED'}

class NODE_OT_SunPath(bpy.types.Operator):
    bl_idname = "node.sunpath"
    bl_label = "Sun Path"
    bl_description = "Create a Sun Path"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        if viparams(self, scene):
            self.report({'ERROR'},"Save the Blender file before continuing")
            return {'CANCELLED'}
        solringnum, sd, numpos = 0, 100, {}
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        node.export()
        scene['viparams']['resnode'], scene['viparams']['restree'] = node.name, self.nodeid.split('@')[1]
        scene['viparams']['vidisp'] = 'sp'
        context.scene['viparams']['visimcontext'] = 'SunPath'
        scene.cursor_location = (0.0, 0.0, 0.0)
        matdict = {'SolEquoRings': (1, 0, 0), 'HourRings': (1, 1, 0), 'SPBase': (1, 1, 1), 'Sun': (1, 1, 1), 'PathDash': (1, 1, 1),
                   'SumAng': (1, 0, 0), 'EquAng': (0, 1, 0), 'WinAng': (0, 0, 1)}
        for mat in [mat for mat in matdict if mat not in bpy.data.materials]:
            bpy.data.materials.new(mat)
            bpy.data.materials[mat].diffuse_color = matdict[mat]
            bpy.data.materials[mat].use_shadeless = 1

        suns = [ob for ob in context.scene.objects if ob.type == 'LAMP' and ob.data.type == 'SUN']
        if suns:
            sun = suns[0]
            [scene.objects.unlink(sun) for sun in suns[1:]]
            sun.animation_data_clear()
        else: 
            bpy.ops.object.lamp_add(type = "SUN")
            sun = context.active_object
                  
        sun.data.shadow_soft_size = 0.01            
        sun['VIType'] = 'Sun'
        
        if scene.render.engine == 'CYCLES' and scene.world.get('node_tree') and 'Sky Texture' in [no.bl_label for no in scene.world.node_tree.nodes]:
            scene.world.node_tree.animation_data_clear()

        sun['solhour'], sun['solday'] = scene.solhour, scene.solday

        if "SkyMesh" not in [ob.get('VIType') for ob in context.scene.objects]:
            bpy.data.materials.new('SkyMesh')
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, size=105)
            smesh = context.active_object
            smesh.location, smesh.rotation_euler[0], smesh.cycles_visibility.shadow, smesh.name, smesh['VIType']  = (0,0,0), pi, False, "SkyMesh", "SkyMesh"
            bpy.ops.object.material_slot_add()
            smesh.material_slots[0].material = bpy.data.materials['SkyMesh']
            bpy.ops.object.shade_smooth()
            smesh.hide = True
        else:
            smesh =  [ob for ob in context.scene.objects if ob.get('VIType') and ob['VIType'] == "SkyMesh"][0]

        if "SunMesh" not in [ob.get('VIType') for ob in context.scene.objects]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=12, size=1)
            sunob = context.active_object
            sunob.location, sunob.cycles_visibility.shadow, sunob.name, sunob['VIType'] = (0, 0, 0), 0, "SunMesh", "SunMesh"
        else:
            sunob = [ob for ob in context.scene.objects if ob.get('VIType') == "SunMesh"][0]

        if len(sunob.material_slots) == 0:
             bpy.ops.object.material_slot_add()
             sunob.material_slots[0].material = bpy.data.materials['Sun']

        for ob in context.scene.objects:
            if ob.get('VIType') == "SPathMesh":
                context.scene.objects.unlink(ob)
                ob.name = 'oldspathmesh'

        bpy.ops.object.add(type = "MESH")
        spathob = context.active_object
        spathob.location, spathob.name,  spathob['VIType'], spathmesh = (0, 0, 0), "SPathMesh", "SPathMesh", spathob.data
        sun.parent = spathob
        sunob.parent = sun
        smesh.parent = spathob
        bm = bmesh.new()
        bm.from_mesh(spathmesh)

        for doy in range(0, 365):
            for hour in range(1, 25):
                ([solalt, solazi]) = solarPosition(doy, hour, scene.latitude, scene.longitude)[2:]
                bm.verts.new().co = [-(sd-(sd-(sd*cos(solalt))))*sin(solazi), -(sd-(sd-(sd*cos(solalt))))*cos(solazi), sd*sin(solalt)]
        if hasattr(bm.verts, "ensure_lookup_table"):
            bm.verts.ensure_lookup_table()
        for v in range(24, len(bm.verts)):
            bm.edges.new((bm.verts[v], bm.verts[v - 24]))
        if v in range(8568, 8761):
            bm.edges.new((bm.verts[v], bm.verts[v - 8568]))

        for doy in (79, 172, 355):
            for hour in range(1, 241):
                ([solalt, solazi]) = solarPosition(doy, hour*0.1, scene.latitude, scene.longitude)[2:]
                bm.verts.new().co = [-(sd-(sd-(sd*cos(solalt))))*sin(solazi), -(sd-(sd-(sd*cos(solalt))))*cos(solazi), sd*sin(solalt)]
                if hasattr(bm.verts, "ensure_lookup_table"):
                    bm.verts.ensure_lookup_table()
                if bm.verts[-1].co.z >= 0 and doy in (172, 355) and not hour%10:
                    numpos['{}-{}'.format(doy, int(hour*0.1))] = bm.verts[-1].co[:]
                if hour != 1:
                    bm.edges.new((bm.verts[-2], bm.verts[-1]))
                    solringnum += 1
                if hour == 240:
                    bm.edges.new((bm.verts[-240], bm.verts[-1]))
                    solringnum += 1
        
        bm.to_mesh(spathmesh)
        bm.free()

        bpy.ops.object.convert(target='CURVE')
        spathob.data.bevel_depth, spathob.data.bevel_resolution = 0.15, 6
        bpy.context.object.data.fill_mode = 'FULL'
        bpy.ops.object.convert(target='MESH')
        
        bpy.ops.object.material_slot_add()
        spathob.material_slots[0].material, spathob['numpos'] = bpy.data.materials['HourRings'], numpos
        bpy.ops.object.material_slot_add()
        spathob.material_slots[1].material = bpy.data.materials['PathDash']
        for face in spathob.data.polygons:
            face.material_index = 0 if not int(face.index/16)%2 else 1
                

        for vert in spathob.data.vertices[0:16 * (solringnum + 3)]:
            vert.select = True

        bpy.ops.object.material_slot_add()
        spathob.material_slots[-1].material = bpy.data.materials['SolEquoRings']
        spathob.active_material_index = 2
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.object.material_slot_assign()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(0.0, 0.0, 0.0), plane_no=(0.0, 0.0, 1.0), use_fill=True, clear_inner=True, clear_outer=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        compassos = compass((0,0,0.01), sd, spathob, bpy.data.materials['SPBase'])
        spro = spathrange([bpy.data.materials['SumAng'], bpy.data.materials['EquAng'], bpy.data.materials['WinAng']])
        objoin(compassos + [spro] + [spathob])
#        objoin(txts + [coo] + [wro])
        

        for ob in (spathob, sunob, smesh):
            ob.cycles_visibility.diffuse, ob.cycles_visibility.shadow, ob.cycles_visibility.glossy, ob.cycles_visibility.transmission, ob.cycles_visibility.scatter = [False] * 5
            ob.show_transparent = True

        if cyfc1 not in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.append(cyfc1)
        bpy.ops.view3d.spnumdisplay('INVOKE_DEFAULT')
        return {'FINISHED'}

class VIEW3D_OT_SPNumDisplay(bpy.types.Operator):
    '''Display results legend and stats in the 3D View'''
    bl_idname = "view3d.spnumdisplay"
    bl_label = "Point numbers"
    bl_description = "Display the times and solstices on the sunpath"
    bl_register = True
    bl_undo = True

    def modal(self, context, event):
        scene = context.scene
        if context.area:
            context.area.tag_redraw()
        if scene.vi_display == 0 or scene['viparams']['vidisp'] != 'sp':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_spnum, 'WINDOW')
            [scene.objects.unlink(o) for o in scene.objects if o.get('VIType') and o['VIType'] in ('SunMesh', 'SkyMesh')]
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scene = context.scene
        simnode = bpy.data.node_groups[scene['viparams']['restree']].nodes[scene['viparams']['resnode']]
        self._handle_spnum = bpy.types.SpaceView3D.draw_handler_add(spnumdisplay, (self, context, simnode), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        scene.vi_display = 1
        return {'RUNNING_MODAL'}
        
#class VIEW3D_OT_SPTime(bpy.types.Operator):
#    '''Display results legend and stats in the 3D View'''
#    bl_idname = "view3d.sptimeisplay"
#    bl_label = "Point numbers"
#    bl_description = "Display the current solar time on the sunpath"
#    bl_register = True
#    bl_undo = True
#
#    def modal(self, context, event):
#        scene = context.scene
#        if context.area:
#            context.area.tag_redraw()
#        if scene.vi_display == 0 or scene['viparams']['vidisp'] != 'sp':
#            bpy.types.SpaceView3D.draw_handler_remove(self._handle_sptime, 'WINDOW')
#            [scene.objects.unlink(o) for o in scene.objects if o.get('VIType') and o['VIType'] in ('SunMesh', 'SkyMesh')]
#            return {'CANCELLED'}
#        return {'PASS_THROUGH'}
#
#    def invoke(self, context, event):
#        scene = context.scene
#        simnode = bpy.data.node_groups[scene['viparams']['restree']].nodes[scene['viparams']['resnode']]
#        self._handle_sptime = bpy.types.SpaceView3D.draw_handler_add(sptimedisplay, (self, context, simnode), 'WINDOW', 'POST_PIXEL')
#        context.window_manager.modal_handler_add(self)
#        scene.vi_display = 1
#        return {'RUNNING_MODAL'}

class NODE_OT_WindRose(bpy.types.Operator):
    bl_idname = "node.windrose"
    bl_label = "Wind Rose"
    bl_description = "Create a Wind Rose"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        if viparams(self, scene):
            return {'CANCELLED'}
        if simnode.startmonth > simnode.endmonth:
            self.report({'ERROR'},"Start month is later than end month")
            return {'CANCELLED'}
        if not mp:
            self.report({'ERROR'},"There is something wrong with your matplotlib installation")
            return {'FINISHED'}

        simnode.export()
        locnode = simnode.inputs['Location in'].links[0].from_node
        scene['viparams']['resnode'], scene['viparams']['restree'] = simnode.name, self.nodeid.split('@')[1]
        scene['viparams']['vidisp'], scene.vi_display = 'wr', 1
        context.scene['viparams']['visimcontext'] = 'Wind'
        mon = [int(mo) for mo in locnode['allresdict']['Month']]
        awd = [float(wd) for mi, wd in enumerate(locnode['allresdict']['20']) if simnode.startmonth <= mon[mi] <= simnode.endmonth]
        aws = [float(ws) for mi, ws in enumerate(locnode['allresdict']['21']) if simnode.startmonth <= mon[mi] <= simnode.endmonth]
        taws = [float(ws) for ws in locnode['allresdict']['21']]
        simnode['maxres'], simnode['minres'], simnode['avres']= max(taws), min(taws), sum(taws)/len(taws)
        (fig, ax) = wr_axes()
        sbinvals = arange(0,int(ceil(max(taws))),2)
        dbinvals = arange(-11.25,372.25,22.5)
        dfreq = histogram(awd, bins=dbinvals)[0]
        dfreq[0] = dfreq[0] + dfreq[-1]
        dfreq = dfreq[:-1]
        simnode['maxfreq'] = 100*numpy.max(dfreq)/len(awd)
        simnode['nbins'] = len(sbinvals)

        if simnode.wrtype == '0':
            ax.bar(awd, aws, bins=sbinvals, normed=True, opening=0.8, edgecolor='white')
        if simnode.wrtype == '1':
            ax.box(awd, aws, bins=sbinvals, normed=True)
        if simnode.wrtype in ('2', '3', '4'):
            ax.contourf(awd, aws, bins=sbinvals, normed=True, cmap=cm.hot)

        plt.savefig(scene['viparams']['newdir']+'/disp_wind.svg')
        (wro, scale) = wind_rose(simnode['maxres'], scene['viparams']['newdir']+'/disp_wind.svg', simnode.wrtype)
        wro['maxres'], wro['minres'], wro['avres'] = max(aws), min(aws), sum(aws)/len(aws)
        windnum(simnode['maxfreq'], (0,0,0), scale, compass((0,0,0), scale, wro, wro.data.materials['wr-000000']))
        bpy.ops.view3d.wrlegdisplay('INVOKE_DEFAULT')
#        if simnode.wrtype == '4':
#            (fig, ax) = wr_axes()
#            ax.contour(awd, aws, bins=sbinvals, normed=True, cmap=cm.hot)
#            plt.savefig(scene['viparams']['newdir']+'/disp_wind.svg')
        return {'FINISHED'}

class VIEW3D_OT_WRLegDisplay(bpy.types.Operator):
    '''Display results legend and stats in the 3D View'''
    bl_idname = "view3d.wrlegdisplay"
    bl_label = "Wind rose legend"
    bl_description = "Display Wind Rose legend"
    bl_register = True
    bl_undo = True

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
        if context.scene.vi_display == 0 or context.scene['viparams']['vidisp'] != 'wr':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_spnum, 'WINDOW')
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        simnode = bpy.data.node_groups[context.scene['viparams']['restree']].nodes[context.scene['viparams']['resnode']]
        self._handle_spnum = bpy.types.SpaceView3D.draw_handler_add(viwr_legend, (self, context, simnode), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_Shadow(bpy.types.Operator):
    bl_idname = "node.shad"
    bl_label = "Shadow Study"
    bl_description = "Undertake a shadow study"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
#        return context.window_manager.invoke_props_dialog(self)
        scene = context.scene        
        if viparams(self, scene):            
            return {'CANCELLED'}

        shadobs = retobjs('livig')
        if not shadobs:
            self.report({'ERROR'},"No shading objects have a material attached.")
            return {'CANCELLED'}
            
        scene['liparams']['shadc'] = [ob.name for ob in retobjs('ssc')]
        if not scene['liparams']['shadc']:
            self.report({'ERROR'},"No objects have a VI Shadow material attached.")
            return {'CANCELLED'}

        scene['viparams']['restree'] = self.nodeid.split('@')[1]
        scene['viparams']['vidisp'] = 'ss'
        clearscene(scene, self)
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
#        simnode.running = 1
        scene['viparams']['visimcontext'] = 'Shadow'
        if not scene.get('liparams'):
           scene['liparams'] = {}
        scene['liparams']['cp'], scene['liparams']['unit'], scene['liparams']['type'] = simnode.cpoint, '% Sunlit', 'VI Shadow'
        simnode.preexport()
        (scene['liparams']['fs'], scene['liparams']['fe']) = (scene.frame_current, scene.frame_current) if simnode.animmenu == 'Static' else (scene.frame_start, scene.frame_end)
        cmap('grey')

        if simnode.starthour > simnode.endhour:
            self.report({'ERROR'},"End hour is before start hour.")
            return{'CANCELLED'}
        
        scene['viparams']['resnode'], simnode['Animation'] = simnode.name, simnode.animmenu

        if simnode['Animation'] == 'Static':
            scmaxres, scminres, scavres, scene['liparams']['fs'] = [0], [100], [0], scene.frame_current
        else:
            (scmaxres, scminres, scavres) = [[x] * (scene.frame_end - scene.frame_start + 1) for x in (0, 100, 0)]
        
        frange = range(scene['liparams']['fs'], scene['liparams']['fe'] + 1)
        time = datetime.datetime(datetime.datetime.now().year, simnode.startmonth, 1, simnode.starthour - 1)
        y =  datetime.datetime.now().year if simnode.endmonth >= simnode.startmonth else datetime.datetime.now().year + 1
        endtime = datetime.datetime(y, simnode.endmonth, (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[simnode.endmonth - 1], simnode.endhour - 1)
        interval = datetime.timedelta(hours = modf(simnode.interval)[0], minutes = 60 * modf(simnode.interval)[1])
        times = [time + interval*t for t in range(int((endtime - time)/interval)) if simnode.starthour <= (time + interval*t).hour <= simnode.endhour]
        sps = [solarPosition(t.timetuple().tm_yday, t.hour+t.minute/60, scene.latitude, scene.longitude)[2:] for t in times]
        direcs = [mathutils.Vector((-sin(sp[1]), -cos(sp[1]), tan(sp[0]))) for sp in sps if sp[0] > 0]
        calcno = len(frange) * sum(len([f for f in o.data.polygons if o.data.materials[f.material_index].mattype == '2']) for o in [scene.objects[on] for on in scene['liparams']['shadc']])
        calcsteps = [int(i * calcno/20) for i in range(0, 21)]     
        curres = 0
        starttime = datetime.datetime.now()
        progressfile(scene, starttime, calcsteps, curres, 'clear')
        kivyrun = progressbar(os.path.join(scene['viparams']['newdir'], 'viprogress'))

        
        for oi, o in enumerate([scene.objects[on] for on in scene['liparams']['shadc']]):
            o['omin'], o['omax'], o['oave'] = {}, {}, {}
            bm = bmesh.new()
            bm.from_mesh(o.data)
            clearlayers(bm)
            bm.transform(o.matrix_world)
            geom = bm.faces if simnode.cpoint == '0' else bm.verts
            geom.layers.int.new('cindex')
            cindex = geom.layers.int['cindex']
            [geom.layers.float.new('res{}'.format(fi)) for fi in frange]

            for frame in frange:                
#                scene.frame_set(frame)
                shadtree = rettree(scene, shadobs)
                shadres = geom.layers.float['res{}'.format(frame)]
                if simnode.cpoint == '0':
                    gpoints = [f for f in geom if o.data.materials[f.material_index].mattype == '2']
                if simnode.cpoint == '1':
                    gpoints = [v for v in geom if any([o.data.materials[f.material_index].mattype == '2' for f in v.link_faces])]
                for g, gp in enumerate(gpoints):
                    gp[cindex] = g + 1                    
                    if simnode.cpoint == '0':
                        gp[shadres] = 100 * (1 - sum([(1, 0)[shadtree.ray_cast(gp.calc_center_bounds(), direc)[3] == None] for direc in direcs])/len(direcs))
                    else:
                        gp[shadres] = 100 * (1 - sum([(1, 0)[shadtree.ray_cast(gp.co, direc)[3] == None] for direc in direcs])/len(direcs))

                    curres += 1
                    if curres in calcsteps:
                        if progressfile(scene, starttime, calcsteps, curres, 'run') == 'CANCELLED':
                            return {'CANCELLED'}
#                    if curres in calcsteps:
#                        with open(os.path.join(scene['viparams']['newdir'], 'viprogress'), 'r') as progressfile:
#                            if 'Cancel' in progressfile.read():
#                                return {'CANCELLED'}
#                                
#                        with open(os.path.join(scene['viparams']['newdir'], 'viprogress'), 'w') as progressfile:
#                            progressfile.write('{} {}'.format(5 * calcsteps.index(curres), (time.now() - starttime)/calcsteps.index(curres) * (20 - calcsteps.index(curres))))
                    
                o['omin']['res{}'.format(frame)], o['omax']['res{}'.format(frame)], o['oave']['res{}'.format(frame)] = min([gp[shadres] for gp in gpoints]), max([gp[shadres] for gp in gpoints]), sum([gp[shadres] for gp in gpoints])/len(gpoints)

            bm.transform(o.matrix_world.inverted())
            bm.to_mesh(o.data)
            bm.free()

        scene.vi_leg_max, scene.vi_leg_min = 100, 0
#        scene.frame_set(scene['liparams']['fs'])
        if kivyrun.poll() is None:
            kivyrun.kill()
#        simnode.running = 0
        scene.vi_display = 1
        simnode.postexport(scene)
        return {'FINISHED'}

# Openfoam operators

class NODE_OT_Blockmesh(bpy.types.Operator):
    bl_idname = "node.blockmesh"
    bl_label = "Blockmesh export"
    bl_description = "Export an Openfoam blockmesh"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        expnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        bmos = [o for o in scene.objects if o.vi_type == '2']
        
        if viparams(self, scene):
            return {'CANCELLED'}        
        if len(bmos) != 1:
            ({'ERROR'},"One and only one object with the CFD Domain property is allowed")
            return {'ERROR'}
        with open(os.path.join(scene['viparams']['ofsfilebase'], 'controlDict'), 'w') as cdfile:
            cdfile.write(fvcdwrite("simpleFoam", 0.005, 5))
        with open(os.path.join(scene['viparams']['ofsfilebase'], 'fvSolution'), 'w') as fvsolfile:
            fvsolfile.write(fvsolwrite(expnode))
        with open(os.path.join(scene['viparams']['ofsfilebase'], 'fvSchemes'), 'w') as fvschfile:
            fvschfile.write(fvschwrite(expnode))
        with open(os.path.join(scene['viparams']['ofcpfilebase'], 'blockMeshDict'), 'w') as bmfile:
            bmfile.write(fvbmwrite(bmos[0], expnode))
        if not expnode.existing:
            call(("blockMesh", "-case", "{}".format(scene['viparams']['offilebase'])))
            fvblbmgen(bmos[0].data.materials, open(os.path.join(scene['viparams']['ofcpfilebase'], 'faces'), 'r'), open(os.path.join(scene['viparams']['ofcpfilebase'], 'points'), 'r'), open(os.path.join(scene['viparams']['ofcpfilebase'], 'boundary'), 'r'), 'blockMesh')
        else:
            pass

        expnode.export()
        return {'FINISHED'}

class NODE_OT_Snappymesh(bpy.types.Operator):
    bl_idname = "node.snappy"
    bl_label = "SnappyHexMesh export"
    bl_description = "Export an Openfoam snappyhexmesh"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def execute(self, context):
        scene, mats = context.scene, []

        for dirname in os.listdir(scene['viparams']['offilebase']):
            if os.path.isdir(os.path.join(scene['viparams']['offilebase'], dirname)) and dirname not in ('0', 'constant', 'system'):
                shutil.rmtree(os.path.join(scene['viparams']['offilebase'], dirname))
        for fname in os.listdir(scene['viparams']['ofcpfilebase']):
            if os.path.isfile(os.path.join(scene['viparams']['ofcpfilebase'], fname)) and fname in ('cellLevel', 'pointLevel', 'surfaceIndex', 'level0Edge', 'refinementHistory'):
                os.remove(os.path.join(scene['viparams']['ofcpfilebase'], fname))

        expnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        fvos = [o for o in scene.objects if o.vi_type == '3']
        if fvos:
            selobj(scene, fvos[0])
            bmos = [o for o in scene.objects if o.vi_type == '2']
#                bpy.ops.export_mesh.stl(filepath=os.path.join(scene['viparams']['ofctsfilebase'], '{}.obj'.format(o.name)), check_existing=False, filter_glob="*.stl", axis_forward='Y', axis_up='Z', global_scale=1.0, use_scene_unit=True, ascii=False, use_mesh_modifiers=True)
            fvobjwrite(scene, fvos[0], bmos[0])
#            bpy.ops.export_scene.obj(check_existing=True, filepath=os.path.join(scene['viparams']['ofctsfilebase'], '{}.obj'.format(fvos[0].name)), axis_forward='Y', axis_up='Z', filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=True, use_smooth_groups=False, use_smooth_groups_bitflags=False, use_normals=False, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=False, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=True, keep_vertex_order=False, global_scale=1.0, path_mode='AUTO')
            gmats = [mat for mat in fvos[0].data.materials if mat.flovi_ground]
#            if gmats:
            with open(os.path.join(scene['viparams']['ofsfilebase'], 'snappyHexMeshDict'), 'w') as shmfile:
                shmfile.write(fvshmwrite(expnode, fvos[0], ground = gmats))
            with open(os.path.join(scene['viparams']['ofsfilebase'], 'meshQualityDict'), 'w') as mqfile:
                mqfile.write(fvmqwrite())
            with open(os.path.join(scene['viparams']['ofsfilebase'], 'surfaceFeatureExtractDict'), 'w') as sfefile:
                sfefile.write(fvsfewrite(fvos[0].name))
        call(('surfaceFeatureExtract', "-case", "{}".format(scene['viparams']['offilebase'])))
        call(('snappyHexMesh', "-overwrite", "-case", "{}".format(scene['viparams']['offilebase'])))
        for mat in fvos[0].data.materials:
#            mat.name = '{}_{}'.format(fvos[0].name, mat.name)
            mats.append(mat)
        for mat in [o for o in scene.objects if o.vi_type == '2'][0].data.materials:
            mats.append(mat)
        fvblbmgen(mats, open(os.path.join(scene['viparams']['ofcpfilebase'], 'faces'), 'r'), open(os.path.join(scene['viparams']['ofcpfilebase'], 'points'), 'r'), open(os.path.join(scene['viparams']['ofcpfilebase'], 'boundary'), 'r'), 'hexMesh')

        expnode.export()
        return {'FINISHED'}

class NODE_OT_FVSolve(bpy.types.Operator):
    bl_idname = "node.fvsolve"
    bl_label = "FloVi simulation"
    bl_description = "Solve an OpenFOAM case"
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        bmos = [o for o in scene.objects if o.vi_type in ('2', '3')]
        with open(os.path.join(scene['viparams']['ofsfilebase'], 'controlDict'), 'w') as cdfile:
            cdfile.write(fvcdwrite(simnode.solver, simnode.dt, simnode.et))
        fvvarwrite(scene, bmos, simnode)
        with open(os.path.join(scene['viparams']['ofsfilebase'], 'fvSolution'), 'w') as fvsolfile:
            fvsolfile.write(fvsolwrite(simnode))
        with open(os.path.join(scene['viparams']['ofsfilebase'], 'fvSchemes'), 'w') as fvschfile:
            fvschfile.write(fvschwrite(simnode))
        with open(os.path.join(scene['viparams']['ofcfilebase'], 'transportProperties'), 'w') as fvtppfile:
            fvtppfile.write(fvtppwrite(simnode.solver))
        if simnode.solver != 'icoFoam':
            with open(os.path.join(scene['viparams']['ofcfilebase'], 'RASProperties'), 'w') as fvrasfile:
                fvrasfile.write(fvraswrite(simnode.turbulence))
        call((simnode.solver, "-case", "{}".format(scene['viparams']['offilebase'])))
        Popen(("paraFoam", "-case", "{}".format(scene['viparams']['offilebase'])))
        simnode.export()
        return {'FINISHED'}
