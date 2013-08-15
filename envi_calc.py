#import bpy, 
import os, glob, bpy, datetime, time
#, subprocess
from subprocess import PIPE, Popen
from os import rename
from os.path import basename
from bpy.props import EnumProperty, IntProperty
from .vi_func import iprop, eprop
from . import vi_node

def envi_sim(calc_op, node):
    dos = [[], [], [], [], []]
    at = [[], []]
    ah = [[], []]
    aws = [[], []]
    awd = [[], []]
    asd = [[], []]
    asb = [[], []]
    xtypes = []
    zoneres = []
    zoneresno = []
    os.chdir(node.newdir)
    reslist = []
    climlist = []
    zonelist = []
    zonereslist = []
    esimcmd = "EnergyPlus in.idf in.epw" 
    esimrun = Popen(esimcmd, shell = True, stdout = PIPE)
    for line in esimrun.stdout:
        print(line) 
    for fname in os.listdir('.'):
        if fname.split(".")[0] == node.resname:
            os.remove(node.newdir+node.fold+fname)
    for fname in os.listdir('.'):
        if fname.split(".")[0] == "eplusout":
            rename(fname, fname.replace("eplusout", node.resname))
#    scene.envi_sim = True
    
    resfile = open(node.newdir+node.fold+node.resname+".eso")
    
