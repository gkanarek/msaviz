======================
MSA Visualization Tool
======================

This tool is a prototype for the "Spectrum View" mode, when designing a NIRSpec MSA observation with APT. The intent for the tool is to provide a means of visualizing the spectra which will be observed given a particular MSA shutter configuration, filter, and grating.

In the current standalone implementation, the user must provide an MSA configuration file, which is a .csv file which can be exported from APT, and contains a record of which shutters are open. Once the MSA config file has been parsed, and a filter+grating combination is chosen, the tool displays a simplified model of where the spectra from the open shutters will fall on the NRS1 and NRS2 detectors.

Installation
------------
It is strongly recommended to use MSAViz in conjunction with the `Anaconda Python distribution <https://www.continuum.io/anaconda-overview>`_, which greatly simplifies the installation of dependencies.

NOTE: these instructions have not been tested on Windows.

**Step 1: Create a new conda environment.**
::

$ conda create --name msaviz pip numpy scipy astropy cython
$ source activate msaviz

You can specify a particular python version when creating the conda environment with ``python=2`` or ``python=3`` or something similar; otherwise, it will default to the python version of your Anaconda distribution.

**Step 2: Install Kivy and its dependencies.**

*Windows:*
::

$ conda install docutils pygments
$ pip install pypiwin32 kivy.deps.sdl2 kivy.deps.glew
$ pip install kivy

*Mac:*
To install the Kivy dependencies, you will need to have the `Homebrew package manager <https://brew.sh/>`_ installed. If you are trying to install this on a Mac owned by STScI, you will likely run into problems when attempting to install Homebrew. I have included the ``install_homebrew.sh`` script `here <https://github.com/gkanarek/msaviz/blob/master/install_homebrew.sh>`_, to handle this task. Once you run the script, and follow the instructions at the end, simply do ``$ brew_activate`` in advance any time you activate the ``msaviz`` conda environment.
::

$ brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer
$ USE_OSX_FRAMEWORKS=0 pip install -I --no-cache-dir --no-binary all kivy

**Step 3: Install MSAViz.**
::

$ pip install msaviz

If you're viewing this on testpypi.python.org, try this instead:
::

$ pip install -i https://testpypi.python.org/pypi msaviz

Quickstart Guide
----------------
To begin using MSAViz, start the conda environment (if on an STScI Mac, see above) and run the package:
::

$ source activate msaviz
$ msaviz

**File Select Screen**

When the interface has opened, complete the following steps on the file select screen:

1. Choose a working directory (the included ``test/`` directory is the default).
2. Select a filter & grating combination using the dropdown.
3. Choose an MSA config file which has been exported from APT.
4. Press `Parse` and wait while the MSA config file is parsed and the wavelengths are calculated.
5. Once this is complete, press `Show the Spectrum Display!` to view the visualization.

.. image:: https://github.com/gkanarek/msaviz/blob/master/screenshots/fileselect_screen.png

**Spectrum View Screen**

On the spectrum view screen, the spectrum from each shutter is displayed on a representation of the two detectors. A colorbar at the bottom of the screen shows the displayed wavelengths. 

To zoom & pan the display, simulate a multi-touch with a right-click (which will leave a small red dot on the screen, which is the focus point for zooming), then click and drag to increase or decrease zoom. After zooming in, click and drag to pan in any direction. You can zoom back out with the same method as zooming in.

Click `Export...` and choose a filename to export an ascii table showing the open shutters and their wavelength bounds on each detector (including the predicted lost wavelengths due to the detector gap).

Click `Save...` and choose a filename to export a PNG image of the spectrum display. This function does not work when the display is zoomed.

Click `Shutters...` to move to the shutter view Screen (see below), or `Back` to return to the file select Screen.

.. image:: https://github.com/gkanarek/msaviz/blob/master/screenshots/spectrumview_screen.png

**Shutter View Screen**

On the shutter view screen, a map of the four MSA quadrants is shown, indicating all closed (black), open (orange), inactive (grey), and stuck-open (red) shutters. You can zoom & pan this display in the same way as the spectrum view screen.

Click on any open shutter to select or deselect it; selected shutters turn cyan, and cause the corresponding spectrum on the spectrum view screen to be highlighted. Note that the individual shutters in an MSA slitlet must be selected individually if you want to highlight all of the associated spectra.

Click `Save...` and choose a filename to export a PNG image of the shutter display. This function does not work when the display is zoomed. Click `Back` to return to the spectrum view screen.

.. image:: https://github.com/gkanarek/msaviz/blob/master/screenshots/shutterview_screen.png

Programmatic API
----------------
The MSAViz package exposes an object and two functions to be used from the python command line, or from other python scripts. They can be imported like so:
::

>>> from msaviz import MSA, calculate_wavelengths, parse_msa_config

The `MSA` class provides a direct interface for predicting the wavelengths which will fall on each detector for a given shutter. Once it has been instantiated with paired filter and grating name strings, it can be called with the Quadrant, Row, and Column coordinates and an NRS number. *Note that these are 0-based indexing, so you must subtract 1 from the usual coordinates and NRS number.*
::

>>> msa = MSA('f070lp', 'g140h')
>>> wavelengths = msa(0, 174, 15, 1) # Quadrant 1, Column 175, Row 16, NRS2
>>> wavelengths.shape
(2048,)


The `calculate_wavelengths` function replicates the Export function of the spectrum view screen, returning an `astropy.table.QTable` with the wavelength bounds on each detector for each open shutter.
::

>>> wavelength_table = calculate_wavelengths('msa_config1.csv', 'f170lp', 'g235m', outfile='msa_config1_f170lp_g235m_wave.txt')

This function accepts three positional arguments and one optional keyword argument: 

- ``config_file``, the path to an MSA config file (string)
- ``filtername``, the name of one of the NIRSpec filters (string)
- ``gratingname``, the name of one of the NIRSpec gratings, which must be paired with the given filter (string)
- ``outfile``, the path to an output file where the resulting table will be written (string, optional)

Finally, `parse_msa_config` is a utility function which parses an MSA config file and returns a dictionary of shutter coordinates and status. By default, only open and stuck-open shutters are included, and the status is a boolean value (True if the shutter is stuck-open, False if it is simply open); however, by setting `return_all=True`, the function returns a dictionary of every shutter in the MSA, and the status is a single character code ('x' is inactive, 's' is stuck-open, '1' is open, and '0' is closed).
::

>>> for (q,i,j), stuck in parse_msa_config('msaviz/test/single_shutter.csv').items():
...     print('Q {}, I {}, J {} - {}'.format(q+1, i+1, j+1, stuck))
... 
Q 3, I 240, J 61 - True
Q 1, I 177, J 121 - True
Q 1, I 35, J 30 - False
Q 3, I 328, J 132 - True
Q 2, I 244, J 46 - True
Q 1, I 176, J 121 - True
Q 2, I 53, J 43 - True
Q 3, I 242, J 69 - True
Q 3, I 44, J 155 - True
Q 2, I 196, J 50 - True
Q 2, I 27, J 94 - True
Q 3, I 331, J 104 - True
Q 3, I 144, J 42 - True
Q 1, I 105, J 169 - True
Q 1, I 104, J 169 - True
Q 1, I 175, J 121 - True
Q 1, I 38, J 25 - True
Q 2, I 235, J 40 - True
Q 2, I 321, J 117 - True
Q 2, I 26, J 94 - True
Q 3, I 307, J 139 - True
Q 3, I 330, J 35 - True
Q 4, I 351, J 156 - True



 