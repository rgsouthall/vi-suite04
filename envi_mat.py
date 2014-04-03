# EnVi materials database
s = 70
from collections import OrderedDict

class envi_materials(object):
    def __init__(self):
        # Define materials with a comma separated dictionary, with material name as key, giving (Roughness, Conductivity {W/m-K}, Density {kg/m3}, Specific Heat {J/kg-K}, Thermal Absorbtance, Solar Absorbtance, Visible Absorbtance, Default thickness)    
        self.metal_datd = {'Copper': ('Smooth', '200', '8900.0', '418.00', '0.72', '0.65', '0.65', '5'), 
                        'Steel': ('Smooth', '50', '7800.0', '502.0', '0.12', '0.2', '0.2', '5'), 
                        'Aluminium': ('Smooth', '210', '2700', '880.00', '0.22', '0.2', '0.2', '5'),
                        'Lead': ('Smooth', '35.3', '11340', '128.00', '0.05', '0.05', '0.05', '5')}
        self.metal_dat = OrderedDict(sorted(self.metal_datd.items()))
        
        self.brick_datd = {'Standard Brick': ('Rough', '0.8', '1800', '900.00', '0.900000', '0.600000', '0.600000', '100'), 
                        'Inner brick': ('Rough', '0.62', '1800', '840.00', '0.93', '0.700000', '0.700000', '100'),
                        'Outer brick': ('Rough', '0.96', '2000', '650.00', '0.90', '0.930000', '0.930000', '100'),
                        'Vermiculite insulating brick': ('Rough', '0.27', '700', '840.00', '0.90', '0.650000', '0.650000', '100'),
                        'Honeycomb brick': ('Rough', '0.27', '1700', '1000.00', '0.90', '0.7', '0.7', '102')}
        self.brick_dat = OrderedDict(sorted(self.brick_datd.items()))
        
        self.cladding_datd = {'Stucco': ('Smooth', '0.692', '1858', '836.00', '0.900000', '0.9200000', '0.920000', '25'),
                              'Plaster board': ('Smooth', '0.7264', '1602', '836.00', '0.900000', '0.9200000', '0.920000', '20')}
        self.cladding_dat = OrderedDict(sorted(self.cladding_datd.items()))
        
        self.concrete_datd = {'Light mix concrete': ('MediumRough', '0.38', '1200.0', '653', '0.9', '0.65', '0.65', '100'),
                        'Aerated concrete block': ('Rough', '0.24', '750.0', '1000', '0.9', '0.65', '0.65', '100'),
                        'Inner concrete block': ('Rough', '0.51', '1400.0', '1000', '0.9', '0.65', '0.65', '100'),
                        'Heavy mix concrete': ('Rough', '1.4', '2100.0', '653.0', '0.90', '0.65', '0.65', '100'),
                        'Concrete Floor slab': ('MediumRough', '1.73', '2242.6', '836.0', '0.90', '0.65', '0.65', '100')}
        self.concrete_dat = OrderedDict(sorted(self.concrete_datd.items()))
        
        self.wood_datd = {'Wood flooring': ('MediumSmooth', '0.14', '600.0', '1210.0', '0.91', '0.65', '0.65', '25'),
                        'Parquet flooring': ('MediumSmooth', '0.17', '740.0', '2000.0', '0.90', '0.65', '0.65', '12'),
                        'Medium hardboard': ('MediumSmooth', '0.17', '740.0', '2000.0', '0.90', '0.65', '0.65', '12'),
                        'Plywood': ('MediumSmooth', '0.15', '700.0', '1420.0', '0.90', '0.65', '0.65', '25'),
                        'Chipboard': ('MediumSmooth', '0.15', '800.0', '2093.0', '0.91', '0.65', '0.65', '25'),
                        'Hardwood': ('MediumSmooth', '0.16', '720.8', '1255.2', '0.90', '0.78', '0.78', '50')}
        self.wood_dat = OrderedDict(sorted(self.wood_datd.items()))
        
        self.stone_datd = {'Sandstone': ('MediumSmooth', '1.83', '2200.0', '712.0', '0.90', '0.6', '0.6', '200'),
                         'Clay tile': ('MediumSmooth', '0.85', '1900.0', '837.0', '0.90', '0.6', '0.6', '6'),
                         'Common earth': ('Rough', '1.28', '1460.0', '879.0', '0.90', '0.85', '0.85', '200'),                
                         'Gravel': ('Rough', '1.28', '1460.0', '879.0', '0.90', '0.85', '0.85', '200')}
        self.stone_dat = OrderedDict(sorted(self.stone_datd.items()))
        
        self.gas_datd = {'Air 20-50mm': ('Gas', 'Air', '0.17'),
                        'Horizontal Air 20-50mm Heat Down': ('Gas', 'Air', '0.21'),
                        'Horizontal Air 20-50mm Heat Up': ('Gas', 'Air', '0.17')}
        self.gas_dat = OrderedDict(sorted(self.gas_datd.items()))
        
        self.wgas_datd = {'Argon': ('Gas', 'Argon'),
                        'Krypton':('Gas', 'Krypton'),
                        'Xenon':('Gas', 'Xenon'),
                        'Air': ('Gas', 'Air')}
        self.wgas_dat = OrderedDict(sorted(self.wgas_datd.items()))
        
        self.glass_datd = {'Clear 6mm': ('Glazing', 'SpectralAverage', '', '0.006', '0.775', '0.071', '0.071', '0.881', '0.080', '0.080', '0.0', '0.84', '0.84', '0.9'),
                          'Clear 3mm': ('Glazing', 'SpectralAverage', '', '0.003', '0.837', '0.075', '0.075', '0.898', '0.081', '0.081', '0.0', '0.84', '0.84', '0.9'),
                          'Clear 6mm LoE': ('Glazing', 'SpectralAverage', '', '0.006', '0.600', '0.0170', '0.220', '0.840', '0.055', '0.078', '0.0', '0.84', '0.10', '0.9'),
                          'Clear 3mm LoE': ('Glazing', 'SpectralAverage', '', '0.003', '0.630', '0.190', '0.220', '0.850', '0.056', '0.079', '0.0', '0.84', '0.10', '0.9')}
        self.glass_dat = OrderedDict(sorted(self.glass_datd.items()))
        
        self.insulation_datd = {'Glass fibre quilt': ('Rough', '0.04', '12.0', '840.0', '0.9', '0.65', '0.65', '100'),
                        'EPS': ('MediumSmooth', '0.05', '15', '1000.0', '0.90', '0.7', '0.7', '100'),
                        'Cavity wall insul': ('Rough', '0.037', '300.0', '1000.0', '0.90', '0.6', '0.6', '100'),
                        'Roofing felt': ('Rough', '0.19', '960.0', '837.0', '0.90', '0.9', '0.9', '6'),
                        'Wilton wool carpet': ('Rough', '0.06', '186.0', '1360.0', '0.90', '0.60', '0.60', '5'),
                        'Thermawall TW50': ('MediumSmooth', '0.022', '32.000', '1500', '0.900000', '0.600000', '0.600000', '200')}
        self.insulation_dat = OrderedDict(sorted(self.insulation_datd.items()))
        
        self.namedict = OrderedDict()
        self.thickdict = OrderedDict()
        self.i = 0
        self.matdat = OrderedDict()
        self.matdat.update(self.brick_dat)
        self.matdat.update(self.cladding_dat)
        self.matdat.update(self.concrete_dat)
        self.matdat.update(self.gas_dat)
        self.matdat.update(self.insulation_dat)
        self.matdat.update(self.metal_dat)
        self.matdat.update(self.stone_dat)
        self.matdat.update(self.wood_dat)
        self.matdat.update(self.glass_dat)
        self.matdat.update(self.wgas_dat)
        
    def omat_write(self, idf_file, name, stringmat, thickness):
        idf_file.write("Material,\n\
    {0:{width}}! - Name\n\
    {2[0]:{width}}! - Roughness\n\
    {1:{width}}! - Thickness (m)\n\
    {2[1]:{width}}! - Conductivity (W/m-K)\n\
    {2[2]:{width}}! - Density (kg/m3)\n\
    {2[3]:{width}}! - Specific Heat Capacity (J/kg-K)\n\
    {2[4]:{width}}! - Thermal Absorptance\n\
    {2[5]:{width}}! - Solar Absorptance\n\
    {2[6]:{width}}! - Visible Absorptance\n\n".format(name + ",", thickness + ",", stringmat, width = s-4))

    def amat_write(self, idf_file, name, stringmat):        
        idf_file.write("Material:AirGap,\n\
    {0:{width}}! - Name\n\
    {1:{width}}! - Resistance\n\n".format(name + ",", stringmat, width = s-4))
    
    def tmat_write(self, idf_file, name, stringmat, thickness):
        idf_file.write("WindowMaterial:{2[0]}\n\
    {0:{width}}! - Name\n\
    {2[1]:{width}}! - Optical Data Type\n\
    {2[2]:{width}}! - Window Glass Spectral Data Set Name\n\
    {1:{width}}! - Thickness (m)\n\
    {2[4]:{width}}! - Solar Transmittance at Normal Incidence\n\
    {2[5]:{width}}! - Front Side Solar Reflectance at Normal Incidence\n\
    {2[6]:{width}}! - Back Side Solar Reflectance at Normal Incidence\n\
    {2[7]:{width}}! - Visible Transmittance at Normal Incidence\n\
    {2[8]:{width}}! - Front Side Visible Reflectance at Normal Incidence\n\
    {2[9]:{width}}! - Back Side Visible Reflectance at Normal Incidence\n\
    {2[10]:{width}}! - Infrared Transmittance at Normal Incidence\n\
    {2[11]:{width}}! - Front Side Infrared Hemispherical Emissivity\n\
    {2[12]:{width}}! - Back Side Infrared Hemispherical Emissivity\n\
    {2[13]:{width}}! - Conductivity (W/m-K)\n\n".format(name + ",", thickness + ",", stringmat, width = s-4))
    
    def gmat_write(self, idf_file, name, stringmat, thickness):           
        idf_file.write("WindowMaterial:{1[0]}\n\
    {0:{width}}! - Name\n\
    {1[1]:{width}}! - Gas Type\n\
    {2:{width}}! - Thickness\n\n".format(name + ",", stringmat, thickness + ";", width = s-4))   


