# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 10:12:50 2017

@author: gkanarek
"""

from __future__ import absolute_import, division, print_function

import os

from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.properties import (StringProperty, BooleanProperty, ListProperty,
                             NumericProperty, AliasProperty, ObjectProperty)
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

<WaveTableCell>:
    size_hint_x: None
    width: '150dp'
    markup: True
    font_size: '20sp' if self.header else '15sp'
    text_size: self.size
    halign: 'left'
    valign: 'middle'

<WaveTableHeader>:
    rows: 1
    spacing: '10dp', 0
    padding: '10dp', 0
    size_hint: None, None
    height: '30dp'
    width: self.minimum_width
    canvas.before:
        Color:
            rgba: 1, 1, 1, bool(self.colnames)
        Line:
            points: [self.x, self.y, self.right, self.y]
            width: 2

<WaveTableEntry>:
    rows: 1
    spacing: '10dp', 0
    padding: '10dp', 0
    size_hint: None, None
    height: '30dp'
    width: self.minimum_width

<WavelengthPopup>:
    title: "Check wavelengths against the detector boundaries"
    size_hint: 1, 1
    auto_dismiss: False
    fname: app.filtname
    dname: app.gratname
    msafile: os.path.basename(app.msa_file)
    msa: app.msa
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '30dp'
            Label:
                text: "Enter a wavelength to check:"
                text_size: self.size
                halign: "center"
                valign: "middle"
            TextInput:
                hint_text: "Wavelength"
                text: ""
                multiline: False
                id: wtext
            Label:
                text: "microns"
                text_size: self.size
                halign: "left"
                valign: "middle"
                size_hint_x: None
                width: '80dp'
            Button:
                text: "Submit"
                on_release: root.add_wavelength()
                font_size: '12pt'
                size_hint_x: None
                width: '80dp'
        ScrollView:
            GridLayout:
                cols: 1
                id: wavelist
                size_hint: None, None
                size: self.minimum_size
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '30dp'
            Button:
                text: "Save to file"
                on_release: root.save_table()
            Button:
                text: "Done"
                on_release: root.done()
                

<FindShutterPopup>:
    title: "Find an MSA shutter"
    size_hint: 1, 1
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '30dp'
            Label:
                text: "Currently selected shutters:"
                text_size: self.size
                halign: "center"
                valign: "middle"
            Spinner:
                text: "No shutters selected" if not self.values else "Choose a shutter"
                values: root.selected_shutters
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
        path: os.path.join(app.homedir, 'test')
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
            source: os.path.join(app.homedir,'data','prism.zip')
            anim_delay: 0.05
            allow_stretch: True
            id: prism
        Widget:
        ProgressBar:
            max: root.num_shutters
            value: root.current_shutter
        Widget:
""")
    
class WaveTableCell(Label):
    header = BooleanProperty(False)

class WaveTableHeader(GridLayout):
    colnames = ListProperty([])
    
    def on_colnames(self, instance, value):
        if not self.colnames:
            return
        self.clear_widgets()
        
        shutter = WaveTableCell(text='[b]Shutter[/b]', header=True)
        self.add_widget(shutter)
        
        for col in sorted(self.colnames):
            if col in ['Quadrant', 'Column', 'Row']:
                continue
            cell = WaveTableCell(text='[b]{}[/b]'.format(col), header=True)
            self.add_widget(cell)
    
class WaveTableEntry(GridLayout):
    rownum = NumericProperty(0)
    table = ObjectProperty(None, allownone=True, force_dispatch=True)
    
    def on_table(self, instance, value):
        self.update_data()
    
    def on_rownum(self, instance, value):
        self.update_data()
    
    def update_data(self):
        if self.table is None:
            return
        self.clear_widgets()
        
        out = [("In gap", [146/255., 0, 0, 1]), 
               ("On NRS1", [182/255., 219/255., 1, 1]),
               ("On NRS2", [182/255., 219/255., 1, 1]), 
               ("NRS1 edge", [1, 182/255., 119/255., 1]),
               ("NRS2 edge", [1, 182/255., 119/255., 1]),
               ("Too high", [146/255., 0, 0, 1]),
               ("Too low", [146/255., 0, 0, 1])]
        
        row = self.table[self.rownum]
        
        shutter = WaveTableCell(text='Q {}, I {}, J {}'.format(row['Quadrant'], 
                                                               row['Column'],
                                                               row['Row']),
                                header=False)
        self.add_widget(shutter)
        
        for col in row.colnames:
            if col in ['Quadrant', 'Column', 'Row']:
                continue
            msg, color = out[row[col]]
            cell = WaveTableCell(text=msg, color=color, header=False)
            self.add_widget(cell)

class WavelengthPopup(Popup):
    table = ObjectProperty(None, allownone=True, force_dispatch=True)
    wavelengths = ListProperty([])
    msa = ObjectProperty(None, allownone=True)
    msafile = StringProperty("")
    fname = StringProperty("")
    dname = StringProperty("")
    header = ObjectProperty(None)
    entries = ListProperty([])
    
    def __init__(self, **kw):
        super(WavelengthPopup, self).__init__(**kw)
        self.header = WaveTableHeader()
        self.ids.wavelist.add_widget(self.header)
        
        for i in range(self.msa.nopen):
            entry = WaveTableEntry(rownum=i)
            self.entries.append(entry)
            self.ids.wavelist.add_widget(entry)
    
    def add_wavelength(self):
        if self.msa is None:
            return
        
        try:
            wave = float(self.ids.wtext.text)
        except ValueError:
            self.ids.wtext.text = ""
            return
        
        if wave < self.msa.sci_range[0] or wave > self.msa.sci_range[1]:
            self.ids.wtext.text = ""
            return
        
        self.ids.wtext.text = ""
        
        self.wavelengths.append(wave)
        self.table = self.msa.verify_wavelength(self.wavelengths, 
                                                verbose=False)
        
        self.header.colnames = self.table.colnames
        for entry in self.entries:
            entry.table = self.table
    
    def save_table(self):
        if not self.wavelengths or self.table is None:
            return
        suggested, ext = os.path.splitext(self.msafile)
        suggested += '_'+self.fname+'_'+self.dname+'_wavecheck.txt'
        popup = MSAFilePopup(title="Save...", allowed_ext=["*.txt"], 
                             suggested_file=suggested)
        popup.bind(on_dismiss=self.write_table)
        popup.open()
    
    def write_table(self, instance):
        if instance.canceled:
            return
        txt_out = os.path.join(instance.selected_path, instance.selected_file)
        self.table.write(txt_out, format='ascii.fixed_width_two_line')
    
    def done(self):
        self.dismiss()

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