#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 14:24:34 2017

@author: gkanarek
"""

import os

from msaviz.msa import MSA, MSAConfig
from astropy.table import Table
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import timeit

rawdir = os.path.join(os.path.expanduser('~'),'Desktop','wave_tool_raw')
savedir = os.path.join(rawdir, 'accuracy')
fstub = 'jwst_nirspec_{}_{}_mos_gap.fits'
gstub = 'jwst_nirspec_{}_disp.fits'
prism = 'jwst_nirspec_clear_prism_mos_all.fits'
pris2 = 'prism_mos_wavelengths.fits'

filt_grating = [('f070lp', 'g140h'),
                ('f070lp', 'g140m'),
                ('f100lp', 'g140h'),
                ('f100lp', 'g140m'),
                ('f170lp', 'g235h'),
                ('f170lp', 'g235m'),
                ('f290lp', 'g395h'),
                ('f290lp', 'g395m'),
                ('clear', 'prism')]

def plot_quadrants(fname, dname):
    filename = os.path.join(rawdir, fstub.format(fname, dname))
    wtable = Table.read(filename, format='fits', hdu=1)
    outfile = os.path.join(savedir, "{}_{}_ref.png".format(fname, dname))
    data = np.zeros((4, 365, 171, 4), dtype=float)
    output_cols = ['WL491', 'WR491', #wavelengths located at the left and right boundaries of SCA491
                   'WL492', 'WR492'] #wavelengths located at the left and right boundaries of SCA492
    q, i, j = [wtable[x]-1 for x in 'QIJ'] #convert from 1-based to 0-based indexing
    #origin is in upper right, not upper left
    i = 364 - i
    
    #convert everything to a 3D numpy array
    data[q, i, j] = np.vstack((wtable[col] for col in output_cols)).T
    ii,jj = np.mgrid[:365,:171]
    
    edges = ['Q{} SCA1 left', 'Q{} SCA1 right', 
             'Q{} SCA2 left', 'Q{} SCA2 right ']
    
    fig = plt.figure(figsize=(16,16))
    fig.suptitle('{} + {}'.format(fname.upper(), dname.upper()), fontsize=30)
    
    for qu, quad in enumerate(data):
        ok = quad > 0.
        if not np.count_nonzero(ok):
            continue
        for edge in range(4):
            kk = ok[..., edge]
            tmp = ma.masked_array(quad[ii, jj, edge], mask=~kk, 
                                  fill_value=np.nan)
            ax = fig.add_subplot(4, 4, qu*4+edge+1, projection='3d')
            ax.plot_wireframe(ii, jj, tmp.filled(), rstride=5, cstride=5)
            
            if np.count_nonzero(kk):
                ax.set_xlabel('Shutter J')
                ax.set_ylabel('Shutter I')
                ax.set_zlabel('Wavelength (micron)')
                plt.locator_params(nbins=4, tight=True)
            else:
                ax.axes.xaxis.set_ticklabels([])
                ax.axes.yaxis.set_ticklabels([])
                ax.axes.zaxis.set_ticklabels([])
            ax.set_title(edges[edge].format(qu+1))
    
    fig.savefig(outfile)
    plt.close()
    
def get_valid_prism_shutters(tab):
    valid = []
    ptab = ['{}|{}|{}'.format(q,row['I'],row['J']) for q in range(1,5) for row in Table.read(os.path.join(rawdir, pris2), format='fits', hdu=q)]
    wtab = list(map(lambda qij: '{}|{}|{}'.format(*qij), zip(tab['Q'], tab['I'], tab['J'])))
    valid = list(filter(lambda n: wtab[n] in ptab, range(len(wtab))))
    return tab[valid]
    
    
def prism_accuracy(display=True):
    filename = os.path.join(rawdir, prism)
    wtable = Table.read(filename, format='fits', hdu=1)
    wtable = get_valid_prism_shutters(wtable)
    
    msa = MSA('clear', 'prism')
    
    err = []
    
    n = len(wtable)
    
    q, i, j = [wtable[x]-1 for x in 'QIJ']
    coords = np.vstack((q,i,j))
    pwaves = np.transpose(msa(coords), (1,0,2))
    
    for r,row in enumerate(wtable):
        #Get predicted wavelengths from MSA model
        pwav = pwaves[r]
        if not np.count_nonzero(np.isfinite(pwav)):
            continue
        for nrs in (0,1):
            p0 = row['PIXELX49{}'.format(nrs+1)][[0,99]]
            w0 = row['WAVELENGTH49{}'.format(nrs+1)][[0,99]]
            if 0. in w0:
                continue
            w1 = pwav[nrs,[np.ceil(p0[0]).astype(int), np.floor(p0[1]).astype(int)]]
            if ((w1-w0)/w0).min() < -0.5:
                import pdb; pdb.set_trace()
            err.extend(((w1-w0)/w0).tolist())
    
    print("Error: min {}, median {}, max {}, abs median {}".format(np.min(err),
                                                    np.median(err),
                                                    np.max(err), 
                                                    np.median(np.abs(err))))
            
    if display:
        stub = 'clear_prism.png'
        n, bins, patches = plt.hist(err, 100, facecolor='green', alpha=0.75)
        plt.suptitle('CLEAR + PRISM', fontsize=30)
        plt.yscale('log', nonposy='clip')
        plt.xlabel('fractional wavelength error')
        plt.ylabel('# of shutters')
        plt.savefig(os.path.join(savedir, stub), bbox_inches='tight')
        plt.close()
    
    return err


def accuracy(fname, dname, display=True):
    print("Now working on filter {}, disperser {}".format(fname, dname))
    #Compare with wavelengths from reference files
    if dname == 'prism':
        return prism_accuracy(display=display)
    filename = os.path.join(rawdir, fstub.format(fname, dname))
    wtable = Table.read(filename, format='fits', hdu=1)
    wtable.add_index('I')
    err = []
    lo, hi = wtable[0]['WMIN-SCIENCE'], wtable[0]['WMAX-SCIENCE']
    
    #initialize MSA model
    msa = MSA(fname, dname)
    locations = [(0, 0, 'WL491'), (0, 2047, 'WR491'), (1, 0, 'WL492'),
                     (1, 2047, 'WR492')]
    
    #Because there are too many to test them all at once, we'll go
    #by column.
    prog = 0.2
    for column in range(1,366):
        if column /365 >= prog:
            print("{}% complete".format(int(prog*100)))
            prog += 0.2
        #Get predicted wavelengths from MSA model
        msa_col = wtable.loc[column]
        q,i,j = [msa_col[x]-1 for x in 'QIJ']
        coords = np.vstack((q,i,j))
        pwaves = np.transpose(msa(coords), (0, 2, 1))
        for v, (det, edge, col) in enumerate(locations):
            wav = pwaves[det, edge]
            ref = msa_col[col]
            
            #group by reference flags
            low = (ref == -1) & (wav > 0.)
            high = (ref == -2) & (wav > 0.)
            on = (ref > 0) & (wav > 0.)
            
            #Store errors, dealing with flags appropriately
            err.extend((np.maximum(wav[low] - lo, 0.) / lo).tolist())
            err.extend((np.minimum(wav[high] - hi, 0.) / hi).tolist())
            err.extend(((wav[on] - ref[on]) / ref[on]).tolist())
    
    print("Error: min {}, median {}, max {}, abs median {}".format(np.min(err),
                                                    np.median(err),
                                                    np.max(err), 
                                                    np.median(np.abs(err))))
            
    if display:
        stub = '{}_{}.png'.format(fname, dname)
        n, bins, patches = plt.hist(err, 100, facecolor='green', alpha=0.75)
        plt.suptitle('{} + {}'.format(fname.upper(), dname.upper()), fontsize=30)
        plt.yscale('log', nonposy='clip')
        plt.xlabel('fractional wavelength error')
        plt.ylabel('# of shutters')
        plt.savefig(os.path.join(savedir, stub), bbox_inches='tight')
        plt.close()
    
    return err

if __name__ == "__main__":
    prism_accuracy()
    """
    for fg in filt_grating[:-1]:
        #plot_quadrants(*fg)
        #accuracy(*fg)
    for f,g in filt_grating:
        s = 'msa=MSAConfig("{}","{}","/Users/gkanarek/Desktop/TEST_config.csv")'.format(f,g)
        print(f, g, min(timeit.repeat(stmt=s, globals=globals(), number=10))/10.)
    msa = MSA('f170lp','g235m')
    runtime = []
    ns = [1]+list(range(5,305,5))
    for n in ns:
        q, i, j = [3]*n, list(range(10,n+10)), [50]*n
        coords = np.vstack((q,i,j))
        t = min(timeit.repeat('msa(coords)', globals=globals(), number=10))/10
        print(n, t)
        runtime.append(t)
    
    plt.plot(ns, runtime, '-+g')
    plt.xlabel('Number of open shutters')
    plt.ylabel('Computation time')
    plt.savefig(os.path.join(savedir,'comptime.png'), bbox_inches='tight')"""
        