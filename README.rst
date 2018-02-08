====================================
JWST MSA Spectral Visualization Tool
====================================

The JWST MSA Spectral Visualization Tool (MSAViz) was designed to visualize the layout of MOS spectra on the NIRSpec detectors, given a particular MSA shutter configuration (exported from APT), filter, and disperser. This gives the user a means of identifying problematic shutters, for which wavelengths of interest which may fall near or in the detector gap during observations.

Introduction
------------

A proposal for a MOS observation with NIRSpec will often intend to observe a particular wavelength region of interest, depending on the science case of the proposal. A user who designs such an observation with APT and the MSA Planning Tool (MPT) will need to identify the wavelengths that will be obtained from spectra observed with a particular MSA configuration, to determine whether the region of interest is likely to be included in the spectra for the associated targets, or if the region instead falls in the detector gap (or beyond the bounds of the detector entirely) for one or more targets.

The NIRSpec instrument model (calibrated from ground-test data) can be used to establish a WCS solution that assigns a wavelength to each pixel on both detectors. Doing so for each configuration considered during a proposal would be extremely time-consuming and computationally expensive. This tool provides an interface to a parameterized prediction algorithm which streamlines these calculations, and visualizes them in an intuitive way for the user's exploration.

Installation with Anaconda and pip
----------------------------------

It is strongly recommended to use MSAViz in conjunction with the `Anaconda Python distribution <https://www.continuum.io/anaconda-overview>`_, which greatly simplifies the installation of dependencies. These instructions assume that Anaconda has been successfully installed.

NOTE: these instructions have not been tested on Windows.

**Step 1: Create a new conda environment.**
::

    $ conda create --name msaviz pip numpy scipy astropy cython
    $ source activate msaviz

You can specify a particular python version when creating the conda environment with ``python=2`` or ``python=3`` or something similar; otherwise, it will default to the python version of your Anaconda distribution.

If you prefer to use msaviz in an existing conda environment (which already has the dependencies installed), feel free to do so. Just skip the ``conda create`` line, and then  ``$ source activate <your_environment>`` instead of ``$ source activate msaviz``. However, make sure that your environment has `sufficiently-new versions <https://github.com/spacetelescope/msaviz/blob/master/requirements.txt>`_ of the dependent packages.

**Step 2: Install Kivy and its dependencies.**

*Windows:*
::

    $ conda install docutils pygments
    $ pip install pypiwin32 kivy.deps.sdl2 kivy.deps.glew
    $ pip install kivy
    $ garden install filebrowser

*Mac:*

To install the Kivy dependencies, you will need to have the `Homebrew package manager <https://brew.sh/>`_ installed. If you are trying to install this on a Mac owned by STScI, you will likely run into problems when attempting to install Homebrew. I have included the ``install_homebrew.sh`` script `here <https://github.com/spacetelescope/msaviz/blob/master/install_homebrew.sh>`_, to handle this task. Once you run the script, and follow the instructions at the end, simply do ``$ brew_activate`` in advance any time you activate your conda environment.
::

    $ brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer
    $ USE_OSX_FRAMEWORKS=0 pip install -I --no-cache-dir --no-binary all kivy
    $ garden install filebrowser

Note that (at the time these instructions were written) the current official release of Kivy causes an error on installation due to a recent version of SDL2. If this error occurs, install the dev version of Kivy instead, using this command:
::

    $ USE_OSX_FRAMEWORKS=0 pip install -I --no-cache-dir --no-binary all http://github.com/kivy/kivy/archive/master.zip

**Step 3: Install MSAViz.**
::

    $ pip install msaviz

If you're viewing this on testpypi.python.org, try this instead:
::

    $ pip install -i https://testpypi.python.org/pypi msaviz

Quickstart Guide
----------------
MSAViz requires an MSA configuration file to be exported from APT.

**Export an MSA Config file from APT**

In terms of the proposal creation workflow, the use of MSAViz occurs once the MSA Planning Tool (MPT) has generated plans for a given observation. To export an MSA config file that can be parsed by MSAViz, follow these steps:

1. Open the JWST proposal with APT, and navigate to the specific observation in the proposal's hierarchical menu. Press on the arrow next to the desired MSA plan, which will open the MPT.

