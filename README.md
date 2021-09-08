# Mirage2
A simulator for modeling microlensing of gravitationally lensed quasars of arbitrary radius.

Program documentation may be found [here](https://cs.trinity.edu/~jkoeller/Mirage)

Paper accompanying its release detailing the physics [here](https://digitalcommons.trinity.edu/physics_honors/10/).

Conference papers detailing the implementation using Apache Spark may be found [here](https://www.semanticscholar.org/paper/Applications-of-Apache-Spark-TM-for-Numerical-Koeller-Lewis/5acabc9a608872d324934a2ec833723a8c723057) and [here](https://www.semanticscholar.org/paper/Using-Apache-Spark-TM-for-Distributed-Computation-a-Koeller-Lewis/0ef96e757a4e7da8424e903f834a9a636051a4de?p2df).



# Installation Details:


MINIMUM REQUIREMENTS:

Most dependencies of mirage will be automatically downloaded during configuration. However, a few tools will be needed to get started:

  - Python 3
  - Python Header files (python-dev)
  - Java 8
  - Scala Build Tool (sbt) (optional)


To install Mirage, run the following commands:

`bash configure`
`make`

If you are a developer and wish to edit the source code, you will need cython, python developer tools, and sbt installed. You can then re-compile the entire project via

`make all`

Lastly, if you would like to make locally hosted documentation and have the sphinx documentation engine installed, running the command

`make docs`

will generate html in the docs/build directory.
