# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 10:07:00 2017

@author: gkanarek
"""

from __future__ import absolute_import, division, print_function

import os
import numpy as np

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.properties import (AliasProperty, StringProperty, ListProperty,
                             NumericProperty, ReferenceListProperty,
                             ObjectProperty)

from ..widgets.popups import MSAFilePopup, WavelengthPopup
from ..widgets.spectral import SpectralBase
from ..widgets import FloatStencil, LockScatter
from ..spectrumview import SpectrumLayout

Builder.load_string("""#:import os os
#:import np numpy

<CBarMark>:
    valign: 'middle'
    halign: 'center'
    text_size: self.size
    text: '{}'.format(round(self.wave, 2))
    size_hint_x: None
    width: '50dp'

<Colorbar>:
    orientation: 'vertical'
    size_hint_y: None
    height: '50dp'
    data: bar.data
    canvas.after:
        Color:
            rgba: 1, 1, 1, 1
        Line:
            rectangle: self.x + 0.05 * self.width, self.y + 0.5 * self.height, self.width * 0.9, self.height * 0.5
            width: 1.1
        Line:
            points: self._tick_vert
            width: 1.1
    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'center'
        SpectralBase:
            txtr_dims: 2048, 1
            border: 0.
            sci_range: root.sci_range
            id: bar
            size_hint_x: 0.9
    FloatLayout:
        orientation: 'horizontal'
        size_hint_x: 
        id: cblabels

<SpectrumScreen>:
    filtname: app.filtname
    gratname: app.gratname
    msafile: os.path.basename(app.msa_file)
    msa: app.msa
    filt_grating: app.filt_grating
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'vertical'
            id: specpane
            FloatStencil:
                LockScatter:
                    id: dpane
                    size_hint: 1., 1.
                    SpectrumLayout:
                        id: detector
                        size_hint: 1., 1.
                        #open_shutters: app.msa.open_shutters
                        msa: root.msa
            AnchorLayout:
                anchor_x: 'center'
                size_hint_y: None
                height: '50dp'
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
                width: '150dp'
                text: 'Check Wavelength'
                on_release: root.wavelength_dialog()
                font_size: '12pt'
            Button:
                size_hint_x: None
                width: '100dp'
                text: 'Export...'
                on_release: root.export_dialog()
                font_size: '12pt'
            Button:
                size_hint_x: None
                width: '100dp'
                text: 'Save...'
                on_release: root.save_dialog()
                font_size: '12pt'
                disabled: dpane.scale > 1.0
            Button:
                size_hint_x: None
                width: '100dp'
                text: 'Shutters...'
                on_release: app.change_screen('shutters', 'left')
                font_size: '12pt'
            Button:
                size_hint_x: None
                width: '100dp'
                text: 'Back'
                on_release: app.change_screen('init', 'right')
                font_size: '12pt'
""")

class CBarMark(Label):
    wave = NumericProperty(0.)
    
class Colorbar(BoxLayout):
    wave_labels = ListProperty([0.]*5)
    msa = ObjectProperty(None, allownone=True)
    
    sci_min = NumericProperty(0.)
    sci_max = NumericProperty(1.)
    sci_range = ReferenceListProperty(sci_min, sci_max)
    
    data = ObjectProperty(None, allownone=True, force_dispatch=True)
    
    _tick_vert = ListProperty([])
    #_tick_idx = ListProperty([])
    
    def _get_dlims(self):
        if self.msa is None:
            return [0.0] * 2
        
        l0, l1 = self.msa.sci_range
        l0 = np.floor(l0*10.) / 10.
        l1 = np.ceil(l1*10.) / 10.
        return [float(l0), float(l1)]
    
    dlims = AliasProperty(_get_dlims, None, bind=['msa'])
    
    def convert_wave(self, wave):
        l0, l1 = self.dlims
        #sci_min is at x/w = 0.05
        #sci_max is at x/w = 0.95
        norm = (wave - l0) / (l1 - l0)
        return norm * 0.9 + 0.05
    
    def on_msa(self, instance, value):
        if self.msa:
            self.sci_range = self.msa.sci_range
            l0, l1 = self.dlims
            self.ids.bar.data = np.tile(np.linspace(l0, l1, 
                                            num=self.ids.bar.txtr_width), 
                                            (1, self.ids.bar.txtr_height))
            self.update_ticks()
    
    def on_size(self, instance, value):
        self.update_ticks()
    
    def on_pos(self, instance, value):
        self.update_ticks()
            
    def update_ticks(self):
        if not self.msa:
            return
        
        l0, l1 = self.dlims
        
        #update colorbar ticks & labels
        self.ids.cblabels.clear_widgets()
        vert = []
        #idx = []
        
        #calculate tick spacing
        dlim = round(l1 - l0, 1)
        step = 0.1
        major = 5
        ntick = int(dlim / step)
        if ntick > 20:
            step = 0.2
            ntick = int(dlim / step)
            if ntick > 20:
                step = 0.5
                major = 2
                ntick = int(dlim / step)
        y = self.ids.bar.y
        major_y = self.top
        minor_y = (y + major_y) / 2
        current = l0
        for t in range(ntick+1):
            x = float(self.convert_wave(current))
            tx = x * self.width + self.x
            lo = [tx, y]
            if t % major == 0: #major tick
                label = CBarMark(wave=float(current), pos_hint={'center_x': x,
                                                                'center_y': 0.5})
                self.ids.cblabels.add_widget(label)
                hi = [tx, major_y]
            else: #minor tick
                hi = [tx, minor_y]
            vert.extend(lo + hi + lo)
            current += step
        
        self._tick_vert = vert
        


class SpectrumScreen(Screen):
    filtname = StringProperty('')
    gratname = StringProperty('')
    msafile = StringProperty('')
    filt_grating = ListProperty([])
    msa = ObjectProperty(None, allownone=True)
    
    def on_pre_enter(self):
        self.ids.dpane.transform_with_touch(False)
    
    def on_leave(self):
        self.ids.dpane.scale = 1.0
        self.ids.dpane.transform_with_touch(False)
    
    def _get_wavelabels(self):
        if self.msa is None:
            return [0.0] * 5
        l0, l1 = self.msa.sci_range
        l0 = np.floor(l0*10.) / 10.
        l1 = np.ceil(l1*10.) / 10.
        return np.linspace(l0, l1, num=5).tolist()
    
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
        self.msa.write_wavelength_table(txt_out)
        
    
    def save_png(self, instance):
        if instance.canceled:
            return
        png_out = os.path.join(instance.selected_path, instance.selected_file)
        filebase, ext = os.path.splitext(png_out)
        png_out = filebase + '.png'
        self.ids.specpane.export_to_png(png_out)
    
    def wavelength_dialog(self):
        popup = WavelengthPopup()
        popup.open()