import bpy, os, itertools, subprocess, datetime, shutil, mathutils, bmesh
from .vi_func import epentry, ceilheight, selobj, facearea, boundpoly, epschedwrite, selmesh
dtdf = datetime.date.fromordinal

def enpolymatexport(exp_op, node, locnode, em, ec):
    scene = bpy.context.scene
    for scene in bpy.data.scenes:
        scene.update()
    en_epw = open(locnode.weather, "r")
    en_idf = open(scene['enparams']['idf_file'], 'w')
    enng = [ng for ng in bpy.data.node_groups if ng.bl_label == 'EnVi Network'][0]
    en_idf.write("!- Blender -> EnergyPlus\n!- Using the EnVi export scripts\n!- Author: Ryan Southall\n!- Date: {}\n\nVERSION,{};\n\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), scene['enparams']['epversion']))

    params = ('Name', 'North Axis (deg)', 'Terrain', 'Loads Convergence Tolerance Value', 'Temperature Convergence Tolerance Value (deltaC)',
              'Solar Distribution', 'Maximum Number of Warmup Days(from MLC TCM)')
    paramvs = (node.loc, '0.00', ("City", "Urban", "Suburbs", "Country", "Ocean")[int(node.terrain)], '0.004', '0.4', 'FullInteriorAndExteriorWithReflections', '15')
    en_idf.write(epentry('Building', params, paramvs))
    params = ('Time Step in Hours', 'Algorithm', 'Algorithm', 'Algorithm', 'Default frequency of calculation', 'no zone sizing, system sizing, plant sizing, no design day, use weather file')
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

    for mat in [mat for mat in bpy.data.materials if mat.envi_export == True and mat.envi_con_type != "None" and not (mat.envi_con_makeup == '1' and mat.envi_layero == '0')]:
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
            curlaynames = matname[-(pm + 1):]
            namelist.append(conname)
            ec.con_write(en_idf, mat.envi_con_type, conname, str(namelist.count(conname)-1), mat.name, curlaynames)

        elif mat.envi_con_makeup == '1' and mat.envi_con_type not in ('None', 'Shading', 'Aperture'):
            thicklist = (mat.envi_export_lo_thi, mat.envi_export_l1_thi, mat.envi_export_l2_thi, mat.envi_export_l3_thi, mat.envi_export_l4_thi)
            conname = mat.name
            layers = [i for i in itertools.takewhile(lambda x: x != "0", (mat.envi_layero, mat.envi_layer1, mat.envi_layer2, mat.envi_layer3, mat.envi_layer4))]
            if len(layers) in (2, 4) and mat.envi_con_type == 'Window':
                exp_op.report({'ERROR'}, 'Wrong number of layers specified for the {} window construction'.format(mat.name))
                return
            for l, layer in enumerate(layers):
                if layer == "1" and mat.envi_con_type in ("Wall", "Floor", "Roof", "Door"):
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

                elif layer == "2" and mat.envi_con_type in ("Wall", "Floor", "Roof", "Door"):
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
    for obj in [obj for obj in bpy.context.scene.objects if obj.layers[1] == True and obj.envi_type == '0']:
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

    for obj in [obj for obj in bpy.data.objects if obj.layers[1] and obj.type == 'MESH' and obj.vi_type == '1']:
        obm, odv = obj.matrix_world, obj.data.vertices

        for poly in obj.data.polygons:
            mat = obj.data.materials[poly.material_index]
            (obc, obco, se, we) = boundpoly(obj, mat, poly, enng)

            if mat.envi_con_type in ('Wall', "Floor", "Roof") and mat.envi_con_makeup != "2":
                params = list(wfrparams) + ["X,Y,Z ==> Vertex {} (m)".format(v) for v in poly.vertices]
                paramvs = ['{}_{}'.format(obj.name, poly.index), mat.envi_con_type, mat.name, obj.name, obc, obco, se, we, 'autocalculate', len(poly.vertices)]+ ["  {0[0]:.4f}, {0[1]:.4f}, {0[2]:.4f}".format(obm * odv[v].co) for v in poly.vertices]
                en_idf.write(epentry('BuildingSurface:Detailed', params, paramvs))

            elif mat.envi_con_type in ('Door', 'Window')  and mat.envi_con_makeup != "2":
                if len(poly.vertices) > 4:
                    exp_op.report({'ERROR'}, 'Window/door in {} has more than 4 vertices'.format(obj.name))
                xav, yav, zav = obm*mathutils.Vector(poly.center)
                params = list(wfrparams) + ["X,Y,Z ==> Vertex {} (m)".format(v) for v in poly.vertices]
                paramvs = ['{}_{}'.format(obj.name, poly.index), 'Wall', 'Frame', obj.name, obc, obco, se, we, 'autocalculate', len(poly.vertices)] + ["  {0[0]:.4f}, {0[1]:.4f}, {0[2]:.4f}".format(obm * odv[v].co) for v in poly.vertices]
                en_idf.write(epentry('BuildingSurface:Detailed', params, paramvs))

                obound = ('win-', 'door-')[mat.envi_con_type == 'Door']+obco if obco else obco
                params = ['Name', 'Surface Type', 'Construction Name', 'Building Surface Name', 'Outside Boundary Condition Object', 'View Factor to Ground', 'Shading Control Name', 'Frame and Divider Name', 'Multiplier', 'Number of Vertices'] + \
                ["X,Y,Z ==> Vertex {} (m)".format(v) for v in poly.vertices]
                paramvs = [('win-', 'door-')[mat.envi_con_type == 'Door']+'{}_{}'.format(obj.name, poly.index), mat.envi_con_type, mat.name, '{}_{}'.format(obj.name, poly.index), obound, 'autocalculate', '', '', '1', len(poly.vertices)] + \
                ["  {0[0]:.4f}, {0[1]:.4f}, {0[2]:.4f}".format((xav+((obm * odv[v].co)[0]-xav)*0.95, yav+((obm * odv[v].co)[1]-yav)*0.95, zav+((obm * odv[v].co)[2]-zav)*0.95)) for v in poly.vertices]
                en_idf.write(epentry('FenestrationSurface:Detailed', params, paramvs))

            elif mat.envi_con_type == 'Shading' or obj.envi_type == '1':
                params = ['Name', 'Transmittance Schedule Name', 'Number of Vertices'] + ['X,Y,Z ==> Vertex {} (m)'.format(v) for v in range(len(poly.vertices))]
                paramvs = ['{}_{}'.format(obj.name, poly.index), '', len(poly.vertices)] + ['{0[0]:.4f}, {0[1]:.4f}, {0[2]:.4f}'.format(obm * odv[poly.vertices[v]].co) for v in range(len(poly.vertices))]
                en_idf.write(epentry('Shading:Building:Detailed', params, paramvs))

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
    en_idf.write(epschedwrite('Default outdoor CO2 levels 400 ppm', 'Any number', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format('400')]]]]))

    zonenames = [o.name for o in bpy.context.scene.objects if o.layers[1] == True and o.envi_type == '0']
    bpy.context.scene['viparams']['hvactemplate'] = 0
    zonenodes = [n for n in enng.nodes if hasattr(n, 'zone') and n.zone in zonenames]
    
    for zn in zonenodes:
        for schedtype in ('VASchedule', 'TSPSchedule', 'HVAC', 'Occupancy', 'Equipment', 'Infiltration'):
