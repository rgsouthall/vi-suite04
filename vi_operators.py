import bpy, datetime, mathutils, os, bmesh, shutil, subprocess
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
    print(e)
    
    mp = 0

from .livi_export import radgexport, cyfc1, createoconv, createradfile
from .livi_calc  import li_calc
from .vi_display import li_display, li_compliance, linumdisplay, spnumdisplay, li3D_legend, viwr_legend, en_air, en_panel
from .envi_export import enpolymatexport, pregeo
from .envi_mat import envi_materials, envi_constructions
from .vi_func import processf, selobj, livisimacc, solarPosition, wr_axes, clearscene, clearfiles, viparams, objmode, nodecolour, cmap, vertarea, wind_rose, compass, windnum, envizres, envilres
from .vi_func import fvcdwrite, fvbmwrite, fvblbmgen, fvvarwrite, fvsolwrite, fvschwrite, fvtppwrite, fvraswrite, fvshmwrite, fvmqwrite, fvsfewrite, fvobjwrite, sunposenvi, recalculate_text
from .vi_chart import chart_disp
from .vi_gen import vigen

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
            cang = '180 -vth' if simnode['coptions']['Context'] == 'Basic' and simnode['coptions']['Type'] == '1' else cam.data.angle*180/pi
            vv = 180 if simnode['coptions']['Context'] == 'Basic' and simnode['coptions']['Type'] == '1' else cang * scene.render.resolution_y/scene.render.resolution_x
            vd = (0.001, 0, -1*cam.matrix_world[2][2]) if (round(-1*cam.matrix_world[0][2], 3), round(-1*cam.matrix_world[1][2], 3)) == (0.0, 0.0) else [-1*cam.matrix_world[i][2] for i in range(3)]
            if simnode.pmap:
                pmcmd = ('mkpmap', '+fo', '+bv', '-apD', '0.001', '-apo', ' '.join([mat.name.replace(" ", "_") for mat in bpy.data.materials if mat.pport]), '-apg', '{}-{}.gpm'.format(scene['viparams']['filebase'], frame), '{}'.format(simnode.pmapgno), '-apc', '{}-{}.cpm'.format(scene['viparams']['filebase'], frame), '{}'.format(simnode.pmapcno), '{}-{}.oct'.format(scene['viparams']['filebase'], frame))
                subprocess.call(pmcmd)
                rvucmd = "rvu -w -ap {8} 50 -ap {9} 50 -n {0} -vv {1} -vh {2} -vd {3[0]:.3f} {3[1]:.3f} {3[2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} -ab 1 {6}-{7}.oct".format(scene['viparams']['wnproc'], vv, cang, vd, cam.location, simnode['radparams'], scene['viparams']['filebase'], scene.frame_current, '{}-{}.gpm'.format(scene['viparams']['filebase'], frame), '{}-{}.cpm'.format(scene['viparams']['filebase'], frame))
            else:
                rvucmd = "rvu -w -n {0} -vv {1} -vh {2} -vd {3[0]:.3f} {3[1]:.3f} {3[2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct".format(scene['viparams']['wnproc'], vv, cang, vd, cam.location, simnode['radparams'], scene['viparams']['filebase'], scene.frame_current)
            rvurun = Popen(rvucmd.split(), stdout = PIPE, stderr = PIPE)

            for line in rvurun.stderr:
                if 'view up parallel to view direction' in line.decode():
                    self.report({'ERROR'}, "Camera cannot point directly upwards")
                if 'X11' in line.decode():
                    self.report({'ERROR'}, "No X11 display server found. You may need to install XQuartz")

            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "There is no camera in the scene. Radiance preview will not work")
            return {'CANCELLED'}

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
                catrun = Popen(catcmd.split(), stdout = PIPE)
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

            rpictcmd = "rpict -w -vth -vh 180 -vv 180 -x 800 -y 800 -vd {0[0][2]:.3f} {0[1][2]} {0[2][2]} -vp {1[0]} {1[1]} {1[2]} {2} {3}-{4}.oct".format(-1*self.cam.matrix_world, self.cam.location, self.simnode['radparams'], self.scene['viparams']['filebase'], self.frame)
            self.rprun = Popen(rpictcmd.split(), stdout=PIPE)
            egcmd = "evalglare -c {}".format(os.path.join(self.scene['viparams']['newdir'], 'glare{}.hdr'.format(self.frame)))
            self.egrun = Popen(egcmd.split(), stdin = self.rprun.stdout, stdout=PIPE)
            return {'RUNNING_MODAL'}
        else:
            self.report({'ERROR'}, "There is no camera in the scene. Create one for glare analysis")
            return {'FINISHED'}

