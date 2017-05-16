# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 10:07:00 2017

@author: gkanarek
"""

from __future__ import absolute_import, division, print_function

import os

import numpy as np
from astropy.table import QTable
import astropy.units as u

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.properties import (AliasProperty, StringProperty, ListProperty,
                             NumericProperty, ReferenceListProperty,
                             ObjectProperty)

from ..msa import MSA
from ..widgets.popups import MSAFilePopup
from ..widgets.spectral import SpectralBase
from ..widgets import FloatStencil, LockScatter
from ..spectrumview import SpectrumLayout

Builder.load_string("""#:import os os
#:import np numpy

<CBarMark>:
    valign: 'middle'
    halign: ['left','right'][self.mark > 1]
    text_size: self.size
    mark_x: self.x + self.width * (self.mark > 1)
    text: ' {:5.3f}'.format(self.wave)
    canvas:
        Color:
            rgba: 1, 1, 1, 1
        Line:
            points: self.mark_x, self.y, self.mark_x, self.y+self.height
            width: 1.1 * (1 + int(self.mark in [0,3]))

<Colorbar>:
    orientation: 'vertical'
    size_hint_y: None
    height: '50dp'
    data: bar.data
    SpectralBase:
        txtr_dims: 2048, 1
        border: 1
        sci_range: root.sci_range
        id: bar
    BoxLayout:
        orientation: 'horizontal'
        CBarMark:
            mark: 0
            wave: root.wave_labels[self.mark]
        Widget:
        CBarMark:
            mark: 1
            wave: root.wave_labels[self.mark]
        CBarMark:
            mark: 2
            wave: root.wave_labels[self.mark]
        Widget:
        CBarMark:
            mark: 3
            wave: root.wave_labels[self.mark]

<SpectrumScreen>:
    filtname: app.filtname
    gratname: app.gratname
    msafile: os.path.basename(app.msa_file)
    filt_grating: app.filt_grating
    BoxLayout:
        orientation: 'vertical'
        FloatStencil:
            LockScatter:
                size_hint: 1., 1.
                id: dpane
                SpectrumLayout:
                    id: detector
                    size_hint: 1., 1.
                    open_shutters: app.open_shutters
                    msa: root.msa
        Colorbar:
            msa: root.msa
            wave_labels: root.wave_labels
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '30dp'
            canvas.after:
                Color:
                    rgba: 1, 1, 1, 1
                Line:
                    rectangle: self.pos + self.size
                    width: 1.1
            Label:
                text: root.msafile
                halign: 'center'
                valign: 'middle'
                font_size: '12pt'
            Button:
                size_hint_x: None
                width: '80dp'
                text: 'Export...'
                on_release: root.export_dialog()
                font_size: '12pt'
            Button:
                size_hint_x: None
                width: '80dp'
                text: 'Save...'
                on_release: root.save_dialog()
                font_size: '12pt'
                disabled: dpane.scale > 1.0
            Button:
                size_hint_x: None
                width: '80dp'
                text: 'Shutters...'
                on_release: app.sm.current = 'shutters'
                font_size: '12pt'
            Button:
                size_hint_x: None
                width: '80dp'
                text: 'Back'
                on_release: app.sm.current = 'init'
                font_size: '12pt'