.. figure:: https://github.com/spacetelescope/msaviz/blob/master/screenshots/APT1.png
   :alt: APT screenshot #1

   Screenshot of an example JWST proposal in APT. Once the desired plan has been selected, press the arrow button next to the drop-down menu (indicated with an orange circle) to enter the MSA Planning Tool.

2. On the Plans tab of the MPT, choose a pointing to visualize with MSAViz, and press the Show button for that pointing, which will open the Shutter View window.

.. figure:: https://github.com/spacetelescope/msaviz/blob/master/screenshots/APT2.png
   :alt: APT screenshot #2

   Screenshot of an example JWST proposal in APT. Press the Show button (indicated with an orange circle) to open the Shutter View window for the desired pointing.

3. In the Shutter View window, press Export to CSV, and save the configuration file to your working directory. MSAViz will save any output from the tool into the same directory by default (see the File Select Screen section, below).

.. figure:: https://github.com/spacetelescope/msaviz/blob/master/screenshots/APT3.png
   :alt: APT screenshot #3

   Screenshot of an example JWST proposal in APT. Press the Export to CSV button (indicated with an orange circle) to export the MSA configuration file for MSAViz.

**Start MSAViz application**
To begin using MSAViz, start the conda environment (if on an STScI Mac, activate Homebrew before the environment; see above) and run the package:
::

    $ source activate msaviz
    $ msaviz

**File Select Screen**

When the interface has opened, complete the following steps on the file select screen:

1. Choose a working directory (the included ``test/`` directory is the default).
2. Select a filter & grating combination using the dropdown.
3. Choose an MSA config file which has been exported from APT.
4. Press ``Parse`` and wait while the MSA config file is parsed and the wavelengths are calculated.
5. The ``Display spectra from stuck-open shutters`` checkbox will toggle whether or not spectra from stuck-open shutters will be included in the visualization.
5. Once this is complete, press ``Show the Spectrum Display!`` to view the visualization.

.. figure:: https://github.com/spacetelescope/msaviz/blob/master/screenshots/fileselect_screen.png
   :alt: File Select Screen
   
   Screenshot of File Select screen from MSAViz.
   
**Spectrum View Screen**

On the spectrum view screen, the spectrum from each shutter is displayed on a representation of the two detectors. A colorbar at the bottom of the screen shows the displayed wavelengths. 

To zoom & pan the display, simulate a multi-touch with a right-click (which will leave a small red dot on the screen, which is the focus point for zooming), then click and drag to increase or decrease zoom. After zooming in, click and drag to pan in any direction. You can zoom back out with the same method as zooming in.

Click ``Check Wavelength`` to open the associated dialog (see below).

Click ``Export...`` and choose a filename to export an ascii table showing the open shutters and their wavelength bounds on each detector (including the predicted lost wavelengths due to the detector gap).

Click ``Save...`` and choose a filename to export a PNG image of the spectrum display. This function does not work when the display is zoomed.

Click ``Shutters...`` to move to the shutter view Screen (see below), or ``Back`` to return to the file select Screen.

.. figure:: https://github.com/spacetelescope/msaviz/blob/master/screenshots/spectrumview_screen.png
   :alt: Spectrum View Screen
   
   Screenshot of Spectrum View Screen from MSAViz.

**Check Wavelength Dialog**

On the Check Wavelength dialog, you can identify where a particular wavelength or set of wavelengths will likely fall with respect to the two detectors, for all open shutters at once. Enter a wavelength in the text box and press ``Submit`` to add that wavelength to the list.

Once at least one wavelength has been entered, a scrollable table will appear below, showing the list of open shutter coordinates, and where each wavelength will likely fall for each shutter.  This will also warn if a particular wavelength will fall near the edge of one of the two detectors for a given shutter, since that wavelength may fall off of that detector during the actual observation.

Click ``Save to File`` and select a filename and path to save the table of wavelengths to a file. Click ``Done`` to go back to the spectrum view screen.

.. figure:: https://github.com/spacetelescope/msaviz/blob/master/screenshots/checkwavelength_dialog.png
   :alt: Check Wavelength Dialog
   
   Screenshot of Check Wavelength Dialog from MSAViz.

**Shutter View Screen**

On the shutter view screen, a map of the four MSA quadrants is shown, indicating all closed (black), open (orange), inactive (grey), and stuck-open (red) shutters. You can zoom & pan this display in the same way as the spectrum view screen.

