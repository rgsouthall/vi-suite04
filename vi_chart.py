import sys
from .vi_func import retmenu

def label(cat, stat, time, metric):
    catdict = {'Climate': 'Ambient', 'Zone': 'Zone', 'Linkage': 'Linkage', 'External node': 'External node'} 
    st = stat if time != '0' else ''
    return('{} {} {} {}'.format(st, catdict[cat], ('Hourly', 'Daily', 'Monthly')[int(time)], metric))
    
def statdata(res, stat):
    if stat == 'Average':
        return([sum(r)/len(r) for r in res])
    elif stat == 'Maximum':
        return([max(r) for r in res])
    elif stat == 'Minimum':
        return([min(r) for r in res])

def timedata(datastring, timetype, stattype, months, days, dos, dnode, si, ei, Sdate, Edate):
    if timetype == '0':
        return datastring       
    else:
        if timetype == '1':     
            res = [[] for d in range(dnode['Start'], dnode['End']+1)]
            for h, val in enumerate(datastring):
                res[dos[si+h] - dnode['Start']].append(val)

        elif timetype == '2':
            res = [[] for m in range(Sdate.month, Edate.month + 1)]
            for h, val in enumerate(datastring):
                res[months[si+h] - Sdate.month].append(val)
        return(statdata(res, stattype))

