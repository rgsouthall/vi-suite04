import bpy, bpy_extras, sys, datetime, mathutils, os, time
from os import rename
import bpy_extras.io_utils as io_utils
from subprocess import Popen, PIPE

try:
    import numpy
    from numpy import arange
    np = 1
except:
    np = 0

from collections import OrderedDict
from datetime import datetime as dt
from math import cos, sin, pi, ceil, tan, modf

try:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    mp = 1
except:
    mp = 0

from .livi_export import radcexport, radgexport, cyfc1, createoconv, createradfile
from .livi_calc  import li_calc, resapply
from .vi_display import li_display, li_compliance, linumdisplay, spnumdisplay, li3D_legend, viwr_legend
from .envi_export import enpolymatexport, pregeo
from .envi_mat import envi_materials, envi_constructions
from .vi_func import processf, livisimacc, solarPosition, vertarea, wr_axes, clearscene, framerange, vcframe, viparams, objmode, nodecolour, li_calcob
from .vi_chart import chart_disp
from .vi_gen import vigen

envi_mats = envi_materials()
envi_cons = envi_constructions()

class NODE_OT_LiGExport(bpy.types.Operator):
    bl_idname = "node.ligexport"
    bl_label = "VI-Suite export"
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        if bpy.data.filepath and " " not in bpy.data.filepath:
            viparams(scene)
            objmode()
            node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
            node.export(context)
            scene.frame_start, bpy.data.node_groups[self.nodeid.split('@')[1]].use_fake_user = 0, 1
            scene.frame_set(0)
            radgexport(self, node)
            node.exported = True
            node.bl_label = node.bl_label[1:] if node.bl_label[0] == '*' else node.bl_label
            node.outputs['Geometry out'].hide = False
            return {'FINISHED'}

        elif " "  in bpy.data.filepath:
            self.report({'ERROR'},"The directory path or Blender filename has a space in it. Please save again without any spaces and recreate this node")
            bpy.ops.node.delete()
            return {'FINISHED'}

        elif not bpy.data.filepath:
            self.report({'ERROR'},"The Blender file has not been saved. Save the Blender file and recreate this node before exporting")
            bpy.ops.node.delete()
            return {'FINISHED'}