#            try:
            if schedtype == 'HVAC' and zn.inputs[schedtype].links:
                en_idf.write(zn.inputs[schedtype].links[0].from_node.eptcwrite(zn.zone))
                try:
                    en_idf.write(zn.inputs[schedtype].links[0].from_node.inputs['Schedule'].links[0].from_node.epwrite(zn.zone+'_hvacsched', 'Fraction'))                            
                except:
                    en_idf.write(epschedwrite(zn.zone + '_hvacsched', 'Fraction', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00, 1']]]]))

                hsdict = {'HSchedule': '_htspsched', 'CSchedule': '_ctspsched'}
                tvaldict = {'HSchedule': zn.inputs[schedtype].links[0].from_node.envi_htsp, 'CSchedule': zn.inputs[schedtype].links[0].from_node.envi_ctsp}
                for sschedtype in hsdict: 
                    if zn.inputs[schedtype].links[0].from_node.inputs[sschedtype].links:
                        en_idf.write(zn.inputs[schedtype].links[0].from_node.inputs[sschedtype].links[0].from_node.epwrite(zn.zone+hsdict[sschedtype], 'Temperature'))                            
                    else:
                        en_idf.write(epschedwrite(zn.zone + hsdict[sschedtype], 'Temperature', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format(tvaldict[sschedtype])]]]]))

            elif schedtype == 'Occupancy' and zn.inputs[schedtype].links:
                osdict = {'OSchedule': '_occsched', 'ASchedule': '_actsched', 'WSchedule': '_wesched', 'VSchedule': '_avsched', 'CSchedule': '_closched'}
                ovaldict = {'OSchedule': 1, 'ASchedule': zn.inputs[schedtype].links[0].from_node.envi_occwatts, 
                            'WSchedule': zn.inputs[schedtype].links[0].from_node.envi_weff, 'VSchedule': zn.inputs[schedtype].links[0].from_node.envi_airv, 
                            'CSchedule': zn.inputs[schedtype].links[0].from_node.envi_cloth}
                for sschedtype in osdict:
                    svariant = 'Fraction' if sschedtype == 'OSchedule' else 'Any Number'
                    if zn.inputs[schedtype].links[0].from_node.inputs[sschedtype].links:
                        en_idf.write(zn.inputs[schedtype].links[0].from_node.inputs[sschedtype].links[0].from_node.epwrite(zn.zone + osdict[sschedtype], svariant))
                    else:
                        en_idf.write(epschedwrite(zn.zone + osdict[sschedtype], svariant, ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{:.3f}'.format(ovaldict[sschedtype])]]]]))

            elif schedtype == 'Equipment' and zn.inputs[schedtype].links:
                if not zn.inputs[schedtype].links[0].from_node.inputs['Schedule'].links:
                    en_idf.write(epschedwrite(zn.zone + '_eqsched', 'Fraction', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,1']]]]))
                else:
                    en_idf.write(zn.inputs[schedtype].links[0].from_node.inputs['Schedule'].links[0].from_node.epwrite(zn.zone+'_eqsched', 'Fraction'))
            elif schedtype == 'Infiltration' and zn.inputs[schedtype].links:
                if not zn.inputs[schedtype].links[0].from_node.inputs['Schedule'].links:
                    en_idf.write(epschedwrite(zn.zone + '_infsched', 'Fraction', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format(1)]]]]))
                else:
                    en_idf.write(zn.inputs[schedtype].links[0].from_node.inputs['Schedule'].links[0].from_node.epwrite(zn.zone+'_infsched', 'Fraction'))
            elif schedtype == 'VASchedule' and zn.inputs[schedtype].links:
                en_idf.write(zn.inputs[schedtype].links[0].from_node.epwrite(zn.zone+'_vasched', 'Fraction'))

            elif schedtype == 'TSPSchedule' and zn.inputs[schedtype].links:
                en_idf.write(zn.inputs[schedtype].links[0].from_node.epwrite(zn.zone+'_tspsched', 'Temperature'))

