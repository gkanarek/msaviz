# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 12:55:35 2017

@author: gkanarek
"""
from __future__ import absolute_import, division, print_function

import os
import numpy as np

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import (StringProperty, AliasProperty, BooleanProperty,
                             ListProperty, NumericProperty, ObjectProperty)
from kivy.graphics.texture import Texture

from ..widgets import FloatStencil, LockScatter
from ..widgets.popups import MSAFilePopup, FindShutterPopup

Builder.load_string("""#:import os os
<ShutterZone>:
    update: app.update_shutters
    theapp: app
    anchor_x: 'center'
    anchor_y: 'center'
    pos_hint: self.zposhint
    size_hint: self.zsizehint
    on_selected: app.update_selected(self.quadrant, self.selected)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            size: self.size
            pos: self.pos
    canvas.after:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            size: self.size
            pos: self.pos
            texture: self.shutter_texture
        Line:
            rectangle: self.pos + self.size
            width: 1
    Label:
        color: 0.4, 0.4, 0.4, 1
        text: "Q{}".format(root.quadrant+1)
        font_size: 1.5*app.labelsize
        text_size: self.size
        halign: 'center'
        valign: 'middle'
        size_hint: 1, 1

<ShutterLayout>:
    canvas.before:
        Color:
            rgba: 0.4, 0.4, 0.4, 1.
        Rectangle:
            size: self.size
            pos: self.pos
    ShutterZone:
        quadrant: 2
        id: q2
    ShutterZone:
        quadrant: 0
        id: q0
    ShutterZone:
        quadrant: 3
        id: q3
    ShutterZone:
        quadrant: 1
        id: q1
            

<ShutterScreen>:
    msafile: os.path.basename(app.msa_file)
    filtname: app.filtname
    gratname: app.gratname
    BoxLayout:
        orientation: 'vertical'
        FloatStencil:
            id: stencil
            LockScatter:
                size_hint: 1., 1.
                id: shutterpane
                ShutterLayout:
                    id: shutterlayout
                    size_hint: 1., 1.
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
                text_size: self.size
                halign: 'center'
                valign: 'middle'
                font_size: '12pt'
            Label:
                text: root.recent_select_text
                text_size: self.size
                halign: 'center'
                valign: 'middle'
                font_size: '12pt'
            Button:
                size_hint_x: None
                width: '80dp'
                text: 'Find...'
                on_release: root.find_dialog()
                font_size: '12pt'
            Button:
                size_hint_x: None
                width: '80dp'
                text: 'Save...'
                on_release: root.save_dialog()
                font_size: '12pt'
                disabled: shutterpane.scale > 1.0
            Button:
                size_hint_x: None
                width: '80dp'
                text: 'Back'
                on_release: app.sm.current = 'spectral'
                font_size: '12pt'
