import bpy, os, itertools, subprocess, datetime, sys, nodeitems_utils, mathutils
from nodeitems_utils import  NodeItem
from . import vi_func
from . import vi_node
dtdf = datetime.date.fromordinal
#from subprocess import PIPE, Popen, STDOUT
#from math import pi, sin, cos, acos, asin
s = 70

def enpolymatexport(exp_op, node, em, ec):
#    daytypes = ("AllDays", "Weekdays", "Weekends")
#    lineends = (",\n", ";\n\n", ",\n", ";\n\n")
    scene = bpy.context.scene
    for scene in bpy.data.scenes:
        scene.update()
    en_epw = open(node.weather, "r")
    en_idf = open(node.idf_file, 'w')

    en_idf.write("!- Blender -> EnergyPlus\n\
!- Using the EnVi export scripts\n\
!- Author: Ryan Southall\n\
!- Date: {1}\n\n\
{2:{width}}!- EnergyPlus Version Identifier\n\n\
Building,\n\
{3:{width}}!- Name\n\
{4:{width}}!- North Axis (deg)\n\
{5:{width}}!- Terrain\n\
{6:{width}}!- Loads Convergence Tolerance Value\n\
{7:{width}}!- Temperature Convergence Tolerance Value (deltaC)\n\
{8:{width}}!- Solar Distribution\n\
{9:{width}}!- Maximum Number of Warmup Days (from MLC TCM)\n\n\
{10:{width}}!- Time Step in Hours \n\
SurfaceConvectionAlgorithm:Inside, TARP;                              !- Algorithm \n\
SurfaceConvectionAlgorithm:Outside, TARP;                             !- Algorithm \n\
HeatBalanceAlgorithm, ConductionTransferFunction; \n\
ShadowCalculation, AverageOverDaysInFrequency, 10;                    !- (default frequency of calculation)\n\
SimulationControl, No,No,No,No,Yes;                                   !- no zone sizing, system sizing, plant sizing, no design day, use weather file\n\n".format(',',
datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "VERSION,8.0.0;", "    "+node.loc+",", "    0.000,", ("    City,", "    Urban,", "    Suburbs,", "    Country,", "    Ocean,")[int(node.terrain)],
'    0.004,', '    0.4,', '    FullExteriorWithReflections,', '    15;', 'Timestep,  '+str(node.timesteps)+';', width = s))

    en_idf.write("RunPeriod,\n\
    {0:{width}}!- Name\n\
    {1:<{width}}!- Begin Month\n\
    {2:<{width}}!- Begin Day\n\
    {3:<{width}}!- End Month\n\
    {4:<{width}}!- End Day\n\
    {5:{width}}!- Day of Week for Start Day\n\
    {6:{width}}!- Use Weather File Holidays and Special Days\n\
    {6:{width}}!- Use Weather File Daylight Saving Period\n\
    {7:{width}}!- Apply Weekend Holiday Rule\n\
    {6:{width}}!- Use Weather File Rain Indicators\n\
    {6:{width}}!- Use Weather File Snow Indicators\n\
    {8:{width}}!- Number of Times Runperiod to be Repeated\n\n".format(",", str(dtdf(node.sdoy).month)+',', str(dtdf(node.sdoy).day)+',', \
    str(dtdf(node.edoy).month)+',', str(dtdf(node.edoy).day)+',', "UseWeatherFile,", "Yes,", "No,", "1;","", width = s-4))

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
    matcount = []
    matname = []
