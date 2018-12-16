# Mirage2
A simulator for modeling microlensing of gravitationally lensed quasars of arbitrary radius.




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