class envi_constructions(object):
    def __init__(self):
        self.wall_cond = {'External Wall 1': ('Standard Brick', 'Thermawall TW50', 'Inner concrete block'), 'Party Wall 1': ('Plaster board', 'Standard Brick', 'Plaster board')}
        self.wall_con = OrderedDict(sorted(self.wall_cond.items()))
        self.floor_cond = {'Ground Floor 1': ('Common earth', 'Gravel', 'Heavy mix concrete', 'Horizontal Air 20-50mm Heat Down', 'Chipboard')}
        self.floor_con = OrderedDict(sorted(self.floor_cond.items()))
        self.roof_cond = {'Roof 1': ('Clay tile', 'Roofing felt', 'Plywood')}
        self.roof_con = OrderedDict(sorted(self.roof_cond.items()))
        self.door_cond = {'Internal Door 1': ('Chipboard', 'Hardwood', 'Chipboard')}
        self.door_con = OrderedDict(sorted(self.door_cond.items()))
        self.glaze_cond = {'Standard Double Glazing': ('Clear 3mm', 'Air', 'Clear 3mm'), 'Low-E Double Glazing': ('Clear 3mm', 'Air', 'Clear 3mm LoE')}
        self.glaze_con = OrderedDict(sorted(self.glaze_cond.items()))
        self.p = 0
    
    def con_write(self, idf_file, contype, name, nl, mn):
        con = (self.wall_con, self.roof_con, self.floor_con, self.door_con, self.glaze_con)[("Wall", "Roof", "Floor", "Door", "Window").index(contype)]
        idf_file.write("Construction,\n\
    {0:{width}}! - Name\n\
    {1:{width}}! - Outside Layer\n".format(mn+",", con[name][0]+'-'+nl+(";", ",", ",", ",", ",")[len(con[name]) - 1], width = s-4))
        for i in range(len(con[name])):
            if i > 0:
                idf_file.write("    {0:{width}}{1}".format(con[name][i]+'-'+nl+(';', ',', ',', ',', ',')[len(con[name]) - i - 1], "! - Layer "+str(i), width = s-4)+("\n\n", "\n", "\n", "\n", "\n")[len(con[name]) - i - 1])
        
