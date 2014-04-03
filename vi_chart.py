import sys

try:
    import matplotlib.pyplot as plt
    mp = 1
except:
    mp = 0
        
def label(cat, stat, time, metric):
    if cat == 'Climate':
        catstring = 'Ambient'
    elif cat == 'Zone':
        catstring = 'Zone'
    elif cat == 'Linkage':
        catstring = 'Linkage'
    return('{} {} {} {}'.format(stat, catstring, ('Hourly', 'Daily', 'Monthly')[int(time)], metric))
    
def statdata(res, stat):
    if stat == 'Average':
        return([sum(r)/len(r) for r in res])
    elif stat == 'Maximum':
        return([max(r) for r in res])
    elif stat == 'Minimum':
        return([min(r) for r in res])

def timedata(datastring, timetype, stattype, months, days, dos, dnode, si, ei, Sdate, Edate):
    if timetype == '0':
        return([float(x) for x in datastring])
    else:
        if timetype == '1':
            res = [[] for d in range(dnode['Start'], dnode['End']+1)]
            for h, val in enumerate([float(val) for val in datastring]):
                res[int(dos[1:][si+h]) - dnode['Start']].append(val)

        elif timetype == '2':
            res = [[] for m in range(Sdate.month, Edate.month + 1)]
            for h, val in enumerate([float(val) for val in datastring]):
                res[int(months[si+h]) - Sdate.month].append(val)
        return(statdata(res, stattype))

