# -*- coding: utf-8 -*-
"""
Created on Tue Nov  1 14:42:15 2016

@author: gkanarek
"""
from __future__ import absolute_import, division, print_function

import os

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import (ListProperty, NumericProperty, StringProperty,
                             AliasProperty, DictProperty, ObjectProperty,
                             BooleanProperty)
from kivy.core.window import Window
from kivy.metrics import sp

from .screens import InitScreen, SpectrumScreen, ShutterScreen

kv = """
ScreenManager:
    InitScreen:
        name: 'init'
        id: initscreen
    SpectrumScreen:
        name: 'spectral'
        id: specscreen
    ShutterScreen:
        name: 'shutters'
        id: shutterscreen
"""

home_dir = os.path.dirname(os.path.realpath(__file__))

class WaveTool(App):
    homedir = StringProperty(home_dir)
    working_dir = StringProperty(os.path.join(home_dir, 'test'))
    filt_grating = ListProperty([('clear', 'prism'), #--> prism not supported yet
                                 ('f070lp', 'g140h'),
                                 ('f070lp', 'g140m'),
                                 ('f100lp', 'g140h'),
                                 ('f100lp', 'g140m'),
                                 ('f170lp', 'g235h'),
                                 ('f170lp', 'g235m'),
                                 ('f290lp', 'g395h'),
                                 ('f290lp', 'g395m')])
    fglist = ListProperty([])
    msa_file = StringProperty('')
    open_shutters = DictProperty({})
    all_shutters = ListProperty([{},{},{},{}])
    update_shutters = BooleanProperty(False)
    filtname = StringProperty('')
    gratname = StringProperty('')
    initial_size = ListProperty([])
    labelsize = NumericProperty(sp(30))
    sm = ObjectProperty(None)
    selected_shutters = ListProperty([[],[],[],[]])
    
    def build(self):
        self.title = "MSA Spectral Visualization Tool"
        self.icon = os.path.join('data', 'nirspec.png')
        self.fglist = ["{}/{}".format(f,g) for f,g in self.filt_grating]
        import pdb, traceback, sys
        try:
            self.sm = Builder.load_string(kv)
        except Exception as e:
            t, value, tb = sys.exc_info()
            traceback.print_exc()
            pdb.post_mortem(tb)
        self.sm.ids.initscreen.bind(msa_file=self.setter('msa_file'),
                                    open_shutters=self.setter('open_shutters'),
                                    filtname=self.setter('filtname'),
                                    gratname=self.setter('gratname'),
                                    all_shutters=self.setter('all_shutters'),
                                    workingdir=self.setter('working_dir'))
        self.bind(selected_shutters=self.sm.ids.shutterscreen.setter('selected'))
        self.sm.current = 'init'
        self.initial_size = Window.size
        Window.bind(on_resize=self.resize)
        return self.sm
    
    def on_all_shutters(self, instance, value):
        self.update_shutters = not self.update_shutters
    
    def update_selected(self, quadrant, selected):
        tmp = [x[:] for x in self.selected_shutters]
        new = list(set(selected) - set(tmp[quadrant]))
        if new:
            self.sm.ids.shutterscreen.recent_select = [quadrant+1] + [x+1 for x in new[0]]
        else:
            self.sm.ids.shutterscreen.recent_select = []
        tmp[quadrant] = selected
        self.selected_shutters = tmp
    
    def resize(self, instance, width, height):
        dw = width / self.initial_size[0]
        dh = height / self.initial_size[1]
        scale = min(dw, dh)
        self.labelsize = sp(30 * scale)
    
    def _get_fg(self):
        return '{}/{}'.format(self.filtname, self.gratname)
    fg = AliasProperty(_get_fg, None, bind=['filtname', 'gratname'])
    
if __name__ == "__main__":
    WaveTool().run()