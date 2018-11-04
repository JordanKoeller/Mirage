#!/bin/bash

pushd mirage
python setup.py build_ext --inplace
popd