""")

class CBarMark(Label):
    mark = NumericProperty(0)
    wave = NumericProperty(0.)

class Colorbar(BoxLayout):
    wave_labels = ListProperty([0.]*4)
    msa = ObjectProperty(None, allownone=True)
    
    sci_min = NumericProperty(0.)
    sci_max = NumericProperty(1.)
    sci_range = ReferenceListProperty(sci_min, sci_max)
    
    data = ObjectProperty(None, allownone=True, force_dispatch=True)
    
    def on_msa(self, instance, value):
        if self.msa:
            self.sci_range = self.msa.sci_range


class SpectrumScreen(Screen):
    filtname = StringProperty('')
    gratname = StringProperty('')
    msafile = StringProperty('')
    filt_grating = ListProperty([])
    
    def _get_msa(self):
        if (self.filtname, self.gratname) not in self.filt_grating:
            return None
        return MSA(self.filtname, self.gratname)
    
    msa = AliasProperty(_get_msa, None, bind=['filtname','gratname'])
    
    def on_pre_enter(self):
        self.ids.dpane.transform_with_touch(False)
    
    def on_leave(self):
        self.ids.dpane.scale = 1.0
        self.ids.dpane.transform_with_touch(False)
    
    def _get_wavelabels(self):
        if self.msa is None:
            return [0.0] * 4
        l0, l1 = self.msa.sci_range
        dl = l1 - l0
        return [l0, l0+dl/3., l1-dl/3., l1]
    
    wave_labels = AliasProperty(_get_wavelabels, None, bind=['msa'])
    
    def save_dialog(self):
        suggested, ext = os.path.splitext(self.msafile)
        suggested += '_'+self.filtname+'_'+self.gratname+'_spectral.png'
        popup = MSAFilePopup(title="Save...", allowed_ext=["*.png"], 
                             suggested_file=suggested)
        popup.bind(on_dismiss=self.save_png)
        popup.open()
    
    def export_dialog(self):
        suggested, ext = os.path.splitext(self.msafile)
        suggested += '_'+self.filtname+'_'+self.gratname+'_wavelengths.txt'
        popup = MSAFilePopup(title="Save...", allowed_ext=["*.txt"], 
                             suggested_file=suggested)
        popup.bind(on_dismiss=self.export_txt)
        popup.open()
    
    def export_txt(self, instance):
        if instance.canceled:
            return
        txt_out = os.path.join(instance.selected_path, instance.selected_file)
        shutter_limits = self.ids.detector.shutter_limits
        q,i,j = zip(*sorted(shutter_limits.keys()))
        nshutter = len(shutter_limits)
        limits = np.zeros((nshutter, 4), dtype=float)
        for row, qij in enumerate(zip(q,i,j)):
            limits[row] = shutter_limits[qij]
        limits = limits * u.micron
        lo1, hi1, lo2, hi2 = limits.T
        
        shutters = QTable([q,i,j,lo1, hi1, lo2, hi2], names=["Quadrant", 
                                                             "Column", "Row", 
                                                             "NRS1-min",
                                                             "NRS1-max", 
                                                             "NRS2-min", 
                                                             "NRS2-max"],
                          meta={"MSA Config File":self.msafile,
                                "Open shutters": len(shutter_limits),
                                "Filter": self.filtname,
                                "Grating": self.gratname},
                          masked=True, dtype=('i4','i4','i4','f8','f8','f8','f8'))
            
        shutters['NRS1-min'].info.format = '6.4f'
        shutters['NRS1-max'].info.format = '6.4f'
        shutters['NRS2-min'].info.format = '6.4f'
        shutters['NRS2-max'].info.format = '6.4f'
        
        shutters['NRS1-min'].mask = ~np.isfinite(lo1)
        shutters['NRS1-max'].mask = ~np.isfinite(hi1)
        shutters['NRS2-min'].mask = ~np.isfinite(lo2)
        shutters['NRS2-max'].mask = ~np.isfinite(hi2)
        
        with open(txt_out, 'w') as f:
            #print out the header
            f.write("## MSA Config File: {}\n".format(self.msafile))
            f.write("## {} open shutters\n".format(len(shutter_limits)))
            f.write("## Filter: {}\n".format(self.filtname))
            f.write("## Grating: {}\n".format(self.gratname))
            f.write("\n")
            shutters.write(f, format='ascii.fixed_width_two_line')
        
    
    def save_png(self, instance):
        if instance.canceled:
            return
        png_out = os.path.join(instance.selected_path, instance.selected_file)
        filebase, ext = os.path.splitext(png_out)
        png_out = filebase + '.png'
        self.ids.dpane.export_to_png(png_out)