class NODE_OT_LiViCalc(bpy.types.Operator):
    bl_idname = "node.livicalc"
    bl_label = "LiVi simulation"
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        if viparams(self, scene):
            return {'CANCELLED'}
        
            
        objmode()
#        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel, scene.li_disp_count = 0, 0, 0, 0, 0, 0, 0, 0
#        scene['viparams']['vidisp'] = 'li'
        clearscene(scene, self)
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        simnode.preexport()
        
#        subcontext = simnode.inputs['Context in'].links[0].from_socket['Options']['Type']
        
        contextdict = {'Basic': 'LiVi Basic', 'Compliance': 'LiVi Compliance', 'CBDM': 'LiVi CBDM'}        
#        links = (list(simnode.inputs['Geometry in'].links[:]) + list(simnode.inputs['Context in'].links[:]))
#        frames = [sorted([int(k) for k in link.from_socket['Text'].keys]) for link in links]
        
        # Set scene parameters
        scene['viparams']['visimcontext'] = contextdict[simnode['coptions']['Context']]
        scene['liparams']['fs'] = min((simnode['coptions']['fs'], simnode['goptions']['fs'])) 
        scene['liparams']['fe'] = max((simnode['coptions']['fe'], simnode['goptions']['fe'])) 
        scene['liparams']['cp'] = simnode['goptions']['cp']
        scene['liparams']['unit'] = simnode['coptions']['unit']
        scene['liparams']['type'] = simnode['coptions']['Type']
        scene.frame_start, scene.frame_end = scene['liparams']['fs'], scene['liparams']['fe']

#        if simnode['coptions']['Context'] in ('Basic', 'Compliance') or (simnode['coptions']['Context'] == 'CBDM' and simnode['coptions']['Type'] in ('0', '1')):
        for frame in range(scene['liparams']['fs'], scene['liparams']['fe'] + 1):
#            if not simnode.edit_file:
            createradfile(scene, frame, self, simnode)
#            elif not os.path.isfile(os.path.join(scene['viparams']['newdir'], scene['viparams']['filename']+'-{}.rad'.format(frame))):
#                self.report({'ERROR'}, "There is no saved radiance input file. Turn off the edit file option")
#                return {'CANCELLED'}
            createoconv(scene, frame, self, simnode)

#        if simnode['coptions']['Context'] != 'Basic' and simnode['coptions']['Context'] != '1':
#            geogennode = geonode.inputs['Generative in'].links[0].from_node if geonode.inputs['Generative in'].links else 0
#            tarnode = connode.inputs['Target in'].links[0].from_node if connode.inputs['Target in'].is_linked else 0
#            if geogennode and tarnode:
#                simnode['Animation'] = 'Animated'
#                vigen(self, li_calc, resapply, geonode, connode, simnode, geogennode, tarnode)
#            if simnode['coptions']['Type']  != '1':
#                scene['liparams']['type'] = 'Basic'
#                simnode['Animation'] = 'Animated' if scene['liparams']['gfe'] > 0 or scene['liparams']['cfe'] > 0 else 'Static'
        li_calc(self, simnode, livisimacc(simnode))
        if simnode['coptions']['Context'] != 'CBDM' and simnode['coptions']['Context'] != '3':
            scene.vi_display = 1
