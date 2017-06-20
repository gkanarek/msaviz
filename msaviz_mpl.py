# -*- coding: utf-8 -*-
"""
Created on Thu May 18 09:33:22 2017

@author: gkanarek
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid

from msaviz import MSAConfig, parse_msa_config


class MSAVizMPL(object):
    """
    This is a version of the MSAViz prototype which produces output with 
    matplotlib instead of Kivy.
    """
    
    spectrum_view_style = {'text.color': (0.7, 0.7, 0.7),
                           'axes.facecolor': 'black',
                           'axes.edgecolor': 'black',
                           'figure.facecolor': (0.4, 0.4, 0.4),
                           'figure.figsize': (10, 7.5),
                           'figure.subplot.hspace': 0.,
                           'figure.subplot.wspace': 0.174,
                           'image.interpolation': 'none',
                           'image.cmap': 'Spectral_r',
                           'image.origin': 'lower'}
    shutter_view_style = {'text.color': (0.7, 0.7, 0.7),
                          'axes.facecolor': 'black',
                          'axes.edgecolor': 'black',
                          'figure.facecolor': (0.4, 0.4, 0.4),
                          'figure.figsize': (10, 7.5),
                          'figure.subplot.hspace': 0.02,
                          'figure.subplot.wspace': 0.02,
                          'image.interpolation': 'none',
                          'image.origin': 'upper'}
    
    def __init__(self, filtername, dispersername, config_file):
        self._msa = MSAConfig(filtername, dispersername, config_file)
        self.selected = []
        
    def write_wavelengths(self, outfile):
        self._msa.write_wavelength_table(outfile)
        
    @property
    def spectrum_view(self):
        """
        Construct the spectrum view in mpl.
        """
        
        l0, l1 = self._msa.sci_range #min and max wavelength range
        dl = (l1 - l0) / 3. #spacing of colorbar labels
        
        with plt.style.context(self.spectrum_view_style):
            fig = plt.figure()
            grid = ImageGrid(fig, 111, nrows_ncols=(2,2), cbar_mode='single',
                             cbar_location='top')
            qx, qy = [0,1,0,1], [1,1,0,0]
            for ax, x, y in zip(grid, qx, qy):
                im = ax.imshow(self._msa._nrs[x, y], vmin=l0, vmax=l1)
                ax.imshow(self._msa._stu[x, y], vmin=l0, vmax=l1, alpha=0.5)
                ax.axis('off')
            ax.cax.colorbar(im, ticks=[l0, l0+dl, l1-dl, l1])
            ax.cax.toggle_label(True)
        
        return fig
    
    @property
    def shutter_view(self):
        """
        Construct the shutter view in mpl.
        """
        all_shutters = parse_msa_config(self._msa.conf, open_only=False)
        color = {"0": [255, 155, 5, 255], "1": [0, 0, 0, 0],
                 "x": [68, 68, 68, 255], "s": [135, 44, 44, 255]}
        s_color = [29, 226, 226, 255]
        
        with plt.style.context(self.shutter_view_style):
            fig, ax = plt.subplots(2, 2, subplot_kw={'aspect':0.5})
            for q in range(4):
                qx, qy = [0,1,0,1], [1,1,0,0]
                data = np.zeros((365, 171, 4), dtype=np.uint8)
                for j in range(171):
                    for i in range(365):
                        val = all_shutters[(q,i,j)]
                        colr = color[val] if (q,i,j) not in self.selected else s_color
                        data[364-i,j] = colr
                ax[qx,qy].imshow(data)
                ax[qx,qy].text(182, 85, 'Q{}'.format(q+1), fontsize=30,
                               ha='center', va='center')
                ax[qx,qy].axis('off')
        
        return fig
                        
        
        
        