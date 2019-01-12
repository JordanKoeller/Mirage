Getting Started with Mirage
===========================

Mirage has three main use cases:

* Visualizing gravitationally (micro)lensed quasars.
* Computing large-scale simulations of microlensed quasars.
* Analyzing results of large-scale simulations.

We will explore all three of these cases momentarily. Crucially to each of these uses, however, is an understanding of how |Mirage| works, how to choose the appropriate execution context, and how to specify a lensed system.

How Mirage Works
================

At its core, |Mirage| is essentially a massive ray-tracer. To simulate gravitational lensing, |Mirage| sends a bundle of rays from the observer, through the gravitational lens, and computes where the rays intersect the lens plane. The lensed image of a quasar can then be rendered by computing which rays successfully connect the observer to the quasar. As such, the important information |Mirage| needs to simulate a quasar are:

* Distance to the lensing object and quasar
* Mass profile of the lensing object
* Quasar's radius and location relative to the center of the lensing object
* How many rays to compute
* The angular size of the bundle of rays to compute.

Specifying the Execution Context
=================================

TODO

Specifying a Lensed System
==========================

|Mirage| uses the |Parameters| class to specify a lensed system. This object bundles together information to describe a lens, a quasar, and the bundle of rays to send. While the |Parameters| class can be instantiated directly from its constructor, usage of the |ParametersView| is highly recommended. 