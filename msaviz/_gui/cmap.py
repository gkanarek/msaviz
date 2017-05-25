# -*- coding: utf-8 -*-
"""
Created on Tue Jan  3 13:28:26 2017

@author: gkanarek

This is blatant stealing and/or adaptation of matplotlib code. I'm doing this
so that my packaging doesn't need to include all of matplotlib when I'm only
using a single colormap
"""

import numpy as np

_Spectral_data = tuple(reversed(( #we reverse it to get Spectral_r
    (0.61960784313725492, 0.003921568627450980, 0.25882352941176473),
    (0.83529411764705885, 0.24313725490196078 , 0.30980392156862746),
    (0.95686274509803926, 0.42745098039215684 , 0.2627450980392157 ),
    (0.99215686274509807, 0.68235294117647061 , 0.38039215686274508),
    (0.99607843137254903, 0.8784313725490196  , 0.54509803921568623),
    (1.0                , 1.0                 , 0.74901960784313726),
    (0.90196078431372551, 0.96078431372549022 , 0.59607843137254901),
    (0.6705882352941176 , 0.8666666666666667  , 0.64313725490196083),
    (0.4                , 0.76078431372549016 , 0.6470588235294118 ),
    (0.19607843137254902, 0.53333333333333333 , 0.74117647058823533),
    (0.36862745098039218, 0.30980392156862746 , 0.63529411764705879)
    )))

vals = np.linspace(0., 1., len(_Spectral_data))

cdict = dict(red=[], green=[], blue=[], alpha=[])
for val, color in zip(vals, _Spectral_data):
    r, g, b = color
    cdict['red'].append((val, r, r))
    cdict['green'].append((val, g, g))
    cdict['blue'].append((val, b, b))
    cdict['alpha'].append((val, 1., 1,))

def makeMappingArray(N, data, gamma=1.0):
    """Create an *N* -element 1-d lookup table
    *data* represented by a list of x,y0,y1 mapping correspondences.
    Each element in this list represents how a value between 0 and 1
    (inclusive) represented by x is mapped to a corresponding value
    between 0 and 1 (inclusive). The two values of y are to allow
    for discontinuous mapping functions (say as might be found in a
    sawtooth) where y0 represents the value of y for values of x
    <= to that given, and y1 is the value to be used for x > than
    that given). The list must start with x=0, end with x=1, and
    all values of x must be in increasing order. Values between
    the given mapping points are determined by simple linear interpolation.
    Alternatively, data can be a function mapping values between 0 - 1
    to 0 - 1.
    The function returns an array "result" where ``result[x*(N-1)]``
    gives the closest value for values of x between 0 and 1.
    """
    
    adata = np.array(data)
    shape = adata.shape
    if len(shape) != 2 or shape[1] != 3:
        raise ValueError("data must be nx3 format")

    x = adata[:, 0]
    y0 = adata[:, 1]
    y1 = adata[:, 2]

    if x[0] != 0. or x[-1] != 1.0:
        raise ValueError(
            "data mapping points must start with x=0 and end with x=1")
    if (np.diff(x) < 0).any():
        raise ValueError("data mapping points must have x in increasing order")
    # begin generation of lookup table
    x = x * (N - 1)
    lut = np.zeros((N,), float)
    xind = (N - 1) * np.linspace(0, 1, N) ** gamma
    ind = np.searchsorted(x, xind)[1:-1]

    distance = (xind[1:-1] - x[ind - 1]) / (x[ind] - x[ind - 1])
    lut[1:-1] = distance * (y0[ind] - y1[ind - 1]) + y1[ind - 1]
    lut[0] = y1[0]
    lut[-1] = y0[-1]
    # ensure that the lut is confined to values between 0 and 1 by clipping it
    return np.clip(lut, 0.0, 1.0)

