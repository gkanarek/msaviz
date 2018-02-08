# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 10:25:25 2017

@author: gkanarek
"""
from __future__ import absolute_import, division, print_function

import numpy as np

from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import (ReferenceListProperty, VariableListProperty,
                             AliasProperty, ObjectProperty, NumericProperty,
                             BooleanProperty, BoundedNumericProperty)
from kivy.graphics.texture import Texture

#we use the reversed Spectral colormap to match wavelength.
#cmap.py replicates the Spectral_r functionality from matplotlib, 
#so we don't have to drag along the full mpl package for just this.
from ..cmap import spectral_cmap

Builder.load_string("""
<SpectralBase>:
    canvas.before:
        Color:
            rgba: 0, 0, 0, self.bg_shading
        Rectangle:
            size: self.size
            pos: self.pos
    canvas:
        Color:
            rgba: 1, 1, 1, self.txtr_shading
        Rectangle:
            size: self.inset_size
            pos: self.inset_pos
            texture: self.display_texture
    canvas.after:
        Color:
            rgba: 1, 1, 1, self.border[0]
        Line:
            points: self.border_points[0]
        Color:
            rgba: 1, 1, 1, self.border[1]
        Line:
            points: self.border_points[1]
        Color:
            rgba: 1, 1, 1, self.border[2]
        Line:
            points: self.border_points[2]
        Color:
            rgba: 1, 1, 1, self.border[3]
        Line:
            points: self.border_points[3] 
""")

class SpectralBase(Widget):
    """
    This is a base widget for anything which will want to display a texture
    using the spectral colormap defined in cmap.py. 
    
    A white border can be added by setting the SpectralBase.border 
    VariableListProperty to True; alternatively, the left, top, right, and 
    bottom borders (respectively) can be controlled by setting individual 
    elements of SpectralBase.border (which is of length 4). The width of the 
    border (default is 2px) can be controlled with SpectralBase.border_width.
    
    The transparency of the texture (e.g., for stuck-open shutters) is controlled
    with the SpectalBase.txtr_shading NumericProperty. In addition, a black
    background is included (to wipe out any underlying colors which could screw
    up the look of the spectra), whose transparency can be controlled with
    the SpectralBase.bg_shading NumericProperty.
    """
    sci_min = NumericProperty(0.)
    sci_max = NumericProperty(1.)
    sci_range = ReferenceListProperty(sci_min, sci_max)
    
    cmap = ObjectProperty(spectral_cmap)
    
    data = ObjectProperty(None, allownone=True, force_dispatch=True)
    
    border = VariableListProperty(0.)
    border_width = BoundedNumericProperty(2, min=0.)
    
    empty = BooleanProperty(False)
    
    txtr_height = NumericProperty(1)
    txtr_width = NumericProperty(2048)
    txtr_dims = ReferenceListProperty(txtr_width, txtr_height)
    
    txtr_shading = BoundedNumericProperty(1., min=0., max=1.)
    bg_shading = NumericProperty(1., min=0., max=1.)
    
    def on_data(self, instance, value):
        if self.data is None:
            self.txtr_dims = (2048, 1)
        else:
            self.txtr_dims = (self.data.shape[1], self.data.shape[0])
    
    def _get_default_data(self):
        data = np.tile(np.linspace(self.sci_min, self.sci_max, 
                                   num=self.txtr_width),
                       (1, self.txtr_height))
        return data.tolist()
    
    default_data = AliasProperty(_get_default_data, None, force_dispatch=True,
                                 bind=['sci_range', 'txtr_dims'])

    def _get_display_texture(self):
        txtr = Texture.create(size=self.txtr_dims, colorfmt='rgba')
        if self.empty:
            return txtr
        if self.data is None:
            data = np.array(self.default_data)
        else:
            data = self.data
        scm = self.cmap(vmin=self.sci_min, vmax=self.sci_max)
        output_grad = scm(data, bytes=True)
        fin = np.isfinite(data)
        blank = np.zeros_like(data, dtype=bool)
        blank[fin] = np.logical_or(data[fin] < self.sci_min, 
                                   data[fin] > self.sci_max)
        output_grad[blank, 3] = 0.
        txtr.blit_buffer(output_grad.tostring(), colorfmt='rgba', 
                         bufferfmt='ubyte')
        return txtr
    
    display_texture = AliasProperty(_get_display_texture, None, 
                                    bind=['sci_range', 'txtr_dims', 'data'])
    
    def _get_inset_size(self):
        base_size = self.size[:]
        for side,on in enumerate(self.border): #left, top, right, bottom
            if not on:
                continue
            wh = side % 2
            base_size[wh] -= self.border_width
        return base_size
    
    inset_size = AliasProperty(_get_inset_size, None, bind=['size', 'border', 
                                                            'border_width'])
    
    def _get_inset_pos(self):
        base_pos = self.pos[:]
        base_pos[0] += self.border_width * self.border[0]
        base_pos[1] += self.border_width * self.border[3]
        return base_pos
    
    inset_pos = AliasProperty(_get_inset_pos, None, bind=['pos', 'border',
                                                          'border_width'])
    
    def _get_border_points(self):
        points = []
        corners = [(self.x, self.y), (self.x, self.top), (self.right, self.top),
                   (self.right, self.y), (self.x, self.y)]
        for side in range(4):
            xy = [p + self.border_width / 2 for p in corners[side] + corners[side+1]]
            points.append(xy)
        return points
    
    border_points = AliasProperty(_get_border_points, None, bind=['pos', 'size',
                                                                  'border_width'])
