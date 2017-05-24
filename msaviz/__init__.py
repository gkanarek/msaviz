# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 13:55:41 2017

@author: gkanarek
"""
from __future__ import absolute_import


from .msa import (parse_msa_config, MSAConfig, wavelength_table, 
                  check_wavelengths, MSA)

__all__ = ['run', 'MSAConfig', 'parse_msa_config', 'wavelength_table', 
           'check_wavelengths', 'MSA']

def run():
    """Entry point for the MSA Visualization Tool script."""
    from ._gui import WaveTool
    WaveTool().run()
    
if __name__ == "__main__":
    run()