#    objno = len([obj for obj in bpy.data.objects if obj.layers[1] == True])

    for line in resfile:
        if len(line.split(",")) > 2 and line.split(",")[2] == "Day of Simulation[]":
            dos[0] = line.split(",")[0]
            xtypes.append("Time")
        elif len(line.split(",")) > 2 and line.split(",")[2] == "Environment":
            if line.split(",")[3].strip('\n') == "Site Outdoor Air Drybulb Temperature [C] !Hourly":
                climlist.append(('Ambient Temperature (C)', 'Ambient Temperature (C)', 'Climate results'))
                at[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Outdoor Air Relative Humidity [%] !Hourly":
                climlist.append(('Ambient Humidity (%)', 'Ambient Humidity (%)', 'Climate results'))
                ah[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Wind Speed [m/s] !Hourly":
                climlist.append(('Ambient Wind Speed (m/s)', 'Ambient Wind Speed (m/s)', 'Climate results'))
                aws[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Wind Direction [deg] !Hourly":
                climlist.append(('Ambient Wind Direction (deg from N)', 'Ambient Wind Direction (deg from N)', 'Climate results'))
                awd[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Diffuse Solar Radiation Rate per Area [W/m2] !Hourly":
                climlist.append(('Diffuse Solar Radiation (W/m^2)', 'Diffuse Solar Radiation (W/m^2)', 'Climate results'))
                asd[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Direct Solar Radiation Rate per Area [W/m2] !Hourly":
                climlist.append(('Direct Solar Radiation (W/m^2)', 'Direct Solar Radiation (W/m^2)', 'Climate results'))
                asb[0] = line.split(",")[0]
            xtypes.append("Climate")
        
        elif len(line.split(",")) > 2 and line.split(",")[2] in [obj.name.upper() for obj in bpy.data.objects if obj.layers[1] == True]:
            for obj in bpy.data.objects:
                if obj.layers[1] == True and obj.name.upper() == line.split(",")[2]:
                    if (obj.name, obj.name, 'Zone name') not in zonelist:
                        zonelist.append((obj.name, obj.name, 'Zone name'))
                    if line.split(",")[3].split("!")[0] == "Zone Infiltration Current Density Volume Flow Rate [m3/s] ":
                        zoneres.append([line.split(",")[0], obj.name, "Zone Infiltration [m3/s] "])
                    elif line.split(",")[3].split("!")[0] == "Zone Windows Total Transmitted Solar Radiation Rate [W] ":
                        zoneres.append([line.split(",")[0], obj.name, "Total Solar Gain [W] "])
                    else:
                        zoneres.append([line.split(",")[0], obj.name, line.split(",")[3].split("!")[0]])
                    zoneresno.append(line.split(",")[0])
                    if line.split(",")[3].split("!")[0] not in [zr[1] for zr in zonereslist]:
                        if line.split(",")[3].split("!")[0] == "Zone Infiltration Current Density Volume Flow Rate [m3/s] ":
                            zonereslist.append(("Zone Infiltration [m3/s] ", line.split(",")[3].split("!")[0], 'Results Parameter'))
                        elif line.split(",")[3].split("!")[0] == "Zone Windows Total Transmitted Solar Radiation Rate [W] ":
                            zonereslist.append(("Total Solar Gain [W] ", line.split(",")[3].split("!")[0], 'Results Parameter'))
                        else:
                            zonereslist.append((line.split(",")[3].split("!")[0], line.split(",")[3].split("!")[0], 'Results Parameter'))
            if ("Zone", "Zone", "Plot a zone result on the x-axis") not in node['xtypes']:
                xtypes.append("Zone")     
#            er.zonereslist = zonereslist
            
        elif line.split(",")[0] in zoneresno:
            zoneres[[i for i,x in enumerate(zoneresno) if x == line.split(",")[0]][0]].append(float(line.split(",")[1].strip("\n")))
            
        elif line.split(",")[0] == dos[0]:
            dos[1].append(int(line.split(",")[1]))
            dos[2].append(int(line.split(",")[2]))
            dos[3].append(int(line.split(",")[3]))
            dos[4].append(int(line.split(",")[5]))
        
        elif line.split(",")[0] == at[0]: 
            at[1].append(float(line.split(",")[1].strip('\n')))
        
        elif line.split(",")[0] == ah[0]: 
            ah[1].append(float(line.split(",")[1].strip('\n')))
        
        elif line.split(",")[0] == aws[0]: 
            aws[1].append(float(line.split(",")[1].strip('\n')))    
        
        elif line.split(",")[0] == awd[0]: 
            awd[1].append(float(line.split(",")[1].strip('\n')))   
        
        elif line.split(",")[0] == asb[0]: 
            asb[1].append(float(line.split(",")[1].strip('\n'))) 
        
        elif line.split(",")[0] == asd[0]: 
            asd[1].append(float(line.split(",")[1].strip('\n'))) 
    
    for obj in bpy.data.objects:
        for zr in zoneres:
            if obj.layers[1] == True and obj.name == zr[1] and "Zone Air System Sensible Heating Rate [W]" in zr[2]:
                obj["kwhh"] = sum(zr[3:])*0.001
                obj["kwhhm2"] = obj["kwhh"]/obj["floorarea"]
            if obj.layers[1] == True and obj.name == zr[1] and "Zone Air System Sensible Cooling Rate [W]" in zr[2]:   
                obj["kwhc"] = sum(zr[3:])*0.001
                obj["kwhcm2"] = obj["kwhc"]/obj["floorarea"]
    
#    node.xtypes = bpy.props.EnumProperty(items = xtypes, default = '0')
    if len(zonelist) > 0:
        zonelist.append(('All Zones', 'All Zones', 'Zone name'))
        node.reszoney1 = node.reszoney2 = node.reszoney3 = node.reszone = eprop(zonelist, "Zone results", "Zone results identifier", zonelist[-1][0])
        node.ytype1 = eprop([("0", "Climate", "Plot a climate parameter on the x-axis"), ("1", "Zone", "Plot a zone result on the x-axis")], "Y-axis 1", "specify the EnVi results display", "0")
        node.ytype2 = eprop([("0", "None", "Plot a climate parameter on the y-axis"), ("1", "Climate", "Plot a climate parameter on the x-axis"), ("2", "Zone", "Plot a zone result on the x-axis")],
                                                        "Y-axis 2","specify the EnVi results display", "0")
        node.ytype3 = eprop([("0", "None", "Plot a climate parameter on the x-axis"), ("1", "Climate", "Plot a climate parameter on the x-axis"), ("2", "Zone", "Plot a zone result on the x-axis")],
                                                        "Y-axis 3", "specify the EnVi results display","0")
        node.resparamy1 = bpy.types.Scene.envi_resparamy2 = bpy.types.Scene.envi_resparamy3 = bpy.types.Scene.envi_resparam = eprop(zonereslist, "Zone results", "Zone results identifier", zonereslist[0][0])
    else:
        node.ytype1 = EnumProperty(items = [("0", "Climate", "Plot a climate parameter on the x-axis")],
                                                        name="Y-axis 1",
                                                        description="specify the EnVi results display",
                                                        default="0")
        node.ytype2 = EnumProperty(items = [("0", "None", "Plot a climate parameter on the x-axis"), ("1", "Climate", "Plot a climate parameter on the x-axis")],
                                                        name="Y-axis 2",
                                                        description="specify the EnVi results display",
                                                        default="0")
        node.ytype3 = EnumProperty(items = [("0", "None", "Plot a climate parameter on the x-axis"), ("1", "Climate", "Plot a climate parameter on the x-axis")],
                                                        name="Y-axis 3",
                                                        description="specify the EnVi results display",
                                                        default="0")
    [reslist.append((filename.split(".")[0], filename.split(".")[0], 'Results File')) for filename in glob.glob("*.eso")]

    node.resfiles = EnumProperty(
            items = reslist, name="Results file", description="Name of the results file", default=node.resname)
    try:
        node.resclimy1 = EnumProperty(items = climlist, name="Climate results", description="Climate results type", default=climlist[0][0])
        node.resclimy2 = bpy.types.Scene.envi_resclimy3 = bpy.types.Scene.envi_resclim = EnumProperty(items = climlist, name="Climate results", description="Climate results type", default=climlist[0][0])
    except:
        calc_op.report({'ERROR'},"No results have been selected for export")
        
    startdate = datetime.datetime(2010, dos[2][1], dos[3][1], dos[4][1]-1)
    enddate = datetime.datetime(2010, dos[2][-1], dos[3][-1], dos[4][-1]-1)
    node['xtypes'] = xtypes
#    bpy.utils.unregister_class(ViEnRXIn)
    

    
    node.dsm = iprop("Month", "Month of the year", 1, 12, dos[2][0])
    node.dsd = iprop("Day", "Day of the month", 1, 31, dos[3][0])
    node.dsd30 = iprop("Day", "Day of the month",1, 30, dos[3][0])
    node.dsd28 = iprop("Day", "Day of the month", 1, 28, dos[3][0])
    node.dsh = iprop("Hour", "Hour of the day", 1, 24, dos[4][0])
    node.dem = iprop("Month", "Month of the year", 1, 12, dos[2][-1])
    node.ded = iprop("Day", "Day of the year", 1, 31, dos[3][-1])
    node.ded30 = iprop("Day", "Day of the year", 1, 30, dos[3][-1])
    node.ded28 = iprop("Day", "Day of the year", 1, 28, dos[3][-1])
    node.deh = iprop("Hour", "Hour of the day", 1, 24, dos[4][-1])
    calc_op.report({'INFO'}, "Calculation is finished.")  
            
    if node.resname+".err" not in [im.name for im in bpy.data.texts]:
        bpy.data.texts.load(node.newdir+"/"+node.resname+".err")

#def envi_reslist    