#    customcount = []
    namelist = []


    if 'Window' in [mat.envi_con_type for mat in bpy.data.materials] or 'Door' in [mat.envi_con_type for mat in bpy.data.materials]:
        en_idf.write('Material,\n\
    {0:{width}}!- Name\n\
    {1:{width}}!- Roughness\n\
    {2:{width}}!- Thickness (m)\n\
    {3:{width}}!- Conductivity (W/m-K)\n\
    {4:{width}}!- Density (kg/m3)\n\
    {5:{width}}!- Specific Heat (J/kg-K)\n\
    {6:{width}}!- Thermal Absorptance\n\
    {7:{width}}!- Solar Absorptance\n\
    {8:{width}}!- Visible Absorptance\n\n\
Construction,\n\
    {9:{width}}!- Name\n\
    {10:{width}}!- Outside Layer\n\n'.format('Wood frame,', 'Rough,', '0.12,', '0.1,', '1400.000,', '1000,', '0.9,', '0.6,', '0.6;' , 'Frame,', 'Wood frame;', width = s))


    for mat in [mat for mat in bpy.data.materials if mat.envi_export == True and mat.envi_con_type != "None"]:
        if mat.envi_con_makeup == '1':
            matname = []
            if mat.envi_layero != '0':
                if mat.envi_layero == '1':
                    if mat.envi_con_type in ('Wall', "Floor", "Roof", "Door"):
                        cono = [co for co, con in enumerate(('0', '1', '2', '3', '4', '5', '6')) if mat.envi_layeroto == con][0]
                        typelist = (mat.envi_export_bricklist_lo, mat.envi_export_concretelist_lo, mat.envi_export_metallist_lo, mat.envi_export_stonelist_lo, mat.envi_export_woodlist_lo, mat.envi_export_gaslist_lo, mat.envi_export_insulationlist_lo)[cono]
                        conlist = (em.brick_dat, em.concrete_dat, em.metal_dat, em.stone_dat, em.wood_dat, em.gas_dat, em.insulation_dat)[cono]
                        if cono != 5:
                            en_idf.write("Material,\n" +
                                "{0:{width}}! - Name\n".format("    "+typelist+ "-"+str(matcount.count(typelist))+",", width = s) +
                                "{0:{width}}! - Roughness\n".format("    "+conlist[typelist][0]+",", width = s) +
                                "{0:{width}}! - Thickness (m)\n".format("    "+str(float(mat.envi_export_lo_thi)/1000)+",", width = s) +
                                "{0:{width}}! - Conductivity (W/m-K)\n".format("    "+str(conlist[typelist][1])+",", width = s) +
                                "{0:{width}}! - Density (kg/m3)\n".format("    "+str(conlist[typelist][2])+",", width = s) +
                                "{0:{width}}! - Specific Heat (J/kg-K)\n".format("    "+str(conlist[typelist][3])+",", width = s) +
                                "{0:{width}}! - Thermal Absorptance\n".format("    "+str(conlist[typelist][4])+",", width = s) +
                                "{0:{width}}! - Solar Absorptance\n".format("    "+str(conlist[typelist][5])+",", width = s) +
                                "{0:{width}}! - Visible Absorptance\n\n".format("    "+str(conlist[typelist][6])+";", width = s))
                        else:
                            en_idf.write("Material:AirGap,\n" +
                            "{0:{width}}! - Name\n".format("    "+(typelist)+'-'+str(matcount.count(typelist)), width = s)+"," +
                            "{0:{width}}! - Thermal Resistance (m2-K/W)\n\n".format(str(conlist[typelist][2])+";", width = s))
                        matname.append((typelist)+'-'+str(matcount.count(typelist)))
                        matcount.append(typelist)

                    elif mat.envi_con_type == 'Window':
                        cono = [co for co, con in enumerate(('0', '1')) if mat.envi_layerott == con][0]
                        typelist = (mat.envi_export_glasslist_lo, mat.envi_export_gaslist_lo)[cono]
                        conlist = (em.glass_dat, em.gas_dat)[cono]
                        if cono == 0:
                            en_idf.write("WindowMaterial:Glazing,\n" +
                            "{0:{width}}! - Name\n".format("    "+typelist+"-"+str(matcount.count(typelist))+",", width = s) +
                            "{0:{width}}! - Optical Data Type\n".format("    "+conlist[typelist][1]+",", width = s) +
                            "{0:{width}}! - Window Glass Spectral Data Set Name\n".format("    "+conlist[typelist][2]+",", width = s) +
                            "{0:{width}}! - Thickness (m)\n".format("    "+conlist[typelist][3]+",", width = s) +
                            "{0:{width}}! - Solar Transmittance at Normal Incidence\n".format("    "+conlist[typelist][4]+",", width = s) +
                            "{0:{width}}! - Front Side Solar Reflectance at Normal Incidence\n".format("    "+conlist[typelist][5]+",", width = s) +
                            "{0:{width}}! - Back Side Solar Reflectance at Normal Incidence\n".format("    "+conlist[typelist][6]+",", width = s) +
                            "{0:{width}}! - Visible Transmittance at Normal Incidence\n".format("    "+conlist[typelist][7]+",", width = s) +
                            "{0:{width}}! - Front Side Visible Reflectance at Normal Incidence\n".format("    "+conlist[typelist][8]+",", width = s) +
                            "{0:{width}}! - Back Side Visible Reflectance at Normal Incidence\n".format("    "+conlist[typelist][9]+",", width = s) +
                            "{0:{width}}! - Infrared Transmittance at Normal Incidence\n".format("    "+conlist[typelist][10]+",", width = s) +
                            "{0:{width}}! - Front Side Infrared Hemispherical Emissivity\n".format("    "+conlist[typelist][11]+",", width = s) +
                            "{0:{width}}! - Back Side Infrared Hemispherical Emissivity\n".format("    "+conlist[typelist][12]+",", width = s) +
                            "{0:{width}}! - Conductivity (W/m-K)\n\n".format("    "+conlist[typelist][13]+";", width = s))
                        matname.append((typelist)+'-'+str(matcount.count(typelist)))
                        matcount.append(typelist)

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
                if layer == "1" and mat.envi_con_type in ("Wall", "Foor", "Roof"):
                    mats = ((mat.envi_export_bricklist_lo, mat.envi_export_claddinglist_lo, mat.envi_export_concretelist_lo, mat.envi_export_metallist_lo, mat.envi_export_stonelist_lo, mat.envi_export_woodlist_lo, mat.envi_export_gaslist_lo, mat.envi_export_insulationlist_lo), \
                    (mat.envi_export_bricklist_l1, mat.envi_export_claddinglist_l1, mat.envi_export_concretelist_l1, mat.envi_export_metallist_l1, mat.envi_export_stonelist_l1, mat.envi_export_woodlist_l1, mat.envi_export_gaslist_l1, mat.envi_export_insulationlist_l1), \
                    (mat.envi_export_bricklist_l2, mat.envi_export_claddinglist_l2, mat.envi_export_concretelist_l2, mat.envi_export_metallist_l2, mat.envi_export_stonelist_l2, mat.envi_export_woodlist_l2, mat.envi_export_gaslist_l2, mat.envi_export_insulationlist_l2), \
                    (mat.envi_export_bricklist_l3, mat.envi_export_claddinglist_l3, mat.envi_export_concretelist_l3, mat.envi_export_metallist_l3, mat.envi_export_stonelist_l3, mat.envi_export_woodlist_l3, mat.envi_export_gaslist_l3, mat.envi_export_insulationlist_l3), \
                    (mat.envi_export_bricklist_l4, mat.envi_export_claddinglist_l4, mat.envi_export_concretelist_l4, mat.envi_export_metallist_l4, mat.envi_export_stonelist_l4, mat.envi_export_woodlist_l4, mat.envi_export_gaslist_l4, mat.envi_export_insulationlist_l4))\
                    [l][int((mat.envi_layeroto, mat.envi_layer1to, mat.envi_layer2to, mat.envi_layer3to, mat.envi_layer4to)[l])]
                    if mats not in em.gas_dat:
                        params = [str(mat)+(",", ",", ",", ",", ",", ",", ";", ",")[x] for x, mat in enumerate(em.matdat[mats])]
                        em.omat_write(en_idf, mats+"-"+str(matcount.count(mats)), params, str(thicklist[l]/1000))
                    else:
                        params = [em.matdat[presetmat][2]+';']
                        em.amat_write(en_idf, mats+"-"+matcount.count(mats), params, str(thicklist[l]/1000))

                elif layer == "1" and mat.envi_con_type == "Window":
                    mats = ((mat.envi_export_glasslist_lo, mat.envi_export_wgaslist_l1, mat.envi_export_glasslist_l2, mat.envi_export_wgaslist_l3, mat.envi_export_glasslist_l4)[l])
                    if l in (0, 2, 4):
                        params = [str(mat)+(",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",", ",",";")[x] for x, mat in enumerate(em.matdat[mats])]
                        em.tmat_write(en_idf, presetmat+"-"+str(em.namedict[presetmat]), params, str(thicklist[l]/1000))
                    else:
                        params = [str(mat)+( ",", ",", ",")[x] for x, mat in enumerate(em.matdat[mats])]
                        em.gmat_write(en_idf, presetmat+"-"+str(em.namedict[presetmat]), params, str(thicklist[l]/1000))

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

            en_idf.write('Construction,\n    {:{width}}{}\n'.format(mat.name+",", "!- Name", width = s-4))
            for i, mn in enumerate(conlist):
                en_idf.write("    {0:{width}}{1}".format(mn+(',', ';')[len(conlist) == i + 1], "!- Layer "+str(i)+('\n', '\n\n')[len(conlist) == i + 1], width = s-4))



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
            "    {0:{width}}!- Ceiling Height (m)\n".format("{:.3f}".format(vi_func.ceilheight(obj, [])) + ",", width = s - 4) +
            "    {0:{width}}!- Volume (m3)\n".format("{:.2f}".format(vi_func.objvol(obj)) + ",", width = s - 4) +
            "    autocalculate,                                                    !- Floor Area (m2)\n" +
            "    TARP,                                                             !- Zone Inside Convection Algorithm\n"+
            "    TARP,                                                             !- Zone Outside Convection Algorithm\n"+
            "    Yes;                                                              !- Part of Total Floor Area\n\n")


    en_idf.write("GlobalGeometryRules,\n" +
        "    UpperRightCorner,                                                  !- Starting Vertex Position\n" +
        "    Counterclockwise,                                                 !- Vertex Entry Direction\n" +
        "    World;                                                            !- Coordinate System\n\n")

    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: SURFACE DEFINITIONS ===========\n\n")

    for obj in [obj for obj in bpy.data.objects if obj.layers[1] and obj.type == 'MESH' and obj.envi_type != '0']:
        obm, odv = obj.matrix_world, obj.data.vertices
        obj["floorarea"] = sum([vi_func.triarea(obj, face) for face in obj.data.polygons if obj.data.materials[face.material_index].envi_con_type =='floor'])
        for poly in obj.data.polygons:
            mat = obj.data.materials[poly.material_index]
            (obc, obco, se, we) = vi_func.boundpoly(obj, mat, poly)

            if mat.envi_con_type in ('Wall', "Floor", "Roof") and mat.envi_con_makeup != "2":
                en_idf.write('\nBuildingSurface:Detailed,\n' +
                "    {0:{width}}!- Name\n".format(obj.name+'_'+str(poly.index)+",", width = s) +
                "    {0:{width}}!- Surface Type\n".format(mat.envi_con_type + ",", width = s) +
                "    {0:{width}}!- Construction Name\n".format(mat.name+",", width = s) +
                "    {0:{width}}!- Zone Name\n".format(obj.name+",", width = s) +
                "    {0:{width}}!- Outside Boundary Condition\n".format(obc+",", width = s) +
                "    {0:{width}}!- Outside Boundary Condition Object\n".format(obco+",", width = s) +
                "    {0:{width}}!- Sun Exposure\n" .format(se+",", width = s) +
                "    {0:{width}}!- Wind Exposure\n" .format(we+",", width = s) +
                "    {0:{width}}!- View Factor to Ground\n".format("autocalculate,", width = s) +
                "    {0:{width}}!- Number of Vertices\n".format(str(len(poly.vertices))+",", width = s))
                for vert in poly.vertices:
                    en_idf.write("    {0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}{1:{width}} {2}".format(obm * odv[vert].co, (',', ';')[vert == poly.vertices[-1]], "!- X,Y,Z ==> Vertex "+str(vert)+" {m}\n", width = s - 16))

                if mat.envi_con_type == "Floor":
                    obj["floorarea"] = obj["floorarea"] + poly.area

            elif  mat.envi_con_type in ('Door', 'Window'):
                xav, yav, zav = obm*mathutils.Vector(poly.center)
                en_idf.write('BuildingSurface:Detailed,\n'\
                "    {:{width}}!- Name\n".format(obj.name+'_'+str(poly.index)+",", width = s - 4) +
                "    Wall,                                                             !- Surface Type\n"+
                "    Frame,                                                     !- Construction Name\n"+
                "    {:{width}}!- Zone Name\n".format(obj.name+",", width = s - 4) +
                "    {0:{width}}!- Outside Boundary Condition\n".format(obc+",", width = s) +
                "    {0:{width}}!- Outside Boundary Condition Object\n".format(obco+",", width = s) +
                "    {0:{width}}!- Sun Exposure\n" .format(se+",", width = s) +
                "    {0:{width}}!- Wind Exposure\n" .format(we+",", width = s) +
                "    autocalculate,                                                    !- View Factor to Ground\n" +
                "    {0:{width}}!- Number of Vertices\n".format(str(len(poly.vertices))+",", width = s))
                for vert in poly.vertices:
                        en_idf.write("  {0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}{1:{width}}{2}".format(obm * odv[vert].co, (',', ';')[vert == poly.vertices[-1]], "!- X,Y,Z ==> Vertex "+str(vert)+" {m}\n", width = s - 16))


                en_idf.write('\nFenestrationSurface:Detailed,\n\
                {0}!- Name\n\
                {1:{width}}!- Surface Type\n\
                {2:{width}}!- Construction Name\n\
                {3:{width}}!- Building Surface Name\n\
                {4:{width}}!- Outside Boundary Condition Object\n\
                {5:{width}}!- View Factor to Ground\n\
                {6:{width}}!- Shading Control Name\n\
                {6:{width}}!- Frame and Divider Name\n\
                {7:{width}}!- Multiplier\n\
                {8:{width}}!- Number of Vertices\n'.format(('win-', 'door-')[mat.envi_con_type == 'Door']+obj.name+'_'+str(poly.index)+',', mat.envi_con_type+',', mat.name+',', obj.name+'_'+str(poly.index)+',', obco+',', 'autocalculate,', ',', '1,', str(len(poly.vertices))+",", width = s))
                for vert in poly.vertices:
                     en_idf.write("  {0[0]:.3f}, {0[1]:.3f}, {0[2]:.3f}{1:{width}}{2}".format((xav+((obm * odv[vert].co)[0]-xav)*0.95, yav+((obm * odv[vert].co)[1]-yav)*0.95, zav+((obm * odv[vert].co)[2]-zav)*0.95), (',', ';')[vert == poly.vertices[-1]], "!- X,Y,Z ==> Vertex "+str(vert)+" {m}\n", width = s - 8))

            elif mat.envi_con_type == 'Shading':
                en_idf.write('\nShading:Building:Detailed,\n' +
                "{0:{width}}! - Name\n".format("    "+obj.name+'_'+str(poly.index)+",",  width = s) +
                "{0:{width}}! - Transmittance Schedule Name\n".format("    ,",  width = s) +
                "{0:{width}}! - Number of Vertices\n".format("    3,",  width = s) +
                "{0}{1[0]:.3f}, {1[1]:.3f}, {1[2]:.3f}, {2}".format("       ", obm * odv[poly.vertices[0]].co,  "                                          !- X,Y,Z ==> Vertex 1 {m}\n") +
                "{0}{1[0]:.3f}, {1[1]:.3f}, {1[2]:.3f}, {2}".format("       ", obm * odv[poly.vertices[1]].co,  "                                          !- X,Y,Z ==> Vertex 1 {m}\n") +
                "{0}{1[0]:.3f}, {1[1]:.3f}, {1[2]:.3f}; {2}".format("       ", obm * odv[poly.vertices[2]].co,  "                                          !- X,Y,Z ==> Vertex 1 {m}\n\n"))

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
            en_idf.write("ThermostatSetpoint:DualSetpoint,\n\
    %s Dual Setpoint,%s!- Name\n" %(obj.name, spformat("Dual Setpoint "+obj.name)) +"\
    Heating Setpoints %s,%s!- Setpoint Temperature Schedule Name\n" %(obj.name, spformat("Heating Setpoints "+obj.name))+"\
    Cooling Setpoints %s;%s!- Setpoint Temperature Schedule Name\n\n" %(obj.name, spformat("Cooling Setpoints "+obj.name)))
            ct = 4

        elif cool:
            en_idf.write("ThermostatSetpoint:SingleCooling,\n\
    %s Cooling Setpoint,%s!- Name\n" %(obj.name, spformat("Cooling Setpoint "+obj.name)) +"\
    Cooling Setpoints %s;%s!- Setpoint Temperature Schedule Name\n\n" %(obj.name, spformat("Cooling Setpoints "+obj.name)))
            ct = 2
        elif heat:
            en_idf.write("ThermostatSetpoint:SingleHeating,\n\
    %s Heating Setpoint,%s!- Name\n" %(obj.name, spformat("Heating Setpoint "+obj.name)) +"\
    Heating Setpoints %s;%s!- Setpoint Temperature Schedule Name\n\n" %(obj.name, spformat("Heating Setpoints "+obj.name)))
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

            en_idf.write("ZoneHVAC:IdealLoadsAirSystem,\n\
    %s_Air,%s!- Name\n" %(obj.name, spformat(obj.name+"_Air")) +"\
    ,%s!- Availability Schedule Name\n"%(spformat("")) +"\
    %s_supairnode,%s!- Zone Supply Air Node Name\n" %(obj.name, spformat(obj.name+"_supairnode")) +"\
    ,%s!- Zone Exhaust Air Node Name\n" %(spformat("")) +"\
    50,%s!- Maximum Heating Supply Air Temperature {C}\n" %(spformat("50")) +"\
    10,%s!- Minimum Cooling Supply Air Temperature {C}\n" %(spformat("10")) +"\
    0.015,%s!- Maximum Heating Supply Air Humidity Ratio {kg-H2O/kg-air}\n" %(spformat("0.015")) +"\
    0.009,%s!- Minimum Cooling Supply Air Humidity Ratio {kg-H2O/kg-air}\n" %(spformat("0.009")) +"\
    LimitCapacity,%s!- Heating Limit\n" %(spformat("LimitCapacity")) +"\
    ,%s!- Maximum Heating Air Flow Rate {m3/s}\n" %(spformat("")) +"\
    %s,%s!- Maximum Sensible Heating Capacity {W}\n" %(obj.envi_heats1c, spformat(obj.envi_heats1c)) +"\
    LimitCapacity,%s!- Cooling Limit\n" %(spformat("LimitCapacity")) +"\
    ,%s!- Maximum Cooling Air Flow Rate {m3/s}\n" %(spformat("")) +"\
    %s,%s!- Maximum Total Cooling Capacity {W}\n" %(obj.envi_cools1c, spformat(obj.envi_cools1c)) +"\
    ,%s!- Heating Availability Schedule Name\n" %(spformat("")) +"\
    ,%s!- Cooling Availability Schedule Name\n" %(spformat("")) +"\
    ConstantSupplyHumidityRatio,%s!- Dehumidification Control Type\n" %(spformat("ConstantSupplyHumidityRatio")) +"\
    ,%s!- Cooling Sensible Heat Ratio {dimensionless}\n" %(spformat("")) +"\
    ConstantSupplyHumidityRatio,%s!- Humidification Control Type\n" %(spformat("ConstantSupplyHumidityRatio")) +"\
    ,%s!- Design Specification Outdoor Air Object Name\n" %(spformat("")) +"\
    ,%s!- Outdoor Air Inlet Node Name\n" %(spformat("")) +"\
    ,%s!- Demand Controlled Ventilation Type\n" %(spformat("")) +"\
    ,%s!- Outdoor Air Economizer Type\n" %(spformat("")) +"\
    ,%s!- Heat Recovery Type\n" %(spformat("")) +"\
    ,%s!- Sensible Heat Recovery Effectiveness {dimensionless}\n" %(spformat("")) +"\
    ;%s!- Latent Heat Recovery Effectiveness {dimensionless}\n\n" %(spformat("")))

            en_idf.write("NodeList,\n\
    %sInlets,%s!- Name\n" %(obj.name, spformat(obj.name+"Inlets")) +"\
    %s_supairnode;%s!- Node 1 Name\n\n" %(obj.name, spformat(obj.name+"_supairnode")))



        if obj.envi_occtype != "0":
            occ = occupancy(obj)


            en_idf.write("Schedule:Compact,\n\
    "+obj.name+" Occupancy,%s!- Name\n" %(spformat(obj.name+" Occupancy")) + "\
    Fraction,%s!- Schedule Type Limits Name\n" %(spformat("Fraction")) + "\
    Through: 12/31,\n\
%s" %(occ.writeuf()))

            en_idf.write("People,\n\
    %s,%s!- Name\n" %(obj.name+" Occupancy Schedule", spformat(obj.name+" Occupancy Schedule")) +"\
    %s,%s!- Zone or ZoneList Name\n" %(obj.name, spformat(obj.name)) + "\
    %s,%s!- Number of People Schedule Name\n" %(obj.name+" Occupancy", spformat(obj.name+" Occupancy")) +"\
    People,"+spformat("People")+ "!- Number of People Calculation Method\n\
    %s,%s!- Number of People\n" %((obj.envi_occsmax, "", "")[int(obj.envi_occtype)-1], spformat((obj.envi_occsmax, "", "")[int(obj.envi_occtype)-1])) +"\
    %s,%s!- People per Zone Floor Area {person/m2}\n" %(( "", obj.envi_occsmax, "")[int(obj.envi_occtype)-1], spformat(( "", obj.envi_occsmax, "")[int(obj.envi_occtype)-1])) +"\
    %s,%s!- Zone Floor Area per Person {m2/person}\n" %(("", "", obj.envi_occsmax)[int(obj.envi_occtype)-1], spformat(("", "", obj.envi_occsmax)[int(obj.envi_occtype)-1])) +"\
    0.7,%s!- Fraction Radiant\n" %(spformat("0.7")) + "\
    ,%s!- Sensible Heat Fraction\n" %(spformat("")) + "\
    %s Activity Lvl;%s!- Activity Level Schedule Name\n\n" %(obj.name, spformat(obj.name+" Activity Lvl")))

            en_idf.write("Schedule:Compact,\n\
    %s Activity Lvl,%s!- Name\n" %(obj.name, spformat(obj.name+" Activity Lvl")) +"\
    Any Number,%s!- Schedule Type Limits Name\n" %(spformat("Any Number")) +"\
    Through:12/31,\n\
%s" %(occ.writeactivity()))

        if (obj.envi_inftype != "0" and obj.envi_occtype == "0") or (obj.envi_occinftype != "0" and obj.envi_occtype != "0"):
            infil = infiltration(obj)
            en_idf.write("ZoneInfiltration:DesignFlowRate, \n\
    %s Infiltration,%s!- Name\n" %(obj.name, spformat(obj.name + " Infiltration")) +"\
    %s,%s!- Zone or ZoneList Name\n" %(obj.name, spformat(obj.name)) +"\
    %s Infiltration Schedule,%s!- Schedule Name\n" %(obj.name, spformat(obj.name +" Infiltration Schedule")) +"\
    %s,%s!- Design Flow Rate Calculation Method\n" %(infil.infilcalc, spformat(infil.infilcalc)) +"\
    %s,%s!- Design Flow Rate {m3/s}\n" %(infil.infilmax[0], spformat(infil.infilmax[0])) +"\
    %s,%s!- Flow per Zone Floor Area {m3/s-m2}\n" %(infil.infilmax[1], spformat(infil.infilmax[1])) +"\
    %s,%s!- Flow per Exterior Surface Area {m3/s-m2}\n" %(infil.infilmax[2], spformat(infil.infilmax[2])) +"\
    %s,%s!- Air Changes per Hour {1/hr}\n" %(infil.infilmax[3], spformat(infil.infilmax[3])) +"\
    1.0000,%s!- Constant Term Coefficient\n" %(spformat("1.0000")) +"\
    0.0000,%s!- Temperature Term Coefficient\n" %(spformat("0.0000")) +"\
    0.0000,%s!- Velocity Term Coefficient\n" %(spformat("0.0000")) +"\
    0.0000;%s!- Velocity Squared Term Coefficient\n\n" %(spformat("1.0000")))

            if obj.envi_occtype != "0" and obj.envi_occinftype == "1":
                en_idf.write("Schedule:Compact,\n\
    %s Infiltration Schedule,%s!- Name\n" %(obj.name, spformat(obj.name + " Infiltration Schedule")) +"\
    Any Number,%s!- Schedule Type Limits Name\n" %(spformat("Any Number")) +"\
    THROUGH: 12/31,\n\
    %s" %(infil.writeinfuf(occ, obj)))

            else:
                en_idf.write("Schedule:Compact,\n\
    %s Infiltration Schedule,%s!- Name\n" %(obj.name, spformat(obj.name + " Infiltration Schedule")) +"\
    Any Number,%s!- Schedule Type Limits Name\n" %(spformat("Any Number")) +"\
    THROUGH: 12/31,\n\
    FOR: AllDays,\n\
    UNTIL: 24:00,1;\n\n")

    writeafn(en_idf)

    en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: REPORT VARIABLE ===========\n\n")

    if node.resat == True:
        en_idf.write("Output:Variable,*,Site Outdoor Air Drybulb Temperature,Hourly;\n")
    if node.resaws == True:
        en_idf.write("Output:Variable,*,Site Wind Speed,Hourly;\n")
    if node.resawd == True:
        en_idf.write("Output:Variable,*,Site Wind Direction,Hourly;\n")
    if node.resah == True:
        en_idf.write("Output:Variable,*,Site Outdoor Air Relative Humidity,hourly;\n")
    if node.resasb == True:
        en_idf.write("Output:Variable,*,Site Direct Solar Radiation Rate per Area,hourly;\n")
    if node.resasd == True:
        en_idf.write("Output:Variable,*,Site Diffuse Solar Radiation Rate per Area,hourly;\n")
    if node.restt == True:
        en_idf.write("Output:Variable,*,Zone Air Temperature,hourly;\n")
    if node.restwh == True:
        en_idf.write("Output:Variable,*,Zone Air System Sensible Heating Rate,hourly;\n")
    if node.restwc == True:
        en_idf.write("Output:Variable,*,Zone Air System Sensible Cooling Rate,hourly;\n")
    if node.rescpm == True:
        en_idf.write("Output:Variable,*,FangerPMV,hourly;\n")
    if node.rescpp == True:
        en_idf.write("Output:Variable,*,FangerPPD,hourly;\n")
    if node.resims == True:
        en_idf.write("Output:Variable,*,Zone Infiltration Current Density Volume Flow Rate [m3/s], hourly;\n")
    if node.reswsg == True:
        en_idf.write("Output:Variable,*,Zone Windows Total Transmitted Solar Radiation Rate [W],hourly;\n")
    if node.resco2 == True:
        en_idf.write("Output:Variable,*,AFN Node CO2 Concentration,hourly;\n")
    if node.resl12ms == True:
        print([cnode for cnode in bpy.data.node_groups['EnVi Network'].nodes if cnode.bl_idname == 'EnViCLink'])
        for cnode in [cnode for cnode in bpy.data.node_groups['EnVi Network'].nodes if cnode.bl_idname == 'EnViCLink']:
            for su in cnode['surf']:
                en_idf.write("Output:Variable,{},AFN Linkage Node 1 to Node 2 Volume Flow Rate,hourly;\n".format(su))
#        for i in range(1, 1 + len([snode for snode in bpy.data.node_groups['EnVi Network'] if snode.bl_idname == 'EnViSLinkNode' and snode.inputs['Node 1'].is_linked])):
#            en_idf.write("Output:Variable,Componentflow_{},AFN Linkage Node 1 to Node 2 Volume Flow Rate,timestep;\n".format(i))
    en_idf.close()
    if 'in.idf' not in [im.name for im in bpy.data.texts]:
        bpy.data.texts.load(node.idf_file)

    if sys.platform == "win32":
        subprocess.call(node.cp+'"'+node.weather+'" '+node.newdir+node.fold+"in.epw", shell = True)
        subprocess.call(node.cp+'"'+os.path.dirname( os.path.realpath( __file__ ) )+node.fold+"EPFiles"+node.fold+"Energy+.idd"+'" '+node.newdir+node.fold, shell = True)
    else:
        subprocess.call(node.cp+node.weather+" "+node.newdir+node.fold+"in.epw", shell = True)
        subprocess.call(node.cp+os.path.dirname( os.path.realpath( __file__ ) )+node.fold+"EPFiles"+node.fold+"Energy+.idd "+node.newdir+node.fold, shell = True)

def pregeo():
    for obj in [obj for obj in bpy.context.scene.objects if obj.layers[1] == True]:
        bpy.context.scene.objects.unlink(obj)
        bpy.data.objects.remove(obj)
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for materials in bpy.data.materials:
        if materials.users == 0:
            bpy.data.materials.remove(materials)

    for obj in [obj for obj in bpy.context.scene.objects if obj.envi_type in ('1', '2') and obj.layers[0] == True]:
        if 'EnVi Network' not in bpy.data.node_groups.keys():
            bpy.ops.node.new_node_tree(type='EnViN', name ="EnVi Network")
            bpy.data.node_groups['EnVi Network'].use_fake_user = 1

        obj["volume"] = vi_func.objvol(obj)
        bpy.data.scenes[0].layers[0:2] = (True, False)

        for mats in obj.data.materials:
            if 'en_'+mats.name not in [mat.name for mat in bpy.data.materials]:
                mats.copy().name = 'en_'+mats.name

        bpy.context.scene.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')

        obj.select = True
        bpy.ops.object.mode_set(mode = "EDIT")
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.duplicate()

        en_obj = bpy.context.scene.objects.active
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
            if slots.material.envi_con_type == 'Wall':
                slots.material.diffuse_color = (1, 1, 1)
            if slots.material.envi_con_type == 'Partition':
                slots.material.diffuse_color = (0.5, 0.5, 0.5)
            if slots.material.envi_con_type == 'Window':
                slots.material.diffuse_color = (0, 1, 1)
            if slots.material.envi_con_type == 'Roof':
                slots.material.diffuse_color = (0, 1, 0)
            if slots.material.envi_con_type == 'Ceiling':
                slots.material.diffuse_color = (0, 0.5, 0)
            if slots.material.envi_con_type == 'Floor':
                slots.material.diffuse_color = (0.44, 0.185, 0.07)
            if slots.material.envi_con_type == 'Ground':
                slots.material.diffuse_color = (0.22, 0.09, 0.04)
            if slots.material.envi_con_type == 'Shading':
                slots.material.diffuse_color = (1, 0, 0)
            if slots.material.envi_con_type == 'Aperture':
                slots.material.diffuse_color = (0, 0, 1)
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
            bpy.data.node_groups['EnVi Network'].nodes.new(type = 'EnViZone').zone = en_obj.name
        else:
            for node in bpy.data.node_groups['EnVi Network'].nodes:
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
                self.baseinfil = obj.envi_infbaselevel * vi_func.objvol(obj) * obj["floorarea"] * obj.envi_occsmax * 0.001
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
                self.baseinfil = (1/(obj.envi_infbaselevel * vi_func.objvol(obj)/obj["floorarea"])) * (1/obj.envi_occsmax) * 0.001
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

def writeafn(en_idf):
    surf = []
    cf = 0
    for enode in bpy.data.node_groups['EnVi Network'].nodes:
        if enode.bl_idname == 'AFNCon':
            cnode = bpy.data.node_groups['EnVi Network'].nodes[('Control')]
            inp = 1 if cnode.wpctype == 'Input' else 0
            en_idf.write("!-   ===========  ALL OBJECTS IN CLASS: AIRFLOW NETWORK ===========\n\n\
AirflowNetwork:SimulationControl,\n\
    {:{width}}!- Name\n\
    {:{width}}!- AirflowNetwork Control\n\
    {:{width}}!- Wind Pressure Coefficient Type\n\
    {:{width}}!- AirflowNetwork Wind Pressure Coefficient Array Name\n\
    {:{width}}!- Height Selection for Local Wind Pressure Calculation\n\
    {:{width}}!- Building Type\n\
    {:{width}}!- Maximum Number of Iterations (dimensionless)\n\
    {:{width}}!- Initialization Type\n\
    {:{width}}!- Relative Airflow Convergence Tolerance (dimensionless)\n\
    {:{width}}!- Absolute Airflow Convergence Tolerance (kg/s)\n\
    {:{width}}!- Convergence Acceleration Limit (dimensionless)\n\
    {:{width}}!- Azimuth Angle of Long Axis of Building (deg)\n\
    {:{width}}!- Ratio of Building Width Along Short Axis to Width Along Long Axis\n\n".format(cnode.afnname+',', cnode.afntype+',',
    cnode.wpctype+',', (",", cnode.wpcaname+',')[inp], (",", cnode.wpchs+',')[inp], (cnode.buildtype+',', ",")[inp], str(cnode.maxiter)+',', str(cnode.initmet)+',',
    str(cnode.rcontol)+',', str(cnode.acontol)+',', str(cnode.conal)+',', (str(cnode.aalax)+',', ",")[inp], (str(cnode.rsala)+';', ";")[inp], width = s))

        if enode.bl_idname == 'EnViCrRef':
            en_idf.write('AirflowNetwork:MultiZone:ReferenceCrackConditions,\n\
    {:{width}}!- Name\n\
    {:{width}}!- Reference Temperature\n\
    {:{width}}!- Reference Pressure\n\
    {:{width}}!- Reference Humidity Ratio\n\n'.format('ReferenceCrackConditions,', str(enode.reft)+',', str(enode.refp)+',', str(enode.refh)+';', width = s))

        if enode.bl_idname == 'EnViZone':
            if enode.outputs['TSPSchedule'].is_linked:
                snode = enode.outputs['TSPSchedule'].links[0].to_node
                control, mvof, lowerlim, upperlim, sched = 'Temperature,', str(snode.mvof)+',', str(snode.lowerlim)+',', str(snode.upperlim)+',', enode.zone+'_tsps,'
                ths = [ts for ts in (snode.t1, snode.t2, snode.t3, snode.t4)]
                fos = [fs for fs in (snode.f1, snode.f2, snode.f3, snode.f4) if fs != '']
                uns = [us for us in (snode.u1, snode.u2, snode.u3, snode.u4) if us != '']
                ts, fs, us = vi_func.rettimes(ths, fos, uns)
                for t in range(len(ts)):
                    if t == 0:
                        en_idf.write('Schedule:Compact,\n\
    {:{width}}!- Name\n\
    {:{width}}!- Schedule Type Limits Name\n'.format(sched, 'Any Number,', width = s))
                    en_idf.write('    {:{width}}!- Field {}\n'.format(ts[t], t*4, width = s))
                    
                    for f in range(len(fs[t])):
                        en_idf.write('    {:{width}}!- Field {}\n'.format(fs[t][f], t*4 +1, width = s))
                        
                        for u in range(len(us[t][f])):
                            en_idf.write('    {:{width}}!- Field {}\n'.format(us[t][f][u][0], t*4 + 2, width = s))
                en_idf.write('\n')

            else:
                control, mvof, lowerlim, upperlim, sched = 'NoVent,', ',', ',', ',', ','

            en_idf.write('AirflowNetwork:MultiZone:Zone,\n\
    {:{width}}!- Zone Name\n\
    {:{width}}!- Ventilation Control Mode\n\
    {:{width}}!- Ventilation Control Zone Temperature Setpoint Schedule Name\n\
    {:{width}}!- Minimum Venting Open Factor (dimensionless)\n\
    {:{width}}!- Lower value for modulating venting open factor (deltaC)\n\
    {:{width}}!- Upper value for modulating venting open factor (deltaC)\n\
    {:{width}}!- Indoor and Outdoor Enthalpy Difference Lower Limit For Maximum Venting Open Factor (deltaJ/kg)\n\
    {:{width}}!- Indoor and Outdoor Enthalpy Difference Upper Limit for Minimun Venting Open Factor (deltaJ/kg)\n\
    {:{width}}!- Venting Availability Schedule Name\n\n'.format(enode.zone + ',', control, sched, mvof,
    lowerlim, upperlim, str(0.0) + ',', str(300000.0) + ',', ';', width = s))

        if enode.bl_idname == 'EnViCLink':
            for sock in ([inp for inp in enode.inputs]+[outp for outp in enode.outputs]):
                if sock.is_linked and 'EnViCAirSocket' in sock.bl_idname:
                    sn = (sock.links[0].from_socket.sn, sock.links[0].to_socket.sn)[sock.in_out == 'OUT']
                    znode = (sock.links[0].from_node, sock.links[0].to_node)[sock.in_out == 'OUT']
                    zn = znode.zone

# Surface definitions

                    if enode.linkmenu in ('SO', 'DO'):
                        en_idf.write('AirflowNetwork:MultiZone:Surface,\n\
    {:{width}}! - Surface Name\n\
    {:{width}}!- Leakage Component Name\n\
    {:{width}}! - External Node Name\n\
    {:{width}}!- Window/Door Opening Factor\n\n'.format(('win-', 'door-')[bpy.data.materials[(sock.links[0].from_socket.name[:-1], sock.links[0].to_socket.name[:-1])[sock.in_out == 'OUT']].envi_con_type == 'Door']+zn+'_'+sn+',',
    'ComponentFlow_'+str(cf)+',', ',', str(enode.wdof)+';', width = s))
                        surf.append(('win-', 'door-')[bpy.data.materials[(sock.links[0].from_socket.name[:-1], sock.links[0].to_socket.name[:-1])[sock.in_out == 'OUT']].envi_con_type == 'Door']+zn+'_'+sn)


                    elif enode.linkmenu == 'Crack':
                        en_idf.write('AirflowNetwork:Multizone:Surface,\n\
    {:{width}}! - Surface Name\n\
    {:{width}}!- Leakage Component Name\n\
    {:{width}}! - External Node Name\n\
    {:{width}}!- Crack Opening Factor\n\n'.format(zn+'_'+sn+',',
    'ComponentFlow_'+str(cf)+',', ',', str(enode.cf)+';', width = s))
                        surf.append(zn+'_'+sn)


                    else:
                        en_idf.write('AirflowNetwork:Multizone:Surface,\n\
    {:{width}}! - Surface Name\n\
    {:{width}}!- Leakage Component Name\n\
    {:{width}}! - External Node Name\n\
    {:{width}}!- Crack Opening Factor\n\n'.format(zn+'_'+sn+',',
    'ComponentFlow_'+str(cf)+',', ',', '0.6;', width = s))
                        surf.append(zn+'_'+sn)
            enode['surf'] = surf

# Component defintions

            if enode.linkmenu == 'Crack':
                en_idf.write('AirflowNetwork:Multizone:Surface:Crack,\n\
    {:{width}}! - Name\n\
    {:{width}}! - Air Mass Flow Coefficient at Reference Conditions (kg/s)\n\
    {:{width}}! - Air Mass Flow Exponent (dimensionless)\n\n'.format('ComponentFlow_'+str(cf)+',', str(enode.amfc)+',', str(enode.amfe)+',', width = s))
                if enode.outputs['Reference'].is_linked:
                    en_idf.write('{:{width}}! - Reference Crack Conditions\n\n'.format('ReferenceCrackConditions;' if enode.outputs['Reference'].is_linked else ';', width = s))
                cf += 1

            if enode.linkmenu == 'ELA':
                en_idf.write('AirflowNetwork:Multizone:Surface:EffectiveLeakageArea,\n\
    {:{width}}! - Name\n\
    {:{width}}! - Effective Leakage Area (dimensionless)\n\
    {:{width}}! - Discharge Coefficient (dimensionless)\n\
    {:{width}}! - Reference Pressure Difference\n\
    {:{width}}! - Air Mass Flow Exponent (dimensionless)\n\n'.format('ComponentFlow_'+str(cf)+',', str(enode.ela)+',', str(enode.dcof)+',', str(enode.rpd)+',', str(enode.amfe)+';', width = s))
                cf += 1

            elif enode.linkmenu == 'EF':
                en_idf.write('AirflowNetwork:Multizone:Component:ZoneExhaustFan,\n\
    {:{width}}! - Name\n\
    {:{width}}! - Air Mass Flow Coefficient When the Zone Exhaust Fan is Off at Reference Conditions (kg/s)\n\
    {:{width}}! - Air Mass Flow Exponent When the Zone Exhaust Fan is Off (dimensionless)\n\n'.format('ComponentFlow_'+str(cf)+',', str(enode.amfc)+',', str(enode.amfe)+';', width = s))
                cf += 1

            elif enode.linkmenu == 'SO':
                en_idf.write('AirflowNetwork:Multizone:Component:SimpleOpening,\n\
    {:{width}}! - Name\n\
    {:{width}}!- Air Mass Flow Coefficient When Opening is Closed (kg/s-m)\n\
    {:{width}}!- Air Mass Flow Exponent When Opening is Closed (dimensionless)\n\
    {:{width}}!- Minimum Density Difference for Two-way Flow\n\
    {:{width}}!- Discharge Coefficient\n\n'.format('ComponentFlow_'+str(cf)+',', str(enode.amfcc)+',', str(enode.amfec)+',', str(enode.ddtw)+',', str(enode.dcof)+';', width = s))
                cf += 1

            elif enode.linkmenu == 'DO':
                en_idf.write('AirflowNetwork:Multizone:Component:DetailedOpening,\n\
    {:{width}}! - Name\n\
    {:{width}}!- Air Mass Flow Coefficient When Opening is Closed (kg/s-m)\n\
    {:{width}}!- Air Mass Flow Exponent When Opening is Closed (dimensionless)\n\
    {:{width}}!- Type of Rectanguler Large Vertical Opening (LVO)\n\
    {:{width}}!- Extra Crack Length or Height of Pivoting Axis (m)\n\
    {:{width}}!- Number of Sets of Opening Factor Data\n\
    0.0,                                                               !- Opening Factor 1 (dimensionless)\n\
    {:{width}}!- Discharge Coefficient for Opening Factor 1 (dimensionless)\n\
    {:{width}}!- Width Factor for Opening Factor 1 (dimensionless)\n\
    {:{width}}!- Height Factor for Opening Factor 1 (dimensionless)\n\
    {:{width}}!- Start Height Factor for Opening Factor 1 (dimensionless)\n\
    {:{width}}!- Opening Factor 2 (dimensionless)\n\
    {:{width}}!- Discharge Coefficient for Opening Factor 2 (dimensionless)\n\
    {:{width}}!- Width Factor for Opening Factor 2 (dimensionless)\n\
    {:{width}}!- Height Factor for Opening Factor 2 (dimensionless)\n\
    {:{width}}!- Start Height Factor for Opening Factor 2 (dimensionless)\n'.format('Component_'+str(cf)+',', str(enode.amfcc)+',',
    str(enode.amfec)+',', enode.lvo+',', ('Extra,', str(enode.ecl)+',')[enode.lvo == 'NonPivoted'], str(enode.noof)+',', str(enode.dcof1) + ',',
    str(enode.wfof1)+',', str(enode.hfof1)+ ',', str(enode.sfof1) + ',', str(enode.of2) + ',', str(enode.dcof2)+',',str(enode.wfof2)+',',
    str(enode.hfof2)+ ',', str(enode.sfof2) + (',', ';')[enode.noof == 2], width = s))
                cf += 1

                if enode.noof > 2:
                    en_idf.write('    {:{width}}!- Opening Factor 3 (dimensionless)\n\
    {:{width}}!- Discharge Coefficient for Opening Factor 3 (dimensionless)\n\
    {:{width}}!- Width Factor for Opening Factor 3 (dimensionless)\n\
    {:{width}}!- Height Factor for Opening Factor 3 (dimensionless)\n\
    {:{width}}!- Start Height Factor for Opening Factor 3 (dimensionless)'.format(str(enode.of3) + ',', str(enode.dcof3)+',',str(enode.wfof3)+',', str(enode.hfof3)+ ',', str(enode.sfof3) + (',', ';')[enode.noof == 3],  width = s))

                if enode.noof > 3:
                    en_idf.write('    {:{width}}!- Opening Factor 4 (dimensionless)\n\
    {:{width}}!- Discharge Coefficient for Opening Factor 4 (dimensionless)\n\
    {:{width}}!- Width Factor for Opening Factor 4 (dimensionless)\n\
    {:{width}}!- Height Factor for Opening Factor 4 (dimensionless)\n\
    {:{width}}!- Start Height Factor for Opening Factor 4 (dimensionless)\n\n'.format(str(enode.of4) + ',', str(enode.dcof4)+',',str(enode.wfof4)+',', str(enode.hfof4)+ ',', str(enode.sfof4) + ';',  width = s))

            elif enode.linkmenu == 'HO':
                en_idf.write('AirflowNetwork:Multizone:Component:HorizontalOpening,\n\
    {:{width}}! - Name\n\
    {:{width}}!- Air Mass Flow Coefficient When Opening is Closed (kg/s-m)\n\
    {:{width}}!- Air Mass Flow Exponent When Opening is Closed (dimensionless)\n\
    {:{width}}!- Sloping Plane Angle\n\
    {:{width}}!- Discharge Coefficient\n\n'.format('ComponentFlow_'+str(cf)+',', str(enode.amfcc)+',', str(enode.amfec)+',', str(enode.spa)+',', str(enode.dcof)+';', width = s))

                cf += 1

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