#        else:
#            simnode['Animation'] = 'Animated' if scene['liparams']['gfe'] > 0 or scene['liparams']['cfe'] > 0 else 'Static'
#            scene['liparams']['fs'] = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_start
#            scene['liparams']['fe'] = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_end
#            li_calc(self, simnode, livisimacc(simnode))
#        scene.vi_display = 1 if simnode['coptions']['Type'] != '1' or simnode['coptions']['Context'] != 'CBDM' else 0
#        scene['liparams']['fe'] = max(context.scene['liparams']['gfe'], context.scene['liparams']['cfe'])
        scene['viparams']['vidisp'] = 'li'
        scene['viparams']['resnode'] = simnode.name
        scene['viparams']['restree'] = self.nodeid.split('@')[1]
        simnode.postexport()
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
                    scene.vi_leg_max += 10
                    return {'RUNNING_MODAL'}
                if event.type == 'WHEELDOWNMOUSE':
                    if scene.vi_leg_max >= 10:
                        scene.vi_leg_max -= 10
                    else:
                        scene.vi_leg_max = 0
                    return {'RUNNING_MODAL'}
            elif event.mouse_region_x in range(100) and event.mouse_region_y in range(height - 520, height - 420):
                if event.type == 'WHEELUPMOUSE':
                    scene.vi_leg_min += 10
                    return {'RUNNING_MODAL'}
                if event.type == 'WHEELDOWNMOUSE':
                    if scene.vi_leg_min >= 10:
                        scene.vi_leg_min -= 10
                    else:
                        scene.vi_leg_min = 0
                    return {'RUNNING_MODAL'}

#        if (scene.li_disp_panel < 2 and scene.ss_disp_panel < 2) or self.disp != scene.li_disp_count:
        if  not [o for o in bpy.data.objects if o.get('lires')]:
            scene['viparams']['vidisp'] = ''
        if (scene['viparams']['vidisp'] not in ('lipanel', 'sspanel', 'licpanel')) or self.disp != scene.li_disp_count:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_leg, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_pointres, 'WINDOW')
            if scene['liparams']['type'] == 'LiVi Compliance':
                try:
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle_comp, 'WINDOW')
                except:
                    pass
                scene.li_compliance = 0
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        dispdict = {'LiVi Compliance': 'licpanel', 'LiVi Basic': 'lipanel', 'LiVi CBDM': 'lipanel'}
        scene = context.scene
        clearscene(scene, self)
        scene.li_disp_count = scene.li_disp_count + 1 if scene.li_disp_count < 10 else 0
        scene.vi_disp_wire = 0
        self.disp = scene.li_disp_count
        self.simnode = bpy.data.node_groups[scene['viparams']['restree']].nodes[scene['viparams']['resnode']]
#        (connode, geonode) = (0, 0) if self.simnode.bl_label == 'VI Shadow Study' else (self.simnode.export(self.bl_label))
        if self.simnode.bl_label == 'VI Shadow Study':
            scene['viparams']['vidisp'] = 'sspanel'
        else:
            scene['viparams']['vidisp'] = dispdict[scene['viparams']['visimcontext']]