class NODE_OT_EpwSelect(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "node.epwselect"
    bl_label = "Select EPW file"
    bl_description = "Select the EnergyPlus weather file"
    filename = ""
    filename_ext = ".HDR;.hdr;.epw;.EPW;"
    filter_glob = bpy.props.StringProperty(default="*.HDR;*.hdr;*.epw;*.EPW;", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import EPW File with FileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("epw", "EPW", "HDR", "hdr"):
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].epwname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the EPW filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_HdrSelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "node.hdrselect"
    bl_label = "Select HDR/VEC file"
    bl_description = "Select the HDR sky image or vector file"
    filename = ""
    filename_ext = ".HDR;.hdr;"
    filter_glob = bpy.props.StringProperty(default="*.HDR;*.hdr;", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import HDR image file with FileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("HDR", "hdr"):
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].hdrname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the HDR filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_MtxSelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "node.mtxselect"
    bl_label = "Select MTX file"
    bl_description = "Select the matrix file"
    filename = ""
    filename_ext = ".MTX;.mtx;"
    filter_glob = bpy.props.StringProperty(default="*.MTX;*.mtx;", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import MTX file with FileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("MTX", "mtx"):
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].mtxname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the matrix filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_SkySelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "node.skyselect"
    bl_label = "Select RAD file"
    bl_description = "Select the Radiance sky file"
    filename = ""
    filename_ext = ".rad;.RAD;"
    filter_glob = bpy.props.StringProperty(default="*.RAD;*.rad;", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import a Radiance sky file with the fileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("RAD", "rad"):
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].skyname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the Radiance sky filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_LiExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.liexport"
    bl_label = "Export"
    bl_description = "Export the scene to the Radiance file format"
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        locnode = 0 if node.bl_label == 'LiVi Compliance' else node.inputs['Location in'].links[0].from_node
        geonode = node.outputs['Context out'].links[0].to_node.inputs['Geometry in'].links[0].from_node if node.bl_label == 'LiVi CBDM' else 0
        node.export(context)
        scene = context.scene
        viparams(scene)
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        scene.frame_start = 0
        scene.frame_set(0)

        if 'LiVi Basic' in node.bl_label:
            node.starttime = datetime.datetime(datetime.datetime.now().year, 1, 1, int(node.shour), int((node.shour - int(node.shour))*60)) + datetime.timedelta(node.sdoy - 1) if node['skynum'] < 3 else datetime.datetime(datetime.datetime.now().year, 1, 1, 12)
            if node.animmenu == 'Time' and node['skynum'] < 3:
                node.endtime = datetime.datetime(2013, 1, 1, int(node.ehour), int((node.ehour - int(node.ehour))*60)) + datetime.timedelta(node.edoy - 1)
        if bpy.data.filepath:
            objmode()
            if " " not in bpy.data.filepath:
                scene.li_compliance = 1 if node.bl_label == 'LiVi Compliance' else 0
                radcexport(self, node, locnode, geonode)
            else:
#                    node.outputs['Context out'].hide = True
                self.report({'ERROR'},"The directory path or Blender filename has a space in it. Please save again without any spaces")
                return {'FINISHED'}
            return {'FINISHED'}
        else:
#                node.outputs['Context out'].hide = True
            self.report({'ERROR'},"Save the Blender file before exporting")
            return {'FINISHED'}

class NODE_OT_RadPreview(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.radpreview"
    bl_label = "Preview"
    bl_description = "Prevew the scene with Radiance"
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()
        
    def invoke(self, context, event):
        scene = context.scene
        viparams(scene)
        objmode()
#        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        simnode, frame = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]], scene.frame_current
        connode, geonode =  simnode.export(self.bl_label) 
        if frame not in range(scene.fs, scene.fe + 1):
            self.report({'ERROR'}, "Current frame is not within the exported frame range")
            return {'CANCELLED'}
        if not simnode.edit_file:
            createradfile(scene, frame, self, connode, geonode)
        elif not os.path.isfile(os.path.join(scene['viparams']['newdir'], scene['viparams']['filename']+'-{}.rad'.format(frame))):
            self.report({'ERROR'}, "There is no saved radiance input file. Turn off the edit file option")
            return {'CANCELLED'}
        createoconv(scene, frame, self)

        if os.path.isfile("{}-{}.rad".format(scene['viparams']['filebase'], scene.frame_current)):
            cam = scene.camera
            if cam:
                cang = '180 -vth' if connode.analysismenu == '3' else cam.data.angle*180/pi
                vv = 180 if connode.analysismenu == '3' else cang * scene.render.resolution_y/scene.render.resolution_x
                vd = (0.001, 0, -1*cam.matrix_world[2][2]) if (round(-1*cam.matrix_world[0][2], 3), round(-1*cam.matrix_world[1][2], 3)) == (0.0, 0.0) else [-1*cam.matrix_world[i][2] for i in range(3)]
                rvucmd = "rvu -w -n {0} -vv {1} -vh {2} -vd {3[0]:.3f} {3[1]:.3f} {3[2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct".format(scene['viparams']['nproc'], vv, cang, vd, cam.location, simnode['radparams'], scene['viparams']['filebase'], scene.frame_current)               
                rvurun = Popen(rvucmd.split(), stdout = PIPE, stderr = PIPE)
                time.sleep(0.1)
                if rvurun.poll() is not None:                    
                    for line in rvurun.stderr:
                        if 'view up parallel to view direction' in line.decode():
                            self.report({'ERROR'}, "Camera connot point directly upwards")
                            return {'CANCELLED'}
                    self.report({'ERROR'}, "Something wrong with the Radiance preview. Try rerunning the geometry and context export")
                    return {'CANCELLED'}
                return {'FINISHED'}    
            else:
                self.report({'ERROR'}, "There is no camera in the scene. Radiance preview will not work")
                return {'CANCELLED'}
        else:
            self.report({'ERROR'},"Missing export file. Make sure you have exported the scene or that the current frame is within the exported frame range.")
            return {'CANCELLED'}

class NODE_OT_LiVIGlare(bpy.types.Operator):
    bl_idname = "node.liviglare"
    bl_label = "Glare"
    bl_description = "Create a glare fisheye image from the Blender camera perspective"
    bl_register = True
    bl_undo = True
    
    nodeid = bpy.props.StringProperty()
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            if self.egrun.poll() is not None:
                if self.frame > self.scene.fs:
                    time = datetime.datetime(2014, 1, 1, self.connode.shour, 0) + datetime.timedelta(self.connode.sdoy - 1) if self.connode.animmenu == '0' else \
                    datetime.datetime(2014, 1, 1, int(self.connode.shour), int(60*(self.connode.shour - int(self.connode.shour)))) + datetime.timedelta(self.connode.sdoy - 1) + datetime.timedelta(hours = int(self.connode.interval*(self.frame-self.scene.fs)), seconds = int(60*(self.connode.interval*(self.frame-self.scene.fs) - int(self.connode.interval*(self.frame-self.scene.fs)))))
                    rpictcmd = "rpict -w -vth -vh 180 -vv 180 -x 800 -y 800 -vd {0[0][2]} {0[1][2]} {0[2][2]} -vp {1[0]} {1[1]} {1[2]} {2} {3}-{4}.oct".format(-1*self.cam.matrix_world, self.cam.location, self.simnode['radparams'], self.scene['viparams']['filebase'], self.frame)               
                    glarerun = Popen(rpictcmd.split(), stdout = PIPE)
                    egcmd = 'evalglare -c {}.hdr'.format(os.path.join(self.scene['viparams']['newdir'], 'glare'+str(self.frame)))
                    self.egrun = Popen(egcmd.split(), stdin = glarerun.stdout, stdout = PIPE)
                    return {'RUNNING_MODAL'}
                time = datetime.datetime(2014, 1, 1, self.connode.shour, 0) + datetime.timedelta(self.connode.sdoy - 1) if self.connode.animmenu == '0' else \
                    datetime.datetime(2014, 1, 1, int(self.connode.shour), int(60*(self.connode.shour - int(self.connode.shour)))) + datetime.timedelta(self.connode.sdoy - 1) + datetime.timedelta(hours = int(self.connode.interval*(self.frame-self.scene.fs)), seconds = int(60*(self.connode.interval*(self.frame-self.scene.fs) - int(self.connode.interval*(self.frame-self.scene.fs)))))
                with open(self.scene['viparams']['filebase']+".glare", "w") as glaretf:
                    for line in self.egrun.stdout:
                        if line.decode().split(",")[0] == 'dgp':
                            glaretext = line.decode().replace(',', ' ').replace("#INF", "").split(' ')                    
                            glaretf.write("{0:0>2d}/{1:0>2d} {2:0>2d}:{3:0>2d}\ndgp: {4:.3f}\ndgi: {5:.3f}\nugr: {6:.3f}\nvcp: {7:.3f}\ncgi: {8:.3f}\nLveil: {9:.3f}\n".format(time.day, time.month, time.hour, time.minute, *[float(x) for x in glaretext[6:12]]))
                pcondcmd = "pcond -u 300 {0}.hdr > {0}.temphdr".format(os.path.join(self.scene['viparams']['newdir'], 'glare'+str(self.frame)))
                Popen(pcondcmd, shell = True).communicate()
                psigncmd = "{0} {1}.glare | psign -h 32 -cb 0 0 0 -cf 40 40 40 | pcompos {3}.temphdr 0 0 - 800 550 > {3}.hdr" .format(self.scene['viparams']['cat'], self.scene['viparams']['filebase'], self.frame, os.path.join(self.scene['viparams']['newdir'], 'glare'+str(self.frame)))
                Popen(psigncmd, shell = True).communicate()
                rmcmd = "{} {}.temphdr".format(self.scene['viparams']['rm'], os.path.join(self.scene['viparams']['newdir'], 'glare'+str(self.frame)))                   
                Popen(rmcmd.split()).communicate()
                if  'glare{}.hdr'.format(self.frame) in bpy.data.images:
                    bpy.data.images['glare{}.hdr'.format(self.frame)].reload()
                else:
                    bpy.data.images.load(os.path.join(self.scene['viparams']['newdir'], 'glare{}.hdr'.format(self.frame)))     
                self.frame += 1
                if self.frame > self.scene.fe:
                    nodecolour(self.simnode, 0)
                    self.simnode.run = 0
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
        self._timer = wm.event_timer_add(0.5, context.window)
        wm.modal_handler_add(self)
        self.scene = bpy.context.scene
        self.cam = self.scene.camera
        if self.cam:
            self.simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
            self.connode, self.geonode = self.simnode.export(self.bl_label)
            self.frame = self.scene.fs
            for frame in range(self.scene.fs, self.scene.fe + 1):
                if not self.simnode.edit_file:
                    createradfile(self.scene, frame, self.connode, self.geonode)
                elif not os.path.isfile(os.path.join(self.scene['viparams']['newdir'], self.scene['viparams']['filename']+'-{}.rad'.format(frame))):
                    self.report({'ERROR'}, "There is no saved radiance input file. Turn off the edit file option")
                    return {'CANCELLED'}
                createoconv(self.scene, frame, self)

            rpictcmd = "rpict -w -vth -vh 180 -vv 180 -x 800 -y 800 -vd {0[0][2]} {0[1][2]} {0[2][2]} -vp {1[0]} {1[1]} {1[2]} {2} {3}-{4}.oct".format(-1*self.cam.matrix_world, self.cam.location, self.simnode['radparams'], self.scene['viparams']['filebase'], self.frame)               
            glarerun = Popen(rpictcmd.split(), stdout = PIPE)
            egcmd = 'evalglare -c {}.hdr'.format(os.path.join(self.scene['viparams']['newdir'], 'glare'+str(self.frame)))
            self.egrun = Popen(egcmd.split(), stdin = glarerun.stdout, stdout=PIPE)
            return {'RUNNING_MODAL'}
        else:
            self.report({'ERROR'}, "There is no camera in the scene. Create one for glare analysis")
            return {'FINISHED'}

class NODE_OT_LiViCalc(bpy.types.Operator):
    bl_idname = "node.livicalc"
    bl_label = "Radiance Simulation"

    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        viparams(scene)
        objmode()
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel, scene.li_disp_count = 0, 0, 0, 0, 0, 0, 0, 0
        clearscene(scene, self)
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        connode, geonode = simnode.export(self.bl_label)
        
        for frame in range(scene.fs, scene.fe + 1):
            if not simnode.edit_file:
                createradfile(scene, frame, self, connode, geonode)
            elif not os.path.isfile(os.path.join(scene['viparams']['newdir'], scene['viparams']['filename']+'-{}.rad'.format(frame))):
                self.report({'ERROR'}, "There is no saved radiance input file. Turn off the edit file option")
                return {'CANCELLED'}
            createoconv(scene, frame, self)
        scene['LiViContext'] = connode.bl_label
       
        if connode.bl_label == 'LiVi Basic':
            geogennode = geonode.inputs['Generative in'].links[0].from_node if geonode.inputs['Generative in'].links else 0
            tarnode = connode.inputs['Target in'].links[0].from_node if connode.inputs['Target in'].is_linked else 0
            if geogennode and tarnode:
                simnode['Animation'] = 'Animated'
                vigen(self, li_calc, resapply, geonode, connode, simnode, geogennode, tarnode)
            elif connode.analysismenu != '3':
                simnode['Animation'] = 'Animated' if scene.gfe > 0 or scene.cfe > 0 else 'Static'
                li_calc(self, simnode, connode, geonode, livisimacc(simnode, connode))
        else:
            simnode['Animation'] = 'Animated' if scene.gfe > 0 or scene.cfe > 0 else 'Static'
            scene.fs = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_start
            scene.fe = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_end
            li_calc(self, simnode, connode, geonode, livisimacc(simnode, connode))
        scene.vi_display = 1 if connode.analysismenu != '3' or connode.bl_label != 'LiVi CBDM' else 0  
        context.scene.fe = framerange(context.scene, simnode['Animation'])[-1]
        (scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel) = (0, 1, 1, 0, 0, 0) if connode.bl_label == 'LiVi Compliance'  else (0, 1, 0, 0, 0, 0)
        context.scene.resnode = simnode.name
        context.scene.restree = self.nodeid.split('@')[1]
        return {'FINISHED'}

class VIEW3D_OT_LiDisplay(bpy.types.Operator):
    bl_idname = "view3d.lidisplay"
    bl_label = "Radiance Results Display"
    bl_description = "Display the results on the sensor surfaces"
    bl_register = True
    bl_undo = True

    _handle = None
    disp =  bpy.props.IntProperty(default = 1)
    
    def modal(self, context, event):
        if (context.scene.li_disp_panel < 2 and context.scene.ss_disp_panel < 2) or self.disp != context.scene.li_disp_count:            
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_leg, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_pointres, 'WINDOW')
            if context.scene.get('LiViContext') == 'LiVi Compliance':
                try:
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle_comp, 'WINDOW')
                except:
                    pass
                context.scene.li_compliance = 0
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):        
        scene = context.scene 
        scene.li_disp_count += 1
        self.disp = scene.li_disp_count
        simnode = bpy.data.node_groups[scene.restree].nodes[scene.resnode]
        (connode, geonode) = (0, 0) if simnode.bl_label == 'VI Shadow Study' else (simnode.export(self.bl_label))
        li_display(simnode, connode, geonode)
        scene.li_disp_panel, scene.ss_disp_panel = 2, 2
        self._handle_pointres = bpy.types.SpaceView3D.draw_handler_add(linumdisplay, (self, context, simnode, connode, geonode), 'WINDOW', 'POST_PIXEL')
        self._handle_leg = bpy.types.SpaceView3D.draw_handler_add(li3D_legend, (self, context, simnode, connode, geonode), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        if context.scene.get('LiViContext') == 'LiVi Compliance':
            self._handle_comp = bpy.types.SpaceView3D.draw_handler_add(li_compliance, (self, context, connode), 'WINDOW', 'POST_PIXEL')        
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
        lamp['ies_name'] = self.filepath if " " not in self.filepath else self.report({'ERROR'}, "There is a space either in the IES filename or directory location. Rename or move the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_ESOSelect(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "node.esoselect"
    bl_label = "Select EnVi results file"
    bl_description = "Select the EnVi results file to process"
    filename = ""
    filename_ext = ".eso"
    filter_glob = bpy.props.StringProperty(default="*.eso", options={'HIDDEN'})
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()
    
    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Open an eso results file with the file browser", icon='WORLD_DATA')

    def execute(self, context):
        bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].resfilename = self.filepath
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_IDFSelect(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "node.idfselect"
    bl_label = "Select EnergyPlus input file"
    bl_description = "Select the EnVi input file to process"
    filename = ""
    filename_ext = ".idf"
    filter_glob = bpy.props.StringProperty(default="*.idf", options={'HIDDEN'})
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Open an idf input file with the file browser", icon='WORLD_DATA')

    def execute(self, context):
        bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].idffilename = self.filepath
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

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

        for file in ascfiles:
            with open(file, 'r') as ascfile:
                lines = ascfile.readlines()
                (vpos, faces) = [[], []] if node.splitmesh else [vpos, faces]
                xy = [eval(lines[i].split()[1]) for i in (2, 3)]
                [ostartx, ostarty] = xy
                [mstartx, mstarty] = [0, 0] if node.splitmesh else xy
                [cols, rows, size, nodat] = [eval(lines[i].split()[1]) for i in (0, 1, 4, 5)]
                vpos += [(mstartx + (size * ci), mstarty + (size * (rows - ri)), (float(h), 0)[h == nodat]) for ri, height in enumerate([line.split() for line in lines[6:]]) for ci, h in enumerate(height)] 
                faces += [(i, i+1, i+rows + 1, i+rows) for i in range((vlen, 0)[node.splitmesh], len(vpos)-cols) if (i+1)%cols]
                vlen += cols*rows
        
                if node.splitmesh or file == ascfiles[-1]:  
                    (basename, vpos) = (file.split(os.sep)[-1].split('.')[0], vpos) if node.splitmesh else ('Terrain', [(v[0] - minstartx, v[1] - minstarty, v[2]) for v in vpos])
                    me = bpy.data.meshes.new("{} mesh".format(basename)) 
                    me.from_pydata(vpos,[],faces)
                    me.update(calc_edges=True)
                    dir(me)
                    ob = bpy.data.objects.new(basename, me)
                    ob.location = (ostartx - minstartx, ostarty - minstarty, 0) if node.splitmesh else (0, 0, 0)   # position object at 3d-cursor
                    bpy.context.scene.objects.link(ob) 
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
        resstring, reslist = '', [['Month'] + resnode['resdict']['Month']] + [['Day'] + resnode['resdict']['Day']] + [['Hour'] + resnode['resdict']['Hour']] + resnode['allresdict'].values()
        for rline in zip(*reslist):
            for r in rline:
                resstring += '{},'.format(r)
            resstring += '\n'
        with open(self.filepath, 'w') as csvfile:
            csvfile.write(resstring)
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
        viparams(scene)
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        pregeo(self)
        node.export()
        node.outputs[0].hide = False
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
        viparams(scene)
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        locnode = node.inputs['Location in'].links[0].from_node
        if bpy.data.filepath:
            if bpy.context.active_object and not bpy.context.active_object.hide:
                if bpy.context.active_object.type == 'MESH':
                    bpy.ops.object.mode_set(mode = 'OBJECT')
            if " " not in scene['viparams']['filedir'] and " " not in scene['viparams']['filename']:
                enpolymatexport(self, node, locnode, envi_mats, envi_cons)
                node.bl_label = node.bl_label[1:] if node.bl_label[0] == '*' else node.bl_label
                node.exported = True
                node.outputs['Context out'].hide = False
            elif " " in str(node.filedir):
                self.report({'ERROR'},"The directory path containing the Blender file has a space in it.")
                return {'FINISHED'}
            elif " " in str(node.filename):
                self.report({'ERROR'},"The Blender filename has a space in it.")
                return {'FINISHED'}
            node.export()
            return {'FINISHED'}
        else:
            self.report({'ERROR'},"Save the Blender file before exporting")
            return {'FINISHED'}

class NODE_OT_EnSim(bpy.types.Operator, io_utils.ExportHelper):
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
                        for line in [line for line in resfile.readlines()[::-1] if line.split(',')[0] == '2' and len(line.split(',')) == 9]:  
                            self.simnode.run = int(100 * int(line.split(',')[1])/(self.simnode.dedoy - self.simnode.dsdoy))
                            break
                    return {'RUNNING_MODAL'}
                except:
                    return {'RUNNING_MODAL'} 
            else:
                for fname in [fname for fname in os.listdir('.') if fname.split(".")[0] == self.simnode.resname]:                
                    os.remove(os.path.join(scene['viparams']['newdir'], fname))
                
                nfns = [fname for fname in os.listdir('.') if fname.split(".")[0] == "eplusout"]
                for fname in nfns:
                    rename(os.path.join(scene['viparams']['newdir'], fname), os.path.join(scene['viparams']['newdir'],fname.replace("eplusout", self.simnode.resname)))

                if self.simnode.resname+".err" not in [im.name for im in bpy.data.texts]:
                    bpy.data.texts.load(os.path.join(scene['viparams']['newdir'], self.simnode.resname+".err"))

                if 'EnergyPlus Terminated--Error(s) Detected' in self.esimrun.stderr.read().decode() or not [f for f in nfns if f.split(".")[1] == "eso"]:
                    errtext = "There is no results file. Check you have selected results outputs and that there are no errors in the .err file in the Blender text editor." if not [f for f in nfns if f.split(".")[1] == "eso"] else "There was an error in the input IDF file. Check the *.err file in Blender's text editor."
                    self.report({'ERROR'}, errtext)
                    nodecolour(self.simnode, 0)
                    self.simnode.run = -1
                    return {'CANCELLED'}
                else:
                    self.simnode.run = -1
                    nodecolour(self.simnode, 0)
                    processf(self, self.simnode)
                    self.report({'INFO'}, "Calculation is finished.") 
                    if self.simnode.outputs[0].links:
                        socket1, socket2  = self.simnode.outputs[0], self.simnode.outputs[0].links[0].to_socket
                        bpy.data.node_groups[self.nodeid.split('@')[1]].links.remove(self.simnode.outputs[0].links[0])
                        bpy.data.node_groups[self.nodeid.split('@')[1]].links.new(socket1, socket2)
                    viparams(scene)
                    scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 0, 2, 0, 0, 0, 0                    
                    return {'FINISHED'}
        else:
            return {'PASS_THROUGH'}
            
    def invoke(self, context, event):
        scene = context.scene
        wm = context.window_manager
        self._timer = wm.event_timer_add(1, context.window)
        wm.modal_handler_add(self)
        self.simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        self.connode = self.simnode.inputs['Context in'].links[0].from_node
        self.simnode.resfilename = os.path.join(scene['viparams']['newdir'], self.simnode.resname+'.eso')
        self.simnode.dsdoy, self.simnode.dedoy, self.simnode.run = self.connode.sdoy, self.connode.edoy, 0 # (locnode.startmonthnode.sdoy       
        os.chdir(scene['viparams']['newdir'])
        esimcmd = "EnergyPlus in.idf in.epw" 
        self.esimrun = Popen(esimcmd.split(), stdout = PIPE, stderr = PIPE)
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
        Sdate = dt.fromordinal(dt(dt.now().year, 1, 1).toordinal() + node['Start'] -1) + datetime.timedelta(hours = node.dsh - 1)
        Edate = dt.fromordinal(dt(dt.now().year, 1, 1).toordinal() + node['End'] -1 ) + datetime.timedelta(hours = node.deh - 1)
        innodes = list(OrderedDict.fromkeys([inputs.links[0].from_node for inputs in node.inputs if inputs.links]))
        if not mp:
            self.report({'ERROR'},"Matplotlib cannot be found by the Python installation used by Blender")
            return {'CANCELLED'}
        chart_disp(plt, node, innodes, Sdate, Edate)
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
        solringnum, sd, numpos, ordinals = 0, 100, {}, []
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        node.export()
        scene, scene.resnode, scene.restree = context.scene, node.name, self.nodeid.split('@')[1]
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 1, 0, 0, 0, 0, 0
        bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)
        matdict = {'SolEquoRings': (1, 0, 0), 'HourRings': (1, 1, 0), 'SPBase': (1, 1, 1), 'Sun': (1, 1, 1)}
        for mat in [mat for mat in matdict.items() if mat[0] not in bpy.data.materials]:
            bpy.data.materials.new(mat[0])
            bpy.data.materials[mat[0]].diffuse_color = mat[1]
            
        if 'SUN' in [ob.data.type for ob in context.scene.objects if ob.data == 'LAMP' and ob.hide == False]:
            [ob.data.type for ob in context.scene.objects if ob.data == 'LAMP' and ob.data.type == 'SUN'][0]['VIType'] = 'Sun'
        elif 'Sun' not in [ob.get('VIType') for ob in context.scene.objects]:
            bpy.ops.object.lamp_add(type = "SUN")
            sun = context.active_object
            sun['VIType'] = 'Sun'
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

        for doy in range(0, 363):
            if (doy-4)%7 == 0:
                for hour in range(1, 25):
                    ([solalt, solazi]) = solarPosition(doy, hour, scene['latitude'], scene['longitude'])[2:]
                    spathmesh.vertices.add(1)
                    spathmesh.vertices[-1].co = [-(sd-(sd-(sd*cos(solalt))))*sin(solazi), -(sd-(sd-(sd*cos(solalt))))*cos(solazi), sd*sin(solalt)]

        for v in range(24, len(spathmesh.vertices)):
            if spathmesh.vertices[v].co.z > 0 or spathmesh.vertices[v - 24].co.z > 0:
                spathmesh.edges.add(1)
                spathmesh.edges[-1].vertices[0:2] = (v, v - 24)
            if v in range(1224, 1248):
                if spathmesh.vertices[v].co.z > 0 or spathmesh.vertices[v - 1224].co.z > 0:
                    spathmesh.edges.add(1)
                    spathmesh.edges[-1].vertices[0:2] = (v, v - 1224)

        for doy in (79, 172, 355):
            for hour in range(1, 25):
                ([solalt, solazi]) = solarPosition(doy, hour, scene['latitude'], scene['longitude'])[2:]
                spathmesh.vertices.add(1)
                spathmesh.vertices[-1].co = [-(sd-(sd-(sd*cos(solalt))))*sin(solazi), -(sd-(sd-(sd*cos(solalt))))*cos(solazi), sd*sin(solalt)]
                if spathmesh.vertices[-1].co.z >= 0 and doy in (172, 355):
                    numpos['{}-{}'.format(doy, hour)] = spathmesh.vertices[-1].co[:]
                if hour != 1:
                    if spathmesh.vertices[-2].co.z > 0 or spathmesh.vertices[-1].co.z > 0:
                        spathmesh.edges.add(1)
                        solringnum += 1
                        spathmesh.edges[-1].vertices = (spathmesh.vertices[-2].index, spathmesh.vertices[-1].index)
                if hour == 24:
                    if spathmesh.vertices[-24].co.z > 0 or spathmesh.vertices[-1].co.z > 0:
                        spathmesh.edges.add(1)
                        solringnum += 1
                        spathmesh.edges[-1].vertices = (spathmesh.vertices[-24].index, spathmesh.vertices[-1].index)

        for edge in spathmesh.edges:
            intersect = mathutils.geometry.intersect_line_plane(spathmesh.vertices[edge.vertices[0]].co, spathmesh.vertices[edge.vertices[1]].co, mathutils.Vector((0,0,0)), mathutils.Vector((0,0,1)))
            for vert in [vert for vert in (spathmesh.vertices[edge.vertices[0]], spathmesh.vertices[edge.vertices[1]]) if vert.co.z < 0]:
                vert.co = intersect

        bpy.ops.object.convert(target='CURVE')
        spathob.data.bevel_depth, spathob.data.bevel_resolution = 0.08, 6
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
        bpy.context.tool_settings.mesh_select_mode = [True, False, False]
        bpy.ops.object.material_slot_assign()
        bpy.ops.object.material_slot_add()
        spathob.material_slots[-1].material = bpy.data.materials['SPBase']
        spathob.active_material_index = 2

        for i in range(1, 6):
            bpy.ops.mesh.primitive_torus_add(major_radius=i*sd*0.2, minor_radius=i*0.1*0.2, major_segments=64, minor_segments=8, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0))
            bpy.ops.object.material_slot_assign()
        for j in range(5):
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=(2-j%2)*0.04, depth=2.05*sd, end_fill_type='NGON', view_align=False, location=(0.0, 0.0, 0.0), rotation=(pi/2, 0.0, j*pi/4))
            bpy.ops.object.material_slot_assign()
        bpy.ops.object.mode_set(mode='OBJECT')

        for c in range(8):
            bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=((-4, -8)[c%2], sd*1.025, 0.0), rotation=(0.0, 0.0, 0.0))
            txt = bpy.context.active_object
            txt.scale, txt.data.extrude, txt.data.body  = (10, 10, 10), 0.1, ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')[c]
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.material_slot_add()
            txt.material_slots[0].material = bpy.data.materials['SPBase']
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            txt.rotation_euler=(0, 0, -c*pi*0.25)
            ordinals.append(txt)

        for o in ordinals:
            o.select = True
        spathob.select = True
        bpy.context.scene.objects.active = spathob
        bpy.ops.object.join()

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
        if context.scene.vi_display == 0 or not context.scene.sp_disp_panel:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_spnum, 'WINDOW')
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        simnode = bpy.data.node_groups[context.scene.restree].nodes[context.scene.resnode]
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
        if not bpy.data.filepath:
            self.report({'ERROR'},"Save the Blender file first")
            return {'CANCELLED'}
        if mp == 1:
            simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
            simnode.export()
            locnode = simnode.inputs['Location in'].links[0].from_node
            scene, scene.resnode, scene.restree = context.scene, simnode.name, self.nodeid.split('@')[1]
            viparams(scene)
            scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 0, 0, 0, 0, 0, 1

            with open(locnode.weather, "r") as epwfile:
                if simnode.startmonth > simnode.endmonth:
                    self.report({'ERROR'},"Start month is later than end month")
                    return {'FINISHED'}
                else:
                    wvals = [line.split(",")[20:22] for l, line in enumerate(epwfile.readlines()) if l > 7 and simnode.startmonth <= int(line.split(",")[1]) <= simnode.endmonth]
                    simnode['maxres'], simnode['minres'],  simnode['avres']= max([float(w[1]) for w in wvals]), min([float(w[1]) for w in wvals]), sum([float(w[1]) for w in wvals])/len(wvals)

            awd, aws, (fig, ax) = [float(val[0]) for val in wvals], [float(val[1]) for val in wvals], wr_axes()
            binvals = arange(0,int(ceil(max(aws))),2)
            simnode['nbins'] = len(binvals)

            if simnode.wrtype == '0':
                ax.bar(awd, aws, bins=binvals, normed=True, opening=0.8, edgecolor='white')
            if simnode.wrtype == '1':
                ax.box(awd, aws, bins=binvals, normed=True)
            if simnode.wrtype == '2':
                ax.contourf(awd, aws, bins=binvals, normed=True, cmap=cm.hot)
            if simnode.wrtype == '3':
                ax.contourf(awd, aws, bins=binvals, normed=True, cmap=cm.hot)
                ax.contour(awd, aws, bins=binvals, normed=True, colors='black')
            if simnode.wrtype == '4':
                ax.contour(awd, aws, bins=binvals, normed=True, cmap=cm.hot)

            if str(sys.platform) != 'win32':
                plt.savefig(scene['viparams']['newdir']+'/disp_wind.png', dpi = (150), transparent=False)
                if 'disp_wind.png' not in [im.name for im in bpy.data.images]:
                    bpy.data.images.load(scene['viparams']['newdir']+'/disp_wind.png')
                else:
                    bpy.data.images['disp_wind.png'].filepath = scene['viparams']['newdir']+'/disp_wind.png'
                    bpy.data.images['disp_wind.png'].reload()

            # Below is a workaround for the matplotlib/blender png bug
            else:
                canvas = FigureCanvasAgg(fig)
                canvas.draw()
                pixbuffer, pixels = canvas.buffer_rgba(), []
                [w, h] = [int(d) for d in fig.bbox.bounds[2:]]
                pixarray = numpy.frombuffer(pixbuffer, numpy.uint8)
                pixarray.shape = h, w, 4
                pixels = pixarray[::-1].flatten()/255

                if 'disp_wind.png' not in [im.name for im in bpy.data.images]:
                    wrim = bpy.data.images.new('disp_wind.png', height = h, width = w)
                    wrim.file_format = 'PNG'
                    wrim.filepath = os.path.join(scene['viparams']['newdir'], wrim.name)
