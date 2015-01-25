import bpy, os, itertools, subprocess, datetime, sys, mathutils, bmesh
from .vi_func import epentry, objvol, ceilheight, selobj, facearea, boundpoly, rettimes, epschedwrite, selmesh
dtdf = datetime.date.fromordinal

def enpolymatexport(exp_op, node, locnode, em, ec):
    scene = bpy.context.scene
    for scene in bpy.data.scenes:
        scene.update()
    en_epw = open(locnode.weather, "r")
    en_idf = open(scene['viparams']['idf_file'], 'w')
    
#    try:
    enng = [ng for ng in bpy.data.node_groups if ng.bl_label == 'EnVi Network'][0] if [ng for ng in bpy.data.node_groups if ng.bl_label == 'EnVi Network'] else 0
#    except:
#        exp_op.report({'ERROR'}, 'No EnVi node tree found. Have you exported the EnVi Geometry?')
#        return
    en_idf.write("!- Blender -> EnergyPlus\n!- Using the EnVi export scripts\n!- Author: Ryan Southall\n!- Date: {}\n\nVERSION,{};\n\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), scene.epversion))

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
    paramvs = (node.loc, node.startmonth, '1', node.endmonth, ((datetime.date(datetime.datetime.now().year, node.endmonth + (1, -11)[node.endmonth == 12], 1) - datetime.timedelta(days = 1)).day), "UseWeatherFile", "Yes", "Yes", "No", "Yes", "Yes", "1")
    en_idf.write(epentry('RunPeriod', params, paramvs))

    for line in en_epw.readlines():
        if line.split(",")[0].upper() == "GROUND TEMPERATURES":
            gtline, gt = line.split(","), []
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
                matname.append('{}-{}'.format(presetmat, matcount.count(presetmat.upper())))
                matcount.append(presetmat.upper())
                
                if em.namedict.get(presetmat) == None:
                    em.namedict[presetmat] = 0
                    em.thickdict[presetmat] = [thicklist[pm]/1000]
                else:
                    em.namedict[presetmat] = em.namedict[presetmat] + 1
                    em.thickdict[presetmat].append(thicklist[pm]/1000)
                if mat.envi_con_type in ('Wall', 'Floor', 'Roof', 'Door') and presetmat not in em.gas_dat:
                    em.omat_write(en_idf, matname[-1], list(em.matdat[presetmat]), str(thicklist[pm]/1000))
                elif presetmat in em.gas_dat:
                    em.amat_write(en_idf, matname[-1], [em.matdat[presetmat][2]])
                elif mat.envi_con_type =='Window' and em.matdat[presetmat][0] == 'Glazing':
                    em.tmat_write(en_idf, matname[-1], list(em.matdat[presetmat]) + [0], str(thicklist[pm]/1000))
                elif mat.envi_con_type =='Window' and em.matdat[presetmat][0] == 'Gas':
                    em.gmat_write(en_idf, matname[-1], list(em.matdat[presetmat]), str(thicklist[pm]/1000))

            namelist.append(conname)
            ec.con_write(en_idf, mat.envi_con_type, conname, str(namelist.count(conname)-1), mat.name)

        elif mat.envi_con_makeup == '1' and mat.envi_con_type not in ('None', 'Shading', 'Aperture'):
            thicklist = (mat.envi_export_lo_thi, mat.envi_export_l1_thi, mat.envi_export_l2_thi, mat.envi_export_l3_thi, mat.envi_export_l4_thi)
            conname = mat.name
            layers = [i for i in itertools.takewhile(lambda x: x != "0", (mat.envi_layero, mat.envi_layer1, mat.envi_layer2, mat.envi_layer3, mat.envi_layer4))]
            if len(layers) in (2, 4) and mat.envi_con_type == 'Window':
                exp_op.report({'ERROR'}, 'Wrong number of layers specified for the {} window construction'.format(mat.name))
                return
            for l, layer in enumerate(layers):
                if layer == "1" and mat.envi_con_type in ("Wall", "Floor", "Roof"):
                    mats = ((mat.envi_export_bricklist_lo, mat.envi_export_claddinglist_lo, mat.envi_export_concretelist_lo, mat.envi_export_metallist_lo, mat.envi_export_stonelist_lo, mat.envi_export_woodlist_lo, mat.envi_export_gaslist_lo, mat.envi_export_insulationlist_lo), \
                    (mat.envi_export_bricklist_l1, mat.envi_export_claddinglist_l1, mat.envi_export_concretelist_l1, mat.envi_export_metallist_l1, mat.envi_export_stonelist_l1, mat.envi_export_woodlist_l1, mat.envi_export_gaslist_l1, mat.envi_export_insulationlist_l1), \
                    (mat.envi_export_bricklist_l2, mat.envi_export_claddinglist_l2, mat.envi_export_concretelist_l2, mat.envi_export_metallist_l2, mat.envi_export_stonelist_l2, mat.envi_export_woodlist_l2, mat.envi_export_gaslist_l2, mat.envi_export_insulationlist_l2), \
                    (mat.envi_export_bricklist_l3, mat.envi_export_claddinglist_l3, mat.envi_export_concretelist_l3, mat.envi_export_metallist_l3, mat.envi_export_stonelist_l3, mat.envi_export_woodlist_l3, mat.envi_export_gaslist_l3, mat.envi_export_insulationlist_l3), \
                    (mat.envi_export_bricklist_l4, mat.envi_export_claddinglist_l4, mat.envi_export_concretelist_l4, mat.envi_export_metallist_l4, mat.envi_export_stonelist_l4, mat.envi_export_woodlist_l4, mat.envi_export_gaslist_l4, mat.envi_export_insulationlist_l4))\
                    [l][int((mat.envi_layeroto, mat.envi_layer1to, mat.envi_layer2to, mat.envi_layer3to, mat.envi_layer4to)[l])]
                    if mats not in em.gas_dat:
                        em.omat_write(en_idf, '{}-{}'.format(mats, matcount.count(mats.upper())), list(em.matdat[mats]), str(thicklist[l]/1000))
                    else:
                        em.amat_write(en_idf, '{}-{}'.format(mats, matcount.count(mats.upper())), [em.matdat[mats][2]])

                elif layer == "1" and mat.envi_con_type == "Window":
                    mats = ((mat.envi_export_glasslist_lo, mat.envi_export_wgaslist_l1, mat.envi_export_glasslist_l2, mat.envi_export_wgaslist_l3, mat.envi_export_glasslist_l4)[l])
                    if l in (0, 2, 4):
                        em.tmat_write(en_idf, '{}-{}'.format(mats, matcount.count(mats.upper())), list(em.matdat[mats]) + [(0, mat.envi_export_lo_sdiff)[len(layers) == l + 1]], list(em.matdat[mats])[3])
                    else:
                        em.gmat_write(en_idf, '{}-{}'.format(mats, matcount.count(mats.upper())), list(em.matdat[mats]), str(thicklist[l]/1000))

                elif layer == "2" and mat.envi_con_type in ("Wall", "Floor", "Roof"):
                    mats = (mat.envi_export_lo_name, mat.envi_export_l1_name, mat.envi_export_l2_name, mat.envi_export_l3_name, mat.envi_export_l4_name)[l]
                    params = ([mat.envi_export_lo_rough, mat.envi_export_lo_tc, mat.envi_export_lo_rho, mat.envi_export_lo_shc, mat.envi_export_lo_tab, mat.envi_export_lo_sab, mat.envi_export_lo_vab],\
                    [mat.envi_export_l1_rough, mat.envi_export_l1_tc, mat.envi_export_l1_rho, mat.envi_export_l1_shc, mat.envi_export_l1_tab, mat.envi_export_l1_sab, mat.envi_export_l1_vab],\
                    [mat.envi_export_l2_rough, mat.envi_export_l2_tc, mat.envi_export_l2_rho, mat.envi_export_l2_shc, mat.envi_export_l2_tab, mat.envi_export_l2_sab, mat.envi_export_l2_vab],\
                    [mat.envi_export_l3_rough, mat.envi_export_l3_tc, mat.envi_export_l3_rho, mat.envi_export_l3_shc, mat.envi_export_l3_tab, mat.envi_export_l3_sab, mat.envi_export_l3_vab],\
                    [mat.envi_export_l4_rough, mat.envi_export_l4_tc, mat.envi_export_l4_rho, mat.envi_export_l4_shc, mat.envi_export_l4_tab, mat.envi_export_l4_sab, mat.envi_export_l4_vab])[l]
                    em.omat_write(en_idf, mats+"-"+str(matcount.count(mats.upper())), params, str(thicklist[l]/1000))

                elif layer == "2" and mat.envi_con_type == "Window":
                    mats = (mat.envi_export_lo_name, mat.envi_export_l1_name, mat.envi_export_l2_name, mat.envi_export_l3_name, mat.envi_export_l4_name)[l]
                    if l in (0, 2, 4):
                        params = (["Glazing", mat.envi_export_lo_odt, mat.envi_export_lo_sds, mat.envi_export_lo_thi, mat.envi_export_lo_stn, mat.envi_export_lo_fsn, mat.envi_export_lo_bsn, mat.envi_export_lo_vtn, mat.envi_export_lo_fvrn, mat.envi_export_lo_bvrn, mat.envi_export_lo_itn, mat.envi_export_lo_fie, mat.envi_export_lo_bie, mat.envi_export_lo_tc, (0, mat.envi_export_lo_sdiff)[len(layers) == l + 1]],"",\
                    ["Glazing",  mat.envi_export_l2_odt, mat.envi_export_l2_sds, mat.envi_export_l2_thi, mat.envi_export_l2_stn, mat.envi_export_l2_fsn, mat.envi_export_l2_bsn, mat.envi_export_l2_vtn, mat.envi_export_l2_fvrn, mat.envi_export_l2_bvrn, mat.envi_export_l2_itn, mat.envi_export_l2_fie, mat.envi_export_l2_bie, mat.envi_export_l2_tc, (0, mat.envi_export_l2_sdiff)[len(layers) == l + 1]], "",\
                    ["Glazing",  mat.envi_export_l4_odt, mat.envi_export_l4_sds, mat.envi_export_l4_thi, mat.envi_export_l4_stn, mat.envi_export_l4_fsn, mat.envi_export_l4_bsn, mat.envi_export_l4_vtn, mat.envi_export_l4_fvrn, mat.envi_export_l4_bvrn, mat.envi_export_l4_itn, mat.envi_export_l4_fie, mat.envi_export_l4_bie, mat.envi_export_l4_tc, (0, mat.envi_export_l4_sdiff)[len(layers) == l + 1]])[l]
                        em.tmat_write(en_idf, '{}-{}'.format(mats, matcount.count(mats.upper())), params, str(thicklist[l]/1000))
                    else:
                        params = ("", ("Gas", mat.envi_export_wgaslist_l1), "", ("Gas", mat.envi_export_wgaslist_l3))[l]
                        em.gmat_write(en_idf, mats+"-"+str(matcount.count(mats.upper())), params, str(thicklist[l]/1000))
                
                conlist.append('{}-{}'.format(mats, matcount.count(mats.upper())))
                matname.append('{}-{}'.format(mats, matcount.count(mats.upper())))
                matcount.append(mats.upper())

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
            params = ('Name', 'Direction of Relative North (deg)', 'X Origin (m)', 'Y Origin (m)', 'Z Origin (m)', 'Type', 'Multiplier', 'Ceiling Height (m)', 'Volume (m3)',
                      'Floor Area (m2)', 'Zone Inside Convection Algorithm', 'Zone Outside Convection Algorithm', 'Part of Total Floor Area')
            paramvs = (obj.name, 0, 0, 0, 0, 1, 1, ceilheight(obj, []), 'autocalculate', 'autocalculate', 'TARP', 'TARP', 'Yes')
            en_idf.write(epentry('Zone', params, paramvs))
    
    params = ('Starting Vertex Position', 'Vertex Entry Direction', 'Coordinate System')
    paramvs = ('UpperRightCorner', 'Counterclockwise', 'World')
    en_idf.write(epentry('GlobalGeometryRules', params, paramvs))

    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: SURFACE DEFINITIONS ===========\n\n")

    wfrparams = ['Name', 'Surface Type', 'Construction Name', 'Zone Name', 'Outside Boundary Condition', 'Outside Boundary Condition Object', 'Sun Exposure', 'Wind Exposure', 'View Factor to Ground', 'Number of Vertices']

    for obj in [obj for obj in bpy.data.objects if obj.layers[1] and obj.type == 'MESH' and obj.envi_type != '0']:
        obm, odv = obj.matrix_world, obj.data.vertices
        obj["floorarea"] = sum([facearea(obj, face) for face in obj.data.polygons if obj.data.materials[face.material_index].envi_con_type =='floor'])
        for poly in obj.data.polygons:
            mat = obj.data.materials[poly.material_index]
            (obc, obco, se, we) = boundpoly(obj, mat, poly, enng)

            if mat.envi_con_type in ('Wall', "Floor", "Roof") and mat.envi_con_makeup != "2":
                params = list(wfrparams) + ["X,Y,Z ==> Vertex {} (m)".format(v) for v in poly.vertices]
                paramvs = ['{}_{}'.format(obj.name, poly.index), mat.envi_con_type, mat.name, obj.name, obc, obco, se, we, 'autocalculate', len(poly.vertices)]+ ["  {0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}".format(obm * odv[v].co) for v in poly.vertices]
                en_idf.write(epentry('BuildingSurface:Detailed', params, paramvs))
                if mat.envi_con_type == "Floor":
                    obj["floorarea"] = obj["floorarea"] + poly.area

            elif  mat.envi_con_type in ('Door', 'Window'):
                xav, yav, zav = obm*mathutils.Vector(poly.center)
                params = list(wfrparams) + ["X,Y,Z ==> Vertex {} (m)".format(v) for v in poly.vertices]
                paramvs = ['{}_{}'.format(obj.name, poly.index), 'Wall', 'Frame', obj.name, obc, obco, se, we, 'autocalculate', len(poly.vertices)] + ["  {0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}".format(obm * odv[v].co) for v in poly.vertices]
                en_idf.write(epentry('BuildingSurface:Detailed', params, paramvs))

                obound = ('win-', 'door-')[mat.envi_con_type == 'Door']+obco if obco else obco
                params = ['Name', 'Surface Type', 'Construction Name', 'Building Surface Name', 'Outside Boundary Condition Object', 'View Factor to Ground', 'Shading Control Name', 'Frame and Divider Name', 'Multiplier', 'Number of Vertices'] + \
                ["X,Y,Z ==> Vertex {} (m)".format(v) for v in poly.vertices]
                paramvs = [('win-', 'door-')[mat.envi_con_type == 'Door']+'{}_{}'.format(obj.name, poly.index), mat.envi_con_type, mat.name, '{}_{}'.format(obj.name, poly.index), obound, 'autocalculate', '', '', '1', len(poly.vertices)] + \
                ["  {0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}".format((xav+((obm * odv[v].co)[0]-xav)*0.95, yav+((obm * odv[v].co)[1]-yav)*0.95, zav+((obm * odv[v].co)[2]-zav)*0.95)) for v in poly.vertices]
                en_idf.write(epentry('FenestrationSurface:Detailed', params, paramvs))

            elif mat.envi_con_type == 'Shading':
                params = ['Name', 'Transmittance Schedule Name', 'Number of Vertices'] + ['X,Y,Z ==> Vertex {} (m)'.format(v) for v in range(len(poly.vertices))]
                paramvs = ['{}_{}'.format(obj.name, poly.index), '', len(poly.vertices)] + ['{0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}'.format(obm * odv[poly.vertices[v]].co) for v in range(len(poly.vertices))]
                en_idf.write(epentry('Shading:Building:Detailed', params, paramvs))

    co2 = 0
    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: SCHEDULES ===========\n\n")
    params = ('Name', 'Lower Limit Value', 'Upper Limit Value', 'Numeric Type', 'Unit Type')
    paramvs = ("Temperature", -60, 200, "CONTINUOUS", "Temperature")
    en_idf.write(epentry('ScheduleTypeLimits', params, paramvs))
    params = ('Name', 'Lower Limit Value', 'Upper Limit Value', 'Numeric Type')
    paramvs = ("Control Type", 0, 4, "DISCRETE")
    en_idf.write(epentry('ScheduleTypeLimits', params, paramvs))
    params = ('Name', 'Lower Limit Value', 'Upper Limit Value', 'Numeric Type')
    paramvs = ("Fraction", 0, 1, "CONTINUOUS")
    en_idf.write(epentry('ScheduleTypeLimits', params, paramvs))
    params = ['Name']
    paramvs = ["Any Number"]
    en_idf.write(epentry('ScheduleTypeLimits', params, paramvs))

    hcoiobjs = [hcoiwrite(obj) for obj in bpy.context.scene.objects if obj.layers[1] == True and obj.envi_type == '1']
    bpy.context.scene['viparams']['hvactemplate'] = 0
    for hcoiobj in hcoiobjs:
        en_idf.write(hcoiobj.hvacschedwrite())
        if hcoiobj.h:
            en_idf.write(hcoiobj.htspwrite())
        if hcoiobj.c:
            en_idf.write(hcoiobj.ctspwrite())
        if hcoiobj.h or hcoiobj.c:
            en_idf.write(hcoiobj.consched())
        if hcoiobj.obj.envi_occtype != '0':
            en_idf.write(hcoiobj.schedwrite())
            en_idf.write(hcoiobj.aschedwrite())
            if hcoiobj.obj.envi_comfort:
                en_idf.write(hcoiobj.weschedwrite())
                en_idf.write(hcoiobj.avschedwrite())
                en_idf.write(hcoiobj.clschedwrite())
                if hcoiobj.obj.envi_co2 and not co2:
                    en_idf.write(hcoiobj.co2sched())
                    co2 = 1
        if hcoiobj.obj.envi_equiptype != '0':
            en_idf.write(hcoiobj.equipsched())
            
            
        if (hcoiobj.obj.envi_occtype == "1" and hcoiobj.obj.envi_occinftype != 0) or (hcoiobj.obj.envi_occtype != "1" and hcoiobj.obj.envi_inftype != 0):
            en_idf.write(hcoiobj.zisched())

    if enng:
        for snode in [snode for snode in enng.nodes if snode.bl_idname == 'EnViSched' and snode.outputs['Schedule'].is_linked]:
            en_idf.write(snode.epwrite())

    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: THERMOSTSTATS ===========\n\n")
    for hcoiobj in [hcoiobj for hcoiobj in hcoiobjs if hcoiobj.hc]:
        en_idf.write(hcoiobj.thermowrite())
        en_idf.write(hcoiobj.zc())
    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: EQUIPMENT ===========\n\n")
    for hcoiobj in [hcoiobj for hcoiobj in hcoiobjs if hcoiobj.hc and not hcoiobj.obj.envi_hvact]:
        en_idf.write(hcoiobj.ec())
        en_idf.write(hcoiobj.el())
    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: HVAC ===========\n\n")
    for hcoiobj in [hcoiobj for hcoiobj in hcoiobjs if hcoiobj.hc and not hcoiobj.obj.envi_hvact]:
        en_idf.write(hcoiobj.zh())
        if hcoiobj.obj.envi_hvacoam != '0': 
            en_idf.write(hcoiobj.zhoa())
    for hcoiobj in [hcoiobj for hcoiobj in hcoiobjs if hcoiobj.hc and hcoiobj.obj.envi_hvact]:
        en_idf.write(hcoiobj.zht())
    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: OCCUPANCY ===========\n\n")
    for hcoiobj in hcoiobjs:
        if hcoiobj.obj.envi_occtype != "0":
            en_idf.write(hcoiobj.peoplewrite())
    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: OTHER EQUIPMENT ===========\n\n")
    for hcoiobj in hcoiobjs:
        if hcoiobj.obj.envi_equiptype != "0":
            en_idf.write(hcoiobj.equip())
    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: CONTAMINANTS ===========\n\n")
    co2 = 0
    for hcoiobj in hcoiobjs:
        if hcoiobj.obj.envi_co2 and not co2:
            en_idf.write(hcoiobj.co2())
            co2 = 1

    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: INFILTRATION ===========\n\n")
    for hcoiobj in hcoiobjs:
        if (hcoiobj.obj.envi_occtype == "1" and hcoiobj.obj.envi_occinftype != '0') or (hcoiobj.obj.envi_occtype != "1" and hcoiobj.obj.envi_inftype != '0'):
            en_idf.write(hcoiobj.zi())

    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: AIRFLOW NETWORK ===========\n\n")
    
    if enng and enng['enviparams']['afn']:
        writeafn(exp_op, en_idf, enng)

    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: REPORT VARIABLE ===========\n\n")
    epentrydict = {"Output:Variable,*,Site Outdoor Air Drybulb Temperature,Hourly;\n": node.resat, "Output:Variable,*,Site Wind Speed,Hourly;\n": node.resaws,
                   "Output:Variable,*,Site Wind Direction,Hourly;\n": node.resawd, "Output:Variable,*,Site Outdoor Air Relative Humidity,hourly;\n": node.resah,
                   "Output:Variable,*,Site Direct Solar Radiation Rate per Area,hourly;\n": node.resasb, "Output:Variable,*,Zone Air Temperature,hourly;\n": node.restt,
                   "Output:Variable,*,Zone Air System Sensible Heating Rate,hourly;\n": node.restwh, "Output:Variable,*,Zone Air System Sensible Cooling Rate,hourly;\n": node.restwc,
                   "Output:Variable,*,Zone Ideal Loads Supply Air Sensible Heating Rate, hourly;\n": node.ressah, "Output:Variable,*,Zone Ideal Loads Supply Air Sensible Cooling Rate,hourly;\n": node.ressac,
                   "Output:Variable,*,Zone Thermal Comfort Fanger Model PMV,hourly;\n": node.rescpm, "Output:Variable,*,Zone Thermal Comfort Fanger Model PPD,hourly;\n": node.rescpp, "Output:Variable,*,Zone Infiltration Current Density Volume Flow Rate, hourly;\n":node.resim,
                   "Output:Variable,*,Zone Infiltration Air Change Rate, hourly;\n": node.resiach, "Output:Variable,*,Zone Windows Total Transmitted Solar Radiation Rate,hourly;\n": node.reswsg,
                   "Output:Variable,*,AFN Node CO2 Concentration,hourly;\n": node.resco2 and enng['enviparams']['afn'], "Output:Variable,*,Zone Air CO2 Concentration,hourly;\n": node.resco2 and not enng['enviparams']['afn'],
                   "Output:Variable,*,Zone Mean Radiant Temperature,hourly;\n": node.resmrt, "Output:Variable,*,Zone People Occupant Count,hourly;\n": node.resocc,
                   "Output:Variable,*,Zone Air Relative Humidity,hourly;\n": node.resh, "Output:Variable,*,Zone Air Heat Balance Surface Convection Rate, hourly;\n": node.resfhb}
    for ep in epentrydict:
        if epentrydict[ep]:
            en_idf.write(ep)

    if node.resl12ms:
        for cnode in [cnode for cnode in enng.nodes if cnode.bl_idname == 'EnViSFlow']:
            for sno in cnode['sname']:
                en_idf.write("Output:Variable,{0},AFN Linkage Node 1 to Node 2 Volume Flow Rate,hourly;\nOutput:Variable,{0},AFN Linkage Node 2 to Node 1 Volume Flow Rate,hourly;\n".format(sno))
        for snode in [snode for snode in enng.nodes if snode.bl_idname == 'EnViSSFlow']:
            for sno in snode['sname']:
                en_idf.write("Output:Variable,{0},AFN Linkage Node 1 to Node 2 Volume Flow Rate,hourly;\nOutput:Variable,{0},AFN Linkage Node 2 to Node 1 Volume Flow Rate,hourly;\n".format(sno))
    if node.reslof == True:
        for snode in [snode for snode in enng.nodes if snode.bl_idname == 'EnViSSFlow']:
            if snode.linkmenu in ('SO', 'DO', 'HO'):
                for sno in snode['sname']:
                    en_idf.write("Output:Variable,{},AFN Surface Venting Window or Door Opening Factor,hourly;\n".format(sno))

    en_idf.write("Output:Table:SummaryReports,\
    AllSummary;              !- Report 1 Name")
    en_idf.close()
    
    if scene['viparams'].get('hvactemplate'):
        os.chdir(scene['viparams']['newdir'])
        ehtempcmd = "ExpandObjects {}".format(os.path.join(scene['viparams']['newdir'], 'in.idf'))
        subprocess.call(ehtempcmd.split())
        subprocess.call('{} {} {}'.format(scene['viparams']['cp'], os.path.join(scene['viparams']['newdir'], 'expanded.idf'), os.path.join(scene['viparams']['newdir'], 'in.idf')), shell = True)

    if 'in.idf' not in [im.name for im in bpy.data.texts]:
        bpy.data.texts.load(scene['viparams']['idf_file'])

def pregeo(op):
    scene = bpy.context.scene
    bpy.data.scenes[0].layers[0:2] = True, False
    for obj in [obj for obj in scene.objects if obj.layers[1] == True]:
        scene.objects.unlink(obj)
        bpy.data.objects.remove(obj)
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for materials in bpy.data.materials:
        if materials.users == 0:
            bpy.data.materials.remove(materials)
    
    enviobjs = [obj for obj in scene.objects if obj.envi_type in ('1', '2') and obj.layers[0] == True and obj.hide == False]
    envings = [ng for ng in bpy.data.node_groups if ng.bl_label == 'EnVi Network']
    enng = envings[0] if envings else 0
                
    for obj in enviobjs:
        for mats in obj.data.materials:
            if 'en_'+mats.name not in [mat.name for mat in bpy.data.materials]:
                mats.copy().name = 'en_'+mats.name

        selobj(scene, obj)
        selmesh('desel')
        bpy.ops.object.duplicate()

        en_obj = scene.objects.active
        obj.select, en_obj.select, en_obj.name, en_obj.data.name, en_obj.layers[1], en_obj.layers[0], bpy.data.scenes[0].layers[0:2] = False, True, 'en_'+obj.name, en_obj.data.name, True, False, (False, True)
        for s, slots in enumerate(en_obj.material_slots):
            slots.material = bpy.data.materials['en_'+obj.data.materials[s].name]
            slots.material.envi_export = True

            dcdict = {'Wall':(1,1,1), 'Partition':(0.5,0.5,0.5), 'Window':(0,1,1), 'Roof':(0,1,0), 'Ceiling':(0, 0.5, 0), 'Floor':(0.44,0.185,0.07), 'Ground':(0.22, 0.09, 0.04), 'Shading':(1, 0, 0), 'Aperture':(0, 0, 1)}
            if slots.material.envi_con_type in dcdict:
                slots.material.diffuse_color = dcdict[slots.material.envi_con_type]

        for poly in en_obj.data.polygons:
            if en_obj.data.materials[poly.material_index].envi_con_type == 'None':
                poly.select = True

        selmesh('delf')
        en_obj.select = False
        bm = bmesh.new()
        bm.from_mesh(en_obj.data)
        bm.transform(en_obj.matrix_world)
        en_obj["volume"] = bm.calc_volume()
        bm.free()

        if any([(mat.envi_afsurface or mat.envi_boundary) for mat in en_obj.data.materials]):
            enng = bpy.ops.node.new_node_tree(type='EnViN', name ="EnVi Network") if not len([ng for ng in bpy.data.node_groups if ng.bl_label == 'EnVi Network']) else [ng for ng in bpy.data.node_groups if ng.bl_label == 'EnVi Network'][0]                
            enng['enviparams'] = {'wpca': 0, 'wpcn': 0, 'crref': 0, 'afn': 0}
            if 'Control' not in [node.bl_label for node in enng.nodes]:
                enng.nodes.new(type = 'AFNCon')         
                enng.use_fake_user = 1
            if en_obj.envi_type =='1' and en_obj.name not in [node.zone for node in enng.nodes if hasattr(node, 'zone')]:
                enng.nodes.new(type = 'EnViZone').zone = en_obj.name
            elif en_obj.envi_type == '1':
                for node in enng.nodes:
                    if hasattr(node, 'zone') and node.zone == en_obj.name:
                        node.zupdate(bpy.context)
        elif enng and en_obj.name in [node.zone for node in enng.nodes if hasattr(node, 'zone')]:
            for node in enng.nodes:
                if hasattr(node, 'zone') and node.zone == en_obj.name:
                    enng.nodes.remove(node)
            
        bpy.data.scenes[0].layers[0:2] = True, False
        obj.select = True
        scene.objects.active = obj

class hcoiwrite(object):
    def __init__(self, obj):
        self.obj = obj
        self.h = 1 if self.obj.envi_hvachlt != '4' else 0
        self.c = 1 if self.obj.envi_hvacclt != '4' else 0
        self.hc = ('', 'SingleHeating', 'SingleCooling', 'DualSetpoint')[(not self.h and not self.c, self.h and not self.c, not self.h and self.c, self.h and self.c).index(1)]
        self.ctdict = {'DualSetpoint': 4, 'SingleHeating': 1, 'SingleCooling': 2}
        self.limittype = {'0': 'LimitFlowRate', '1': 'LimitCapacity', '2': 'LimitFlowRateAndCapacity', '3': 'NoLimit', '4': ''}

    def hvacschedwrite(self):
        if self.obj.envi_hvacsched:
            ths = [self.obj.hvact1, self.obj.hvact2, self.obj.hvact3, self.obj.hvact4]
            fos = [fs for fs in (self.obj.hvacf1, self.obj.hvacf2, self.obj.hvacf3, self.obj.hvacf4) if fs]
            uns = [us for us in (self.obj.hvacu1, self.obj.hvacu2, self.obj.hvacu3, self.obj.hvacu4) if us]
            ts, fs, us = rettimes(ths, fos, uns)
            return epschedwrite(self.obj.name + '_hvacsched', 'Temperature', ts, fs, us)
        else:
            return epschedwrite(self.obj.name + '_hvacsched', 'Temperature', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,1']]]])
    
    def htspwrite(self):
        if self.obj.envi_htspsched:
            ths = [self.obj.htspt1, self.obj.htspt2, self.obj.htspt3, self.obj.htspt4]
            fos = [fs for fs in (self.obj.htspf1, self.obj.htspf2, self.obj.htspf3, self.obj.htspf4) if fs]
            uns = [us for us in (self.obj.htspu1, self.obj.htspu2, self.obj.htspu3, self.obj.htspu4) if us]
            ts, fs, us = rettimes(ths, fos, uns)
            return epschedwrite(self.obj.name + '_htspsched', 'Temperature', ts, fs, us)
        else:
            return epschedwrite(self.obj.name + '_htspsched', 'Temperature', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format(self.obj.envi_htsp)]]]])

    def ctspwrite(self):
        if self.obj.envi_ctspsched:
            ths = [self.obj.ctspt1, self.obj.ctspt2, self.obj.ctspt3, self.obj.ctspt4]
            fos = [fs for fs in (self.obj.ctspf1, self.obj.ctspf2, self.obj.ctspf3, self.obj.ctspf4) if fs]
            uns = [us for us in (self.obj.ctspu1, self.obj.ctspu2, self.obj.ctspu3, self.obj.ctspu4) if us]
            tts, tfs, tus = rettimes(ths, fos, uns)
            return epschedwrite(self.obj.name + '_ctspsched', 'Temperature', tts, tfs, tus)
        else:
            return epschedwrite(self.obj.name + '_ctspsched', 'Temperature', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format(self.obj.envi_ctsp)]]]])

    def thermowrite(self):
        params = ['Name', 'Setpoint Temperature Schedule Name']
        if self.hc ==  'DualSetpoint':
            params += ['Setpoint Temperature Schedule Name 2']
            paramvs = [self.obj.name+'_tsp', self.obj.name + '_htspsched', self.obj.name + '_ctspsched']
        elif self.hc == 'SingleHeating':
            paramvs = [self.obj.name+'_tsp', self.obj.name + '_htspsched']
        elif self.hc == 'SingleCooling':
            paramvs = [self.obj.name+'_tsp', self.obj.name + '_ctspsched']
        return epentry('ThermostatSetpoint:{}'.format(self.hc), params, paramvs)

    def zc(self):
        params = ('Name', 'Zone or Zonelist Name', 'Control Type Schedule Name', 'Control 1 Object Type', 'Control 1 Name')
        paramvs = (self.obj.name+'_thermostat', self.obj.name, self.obj.name+'_thermocontrol', 'ThermostatSetpoint:{}'.format(self.hc), self.obj.name + '_tsp')
        return epentry('ZoneControl:Thermostat', params, paramvs)

    def consched(self):
        return epschedwrite(self.obj.name + '_thermocontrol', 'Control Type', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format(self.ctdict[self.hc])]]]])

    def ec(self):
        params = ('Zone Name', 'Zone Conditioning Equipment List Name', 'Zone Air Inlet Node or NodeList Name', 'Zone Air Exhaust Node or NodeList Name',
                  'Zone Air Node Name', 'Zone Return Air Node Name')
        paramvs = (self.obj.name, self.obj.name+'_Equipment', self.obj.name+'_supairnode', '', self.obj.name+'_airnode', self.obj.name+'_retairnode')
        return epentry('ZoneHVAC:EquipmentConnections', params, paramvs)

    def el(self):
        params = ('Name', 'Zone Equipment 1 Object Type', 'Zone Equipment 1 Name', 'Zone Equipment 1 Cooling Sequence', 'Zone Equipment 1 Heating or No-Load Sequence')
        paramvs = (self.obj.name+'_Equipment', 'ZoneHVAC:IdealLoadsAirSystem', self.obj.name+'_Air', 1, 1)
        return epentry('ZoneHVAC:EquipmentList', params, paramvs)

    def zh(self):
        params = ('Name', 'Availability Schedule Name', 'Zone Supply Air Node Name', 'Zone Exhaust Air Node Name',
              "Maximum Heating Supply Air Temperature ("+ u'\u00b0'+"C)", "Minimum Cooling Supply Air Temperature ("+ u'\u00b0'+"C)",
              'Maximum Heating Supply Air Humidity Ratio (kgWater/kgDryAir)', 'Minimum Cooling Supply Air Humidity Ratio (kgWater/kgDryAir)',
              'Heating Limit', 'Maximum Heating Air Flow Rate (m3/s)', 'Maximum Sensible Heating Capacity (W)',
              'Cooling limit', 'Maximum Cooling Air Flow Rate (m3/s)', 'Maximum Total Cooling Capacity (W)', 'Heating Availability Schedule Name',
              'Cooling Availability Schedule Name', 'Dehumidification Control Type', 'Cooling Sensible Heat Ratio (dimensionless)', 'Humidification Control Type',
              'Design Specification Outdoor Air Object Name', 'Outdoor Air Inlet Node Name', 'Demand Controlled Ventilation Type', 'Outdoor Air Economizer Type',
              'Heat Recovery Type', 'Sensible Heat Recovery Effectiveness (dimensionless)', 'Latent Heat Recovery Effectiveness (dimensionless)')
        paramvs = ('{}_Air'.format(self.obj.name), ('', self.obj.name+'_hvacsched')[self.obj.envi_hvacsched], '{}_supairnode'.format(self.obj.name), '', self.obj.envi_hvacht, self.obj.envi_hvacct, 0.015, 0.009, self.limittype[self.obj.envi_hvachlt],
                   '{:.4f}'.format(self.obj.envi_hvachaf) if self.obj.envi_hvachlt in ('0', '2') else '', self.obj.envi_hvacshc if self.obj.envi_hvachlt in ('1', '2') else '', self.limittype[self.obj.envi_hvacclt],
                   '{:.4f}'.format(self.obj.envi_hvaccaf) if self.obj.envi_hvacclt in ('0', '2') else '', self.obj.envi_hvacscc if self.obj.envi_hvacclt in ('1', '2') else '',
                   '', '', 'ConstantSupplyHumidityRatio', '', 'ConstantSupplyHumidityRatio', (self.obj.name + ' Outdoor Air', '')[self.obj.envi_hvacoam == '0'], '', '', '', '', '', '')
        return epentry('ZoneHVAC:IdealLoadsAirSystem', params, paramvs)
    
    def zhoa(self):
        oam = {'0':'None', '1':'Flow/Zone', '2':'Flow/Person', '3':'Flow/Area', '4':'Sum', '5':'Maximum', '6':'AirChanges/Hour'}
        params = ('Name', 'Outdoor Air  Method', 'Outdoor Air Flow per Person (m3/s)', 'Outdoor Air Flow per Zone Floor Area (m3/s-m2)', 'Outdoor Air  Flow per Zone',
        'Outdoor Air Flow Air Changes per Hour', 'Outdoor Air Flow Rate Fraction Schedule Name')
        paramvs =(self.obj.name + ' Outdoor Air', oam[self.obj.envi_hvacoam], '{:.4f}'.format(self.obj.envi_hvacfrp) if self.obj.envi_hvacoam in ('2', '4', '5') else '',
                    '{:.4f}'.format(self.obj.envi_hvacfrzfa) if self.obj.envi_hvacoam in ('3', '4', '5') else '', '{:.4f}'.format(self.obj.envi_hvacfrz) if self.obj.envi_hvacoam in ('1', '4', '5') else '', 
                    '{:.4f}'.format(self.obj.envi_hvacfach) if self.obj.envi_hvacoam in ('4', '5', '6') else '', '')          
        return epentry('DesignSpecification:OutdoorAir', params, paramvs)

    def zht(self):
        oam = {'0':'None', '1':'Flow/Zone', '2':'Flow/Person', '3':'Flow/Area', '4':'Sum', '5':'Maximum', '6':'DetailedSpecification'}
        params = ('Zone Name' , 'Thermostat Name', 'System Availability Schedule Name', 'Maximum Heating Supply Air Temperature', 'Minimum Cooling Supply Air Temperature',
                'Maximum Heating Supply Air Humidity Ratio (kgWater/kgDryAir)', 'Minimum Cooling Supply Air Humidity Ratio (kgWater/kgDryAir)', 'Heating Limit', 'Maximum Heating Air Flow Rate (m3/s)',
                'Maximum Sensible Heating Capacity (W)', 'Cooling Limit', 'Maximum Cooling Air Flow Rate (m3/s)', 'Maximum Total Cooling Capacity (W)', 'Heating Availability Schedule Name',
                'Cooling Availability Schedule Name', 'Dehumidification Control Type', 'Cooling Sensible Heat Ratio', 'Dehumidification Setpoint (percent)', 'Humidification Control Type',
                'Humidification Setpoint (percent)', 'Outdoor Air Method', 'Outdoor Air Flow Rate per Person (m3/s)', 'Outdoor Air Flow Rate per Zone Floor (m3/s-m2)', 'Outdoor Air Flow Rate per Zone (m3/s)',
                'Design Specification Outdoor Air Object', 'Demand Controlled Ventilation Type', 'Outdoor Air Economizer Type', 'Heat Recovery Type', 'Sensible Heat Recovery Effectiveness',
                'Latent Heat Recovery Effectiveness')
        paramvs = (self.obj.name, '', ('', self.obj.name+'_hvacsched')[self.obj.envi_hvacsched], self.obj.envi_hvacht, self.obj.envi_hvacct, 0.015, 0.009, self.limittype[self.obj.envi_hvachlt], self.obj.envi_hvachaf if self.obj.envi_hvachlt in ('0', '2') else '',
                   self.obj.envi_hvacshc if self.obj.envi_hvachlt in ('1', '2') else '', self.limittype[self.obj.envi_hvacclt], self.obj.envi_hvaccaf if self.obj.envi_hvacclt in ('0', '2') else '',
                    self.obj.envi_hvacscc if self.obj.envi_hvacclt in ('1', '2') else '', '', '', 'None', '', '', 'None', '', oam[self.obj.envi_hvacoam], '{:.4f}'.format(self.obj.envi_hvacfrp) if self.obj.envi_hvacoam in ('2', '4', '5') else '',
                    '{:.4f}'.format(self.obj.envi_hvacfrzfa) if self.obj.envi_hvacoam in ('3', '4', '5') else '', '{:.4f}'.format(self.obj.envi_hvacfrz) if self.obj.envi_hvacoam in ('1', '4', '5') else '', '', 'None', 'NoEconomizer', 'None', 0.7, 0.65)
        bpy.context.scene['viparams']['hvactemplate'] = 1
        return epentry('HVACTemplate:Zone:IdealLoadsAirSystem', params, paramvs)

    def peoplewrite(self):
        pdict = {'0': '', '1':'People', '2': 'People/Area', '3': 'Area/Person'}
        plist = ['', '', '']
        plist[int(self.obj.envi_occtype) - 1] = self.obj.envi_occsmax
        params =  ['Name', 'Zone or ZoneList Name', 'Number of People Schedule Name', 'Number of People Calculation Method', 'Number of People', 'People per Zone Floor Area (person/m2)',
        'Zone Floor Area per Person (m2/person)', 'Fraction Radiant', 'Sensible Heat Fraction', 'Activity Level Schedule Name']
        paramvs = [self.obj.name + "_occupancy", self.obj.name, self.obj.name + '_occsched', pdict[self.obj.envi_occtype]] + plist + [0.3, '', self.obj.name + '_actsched']
        if self.obj.envi_comfort:
            params += ['Carbon Dioxide Generation Rate (m3/s-W)', 'Enable ASHRAE 55 Comfort Warnings',
                       'Mean Radiant Temperature Calculation Type', 'Surface Name/Angle Factor List Name', 'Work Efficiency Schedule Name', 'Clothing Insulation Calculation Method', 'Clothing Insulation Calculation Method Schedule Name',
                       'Clothing Insulation Schedule Name', 'Air Velocity Schedule Name', 'Thermal Comfort Model 1 Type']
            paramvs += [3.82E-8, 'No', 'zoneaveraged', '', self.obj.name + '_wesched', 'ClothingInsulationSchedule', '', self.obj.name + '_clsched', self.obj.name + '_avsched', 'FANGER']
        return epentry('People', params, paramvs)

    def schedwrite(self):
        if self.obj.envi_occsched:
            ths = [self.obj.occt1, self.obj.occt2, self.obj.occt3, self.obj.occt4]
            fos = [fs for fs in (self.obj.occf1, self.obj.occf2, self.obj.occf3, self.obj.occf4) if fs]
            uns = [us for us in (self.obj.occu1, self.obj.occu2, self.obj.occu3, self.obj.occu4) if us]
            self.pts, self.pfs, self.pus = rettimes(ths, fos, uns)
            return epschedwrite(self.obj.name + '_occsched', 'Fraction', self.pts, self.pfs, self.pus)
        else:
            return epschedwrite(self.obj.name + '_occsched', 'Fraction', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,1']]]])

    def aschedwrite(self):
        if self.obj.envi_asched:
            aths = [self.obj.aocct1, self.obj.aocct2, self.obj.aocct3, self.obj.aocct4]
            afos = [fs for fs in (self.obj.aoccf1, self.obj.aoccf2, self.obj.aoccf3, self.obj.aoccf4) if fs]
            auns = [us for us in (self.obj.aoccu1, self.obj.aoccu2, self.obj.aoccu3, self.obj.aoccu4) if us]
            ats, afs, aus = rettimes(aths, afos, auns)
            return epschedwrite(self.obj.name + '_actsched', 'Any number', ats, afs, aus)
        else:
            return epschedwrite(self.obj.name + '_actsched', 'Any number', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format(self.obj.envi_occwatts)]]]])

    def weschedwrite(self):
        if self.obj.envi_wsched:
            wths = [self.obj.wocct1, self.obj.wocct2, self.obj.wocct3, self.obj.wocct4]
            wfos = [fs for fs in (self.obj.woccf1, self.obj.woccf2, self.obj.woccf3, self.obj.woccf4) if fs]
            wuns = [us for us in (self.obj.woccu1, self.obj.woccu2, self.obj.woccu3, self.obj.woccu4) if us]
            wts, wfs, wus = rettimes(wths, wfos, wuns)
            return epschedwrite(self.obj.name + '_wesched', 'Any number', wts, wfs, wus)
        else:
            return epschedwrite(self.obj.name + '_wesched', 'Any number', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{:.2}'.format(self.obj.envi_weff)]]]])

    def cischedwrite(self):
        return epschedwrite(self.obj.name + '_cisched', 'Any number', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format(5)]]]])

    def avschedwrite(self):
        if self.obj.envi_avsched:
            avths = [self.obj.avocct1, self.obj.avocct2, self.obj.avocct3, self.obj.avocct4]
            avfos = [fs for fs in (self.obj.avoccf1, self.obj.avoccf2, self.obj.avoccf3, self.obj.avoccf4) if fs]
            avuns = [us for us in (self.obj.avoccu1, self.obj.avoccu2, self.obj.avoccu3, self.obj.avoccu4) if us]
            avts, avfs, avus = rettimes(avths, avfos, avuns)
            return epschedwrite(self.obj.name + '_avsched', 'Any number', avts, avfs, avus)
        else:
            return epschedwrite(self.obj.name + '_avsched', 'Any number', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{:.2}'.format(self.obj.envi_airv)]]]])

    def clschedwrite(self):
        if self.obj.envi_clsched:
            cths = [self.obj.cocct1, self.obj.cocct2, self.obj.cocct3, self.obj.cocct4]
            cfos = [fs for fs in (self.obj.coccf1, self.obj.coccf2, self.obj.coccf3, self.obj.coccf4) if fs]
            cuns = [us for us in (self.obj.coccu1, self.obj.coccu2, self.obj.coccu3, self.obj.coccu4) if us]
            cts, cfs, cus = rettimes(cths, cfos, cuns)
            return epschedwrite(self.obj.name + '_clsched', 'Any number', cts, cfs, cus)
        else:
            return epschedwrite(self.obj.name + '_clsched', 'Any number', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{:.2}'.format(self.obj.envi_cloth)]]]])

    def co2(self):
        params = ('Carbon Dioxide Concentration', 'Outdoor Carbon Dioxide Schedule Name', 'Generic Contaminant Concentration', 'Outdoor Generic Contaminant Schedule Name')
        paramvs = ('Yes', 'Default outdoor CO2 levels 400 ppm', 'No', '')
        return epentry('ZoneAirContaminantBalance', params, paramvs)

    def co2sched(self):
        return epschedwrite('Default outdoor CO2 levels 400 ppm', 'Any number', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format('400')]]]])

    def zi(self):
        self.infiltype = self.obj.envi_inftype if self.obj.envi_occtype != '1' else self.obj.envi_occinftype
        self.infildict = {'0': '', '1': 'Flow/Zone', '2': 'Flow/Area', '3': 'Flow/ExteriorArea', '4': 'Flow/ExteriorWallArea',
                          '5': 'AirChanges/Hour', '6': 'Flow/Zone'}
        inflist = ['', '', '', '']
        infdict = {'1': '0', '2': '1', '3':'2', '4':'2', '5': '3', '6': '0'}
        inflevel = self.obj.envi_inflevel if self.obj.envi_occtype != '1' or self.obj.envi_occinftype != '6' else self.obj.envi_inflevel * 0.001 * self.obj.envi_occsmax
        inflist[int(infdict[self.infiltype])] = '{:.4f}'.format(inflevel)
        params = ('Name', 'Zone or ZoneList Name', 'Schedule Name', 'Design Flow Rate Calculation Method', 'Design Flow Rate {m3/s}', 'Flow per Zone Floor Area {m3/s-m2}',
               'Flow per Exterior Surface Area {m3/s-m2}', 'Air Changes per Hour {1/hr}', 'Constant Term Coefficient', 'Temperature Term Coefficient',
                'Velocity Term Coefficient', 'Velocity Squared Term Coefficient')
        paramvs = [self.obj.name + '_infiltration', self.obj.name, self.obj.name + '_infilsched', self.infildict[self.infiltype]] + inflist + [1, 0, 0, 0]
        return epentry('ZoneInfiltration:DesignFlowRate', params, paramvs)

    def zisched(self):
        if self.obj.envi_occtype == '1' and self.obj.envi_occinftype == '6':
            return epschedwrite(self.obj.name + '_infilsched', 'Fraction', self.pts, self.pfs, self.pus)
        elif self.obj.envi_infsched:
            ths = [self.obj.inft1, self.obj.inft2, self.obj.inft3, self.obj.inft4]
            fos = [fs for fs in (self.obj.inff1, self.obj.inff2, self.obj.inff3, self.obj.inff4) if fs]
            uns = [us for us in (self.obj.infu1, self.obj.infu2, self.obj.infu3, self.obj.infu4) if us]
            ts, fs, us = rettimes(ths, fos, uns)
            return epschedwrite(self.obj.name + '_infilsched', 'Fraction', ts, fs, us)
        else:
            return epschedwrite(self.obj.name + '_infilsched', 'Fraction', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format(1)]]]])
            
    def equip(self):
        edict = {'0': '', '1':'EquipmentLevel', '2': 'Watts/Area', '3': 'Watts/Person'}
        elist = ['', '', '']
        elist[int(self.obj.envi_equiptype) - 1] = self.obj.envi_equipmax
        params = ('Name', 'Zone Name', 'SCHEDULE Name', 'Design Level calculation method', 'Design Level (W)', 'Power per Zone Floor Area (Watts/m2)', 'Power per Person (Watts/person)', \
        'Fraction Latent', 'Fraction Radiant', 'Fraction Lost')
        paramvs = [self.obj.name + "_equip", self.obj.name, self.obj.name + "_equipsched", edict[self.obj.envi_equiptype]] + elist + ['0', '0', '0']
        return epentry('OtherEquipment', params, paramvs)
        
    def equipsched(self):
        if self.obj.envi_equipsched:
            ths = [self.obj.equipt1, self.obj.equipt2, self.obj.equipt3, self.obj.equipt4]
            fos = [fs for fs in (self.obj.equipf1, self.obj.equipf2, self.obj.equipf3, self.obj.equipf4) if fs]
            uns = [us for us in (self.obj.equipu1, self.obj.equipu2, self.obj.equipu3, self.obj.equipu4) if us]
            self.pts, self.pfs, self.pus = rettimes(ths, fos, uns)
            return epschedwrite(self.obj.name + '_equipsched', 'Fraction', self.pts, self.pfs, self.pus)
        else:
            return epschedwrite(self.obj.name + '_equipsched', 'Fraction', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,1']]]])

def writeafn(exp_op, en_idf, enng):
    badnodes = [node for node in enng.nodes if node.use_custom_color]
    for node in badnodes:
        node.hide = 0
        exp_op.report({'ERROR'}, 'Bad {} node in the airflow network. Delete the node if not needed or make valid connections'.format(node.name))
    if [enode for enode in enng.nodes if enode.bl_idname == 'AFNCon'] and not [enode for enode in enng.nodes if enode.bl_idname == 'EnViZone']:
        [enng.nodes.remove(enode) for enode in enng.nodes if enode.bl_idname == 'AFNCon']
    for connode in [enode for enode in enng.nodes if enode.bl_idname == 'AFNCon']:
         en_idf.write(connode.epwrite(exp_op, enng))        
    for crnode in [enode for enode in enng.nodes if enode.bl_idname == 'EnViCrRef']:
        en_idf.write(crnode.epwrite())
        enng['enviparams']['crref'] = 1
    extnodes = [enode for enode in enng.nodes if enode.bl_idname == 'EnViExt']
    zonenodes = [enode for enode in enng.nodes if enode.bl_idname == 'EnViZone']
    ssafnodes = [enode for enode in enng.nodes if enode.bl_idname == 'EnViSSFlow']
    safnodes = [enode for enode in enng.nodes if enode.bl_idname == 'EnViSFlow']

    if enng['enviparams']['wpca'] == 1:
        for extnode in extnodes:
            en_idf.write(extnode.epwrite(enng))
    for enode in zonenodes:
        en_idf.write(enode.epwrite())
    for enode in ssafnodes + safnodes:
        en_idf.write(enode.epwrite(exp_op, enng))