#            except Exception as e:
#                print('Tuple', e)

    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: THERMOSTSTATS ===========\n\n")
    for zn in zonenodes:
        for hvaclink in zn.inputs['HVAC'].links:
            en_idf.write(hvaclink.from_node.eptspwrite(zn.zone))

    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: EQUIPMENT ===========\n\n")
    for zn in zonenodes:
        for hvaclink in zn.inputs['HVAC'].links:
            hvaczone = hvaclink.from_node
            if not hvaczone.envi_hvact:
                en_idf.write(zn.inputs['HVAC'].links[0].from_node.epewrite(zn.zone))
    
    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: HVAC ===========\n\n")
    for zn in zonenodes:
        for hvaclink in zn.inputs['HVAC'].links:
            hvacnode = hvaclink.from_node
            if hvacnode.envi_hvact:
                en_idf.write(hvacnode.hvactwrite(zn.zone))
            else:
                en_idf.write(hvacnode.ephwrite(zn.zone))

    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: OCCUPANCY ===========\n\n")
    for zn in zonenodes:
        for occlink in zn.inputs['Occupancy'].links:
            en_idf.write(occlink.from_node.epwrite(zn.zone))

    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: OTHER EQUIPMENT ===========\n\n")
    for zn in zonenodes:
        for eqlink in zn.inputs['Equipment'].links:
            en_idf.write(eqlink.from_node.oewrite(zn.zone))
   
    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: CONTAMINANTS ===========\n\n")
    for zn in zonenodes:
        for occlink in zn.inputs['Occupancy'].links:
            if occlink.from_node.envi_co2 and occlink.from_node.envi_comfort:
                params = ('Carbon Dioxide Concentration', 'Outdoor Carbon Dioxide Schedule Name', 'Generic Contaminant Concentration', 'Outdoor Generic Contaminant Schedule Name')
                paramvs = ('Yes', 'Default outdoor CO2 levels 400 ppm', 'No', '')
                en_idf.write(epentry('ZoneAirContaminantBalance', params, paramvs))
                break

    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: INFILTRATION ===========\n\n")
    for zn in zonenodes:
        for inflink in zn.inputs['Infiltration'].links:
            en_idf.write(inflink.from_node.epwrite(zn.zone))

    en_idf.write("\n!-   ===========  ALL OBJECTS IN CLASS: AIRFLOW NETWORK ===========\n\n")
    
    if enng and enng['enviparams']['afn']:
        writeafn(exp_op, en_idf, enng)

    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: EMS ===========\n\n")   
    emsprognodes = [pn for pn in enng.nodes if pn.bl_idname == 'EnViProg' and not pn.use_custom_color]
    for prognode in emsprognodes:
        en_idf.write(prognode.epwrite())
    
    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: REPORT VARIABLE ===========\n\n")
    epentrydict = {"Output:Variable,*,Zone Air Temperature,hourly;\n": node.restt,
                   "Output:Variable,*,Zone Air System Sensible Heating Rate,hourly;\n": node.restwh, "Output:Variable,*,Zone Air System Sensible Cooling Rate,hourly;\n": node.restwc,
                   "Output:Variable,*,Zone Ideal Loads Supply Air Sensible Heating Rate, hourly;\n": node.ressah, "Output:Variable,*,Zone Ideal Loads Heat Recovery Sensible Heating Rate, hourly;\n": node.reshrhw, 
                   "Output:Variable,*,Zone Ideal Loads Supply Air Sensible Cooling Rate,hourly;\n": node.ressac,
                   "Output:Variable,*,Zone Thermal Comfort Fanger Model PMV,hourly;\n": node.rescpm, "Output:Variable,*,Zone Thermal Comfort Fanger Model PPD,hourly;\n": node.rescpp, "Output:Variable,*,Zone Infiltration Current Density Volume Flow Rate, hourly;\n":node.resim,
                   "Output:Variable,*,Zone Infiltration Air Change Rate, hourly;\n": node.resiach, "Output:Variable,*,Zone Windows Total Transmitted Solar Radiation Rate,hourly;\n": node.reswsg,
                   "Output:Variable,*,AFN Node CO2 Concentration,hourly;\n": node.resco2 and enng['enviparams']['afn'], "Output:Variable,*,Zone Air CO2 Concentration,hourly;\n": node.resco2 and not enng['enviparams']['afn'],
                   "Output:Variable,*,Zone Mean Radiant Temperature,hourly;\n": node.resmrt, "Output:Variable,*,Zone People Occupant Count,hourly;\n": node.resocc,
                   "Output:Variable,*,Zone Air Relative Humidity,hourly;\n": node.resh, "Output:Variable,*,Zone Air Heat Balance Surface Convection Rate, hourly;\n": node.resfhb}
    
    for amb in ("Output:Variable,*,Site Outdoor Air Drybulb Temperature,Hourly;\n", "Output:Variable,*,Site Wind Speed,Hourly;\n", "Output:Variable,*,Site Wind Direction,Hourly;\n",
                "Output:Variable,*,Site Outdoor Air Relative Humidity,hourly;\n", "Output:Variable,*,Site Direct Solar Radiation Rate per Area,hourly;\n", "Output:Variable,*,Site Diffuse Solar Radiation Rate per Area,hourly;\n"):
        en_idf.write(amb)            
    
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
    
    if scene['enparams'].get('hvactemplate'):
        os.chdir(scene['viparams']['newdir'])
        ehtempcmd = "ExpandObjects {}".format(os.path.join(scene['viparams']['newdir'], 'in.idf'))
        subprocess.call(ehtempcmd.split())
        shutil.copyfile(os.path.join(scene['viparams']['newdir'], 'expanded.idf'), os.path.join(scene['viparams']['newdir'], 'in.idf')) 
    
    if 'in.idf' not in [im.name for im in bpy.data.texts]:
        bpy.data.texts.load(scene['enparams']['idf_file'])
    else:
        bpy.data.texts['in.idf'].filepath = scene['enparams']['idf_file']

