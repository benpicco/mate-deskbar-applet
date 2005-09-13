#!/bin/sh

python `pkg-config pygtk-2.0 --variable=codegendir`/h2def.py \
ephy-icon-entry.h \
> iconentry.defs

