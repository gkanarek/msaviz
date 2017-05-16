# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 12:40:32 2017

@author: gkanarek
"""
from __future__ import absolute_import, division, print_function

import os

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import (ListProperty, DictProperty, StringProperty)

from ..msa import parse_msa_config
from ..widgets.popups import WarningPopup, MSAFilePopup, WorkDirPopup

Builder.load_string("""
<InitScreen>:
    fglist: app.fglist
    filt_grating: app.filt_grating
    workingdir: app.working_dir
    BoxLayout:
        orientation: 'vertical'
        Widget:
        Label:
            text_size: self.size
            text: 'NIRSpec MSA Spectrum View Prototype'
            halign: 'center'
            valign: 'middle'
        Widget:
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '30dp'
            Widget:
                size_hint_x: 0.2
            Label:
                text: 'Working directory:'
                text_size: self.size
                halign: 'right'
                valign: 'middle'
                size_hint_x: None
                width: '150dp'
                padding_x: 20
            TextInput:
                multiline: False
                write_tab: False
                valign: 'middle'
                text: root.workingdir
                hint_text: 'Choose a working directory'
                on_focus: if self.text and not self.focus: app.working_dir = self.text
                id: workdirinput
            Button:
                size_hint_x: None
                width: '100dp'
                text: "Choose..."
                on_release: root.dir_fileselect()
            Widget:
                size_hint_x: 0.2
        Widget:
        AnchorLayout:
            anchor_x: 'center'
            size_hint_y: None
            height: '30dp'
            Spinner:
                text: "Choose a filter/grating combination"
                values: root.fglist
                id: fgspinner
                on_text: root.fgchoice()
                size_hint_x: 0.75
        Widget:
            size_hint_y: 0.2
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '30dp'
            Widget:
                size_hint_x: 0.2
            TextInput:
                multiline: False
                write_tab: False
                valign: 'middle'
                hint_text: 'Select an MSA config file'
                on_focus: if self.text and not self.focus: root.msa_file = self.text
                id: msainput
            Button:
                size_hint_x: None
                width: '100dp'
                text: "Choose..."
                on_release: root.msa_fileselect()
            Widget:
                size_hint_x: 0.2
        Widget:
            size_hint_y: 0.2
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '30dp'
            Widget:
            Button:
                size_hint_x: None
                width: '100dp'
                text: "Parse File"
                on_release: root.msa_parse()
                canvas.before:
                    Color:
                        rgba: not root.open_shutters, bool(root.open_shutters), 0, 1
                    Rectangle:
                        size: self.size
                        pos: self.pos
            Label:
                text: "" if not root.open_shutters else "{} open shutters".format(len([x for x,y in root.open_shutters.items() if not y]))
                canvas.before:
                    Color:
                        rgba: not root.open_shutters, 0.6*bool(root.open_shutters), 0, 1
                    Rectangle:
                        size: self.size
                        pos: self.pos
            Widget:                
        Widget:
        AnchorLayout:
            anchor_x: 'center'
            size_hint_y: None
            height: '30dp'
            Button:
                text: "Show the Spectrum Display!"
                on_release: if root.go_display(): app.sm.current = 'spectral'
                size_hint_x: 0.75
""")


class InitScreen(Screen):
    fglist = ListProperty([])
    filt_grating = ListProperty([])
    open_shutters = DictProperty({})
    msa_file = StringProperty('')
    filtname = StringProperty('')
    gratname = StringProperty('')
    all_shutters = ListProperty([{},{},{},{}])
    workingdir = StringProperty('')
    
    def go_display(self):
        if not self.filtname or not self.gratname:
            popup = WarningPopup(text="Please select a filter & grating combination!")
            popup.open()
            return False
        if not self.msa_file:
            popup = WarningPopup(text="Please choose an MSA config file!")
            popup.open()
            return False
        if not self.open_shutters:
            popup = WarningPopup(text="Please parse the MSA config file!")
            popup.open()
            return False
        return True
        
    def fgchoice(self):
        if not (self.ids.fgspinner.text in self.fglist):
            return
        fg = self.fglist.index(self.ids.fgspinner.text)
        self.filtname, self.gratname = self.filt_grating[fg]
    
    def msa_fileselect(self):
        popup = MSAFilePopup()
        popup.bind(on_dismiss=self.set_msafile)
        popup.open()
    
    def dir_fileselect(self):
        popup = WorkDirPopup(suggested_dir=self.workingdir)
        popup.bind(on_dismiss=self.set_workingdir)
        popup.open()
    
    def set_msafile(self, instance):
        if instance.canceled:
            return
        self.msa_file = os.path.join(instance.selected_path, 
                                     instance.selected_file)
        self.ids.msainput.text = self.msa_file
        return False
    
    def set_workingdir(self, instance):
        if instance.canceled:
            return
        self.workingdir = os.path.join(instance.selected_path, 
                                     instance.selected_file)
        self.ids.workdirinput.text = self.workingdir
        return False
    
    def on_msa_file(self, instance, value):
        self.open_shutters = {}
        self.all_shutters = [{},{},{},{}]
    
    def msa_parse(self):
        if not self.msa_file:
            popup = WarningPopup(text="Please choose an MSA config file (must be a csv file)!")
            popup.open()
            return
        try:
            self.open_shutters = parse_msa_config(self.msa_file)
            alls = parse_msa_config(self.msa_file, return_all=True)
            tmp = [{}, {}, {}, {}]
            for q,i,j in alls:
                tmp[q][(i,j)] = alls[(q,i,j)]
            self.all_shutters = tmp
        except (OSError, EOFError):
            popup = WarningPopup(text="Error when parsing MSA config file!\nPlease verify file name and format!")
            popup.open()
            return