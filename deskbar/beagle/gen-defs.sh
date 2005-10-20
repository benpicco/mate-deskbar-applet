#!/bin/sh

python `pkg-config pygtk-2.0 --variable=codegendir`/h2def.py \
`pkg-config --variable=includedir libbeagle-0.0`/libbeagle/beagle/*.h \
> _beagle.defs.new