#        (scene.li_disp_panel, scene.ss_disp_panel) = (0, 2) if self.simnode.bl_label == 'VI Shadow Study' else (2, 0)
        li_display(self.simnode)
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
                    me.from_pydata(vpos,[],faces)
                    me.update(calc_edges=True)
                    ob = bpy.data.objects.new(basename, me)
                    ob.location = (ostartx - minstartx, ostarty - minstarty, 0) if node.splitmesh else (0, 0, 0)   # position object at 3d-cursor
                    bpy.context.scene.objects.link(ob)
        bpy.context.user_preferences.edit.use_global_undo = True
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_CSVExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.csvexport"
    bl_label = "Export a CSV file"
    bl_description = "Select the CSV file to export"
    filename = ""
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
        resnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].inputs['Results in'].links[0].from_node
        resstring = ' '.join(['Month,', 'Day,', 'Hour,'] + ['{} {},'.format(resnode['resdict'][k][0], resnode['resdict'][k][1]) for k in sorted(resnode['resdict'].keys(), key=lambda x: float(x)) if len(resnode['resdict'][k]) == 2] + ['\n'])
        resdata = [resnode['allresdict']['Month'], resnode['allresdict']['Day'], resnode['allresdict']['Hour']] + [list(resnode['allresdict'][k]) for k in sorted(resnode['resdict'].keys(), key=lambda x: float(x)) if k in resnode['allresdict']]
        for rline in zip(*resdata):
            for r in rline:
                resstring += '{},'.format(r)
            resstring += '\n'
        with open(self.filepath, 'w') as csvfile:
            csvfile.write(resstring)
        return {'FINISHED'}

    def invoke(self,context,event):
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
#        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        node.sdoy = datetime.datetime(datetime.datetime.now().year, node.startmonth, 1).timetuple().tm_yday
        node.edoy = (datetime.date(datetime.datetime.now().year, node.endmonth + (1, -11)[node.endmonth == 12], 1) - datetime.timedelta(days = 1)).timetuple().tm_yday
        locnode = node.inputs['Location in'].links[0].from_node
        shutil.copyfile(locnode.weather, os.path.join(scene['viparams']['newdir'], "in.epw"))
        shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(os.path.realpath( __file__ ))), "EPFiles", "Energy+.idd"), os.path.join(scene['viparams']['newdir'], "Energy+.idd"))

        if bpy.context.active_object and not bpy.context.active_object.hide:
            if bpy.context.active_object.type == 'MESH':
                bpy.ops.object.mode_set(mode = 'OBJECT')

        enpolymatexport(self, node, locnode, envi_mats, envi_cons)
        node.bl_label = node.bl_label[1:] if node.bl_label[0] == '*' else node.bl_label
        node.exported, node.outputs['Context out'].hide = True, False
        node.export()
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
                    with open(os.path.join(scene['viparams']['newdir'], 'eplusout.eso'), 'r') as resfile:
                        for resline in [line for line in resfile.readlines()[::-1] if line.split(',')[0] == '2' and len(line.split(',')) == 9]:
                            self.simnode.run = int(100 * int(resline.split(',')[1])/(self.simnode.dedoy - self.simnode.dsdoy))
                            break
                    return {'PASS_THROUGH'}
                except:
                    return {'PASS_THROUGH'}
            elif self.frame < scene['enparams']['fe']:
                self.frame += 1
                bpy.ops.node.ensim('INVOKE_DEFAULT')
            else:
                for fname in [fname for fname in os.listdir('.') if fname.split(".")[0] == self.simnode.resname]:
                    os.remove(os.path.join(scene['viparams']['newdir'], fname))

                nfns = [fname for fname in os.listdir('.') if fname.split(".")[0] == "eplusout"]
                for fname in nfns:
                    rename(os.path.join(scene['viparams']['newdir'], fname), os.path.join(scene['viparams']['newdir'],fname.replace("eplusout", self.simnode.resname)))

                if self.simnode.resname+".err" not in [im.name for im in bpy.data.texts]:
                    bpy.data.texts.load(os.path.join(scene['viparams']['newdir'], self.simnode.resname+".err"))

                if 'EnergyPlus Terminated--Error(s) Detected' in self.esimrun.stderr.read().decode() or not [f for f in nfns if f.split(".")[1] == "eso"] or self.simnode.run == 0:
                    errtext = "There is no results file. Check you have selected results outputs and that there are no errors in the .err file in the Blender text editor." if not [f for f in nfns if f.split(".")[1] == "eso"] else "There was an error in the input IDF file. Check the *.err file in Blender's text editor."
                    self.report({'ERROR'}, errtext)
                    self.simnode.run = -1
                    return {'CANCELLED'}
                else:
                    nodecolour(self.simnode, 0)
                    processf(self, self.simnode)
                    self.report({'INFO'}, "Calculation is finished.")
                    scene['viparams']['resnode'], scene['viparams']['connode'], scene['viparams']['vidisp'] = self.nodeid, '{}@{}'.format(self.connode.name, self.nodeid.split('@')[1]), 'en'
