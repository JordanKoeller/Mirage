
Getting Started with Mirage
===========================

Mirage has three main use cases:

* Visualizing gravitationally (micro)lensed quasars.
* Computing large-scale simulations of microlensed quasars.
* Analyzing results of large-scale simulations.

We will explore all three of these cases momentarily. Crucially to each of these uses, however, is an understanding of how |Mirage| works, how to choose the appropriate execution context, and how to specify a lensed system.

How Mirage Works
----------------

At its core, |Mirage| is essentially a massive ray-tracer. To simulate gravitational lensing, |Mirage| sends a bundle of rays from the observer, through the gravitational lens, and computes where the rays intersect the lens plane. The lensed image of a quasar can then be rendered by computing which rays successfully connect the observer to the quasar. As such, the important information |Mirage| needs to simulate a quasar are:

* Distance to the lensing object and quasar
* Mass profile of the lensing object
* Quasar's radius and location relative to the center of the lensing object
* How many rays to compute
* The angular size of the bundle of rays to compute.

Specifying the Execution Context
--------------------------------

TODO

Specifying a Lensed System
--------------------------

|Mirage| uses the |Parameters| class to specify a lensed system. This object bundles together information to describe a lens, a quasar, and the bundle of rays to send. While the |Parameters| class can be instantiated directly from its constructor, usage of the |ParametersView| is highly recommended. The |ParametersView| opens a new GUI window with text boxes and such to input all the parameters |Mirage| requires to construct a lensed system. ::

	>>> import mirage
	>>> param_view = mirage.getParametersView()
	# After you have configured the parameters in the GUI window that opens up,
	# param_view.get_parameters() returns the constructed Parameters object.
	>>> parameters = param_view.get_parameters()

From the created |ParametersView|, once you have specified the system, you can save it to a file or return it by calling :func:`get_parameters <mirage.views.ParametersView.ParametersView.get_parameters>` on the ``param_view`` object.

.. note:: If you have a |Parameters| instance or a file containing a |Parameters| instance, you can pass that to :func:`mirage.getParametersView` to pre-load the parameters.

Alternatively, a |Parameters| instance can be loaded in from a |Parameters| file specification. To read more about file specifications, see :doc:`Reading and Writing Simulation Files <filespecification>`.

.. note:: |Mirage| uses two different objects to specify a macro-lensing versus micro-lensing simulation. The |Parameters| object is only suitable for macro-lensing simulations. To simulate a micro-lensing system, you must construct a |MicrolensingParameters| object by also supplying |Mirage| with the position of the macro-image you want to model (relative to the center of the lensing galaxy), The dimensions of the source plane to consider, and a scheme for populating the region with stars. If you are using the |ParametersView|, it includes options to specify a |MicrolensingParameters| object. Otherwise, the |Parameters| and |MicrolensingParameters| can be converted back and forth with the :func:`to_microParams <mirage.parameters.Parameters.Parameters.to_microParams>` and :func:`to_macroParams <mirage.parameters.Parameters.MicrolensingParameters.to_macroParams>` methods.
	
	Note that |MicrolensingParameters| is a subtype of |Parameters|. Thus, for the sake of these tutorials, a |Parameters| object can also be a |MicrolensingParameters| object, unless otherwise specified.

Visualizing Gravitationally Lensed Systems
------------------------------------------

Once you have a |Parameters| object made to specify your system, it can be visualized with a |LensView| object. The |LensView| object is another GUI window that provides |Mirage| a canvas to render lensed quasars to. ::
	
	>>> lensView = mirage.getLensedView(parameters)

.. note:: If you want to explore lensed system parameters to see how the image changes, you can bind a |ParametersView| to the |LensView| by passing it into the :func:`getLensedView <mirage.getLensedView>` function. Every time you refresh the |LensView|, it will then display the image of the newest set of parameters.

From the |LensView|, you can specify the quasar location as well as give it a velocity for animations. Note that these data are not stored in the |Parameters| object. If you want to save the animation information, you can get an |AnimationSimulation| instance from the |LensView| by accessing the :func:`simulation <mirage.views.LensView.LensView.simulation>` attribute on the ``lensView``.

Running Large-scale simulations
-------------------------------

To set up large-scale simulations, |Mirage| needs some more information than what a |Parameters| object contains. This extra information can be added on to a |Parameters| object by wrapping up an instance in a |Simulation| object. Similarly to constructing the |Parameters| object, this can be done programatically, by loading in from a file, or by wrapping the |ParametersView| instance in a |SimulationView| decorator. This will add some extra text boxes and options onto the GUI window associated with the |ParametersView|. ::
	
	# Assuming the ParametersView object was defined as above.
	>>> from mirage.views import SimulationView
	>>> simulation_view = SimulationView(param_view)

