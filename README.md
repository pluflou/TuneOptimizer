# TuneOptimizer
Automated algorithm using cothread module and EPICS to optimize tune through SECAR

This is still under construction. Upon completion, the code will:
1. Communicate with EPICS through caget and caput to move/read devices along the beamline
2. Analyze the data from the viewer (see [viewer repo](https://github.com/pluflou/Viewer-Image-Analysis)) to locate beam
3. Use that data plus readings from cups and apertures to decide which element to modify/which direction to go in order to converge towards the best tune
4. The optimal tune is reached once the method minimizes the aperture readings while maximizing transmission (readings on cups), and keeping the beam on the viewer from steering more than ~5 mm
