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
    rnx = dnode.inputs['X-axis'].links[0].from_node
    rdx = rnx['resdictnew']
    framex = dnode.inputs['X-axis'].framemenu if len(rnx['resdictnew']) > 1 else rnx['resdictnew'].keys()[0]
    rdxf = rdx[framex]
    if len(rnx['resdictnew']) > 1 and dnode.animated:
        pass
    else:        
        sm, sd, sh, em, ed, eh = Sdate.month, Sdate.day, Sdate.hour, Edate.month, Edate.day, Edate.hour    
        (dm, dd, dh) = ([int(x) for x in rdxf['Time']['Month'].split()], [int(x) for x in rdxf['Time']['Day'].split()], [int(x) for x in rdxf['Time']['Hour'].split()])
        for i in range(len(rdxf['Time']['Hour'].split())):
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
        rdxft = rdxf[dnode.inputs['X-axis'].rtypemenu]
        for rd in rdxft.keys():
            if rd == menus[0]:
                xdata = timedata([dnode.inputs['X-axis'].multfactor * float(xd) for xd in rdxft[rd].split()[si:ei + 1]], dnode.timemenu, dnode.inputs['X-axis'].statmenu, rdxf['Time']['Month'], rdxf['Time']['Day'], rdxf['Time']['dos'], dnode, si, ei, Sdate, Edate)
                xlabel = label(dnode.inputs['X-axis'].rtypemenu, dnode.inputs['X-axis'].statmenu, dnode.timemenu, menus[0])
                break
                    
    rny1 = dnode.inputs['Y-axis 1'].links[0].from_node
    rdy1 = rny1['resdictnew']
    framey1 = dnode.inputs['Y-axis 1'].framemenu if len(rnx['resdictnew']) > 1 else rny1['resdictnew'].keys()[0]
    rdy1f = rdy1[framey1]
    menusy1 = retmenu(dnode, 'Y-axis 1', dnode.inputs['Y-axis 1'].rtypemenu)
    rdy1ft = rdy1f[dnode.inputs['Y-axis 1'].rtypemenu]

    for rd in rdy1ft.keys():
        if rd == menusy1[0]:
            y1data = timedata(rdy1ft[rd].split()[si:ei + 1], dnode.timemenu, dnode.inputs['Y-axis 1'].statmenu, rdy1f['Time']['Month'], rdy1f['Time']['Day'], rdy1f['Time']['dos'], dnode, si, ei, Sdate, Edate)
            ylabel = label(dnode.inputs['Y-axis 1'].rtypemenu, dnode.inputs['Y-axis 1'].statmenu, dnode.timemenu, menusy1[0])
            line, = plt.plot(xdata, [dnode.inputs['Y-axis 1'].multfactor * float(yd) for yd in y1data], color='k', linewidth = 0.2, label=dnode.inputs['Y-axis 1'].rtypemenu + (" ("+dnode.inputs['Y-axis 1'].statmenu + ")", "")[dnode.timemenu == '0'])    
            break
        
    if dnode.inputs['Y-axis 2'].links:
        rny2 = dnode.inputs['Y-axis 2'].links[0].from_node
        rdy2 = rny2['resdictnew']
        framey2 = dnode.inputs['Y-axis 2'].framemenu if len(rnx['resdictnew']) > 1 else rny2['resdictnew'].keys()[0]
        rdy2f = rdy2[framey2]
        menus = retmenu(dnode, 'Y-axis 2', dnode.inputs['Y-axis 2'].rtypemenu)
        rdy2ft = rdy1f[dnode.inputs['Y-axis 2'].rtypemenu]
        
        for rd in rdy1ft.keys():
            if rd == menus[0]:
                y2data = timedata(rdy2ft[rd].split()[si:ei + 1], dnode.timemenu, dnode.inputs['Y-axis 2'].statmenu, rdy2f['Time']['Month'], rdy1f['Time']['Day'], rdy2f['Time']['dos'], dnode, si, ei, Sdate, Edate)
                ylabel = label(dnode.inputs['Y-axis 2'].rtypemenu, dnode.inputs['Y-axis 2'].statmenu, dnode.timemenu, menus[0])
                line, = plt.plot(xdata, [dnode.inputs['Y-axis 2'].multfactor * float(yd) for yd in y2data], color='k', linewidth = 0.2, label=dnode.inputs['Y-axis 2'].rtypemenu + (" ("+dnode.inputs['Y-axis 2'].statmenu + ")", "")[dnode.timemenu == '0'])    
                break
    if dnode.inputs['Y-axis 3'].links:
        rny3 = dnode.inputs['Y-axis 3'].links[0].from_node
        rdy3 = rny3['resdictnew']
        framey3 = dnode.inputs['Y-axis 3'].framemenu if len(rnx['resdictnew']) > 1 else rny3['resdictnew'].keys()[0]
        rdy3f = rdy3[framey3]
        menus = retmenu(dnode, 'Y-axis 3', dnode.inputs['Y-axis 3'].rtypemenu)
        rdy3ft = rdy3f[dnode.inputs['Y-axis 3'].rtypemenu]
        
        for rd in rdy1ft.keys():
            if rd == menus[0]:
                y3data = timedata(rdy3ft[rd].split()[si:ei + 1], dnode.timemenu, dnode.inputs['Y-axis 3'].statmenu, rdy3f['Time']['Month'], rdy3f['Time']['Day'], rdy3f['Time']['dos'], dnode, si, ei, Sdate, Edate)
                ylabel = label(dnode.inputs['Y-axis 3'].rtypemenu, dnode.inputs['Y-axis 3'].statmenu, dnode.timemenu, menus[0])
                line, = plt.plot(xdata, [dnode.inputs['Y-axis 3'].multfactor * float(yd) for yd in y3data], color='k', linewidth = 0.2, label=dnode.inputs['Y-axis 3'].rtypemenu + (" ("+dnode.inputs['Y-axis 3'].statmenu + ")", "")[dnode.timemenu == '0'])    

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