#                    wrim.save()
                else:
                    wrim = bpy.data.images['disp_wind.png']
                wrim.pixels = pixels
                wrim.update()
                wrim.save()
                wrim.reload()

            plt.savefig(scene['viparams']['newdir']+'/disp_wind.svg')

            if 'Wind_Plane' not in [ob.get('VIType') for ob in bpy.context.scene.objects]:
                bpy.ops.mesh.primitive_plane_add(enter_editmode=False, location=(0.0, 0.0, 0.0))
                bpy.context.active_object['VIType'] = 'Wind_Plane'
                wind_mat = bpy.data.materials.new('Wind_Rose')
                tex = bpy.data.textures.new(type = 'IMAGE', name = 'Wind_Tex')
                tex.image = bpy.data.images['disp_wind.png']
                wind_mat.texture_slots.add()
                wind_mat.texture_slots[0].texture = tex
                wind_mat.texture_slots[0].use_map_alpha = True
                bpy.context.active_object.name = "Wind_Plane"
                bpy.ops.object.material_slot_add()
                bpy.context.active_object.material_slots[0].material = wind_mat
                bpy.context.active_object.data.uv_textures.new()
                bpy.context.active_object.data.uv_textures[0].data[0].image = bpy.data.images['disp_wind.png']
                bpy.context.active_object.scale = (100, 100, 100)
                wind_mat.use_transparency = False
                wind_mat.transparency_method = 'Z_TRANSPARENCY'
                wind_mat.alpha = 0.0
            bpy.ops.view3d.wrlegdisplay('INVOKE_DEFAULT')
            return {'FINISHED'}
        else:
            self.report({'ERROR'},"There is something wrong with your matplotlib installation")
            return {'FINISHED'}

