# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:05:22 2017

@author: gkanarek
"""

from __future__ import absolute_import, division, print_function

#horizontal MSA gap 22"
#vertical MSA gap 36"

from threading import Thread

from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.graphics import InstructionGroup, Color, Rectangle
from kivy.clock import Clock
from kivy.properties import (ObjectProperty, NumericProperty, BooleanProperty,
                             DictProperty, ReferenceListProperty, AliasProperty,
                             ListProperty)

from .widgets.popups import WaitPopup
from .widgets.spectral import SpectralBase

import numpy as np

Builder.load_string("""
<SpectralQuadrant>:
    empty: False
    size_hint: 1., 1.
    pos_hint: {'x': 0., 'y': 0.}
    bg_shading: 0.95 - int(self.stuck)
    txtr_shading: 1-0.5*int(self.stuck)
    border: [1, 1 - (self.quadrant % 2), 1, self.quadrant % 2]
    border_width: 1.1
    
<SpectralZone>:
    anchor_x: 'center'
    anchor_y: 'center'
    size_hint: self.qsizehint
    pos_hint: self.qposhint
    SpectralQuadrant:
        id: chosen
        quadrant: root.quadrant
        sci_range: root.sci_range
        data: root.data
    SpectralQuadrant:
        quadrant: root.quadrant
        sci_range: root.sci_range
        data: root.stuck_data
        stuck: True

