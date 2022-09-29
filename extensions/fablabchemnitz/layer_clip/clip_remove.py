#!/usr/bin/env python3

# Copyright (c) 2012 Stuart Pernsteiner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import inkex

class RemoveClipEffect(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

    def effect(self):
        vals = list(self.svg.selected.values())
        if len(vals) == 0:
            inkex.errormsg(_("Error: No selection"))
            exit(1)
        path = vals[0]
        layer = path.getparent()
        if layer.attrib.has_key('clip-path'):
            del layer.attrib['clip-path']

        # Update layer name
        label_attr = inkex.addNS('label', 'inkscape')
        if layer.get(inkex.addNS('groupmode','inkscape')) != 'layer':
            inkex.errormsg(_("Error: Selection's parent is not a layer"))
            exit(1)
            
        layer_label = layer.get(label_attr)
        if layer_label[-4:] == " (C)":
            layer.set(label_attr, layer_label[:-4])


# Create effect instance and apply it.
RemoveClipEffect().run()


