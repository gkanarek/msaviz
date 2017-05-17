# -*- coding: utf-8 -*-
"""
Created on Tue Nov  8 10:01:31 2016

@author: gkanarek
"""

from __future__ import absolute_import, division, print_function

import json
from collections import namedtuple
import csv
import os

from astropy.io import fits
from astropy.table import Table, QTable
from scipy.integrate import odeint
from astropy.modeling import models, fitting
import astropy.units as u
from scipy.interpolate import interp1d
import numpy as np

from .shuttercoord import ShutterCoord

#Use namedtuple to define the container for each quadrant of each reference
#file, in a format which is very easily serializable to JSON.
QuadrantModel = namedtuple('QuadrantBase', ['filter','grating','quadrant',
                                           'type1', 'param1', 'pix1', 
                                           'type2', 'param2', 'pix2'])

base_dir = os.path.dirname(os.path.realpath(__file__))

edges_file = os.path.join(base_dir, 'data', 'edges.json')
range_file = os.path.join(base_dir, 'data', 'ranges.json')
prism_file = os.path.join(base_dir, 'data', 'jwst_nirspec_prism_mos_wavelengths.fits')
disp_files = os.path.join(base_dir, 'data', 'jwst_nirspec_{}_disp.fits')

with open(edges_file) as f:
    edge_data = json.load(f)

quadrant_data = {}
for fg, edge in edge_data.items():
    f,g = fg.split("/")
    filtgrat = {}
    for q, sca in edge.items():
        filtgrat[int(q)] = QuadrantModel._make(sca)
    quadrant_data[(f,g)] = filtgrat

with open(range_file) as f:
    range_data = json.load(f)

#The prism requires some special handling, and has its own dedicated file.

def parse_msa_config(filename, return_all=False):
    """
    A function to read an MSA config file, which is a csv with values: 
        'x' (inactive), 0 (open), 1 (closed), 's' (stuck open)
    ...and then turn it into a dictionary of open shutters.
    
    The csv data has 730 rows and 342 columns. The quadrants correspond (using
    0-based indexing) to:
        - Q1 = row 365-729, col 000-170
        - Q2 = row 365-729, col 171-341
        - Q3 = row 000-364, col 000-170
        - Q4 = row 000-364, col 171-341
    
    Rows and columns will be swapped, to match up with my mental model of the 
    detector layout.
    
    Note that in MSA coords, shutter 1,1 for each quadrant is in the top right.
    
    We'll output a dictionary, with keys being tuples of (Q,I,J) for open shutters, 
    and values being False (for a normal open shutter) or True (for a stuck open
    shutter). Closed shutters are not included in the dictionary.
    """
    open_shutters = {}
    all_shutters = {}
    
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        next(reader) #the first row is a comment
        for x, column in enumerate(reader):
            for y, shutter in enumerate(column):
                cc = ShutterCoord.from_xy(x, y)
                if shutter in '0s':
                    open_shutters[cc.qij] = shutter == 's'
                all_shutters[cc.qij] = shutter
                
    if return_all:
        return all_shutters
    return open_shutters