#                    scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
                    self.simnode.run = -1
                    return {'FINISHED'}
        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scene = context.scene
        self.frame = scene.frame_start
        if viparams(self, scene):
            return {'CANCELLED'}
        context.scene['viparams']['visimcontext'] = 'EnVi'
        wm = context.window_manager
        self._timer = wm.event_timer_add(1, context.window)
        wm.modal_handler_add(self)
        self.simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        self.simnode.sim()
        self.connode = self.simnode.inputs['Context in'].links[0].from_node
        self.simnode.resfilename = os.path.join(scene['viparams']['newdir'], self.simnode.resname+'.eso')
        os.chdir(scene['viparams']['newdir'])
        esimcmd = "EnergyPlus"
        self.esimrun = Popen(esimcmd.split(), stderr = PIPE)
        self.simnode.run = 0
        return {'RUNNING_MODAL'}

class VIEW3D_OT_EnDisplay(bpy.types.Operator):
    bl_idname = "view3d.endisplay"
    bl_label = "EnVi display"
    bl_description = "Display the EnVi results"
    bl_register = True
    bl_undo = True
    _handle = None
    disp =  bpy.props.IntProperty(default = 1)

    def modal(self, context, event):
        scene = context.scene
        if scene['viparams']['vidisp'] not in ('en', 'enpanel'):
            try:
#                if self.get('_handle_air'):
                bpy.types.SpaceView3D.draw_handler_remove(self._handle_air, 'WINDOW')
            except:
                pass
#            bpy.types.SpaceView3D.draw_handler_remove(self._handle_hum, 'WINDOW')
#            bpy.types.SpaceView3D.draw_handler_remove(self._handle_wind, 'WINDOW')
#            bpy.types.SpaceView3D.draw_handler_remove(self._handle_ztemp, 'WINDOW')
            if not scene.get('enpanel_disp'):
                bpy.types.SpaceView3D.draw_handler_remove(self._handle_enpanel, 'WINDOW')
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        scene, valheaders = context.scene, []
        resnode = bpy.data.node_groups[scene['viparams']['resnode'].split('@')[1]].nodes[scene['viparams']['resnode'].split('@')[0]]
        eresobs = {o.name: o.name.upper() for o in bpy.data.objects if o.name.upper() in [rval[0] for rval in resnode['resdict'].values()]}
#        ereslinks = {o.name: o.name.upper() for o in bpy.data.objects if o.name.upper() in [rval[0] for rval in resnode['resdict'].values()]}
#        scene['enviparams']['resobs'] = [o.name for o in bpy.data.objects if 'EN_'+o.name.upper() in [rval[0] for rval in resnode['resdict'].values()]]
        scene.frame_start, scene.frame_end = 0, 24 * (resnode['End'] - (resnode['Start'] - 1)) - 1
        if scene.resas_disp:
            suns = [o for o in bpy.data.objects if o.type == 'LAMP' and o.data.type == 'SUN']
            if not suns:
                bpy.ops.object.lamp_add(type='SUN')
                sun = bpy.context.object
            else:
                sun = suns[0]
            for headvals in resnode['resdict'].items():
                if len(headvals[1]) == 2 and headvals[1][1] == 'Direct Solar (W/m^2)':
                    valheaders.append(headvals[0])
                if len(headvals[1]) == 2 and headvals[1][1] == 'Diffuse Solar (W/m^2)':
                     valheaders.append(headvals[0])
            sunposenvi(scene, resnode, range(scene.frame_start, scene.frame_end), sun, valheaders)

        if scene.resaa_disp:
            for rtype in ('Temperature (degC)', 'Wind Speed (m/s)', 'Wind Direction (deg)', 'Humidity (%)'):
                for headvals in resnode['resdict'].items():
                    if headvals[1][0] == 'Climate' and headvals[1][1] == rtype:
                        valheaders.append(headvals[0])

            self._handle_air = bpy.types.SpaceView3D.draw_handler_add(en_air, (self, context, resnode, valheaders), 'WINDOW', 'POST_PIXEL')

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
        if not bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.append(recalculate_text)

        self._handle_enpanel = bpy.types.SpaceView3D.draw_handler_add(en_panel, (self, context, resnode), 'WINDOW', 'POST_PIXEL')
        scene['viparams']['vidisp'] = 'enpanel'
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

        if not len(innodes[0]['allresdict']['Hour']):
            self.report({'ERROR'},"There are no results in the results file. Check the results.err file in Blender")
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
        solringnum, sd, numpos = 0, 100, {}
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        node.export()
        scene, scene['viparams']['resnode'], scene['viparams']['restree'] = context.scene, node.name, self.nodeid.split('@')[1]
