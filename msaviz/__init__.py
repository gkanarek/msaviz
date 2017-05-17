# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 13:55:41 2017

@author: gkanarek
"""
from __future__ import absolute_import


from .msa import parse_msa_config, MSAConfig

__all__ = ['run', 'MSAConfig', 'parse_msa_config']

def run():
    """Entry point for the MSA Visualization Tool script."""
    from .msaviz import WaveTool
    WaveTool().run()
    
if __name__ == "__main__":
    run()