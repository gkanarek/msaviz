# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 10:12:50 2017

@author: gkanarek
"""

from __future__ import absolute_import, division, print_function

import os

from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.properties import (StringProperty, BooleanProperty, ListProperty,
                             NumericProperty, AliasProperty)
from kivy.clock import Clock


Builder.load_string("""#:import os os
#:import FileBrowser kivy.garden.filebrowser

<WarningPopup>:
    title: 'Oops!'
    auto_dismiss: True
    size_hint: 0.4, 0.4
    Label:
        text: root.text
        halign: 'center'
        valign: 'middle'
        text_size: self.size

<FindShutterPopup>:
    title: "Find an MSA shutter"
    size_hint: 1, 1
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'horizontal'
            Label:
                text: "Currently selected shutters:"
                text_size: self.size
                halign: "center"
                valign: "middle"
                size_hint_y: None
                height: '30dp'
            Spinner:
                text: "No shutters selected" if not self.values else "Choose a shutter"
                values: root.selected_shutters
                size_hint_y: None
                height: '30dp'
                on_text: root.choose_shutter(self.values.index(self.text))
        Widget:
        GridLayout:
            cols: 3
            size_hint_y: None
            height: self.minimum_height
            spacing: '10dp', '30dp' 
            Label:
                text: "Quadrant:"
                text_size: self.size
                halign: "right"
                valign: "middle"
                size_hint_y: None
                height: '30dp'
            TextInput:
                hint_text: "Enter a number from 1 to 4"
                multiline: False
                size_hint_y: None
                height: '30dp'
                on_focus: if not self.focus: root.check_quadrant()
                id: qtext
            Label:
                text: root.qerr
                text_size: self.size
                halign: "center"
                valign: "middle"
                size_hint_y: None
                height: '30dp'
                color: 1, 0, 0, 1
            Label:
                text: "Column:"
                text_size: self.size
                halign: "right"
                valign: "middle"
                size_hint_y: None
                height: '30dp'
            TextInput:
                hint_text: "Enter a number from 1 to 365"
                multiline: False
                size_hint_y: None
                height: '30dp'
                on_focus: if not self.focus: root.check_column()
                id: itext
            Label:
                text: root.ierr
                text_size: self.size
                halign: "center"
                valign: "middle"
                size_hint_y: None
                height: '30dp'
                color: 1, 0, 0, 1
            Label:
                text: "Row:"
                text_size: self.size
                halign: "right"
                valign: "middle"
                size_hint_y: None
                height: '30dp'
            TextInput:
                hint_text: "Enter a number from 1 to 171"
                multiline: False
                size_hint_y: None
                height: '30dp'
                on_focus: if not self.focus: root.check_row()
                id: jtext
            Label:
                text: root.jerr
                text_size: self.size
                halign: "center"
                valign: "middle"
                size_hint_y: None
                height: '30dp'
                color: 1, 0, 0, 1
        Widget:
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '30dp'
            Button:
                text: "Find this shutter"
                on_release: root.done()
            Button:
                text: "Cancel"
                on_release: root.cancel()

<MSAFilePopup>:
    title: "Choose an MSA Config File"
    size_hint: 1, 1
    auto_dismiss: False
    FileBrowser:
        id: fbrowser
        path: app.working_dir
        on_success: root.select()
        on_canceled: root.cancel()
        filters: root.allowed_ext

<WorkDirPopup>:
    title: "Choose a working directory"
    size_hint: 1, 1
    auto_dismiss: False
    FileBrowser:
        id: fbrowser
        path: os.path.join(app.homedir, '..', 'test')
        on_success: root.select()
        on_canceled: root.cancel()
        dirselect: True
        filters: [root.isdir]

<WaitPopup>:
    title: 'Please Wait...'
    auto_dismiss: False
    size_hint_y: 0.8
    BoxLayout:
        orientation: 'vertical'
        Image:
            size_hint_y: None
            height: 0.5*self.width
            source: os.path.join(app.homedir,'..','data','prism.zip')
            anim_delay: 0.05
            allow_stretch: True
            id: prism
        Widget:
        ProgressBar:
            max: root.num_shutters
            value: root.current_shutter
        Widget:
""")

class FindShutterPopup(Popup):
    selected = ListProperty([])
    qerr = StringProperty('')
    ierr = StringProperty('')
    jerr = StringProperty('')
    chosen = ListProperty([])
    quad = NumericProperty(0)
    row = NumericProperty(0)
    col = NumericProperty(0)
    canceled = BooleanProperty(False)
    
    def _get_selected_shutters(self):
        return ['Q {}, I {}, J {}'.format(*qij) for qij in self.selected]
    
    selected_shutters = AliasProperty(_get_selected_shutters, None, bind=['selected'])
    
    def choose_shutter(self, idx):
        self.quad, self.col, self.row = self.selected[idx]
        self.qerr = ""
        self.ids.qtext.text = str(self.quad)
        self.ierr = ""
        self.ids.itext.text = str(self.col)
        self.jerr = ""
        self.ids.jtext.text = str(self.row)
    
    def check_quadrant(self):
        try:
            self.quad = int(self.ids.qtext.text)
        except ValueError:
            self.quad = 0

        if self.quad < 1 or self.quad > 4:
            self.qerr = "Invalid quadrant"
            self.ids.qtext.text = ""
            self.quad = 0
        else:
            self.qerr = ""
    
    def check_column(self):
        try:
            self.col = int(self.ids.itext.text)
        except ValueError:
            self.col = 0

        if self.col < 1 or self.col > 365:
            self.ierr = "Invalid column"
            self.ids.itext.text = ""
            self.col = 0
        else:
            self.ierr = ""

    def check_row(self):
        try:
            self.row = int(self.ids.jtext.text)
        except ValueError:
            self.row = 0

        if self.row < 1 or self.row > 171:
            self.jerr = "Invalid row"
            self.ids.jtext.text = ""
            self.row = 0
        else:
            self.jerr = ""
    
    def done(self):
        self.quad = self.quad - 1
        self.col = self.col - 1
        self.row = self.row - 1
        self.canceled = False
        self.dismiss()
    
    def cancel(self):
        self.canceled = True
        self.quad = self.row = self.col = 0
        self.dismiss()

class MSAFilePopup(Popup):
    selected_file = StringProperty('')
    selected_path = StringProperty('')
    canceled = BooleanProperty(False)
    allowed_ext = ListProperty(['*.csv'])
    suggested_file = StringProperty('')
    
    def on_open(self):
        self.ids.fbrowser.ids.file_text.text = self.suggested_file
    
    def select(self):
        self.selected_file = self.ids.fbrowser.filename
        self.selected_path = self.ids.fbrowser.path
        self.dismiss()
        
    def cancel(self):
        self.selected_file = ''
        self.selected_path = ''
        self.canceled = True
        self.dismiss()

class WorkDirPopup(Popup):
    selected_dir = StringProperty('')
    selected_path = StringProperty('')
    canceled = BooleanProperty(False)
    suggested_dir = StringProperty('')
    
    def on_open(self):
        self.ids.fbrowser.ids.file_text.text = self.suggested_dir
    
    def select(self):
        self.selected_file = self.ids.fbrowser.filename
        self.selected_path = self.ids.fbrowser.path
        self.dismiss()
        
    def isdir(self, directory, filename):
        return os.path.isdir(os.path.join(directory, filename))
        
    def cancel(self):
        self.selected_file = ''
        self.selected_path = ''
        self.canceled = True
        self.dismiss()

class WarningPopup(Popup):
    text = StringProperty('')

class WaitPopup(Popup):
    current_shutter = NumericProperty(0)
    num_shutters = NumericProperty(0)
    
    def __init__(self, **kw):
        super(WaitPopup, self).__init__(**kw)
        Clock.schedule_once(self.set_height, 0.1)
    
    def set_height(self, dt):
        self.ids.prism.height = 0.5 * self.ids.prism.width