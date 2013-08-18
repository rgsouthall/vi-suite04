import bpy, math, datetime, os
from . import windrose 
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import datetime
from numpy import arange

def processtime(stat, ttype, time, metric, st, et):
    
    resmonth = [[] for x in range(12)]
    resday = [[]for x in range(366)]
    reshour = []

    if ttype == 'Monthly':
        for m, month in enumerate(time[2][1:]):
            if datetime.datetime(2010, time[2][m], time[3][m], time[4][m]-1) >= st and datetime.datetime(2010, time[2][m], time[3][m], time[4][m]-1) <= et:
                resmonth[int(month)-1].append(metric[m])
        res = resmonth
      
    if ttype == 'Daily':
        for d, day in enumerate(time[1][1:]):
            if datetime.datetime(2010, time[2][d], time[3][d], time[4][d]-1) >= st and datetime.datetime(2010, time[2][d], time[3][d], time[4][d]-1) <= et:
                resday[datetime.datetime(2000, time[2][d], time[3][d], time[4][d]-1).timetuple().tm_yday - 1].append(metric[d])
        res = resday
        
    if ttype == 'Hourly':
        for d, day in enumerate(time[1]):
            if datetime.datetime(2010, time[2][d], time[3][d], time[4][d]-1) >= st and datetime.datetime(2010, time[2][d], time[3][d], time[4][d]-1) <= et:
                reshour.append(metric[d])
        res = reshour
        
    if ttype != 'Hourly':
        if stat == "Average":

            res = [sum(r)/len(r) for r in res if r != []]
            

        if stat == "Maximum":
            res = [max(r) for r in res if r != []]
                
        if stat == "Minimum":
            res = [min(r) for r in res if r != []]
    return(res)

def statdata(res, stat, timetype, ds):
    if stat == 'Average':
        return([sum(r)/len(r) for r in res], "Average "+("Daily ", "Monthly ")[int(timetype)]+ds)
    elif stat == 'Maximum':
        return([max(r) for r in res], "Maximum "+("Daily ", "Monthly ")[int(timetype)]+ds)
    elif stat == 'Minimum':
        return([min(r) for r in res], "Minimum "+("Daily ", "Monthly ")[int(timetype)]+ds)
        
def timedata(datastring, timetype, stattype, months, days, dos, dnode, si, ei): 
    if timetype == '0':
        return([float(x) for x in datastring], "")
    else:
        if timetype == '1':
            res = [[] for d in range(dnode['Start'], dnode['End']+1)]
            for h, val in enumerate([float(val) for v, val in enumerate(datastring[2:]) if datetime.datetime(2013, int(months[v]), int(days[v])).timetuple().tm_yday >= dnode['Start'] and datetime.datetime(2013, int(months[v]), int(days[v])).timetuple().tm_yday <= dnode['End']]):
                res[int(dos[1:][h]) - 1].append(val)
        elif timetype == '2':  
            res = [[] for m in range(len(months) + 1) if datetime.date.fromordinal(datetime.date(2013, int(months[m]), int(days[m])).toordinal() + days - 1) >= dnode['Start'] and datetime.date.fromordinal(datetime.date(2013, int(months[m]), int(days[m])).toordinal() + days - 1) <= dnode['End']]        
            for h in range(len(datastring - 1)):
                res[int(months[h]) - 1].append(float(datastring[2:][h]))
        return(statdata(res, stattype, timetype, ""))
        
