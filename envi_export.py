import bpy, os, itertools, subprocess, datetime, sys, nodeitems_utils, mathutils
from nodeitems_utils import  NodeItem
from .vi_func import epentry, objvol, ceilheight, selobj, triarea, boundpoly
from . import vi_node
dtdf = datetime.date.fromordinal
#from subprocess import PIPE, Popen, STDOUT
#from math import pi, sin, cos, acos, asin
s = 70

def enpolymatexport(exp_op, node, locnode, em, ec):
#    daytypes = ("AllDays", "Weekdays", "Weekends")
#    lineends = (",\n", ";\n\n", ",\n", ";\n\n")
    scene = bpy.context.scene
    for scene in bpy.data.scenes:
        scene.update()
    en_epw = open(locnode.weather, "r")
    en_idf = open(scene['viparams']['idf_file'], 'w')
    node.sdoy = datetime.datetime(datetime.datetime.now().year, locnode.startmonth, 1).timetuple().tm_yday
    node.edoy = (datetime.date(datetime.datetime.now().year, locnode.endmonth + (1, -11)[locnode.endmonth == 12], 1) - datetime.timedelta(days = 1)).timetuple().tm_yday
    enng = [ng for ng in bpy.data.node_groups if 'EnVi Network' in ng.bl_label][0] if [ng for ng in bpy.data.node_groups if 'EnVi Network' in ng.bl_label] else 0

    en_idf.write("!- Blender -> EnergyPlus\n!- Using the EnVi export scripts\n!- Author: Ryan Southall\n!- Date: {}\n\nVERSION,8.1.0;\n\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    
    params = ('Name', 'North Axis (deg)', 'Terrain', 'Loads Convergence Tolerance Value', 'Temperature Convergence Tolerance Value (deltaC)',
              'Solar Distribution', 'Maximum Number of Warmup Days(from MLC TCM)')
    paramvs = (node.loc, '0.00', ("City", "Urban", "Suburbs", "Country", "Ocean,")[int(node.terrain)], '0.004', '0.4', 'FullExteriorWithReflections', '15')
    en_idf.write(epentry('Building', params, paramvs))
    params = ('Time Step in Hours', 'Algorithm', 'Algorithm', 'Algorithm', '(default frequency of calculation)', 'no zone sizing, system sizing, plant sizing, no design day, use weather file')
    paramvs = ('Timestep, {}'.format(node.timesteps), 'SurfaceConvectionAlgorithm:Inside, TARP', 'SurfaceConvectionAlgorithm:Outside, TARP', 'HeatBalanceAlgorithm, ConductionTransferFunction',
               'ShadowCalculation, AverageOverDaysInFrequency, 10', 'SimulationControl, No,No,No,No,Yes')

    for ppair in zip(params, paramvs):
        en_idf.write(epentry('', [ppair[0]], [ppair[1]]) + ('', '\n\n')[ppair[0] == params[-1]])

    params = ('Name', 'Begin Month', 'Begin Day', 'End Month', 'End Day', 'Day of Week for Start Day', 'Use Weather File Holidays and Special Days', 'Use Weather File Daylight Saving Period',\
    'Apply Weekend Holiday Rule', 'Use Weather File Rain Indicators', 'Use Weather File Snow Indicators', 'Number of Times Runperiod to be Repeated')
    paramvs = (node.loc, locnode.startmonth, '1', locnode.endmonth, ((datetime.date(datetime.datetime.now().year, locnode.endmonth + (1, -11)[locnode.endmonth == 12], 1) - datetime.timedelta(days = 1)).day), "UseWeatherFile", "Yes", "Yes", "No", "Yes", "Yes", "1")
    en_idf.write(epentry('RunPeriod', params, paramvs))

#    en_idf.write("Site:Location,\n")
#    en_idf.write(es.wea.split("/")[-1].strip('.epw')+",   !- LocationName\n")
#    en_idf.write(str(scene.envi_export_latitude)+",   !- Latitude {deg}\n")
#    en_idf.write(str(scene.envi_export_longitude)+",   !- Longitude {deg} [check this value]\n")
#    en_idf.write(str(scene.envi_export_meridian)+",   !- TimeZone {hr} [supplied by user]\n")
#    en_idf.write("10.0;   !- Elevation {m} [supplied by user]\n\n")
    for line in en_epw.readlines():
        if line.split(",")[0].upper() == "GROUND TEMPERATURES":
            gtline = line.split(",")
            gt = []
            for gtn in range(int(gtline[1])):
                gt.append((gtline[2+gtn*16], [g.strip("\n") for g in gtline[6+gtn*16:18+gtn*16]]))
                if float(gt[gtn][0]) > 0.0 and float(gt[gtn][0]) <= 1:
                    en_idf.write("Site:GroundTemperature:BuildingSurface, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {};\n".format(*gt[gtn][1][:]))
                elif float(gt[gtn][0]) == 0.5:
                    en_idf.write("Site:GroundTemperature:Shallow, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {};\n".format(*gt[gtn][1][:]))
                elif float(gt[gtn][0]) > 3.5 and float(gt[gtn][0]) < 4.5:
                    en_idf.write("Site:GroundTemperature:Deep, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {};\n".format(*gt[gtn][1][:]))
            en_idf.write("\n")
            break
    en_epw.close()

    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: MATERIAL & CONSTRUCTIONS ===========\n\n")
    matcount, matname, namelist = [], [], []
#    customcount = []
    if 'Window' in [mat.envi_con_type for mat in bpy.data.materials] or 'Door' in [mat.envi_con_type for mat in bpy.data.materials]:
        params = ('Name', 'Roughness', 'Thickness (m)', 'Conductivity (W/m-K)', 'Density (kg/m3)', 'Specific Heat (J/kg-K)', 'Thermal Absorptance', 'Solar Absorptance', 'Visible Absorptance', 'Name', 'Outside Layer') 
        paramvs = ('Wood frame', 'Rough', '0.12', '0.1', '1400.00', '1000', '0.9', '0.6', '0.6', 'Frame', 'Wood frame')
        en_idf.write(epentry('Material', params[:-2], paramvs[:-2]))
        en_idf.write(epentry('Construction', params[-2:], paramvs[-2:]))

    for mat in [mat for mat in bpy.data.materials if mat.envi_export == True and mat.envi_con_type != "None"]:
        conlist = []
        if mat.envi_con_makeup == '0' and mat.envi_con_type not in ('None', 'Shading', 'Aperture'):
            thicklist = (mat.envi_export_lo_thi, mat.envi_export_l1_thi, mat.envi_export_l2_thi, mat.envi_export_l3_thi, mat.envi_export_l4_thi)
            conname = (mat.envi_export_wallconlist, mat.envi_export_roofconlist, mat.envi_export_floorconlist, mat.envi_export_doorconlist, mat.envi_export_glazeconlist)[("Wall", "Roof", "Floor", "Door", "Window").index(mat.envi_con_type)]
            mats = (ec.wall_con, ec.roof_con, ec.floor_con, ec.door_con, ec.glaze_con)[("Wall", "Roof", "Floor", "Door", "Window").index(mat.envi_con_type)][conname]
            for pm, presetmat in enumerate(mats):
                if em.namedict.get(presetmat) == None:
                    em.namedict[presetmat] = 0
                    em.thickdict[presetmat] = [thicklist[pm]/1000]
                else:
                    em.namedict[presetmat] = em.namedict[presetmat] + 1
                    em.thickdict[presetmat].append(thicklist[pm]/1000)
                if mat.envi_con_type in ('Wall', 'Floor', 'Roof', 'Door') and presetmat not in em.gas_dat:
                    params = [str(mat)+(",", ",", ",", ",", ",", ",", ";", ",")[x] for x, mat in enumerate(em.matdat[presetmat])]
                    em.omat_write(en_idf, presetmat+"-"+str(em.namedict[presetmat]), params, str(thicklist[pm]/1000))
                elif presetmat in em.gas_dat:
                    params = em.matdat[presetmat][2]+';'
                    em.amat_write(en_idf, presetmat+"-"+str(em.namedict[presetmat]), params)
                elif mat.envi_con_type =='Window' and em.matdat[presetmat][0] == 'Glazing':
                    params = [str(mat)+(",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",",";")[x] for x, mat in enumerate(em.matdat[presetmat])]
                    em.tmat_write(en_idf, presetmat+"-"+str(em.namedict[presetmat]), params, str(thicklist[pm]/1000))
                elif mat.envi_con_type =='Window' and em.matdat[presetmat][0] == 'Gas':
                    params = [str(mat)+( ",", ",", ",")[x] for x, mat in enumerate(em.matdat[presetmat])]
                    em.gmat_write(en_idf, presetmat+"-"+str(em.namedict[presetmat]), params, str(thicklist[pm]/1000))
                matname.append((presetmat)+'-'+str(matcount.count(presetmat)))
                matcount.append(presetmat)

            namelist.append(conname)
            ec.con_write(en_idf, mat.envi_con_type, conname, str(namelist.count(conname)-1), mat.name)

        elif mat.envi_con_makeup == '1' and mat.envi_con_type not in ('None', 'Shading', 'Aperture'):
            thicklist = (mat.envi_export_lo_thi, mat.envi_export_l1_thi, mat.envi_export_l2_thi, mat.envi_export_l3_thi, mat.envi_export_l4_thi)
            conname = mat.name
            
            for l, layer in enumerate([i for i in itertools.takewhile(lambda x: x != "0", (mat.envi_layero, mat.envi_layer1, mat.envi_layer2, mat.envi_layer3, mat.envi_layer4))]):
                if layer == "1" and mat.envi_con_type in ("Wall", "Floor", "Roof"):
                    mats = ((mat.envi_export_bricklist_lo, mat.envi_export_claddinglist_lo, mat.envi_export_concretelist_lo, mat.envi_export_metallist_lo, mat.envi_export_stonelist_lo, mat.envi_export_woodlist_lo, mat.envi_export_gaslist_lo, mat.envi_export_insulationlist_lo), \
                    (mat.envi_export_bricklist_l1, mat.envi_export_claddinglist_l1, mat.envi_export_concretelist_l1, mat.envi_export_metallist_l1, mat.envi_export_stonelist_l1, mat.envi_export_woodlist_l1, mat.envi_export_gaslist_l1, mat.envi_export_insulationlist_l1), \
                    (mat.envi_export_bricklist_l2, mat.envi_export_claddinglist_l2, mat.envi_export_concretelist_l2, mat.envi_export_metallist_l2, mat.envi_export_stonelist_l2, mat.envi_export_woodlist_l2, mat.envi_export_gaslist_l2, mat.envi_export_insulationlist_l2), \
                    (mat.envi_export_bricklist_l3, mat.envi_export_claddinglist_l3, mat.envi_export_concretelist_l3, mat.envi_export_metallist_l3, mat.envi_export_stonelist_l3, mat.envi_export_woodlist_l3, mat.envi_export_gaslist_l3, mat.envi_export_insulationlist_l3), \
                    (mat.envi_export_bricklist_l4, mat.envi_export_claddinglist_l4, mat.envi_export_concretelist_l4, mat.envi_export_metallist_l4, mat.envi_export_stonelist_l4, mat.envi_export_woodlist_l4, mat.envi_export_gaslist_l4, mat.envi_export_insulationlist_l4))\
                    [l][int((mat.envi_layeroto, mat.envi_layer1to, mat.envi_layer2to, mat.envi_layer3to, mat.envi_layer4to)[l])]

                    if mats not in em.gas_dat:
                        params = [str(mat)+(",", ",", ",", ",", ",", ",", ";", ",")[x] for x, mat in enumerate(em.matdat[mats])]
                        em.omat_write(en_idf, '{}-{}'.format(mats, matcount.count(mats)), params, str(thicklist[l]/1000))
                    else:
                        params = [em.matdat[mats][2]+';']
                        em.amat_write(en_idf, '{}-{}'.format(mats, matcount.count(mats)), params)

                elif layer == "1" and mat.envi_con_type == "Window":
                    mats = ((mat.envi_export_glasslist_lo, mat.envi_export_wgaslist_l1, mat.envi_export_glasslist_l2, mat.envi_export_wgaslist_l3, mat.envi_export_glasslist_l4)[l])
                    if l in (0, 2, 4):
                        params = [str(mat)+(",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",",";")[x] for x, mat in enumerate(em.matdat[mats])]
                        em.tmat_write(en_idf, '{}-{}'.format(mats, matcount.count(mats)), params, str(thicklist[l]/1000))
                    else:
                        params = [str(mat)+( ",", ",", ",")[x] for x, mat in enumerate(em.matdat[mats])]
                        em.gmat_write(en_idf, '{}-{}'.format(mats, matcount.count(mats)), params, str(thicklist[l]/1000))

                elif layer == "2" and mat.envi_con_type in ("Wall", "Floor", "Roof"):
                    mats = (mat.envi_export_lo_name, mat.envi_export_l1_name, mat.envi_export_l2_name, mat.envi_export_l3_name, mat.envi_export_l4_name)[l]
                    params = [str(mat)+(",", ",", ",", ",", ",", ",", ";", ",")[x] for x, mat in enumerate(((mat.envi_export_lo_rough, mat.envi_export_lo_tc, mat.envi_export_lo_rho, mat.envi_export_lo_shc, mat.envi_export_lo_tab, mat.envi_export_lo_sab, mat.envi_export_lo_vab),\
                    (mat.envi_export_l1_rough, mat.envi_export_l1_tc, mat.envi_export_l1_rho, mat.envi_export_l1_shc, mat.envi_export_l1_tab, mat.envi_export_l1_sab, mat.envi_export_l1_vab),\
                    (mat.envi_export_l2_rough, mat.envi_export_l2_tc, mat.envi_export_l2_rho, mat.envi_export_l2_shc, mat.envi_export_l2_tab, mat.envi_export_l2_sab, mat.envi_export_l2_vab),\
                    (mat.envi_export_l3_rough, mat.envi_export_l3_tc, mat.envi_export_l3_rho, mat.envi_export_l3_shc, mat.envi_export_l3_tab, mat.envi_export_l3_sab, mat.envi_export_l3_vab),\
                    (mat.envi_export_l4_rough, mat.envi_export_l4_tc, mat.envi_export_l4_rho, mat.envi_export_l4_shc, mat.envi_export_l4_tab, mat.envi_export_l4_sab, mat.envi_export_l4_vab))[l])]
                    em.omat_write(en_idf, mats+"-"+str(matcount.count(mats)), params, str(thicklist[l]/1000))

                elif layer == "2" and mat.envi_con_type == "Window":
                    mats = (mat.envi_export_lo_name, mat.envi_export_l1_name, mat.envi_export_l2_name, mat.envi_export_l3_name, mat.envi_export_l4_name)[l]
                    if l in (0, 2, 4):
                        params = [str(mat)+(",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",",";")[x] for x, mat in enumerate((("Glazing", mat.envi_export_lo_odt, mat.envi_export_lo_sds, mat.envi_export_lo_thi, mat.envi_export_lo_stn, mat.envi_export_lo_fsn, mat.envi_export_lo_bsn, mat.envi_export_lo_vtn, mat.envi_export_lo_fvrn, mat.envi_export_lo_bvrn, mat.envi_export_lo_itn, mat.envi_export_lo_fie, mat.envi_export_lo_bie, mat.envi_export_lo_tc),"",\
                    ("Glazing",  mat.envi_export_l2_odt, mat.envi_export_l2_sds, mat.envi_export_l2_thi, mat.envi_export_l2_stn, mat.envi_export_l2_fsn, mat.envi_export_l2_bsn, mat.envi_export_l2_vtn, mat.envi_export_l2_fvrn, mat.envi_export_l2_bvrn, mat.envi_export_l2_itn, mat.envi_export_l2_fie, mat.envi_export_l2_bie, mat.envi_export_l2_tc), "",\
                    ("Glazing",  mat.envi_export_l4_odt, mat.envi_export_l4_sds, mat.envi_export_l4_thi, mat.envi_export_l4_stn, mat.envi_export_l4_fsn, mat.envi_export_l4_bsn, mat.envi_export_l4_vtn, mat.envi_export_l4_fvrn, mat.envi_export_l4_bvrn, mat.envi_export_l4_itn, mat.envi_export_l4_fie, mat.envi_export_l4_bie, mat.envi_export_l4_tc))[l])]
                        em.tmat_write(en_idf, mats+"-"+str(matcount.count(mats)), params, str(thicklist[l]/1000))
                    else:
                        params = [str(mat)+( ",", ",", ",")[x] for x, mat in enumerate(("", ("Gas", mat.envi_export_wgaslist_l1), "", ("Gas", mat.envi_export_wgaslist_l1))[l])]
                        em.gmat_write(en_idf, mats+"-"+str(matcount.count(mats)), params, str(thicklist[l]/1000))

                conlist.append((mats)+'-'+str(matcount.count(mats)))
                matname.append((mats)+'-'+str(matcount.count(mats)))
                matcount.append(mats)
            
            params, paramvs = ['Name'],  [mat.name]
            for i, mn in enumerate(conlist):
                params.append('Layer {}'.format(i))
                paramvs.append(mn)
            en_idf.write(epentry('Construction', params, paramvs))

    em.namedict = {}
    em.thickdict = {}

    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: ZONES ===========\n\n")
    for obj in [obj for obj in bpy.context.scene.objects if obj.layers[1] == True and obj.envi_type == '1']:
        if obj.type == 'MESH':
            en_idf.write("Zone,\n    {0:{width}}!- Name\n".format(obj.name+",", width = s - 4) +
            "    0,                                                                !- Direction of Relative North (deg)\n" +
            "    0,                                                                !- X Origin (m)\n" +
            "    0,                                                                !- Y Origin (m)\n" +
            "    0,                                                                !- Z Origin (m)\n" +
            "    1,                                                                !- Type\n" +
            "    1,                                                                !- Multiplier\n" +
            "    {0:{width}}!- Ceiling Height (m)\n".format("{:.3f}".format(ceilheight(obj, [])) + ",", width = s - 4) +
            "    {0:{width}}!- Volume (m3)\n".format("{:.2f}".format(objvol('', obj)) + ",", width = s - 4) +
            "    autocalculate,                                                    !- Floor Area (m2)\n" +
            "    TARP,                                                             !- Zone Inside Convection Algorithm\n"+
            "    TARP,                                                             !- Zone Outside Convection Algorithm\n"+
            "    Yes;                                                              !- Part of Total Floor Area\n\n")


    en_idf.write("GlobalGeometryRules,\n" +
        "    UpperRightCorner,                                                  !- Starting Vertex Position\n" +
        "    Counterclockwise,                                                 !- Vertex Entry Direction\n" +
        "    World;                                                            !- Coordinate System\n\n")

    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: SURFACE DEFINITIONS ===========\n\n")

    wfrparams = ['Name', 'Surface Type', 'Construction Name', 'Zone Name', 'Outside Boundary Condition', 'Outside Boundary Condition Object', 'Sun Exposure', 'Wind Exposure', 'View Factor to Ground', 'Number of Vertices']
    hcparams = ('Name', 'Setpoint Temperature Schedule Name', 'Setpoint Temperature Schedule Name')
    spparams = ('Name', 'Setpoint Temperature Schedule Name')
#    cspparams = ('Name', 'Setpoint Temperature Schedule Name')
    
    for obj in [obj for obj in bpy.data.objects if obj.layers[1] and obj.type == 'MESH' and obj.envi_type != '0']:
        obm, odv = obj.matrix_world, obj.data.vertices
        obj["floorarea"] = sum([triarea(obj, face) for face in obj.data.polygons if obj.data.materials[face.material_index].envi_con_type =='floor'])
        for poly in obj.data.polygons:
            mat = obj.data.materials[poly.material_index]
            (obc, obco, se, we) = boundpoly(obj, mat, poly)

            if mat.envi_con_type in ('Wall', "Floor", "Roof") and mat.envi_con_makeup != "2":
                params = list(wfrparams)
                paramvs = ['{}_{}'.format(obj.name, poly.index), mat.envi_con_type, mat.name, obj.name, obc, obco, se, we, 'autocalculate', len(poly.vertices)]
                for vert in poly.vertices:
                    params.append("X,Y,Z ==> Vertex {} (m)".format(vert))
                    paramvs.append("  {0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}".format(obm * odv[vert].co))
                en_idf.write(epentry('BuildingSurface:Detailed', params, paramvs))

                if mat.envi_con_type == "Floor":
                    obj["floorarea"] = obj["floorarea"] + poly.area

            elif  mat.envi_con_type in ('Door', 'Window'):
                xav, yav, zav = obm*mathutils.Vector(poly.center)
                params = list(wfrparams)
                paramvs = ['{}_{}'.format(obj.name, poly.index), 'Wall', 'Frame', obj.name, obc, obco, se, we, 'autocalculate', len(poly.vertices)]
                for vert in poly.vertices:
                    params.append("!- X,Y,Z ==> Vertex {} (m)".format(vert))
                    paramvs.append("  {0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}".format(obm * odv[vert].co))
                en_idf.write(epentry('BuildingSurface:Detailed', params, paramvs))

                params = ['Name', 'Surface Type', 'Construction Name', 'Building Surface Name', 'Outside Boundary Condition Object', 'View Factor to Ground', 'Shading Control Name', 'Frame and Divider Name', 'Multiplier', 'Number of Vertices']
                paramvs = [('win-', 'door-')[mat.envi_con_type == 'Door']+'{}_{}'.format(obj.name, poly.index), mat.envi_con_type, mat.name, '{}_{}'.format(obj.name, poly.index), obco, 'autocalculate', '', '', '1', len(poly.vertices)]
                for vert in poly.vertices:
                    paramvs.append("  {0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}".format((xav+((obm * odv[vert].co)[0]-xav)*0.95, yav+((obm * odv[vert].co)[1]-yav)*0.95, zav+((obm * odv[vert].co)[2]-zav)*0.95)))
                    params.append("X,Y,Z ==> Vertex {} (m)".format(vert))
                en_idf.write(epentry('FenestrationSurface:Detailed', params, paramvs))
                
            elif mat.envi_con_type == 'Shading':
                params = ['Name', 'Transmittance Schedule Name', 'Number of Vertices', 'X,Y,Z ==> Vertex 1 (m)', 'X,Y,Z ==> Vertex 2 (m)', 'X,Y,Z ==> Vertex 3 (m)']
                paramvs = ['{}_{}'.format(obj.name, poly.index), '', '3', obm * odv[poly.vertices[0]].co, obm * odv[poly.vertices[1]].co, obm * odv[poly.vertices[2]].co]
                en_idf.write(epentry('Shading:Building:Detailed', params, paramvs))
#                en_idf.write('\nShading:Building:Detailed,\n' +
#                "{0:{width}}! - Name\n".format("    "+obj.name+'_'+str(poly.index)+",",  width = s) +
#                "{0:{width}}! - Transmittance Schedule Name\n".format("    ,",  width = s) +
#                "{0:{width}}! - Number of Vertices\n".format("    3,",  width = s) +
#                "{0}{1[0]:.3f}, {1[1]:.3f}, {1[2]:.3f}, {2}".format("       ", obm * odv[poly.vertices[0]].co,  "                                          !- X,Y,Z ==> Vertex 1 {m}\n") +
#                "{0}{1[0]:.3f}, {1[1]:.3f}, {1[2]:.3f}, {2}".format("       ", obm * odv[poly.vertices[1]].co,  "                                          !- X,Y,Z ==> Vertex 1 {m}\n") +
#                "{0}{1[0]:.3f}, {1[1]:.3f}, {1[2]:.3f}; {2}".format("       ", obm * odv[poly.vertices[2]].co,  "                                          !- X,Y,Z ==> Vertex 1 {m}\n\n"))

    for o, obj in enumerate([obj for obj in bpy.context.scene.objects if obj.layers[1] == True and obj.envi_type == '1']):
        if o == 0:
            en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: SCHEDULES ===========\n\n")
            en_idf.write("ScheduleTypeLimits,\n{0:{width}}!- Name\n{1:{width}}!- Lower Limit Value\n{2:{width}}!- Upper Limit Value\n{3:{width}}!- Numeric Type\n{4:{width}}!- Unit Type\n\n".format("    Temperature,", "    -60,", "    200,", "    CONTINUOUS,", "    Temperature;", width = s))
            en_idf.write("ScheduleTypeLimits,\n    Control Type,%s!- Name\n    0,%s!- Lower Limit Value\n    4,%s!- Upper Limit Value\n    DISCRETE;%s!- Numeric Type\n\n" %(spformat("Control Type"), spformat("0"), spformat("0"), spformat("DISCRETE")))
            en_idf.write("ScheduleTypeLimits,\n    Fraction,%s!- Name\n    0.00,%s!- Lower Limit Value\n    1.00,%s!- Upper Limit Value\n    CONTINUOUS;%s!- Numeric Type\n\n" %(spformat("Fraction"), spformat("0.00"), spformat("1.00"), spformat("CONTINUOUS")))
            en_idf.write("ScheduleTypeLimits,\n    Any Number;%s!- Name\n\n"  %(spformat("Any Number")))

        if obj.envi_heats1 == True:
            heat = heating(obj)
            en_idf.write("Schedule:Compact,\n\
    Heating Setpoints %s,%s!- Name\n" %(obj.name, spformat("Heating Setpoints "+obj.name)) + "\
    Temperature,%s!- Schedule Type Limits Name\n" %(spformat("Temperature")) + "\
    Through: 12/31,\n\
%s" %(heat.writesp()))
        else:
            heat = None

        if obj.envi_cools1 == True:
            cool = cooling(obj)
            en_idf.write("Schedule:Compact,\n\
    Cooling Setpoints %s,%s!- Name\n" %(obj.name, spformat("Cooling Setpoints "+obj.name)) + "\
    Temperature,%s!- Schedule Type Limits Name\n" %(spformat("Temperature")) + "\
    Through: 12/31,\n\
%s" %(cool.writesp()))
        else:
            cool = None

        if heat and cool:
            params = list(hcparams)
            paramvs = ('{} Dual Setpoint'.format(obj.name), 'Heating Setpoints {}'.format(obj.name), 'Cooling Setpoints {}'.format(obj.name))
            en_idf.write(epentry('ThermostatSetpoint:DualSetpoint', params, paramvs))
#            en_idf.write("ThermostatSetpoint:DualSetpoint,\n\
#    %s Dual Setpoint,%s!- Name\n" %(obj.name, spformat("Dual Setpoint "+obj.name)) +"\
#    Heating Setpoints %s,%s!- Setpoint Temperature Schedule Name\n" %(obj.name, spformat("Heating Setpoints "+obj.name))+"\
#    Cooling Setpoints %s;%s!- Setpoint Temperature Schedule Name\n\n" %(obj.name, spformat("Cooling Setpoints "+obj.name)))
            ct = 4

        elif cool:
            params = list(spparams)
            paramvs = ('{} Cooling Setpoint'.format(obj.name), 'Cooling Setpoints {}'.format(obj.name))
            en_idf.write(epentry('ThermostatSetpoint:SingleCooling', params, paramvs))
#            en_idf.write("ThermostatSetpoint:SingleCooling,\n\
#    %s Cooling Setpoint,%s!- Name\n" %(obj.name, spformat("Cooling Setpoint "+obj.name)) +"\
#    Cooling Setpoints %s;%s!- Setpoint Temperature Schedule Name\n\n" %(obj.name, spformat("Cooling Setpoints "+obj.name)))
            ct = 2
        elif heat:
            params = list(spparams)
            paramvs = ('{} Heating Setpoint'.format(obj.name), 'Heating Setpoints {}'.format(obj.name))
            en_idf.write(epentry('ThermostatSetpoint:SingleHeating', params, paramvs))
#            en_idf.write("ThermostatSetpoint:SingleHeating,\n\
#    %s Heating Setpoint,%s!- Name\n" %(obj.name, spformat("Heating Setpoint "+obj.name)) +"\
#    Heating Setpoints %s;%s!- Setpoint Temperature Schedule Name\n\n" %(obj.name, spformat("Heating Setpoints "+obj.name)))
            ct = 1

        if obj.envi_heats1 == True or obj.envi_cools1 == True:
            en_idf.write("ZoneControl:Thermostat,\n\
    %s Thermostat,%s!- Name\n" %(obj.name, spformat(obj.name+" Thermostat")) +"\
    %s,%s!- Zone or ZoneList Name\n" %(obj.name, spformat(obj.name)) +"\
    %s Control Type Sched,%s!- Control Type Schedule Name\n" %(obj.name, spformat(obj.name+" Control Type Sched")))
            if ct == 1:
                en_idf.write("    ThermostatSetpoint:SingleHeating,%s!- Control 1 Object Type\n" %(spformat("ThermostatSetpoint:SingleHeating"))+ "\
    %s Heating Setpoint;%s!- Control 1 Name\n\n" %(obj.name, spformat(obj.name+" Heating Setpoint")))
            if ct == 2:
                en_idf.write("    ThermostatSetpoint:SingleCooling,%s!- Control 1 Object Type\n" %(spformat("ThermostatSetpoint:SingleCooling"))+ "\
    %s Cooling Setpoint;%s!- Control 2 Name\n\n" %(obj.name, spformat(obj.name+" Cooling Setpoint")))
            if ct == 4:
                en_idf.write("    ThermostatSetpoint:DualSetpoint,%s!- Control 1 Object Type\n" %(spformat("ThermostatSetpoint:DualSetpoint"))+ "\
    %s Dual Setpoint;%s!- Control 4 Name\n\n" %(obj.name, spformat(obj.name+" Dual Setpoint")))

            en_idf.write("Schedule:Compact,\n\
    %s Control Type Sched,%s!- Name" %(obj.name, spformat(obj.name + " Control Type Sched")) +"\n\
    Control Type,%s!- Schedule Type Limits Name\n" %(spformat("Control Type")) +"\
    Through: 12/31,\n\
    For: Alldays,\n\
    Until: 24:00,%s;\n\n" %(ct))

            en_idf.write("ZoneHVAC:EquipmentConnections,\n\
    %s,%s!- Zone Name\n" %(obj.name, spformat(obj.name)) +"\
    %s_Equipment,%s!- Zone Conditioning Equipment List Name\n" %(obj.name, spformat(obj.name+"_Equipment"))+ "\
    %s_supairnode,%s!- Zone Air Inlet Node or NodeList Name\n" %(obj.name, spformat(obj.name+"_supairnode")) +"\
    ,%s!- Zone Air Exhaust Node or NodeList Name\n" %(spformat("")) +"\
    %s_airnode,%s!- Zone Air Node Name\n" %(obj.name, spformat(obj.name+"_airnode"))+ "\
    %s_retairnode;%s!- Zone Return Air Node Name\n\n" %(obj.name, spformat(obj.name+"_retairnode")))

            en_idf.write("ZoneHVAC:EquipmentList,\n\
    %s_Equipment,%s!- Name\n" %(obj.name, spformat(obj.name+"_Equipment")) +"\
    ZoneHVAC:IdealLoadsAirSystem,%s!- Zone Equipment 1 Object Type\n" %(spformat("ZoneHVAC:IdealLoadsAirSystem")) +"\
    %s_Air,%s!- Zone Equipment 1 Name\n" %(obj.name, spformat(obj.name+"_Air")) +"\
    1,%s!- Zone Equipment 1 Cooling Sequence\n" %(spformat("1")) +"\
    1;%s!- Zone Equipment 1 Heating or No-Load Sequence\n\n"  %(spformat("1")))

            params = ('Name', 'Availability Schedule Name', 'Zone Supply Air Node Name', 'Zone Exhaust Air Node Name', 'Maximum Heating Supply Air Temperature (C)', 
                      'Minimum Cooling Supply Air Temperature (C)', ' Maximum Heating Supply Air Humidity Ratio (kg-H2O/kg-air)', 'Minimum Cooling Supply Air Humidity Ratio (kg-H2O/kg-air)',
                        'Heating Limit', 'Maximum Heating Air Flow Rate (m3/s)', 'Maximum Sensible Heating Capacity (W)', 'Cooling Limit', 'Maximum Cooling Air Flow Rate (m3/s)', 
                        'Maximum Total Cooling Capacity (W)', 'Heating Availability Schedule Name', 'Cooling Availability Schedule Name', 'Dehumidification Control Type', 'Design Specification Outdoor Air Object Name',
                        ' Outdoor Air Inlet Node Name', 'Demand Controlled Ventilation Type', 'Outdoor Air Economizer Type', 'Heat Recovery Type', 'Sensible Heat Recovery Effectiveness (dimensionless)', 'Latent Heat Recovery Effectiveness (dimensionless)')
            paramvs = ('{}_Air'.format(obj.name), '', '{}_supairnode'.format(obj.name), '', '', 50, 10, 0.015, 0.009, 'LimitCapacity', '', obj.envi_heats1c, 'LimitCapacity', '',\
            obj.envi_cools1c, '', '', 'ConstantSupplyHumidityRatio', '', '', '', '', '', '', '')
            en_idf.write(epentry('ZoneHVAC:IdealLoadsAirSystem', params, paramvs))
#            en_idf.write("ZoneHVAC:IdealLoadsAirSystem,\n\
#    %s_Air,%s!- Name\n" %(obj.name, spformat(obj.name+"_Air")) +"\
#    ,%s!- Availability Schedule Name\n"%(spformat("")) +"\
#    %s_supairnode,%s!- Zone Supply Air Node Name\n" %(obj.name, spformat(obj.name+"_supairnode")) +"\
#    ,%s!- Zone Exhaust Air Node Name\n" %(spformat("")) +"\
#    50,%s!- Maximum Heating Supply Air Temperature {C}\n" %(spformat("50")) +"\
#    10,%s!- Minimum Cooling Supply Air Temperature {C}\n" %(spformat("10")) +"\
#    0.015,%s!- Maximum Heating Supply Air Humidity Ratio {kg-H2O/kg-air}\n" %(spformat("0.015")) +"\
#    0.009,%s!- Minimum Cooling Supply Air Humidity Ratio {kg-H2O/kg-air}\n" %(spformat("0.009")) +"\
#    LimitCapacity,%s!- Heating Limit\n" %(spformat("LimitCapacity")) +"\
#    ,%s!- Maximum Heating Air Flow Rate {m3/s}\n" %(spformat("")) +"\
#    %s,%s!- Maximum Sensible Heating Capacity {W}\n" %(obj.envi_heats1c, spformat(obj.envi_heats1c)) +"\
#    LimitCapacity,%s!- Cooling Limit\n" %(spformat("LimitCapacity")) +"\
#    ,%s!- Maximum Cooling Air Flow Rate {m3/s}\n" %(spformat("")) +"\
#    %s,%s!- Maximum Total Cooling Capacity {W}\n" %(obj.envi_cools1c, spformat(obj.envi_cools1c)) +"\
#    ,%s!- Heating Availability Schedule Name\n" %(spformat("")) +"\
#    ,%s!- Cooling Availability Schedule Name\n" %(spformat("")) +"\
#    ConstantSupplyHumidityRatio,%s!- Dehumidification Control Type\n" %(spformat("ConstantSupplyHumidityRatio")) +"\
#    ,%s!- Cooling Sensible Heat Ratio {dimensionless}\n" %(spformat("")) +"\
#    ConstantSupplyHumidityRatio,%s!- Humidification Control Type\n" %(spformat("ConstantSupplyHumidityRatio")) +"\
#    ,%s!- Design Specification Outdoor Air Object Name\n" %(spformat("")) +"\
#    ,%s!- Outdoor Air Inlet Node Name\n" %(spformat("")) +"\
#    ,%s!- Demand Controlled Ventilation Type\n" %(spformat("")) +"\
#    ,%s!- Outdoor Air Economizer Type\n" %(spformat("")) +"\
#    ,%s!- Heat Recovery Type\n" %(spformat("")) +"\
#    ,%s!- Sensible Heat Recovery Effectiveness {dimensionless}\n" %(spformat("")) +"\
#    ;%s!- Latent Heat Recovery Effectiveness {dimensionless}\n\n" %(spformat("")))

            params = ('Name', 'Node 1 Name')
            paramvs = ('{}Inlets'.format(obj.name), '{}_supairnode'.format(obj.name))  
            en_idf.write(epentry('Nodelist', params, paramvs))
#            en_idf.write("NodeList,\n\
#    %sInlets,%s!- Name\n" %(obj.name, spformat(obj.name+"Inlets")) +"\
#    %s_supairnode;%s!- Node 1 Name\n\n" %(obj.name, spformat(obj.name+"_supairnode")))



        if obj.envi_occtype != "0":
            occ = occupancy(obj)
#            params = ('Name', 'Schedule Type Limits Name')
#            params = (obj.name+" Occupancy", 'Fraction')
#            en_idf.write(epentry("Schedule:Compact", params, paramvs))
            
            en_idf.write("Schedule:Compact","\n\
    "+obj.name+" Occupancy,%s!- Name\n" %(spformat(obj.name+" Occupancy")) + "\
    Fraction,%s!- Schedule Type Limits Name\n" %(spformat("Fraction")) + "\
    Through: 12/31,\n\
%s" %(occ.writeuf()))

            params = ('Name', ' Zone or ZoneList Name', 'Number of People Schedule Name', 'Number of People Calculation Method', 'Number of People', 'People per Zone Floor Area (person/m2)',
                    'Zone Floor Area per Person (m2/person)', 'Zone Floor Area per Person (m2/person)', 'Fraction Radiant', 'Sensible Heat Fraction', 'Activity Level Schedule Name')
            paramvs = (obj.name+" Occupancy Schedule", obj.name, obj.name+" Occupancy", 'People', (obj.envi_occsmax, "", "")[int(obj.envi_occtype)-1], ( "", obj.envi_occsmax, "")[int(obj.envi_occtype)-1], \
            ("", "", obj.envi_occsmax)[int(obj.envi_occtype)-1], 0.7, '', obj.name + 'Activity Lvl')
            en_idf.write(epentry("People", params, paramvs))
#            ,\n\
#    %s,%s!- Name\n" %(obj.name+" Occupancy Schedule", spformat(obj.name+" Occupancy Schedule")) +"\
#    %s,%s!- Zone or ZoneList Name\n" %(obj.name, spformat(obj.name)) + "\
#    %s,%s!- Number of People Schedule Name\n" %(obj.name+" Occupancy", spformat(obj.name+" Occupancy")) +"\
#    People,"+spformat("People")+ "!- Number of People Calculation Method\n\
#    %s,%s!- Number of People\n" %((obj.envi_occsmax, "", "")[int(obj.envi_occtype)-1], spformat((obj.envi_occsmax, "", "")[int(obj.envi_occtype)-1])) +"\
#    %s,%s!- People per Zone Floor Area {person/m2}\n" %(( "", obj.envi_occsmax, "")[int(obj.envi_occtype)-1], spformat(( "", obj.envi_occsmax, "")[int(obj.envi_occtype)-1])) +"\
#    %s,%s!- Zone Floor Area per Person {m2/person}\n" %(("", "", obj.envi_occsmax)[int(obj.envi_occtype)-1], spformat(("", "", obj.envi_occsmax)[int(obj.envi_occtype)-1])) +"\
#    0.7,%s!- Fraction Radiant\n" %(spformat("0.7")) + "\
#    ,%s!- Sensible Heat Fraction\n" %(spformat("")) + "\
#    %s Activity Lvl;%s!- Activity Level Schedule Name\n\n" %(obj.name, spformat(obj.name+" Activity Lvl")))

            en_idf.write("Schedule:Compact,\n\
    %s Activity Lvl,%s!- Name\n" %(obj.name, spformat(obj.name+" Activity Lvl")) +"\
    Any Number,%s!- Schedule Type Limits Name\n" %(spformat("Any Number")) +"\
    Through:12/31,\n\
%s" %(occ.writeactivity()))

        if (obj.envi_inftype != "0" and obj.envi_occtype == "0") or (obj.envi_occinftype != "0" and obj.envi_occtype != "0"):
            infil = infiltration(obj)
            params = ('Name', 'Zone or ZoneList Name', 'Schedule Name', 'Design Flow Rate Calculation Method', 'Design Flow Rate (m3/s)', 'Flow per Zone Floor Area (m3/s-m2)', 'Flow per Exterior Surface Area (m3/s-m2'\
            'Air Changes per Hour (1/hr)', 'Constant Term Coefficient', 'Temperature Term Coefficient', 'Velocity Term Coefficient', 'Velocity Squared Term Coefficient')
            paramvs = ('{} Infiltration', obj.name, '{} Infiltration Schedule'.format(obj.name), infil.infilcalc, infil.infilmax[0], infil.infilmax[1], infil.infilmax[2], infil.infilmax[3],\
            1.00, 0.00, 0.00, 1.00)
            en_idf.write(epentry('ZoneInfiltration:DesignFlowRate', params, paramvs))
#            en_idf.write("ZoneInfiltration:DesignFlowRate, \n\
#    %s Infiltration,%s!- Name\n" %(obj.name, spformat(obj.name + " Infiltration")) +"\
#    %s,%s!- Zone or ZoneList Name\n" %(obj.name, spformat(obj.name)) +"\
#    %s Infiltration Schedule,%s!- Schedule Name\n" %(obj.name, spformat(obj.name +" Infiltration Schedule")) +"\
#    %s,%s!- Design Flow Rate Calculation Method\n" %(infil.infilcalc, spformat(infil.infilcalc)) +"\
#    %s,%s!- Design Flow Rate {m3/s}\n" %(infil.infilmax[0], spformat(infil.infilmax[0])) +"\
#    %s,%s!- Flow per Zone Floor Area {m3/s-m2}\n" %(infil.infilmax[1], spformat(infil.infilmax[1])) +"\
#    %s,%s!- Flow per Exterior Surface Area {m3/s-m2}\n" %(infil.infilmax[2], spformat(infil.infilmax[2])) +"\
#    %s,%s!- Air Changes per Hour {1/hr}\n" %(infil.infilmax[3], spformat(infil.infilmax[3])) +"\
#    1.0000,%s!- Constant Term Coefficient\n" %(spformat("1.0000")) +"\
#    0.0000,%s!- Temperature Term Coefficient\n" %(spformat("0.0000")) +"\
#    0.0000,%s!- Velocity Term Coefficient\n" %(spformat("0.0000")) +"\
#    0.0000;%s!- Velocity Squared Term Coefficient\n\n" %(spformat("1.0000")))

            if obj.envi_occtype != "0" and obj.envi_occinftype == "1":
                en_idf.write("Schedule:Compact,\n\
    %s Infiltration Schedule,%s!- Name\n" %(obj.name, spformat(obj.name + " Infiltration Schedule")) +"\
    Any Number,%s!- Schedule Type Limits Name\n" %(spformat("Any Number")) +"\
    THROUGH: 12/31,\n\
    %s" %(infil.writeinfuf(occ, obj)))
            else:
                params = ('Name', 'Schedule Type Limits Name', 'Through', 'For', 'Until')
                paramvs = ('{} Infiltration Schedule'.format(obj.name), 'Any Number', 'THROUGH: 12/31', 'FOR: AllDays', 'UNTIL: 24:00,1')
                en_idf.write(epentry('Schedule:Compact', params, paramvs))
#                en_idf.write("Schedule:Compact,\n\
#    %s Infiltration Schedule,%s!- Name\n" %(obj.name, spformat(obj.name + " Infiltration Schedule")) +"\
#    Any Number,%s!- Schedule Type Limits Name\n" %(spformat("Any Number")) +"\
#    THROUGH: 12/31,\n\
#    FOR: AllDays,\n\
#    UNTIL: 24:00,1;\n\n")
    
    if enng:
        for snode in [snode for snode in enng.nodes if snode.bl_idname == 'EnViSched' and snode.outputs['Schedule'].is_linked]:
            en_idf.write(snode.epwrite())

    writeafn(exp_op, en_idf, enng)

    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: REPORT VARIABLE ===========\n\n")
    epentrydict = {"Output:Variable,*,Site Outdoor Air Drybulb Temperature,Hourly;\n": node.resat, "Output:Variable,*,Site Outdoor Air Drybulb Temperature,Hourly;\n": node.resaws,
                   "Output:Variable,*,Site Wind Direction,Hourly;\n": node.resawd, "Output:Variable,*,Site Outdoor Air Relative Humidity,hourly;\n": node.resah,
                   "Output:Variable,*,Site Direct Solar Radiation Rate per Area,hourly;\n": node.resasb, "Output:Variable,*,Zone Air Temperature,hourly;\n": node.restt,
                   "Output:Variable,*,Zone Air System Sensible Heating Rate,hourly;\n": node.restwh, "Output:Variable,*,Zone Air System Sensible Cooling Rate,hourly;\n": node.restwc,
                   "Output:Variable,*,FangerPMV,hourly;\n": node.rescpm, "Output:Variable,*,FangerPPD,hourly;\n": node.rescpp, "Output:Variable,*,AFN Zone Infiltration Volume, hourly;\n":node.resim,
                   "Output:Variable,*,AFN Zone Infiltration Air Change Rate, hourly;\n": node.resiach, "Output:Variable,*,Zone Windows Total Transmitted Solar Radiation Rate [W],hourly;\n": node.reswsg,
                   "Output:Variable,*,AFN Node CO2 Concentration,hourly;\n": node.resco2}
    for ep in epentrydict:
        if epentrydict[ep]:
            en_idf.write(ep)

    if node.resl12ms:
        for cnode in [cnode for cnode in bpy.data.node_groups['EnVi Network'].nodes if cnode.bl_idname == 'EnViSFlow']:
            for sno in cnode['sname']:
                en_idf.write("Output:Variable,{},AFN Linkage Node 1 to Node 2 Volume Flow Rate,hourly;\n".format(sno))
        for snode in [snode for snode in bpy.data.node_groups['EnVi Network'].nodes if snode.bl_idname == 'EnViSSFlow']:
            for sno in snode['sname']:
                en_idf.write("Output:Variable,{},AFN Linkage Node 1 to Node 2 Volume Flow Rate,hourly;\n".format(sno))
    if node.reslof == True:
        for snode in [cnode for cnode in bpy.data.node_groups['EnVi Network'].nodes if cnode.bl_idname == 'EnViSSFlow']:
            if snode.linkmenu in ('SO', 'DO' 'HO'):
                for sno in snode['sname']:
                    en_idf.write("Output:Variable,{},AFN Surface Venting Window or Door Opening Factor,hourly;\n".format(sno)) 
    en_idf.write("Output:Table:SummaryReports,\
    AllSummary;              !- Report 1 Name")
    en_idf.close()

    if 'in.idf' not in [im.name for im in bpy.data.texts]:
        bpy.data.texts.load(scene['viparams']['idf_file'])

    if sys.platform == "win32":
        subprocess.call(node.cp+'"'+locnode.weather+'" '+os.path.join(node.newdir, "in.epw"), shell = True)
        subprocess.call(node.cp+'"'+os.path.dirname( os.path.realpath( __file__ ) )+node.fold+"EPFiles"+node.fold+"Energy+.idd"+'" '+node.newdir+node.fold, shell = True)
    else:
        subprocess.call(node.cp+locnode.weather.replace(' ', '\ ')+" "+os.path.join(node.newdir, "in.epw"), shell = True)
        subprocess.call(node.cp+scene.vipath.replace(' ', '\ ')+os.sep+"EPFiles"+os.sep+"Energy+.idd "+node.newdir+os.sep, shell = True)

def pregeo(op):
    scene = bpy.context.scene
    for obj in [obj for obj in scene.objects if obj.layers[1] == True]:
        scene.objects.unlink(obj)
        bpy.data.objects.remove(obj)
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for materials in bpy.data.materials:
        if materials.users == 0:
            bpy.data.materials.remove(materials)

    for obj in [obj for obj in scene.objects if obj.envi_type in ('1', '2') and obj.layers[0] == True and obj.hide == False]:
        if 'EnVi Network' not in bpy.data.node_groups.keys():
            enng = bpy.ops.node.new_node_tree(type='EnViN', name ="EnVi Network")
            bpy.data.node_groups['EnVi Network'].use_fake_user = 1

        obj["volume"] = objvol(op, obj)
        bpy.data.scenes[0].layers[0:2] = (True, False)

        for mats in obj.data.materials:
            if 'en_'+mats.name not in [mat.name for mat in bpy.data.materials]:
                mats.copy().name = 'en_'+mats.name

#        scene.objects.active = obj
#        bpy.ops.object.select_all(action='DESELECT')

        selobj(scene, obj)
        bpy.ops.object.mode_set(mode = "EDIT")
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.duplicate()

        en_obj = scene.objects.active
#        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        obj.select = False
        en_obj.select = True
        en_obj.name = 'en_'+obj.name
        en_obj.data.name = 'en_'+obj.data.name
        en_obj.layers[1] = True
        en_obj.layers[0] = False
        bpy.data.scenes[0].layers[0:2] = (False, True)
        for s, slots in enumerate(en_obj.material_slots):
            bpy.data.materials['en_'+en_obj.data.materials[s].name].envi_export = True
            slots.material = bpy.data.materials['en_'+en_obj.data.materials[s].name]
            dcdict = {'Wall':(1,1,1), 'Partition':(0.5,0.5,0.5), 'Window':(0,1,1), 'Roof':(0,1,0), 'Ceiling':(0, 0.5, 0), 'Floor':(0.44,0.185,0.07), 'Ground':(0.22, 0.09, 0.04), 'Shading':(1, 0, 0), 'Aperture':(0, 0, 1)}
            slots.material.diffuse_color = dcdict[slots.material.envi_con_type]

        for poly in en_obj.data.polygons:
            if en_obj.data.materials[poly.material_index].envi_con_type == 'None':
                poly.select = True
        bpy.ops.object.mode_set(mode = "EDIT")
        bpy.ops.mesh.delete(type = 'FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode = 'OBJECT')
        en_obj.select = False

        if en_obj.name not in [node.zone for node in bpy.data.node_groups['EnVi Network'].nodes if hasattr(node, 'zone')]:
            enng.nodes.new(type = 'EnViZone').zone = en_obj.name
        else:
            for node in enng.nodes:
                if hasattr(node, 'zone') and node.zone == en_obj.name:
                    node.zupdate(bpy.context)

class heating(object):
    def __init__(self, obj):
        self.heatdays = [("AllDays", "WeekDays", "WeekEnds")[int(obj.envi_heats1d)]]
        if obj.envi_heats2 == True:
            if obj.envi_heats1d == "1":
                self.heatdays.append("WeekEnds")
            elif obj.envi_heats1d == "2":
                self.heatdays.append("WeekDays")

        heatshours = ((obj.envi_heats1p1st, obj.envi_heats1p2st, obj.envi_heats1p3st), (obj.envi_heats2p1st, obj.envi_heats2p2st, obj.envi_heats2p3st))
        heatehours= ((obj.envi_heats1p1et, obj.envi_heats1p2et, obj.envi_heats1p3et), (obj.envi_heats2p1et, obj.envi_heats2p2et, obj.envi_heats2p3et))
        setpoints = ((obj.envi_heats1sp1, obj.envi_heats1sp2, obj.envi_heats1sp3), (obj.envi_heats2sp1, obj.envi_heats2sp2, obj.envi_heats2sp3))
        self.untils = [[] for x in range(2)]
        self.nsetpoints = [[] for x in range(2)]
        for i in range(0,len(self.heatdays)):
            if heatshours[i][0] > 1:
                self.nsetpoints[i].append(-50)
                self.untils[i].append(heatshours[i][0])

            for t, et in enumerate(heatehours[i]):
                if t > 0 and heatshours[i][t] > heatehours[i][t-1]:
                    self.nsetpoints[i].append(-50)
                    self.untils[i].append(heatshours[i][t])
                if t > 0 and et > heatshours[i][t]  and heatshours[i][t] == heatehours[i][t-1]:
                    self.untils[i].append(et)
                    self.nsetpoints[i].append(setpoints[i][t])
                elif t > 0 and heatshours[i][t] == heatshours[i][t-1] and heatehours[i][t] == heatehours[i][t-1]:
                    pass
                elif et > heatshours[i][t]:
                    self.untils[i].append(et)
                    self.nsetpoints[i].append(setpoints[i][t])
            try:
                if self.untils[i][-1] < 24:
                    self.nsetpoints[i].append(-50)
                    self.untils[i].append(24)
            except:
                self.nsetpoints[i].append(0)
                self.untils[i].append(24)

    def writesp(self):
        sc = 0
        String = ""
        for cd, heatd in enumerate(self.heatdays):
            String = String + "    For: %s,\n" %(heatd)
            for u, until in enumerate(self.untils[cd]):
                if u == len(self.untils[cd]) -1 and cd == len(self.heatdays) - 1 and "AllDays" in self.heatdays:
                    sc = 1
                String = String+"    Until: %s:00,%s%s\n" %(until, self.nsetpoints[cd][u], (",", ";")[sc])
                if u == len(self.untils[cd]) -1 and cd == len(self.heatdays) - 1 and "AllDays" not in self.heatdays:
                    String = String+"    For AllOtherDays,\n    Until: 24:00, -50;\n"
        return(String+"\n")

class cooling(object):
    def __init__(self, obj):
        self.cooldays = [("AllDays", "WeekDays", "WeekEnds")[int(obj.envi_cools1d)]]
        if obj.envi_cools2 == True:
            if obj.envi_cools1d == "1":
                self.cooldays.append("WeekEnds")
            elif obj.envi_cools1d == "2":
                self.cooldays.append("WeekDays")

        coolshours = ((obj.envi_cools1p1st, obj.envi_cools1p2st, obj.envi_cools1p3st), (obj.envi_cools2p1st, obj.envi_cools2p2st, obj.envi_cools2p3st))
        coolehours= ((obj.envi_cools1p1et, obj.envi_cools1p2et, obj.envi_cools1p3et), (obj.envi_cools2p1et, obj.envi_cools2p2et, obj.envi_cools2p3et))
        setpoints = ((obj.envi_cools1sp1, obj.envi_cools1sp2, obj.envi_cools1sp3), (obj.envi_cools2sp1, obj.envi_cools2sp2, obj.envi_cools2sp3))
        self.untils = [[] for x in range(2)]
        self.nsetpoints = [[] for x in range(2)]
        for i in range(0,len(self.cooldays)):

            if coolshours[i][0] > 1:
                self.nsetpoints[i].append(200)
                self.untils[i].append(coolshours[i][0])

            for t, et in enumerate(coolehours[i]):
                if t > 0 and coolshours[i][t] > coolehours[i][t-1]:
                    self.nsetpoints[i].append(200)
                    self.untils[i].append(coolshours[i][t])
                if t > 0 and et > coolshours[i][t]  and coolshours[i][t] == coolehours[i][t-1]:
                    self.untils[i].append(et)
                    self.nsetpoints[i].append(setpoints[i][t])
                elif t > 0 and coolshours[i][t] == coolshours[i][t-1] and coolehours[i][t] == coolehours[i][t-1]:
                    pass
                elif et > coolshours[i][t]:
                    self.untils[i].append(et)
                    self.nsetpoints[i].append(setpoints[i][t])
            try:
                self.untils[i][-1] < 24
                self.nsetpoints[i].append(200)
                self.untils[i].append(24)
            except:
                self.nsetpoints[i].append(0)
                self.untils[i].append(24)

    def writesp(self):
        sc = 0
        String = ""
        for cd, coold in enumerate(self.cooldays):
            String = String + "    For: %s,\n" %(coold)
            for u, until in enumerate(self.untils[cd]):
                if u == len(self.untils[cd]) -1 and cd == len(self.cooldays) - 1 and "AllDays" in self.cooldays:
                    sc = 1
                String = String+"    Until: %s:00,%s%s\n" %(until, self.nsetpoints[cd][u], (",", ";")[sc])
                if u == len(self.untils[cd]) -1 and cd == len(self.cooldays) - 1 and "AllDays" not in self.cooldays:
                    String = String+"    For AllOtherDays,\n    Until: 24:00, 200;\n"
        return(String+"\n")

class occupancy(object):
    def __init__(self, obj):
        self.occdays = [("AllDays", "WeekDays", "WeekEnds")[int(obj.envi_occs1d)]]
        if obj.envi_occs2 == True:
            if obj.envi_occs1d == "1":
                self.occdays.append("WeekEnds")
            elif obj.envi_occs1d == "2":
                self.occdays.append("WeekDays")

        self.occact = (obj.envi_occs1watts, obj.envi_occs2watts)
        occshours = ((obj.envi_occs1p1st, obj.envi_occs1p2st, obj.envi_occs1p3st), (obj.envi_occs2p1st, obj.envi_occs2p2st, obj.envi_occs2p3st))
        occehours= ((obj.envi_occs1p1et, obj.envi_occs1p2et, obj.envi_occs1p3et), (obj.envi_occs2p1et, obj.envi_occs2p2et, obj.envi_occs2p3et))
        fractions = ((obj.envi_occs1p1level, obj.envi_occs1p2level, obj.envi_occs1p3level), (obj.envi_occs2p1level, obj.envi_occs2p2level, obj.envi_occs2p3level))
        self.untils = [[] for x in range(2)]
        self.nfractions = [[] for x in range(2)]
        for i in range(0,len(self.occdays)):

            if occshours[i][0] > 1:
                self.nfractions[i].append(0)
                self.untils[i].append(occshours[i][0])

            for t, et in enumerate(occehours[i]):
                if t > 0 and occshours[i][t] > occehours[i][t-1]:
                    self.nfractions[i].append("0")
                    self.untils[i].append(occshours[i][t])
                if t > 0 and et > occshours[i][t]  and occshours[i][t] == occehours[i][t-1]:
                    self.untils[i].append(et)
                    self.nfractions[i].append(fractions[i][t])
                elif t > 0 and occshours[i][t] == occshours[i][t-1] and occehours[i][t] == occehours[i][t-1]:
                    pass
                elif et > occshours[i][t]:
                    self.untils[i].append(et)
                    self.nfractions[i].append(fractions[i][t])
            try:
                if self.untils[i][-1] < 24:
                    self.nfractions[i].append(0)
                    self.untils[i].append(24)
            except:
                self.nfractions[i].append(0)
                self.untils[i].append(24)

    def writeuf(self):
        sc = 0
        String = ""
        for od, occd in enumerate(self.occdays):
            String = String + "    For: %s,\n" %(occd)
            for u, until in enumerate(self.untils[od]):
                if u == len(self.untils[od]) -1 and od == len(self.occdays) - 1 and "AllDays" in self.occdays:
                    sc = 1
                String = String+"    Until: %s:00,%s%s\n" %(until, self.nfractions[od][u], (",", ";")[sc])
                if u == len(self.untils[od]) -1 and od == len(self.occdays) - 1 and "AllDays" not in self.occdays:
                    String = String+"    For AllOtherDays,\n    Until: 24:00, 0;\n"
        return(String+"\n")

    def writeactivity(self):
        String =""
        for od, occd in enumerate(self.occdays):
            String = String + "    For: {},\n".format(occd)
            if "AllDays" in self.occdays:
                String = String +"    Until: 24:00,{}{}\n".format(self.occact[od], (",", ";")[int(od+1/len(self.occdays))])
            elif od != len(self.occdays) - 1:
                String = String +"    Until: 24:00,{}{}\n".format(self.occact[od], ",")
            else:
                String = String +"    Until: 24:00,{}{}\n".format(self.occact[od], ",") + "    For AllOtherDays,\n    Until: 24:00, 90;\n"
        return(String + "\n")


class infiltration(object):
    def __init__(self, obj):
        if obj.envi_inftype == "2" and obj.envi_occtype == "0":
            self.infilmax = (obj.envi_inflevel, "", "", "")
            self.infilcalc = "Flow/Zone"
        elif obj.envi_inftype == "3" and obj.envi_occtype == "0":
            self.infilmax = ("", "", "", obj.envi_inflevel)
            self.infilcalc = "AirChanges/Hour"
        elif obj.envi_occinftype == "1" and obj.envi_occtype == "1":
            self.infilmax = (obj.envi_inflevel * obj.envi_occsmax * 0.001, "", "", "")
            self.infil = obj.envi_inflevel * obj.envi_occsmax * 0.001
            self.infilcalc = "Flow/Zone"
            if obj.envi_infbasetype == "0":
                self.baseinfil = obj.envi_infbaselevel
            else:
                self.baseinfil = obj.envi_infbaselevel * float(obj["volume"]) / 3600
        elif obj.envi_occinftype == "2" and obj.envi_occtype == "1":
            self.infilmax = (obj.envi_inflevel, "", "", "")
            self.infilcalc = "Flow/Zone"
        elif obj.envi_occinftype == "3" and obj.envi_occtype == "1":
            self.infilmax = ("", "", "", obj.envi_inflevel)
            self.infilcalc = "AirChanges/Hour"
        elif obj.envi_occinftype == "1" and obj.envi_occtype == "2":
            self.infilmax = ( "", obj.envi_inflevel * obj.envi_occsmax * 0.001, "", "")
            self.infilcalc = "Flow/Area"
            self.infil = obj.envi_inflevel * obj.envi_occsmax * 0.001
            if obj.envi_infbasetype == "0":
                self.baseinfil = obj.envi_infbaselevel * obj["floorarea"] * obj.envi_occsmax * 0.001
            else:
                self.baseinfil = obj.envi_infbaselevel * objvol(obj) * obj["floorarea"] * obj.envi_occsmax * 0.001
        elif obj.envi_occinftype == "2" and obj.envi_occtype == "2":
            self.infilmax = ("", obj.envi_inflevel, "", "")
            self.infilcalc = "Flow/Area"
        elif obj.envi_occinftype == "3" and obj.envi_occtype == "2":
            self.infilmax = ("", "", "", obj.envi_inflevel)
            self.infilcalc = "AirChanges/Hour"
        elif obj.envi_occinftype == "1" and obj.envi_occtype == "3":
            self.infilmax = ("", obj.envi_inflevel * 1/obj.envi_occsmax * 0.001, "")
            self.infilcalc = "Flow/Area"
            self.infil = obj.envi_inflevel * 1/obj.envi_occsmax * 0.001
            if obj.envi_infbasetype == "0":
                self.baseinfil = (1/(obj.envi_infbaselevel/obj["floorarea"])) * 1/obj.envi_occsmax * 0.001
            else:
                self.baseinfil = (1/(obj.envi_infbaselevel * objvol(obj)/obj["floorarea"])) * (1/obj.envi_occsmax) * 0.001
        elif obj.envi_occinftype == "2" and obj.envi_occtype == "3":
            self.infilmax = ("", obj.envi_inflevel, "", "")
            self.infilcalc = "Flow/Area"
        elif obj.envi_occinftype == "3" and obj.envi_occtype == "3":
            self.infilmax = ("", "", "", obj.envi_inflevel)
            self.infilcalc = "AirChanges/Hour"
        else:
            self.infilmax = ("", "", "", "")
            self.infilcalc = ""

    def writeinfuf(self, occ, obj):
        sc = 0
        String = ""
        for od, occd in enumerate(occ.occdays):
            String = String + "    For: {},\n".format(occd)
            for u, until in enumerate(occ.untils[od]):
                if u == len(occ.untils[od]) -1 and od == len(occ.occdays) - 1 and "AllDays" in occ.occdays:
                    sc = 1
                String = String+"    Until: %s:00,%s%s\n" %(until, self.baseinfil/self.infil + float(occ.nfractions[od][u]), (",", ";")[sc])
                if u == len(occ.untils[od]) -1 and od == len(occ.occdays) - 1 and "AllDays" not in occ.occdays:
                    String = String+"    For AllOtherDays,\n    Until: 24:00, 0;\n"
        return(String+"\n")

def writeafn(exp_op, en_idf, enng):
    cf = 0
    if not len([enode for enode in enng.nodes if enode.bl_idname == 'AFNCon']):
        enng.nodes.new(type = 'AFNCon')

    else: 
        contnode = [enode for enode in enng.nodes if enode.bl_idname == 'AFNCon'][0]
        en_idf.write(contnode.epwrite(exp_op))
        extnodes = [enode for enode in enng.nodes if enode.bl_idname == 'EnViExt']
        crrefnodes = [enode for enode in enng.nodes if enode.bl_idname == 'EnViCrRef']
        zonenodes = [enode for enode in enng.nodes if enode.bl_idname == 'EnViZone']
        ssafnodes = [enode for enode in enng.nodes if enode.bl_idname == 'EnViSSFlow']
        safnodes = [enode for enode in enng.nodes if enode.bl_idname == 'EnViSFlow']
                
        for enode in zonenodes:
            en_idf.write(enode.epwrite())
        for enode in ssafnodes + safnodes:
            en_idf.write(enode.epwrite(exp_op, crref = crrefnodes))
            
def spformat(s):
    space = "                                                                       "
    if s == "":
        return(space)
    else:
        return(space[len(str(s)):])

def lineends(tot, cur, flag):
    if cur + 1 < tot:
        return(",\n")
    else:
        if flag == 0:
            return(",\n")
        else:
            return(";\n\n")