class _MSA(object):
    """
    The workhorse object for calculating pixel-to-wavelength mappings for each
    filter/grating combination.
    
    Algorithmically, we determine an initial condition for a given shutter to
    use as an anchor point, then integrate the dispersion curve of the grating
    to map the rest of the pixels.
    
    Initial conditions are taken from (a) 2nd-degree, 2D polynomial fits to the
    ETC detector gap reference files, for all but the prism; or (b) a look-up
    table for the prism. 
    
    In addition, for the prism, a 3rd-degree, 1D polynomial correction is 
    applied to the integrated dispersion solution, to reduce pixel errors 
    (compared to the instrument model).
    """
    
    def __init__(self, filtname, gratingname):
        self.filter = filtname
        self.grating = gratingname
        self.sci_range = range_data["{}/{}".format(self.filter, self.grating)]
        
        dtable = fits.getdata(disp_files.format(self.grating),1)
        dwav = dtable['WAVELENGTH']
        dlds = dtable['DLDS']
        
        if self.grating == "prism":
            self.quadrants = []
            for q in range(1,5):
                tab = Table.read(prism_file, q)
                tab.add_index('I')
                tab.add_index('J')
                self.quadrants.append(tab)
            self.dispersion = interp1d(dwav, dlds, fill_value='extrapolate')
            self._eval = self._prism_wrapper
        else:
            self.quadrants = quadrant_data[(self.filter, self.grating)]
            fitter = fitting.LinearLSQFitter()
            self.dispersion = fitter(models.Polynomial1D(6), dwav, dlds)
            self._eval = self._grating_wrapper
    
    def __call__(self, *arg):
        return self._eval(*arg)
        
    def _prism_wrapper(self, coords):
        """
        Unlike for the gratings, the prism is not integrated over the same set 
        of pixels for each shutter. Therefore, we still need to integrate each
        shutter individually.
        """
        ns = len(coords)
        
        #we'll leave 0s wherever the spectrum doesn't fall on the detector
        output = np.zeros((2, ns, 2048), dtype=float)
        
        for idx,(q,c,r) in enumerate(coords):
            for n in (0,1):
                output[n,idx] = self._prism_evaluate(q,c,r,n)
        
        return output
        
    def _prism_evaluate(self, quadrant, i, j, nrs):
        """
        The prism requires special handling; this function integrates the
        dispersion curve just like the othrs, but then applies a 3rd-order
        polynomial correction which has previously been fit.
        """
        data = self.quadrants[quadrant]
        try:
            d1 = data.loc['I', i+1]
            row = d1.loc['J', j+1]
        except KeyError as key:
            return None
        pix, wav, par = [row[_+"49{}".format(nrs+1)] for _ in ['PIX','WAV','PAR']]
        
        if ~np.isfinite(wav):
            return None
        
        all_pix = np.arange(2048, dtype=float)
        in_bounds = np.logical_and(all_pix >= pix[0], all_pix <= pix[1])
        integrate_pixels = [pix[0]] + all_pix[in_bounds].tolist()
        
        base, dinfo = odeint(self._integrate_func, wav, integrate_pixels, 
                             full_output=True)
        correction = models.Polynomial1D(degree=3, c0=par[0], c1=par[1], 
                                         c2=par[2], c3=par[3])(all_pix[in_bounds])
        all_wav = np.zeros_like(all_pix)
        all_wav[in_bounds] = base.squeeze()[1:] + correction
        return all_wav    
    
    def _integrate_func(self, y, x):
        return self.dispersion(y)
        
    def _grating_integrate(self, pix0, params, i0, j0):
        """
        Perform the actual integration by way of scipy.integrate.odeint
        """
        dx = [-1,1][pix0 == 0] #integration direction
        outx = np.arange(2048, dtype=float) #pixels at which to integrate
        
        #Wavelength IC
        model = models.Polynomial2D(2)
        model.parameters = params
        wav = model(j0, i0)
        
        #integrate
        outy, dinfo = odeint(self._integrate_func, wav, outx[::dx], 
                             full_output=True)
        return outy[::dx] #go back to pixels 0->2047
    
    def _grating_wrapper(self, coords):
        """
        We only have two possible paths of integration: left-to-right, and 
        right-to-left. Using the magic of ODEINT, we can do each set of these
        simultaneously, then combine the results.
        """
        
        ns = coords.shape[1] #number of shutters we're checking
        
        #we'll leave 0s wherever the spectrum doesn't fall on the detector
        output = np.zeros((2, ns, 2048), dtype=float)
        
        for q, quad in self.quadrants.items():
            if q not in self.quadrants: #no shutters in this quadrant
                continue
            #which shutters are in this quadrant?
            idx, = (coords[0] == q).nonzero()
            
            if quad.pix1 is not None: #include NRS1
                output[0, idx] = self._grating_integrate(quad.pix1,
                                                         quad.param1,
                                                         coords[1,idx],
                                                         coords[2,idx]).T
            if quad.pix2 is not None:
                output[1, idx] = self._grating_integrate(quad.pix2,
                                                         quad.param2,
                                                         coords[1,idx],
                                                         coords[2,idx]).T
        
        return output