#        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 1, 0, 0, 0, 0, 0
        scene['viparams']['vidisp'] = 'sp'
        context.scene['viparams']['visimcontext'] = 'SunPath'
        scene.cursor_location = (0.0, 0.0, 0.0)
        matdict = {'SolEquoRings': (1, 0, 0), 'HourRings': (1, 1, 0), 'SPBase': (1, 1, 1), 'Sun': (1, 1, 1)}
        for mat in [mat for mat in matdict.items() if mat[0] not in bpy.data.materials]:
            bpy.data.materials.new(mat[0])
            bpy.data.materials[mat[0]].diffuse_color = mat[1]

        if 'SUN' in [ob.data.type for ob in context.scene.objects if ob.data == 'LAMP' and ob.hide == False]:
            [ob.data.type for ob in context.scene.objects if ob.data == 'LAMP' and ob.data.type == 'SUN'][0]['VIType'] = 'Sun'
        elif 'Sun' not in [ob.get('VIType') for ob in context.scene.objects]:
            bpy.ops.object.lamp_add(type = "SUN")
#            sun = context.active_object
            context.active_object['VIType'] = 'Sun'
        else:
            sun = [ob for ob in context.scene.objects if ob.get('VIType') == 'Sun'][0]
            sun.animation_data_clear()

        if scene.render.engine == 'CYCLES' and bpy.data.worlds['World'].get('node_tree') and 'Sky Texture' in [no.bl_label for no in bpy.data.worlds['World'].node_tree.nodes]:
            bpy.data.worlds['World'].node_tree.animation_data_clear()

        sun['solhour'], sun['solday'], sun['soldistance'] = scene.solhour, scene.solday, scene.soldistance

        if "SkyMesh" not in [ob.get('VIType') for ob in context.scene.objects]:
            bpy.data.materials.new('SkyMesh')
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, size=105)
            smesh = context.active_object
            smesh.location, smesh.rotation_euler[0], smesh.cycles_visibility.shadow, smesh.name, smesh['VIType']  = (0,0,0), pi, False, "SkyMesh", "SkyMesh"
            bpy.ops.object.material_slot_add()
            smesh.material_slots[0].material = bpy.data.materials['SkyMesh']
            bpy.ops.object.shade_smooth()
            smesh.hide = True

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
        bm = bmesh.new()
        bm.from_mesh(spathmesh)

        for doy in range(0, 363):
            for hour in range(1, 25):
                ([solalt, solazi]) = solarPosition(doy, hour, scene.latitude, scene.longitude)[2:]
                bm.verts.new().co = [-(sd-(sd-(sd*cos(solalt))))*sin(solazi), -(sd-(sd-(sd*cos(solalt))))*cos(solazi), sd*sin(solalt)]
        for v in range(24, len(bm.verts)):
            if hasattr(bm.verts, "ensure_lookup_table"):
                bm.verts.ensure_lookup_table()
            bm.edges.new((bm.verts[v], bm.verts[v - 24]))
            if v in range(8568, 8736):
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

        for vert in spathob.data.vertices[0:16 * (solringnum + 3)]:
            vert.select = True

        bpy.ops.object.material_slot_add()
        spathob.material_slots[-1].material = bpy.data.materials['SolEquoRings']
        spathob.active_material_index = 1
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.object.material_slot_assign()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(0.0, 0.0, 0.0), plane_no=(0.0, 0.0, 1.0), use_fill=True, clear_inner=True, clear_outer=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        compass((0,0,-sd*0.01), sd, spathob, bpy.data.materials['SPBase'])

        for ob in (spathob, sunob):
            spathob.cycles_visibility.diffuse, spathob.cycles_visibility.shadow, spathob.cycles_visibility.glossy, spathob.cycles_visibility.transmission = [False] * 4

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
        if context.area:
            context.area.tag_redraw()
        if context.scene.vi_display == 0 or context.scene['viparams']['vidisp'] != 'sp':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_spnum, 'WINDOW')
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        simnode = bpy.data.node_groups[context.scene['viparams']['restree']].nodes[context.scene['viparams']['resnode']]
        self._handle_spnum = bpy.types.SpaceView3D.draw_handler_add(spnumdisplay, (self, context, simnode), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        context.scene.vi_display = 1
        return {'RUNNING_MODAL'}

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
#        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 0, 0, 0, 0, 0, 1
        scene['viparams']['vidisp'] = 'wr'
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
        if simnode.wrtype == '4':
            (fig, ax) = wr_axes()
            ax.contour(awd, aws, bins=sbinvals, normed=True, cmap=cm.hot)
            plt.savefig(scene['viparams']['newdir']+'/disp_wind.svg')
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
        scene = context.scene
        scene['shadc'] = [ob.name for ob in scene.objects if ob.type == 'MESH' and not ob.hide and len([f for f in ob.data.polygons if ob.data.materials[f.material_index].mattype == '2'])]

        if not scene['shadc']:
            self.report({'ERROR'},"No objects have a VI Shadow material attached.")
            return {'CANCELLED'}

        scene['viparams']['restree'] = self.nodeid.split('@')[1]
#        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 0, 0, 0, 0, 1, 0
        scene['viparams']['vidisp'] = 'ss'
        clearscene(scene, self)
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
#        simnode.running = 1
        scene['viparams']['visimcontext'] = 'Shadow'
        if not scene.get('liparams'):
           scene['liparams'] = {}
        scene['liparams']['cp'], scene['liparams']['unit'], scene['liparams']['type'] = simnode.cpoint, '% Sunlit', 'VI Shadow'
        simnode.export(scene)
        (scene.fs, scene.fe) = (scene.frame_current, scene.frame_current) if simnode.animmenu == 'Static' else (scene.frame_start, scene.frame_end)
        cmap('grey')

        if simnode.starthour > simnode.endhour:
            self.report({'ERROR'},"End hour is before start hour.")
            return{'CANCELLED'}
        scene['viparams']['resnode'], simnode['Animation'] = simnode.name, simnode.animmenu

        if simnode['Animation'] == 'Static':
            scmaxres, scminres, scavres, scene.fs = [0], [100], [0], scene.frame_current
        else:
            (scmaxres, scminres, scavres) = [[x] * (scene.frame_end - scene.frame_start + 1) for x in (0, 100, 0)]
        frange = range(scene.fs, scene.fe + 1)
        fdiff =  1 if simnode['Animation'] == 'Static' else scene.frame_end - scene.frame_start + 1
        time = datetime.datetime(datetime.datetime.now().year, simnode.startmonth, 1, simnode.starthour - 1)
        y =  datetime.datetime.now().year if simnode.endmonth >= simnode.startmonth else datetime.datetime.now().year + 1
        endtime = datetime.datetime(y, simnode.endmonth, (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[simnode.endmonth - 1], simnode.endhour - 1)
        interval = datetime.timedelta(hours = modf(simnode.interval)[0], minutes = 60 * modf(simnode.interval)[1])
        times = [time + interval*t for t in range(int((endtime - time)/interval)) if simnode.starthour <= (time + interval*t).hour <= simnode.endhour]
        sps = [solarPosition(t.timetuple().tm_yday, t.hour+t.minute/60, scene['latitude'], scene['longitude'])[2:] for t in times]
        direcs = [mathutils.Vector((-sin(sp[1]), -cos(sp[1]), tan(sp[0]))) for sp in sps if sp[0] > 0]

        for o in [scene.objects[on] for on in scene['shadc']]:
            o['omin'], o['omax'], o['oave'] = [0] * fdiff, [100] * fdiff, [100] * fdiff
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bm.transform(o.matrix_world)
            obcalcarea = sum([f.calc_area() for f in bm.faces if o.data.materials[f.material_index].mattype == '2'])
            if bm.faces.layers.int.get('cindex'):
                bm.faces.layers.int.remove(bm.faces.layers.int['cindex'])
            if bm.verts.layers.int.get('cindex'):
                bm.verts.layers.int.remove(bm.verts.layers.int['cindex'])
            if simnode.cpoint == '0':
                bm.faces.layers.int.new('cindex')
                cindex = bm.faces.layers.int['cindex']
                [bm.faces.layers.float.new('res{}'.format(fi)) for fi in frange]
            else:
                bm.verts.layers.int.new('cindex')
                cindex = bm.verts.layers.int['cindex']
                bm.verts.layers.int.new('cindex')
                [bm.verts.layers.float.new('res{}'.format(fi)) for fi in frange]

            for fi, frame in enumerate(frange):
                scene.frame_set(frame)
                if simnode.cpoint == '0':
                    shadres = bm.faces.layers.float['res{}'.format(frame)]
                    cfaces = [f for f in bm.faces if o.data.materials[f.material_index].mattype == '2']
                    for ci, f in enumerate([f for f in cfaces]):
                        f[cindex] = ci + 1
                        f[shadres] = 100 * (1 - sum([bpy.data.scenes[0].ray_cast(f.calc_center_median() + (simnode.offset * f.normal), f.calc_center_median() + 10000*direc)[0] for direc in direcs])/len(direcs))
                    o['omin'][fi], o['omax'][fi], o['oave'][fi] = min([f[shadres] for f in cfaces]), max([f[shadres] for f in cfaces]), sum([f[shadres] for f in cfaces])/len(cfaces)
                else:
                    shadres = bm.verts.layers.float['res{}'.format(frame)]
                    cverts = [v for v in bm.verts if any([o.data.materials[f.material_index].mattype == '2' for f in v.link_faces])]
                    for ci, v in enumerate([v for v in cverts]):
                        v[cindex] = ci + 1
                        v[shadres] = 100 * (1 - sum([bpy.data.scenes[0].ray_cast(v.co + simnode.offset*v.normal, v.co + 10000*direc)[0] for direc in direcs])/len(direcs))
                    o['omin'][fi], o['omax'][fi], o['oave'][fi] = min([v[shadres] for v in cverts]), max([v[shadres] for v in cverts]) , obcalcarea * sum([v[shadres]/vertarea(bm,v) for v in cverts])/len(cverts)
            bm.transform(o.matrix_world.inverted())
            bm.to_mesh(o.data)
            bm.free()

        for fi, frame in enumerate(frange):
            simnode['minres']['{}'.format(frame)], simnode['maxres']['{}'.format(frame)], simnode['avres']['{}'.format(frame)] = 0, 100, sum([scene.objects[on]['oave'][fi] for on in scene['shadc']])/len(scene['shadc'])
        scene.vi_leg_max, scene.vi_leg_min = 100, 0
        scene.frame_set(scene.fs)
#        simnode.running = 0
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

        if viparams(self, scene):
            return {'CANCELLED'}
        bmos = [o for o in scene.objects if o.vi_type == '2']
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
#            fvrbm(bmos[0])
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
