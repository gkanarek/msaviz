# -*- coding: utf-8 -*-
"""
Created on Tue Nov  8 10:01:31 2016

@author: gkanarek
"""

from __future__ import absolute_import, division, print_function#, unicode_literals

import json
from collections import namedtuple
import csv
import os

from astropy.io import fits
from astropy.table import Table
from scipy.integrate import odeint
from astropy.modeling import models, fitting
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


class MSA(object):
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
            self._eval = self._prism_evaluate
        else:
            self.quadrants = quadrant_data[(self.filter, self.grating)]
            fitter = fitting.LinearLSQFitter()
            self.dispersion = fitter(models.Polynomial1D(6), dwav, dlds)
            self._eval = self._grating_evaluate
    
    def __call__(self, *arg):
        return self._eval(*arg)
    
    def _prism_evaluate(self, quadrant, i, j, nrs):
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
        
        base, dinfo = odeint(self.func, wav, integrate_pixels, 
                             full_output=True)
        correction = models.Polynomial1D(degree=3, c0=par[0], c1=par[1], 
                                         c2=par[2], c3=par[3])(all_pix[in_bounds])
        all_wav = np.zeros_like(all_pix)
        all_wav[in_bounds] = base.squeeze()[1:] + correction
        return all_wav
    
    def func(self, y, x):
        return self.dispersion(y)
        
    def _grating_integrate(self, x0, y0):
        dx = [-1,1][x0 == 0]
        outx = np.arange(2048, dtype=float)
        outy, dinfo = odeint(self.func, y0, outx[::dx], full_output=True)
        if outy.max() > 20:
            import pdb; pdb.set_trace()
        return outy[::dx]
        
    def _grating_evaluate(self, quadrant, i, j, nrs):
        quadmodel = self.quadrants[quadrant]
        p, t, c = [(quadmodel.pix1, quadmodel.type1, quadmodel.param1), 
                   (quadmodel.pix2, quadmodel.type2, quadmodel.param2)][nrs]
        if p is None:
            return None
        model = models.Polynomial2D(2)
        model.parameters = c
        wav = model(j,i)
        return self._grating_integrate(p, wav).squeeze()


def parse_msa_config(filename, return_all = False):
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