def chart_disp(chart_op, dnode, rnodes, Sdate, Edate):
    rn = dnode.inputs['X-axis'].links[0].from_node
    rd = rn['resdict']
    sm, sd, sh, em, ed, eh = Sdate.month, Sdate.day, Sdate.hour, Edate.month, Edate.day, Edate.hour
    (dm, dd, dh) = ([int(x) for x in rd['Month']], [int(x) for x in rd['Day']], [int(x) for x in rd['Hour']])
    for i in range(len(rd['Hour'])):
        if sm == dm[i] and sd == dd[i] and sh == dh[i] - 1:
            si = i
        elif em == dm[i] and ed == dd[i] and eh == dh[i] - 1:
            ei = i
    plotstyle = ('k', 'k:', 'k--', 'o', 'o', 'o', 'r', 'b', 'g')
    if dnode.inputs['X-axis'].rtypemenu == 'Time':
        if dnode.timemenu == '0':
            xdata = range(1, ei-si + 2)
            xlabel = 'Time (hours)'
        if dnode.timemenu == '1':
            xdata = range(dnode['Start'], dnode['End'] + 1)
            xlabel = 'Time (day of year)'
        if dnode.timemenu == '2':
            xdata = range(Sdate.month, Edate.month + 1)
            xlabel = 'Time (months)'
    else:
        for rd in rn['resdict']:
            rn['resdict'][rd]
            if dnode.inputs['X-axis'].rtypemenu == 'Climate':
                if dnode.inputs['X-axis'].links[0].from_node['resdict'][rd][0:2] == [dnode.inputs['X-axis'].rtypemenu, dnode.inputs['X-axis'].climmenu]:
                    xdata = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['X-axis'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate)
                    xlabel = label('Climate', dnode.inputs['X-axis'].statmenu, dnode.timemenu, dnode.inputs['X-axis'].climmenu)
            elif dnode.inputs['X-axis'].rtypemenu == 'Zone':
                if (dnode.inputs['X-axis'].rtypemenu, dnode.inputs['X-axis'].links[0].from_node['resdict'][rd][0:2]) == ('Zone',[dnode.inputs['X-axis'].zonemenu, dnode.inputs['X-axis'].zonermenu]):
                    xdata = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['X-axis'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate)
                    xlabel = label('Zone', dnode.inputs['X-axis'].statmenu, dnode.timemenu, dnode.inputs['X-axis'].zonermenu)
            elif dnode.inputs['X-axis'].rtypemenu == 'Linkage':
                if (dnode.inputs['X-axis'].rtypemenu, dnode.inputs['X-axis'].links[0].from_node['resdict'][rd][0:2]) == ('Linkage',[dnode.inputs['X-axis'].linkmenu, dnode.inputs['X-axis'].linkrmenu]):
                    xdata = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['X-axis'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate)
                    xlabel = label('Linkage', dnode.inputs['X-axis'].statmenu, dnode.timemenu, dnode.inputs['X-axis'].linkrmenu)
    
    rn = dnode.inputs['Y-axis 1'].links[0].from_node
    for rd in rn['resdict']:
        if dnode.inputs['Y-axis 1'].rtypemenu == 'Climate':
            if rn['resdict'][rd][0:2] == [dnode.inputs['Y-axis 1'].rtypemenu, dnode.inputs['Y-axis 1'].climmenu]:
                y1data = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 1'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate) 
                ylabel = label('Climate', dnode.inputs['Y-axis 1'].statmenu, dnode.timemenu, dnode.inputs['Y-axis 1'].climmenu)
                line, =plt.plot(xdata, y1data, color='k', label='Ambient ' + (" ("+dnode.inputs['Y-axis 1'].statmenu + ")", "")[dnode.timemenu == '0'])    

        elif dnode.inputs['Y-axis 1'].rtypemenu == 'Zone':
            if (dnode.inputs['Y-axis 1'].rtypemenu, rn['resdict'][rd][0:2]) == ('Zone', [dnode.inputs['Y-axis 1'].zonemenu, dnode.inputs['Y-axis 1'].zonermenu]):
                y1data = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 1'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate)
                ylabel = label('Zone', dnode.inputs['Y-axis 1'].statmenu, dnode.timemenu, dnode.inputs['Y-axis 1'].zonermenu)
                line, =plt.plot(xdata, y1data, color='k', label=rn['resdict'][rd][0] + (" ("+dnode.inputs['Y-axis 1'].statmenu + ")", "")[dnode.timemenu == '0'])

        elif dnode.inputs['Y-axis 1'].rtypemenu == 'Linkage':
            if (dnode.inputs['Y-axis 1'].rtypemenu, rn['resdict'][rd][0:2]) == ('Linkage', [dnode.inputs['Y-axis 1'].linkmenu, dnode.inputs['Y-axis 1'].linkrmenu]):
                y1data = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 1'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate)
                ylabel = label('Linkage', dnode.inputs['Y-axis 1'].statmenu, dnode.timemenu, dnode.inputs['Y-axis 1'].linkrmenu)
                line, =plt.plot(xdata, y1data, color='k', label=rn['resdict'][rd][0] + (" ("+dnode.inputs['Y-axis 1'].statmenu + ")", "")[dnode.timemenu == '0']) 
    
    if dnode.inputs['Y-axis 2'].is_linked:
        rn = dnode.inputs['Y-axis 2'].links[0].from_node
        for rd in rn['resdict']:
            if dnode.inputs['Y-axis 2'].rtypemenu == 'Climate':
                if dnode.inputs['Y-axis 2'].links[0].from_node['resdict'][rd][0:2] == [dnode.inputs['Y-axis 2'].rtypemenu, dnode.inputs['Y-axis 2'].climmenu]:
                    y2data, ylabel = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 2'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate), rn['resdict'][rd][1]
                    line, = plt.plot(xdata, y2data, linestyle = '--', color = '0.75', label = 'Ambient ' + (" ("+dnode.inputs['Y-axis 2'].statmenu + ")", "")[dnode.timemenu == '0'])
            elif dnode.inputs['Y-axis 2'].rtypemenu == 'Zone':
                if (dnode.inputs['Y-axis 2'].rtypemenu, rn['resdict'][rd][0:2]) == ('Zone', [dnode.inputs['Y-axis 2'].zonemenu, dnode.inputs['Y-axis 2'].zonermenu]):
                    y2data = timedata(rn['resdict'][rd][si+3:ei+4], dnode.timemenu, dnode.inputs['Y-axis 2'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate)
                    line, = plt.plot(xdata, y2data, color = '0.75', linestyle = '--', label = rn['resdict'][rd][0] + (" ("+dnode.inputs['Y-axis 2'].statmenu + ")", "")[dnode.timemenu == '0'])
            elif dnode.inputs['Y-axis 2'].rtypemenu == 'Linkage':
                if (dnode.inputs['Y-axis 2'].rtypemenu, rn['resdict'][rd][0:2]) == ('Linkage', [dnode.inputs['Y-axis 2'].linkmenu, dnode.inputs['Y-axis 2'].linkrmenu]):
                    y1data = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 2'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate)
                    line, = plt.plot(xdata, y1data, color='k', label=rn['resdict'][rd][0] + (" ("+dnode.inputs['Y-axis 2'].statmenu + ")", "")[dnode.timemenu == '0'])
    
    
    if dnode.inputs['Y-axis 3'].is_linked:
        rn = dnode.inputs['Y-axis 3'].links[0].from_node
        for rd in rn['resdict']:
            if dnode.inputs['Y-axis 3'].rtypemenu == 'Climate':
                if rn['resdict'][rd][0:2] == [dnode.inputs['Y-axis 3'].rtypemenu, dnode.inputs['Y-axis 3'].climmenu]:
                    y3data, ylabel = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 3'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'],rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate), rn['resdict'][rd][1]
                    line, = plt.plot(xdata, y3data, linestyle = ':', color = '0.5',label = 'Ambient ' + (" ("+dnode.inputs['Y-axis 3'].statmenu + ")", "")[dnode.timemenu == '0'])
            elif dnode.inputs['Y-axis 3'].rtypemenu == 'Zone':
                if (dnode.inputs['Y-axis 3'].rtypemenu, rn['resdict'][rd][0:2]) == ('Zone', [dnode.inputs['Y-axis 3'].zonemenu, dnode.inputs['Y-axis 3'].zonermenu]):
                    y3data = timedata(rn['resdict'][rd][si+3:ei+4], dnode.timemenu, dnode.inputs['Y-axis 3'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'],rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate)
                    line, = plt.plot(xdata, y3data, linestyle = ':', color = '0.5',label = rn['resdict'][rd][0] + (" ("+dnode.inputs['Y-axis 3'].statmenu + ")", "")[dnode.timemenu == '0'])
            elif dnode.inputs['Y-axis 3'].rtypemenu == 'Linkage':
                if (dnode.inputs['Y-axis 3'].rtypemenu, rn['resdict'][rd][0:2]) == ('Linkage', [dnode.inputs['Y-axis 3'].linkmenu, dnode.inputs['Y-axis 3'].linkrmenu]):
                    y1data = timedata(rn['resdict'][rd][si+2:ei+3], dnode.timemenu, dnode.inputs['Y-axis 3'].statmenu, rn['resdict']['Month'], rn['resdict']['Day'], rn['resdict'][rn['dos']], dnode, si, ei, Sdate, Edate)
                    line, =plt.plot(xdata, y1data, color='k', label=rn['resdict'][rd][0] + (" ("+dnode.inputs['Y-axis 3'].statmenu + ")", "")[dnode.timemenu == '0'])
    
    plt.xlabel(xlabel)    
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.show()