""")

class ShutterZone(AnchorLayout):
    aspect = NumericProperty(1.)
    quadrant = NumericProperty(0)
    selected = ListProperty([])
    theapp = ObjectProperty(None)
    update = BooleanProperty(False)
        
    def on_touch_down(self, touch):
        if not touch.button == 'left' or self.disabled:
            return
        x, y = touch.pos
        if not self.collide_point(x, y):
            return
            
        tmp = self.selected[:]
        
        lx, ly = self.to_local(x, y, relative=True)
        col = 364 - int(lx / self.width * 365)
        row = 170 - int(ly / self.height * 171)
        val = self.theapp.all_shutters[self.quadrant][(col, row)]
                
        if (col, row) in self.selected:
            tmp.remove((col, row))
        elif val == '0':
            tmp.append((col, row))
        self.selected = tmp
    
    def _get_shutter_texture(self):
        txtr = Texture.create(size=(365*3,171*3), colorfmt='rgba', mipmap=True)
        
        data = np.zeros((171,365,4),dtype=np.uint8)
        
        if self.theapp is not None and self.theapp.all_shutters[self.quadrant]:
            color = {"0": [255, 155, 5, 255], "1": [0, 0, 0, 0],
                     "x": [68, 68, 68, 255], "s": [135, 44, 44, 255]}
            s_color = [29, 226, 226, 255]
            for j in range(171):
                for i in range(365):
                    val = self.theapp.all_shutters[self.quadrant][(i,j)]
                    colr = color[val] if (i,j) not in self.selected else s_color
                    data[170-j,364-i] = colr
        data = np.repeat(np.repeat(data, 3, axis=0), 3, axis=1)
        txtr.blit_buffer(data.tostring(), colorfmt='rgba', bufferfmt='ubyte')
        return txtr
    
    shutter_texture = AliasProperty(_get_shutter_texture, None,
                                    bind=['update', 'selected', 'quadrant'])
    
    def _get_zsizehint(self):
        if self.aspect == 0:
            self.aspect = 1.
        xhint = 0.48
        yhint = 0.48 / self.aspect
        return [xhint, yhint]
    
    zsizehint = AliasProperty(_get_zsizehint, None, bind=['aspect'])
    
    def _get_zposhint(self):
        if self.aspect == 0:
            self.aspect = 1.
        xhint = 0.5 * (1 - self.quadrant // 2) + 0.01
        yhint = 0.25 - 0.24 / self.aspect + 0.5 * (1 - self.quadrant % 2)
        return {'x': xhint, 'y': yhint}
    
    zposhint = AliasProperty(_get_zposhint, None, bind=['quadrant', 'aspect'])    
    

class ShutterLayout(FloatLayout):
    
    def _get_aspect(self):
        """
        Determine the aspect ratio, to keep everthing positioned and sized 
        properly, even after resize.
        """
        if self.width <= 0. or self.height <= 0.:
            return 1.
        return float(self.height) / float(self.width)
    
    aspect = AliasProperty(_get_aspect, None, bind=['size'])

class ShutterScreen(Screen):
    msafile = StringProperty('')
    selected = ListProperty([])
    filtname = StringProperty('')
    gratname = StringProperty('')
    recent_select = ListProperty([])

    def on_pre_enter(self):
        self.ids.shutterpane.transform_with_touch(False)
        
    def on_leave(self):
        self.ids.shutterpane.scale = 1.0
        self.ids.shutterpane.transform_with_touch(False)
    
    def _recent_select_text(self):
        if not self.recent_select:
            return ""
        return "Q {}, I {}, J {}".format(*self.recent_select)
    
    recent_select_text = AliasProperty(_recent_select_text, None, bind=['recent_select'])
        
    def save_dialog(self):
        suggested, ext = os.path.splitext(self.msafile)
        suggested += '_'+self.filtname+'_'+self.gratname+'_shutters.png'
        popup = MSAFilePopup(title="Save...", allowed_ext=["*.png"], 
                             suggested_file=suggested)
        popup.bind(on_dismiss=self.save_png)
        popup.open()
    
    def find_dialog(self):
        sel = [(q+1,i+1,j+1) for q,quad in enumerate(self.selected) for i,j in quad]
        popup = FindShutterPopup(selected=sel)
        popup.bind(on_dismiss=self.zoom_to)
        popup.open()
    
    def zoom_to(self, instance):
        if instance.canceled:
            return
        stencil = self.ids.stencil #parent of the scatter
        scatter = self.ids.shutterpane
        
        q, i, j = instance.quad, instance.col, instance.row
        
        #set the scatter scaling correctly
        scatter.scale = 4.0
        
        #determine the fractional shutter position, w/r/t to quadrant placement
        #in the scatter
        quadrant = self.ids.shutterlayout.ids['q'+str(q)]    
        qw, qh = quadrant.size_hint
        qx, qy = [quadrant.pos_hint[c] for c in 'xy']
        sx0 = (364 - i) / 365 #fractional x in the quadrant
        sy0 = (170 - j) / 171 #fractional y in the quadrant
        
        sfx = sx0 * qw + qx #fractional x position in the scatter
        sfy = sy0 * qh + qy #fractional y position in the scatter
        
        #Now find the offsets from the scatter center, and move the center so
        #that the shutter is on the target (which is the stencil center)
        scx, scy = scatter.center
        (bx, by), (bw, bh) = scatter.bbox
        stx, sty = stencil.center
        
        sx = sfx * bw + bx #pixel x position in scatter
        sy = sfy * bh + by #pixel y position in scatter
        
        x1 = (stx - sx) + scx
        y1 = (sty - sy) + scy
        
        scatter.center = [x1, y1]
        scatter.transform_with_touch(False) #enforce the border lock
        
    
    def save_png(self, instance):
        if instance.canceled:
            return
        png_out = os.path.join(instance.selected_path, instance.selected_file)
        filebase, ext = os.path.splitext(png_out)
        png_out = filebase + '.png'
        self.ids.shutterpane.export_to_png(png_out)
