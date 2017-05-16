# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 13:55:41 2017

@author: gkanarek
"""
from __future__ import absolute_import


from .msaviz import WaveTool

def run():
    """Entry point for the MSA Visualization Tool script."""
    WaveTool().run()
    
if __name__ == "__main__":
    run()