class MSAConfig(object):
    def __init__(self, filtername="", gratingname="", config_file=""):
        self.msa = None
        self.oidx = None
        self._nrs = None
        self._stu = None
        self.shutter_limits = None
        self.open_shutters = {}
        self.conf = ""
        self.fname = ""
        self.gname = ""
        
        self.update_instrument(filtername, gratingname)
        self.update_config(config_file)
        
    def update_config(self, config_file):
        """
        Parse an MSA config file and store the open shutters in a useful format
        for calculations.
        """
        if not config_file:
            return
        self.conf = config_file
        self.open_shutters = parse_msa_config(self.conf)
        
        qrc,s = zip(*sorted(self.open_shutters.items()))
        self.quads, self.cols, self.rows = np.vstack(list(zip(*qrc)))
        self.stuck = np.array(s)
        self.opens = ~self.stuck
        self.oidx, = self.opens.nonzero()
        self.nopen = self.oidx.size
        self._calculate()
    
    def update_instrument(self, filtername, gratingname):
        """
        Create the MSA integrator object.
        """
        if not filtername or not gratingname:
            return
        self.fname = filtername
        self.gname = gratingname
        
        self.msa = _MSA(self.fname, self.gname)
        self.sci_range = self.msa.sci_range
        self._calculate()
    
    def wavelength(self, quadrants, rows, columns):
        if not self.conf or not self.fname:
            return None
        return self.msa(np.vstack((quadrants, rows, columns)))
        
    def _calculate(self):
        """
        Calculate all the wavelengths and shutter limits based on the config
        file and the filter + disperser choices.
        """
        self._nrs = np.zeros((2,2,171,2048), dtype=float)
        self._stu = np.zeros((2,2,171,2048), dtype=float)
        self.shutter_limits = None
        
        if not self.conf or not self.fname:
            return
        
        o = self.opens
        s = self.stuck
        coords = np.vstack((self.quads, self.cols, self.rows))

        lo, hi = self.sci_range
        all_waves = self.msa(coords)
        top = 1 - self.quads % 2
        lims = np.full((self.nopen, 4), np.nan, dtype=float)
        for n, waves in enumerate(all_waves):
            wopen = waves[o]
            wstuck = waves[s]
            
            self._stu[n, top[s], 170-coords[2,s]] = wstuck
            self._nrs[n, top[o], 170-coords[2,o]] = wopen
            
            ok = np.logical_and(wopen.min(axis=1) <= hi,
                                wopen.max(axis=1) >= lo)
            lims[ok,   n*2] = np.maximum(wopen[ok].min(axis=1), lo)
            lims[ok, 1+n*2] = np.minimum(wopen[ok].max(axis=1), hi)
        self.shutter_limits = lims
    
    @property
    def wavelength_table(self):
        """
        Return a QTable of wavelength limits.
        """
        limits = self.shutter_limits * u.micron
        lo1, hi1, lo2, hi2 = limits.T
        q, c, r = (self.quads[self.oidx] + 1, 
                   self.cols[self.oidx] + 1, 
                   self.rows[self.oidx] + 1)
        
        
        shutters = QTable([q, c, r, lo1, hi1, lo2, hi2], names=["Quadrant", 
                                                               "Column", "Row", 
                                                               "NRS1-min",
                                                               "NRS1-max", 
                                                               "NRS2-min", 
                                                               "NRS2-max"],
                      meta={"MSA Config File":self.conf,
                            "Open shutters": self.nopen,
                            "Filter": self.fname,
                            "Disperser": self.gname},
                      masked=True, dtype=('i4','i4','i4','f8','f8','f8','f8'))
        
        shutters['NRS1-min'].info.format = '6.4f'
        shutters['NRS1-max'].info.format = '6.4f'
        shutters['NRS2-min'].info.format = '6.4f'
        shutters['NRS2-max'].info.format = '6.4f'
        
        shutters['NRS1-min'].mask = ~np.isfinite(lo1)
        shutters['NRS1-max'].mask = ~np.isfinite(hi1)
        shutters['NRS2-min'].mask = ~np.isfinite(lo2)
        shutters['NRS2-max'].mask = ~np.isfinite(hi2)
        
        return shutters
    
    def write_wavelength_table(self, outfile):
        """
        Write the wavelengths table to an ascii file.
        """
        with open(outfile, 'w') as f:
            #print out the header
            f.write("## MSA Config File: {}\n".format(self.conf))
            f.write("## {} open shutters\n".format(self.nopen))
            f.write("## Filter: {}\n".format(self.fname))
            f.write("## Disperser: {}\n".format(self.gname))
            f.write("\n")
            self.wavelength_table.write(f, format='ascii.fixed_width_two_line')

def wavelength_table(config_file, filtername, gratingname, outfile=None):
    """
    A utility to expose the wavelength table export functionality from the 
    spectrum view screen, without requiring the use of the GUI.
    """
    
    msaconf = MSAConfig(filtername, gratingname, config_file)
    
    if outfile:
        msaconf.write_wavelength_table(outfile)
    return msaconf.wavelength_table