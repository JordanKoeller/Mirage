.. lensim documentation master file, created by
   sphinx-quickstart on Thu Jan  4 02:00:23 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Mirage's documentation!
===============================================

Mirage is a program for simulating gravitationally lensed 
quasars, on both the macrolensing scale as well as the
microlensing scale. With Mirage, you can specify the parameters
of a quasar being gravitationally lensed by a galaxy between the observer
and quasar, and then generate animations of the lensed system,
light curves, and magnification maps for comparison to physical data.

Mirage simulates gravitationally lensed systems through a ray-tracing 
approach. Simply put, it traces a specified set of paths of light through
the lensing galaxy and discovers which paths successfully connect the observer to the quasar.

Mirage is primarily written in Python, to allow for easy manipulation of 
the program as well as data analysis through Python's interpreter. The
calculation engine, however, gives you options to specify where the heavy lifting occurs. Mirage may be ran locally using a C/C++ implimentation that can take advantage of graphics processors for the ray-tracing, or may be ran on a computational cluster through the Apache Spark (TM) data analytics framework.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   gettingstarted
   dependencies
   documentation
   publications 
   licensing
   citing

What Mirage can do
==================

Mirage is a program initially developed for analyzing light curves from gravitationally lensed quasars. That being said, it is a full-fledged, robust simulator of astrophysical gravitationally lensed objects. Built-in functionality includes:

* Specifying a lensing galaxy as a singular isothermal sphere with external shear, with a specified percentage of the galaxy's mass simulated as individual stars versus continuous dark matter.
* Simulating quasar source objects of arbitrary radius.
* Generating images of gravitationally lensed systems.
* Rendering animations of lensed images as a quasar moves.
* Creating high-resolution magnification maps, exportable to FITS files.
* Generating random or pre-specified light curves, simulating relative motion between the quasar and galaxy.
* Simulating light curves through a random starfield where the stars have random motion.
* Bulk generation of magnification maps and light curves with specified variables changed for discovering correlation.
* Tools for statistical analysis of magnification maps and light curves, as well as visualization and manipulation.
* Open source object-oriented code, written to be easily extensible for other purposes.