def chart_disp(chart_op, plt, dnode, rnodes, Sdate, Edate):
    rn = dnode.inputs['X-axis'].links[0].from_node
    ard = rn['allresdict']
    sm, sd, sh, em, ed, eh = Sdate.month, Sdate.day, Sdate.hour, Edate.month, Edate.day, Edate.hour
    (dm, dd, dh) = ([int(x) for x in ard['Month']], [int(x) for x in ard['Day']], [int(x) for x in ard['Hour']])
    for i in range(len(ard['Hour'])):
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
        menus = retmenu(dnode, 'X-axis', dnode.inputs['X-axis'].rtypemenu)
        for rd in rn['resdict']:
            rn['resdict'][rd]
            if dnode.inputs['X-axis'].rtypemenu == 'Climate':
                if dnode.inputs['X-axis'].links[0].from_node['resdict'][rd][0:2] == [dnode.inputs['X-axis'].rtypemenu, dnode.inputs['X-axis'].climmenu]:
                    xdata = timedata(ard[rd][si:ei + 1], dnode.timemenu, dnode.inputs['X-axis'].statmenu, ard['Month'], ard['Day'], ard['dos'], dnode, si, ei, Sdate, Edate)
                    xlabel = label('Climate', dnode.inputs['X-axis'].statmenu, dnode.timemenu, dnode.inputs['X-axis'].climmenu)
            else:
                if (dnode.inputs['X-axis'].links[0].from_node['resdict'][rd][0:2]) == menus:
                    xdata = timedata(ard[rd][si:ei+1], dnode.timemenu, dnode.inputs['X-axis'].statmenu, ard['Month'], ard['Day'], ard['dos'], dnode, si, ei, Sdate, Edate)
                    xlabel = label(dnode.inputs['X-axis'].rtypemenu, dnode.inputs['X-axis'].statmenu, dnode.timemenu, menus[1])
                    
    rn = dnode.inputs['Y-axis 1'].links[0].from_node
    ard = rn['allresdict']
    for rd in rn['resdict']:
        if dnode.inputs['Y-axis 1'].rtypemenu == 'Climate':
            if rn['resdict'][rd][0:2] == [dnode.inputs['Y-axis 1'].rtypemenu, dnode.inputs['Y-axis 1'].climmenu]:
                y1data = timedata(ard[rd][si:ei+1], dnode.timemenu, dnode.inputs['Y-axis 1'].statmenu, ard['Month'], ard['Day'], ard['dos'], dnode, si, ei, Sdate, Edate) 
                ylabel = label('Climate', dnode.inputs['Y-axis 1'].statmenu, dnode.timemenu, dnode.inputs['Y-axis 1'].climmenu)
                line, = plt.plot(xdata, y1data, color='k', linewidth = 0.2, label='Ambient ' + (" ("+dnode.inputs['Y-axis 1'].statmenu + ")", "")[dnode.timemenu == '0'])    

        else:
            menus = retmenu(dnode, 'Y-axis 1', dnode.inputs['Y-axis 1'].rtypemenu)
            if (rn['resdict'][rd][0:2]) == (menus):
                y1data = timedata(ard[rd][si:ei+1], dnode.timemenu, dnode.inputs['Y-axis 1'].statmenu, ard['Month'], ard['Day'], ard['dos'], dnode, si, ei, Sdate, Edate)
                ylabel = label(dnode.inputs['Y-axis 1'].rtypemenu, dnode.inputs['Y-axis 1'].statmenu, dnode.timemenu, menus[1])
                line, = plt.plot(xdata, y1data, color='k', label=rn['resdict'][rd][0] + (" ("+dnode.inputs['Y-axis 1'].statmenu + ")", "")[dnode.timemenu == '0'])

    if dnode.inputs['Y-axis 2'].links:
        rn = dnode.inputs['Y-axis 2'].links[0].from_node 
        ard = rn['allresdict']
        menus = retmenu(dnode, 'Y-axis 2', dnode.inputs['Y-axis 2'].rtypemenu)
        for rd in rn['resdict']:
            if dnode.inputs['Y-axis 2'].rtypemenu == 'Climate':
                if dnode.inputs['Y-axis 2'].links[0].from_node['resdict'][rd][0:2] == [dnode.inputs['Y-axis 2'].rtypemenu, dnode.inputs['Y-axis 2'].climmenu]:
                    y2data = timedata(ard[rd][si:ei+1], dnode.timemenu, dnode.inputs['Y-axis 2'].statmenu, ard['Month'], ard['Day'], ard['dos'], dnode, si, ei, Sdate, Edate)
                    line, = plt.plot(xdata, y2data, linestyle = '--', color = '0.75', label = 'Ambient ' + (" ("+dnode.inputs['Y-axis 2'].statmenu + ")", "")[dnode.timemenu == '0'])
            else:                 
                if (rn['resdict'][rd][0:2]) == (menus):
                    y2data = timedata(ard[rd][si:ei+1], dnode.timemenu, dnode.inputs['Y-axis 2'].statmenu, ard['Month'], ard['Day'], ard['dos'], dnode, si, ei, Sdate, Edate)
                    line, = plt.plot(xdata, y2data, color='k', label=rn['resdict'][rd][0] + (" ("+dnode.inputs['Y-axis 2'].statmenu + ")", "")[dnode.timemenu == '0'])

    if dnode.inputs['Y-axis 3'].links:
        rn = dnode.inputs['Y-axis 3'].links[0].from_node
        ard = rn['allresdict']
        menus = retmenu(dnode, 'Y-axis 3', dnode.inputs['Y-axis 3'].rtypemenu)
        for rd in rn['resdict']:
            if dnode.inputs['Y-axis 3'].rtypemenu == 'Climate':
                if rn['resdict'][rd][0:2] == [dnode.inputs['Y-axis 3'].rtypemenu, dnode.inputs['Y-axis 3'].climmenu]:
                    y3data = timedata(ard[rd][si:ei+1], dnode.timemenu, dnode.inputs['Y-axis 3'].statmenu, ard['Month'], ard['Day'], ard['dos'], dnode, si, ei, Sdate, Edate)
                    line, = plt.plot(xdata, y3data, linestyle = ':', color = '0.5',label = 'Ambient ' + (" ("+dnode.inputs['Y-axis 3'].statmenu + ")", "")[dnode.timemenu == '0'])
            else:              
                if (rn['resdict'][rd][0:2]) == (menus):
                    y3data = timedata(ard[rd][si:ei+1], dnode.timemenu, dnode.inputs['Y-axis 3'].statmenu, ard['Month'], ard['Day'], ard['dos'], dnode, si, ei, Sdate, Edate)
                    line, = plt.plot(xdata, y3data, color='k', label=rn['resdict'][rd][0] + (" ("+dnode.inputs['Y-axis 3'].statmenu + ")", "")[dnode.timemenu == '0'])
    try:
        plt.xlabel(xlabel)    
        plt.ylabel(ylabel)
        plt.legend()
        plt.grid(True)
        plt.show(block = str(sys.platform) not in ('win32', 'darwin'))
    except Exception as e:
        chart_op.report({'ERROR'}, '{} Invalid data for this component'.format(e))
        

    def plot_graph(*args):
        args[0][0].plot()
        args[0][0].show()
