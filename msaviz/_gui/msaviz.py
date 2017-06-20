# -*- coding: utf-8 -*-
"""
Created on Tue May 16 12:37:06 2017

@author: gkanarek
"""

from os import path
from threading import Thread

home_dir = path.dirname(path.realpath(__file__))
base_dir = path.realpath(path.join(home_dir, '..'))

from kivy.config import Config
Config.setall('kivy', {'exit_on_escape':0, 'desktop':1, 'log_enable': 1,
                       'log_dir': path.join(base_dir, 'logs'), 
                       'log_level': 'debug',
                       'window_icon': path.join(base_dir, 'data', 
                                                'nirspec.iconset',
                                                'icon_512x512.png')})

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import (ListProperty, NumericProperty, StringProperty,
                             AliasProperty, ObjectProperty, BooleanProperty)
from kivy.core.window import Window
from kivy.metrics import sp
from kivy.clock import Clock

from .screens import InitScreen, SpectrumScreen, ShutterScreen
from ..msa import MSAConfig
from .widgets.popups import WaitPopup

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



class WaveTool(App):
    homedir = StringProperty(base_dir)
    working_dir = StringProperty(path.join(base_dir, 'test'))
    filt_grating = ListProperty([('clear', 'prism'),
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
    all_shutters = ListProperty([{},{},{},{}])
    update_shutters = BooleanProperty(False)
    filtname = StringProperty('')
    gratname = StringProperty('')
    initial_size = ListProperty([])
    labelsize = NumericProperty(sp(30))
    sm = ObjectProperty(None)
    selected_shutters = ListProperty([[],[],[],[]])
    msa = ObjectProperty(None, allownone=True)
    waiting = ObjectProperty(None, allownone=True)
    
    def on_msa_file(self, instance, value):
        self.wrapper()
    
    def on_fg(self, instance, value):
        self.wrapper()
        
    def wrapper(self):
        if not self.msa_file or not self.filtname or not self.gratname:
            return
        
        if (self.filtname, self.gratname) not in self.filt_grating:
            return
        
        self.waiting = WaitPopup(num_shutters=0,
                                 current_shutter=0)
        self.waiting.open()
        
        t = Thread(target=self.init_msa)
        t.start()
    
    def init_msa(self):
        msa = MSAConfig(self.filtname, self.gratname, self.msa_file)
        Clock.schedule_once(lambda dt: self.proceed(msa), 0.1)
    
    def proceed(self, msa):
        """
        Dismiss the popup to unblock the app.
        """
        self.msa = msa
        
        if self.waiting:
            self.waiting.dismiss()
            self.waiting = None
        
    
    def build(self):
        self.title = "MSA Spectral Visualization Tool"
        self.icon = path.join(base_dir, 'data', 'nirspec.png')
        self.fglist = ["{}/{}".format(f,g) for f,g in self.filt_grating]
        WaitPopup() #to pre-load animation
        import pdb, traceback, sys
        try:
            self.sm = Builder.load_string(kv)
        except Exception as e:
            t, value, tb = sys.exc_info()
            traceback.print_exc()
            pdb.post_mortem(tb)
        self.sm.ids.initscreen.bind(msa_file=self.setter('msa_file'),
                                    #open_shutters=self.setter('open_shutters'),
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