Click on any open shutter to select or deselect it; selected shutters turn cyan, and cause the corresponding spectrum on the spectrum view screen to be highlighted. Note that the individual shutters in an MSA slitlet must be selected individually if you want to highlight all of the associated spectra.

Click ``Find...`` to enter a set of shutter coordinates (with the option to select from a dropdown of all shutters which are currently selected shutters), and then automatically zoom and pan to center on the chosen shutter.

Click ``Save...`` and choose a filename to export a PNG image of the shutter display. This function does not work when the display is zoomed. Click ``Back`` to return to the spectrum view screen.

.. figure:: https://github.com/spacetelescope/msaviz/blob/master/screenshots/shutterview_screen.png
   :alt: Shutter View Screen
   
   Screenshot of Shutter View Screen from MSAViz

Programmatic API
----------------
The MSAViz package exposes two classes and three functions, which may be used from the python command line, or from other python scripts. They can be imported like so:
::

>>> from msaviz import MSA, MSAConfig #classes
>>> from msaviz import check_wavelengths, parse_msa_config, wavelength_table # functions

The ``MSA`` class is the low-level construct used to calculate pixel-to-wavelength mappings for a given filter+disperser combination. This class will generally not be used, and is included for completeness; see the module documentation for details on its invocation and use. 

The ``MSAConfig`` class includes methods to parse an MSA config file, and calculate wavelengths and useful statistics based on the open shutters for that configuration. Instantiate with paired filter and disperser name strings, as well as the path to an MSA config file (a .csv file exported from APT). The filter & disperser can be changed with ``MSAConfig.update_instrument()``, and the config file can be changed with ``MSAConfig.update_config()``.

- The ``MSAConfig.wavelength()`` method accepts one or more Quadrant, Row, and Column coordinates, and returns a numpy array of wavelength values at each pixel on each detector. *Note that these are 0-based indexing, so you must subtract 1 from the usual coordinates and NRS number.* 
- The ``MSAConfig.wavelength_table`` property returns an ``astropy.table.QTable`` instance containing the wavelength ranges for each shutter on each detector.
- The ``MSAConfig.write_wavelength_table()`` method writes the above table to an ascii file.
- The ``MSAConfig.verify_wavelength()`` method accepts one or more target wavelengths, and returns a table of flags for each shutter indicating the location of the target wavelengths with respect to the detectors.

::

    >>> msa = MSAConfig('f070lp', 'g140h', 'test/single_shutter.csv')
    >>> wavelengths = msa.wavelength(0, 174, 15) # Quadrant 1, Column 175, Row 16
    >>> wavelengths.shape
    (2, 1, 2048)
    >>> msa.write_wavelength_table('single_shutter_table.txt')
    >>> table = msa.verify_wavelength([1.22, 1.84, -19, 1000], verbose=True)
    Trimming target wavelengths outside the filter transmission range...
    Target wavelength 1.22 micron:
     -> falls on NRS2 for 100.0% of shutters
    >>> print(table)
    Quadrant Column Row 1.220 micron
    -------- ------ --- ------------
           1     35  30            2


If the full functionality of the ``MSAConfig`` class isn't required, the ``calculate_wavelengths`` function accepts a ``config_file``, ``filtname``, and ``dispname``, and returns the wavelength table as described above, and optionally writes the table to a given file.
::

    >>> wavelength_table = calculate_wavelengths('msa_config1.csv', 'f170lp', 'g235m', outfile='msa_config1_f170lp_g235m_wave.txt')
    
Similarly, the ``check_wavelengths`` function accepts a list of target wavelengths, as well as a ``config_file``, ``filtname``, and ``dispname``, and uses ``MSAConfig.verify_wavelength`` to return (and optionally write to a given file) a table of wavelength flags for each open shutter.
::

    >>> flag_table = check_wavelengths([1.22, 1.84, -19, 1000], 'msa_config1.csv', 'f170lp', 'g235m', outfile='msa_config1_f170lp_g235m_flags.txt')

Finally, ``parse_msa_config`` is a utility function which parses an MSA config file and returns a dictionary of shutter coordinates and status. By default, only open and stuck-open shutters are included, and the status is a boolean value (True if the shutter is stuck-open, False if it is simply open); however, by setting ``open_only=False``, the function returns a dictionary of every shutter in the MSA, and the status is a single-character code ('x' is inactive, 's' is stuck-open, '1' is open, and '0' is closed). ::

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