From the |SimulationView| you can specify if you want to compute light curves, magnification maps, and locate caustic lines, as well as provide a name and description for the simulation. Lastly, you can specify how many trials to compute and what parameters to vary between trials.

.. seealso:: To learn more about setting up simulations, see :doc:`Parameters and Simulation objects <paramSimObj>`.

Once you have the simulation configured as desired, you will need to save the |Simulation| object to a `.sim` file either programatically (see :doc:`filespecification`) or from the |SimulationView| menu. ::
	
	>>> simulation = simulation_view.get_simulation()
	>>> from mirage.io import save_simulation
	>>> save_simulation(simulation,"filename.sim")

Finally, to calculate the simulation, use the :func:`run_simulation <mirage.run_simulation>` function. ::
	
	>>> from mirage import run_simulation
	>>> run_simulation("filename.sim","result_file")

This function will read the simulation specification inside ``filename.sim`` and save the results to the file ``result_file`` with the `.res` file extensions attached if not present already.

.. warning:: If `result_file.res` already exists in the file system, this method will overwrite `result_file.res`!

Analyzing Simulation Results
----------------------------

The |lens_analysis| module contains all of the main tools for analyzing simulation results. As such, it is highly recommended that you spend some time exploring the |lens_analysis| API to learn what you can do. That being said, I will show a few of the main core analysis functionalities. 

For the purpose of this tutorial, we assume you have ran a simulation saved to `results.res` with the following details:

* 3 trials - each with differently sized simulated quasars
* A magnfication map was computed for each trial
* 10 light curves were computed for each trial.

The main entry point for analyzing results is via the |Result| object. One can be constructed via the :func:`load <mirage.lens_analysis.load>` function in |lens_analysis| ::
	
	>>> from mirage import lens_analysis as la
	# This constructs a Result object.
	>>> result = la.load("results.res")
	# Trials can then be selected by indexing into the Result object.
	>>> trial1 = result[0]
	>>> trial2 = result[1]
	>>> trial3 = result[2]

In addition to the |Result| object, the |Trial| object is also crucial to analyzing results. The |Trial| object has methods for accessing the three result types. ::
	
	>>> mag_map = trial1.magmap
	>>> lightcurves = trial1.lightcurves

To visualize magnification maps, the |MagmapView| object is useful. It can be constructed directly from the |lens_analysis| package by supplying the |Trial| containing the map you want to visualize. ::
	
	>>> view = la.show_map(trial1)

.. note: ::
	You can also construct the view and |Trial| object together by passing the result's filename and trial number you want. ::
		
		>>> view, trial = la.show_map("results.res",0)


With the |MagmapView|, you can visualize magnification maps, save the map as an image file, or click and drag a line through the magnification map to render an approximate light curve for that path. For more information, see the |MagmapView| API listing.

To analyze light curves, |lens_analysis| supplies the |LightCurveBatch| for handling light curve information. With the |LightCurveBatch|, you can isolate caustic crossings, apply smoothing filters, or just plot some (or all) enclosed light curves. A few example actions are given below. ::
	
	#First, get the LightCurveBatch object and call it lightcurves1
	>>> lightcurves1 = trial.lightcurves

	#smooth with a wiener filter and return a new LightCurveBatch
	>>> smoothed_batch = lightcurves1.smooth_with_window(9)

	# pull out a single lightcurve as a LightCurve object
	>>> lc1 = smoothed_batch[0]
	
	# overlay all of the plots on a single Matplotlib figure
	>>> from matplotlib import pyplot as plt
	>>> for x_axis, curve in lightcurves1.plottables(): plt.plot(x_axis, curve)

In addition to the methods available on a |LightCurveBatch|, any method available on a |LightCurve| can be called on each |LightCurve| inside a |LightCurveBatch| with the :func:`map <mirage.lens_analysis.LightCurves.LightCurveBatch.map>` and :func:`apply <mirage.lens_analysis.LightCurves.LightCurveBatch.apply>` 
methods. ::
	
	#Pulls out all caustic events from each curve, flattens them all together, and places into a new LightCurveBatch
	>>> all_caustic_events = lightcurves1.map(lambda curve: curve.get_events(threshold=1.2,isolate_events=True))
	# We then smooth all the events.
	>>> smoothed_caustic_events = all_caustic_events.smooth_with_window(9)

	# The apply method works the same way but returns a list rather than another LightCurveBatch, making it more versatile.
	#As an example, we compute the length of each event and put into a list.
	>>> event_lengths = all_caustic_events.apply(lambda curve: curve.length)

As a final example, if you are working with magnification map data as well as light curve data, you can overlay them in the |MagmapView|. ::
	
	>>> view, trial = la.show_map("results.res",0)
	>>> lightcurve = trial.lightcurves[0]
	>>> view.show_curve(lightcurve)

Again, it is highly recommended that you explore the |lens_analysis| API, especially the |Result|, |Trial|, |LightCurve|, and |LightCurveBatch| objects.


