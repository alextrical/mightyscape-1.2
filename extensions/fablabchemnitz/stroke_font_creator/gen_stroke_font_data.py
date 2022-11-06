#!/usr/bin/env python3

'''
Inkscape extension to generate the data for the stroke font glyphs 
designed in the current SVG. The current SVG must be generated with the
'Create Font Design Template' extension

The data generated by this effect is used by the 'Render Text' extension, 
to render text with the selected stroke font.

Copyright (C) 2019  Shrinivas Kulkarni

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

import inkex, sys, os, re, math
from bezmisc import bezierlengthSimpson

sys.path.append(os.path.dirname(os.path.abspath(__file__))) 
from stroke_font_common import InkscapeCharData, CommonDefs, runEffect, getCubicSuperPath, \
    InkscapeCharDataFactory, syncFontList, getAddFnTypes, getParsedPath, getTransformMat, \
    applyTransform, getCubicBoundingBox, formatSuperPath, getCubicLength, getCubicSuperPath
from stroke_font_manager import FontData, xGlyphName, xAscent, \
    xDescent, xCapHeight, xXHeight, xSpaceROff, xFontId, xSize, getDefaultExtraInfo


def getNearestGuide(guides, minVal, coIdx, hSeq = None):
    if(guides == None or len(guides) == 0):
        return None, None
        
    if(hSeq != None):
        guides = [g for g in guides if int(g[0].get(CommonDefs.idAttribName).split('_')[1]) == hSeq]

    if(len(guides) == 1):
        return guides[0]
        
    for i, guide in enumerate(guides):
        pp = guide[1]
        #pp format [['M',[x1,y1]],['L',[x2,y2]]]
        diff = abs(pp[0][1][coIdx] - minVal)
        
        if(i > 0 and diff > minDiff):
            return guides[i-1]
            
        minDiff = diff
        
    return guides[-1]
    
def getFontSizeFromGuide(pp, vgScaleFact):    
    #pp format [['M',[x1,y1]],['L',[x2,y2]]]
    lHeight = abs(float(pp[1][1][1]) - pp[0][1][1])
    return round(lHeight / vgScaleFact, 2)
    
#Apply transform attribute (only straight lines, no arcs etc.)
def transformedParsedPath(elem):
    pp = getParsedPath(elem.get('d'))
    return pp

    # Following bloc takes care of the special condition where guides are transformed
    # TODO: Make it working for 1.0

    # ~ try:
        # ~ transf = elem.get('transform')
        # ~ mat = parseTransform(transf)
        
        # ~ #pp format [['M',[x1,y1]],['L',[x2,y2]]]
        # ~ for dElem in pp:
            # ~ for i in range(1, len(dElem)):
                # ~ param = dElem[i]
                # ~ t1 = [[param[x], param[x+1]] for x in range(0, len(param), 2)]
                # ~ for t1Elem in t1:
                    # ~ simpletransform.applyTransformToPoint(mat, t1Elem)
                # ~ dElem[i] = [x for l in t1 for x in l]
        # ~ elem.set('d', simplepath.formatPath(pp))        
    # ~ except:
        # ~ #Don't break
        # ~ pass
    
    # ~ return pp

def updateFontData(strokeFontData, glyphPathElems, hGuides, lvGuides, rvGuides, rightOffsetType):    
    for elem in glyphPathElems:
        char = elem.get(CommonDefs.idAttribName)
        path = getCubicSuperPath(elem.get('d'))

        glyphName = elem.get(xGlyphName)
        if(glyphName == None): glyphName = char
        
        #Just in case...
        transf = elem.get('transform')
        mat = getTransformMat(transf)
        applyTransform(mat, path)

        xmin, xmax, ymin, ymax = getCubicBoundingBox(path)
        
        #Nearest to the bottom (ymax)
        hg = getNearestGuide(hGuides, ymax, 1)
        hseq = int(hg[0].get(CommonDefs.idAttribName).split('_')[1])
        hgp = hg[1]
        #hgp format: [['M',[x1,y1]],['H',[x2,y2]]]
        hgY = hgp[0][1][1]
        
        #Nearest to the left edge (xmin)
        lvg = getNearestGuide(lvGuides, xmin, 0, hseq)            
        lvgp = lvg[1]
        #lvgp format: [['M',[x1,y1]],['V',[x2,y2]]]
        lvgX = lvgp[0][1][0]
        
        rvgX = None
        if(rvGuides != None and len(rvGuides) > 0):
            #Nearest to the right edge (xmax)
            rvg = getNearestGuide(rvGuides, xmax, 0, hseq)
            rvgp = rvg[1]
            #rvgp format: [['M',[x1,y1]],['V',[x2,y2]]]
            rvgX = rvgp[0][1][0]
        
        npath = getCubicSuperPath()
        
        maxLenSp = None
        maxSpLen = 0
        
        for subpath in path:
            nsub = []
            spLen = 0
            for seg in subpath:
                nseg = []
                for pt in seg:
                    x = round(pt[0] - lvgX, 2)
                    y = round(pt[1] - hgY, 2)
                    nseg.append([round(x, 4), round(y, 4)])
                nsub.append(nseg)
            npath.append(nsub)

            #Calculate length only if needed
            if(rightOffsetType == 'lastNode'):
                spLen = getCubicLength(npath)
                if(spLen > maxSpLen):
                    maxSpLen = spLen
                    maxLenSp = subpath
        
        if(rightOffsetType == 'lastNode'):
            lastNode = maxLenSp[-1][-1]
            rOffset = lastNode[0] - lvgX
        elif(rvgX != None):
            rOffset = rvgX - lvgX
        else:
            rOffset = xmax - lvgX

        rOffset = round(rOffset, 2)

        pathStr = formatSuperPath(npath)
        strokeFontData.updateGlyph(char, rOffset, pathStr, glyphName)
            
class GenStrokeFontData(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)
        
        addFn, typeFloat, typeInt, typeString, typeBool = getAddFnTypes(self)
        
        addFn('--fontName', action = 'store', type = typeString, dest = 'fontName', \
            help = 'Name of the font to be created')

        addFn('--rightOffsetType', action = 'store', type = typeString, \
            dest = 'rightOffsetType',  help = 'Calculation of the right offset of the glyph')

        addFn('--spaceWidth', action = 'store', type = typeFloat, dest = 'spaceWidth', \
            help = 'Space width (enter only if changed')

        addFn('--crInfo', action = 'store', type = typeString, dest = 'crInfo', \
            help = 'Copyright and license details')

        addFn("--tab", action = "store",  type = typeString, dest = "tab", \
            default = "sampling", help = "Tab") 
          
    def getGuides(self, idName, idVal):        
        return [(pn, transformedParsedPath(pn)) for pn in self.document.xpath('//svg:path', \
            namespaces = inkex.NSS) if pn.get(idName) != None and \
                pn.get(idName).startswith(idVal)]
            
    def getFontExtraInfo(self):
        info = {}
        nodes = [node for node in self.document.xpath('//svg:' + CommonDefs.fontOtherInfo, \
            namespaces = inkex.NSS)]
        if(len(nodes) > 0):
            try:
                node = nodes[0]
                info[xAscent] = float(node.get(xAscent))
                info[xDescent] = float(node.get(xDescent))
                info[xCapHeight] = float(node.get(xCapHeight))
                info[xXHeight] = float(node.get(xXHeight))
                info[xSpaceROff] = float(node.get(xSpaceROff))
                info[xSize] = float(node.get(xSize))
                info[xFontId] = node.get(xFontId)
                return info
            except:
                pass
        return None
            
    def effect(self):
        fontName = self.options.fontName
        rightOffsetType = self.options.rightOffsetType        
        crInfo = self.options.crInfo
        spaceWidth = self.options.spaceWidth
        
        #Guide is a tuple of xml elem and parsed path
        hGuides = self.getGuides(CommonDefs.idAttribName, CommonDefs.hGuideIDPrefix)
        
        hGuides = sorted(hGuides, 
            key = lambda p: int(p[0].get(CommonDefs.idAttribName).split('_')[1]))
        
        lvGuides = self.getGuides(CommonDefs.idAttribName, CommonDefs.lvGuideIDPrefix)
        lvGuides = sorted(lvGuides, key = lambda p: (p[0].get(CommonDefs.idAttribName)))
                
        rvGuides = self.getGuides(CommonDefs.idAttribName, CommonDefs.rvGuideIDPrefix)
        rvGuides = sorted(rvGuides, key = lambda p: (p[0].get(CommonDefs.idAttribName)))
                
        if(len(lvGuides) == 0  or len(hGuides) == 0):
            inkex.errormsg("Missing guides. Please use the Create Font Design " + \
                "Template extension to design the font.")
            return 

        extraInfo = self.getFontExtraInfo()
        if(extraInfo == None): 
            fontSize = getFontSizeFromGuide(lvGuides[0][1], CommonDefs.vgScaleFact)
            extraInfo = getDefaultExtraInfo(fontName, fontSize)

        fontSize = extraInfo[xSize]

        if(round(spaceWidth, 1) == 0):
            spaceWidth = extraInfo[xSpaceROff]
            if(round(spaceWidth, 1) == 0): spaceWidth = fontSize / 2

        extraInfo[xSpaceROff] = spaceWidth

        extPath = os.path.dirname(os.path.abspath(__file__))
        strokeFontData = FontData(extPath, fontName, fontSize, InkscapeCharDataFactory())

        strokeFontData.setCRInfo(crInfo)
        strokeFontData.setExtraInfo(extraInfo)
        
        glyphPaths = [p for p in self.document.xpath('//svg:path', namespaces=inkex.NSS) \
                if (len(p.get(CommonDefs.idAttribName)) == 1)]
            
        updateFontData(strokeFontData, glyphPaths, hGuides, lvGuides, rvGuides, rightOffsetType)
        
        strokeFontData.updateFontXML()
        
        syncFontList(extPath)

try:
	runEffect(GenStrokeFontData())
except:    
    inkex.errormsg('The data was not generated due to an error. ' + \
	'If you are creating non-english glyphs then save the document, re-open and' + \
	'try generating the font data once again.')
