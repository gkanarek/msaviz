# -*- coding: utf-8 -*-
"""
Created on Fri Mar  3 13:06:01 2017

@author: gkanarek
"""

from __future__ import absolute_import, division, print_function

from warnings import warn

import numpy as np


class ShutterCoord(object):
    """
    This is a convenience class to handle conversions between the four coordinate
    systems: numpy coordinates (q,i,j), MSA coordinates (like qij but 1-based),
    x/y (looking at the MSA as a whole, instead of quadrants), and 1-d indexing
    (for use with tables).
    
    The internal representation is MSA coordinates; to create a ShutterCoord
    object from one of the other systems, use the classmethods defined below.
    Access is through properties.
    """
    
    _xy_cache = {}
    _qij_cache = {}
    _idx_cache = {}
    
    def __init__(self, quad=0, col=0, row=0):
        """
        Initialize the MSA coordinates internal representation.
        """
        self.quad, self.col, self.row = self._standardize_inputs(quad, col,
                                                                 row)
        
    @property
    def _msa(self):
        """
        Quick access to the MSA representation tuple, primarily used for 
        convenience when working with caches.
        
        For internal use only.
        """
        return (self.quad, self.col, self.row)
    
    @staticmethod
    def _test_array(*arg):
        """
        Convenience method to test an arbitrary number of arguments, returning
        a list of bools indicating whether or not they are numpy arrays.
        
        For internal use only.
        """
        return [isinstance(c, np.ndarray) for c in arg]
    
    def _standardize_inputs(self, *args):
        """
        A wrapper function for _standardize_input (below) to work on all arguments.
        """
        arrays = self._test_array(*args)
        if any(arrays):
            self.cache = False
            if not all(arrays):
                warn("Broadcasting scalar arguments to arrays...", 
                     RuntimeWarning)
            
            #Standardize 
            size = [a.size for i,a in enumerate(args) if arrays[i]]
            final_size = min(size)
            if any([s != final_size for s in size]):
                warn("Arrays are not the same size; truncating long arrays...",
                     RuntimeWarning)
            
            std = self._standardize_input
            out = [std(arg, max_size=final_size, scalar=not arr) 
                                for arg,arr in zip(args, arrays)]
        else:
            out = list(map(int, args)) #just in case we have any int16s thrown in
            self.cache = True
        
        return out
        
    @staticmethod
    def _standardize_input(arg, max_size=None, scalar=False):
        """
        If the input is an array (scalar=False), truncate to max_size if 
        indicated, and ensure that the dtype is int64.
        
        If the input is scalar (scalar=False), broadcast to max_size.
        """
        if scalar:
            if not max_size:
                raise ValueError("Need a max size for standardizing scalar input")
            return np.full(max_size, arg, dtype=int)
        else:
            out = arg.astype(int)
            if max_size:
                out = out[:max_size]
            return out
    
    #Conversion functions!
    
    @staticmethod
    def _to_qij(q, c, r):
        return (q-1, c-1, r-1)
    
    @staticmethod
    def _from_qij(q, i, j):
        return (q+1, i+1, j+1)
    
    @staticmethod
    def _to_xy(q, c, r):
        qcol = [1,1,0,0]
        qrow = [1,0,1,0]
        x = (365-c) + 365*qcol[q-1]
        y = (171-r) + 171*qrow[q-1]
        return (x, y)
    
    @staticmethod
    def _from_xy(x, y):
        quad_row = y // 171
        quad_col = x // 365
        q = 2 * quad_col + quad_row + 1
        c = x % 365 + 1
        r = y % 171 + 1
        return (q,c,r)
    
    @staticmethod
    def _to_idx(q, c, r):
        qq = (q - 1) * 365 * 171
        ii = (c - 1) * 171
        jj = (r - 1)
        return qq + ii + jj
    
    @staticmethod
    def _from_idx(idx):
        r = idx % 171
        c = ((idx - r) // 171) % 365
        q = ((idx - r - c*171) // (365 * 171))
        return (q+1, c+1, r+1)
    
    #Now we get to the properties:
    
    @property
    def qij(self):
        if not self.cache:
            return self._to_qij(*self._msa)
        if self._msa not in self._qij_cache:
            self._qij_cache[self._msa] = self._to_qij(*self._msa)
        return self._qij_cache[self._msa]
    
    @qij.setter
    def qij(self, qij):
        q, i, j = self._standardize_inputs(*qij)
        self.quad, self.col, self.row = self._from_qij(q, i, j)
    
    @property
    def xy(self):
        if not self.cache:
            return self._to_xy(*self._msa)
        if self._msa not in self._xy_cache:
            self._xy_cache[self._msa] = self._to_xy(*self._msa)
        return self._xy_cache[self._msa]
    
    @xy.setter
    def xy(self, xy):
        x, y = self._standardize_inputs(*xy)
        self.quad, self.col, self.row = self._from_xy(x, y)
        
    @property
    def idx(self):
        if not self.cache:
            return self._to_idx(*self._msa)
        if self._msa not in self._idx_cache:
            self._idx_cache[self._msa] = self._to_idx(*self._msa)
        return self._idx_cache[self._msa]
    
    @idx.setter
    def idx(self, idx):
        idx, = self.standardize_inputs(idx)
        self.quad, self.col, self.row = self._from_idx(idx)
    
    #Constructor methods!
    
    @classmethod
    def from_qij(cls, q, i, j):
        new = cls()
        new.qij = (q, i, j)
        return new
    
    @classmethod
    def from_xy(cls, x, y):
        new = cls()
        new.xy = (x, y)
        return new
    
    @classmethod
    def from_idx(cls, idx):
        new = cls()
        new.idx = idx
        return new