<OutsideLabel>:
    halign: 'center'
    text_size: self.size
    color: 0.7, 0.7, 0.7, 1.
    padding_y: 5
    font_size: app.labelsize
    size_hint: self.olsizehint
    pos_hint: self.olposhint
    valign: ['bottom','top'][self.quadrant % 2]
    text: "NRS" + "12"[1 - self.quadrant // 2]

<SpectrumLayout>:
    selected: app.selected_shutters
    canvas.before:
        Color:
            rgba: 0.4, 0.4, 0.4, 1.
        Rectangle:
            size: self.size
    Label:
        size_hint: 1, None
        height: '40dp'
        top: root.top
        font_size: app.labelsize
        outline_width: 1
        text: app.fg
        text_size: self.size
        halign: 'center'
        valign: 'middle'
    Label:
        size_hint: 0.08, 1.
        pos_hint: {'x': 0.46, 'y': 0.}
        text_size: self.size[::-1]
        font_size: app.labelsize
        halign: 'center'
        valign: 'middle'
        text: 'DETECTOR GAP'
        color: 0.7, 0.7, 0.7, 1.
        canvas.before:
            PushMatrix
            Rotate:
                angle: 90
                origin: self.center_x, self.center_y, 0
        canvas.after:
            PopMatrix
    SpectralZone:
        quadrant: 2
        id: q2
        sci_range: root.sci_range
        aspect: root.aspect
        data: None if root.nrs is None else root.nrs[0,1]
        stuck_data: None if root.stu is None else root.stu[0,1]
    OutsideLabel:
        aspect: root.aspect
        quadrant: 2
    SpectralZone:
        quadrant: 0
        id: q0
        sci_range: root.sci_range
        aspect: root.aspect
        data: None if root.nrs is None else root.nrs[1,1]
        stuck_data: None if root.stu is None else root.stu[1,1]
    OutsideLabel:
        aspect: root.aspect
        quadrant: 0
    SpectralZone:
        quadrant: 3
        id: q3
        sci_range: root.sci_range
        aspect: root.aspect
        data: None if root.nrs is None else root.nrs[0,0]
        stuck_data: None if root.stu is None else root.stu[0,0]
    OutsideLabel:
        aspect: root.aspect
        quadrant: 3
    SpectralZone:
        quadrant: 1
        id: q1
        sci_range: root.sci_range
        aspect: root.aspect
        data: None if root.nrs is None else root.nrs[1,0]
        stuck_data: None if root.stu is None else root.stu[1,0]
    OutsideLabel:
        aspect: root.aspect
        quadrant: 1
""")

class SpectralQuadrant(SpectralBase):
    """
    One half of an NRS, which I'm associating with an MSA quadrant. I recognize
    that this is somewhat misleading, but I can't think of a better nomenclature.
    """
    
    quadrant = NumericProperty(0)
    stuck = BooleanProperty(False)
    
    def _get_inset_size(self):
        return self.width - 4, self.height - 15
        
    def _get_inset_pos(self):
        xp = self.x + 2
        yp = self.y + 15 * (self.quadrant % 2)
        return (xp, yp)
    
    inset_pos = AliasProperty(_get_inset_pos, None, bind=['x', 'y', 'quadrant'])
    
class SpectralZone(AnchorLayout):
    """
    A wrapper to hold both layers of the quadrant (one for deliberately-opened
    shutters, the other for stuck-open shutters).
    """
    aspect = NumericProperty(1.)
    quadrant = NumericProperty(0)
    data = ObjectProperty(None, allownone=True, force_dispatch=True)
    stuck_data = ObjectProperty(None, allownone=True, force_dispatch=True)
    sci_min = NumericProperty(0.)
    sci_max = NumericProperty(1.)
    sci_range = ReferenceListProperty(sci_min, sci_max)
    
    def _get_qsizehint(self):
        if self.aspect == 0:
            self.aspect = 1.
        xhint = 0.46
        yhint = 0.23 / self.aspect
        return [xhint, yhint]
    
    qsizehint = AliasProperty(_get_qsizehint, None, bind=['aspect'])
    
    def _get_qposhint(self):
        if self.aspect == 0:
            self.aspect = 1.
        xhint = 0.54 * (1 - self.quadrant // 2)
        yhint = 0.5 - (self.quadrant % 2) * 0.23 / self.aspect
        return {'x': xhint, 'y': yhint}
    
    qposhint = AliasProperty(_get_qposhint, None, bind=['quadrant', 'aspect'])
    
class OutsideLabel(Label):
    aspect = NumericProperty(1.)
    quadrant = NumericProperty(0)
    
    def _get_olsizehint(self):
        return 0.46, 0.5 - 0.23/self.aspect
    
    olsizehint = AliasProperty(_get_olsizehint, None, bind=['aspect'])
    
    def _get_olposhint(self):
        xh = 0.54 * (self.quadrant in [0,1])
        yh = (0.5 + 0.23 / self.aspect) * (self.quadrant in [0,2])
        return {'x':xh, 'y':yh}
    
    olposhint = AliasProperty(_get_olposhint, None, bind=['aspect', 'quadrant'])
    

class SpectrumLayout(FloatLayout):
    msa = ObjectProperty(None, allownone=True) #MSA calculation object
    open_shutters = DictProperty({}) #Dictionary of open shutters
    waiting = ObjectProperty(None, allownone=True) #The Please Wait popup
    shutter_limits = DictProperty({}) #Tracking shutter limits for export
    selected = ListProperty([])
    selected_boxes = DictProperty({})
    
    empties = ListProperty([])
    
    #wavelength values:
    sci_min = NumericProperty(0.)
    sci_max = NumericProperty(1.)
    sci_range = ReferenceListProperty(sci_min, sci_max)
    
    #data arrays:
    nrs = ObjectProperty(np.zeros((2,2,171,2048), dtype=float), 
                         allownone=True, force_dispatch=True)
    stu = ObjectProperty(np.zeros((2,2,171,2048), dtype=float), 
                         allownone=True, force_dispatch=True)
    
    def _get_aspect(self):
        """
        Determine the aspect ratio, to keep everthing positioned and sized 
        properly, even after resize.
        """
        if self.width <= 0. or self.height <= 0.:
            return 1.
        return float(self.height) / float(self.width)
    
    aspect = AliasProperty(_get_aspect, None, bind=['size'])
    
    def on_open_shutters(self, instance, value):
        self.wrapper()
    
    def on_msa(self, instance, value):
        self.wrapper()
    
    def wrapper(self):
        if self.msa is None or not self.open_shutters:
            return
        self.sci_range = self.msa.sci_range
        self.waiting = WaitPopup(num_shutters=len(self.open_shutters),
                                 current_shutter = 0)
        self.waiting.open()
        
        t = Thread(target=self.reset)
        t.start()
        #self.reset()
        
    def get_select_bounds(self, q, i, j):
        top = 1 - q % 2
        nrs1, nrs2 = self.nrs[:,top,170-j]
        x1, = np.nonzero(np.logical_and(nrs1 >= self.sci_min, 
                                        nrs1 <= self.sci_max))
        x2, = np.nonzero(np.logical_and(nrs2 >= self.sci_min, 
                                        nrs2 <= self.sci_max))
        if x1.size < 1:
            b1 = []
        else:
            b1 = [x1[0], j, x1[-1]+1, j+1]
        if x2.size < 1:
            b2 = []
        else:
            b2 = [x2[0], j, x2[-1]+1, j+1]
        return [b1, b2]
    
    def on_selected(self, instance, value):
        #prune de-selected shutters
        to_delete = []
        for (q,i,j),box in self.selected_boxes.items():
            if (i,j) not in self.selected[q]:
                self.canvas.after.remove(box)
                to_delete.append((q,i,j))
        for qij in to_delete:
            self.selected_boxes.pop(qij)
        
        #add new boxes
        for q, select in enumerate(self.selected):
            for (i,j) in select:
                if (q,i,j) not in self.selected_boxes:
                    bounds = self.get_select_bounds(q,i,j)
                    targets = [('q2','q0'), ('q3','q1')][q % 2]
                    instr = []
                    for target, box in zip(targets, bounds):
                        #convert from array coords to interface coords
                        if not box: 
                            continue
                        quad = self.ids[target].ids.chosen
                        qx0, qy0 = self.to_widget(*quad.to_window(*quad.inset_pos))
                        qw, qh = quad.inset_size
                        qx1, qy1 = qx0 + qw, qy0 + qh
                        x0, y0, x1, y1 = box
                        bx0 = x0 / 2048 * qw + qx0
                        by1 = (171 - y0) / 171 * qh + qy0
                        bx1 = qx1 - (2048 - x1) / 2048 * qw
                        by0 = qy1 - y1 / 171 * qh
                        box_pos = bx0, by0
                        box_size = (bx1 - bx0), (by1 - by0)
                        instr.append(Rectangle(pos=box_pos, size=box_size))
                    if instr:
                        group = InstructionGroup()
                        group.add(Color(1, 1, 1, 0.6))
                        for ins in instr:
                            group.add(ins)
                    self.selected_boxes[(q,i,j)] = group
                    self.canvas.after.add(group)
        self.canvas.ask_update()
    
    def reset(self):
        """
        Calculate the wavelength arrays. Any updates to the data arrays will 
        propogate to their respective SpectralZone, thanks to the magic of 
        Kivy properties).
        """
        #initialize arrays for spectra
        #dimensions: NRS1 vs 2; top vs bottom; shutter row; pixel
        nrs_tmp = np.zeros((2,2,171,2048), dtype=float)
        stu_tmp = np.zeros((2,2,171,2048), dtype=float)
        self.shutter_limits = {}
        
        #calculate each spectrum and put it in the appropriate place
        for (q, i, j), stuck in self.open_shutters.items():
            if self.waiting:
                self.waiting.current_shutter += 1
            top = 1 - q % 2
            lim = [None] * 4
            for n in range(2):
                wave = self._get_shutter(q,i,j,n)
                if wave is None:
                    continue
                if stuck:
                    stu_tmp[n,top,170-j] = wave
                else:
                    nrs_tmp[n,top,170-j] = wave
                    if wave.min() <= self.sci_max and wave.max() >=self.sci_min:
                        lim[n*2:n*2+2] = [max(wave.min(), self.sci_min), 
                                          min(wave.max(), self.sci_max)]
            if not stuck:
                self.shutter_limits[(q+1,i+1,j+1)] = lim
        
        Clock.schedule_once(lambda dt: self.proceed(stu_tmp, nrs_tmp), 0.1)
    
    def proceed(self, stu, nrs):
        """
        Dismiss the popup to unblock the app.
        """
        self.stu = stu
        self.nrs = nrs
        
        if self.waiting:
            self.waiting.dismiss()
            self.waiting = None
        
        
    def _get_shutter(self, q, i, j, n):
        """
        Calculate the data and display parameters for a given shutter.
        """
        if self.msa is None:
            return
        return self.msa(q,i,j,n)