def chart_disp(chart_op, dnode, rnodes, Sdate, Edate):
    rds = [rn['resdict'] for rn in rnodes]
    for i in range(len(rds[0]['Hour'])):
        if datetime.datetime(datetime.datetime.now().year, int(rds[0]['Month'][i]), int(rds[0]['Day'][i]), int(rds[0]['Hour'][i])-1) == Sdate:
            si = i
        if datetime.datetime(datetime.datetime.now().year, int(rds[0]['Month'][i]), int(rds[0]['Day'][i]), int(rds[0]['Hour'][i])-1) == Edate:
            ei = i
    print(si, ei)
    plotstyle=('k', 'k:', 'k--', 'o', 'o', 'o', 'r', 'b', 'g')
    
    if dnode.inputs['X-axis'].rtypemenu == 'Time':
        if dnode.timemenu == '0':
            xdata = range(1, ei-si + 2)
            plt.xlabel('Time (hours)')
        if dnode.timemenu == '1':
            xdata = range(dnode['Start'], dnode['End']+1)
            plt.xlabel('Time (day of year)')
        if dnode.timemenu == '2':
            xdata = range(Sdate.month, Edate.month)
            plt.xlabel('Time (months)')
    
    for rn in rnodes:
        for rd in rn['resdict']:
    #            print(rn['resdict'][rd], dnode.timemenu, dnode.inputs['Y-axis 1'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'],rn['resdict'][rn['dos']])
            if rn['resdict'][rd][0] == dnode.inputs['X-axis'].rtypemenu and rn['resdict'][rd][1] == dnode.inputs['X-axis'].climmenu:
                (xdata, plt.ylabel) = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['X-axis'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'],rn['resdict'][rn['dos']], dnode, si, ei)
            if rn['resdict'][rd][0] == dnode.inputs['Y-axis 1'].rtypemenu and rn['resdict'][rd][1] == dnode.inputs['X-axis'].climmenu:
                (y1data, plt.ylabel) = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 1'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'],rn['resdict'][rn['dos']], dnode, si, ei)
                print(xdata, y1data)
                line, = plt.plot(xdata, y1data, '--', linewidth=2)
            if rn['resdict'][rd][0] == dnode.inputs['Y-axis 2'].rtypemenu and rn['resdict'][rd][1] == dnode.inputs['X-axis'].climmenu:
                (y2data, plt.ylabel) = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 2'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'],rn['resdict'][rn['dos']], dnode, si, ei)
                line, = plt.plot(xdata, y2data, '--', linewidth=2)
            if rn['resdict'][rd][0] == dnode.inputs['Y-axis 3'] and rn['resdict'][rd][1] == dnode.inputs['X-axis'].climmenu:
                (y3data, plt.ylabel) = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 3'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'],rn['resdict'][rn['dos']], dnode, si, ei)
                line, = plt.plot(xdata, y3data, '--', linewidth=2)
   
    
    

#    if dnode.inputs['X-axis'].rtypemenu == 'Climate':
#        for rd in rnodes[0]['resdict']:
#            if rnodes[0]['resdict'][rd][0] == dnode.inputs['X-axis'].rtypemenu and rnodes[0]['resdict'][rd][1] == dnode.inputs['X-axis'].climmenu:
#                if dnode.timemenu == '0':
#                    xdata = [float(x) for x in rnodes[0]['resdict'][rd][2:]]
#                
#    if dnode.inputs['X-axis'].rtypemenu == 'Zone':
#        if dnode.timemenu == '0':
#            for rd in rnodes[0]['resdict']:
#                if rnodes[0]['resdict'][rd][0] == dnode.inputs[0].zonemenu and rnodes[0]['resdict'][rd][1] == dnode.inputs['X-axis'].zonermenu:
#                    xdata = [float(x) for i,x in enumerate(rnodes[0]['resdict'][rd][2:])]  
                    
#    if dnode.inputs['Y-axis 1'].rtypemenu == 'Climate':
#        for rd in rnodes[1]['resdict']:
#            if rnodes[1]['resdict'][rd][0] == 'Environment' and rnodes[1]['resdict'][rd][1] == dnode.inputs['Y-axis 1'].climmenu:
#                if dnode.timemenu == '0':
#                    y1data = [float(y) for y in rnodes[1]['resdict'][rd][2:]]
#                    plt.ylabel(rnodes[1]['resdict'][rd][1])

#    line, = plt.plot(xdata, y1data, '--', linewidth=2)    
#    line, = plt.plot(xdata, y1data, linewidth=2)
    plt.show()   
    
    

    
    



    