class spectral_cmap(object):
    """
    This is a quick and dirty recreation of a matplotlib Colormap, so
    that we don't have to package the entirety of mpl to get a single colormap
    out of it.
    
    The normalization functionality of ScalarMappable is also built in 
    (with default normalization, i.e. linear from 0 to 1).
    """
    
    def __init__(self, vmin=None, vmax=None):
        self.N = 256
        self._segmentdata = cdict
        self._gamma = 1.0
        self.name = "Spectral_r"
        self._rgba_bad = (0.0, 0.0, 0.0, 0.0)  # If bad, don't paint anything.
        self._rgba_under = (0.0, 0.0, 0.0, 1.0)
        self._rgba_over = (0.0, 0.0, 0.0, 1.0)
        self._i_under = self.N
        self._i_over = self.N + 1
        self._i_bad = self.N + 2
        self.vmin, self.vmax = vmin, vmax
        
        #create the lookuptable
        self._lut = np.ones((self.N + 3, 4), float)
        self._lut[:-3, 0] = makeMappingArray(
            self.N, self._segmentdata['red'], self._gamma)
        self._lut[:-3, 1] = makeMappingArray(
            self.N, self._segmentdata['green'], self._gamma)
        self._lut[:-3, 2] = makeMappingArray(
            self.N, self._segmentdata['blue'], self._gamma)
        if 'alpha' in self._segmentdata:
            self._lut[:-3, 3] = makeMappingArray(
                self.N, self._segmentdata['alpha'], 1)

        #set extremes
        if self._rgba_under:
            self._lut[self._i_under] = self._rgba_under
        else:
            self._lut[self._i_under] = self._lut[0]
        if self._rgba_over:
            self._lut[self._i_over] = self._rgba_over
        else:
            self._lut[self._i_over] = self._lut[self.N - 1]
        self._lut[self._i_bad] = self._rgba_bad
    
    def __call__(self, X, alpha=None, bytes=False):
        """
        Parameters
        ----------
        X : scalar, ndarray
            The data value(s) to convert to RGBA.
            For floats, X should be in the interval ``[0.0, 1.0]`` to
            return the RGBA values ``X*100`` percent along the Colormap line.
            For integers, X should be in the interval ``[0, Colormap.N)`` to
            return RGBA values *indexed* from the Colormap with index ``X``.
        alpha : float, None
            Alpha must be a scalar between 0 and 1, or None.
        bytes : bool
            If False (default), the returned RGBA values will be floats in the
            interval ``[0, 1]`` otherwise they will be uint8s in the interval
            ``[0, 255]``.
        Returns
        -------
        Tuple of RGBA values if X is scalar, othewise an array of
        RGBA values with a shape of ``X.shape + (4, )``.
        """
        
        #first run it through the normalizer
        X = np.ma.asarray(X)
        X = self._normalize(X)
        
        #then run it through the colormap calculation
        
        mask_bad = None
        
        if np.isscalar(X):
            vtype = 'scalar'
            xa = np.array([X])
        else:
            vtype = 'array'
            xma = np.ma.array(X, copy=True)  # Copy here to avoid side effects.
            mask_bad = xma.mask              # Mask will be used below.
            xa = xma.filled()                # Fill to avoid infs, etc.
            del xma

        # Calculations with native byteorder are faster, and avoid a
        # bug that otherwise can occur with putmask when the last
        # argument is a numpy scalar.
        if not xa.dtype.isnative:
            xa = xa.byteswap().newbyteorder()

        if xa.dtype.kind == "f":
            # Treat 1.0 as slightly less than 1.
            vals = np.array([1, 0], dtype=xa.dtype)
            almost_one = np.nextafter(*vals)
            np.copyto(xa, almost_one, where=xa == 1.0)
            # The following clip is fast, and prevents possible
            # conversion of large positive values to negative integers.

            xa *= self.N
            np.clip(xa, -1, self.N, out=xa)

            # ensure that all 'under' values will still have negative
            # value after casting to int
            np.copyto(xa, -1, where=xa < 0.0)
            xa = xa.astype(int)

        # Set the over-range indices before the under-range;
        # otherwise the under-range values get converted to over-range.
        np.copyto(xa, self._i_over, where=xa > self.N - 1)
        np.copyto(xa, self._i_under, where=xa < 0)
        
        if mask_bad is not None:
            if mask_bad.shape == xa.shape:
                np.copyto(xa, self._i_bad, where=mask_bad)
            elif mask_bad:
                xa.fill(self._i_bad)
        if bytes:
            lut = (self._lut * 255).astype(np.uint8)
        else:
            lut = self._lut.copy()  # Don't let alpha modify original _lut.

        if alpha is not None:
            alpha = min(alpha, 1.0)  # alpha must be between 0 and 1
            alpha = max(alpha, 0.0)
            if bytes:
                alpha = int(alpha * 255)
            if (lut[-1] == 0).all():
                lut[:-1, -1] = alpha
                # All zeros is taken as a flag for the default bad
                # color, which is no color--fully transparent.  We
                # don't want to override this.
            else:
                lut[:, -1] = alpha
                # If the bad value is set to have a color, then we
                # override its alpha just as for any other value.

        rgba = np.empty(shape=xa.shape + (4,), dtype=lut.dtype)
        lut.take(xa, axis=0, mode='clip', out=rgba)
        if vtype == 'scalar':
            rgba = tuple(rgba[0, :])
        return rgba
        
    @staticmethod
    def process_value(value):
        """
        Homogenize the input *value* for easy and efficient normalization.
        *value* can be a scalar or sequence.
        Returns *result*, *is_scalar*, where *result* is a
        masked array matching *value*.  Float dtypes are preserved;
        integer types with two bytes or smaller are converted to
        np.float32, and larger types are converted to np.float64.
        Preserving float32 when possible, and using in-place operations,
        can greatly improve speed for large arrays.
        Experimental; we may want to add an option to force the
        use of float32.
        """
        is_scalar = np.isscalar(value)
        if is_scalar:
            value = [value]
        dtype = np.min_scalar_type(value)
        if np.issubdtype(dtype, np.integer) or dtype.type is np.bool_:
            # bool_/int8/int16 -> float32; int32/int64 -> float64
            dtype = np.promote_types(dtype, np.float32)
        result = np.ma.array(value, dtype=dtype, copy=True)
        return result, is_scalar
    
    def _normalize(self, value):
        result, is_scalar = self.process_value(value)

        self.autoscale_None(result)
        # Convert at least to float, without losing precision.
        (vmin,), _ = self.process_value(self.vmin)
        (vmax,), _ = self.process_value(self.vmax)
        if vmin == vmax:
            result.fill(0)   # Or should it be all masked?  Or 0.5?
        elif vmin > vmax:
            raise ValueError("minvalue must be less than or equal to maxvalue")
        else:
            # ma division is very slow; we can take a shortcut
            # use np.asarray so data passed in as an ndarray subclass are
            # interpreted as an ndarray. See issue #6622.
            resdat = np.asarray(result.data)
            resdat -= vmin
            resdat /= (vmax - vmin)
            result = np.ma.array(resdat, mask=result.mask, copy=False)
        if is_scalar:
            result = result[0]
        return result

    def inverse(self, value):
        if not self.scaled():
            raise ValueError("Not invertible until scaled")
        (vmin,), _ = self.process_value(self.vmin)
        (vmax,), _ = self.process_value(self.vmax)

        if not np.isscalar(value):
            val = np.ma.asarray(value)
            return vmin + val * (vmax - vmin)
        else:
            return vmin + value * (vmax - vmin)

    def autoscale(self, A):
        """
        Set *vmin*, *vmax* to min, max of *A*.
        """
        self.vmin = np.ma.min(A)
        self.vmax = np.ma.max(A)

    def autoscale_None(self, A):
        ' autoscale only None-valued vmin or vmax'
        if self.vmin is None and np.size(A) > 0:
            self.vmin = np.ma.min(A)
        if self.vmax is None and np.size(A) > 0:
            self.vmax = np.ma.max(A)

    def scaled(self):
        'return true if vmin and vmax set'
        return (self.vmin is not None and self.vmax is not None)