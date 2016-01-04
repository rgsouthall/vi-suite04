import sys, bpy
from .vi_func import retmenu

def label(dnode, metric, axis, variant):
    catdict = {'clim': 'Ambient', 'zone': 'Zone', 'Linkage': 'Linkage', 'External node': 'External node', 'Frames': 'Frame', 'metric': dnode.inputs[axis].rtypemenu + ' metric', 'type': metric} 
    animdict = {'metric': dnode.inputs[axis].rtypemenu + ' metric', 'type': metric}
    if dnode.animated:
        return animdict[variant]
    else:
        return catdict[variant]

def llabel(dnode, metric, axis, variant):
    rdict = {'Climate': 'Ambient', 'Zone': dnode.inputs[axis].zonemenu}
    ldict = {'type': rdict[dnode.inputs[axis].rtypemenu], 'metric': metric, }
    return ldict[variant]
    
def statdata(res, stat):
    if stat == 'Average':
        return([sum(r)/len(r) for r in res])
    elif stat == 'Maximum':
        return([max(r) for r in res])
    elif stat == 'Minimum':
        return([min(r) for r in res])
        
def rvariant(dnode):
    axes = ('Y-axis 1', 'Y-axis 2', 'Y-axis 3')
#        if dnode.inputs[axis].links:
    zones = [dnode.inputs[axis].zonemenu for axis in axes if dnode.inputs[axis].links and dnode.inputs[axis].rtypemenu == 'Zone']
    clims = [dnode.inputs[axis].climmenu for axis in axes if dnode.inputs[axis].links and dnode.inputs[axis].rtypemenu == 'Climate']
    links = [dnode.inputs[axis].climmenu for axis in axes if dnode.inputs[axis].links and dnode.inputs[axis].rtypemenu == 'Linkage']
    if zones and len(set(zones)) + len(set(clims)) == len(zones + clims):
        return 'type'
#    if clims and len(set(clims)) == len(zones + clims):
#        return 'clim'
    else:
        return 'metric'
            
def timedata(datastring, timetype, stattype, months, days, dos, dnode, Sdate, Edate):
    if timetype == '0' or dnode.animated:
        return datastring       
    else:
        if timetype == '1':     
            res = [[] for d in range(dnode['Start'], dnode['End']+1)]
            for h, val in enumerate(datastring):
                res[dos[h] - dnode['Start']].append(val)

        elif timetype == '2':
            res = [[] for m in range(Sdate.month, Edate.month + 1)]
            for h, val in enumerate(datastring):
                res[months[h] - Sdate.month].append(val)
        return(statdata(res, stattype))

def retframe(axis, dnode, frames):
    if len(set(frames)) > 1 and dnode.animated:
        return 'All'
    elif len(set(frames)) > 1:
        return dnode.inputs[axis].framemenu
    else:
        return frames[0]
    

def chart_disp(chart_op, plt, dnode, rnodes, Sdate, Edate):
    variant = rvariant(dnode)
    print(variant)
    rnx = dnode.inputs['X-axis'].links[0].from_node
    rlx = rnx['reslists']
    rzlx = list(zip(*rlx))
    framex = retframe('X-axis', dnode, rzlx[0])
    mdata = [rx[4].split() for rx in rlx if rx[0] == framex and rx[1] == 'Time' and rx[2] == '' and rx[3] == 'Month']
    ddata = [rx[4].split() for rx in rlx if rx[0] == framex and rx[1] == 'Time' and rx[2] == '' and rx[3] == 'Day']
    sdata = [rx[4].split() for rx in rlx if rx[0] == framex and rx[1] == 'Time' and rx[2] == '' and rx[3] == 'DOS']
    hdata = [rx[4].split() for rx in rlx if rx[0] == framex and rx[1] == 'Time' and rx[2] == '' and rx[3] == 'Hour']
    
    if len(set(rzlx[0])) > 1 and dnode.animated:
        si, ei = dnode["Start"] - bpy.context.scene.frame_start, dnode["End"]  - bpy.context.scene.frame_start
    else:        
        sm, sd, sh, em, ed, eh = Sdate.month, Sdate.day, Sdate.hour, Edate.month, Edate.day, Edate.hour    
        (dm, dd, dh) = ([int(x) for x in mdata[0]], [int(x) for x in ddata[0]], [int(x) for x in hdata[0]])
        for i in range(len(hdata[0])):
            if sm == dm[i] and sd == dd[i] and sh == dh[i] - 1:
                si = i
            elif em == dm[i] and ed == dd[i] and eh == dh[i] - 1:
                ei = i
                        
        mdata = [int(m) for m in mdata[0]][si:ei + 1]
        ddata = [int(d) for d in ddata[0]][si:ei + 1]
        sdata = [int(s) for s in sdata[0]][si:ei + 1]

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
        data = [rx[4].split()[si:ei + 1] for rx in rlx if rx[0] == framex and rx[1] == dnode.inputs['X-axis'].rtypemenu and rx[2] == menus[0] and rx[3] == menus[1]][0]
        xdata = timedata([dnode.inputs['X-axis'].multfactor * float(xd) for xd in data], dnode.timemenu, dnode.inputs['X-axis'].statmenu, mdata, ddata, sdata, dnode, Sdate, Edate)