#    if hasattr(scene, 'envi_reszoney1') and scene.envi_reszoney1 == 'All Zones':
#            yplot = []
#            ylegend = []
#
#    plotstyle=('k', 'k:', 'k--', 'o', 'o', 'o', 'r', 'b', 'g')
#       
#    if scene.envi_charttype == '1':
#        ps = 6
#    else:
#        ps = 0
#        
#    if scene.envi_dispperiod == '1':
#        er.dstartdate = datetime.datetime(2010, scene.envi_display_start_month, dstartd, scene.envi_display_start_hour-1)
#        er.denddate = datetime.datetime(2010, scene.envi_display_end_month, dendd, scene.envi_display_end_hour-1)
#    else:
#        er.dstartdate = datetime.datetime(2010, er.dos[2][0], er.dos[3][0], er.dos[4][0]-1)
#        er.denddate = datetime.datetime(2010, er.dos[2][-1], er.dos[3][-1], er.dos[4][-1]-1)
#    
#    if scene.envi_charttype != '2':
#        xdispall = []
#        graph = plt.figure()
#        gsub = graph.add_subplot(111)    
#        
#        if scene.envi_xtime in ('Daily', 'Monthly'):
#            if hasattr(scene, 'envi_resstatsy1'):
#                resstats = (scene.envi_resstatsy1)
#            if hasattr(scene, 'envi_resstatsy2'):
#                resstats = (scene.envi_resstatsy1, scene.envi_resstatsy2)
#            if hasattr(scene, 'envi_resstatsy3'):
#                resstats = (scene.envi_resstatsy1, scene.envi_resstatsy2, scene.envi_resstatsy3)
#        else:
#            resstats = ("", "", "")
#  
#        if scene.envi_xtype == '0':
#            if scene.envi_xtime == 'Hourly':
#                if scene.envi_dispperiod == '1':
#                    for h in range(0, len(er.dos[1])):
#                        if datetime.datetime(2010, er.dos[2][h], er.dos[3][h], er.dos[4][h]-1) >= er.dstartdate and datetime.datetime(2010, er.dos[2][h], er.dos[3][h], er.dos[4][h]-1) <= er.denddate:
#                            xdispall.append(h)
#                    xdisp = xdispall
#                else:
#                    xdisp = range(1, len(er.dos[1])+1)
#                gsub.set_xlabel('Hours')
#                plottit = 'vs. Time (Hours)'
#                plotfile = 'vth'
#            
#            if scene.envi_xtime == 'Daily':
#                for d, day in enumerate(er.dos[1]):
#                    if scene.envi_dispperiod == '1':
#                        if datetime.datetime(2010, er.dos[2][d], er.dos[3][d], er.dos[4][d]-1) >= er.dstartdate and datetime.datetime(2010, er.dos[2][d], er.dos[3][d], er.dos[4][d]-1) <= er.denddate:
#                            xdispall.append(datetime.datetime(2000, er.dos[2][d], er.dos[3][d]).timetuple().tm_yday)
#                    else:
#                        xdispall.append(datetime.datetime(2000, er.dos[2][d], er.dos[3][d]).timetuple().tm_yday)
#                xdisp = list(set(xdispall))
#                gsub.set_xlabel('Day of Year')
#                plottit = 'vs. Time (Days)'
#                plotfile = 'vtd'
#            
#            if scene.envi_xtime == 'Monthly':
#                if scene.envi_dispperiod == '1':
#                    for m, month in enumerate(er.dos[2]):
#                        if datetime.datetime(2010, er.dos[2][m], er.dos[3][m], er.dos[4][m]-1) >= er.dstartdate and datetime.datetime(2010, er.dos[2][m], er.dos[3][m], er.dos[4][m]-1) <= er.denddate:
#                            xdispall.append(er.dos[2][m])
#                    xdisp = list(set(xdispall))
#                else:
#                    xdisp = list(set(er.dos[2]))
#                gsub.set_xlabel('Month')
#                plottit = 'vs. Time (Months)'
#                plotfile = 'vtm'
#        
#        if scene.envi_xtype == '1':
#            ps = 3
#            if scene.envi_resclim == 'Ambient Temperature (C)': 
#                xdisp = er.at[1]
#                gsub.set_xlabel(r'Ambient Temperature ($^\circ$C)')
#                plottit = r'vs. Ambient Temperature ($^\circ$C)'
#                plotfile = 'vat'
#            if scene.envi_resclim == 'Ambient Humidity (%)':
#                xdisp = er.ah[1]
#                gsub.set_xlabel('Ambient Humidity (%)')
#                plottit = 'vs. Ambient Humidity (%)'
#                plotfile = 'vah'           
#            if scene.envi_resclim == 'Ambient Wind Speed (m/s)':
#                xdisp = er.aws[1]
#                gsub.set_xlabel('Ambient Wind Speed (m/s)') 
#                plottit = 'vs. Ambient Wind Speed (m/s)'
#                plotfile = 'vaws'
#            if scene.envi_resclim == 'Ambient Wind Direction (deg from N)':
#                xdisp = er.awd[1]
#                gsub.set_xlabel(r'Ambient Wind Direction ($^o$ from N)') 
#                plottit = r'vs. Ambient Wind Direction ($^o$ from N)'
#                plotfile = 'vawd'
#            if scene.envi_resclim == 'Direct Solar Radiation (W/m^2)':
#                xdisp = er.asb[1]
#                gsub.set_xlabel(r'Direct Solar Radiation (W/m$^2$)') 
#                plottit = r'vs. Direct Solar Radiation (W/m$^2$)'
#                plotfile = 'vasb'
#            if scene.envi_resclim == 'Diffuse Solar Radiation (W/m^2)':
#                xdisp = er.asd[1]
#                gsub.set_xlabel(r'Diffuse Solar Radiation (W/m$^2$)') 
#                plottit = r'vs. Diffuse Solar Radiation (W/m$^2$)'
#                plotfile = 'vasd'
#                
#        if scene.envi_xtype == '2':
#            ps = 3
#            for res in er.zoneres:
#                if res[1] == scene.envi_reszone:
#                    if res[2] == scene.envi_resparam:
#                        xdisp = res[3:]
#                        gsub.set_xlabel(scene.envi_reszone+" Hourly "+scene.envi_resparam) 
#                        plottit = 'vs. '+scene.envi_reszone+" Hourly "+scene.envi_resparam    
#                        plotfile = 'vawd'
#        
#        if scene.envi_ytype1 == '0':
#            if scene.envi_resclimy1 == 'Ambient Temperature (C)':
#                yplot = [[xdisp, processtime(scene.envi_resstatsy1, scene.envi_xtime, er.dos, er.at[1], er.dstartdate, er.denddate), plotstyle[ps]]]
#                if scene.envi_ytype2 != '0':
#                    gsub.set_ylabel(r'Temperature ($^\circ$C)')
#                    ylegend = ["Ambient "+resstats[0]]
#                    plottit = r'Temperature ($^\circ$C) '+plottit
#                    plotfile = 't'+plotfile
#                else:
#                    gsub.set_ylabel(r'Ambient Temperature ($^\circ$C)')
#                    ylegend = None
#                    print(plottit)
#                    plottit = resstats[0] + r'Ambient Temperature ($^\circ$C) '+plottit
#                    plotfile = 'at'+plotfile
#            
#            if scene.envi_resclimy1 == 'Ambient Humidity (%)':
#                yplot = [[xdisp, processtime(scene.envi_resstatsy1, scene.envi_xtime, er.dos, er.ah[1], er.dstartdate, er.denddate), plotstyle[ps]]]
#                if scene.envi_ytype2 != '0':
#                    gsub.set_ylabel('Humidity (%)')
#                    ylegend = ["Ambient "+resstats[0]]
#                    plottit = 'Humidity (%) '+plottit
#                    plotfile = 'h'+plotfile
#                else:
#                    gsub.set_ylabel(r'Ambient Humidity (%)')
#                    plottit = resstats[0] + 'Ambient Humidity (%) '+plottit
#                    ylegend = (None)
#                    plotfile = 'ah'+plotfile
#            
#            if scene.envi_resclimy1 == 'Ambient Wind Speed (m/s)':
#                yplot = [[xdisp, processtime(scene.envi_resstatsy1, scene.envi_xtime, er.dos, er.aws[1], er.dstartdate, er.denddate), plotstyle[ps]]]
#                if scene.envi_ytype2 != '0':
#                    gsub.set_ylabel('Air Speed (m/s)')
#                    ylegend = ["Ambient "+resstats[0]]
#                    plottit = 'Air Speed (m/s) '+plottit
#                    plotfile = 'as'+plotfile
#                else:
#                    gsub.set_ylabel('Ambient Wind Speed (m/s)')
#                    ylegend = (None)
#                    plottit = resstats[0] + 'Ambient Wind Speed (m/s) '+plottit
#                    plotfile = 'aws'+plotfile
#            
#            if scene.envi_resclimy1 == 'Ambient Wind Direction (deg from N)':
#                yplot = [[xdisp, processtime(scene.envi_resstatsy1, scene.envi_xtime, er.dos, er.awd[1], er.dstartdate, er.denddate), plotstyle[ps]]]
#                if scene.envi_ytype2 != '0':
#                    gsub.set_ylabel(resstats[0]+r' Air Direction ($^o$ from N)')
#                    ylegend = ["Ambient "+resstats[0]]
#                    plottit = 'Air Speed (m/s) '+plottit
#                    plotfile = 'ad'+plotfile
#                else:
#                    gsub.set_ylabel('Ambient Wind Direction ($^o$ from N)')
#                    plottit = resstats[0] + 'Air Speed (m/s) '+plottit
#                    plotfile = 'awd'+plotfile
#                    
#            if scene.envi_resclimy1 == 'Direct Solar Radiation (W/m^2)':
#                yplot = [[xdisp, processtime(scene.envi_resstatsy1, scene.envi_xtime, er.dos, er.asb[1], er.dstartdate, er.denddate), plotstyle[ps]]]
#                gsub.set_ylabel(resstats[0]+r' Direct Solar (W/m$^2$)')
#                plottit = r'Direct Solar (W/m$^2$) '+plottit
#                plotfile = 'asb'+plotfile
#                if scene.envi_ytype2 != '0':
#                    ylegend = ["Direct Solar "+ resstats[0]]
#                    
#            if scene.envi_resclimy1 == 'Diffuse Solar Radiation (W/m^2)':
#                yplot = [[xdisp, processtime(scene.envi_resstatsy1, scene.envi_xtime, er.dos, er.asd[1], er.dstartdate, er.denddate), plotstyle[ps]]]
#                gsub.set_ylabel(resstats[0]+r' Diffuse Solar (W/m$^2$)')
#                plottit = 'Diffuse Solar (W/m$^2$) '+plottit
#                plotfile = 'asd'+plotfile
#                if scene.envi_ytype2 != '0':
#                    ylegend = ["Diffuse Solar"]
#                    
#                    
#        if scene.envi_ytype1 == '1':
#            for res in er.zoneres:
#                if scene.envi_reszoney1 != 'All Zones':
#                    if res[1] == scene.envi_reszoney1:
#                        if res[2] == scene.envi_resparamy1:
#                            yplot = [[xdisp, processtime(scene.envi_resstatsy1, scene.envi_xtime, er.dos, res[3:], er.dstartdate, er.denddate), plotstyle[ps]]]
#                            ylegend = [scene.envi_reszoney1]
#                            plotfile = res[2].replace("/s", "s-1")+plotfile
#                else:
#                   if res[2] == scene.envi_resparamy1:
#                        yplot.append([xdisp, processtime(scene.envi_resstatsy1, scene.envi_xtime, er.dos, res[3:], er.dstartdate, er.denddate), plotstyle[ps]])
#                        ylegend.append(res[1])
#                
#            if scene.envi_ytype2 != '0' or scene.envi_reszoney1 != 'All Zones':
#                gsub.set_ylabel(scene.envi_xtime+" "+scene.envi_resparamy1)
#                plottit = scene.envi_resparamy1+' '+plottit
#            else:
#                gsub.set_ylabel(scene.envi_reszoney1+" "+scene.envi_xtime+" "+scene.envi_resparamy1)
#                plottit = scene.envi_reszoney1+" "+scene.envi_resparamy1+' '+plottit
#                plotfile = scene.envi_reszoney1+plotfile
#        
#        ps = ps + 1
#        if scene.envi_ytype2 == '1':
#            if scene.envi_resclimy2 == 'Ambient Temperature (C)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy2, scene.envi_xtime, er.dos, er.at[1], er.dstartdate, er.denddate), plotstyle[ps]])
#            if scene.envi_resclimy2 == 'Ambient Humidity (%)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy2, scene.envi_xtime, er.dos, er.ah[1], er.dstartdate, er.denddate), plotstyle[ps]])
#            if scene.envi_resclimy2 == 'Ambient Wind Speed (m/s)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy2, scene.envi_xtime, er.dos, er.aws[1], er.dstartdate, er.denddate), plotstyle[ps]])
#            if scene.envi_resclimy2 == 'Ambient Wind Direction (deg from N)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy2, scene.envi_xtime, er.dos, er.awd[1], er.dstartdate, er.denddate), plotstyle[ps]])
#            if scene.envi_resclimy2 == 'Direct Solar Radiation (W/m^2)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy2, scene.envi_xtime, er.dos, er.asb[1], er.dstartdate, er.denddate), plotstyle[ps]])
#            if scene.envi_resclimy2 == 'Diffuse Solar Radiation (W/m^2)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy2, scene.envi_xtime, er.dos, er.asd[1], er.dstartdate, er.denddate), plotstyle[ps]])
#            ylegend.append("Ambient "+resstats[1])
#    
#        if scene.envi_ytype2 == '2':
#            for res in er.zoneres:
#                if res[1] == scene.envi_reszoney2:
#                    if res[2] == scene.envi_resparamy2:
#                        yplot.append([xdisp, processtime(scene.envi_resstatsy2, scene.envi_xtime, er.dos, res[3:], er.dstartdate, er.denddate), plotstyle[ps]])
#                        ylegend.append(scene.envi_reszoney2+" "+resstats[1])
#        ps = ps + 1 
#        
#        if scene.envi_ytype3 == '1':
#            if scene.envi_resclimy3 == 'Ambient Temperature (C)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy3, scene.envi_xtime, er.dos, er.at[1], er.dstartdate, er.denddate), plotstyle[ps]])
#                ylegend.append("Ambient "+resstats[2])
#            if scene.envi_resclimy3 == 'Ambient Humidity (%)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy3, scene.envi_xtime, er.dos, er.ah[1], er.dstartdate, er.denddate), plotstyle[ps]])
#                ylegend.append("Ambient "+resstats[2])    
#            if scene.envi_resclimy3 == 'Ambient Wind Speed (m/s)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy3, scene.envi_xtime, er.dos, er.aws[1], er.dstartdate, er.denddate), plotstyle[ps]])
#                ylegend.append("Ambient "+resstats[2])
#            if scene.envi_resclimy3 == 'Ambient Wind Direction (deg from N)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy3, scene.envi_xtime, er.dos, er.awd[1], er.dstartdate, er.denddate), plotstyle[ps]])
#                ylegend.append(resstats[2]+" Diffuse Solar")
#            if scene.envi_resclimy3 == 'Direct Solar Radiation (W/m^2)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy3, scene.envi_xtime, er.dos, er.asb[1], er.dstartdate, er.denddate), plotstyle[ps]])
#                ylegend.append(resstats[2]+" Direct Solar")
#            if scene.envi_resclimy3 == 'Diffuse Solar Radiation (W/m^2)':
#                yplot.append([xdisp, processtime(scene.envi_resstatsy3, scene.envi_xtime, er.dos, er.asd[1], er.dstartdate, er.denddate), plotstyle[ps]])
#                ylegend.append(resstats[2]+" Diffuse Solar")
#    
#        if scene.envi_ytype3 == '2':
#            for res in er.zoneres:
#                if res[1] == scene.envi_reszoney3:
#                    if res[2] == scene.envi_resparamy3:
#                        yplot.append([xdisp, processtime(scene.envi_resstatsy3, scene.envi_xtime, er.dos, res[3:], er.dstartdate, er.denddate), plotstyle[ps]])
#                        ylegend.append(scene.envi_reszoney3+" "+resstats[2])
#                    
#        for p, yp in enumerate(yplot):
#            if scene.envi_xtime == 'Monthly':
#                plt.xticks(arange(1,len(yp[0])+1) + 0.5, [('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')[mon-1] for mon in yp[0]])
#            if scene.envi_charttype == '0':
#                gsub.plot(yp[0], yp[1], yp[2])
#            if scene.envi_charttype == '1':
#                gsub.bar(yp[0], yp[1], 0.75 - (p/6), color = plotstyle[p+6])
#        if scene.envi_ytype2 != '0':
#            gsub.legend(ylegend, 'lower right', shadow=True)
#        gsub.set_title(plottit)
#        gsub.grid(True)
#
#        plt.savefig(plotfile+'.png', dpi = (96))
#        plt.savefig(plotfile+'.svg')
#        if scene.envi_display_graph == True:
#            plt.show()
#        
#        if plotfile+'.png' not in [im.name for im in bpy.data.images]:
#            bpy.data.images.load(plotfile+'.png')
#        else:
#            bpy.data.images[plotfile+'.png'].reload()
#    
#    else:
#        ws = processtime('Average', 'Hourly', er.dos, er.aws[1], er.dstartdate, er.denddate)
#        wd = processtime('Average', 'Hourly', er.dos, er.awd[1], er.dstartdate, er.denddate)
#        ax = new_axes()
#        ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white')
#        ax.box(wd, ws, bins=arange(0,int(math.ceil(max(ws))),1), normed = 1)
##        ax.contourf(wd, ws, bins=arange(0,int(math.ceil(max(ws))),1), normed = 1, cmap=cm.hot)
##        ax.contour(wd, ws, bins=arange(0,int(math.ceil(max(ws))),1), normed = 1, colors='black')
#        set_legend(ax)
#        plt.savefig('rose.png', dpi = (96))
#        plt.savefig('rose.svg')
#        if 'rose.png' not in [im.name for im in bpy.data.images]:
#            bpy.data.images.load('rose.png')
#        else:
#            bpy.data.images['rose.png'].reload()
#        plt.show()