class VIEW3D_OT_WRLegDisplay(bpy.types.Operator):
    '''Display results legend and stats in the 3D View'''
    bl_idname = "view3d.wrlegdisplay"
    bl_label = "Wind rose legend"
    bl_description = "Display Wind Rose legend"
    bl_register = True
    bl_undo = True

    def modal(self, context, event):
        context.area.tag_redraw()
        if context.scene.vi_display == 0 or context.scene.wr_disp_panel != 1:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_spnum, 'WINDOW')
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        simnode = bpy.data.node_groups[context.scene.restree].nodes[context.scene.resnode]
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
        scene.restree = self.nodeid.split('@')[1]
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 0, 0, 0, 0, 1, 0
        clearscene(scene, self)
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        simnode.export()
        (scene.fs, scene.fe) = (scene.frame_current, scene.frame_current) if simnode.animmenu == 'Static' else (scene.frame_start, scene.frame_end)

        if simnode.starthour > simnode.endhour:
            self.report({'ERROR'},"End hour is before start hour.")
            return{'FINISHED'}
        scene.resnode, direcs, obcalclist, simnode['Animation'] = simnode.name, [], [], simnode.animmenu

        if simnode['Animation'] == 'Static':
            scmaxres, scminres, scavres, scene.fs = [0], [100], [0], scene.frame_current
        else:
            (scmaxres, scminres, scavres) = [[x] * scene.frame_end - scene.frame_start + 1 for x in (0, 100, 0)]

        fdiff =  1 if simnode['Animation'] == 'Static' else scene.frame_end - scene.frame_start + 1
        time = datetime.datetime(datetime.datetime.now().year, simnode.startmonth, 1, simnode.starthour - 1)
        y =  datetime.datetime.now().year if simnode.endmonth >= simnode.startmonth else datetime.datetime.now().year + 1
        endtime = datetime.datetime(y, simnode.endmonth, (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[simnode.endmonth - 1], simnode.endhour - 1)
        interval = datetime.timedelta(hours = modf(simnode.interval)[0], minutes = 60 * modf(simnode.interval)[1])
        while time <= endtime:
            if simnode.starthour <= time.hour <= simnode.endhour:
                beta, phi = solarPosition(time.timetuple().tm_yday, time.hour+time.minute/60, scene['latitude'], scene['longitude'])[2:]
                if beta > 0:
                    direcs.append(mathutils.Vector((-sin(phi), -cos(phi), tan(beta))))
            time += interval
        for ob in [ob for ob in scene.objects if ob.type == 'MESH' and not ob.hide]:
            if li_calcob(ob, 'shadow'):
                obavres, shadfaces, shadcentres = [0] * (fdiff), [[] for f in range(fdiff)], [[] for f in range(fdiff)]
                [obsumarea, obmaxres, obminres] = [[0 for f in range(fdiff)] for x in range(3)]
                obcalclist.append(ob)
                scene.objects.active, obm = ob, ob.matrix_world
                ob['cfaces'] = [face.index for face in ob.data.polygons if ob.data.materials[face.material_index].vi_shadow]
                
                while ob.data.vertex_colors:
                    bpy.ops.mesh.vertex_color_remove()
                for findex, frame in enumerate(range(scene.fs, scene.fe + 1)):
                    scene.frame_set(frame)
                    bpy.ops.mesh.vertex_color_add()
                    ob.data.vertex_colors[-1].name = '{}'.format(frame)
                    vertexColour = ob.data.vertex_colors[-1]
                    obsumarea[findex] = sum([face.area for face in ob.data.polygons if ob.data.materials[face.material_index].vi_shadow])
                    shadfaces = [face for face in ob.data.polygons if ob.data.materials[face.material_index].vi_shadow]
                    for face in shadfaces:
                        for li in face.loop_indices:
                            vertexColour.data[li].color = (1, 1, 1)
                    if simnode.cpoint == '0':  
                        ob['cverts'] = []
                        shadcentres[findex] = [[obm*mathutils.Vector((face.center)) + 0.05*face.normal, obm*mathutils.Vector((face.center)), 1] for face in shadfaces]                    
                        for fa, face in enumerate(shadfaces):
                            for direc in direcs:
                                if bpy.data.scenes[0].ray_cast(shadcentres[findex][fa][0], shadcentres[findex][fa][1] + 10000*direc)[0]:
                                    shadcentres[findex][fa][2] -= 1/(len(direcs))
                            if shadcentres[findex][fa][2] < 1:
                                for li in face.loop_indices:
                                    vertexColour.data[li].color = [shadcentres[findex][fa][2]]*3
                            obavres[findex] += face.area * 100 * (shadcentres[findex][fa][2])/obsumarea[findex]
                    else:
                        csfvi = [item for sublist in [face.vertices[:] for face in ob.data.polygons if ob.data.materials[face.material_index].vi_shadow] for item in sublist]
                        ob['cverts'] = [v for (i,v) in enumerate(csfvi) if v not in csfvi[0:i]]
                        shadverts = [ob.data.vertices[i] for i in ob['cverts']]
                        shadcentres[findex] = [[obm*mathutils.Vector((v.co)) + 0.05*v.normal, obm*mathutils.Vector((v.co)), 1] for v in shadverts]
                        cvtup = tuple(ob['cverts'])
                        
                        for vi in range(len(ob['cverts'])):
                            for direc in direcs:
                                if bpy.data.scenes[0].ray_cast(shadcentres[findex][vi][0], shadcentres[findex][vi][1] + 10000*direc)[0]:
                                    shadcentres[findex][vi][2] -= 1/(len(direcs))
                            
                            for fa, face in enumerate(shadfaces):
                                for li in face.loop_indices:
                                    v = ob.data.loops[li].vertex_index
                                    if v in cvtup:
                                        col_i = cvtup.index(v)                                        
                                        if shadcentres[findex][col_i][2] < 1:
                                            vertexColour.data[li].color = [shadcentres[findex][col_i][2]]*3
                        
                        obavres[findex] = sum([vertarea(ob, ob.data.vertices[vi]) * 100 * (shadcentres[findex][i][2]) for i, vi in enumerate(ob['cverts'])])/obsumarea[findex]
                    
                    obmaxres[findex] = 100* (max([sh[2] for sh in shadcentres[findex]]))
                    obminres[findex] = 100* (min([sh[2] for sh in shadcentres[findex]]))

                    scmaxres[findex] = obmaxres[findex] if obmaxres[findex] > scmaxres[findex] else scmaxres[findex]
                    scminres[findex] = obminres[findex] if obminres[findex] < scminres[findex] else scminres[findex]
                    scavres[findex] += obavres[findex]

                ob['omax'] = {str(f):obmaxres[f - scene.fs] for f in framerange(scene, simnode.animmenu)}
                ob['omin'] = {str(f):obminres[f - scene.fs] for f in framerange(scene, simnode.animmenu)}
                ob['oave'] = {str(f):obavres[f - scene.fs] for f in framerange(scene, simnode.animmenu)}
                ob['oreslist'] = {str(f):[100*sh[2] for sh in shadcentres[f - scene.fs]] for f in framerange(scene, simnode.animmenu)}

        vcframe('', scene, obcalclist, simnode.animmenu)
        try:
#            simnode['maxres'], simnode['minres'], simnode['avres'] = scmaxres, scminres, [scavres[f]/len([ob for ob in scene.objects if ob.licalc]) for f in range(fdiff)]
            simnode['maxres'], simnode['minres'], simnode['avres'] = [100]*fdiff, [0]*fdiff, [scavres[f]/len([ob for ob in scene.objects if ob.licalc]) for f in range(fdiff)]
        except ZeroDivisionError:
            self.report({'ERROR'},"No objects have a VI Shadow material attached.")

        scene.frame_set(scene.fs)
        simnode.bl_label = simnode.bl_label[1:] if simnode.bl_label[0] == '*' else simnode.bl_label
        return {'FINISHED'}