#        xlabel = label(dnode.inputs['X-axis'].rtypemenu, dnode.inputs['X-axis'].statmenu, dnode.timemenu, menus[1])
        xlabel = label(dnode, menus[1], 'X-axis', variant)
                    
    rny1 = dnode.inputs['Y-axis 1'].links[0].from_node
    rly1 = rny1['reslists']
    rzly1 = list(zip(*rly1))
    framey1 = retframe('Y-axis 1', dnode, rzly1[0])
    menusy1 = retmenu(dnode, 'Y-axis 1', dnode.inputs['Y-axis 1'].rtypemenu)
    print(menusy1[1])
    y1d = [ry1[4].split()[si:ei + 1] for ry1 in rly1 if ry1[0] == framey1 and ry1[1] == dnode.inputs['Y-axis 1'].rtypemenu and ry1[2] == menusy1[0] and ry1[3] == menusy1[1]][0]
    y1data = timedata([dnode.inputs['Y-axis 1'].multfactor * float(y) for y in y1d], dnode.timemenu, dnode.inputs['Y-axis 1'].statmenu, mdata, ddata, sdata, dnode, Sdate, Edate)
#    ylabel = label(dnode.inputs['Y-axis 1'].rtypemenu, dnode.inputs['Y-axis 1'].statmenu, dnode.timemenu, menusy1[1])
    ylabel = label(dnode, menusy1[1], 'Y-axis 1', variant)
    line, = plt.plot(xdata, [dnode.inputs['Y-axis 1'].multfactor * float(yd) for yd in y1data], color='k', linewidth = 0.2, label = llabel(dnode, menusy1[1], 'Y-axis 1', variant))    
       
    if dnode.inputs['Y-axis 2'].links:
        rny2 = dnode.inputs['Y-axis 2'].links[0].from_node
        rly2 = rny2['reslists']
        rzly2 = list(zip(*rly2))
        framey2 = retframe('Y-axis 2', dnode, rzly2[0])
        menusy2 = retmenu(dnode, 'Y-axis 2', dnode.inputs['Y-axis 2'].rtypemenu)
        y2d = [ry2[4].split()[si:ei + 1] for ry2 in rly2 if ry2[0] == framey2 and ry2[1] == dnode.inputs['Y-axis 2'].rtypemenu and ry2[2] == menusy2[0] and ry2[3] == menusy2[1]][0]
        y2data = timedata([float(y) for y in y2d], dnode.timemenu, dnode.inputs['Y-axis 2'].statmenu, mdata, ddata, sdata, dnode, Sdate, Edate)
#        ylabel = label(dnode.inputs['Y-axis 2'].rtypemenu, dnode.inputs['Y-axis 2'].statmenu, dnode.timemenu, menusy2[1])
        ylabel = label(dnode, menusy2[1], 'Y-axis 2', variant)
        line, = plt.plot(xdata, [dnode.inputs['Y-axis 2'].multfactor * float(yd) for yd in y2data], color='k', linewidth = 0.2, label = llabel(dnode, menusy2[1], 'Y-axis 2', variant))    
 
    if dnode.inputs['Y-axis 3'].links:
        rny3 = dnode.inputs['Y-axis 3'].links[0].from_node
        rly3 = rny3['reslists']
        rzly3 = list(zip(*rly3))
        framey3 = retframe('Y-axis 3', dnode, rzly3[0])
        menusy3 = retmenu(dnode, 'Y-axis 3', dnode.inputs['Y-axis 2'].rtypemenu)
        y3d = [ry3[4].split()[si:ei + 1] for ry3 in rly3 if ry3[0] == framey3 and ry3[1] == dnode.inputs['Y-axis 3'].rtypemenu and ry3[2] == menusy3[0] and ry3[3] == menusy3[1]][0]
        y3data = timedata([float(y) for y in y3d], dnode.timemenu, dnode.inputs['Y-axis 3'].statmenu, mdata, ddata, sdata, dnode, Sdate, Edate)
        ylabel = label(dnode.inputs['Y-axis 3'].rtypemenu, dnode.inputs['Y-axis 3'].statmenu, dnode.timemenu, menusy3[1])
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
