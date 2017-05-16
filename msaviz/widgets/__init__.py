# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 10:13:31 2017

@author: gkanarek
"""

from __future__ import absolute_import, division, print_function

from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.scatterlayout import ScatterLayout

Builder.load_string("""
<FloatStencil>:

<LockScatter>:
    do_rotation: False
    do_scale: True
    do_translation: self.scale > 1.0
    scale_min: 1.0
""")

class FloatStencil(FloatLayout, StencilView):
    pass

class LockScatter(ScatterLayout):
    def transform_with_touch(self, touch):
        if touch:
            super(LockScatter, self).transform_with_touch(touch)
        self.x = min(self.parent.x, self.x)
        self.right = max(self.parent.right, self.right)
        self.y = min(self.parent.y, self.y)
        self.top = max(self.parent.top, self.top)