def pregeo(op):
    scene = bpy.context.scene
    bpy.data.scenes[0].layers[0:2] = True, False
    if bpy.context.active_object and bpy.context.active_object.mode == 'EDIT':
        bpy.ops.object.editmode_toggle()
    for obj in [obj for obj in scene.objects if obj.layers[1] == True]:
        scene.objects.unlink(obj)
        bpy.data.objects.remove(obj)
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for materials in bpy.data.materials:
        if materials.users == 0:
            bpy.data.materials.remove(materials)
    
    enviobjs = [obj for obj in scene.objects if obj.vi_type == '1' and obj.layers[0] == True and obj.hide == False]

    if not [ng for ng in bpy.data.node_groups if ng.bl_label == 'EnVi Network']:
        bpy.ops.node.new_node_tree(type='EnViN', name ="EnVi Network") 
        for screen in bpy.data.screens:
            for area in [area for area in screen.areas if area.type == 'NODE_EDITOR' and area.spaces[0].tree_type == 'ViN']:
                area.spaces[0].node_tree = bpy.data.node_groups[op.nodeid.split('@')[1]]
    enng = [ng for ng in bpy.data.node_groups if ng.bl_label == 'EnVi Network'][0]
    enng.use_fake_user = True
    enng['enviparams'] = {'wpca': 0, 'wpcn': 0, 'crref': 0, 'afn': 0}
    
    [enng.nodes.remove(node) for node in enng.nodes if hasattr(node, 'zone') and node.zone[3:] not in [o.name for o in enviobjs]]
                
    for obj in enviobjs:
        obj["floorarea"] = sum([facearea(obj, face) for face in obj.data.polygons if obj.data.materials[face.material_index].envi_con_type =='Floor' and obj.envi_type == '0'])

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
            if en_obj.data.materials[poly.material_index].envi_con_type == 'None' or (en_obj.data.materials[poly.material_index].envi_con_makeup == '1' and en_obj.data.materials[poly.material_index].envi_layero == '0'):
                poly.select = True 
                
        selmesh('delf')
        en_obj.select = False
        bm = bmesh.new()
        bm.from_mesh(en_obj.data)
        bmesh.ops.triangulate(bm, faces = [face for face in bm.faces if en_obj.data.materials[face.material_index].envi_con_type == 'Shading'])
        bm.transform(en_obj.matrix_world)
        en_obj["volume"] = bm.calc_volume()
        bm.transform(en_obj.matrix_world.inverted())
        bm.to_mesh(en_obj.data)        
        bm.free()
        
        if en_obj.envi_type == '0':
            if en_obj.name not in [node.zone for node in enng.nodes if hasattr(node, 'zone')]:
                enng.nodes.new(type = 'EnViZone').zone = en_obj.name
            else:
                for node in enng.nodes:
                    if hasattr(node, 'zone') and node.zone == en_obj.name:
                        node.zupdate(bpy.context)
            for node in enng.nodes:
                if hasattr(node, 'emszone') and node.emszone == en_obj.name:
                    node.zupdate(bpy.context)

        if any([mat.envi_afsurface for mat in en_obj.data.materials]):
            enng['enviparams']['afn'] = 1
            if 'Control' not in [node.bl_label for node in enng.nodes]:
                enng.nodes.new(type = 'AFNCon')         
                enng.use_fake_user = 1
            
        bpy.data.scenes[0].layers[0:2] = True, False
        obj.select = True
        scene.objects.active = obj

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

