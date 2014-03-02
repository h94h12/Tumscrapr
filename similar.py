import numpy
from PIL import Image
import cv2

def similarness(image1,image2):
    """
Return the correlation distance be1tween the histograms. This is 'normalized' so that
1 is a perfect match while -1 is a complete mismatch and 0 is no match.
"""
    # Open and resize images to 200x200
    i1 = Image.open(image1).resize((200,200))
    i2 = Image.open(image2).resize((200,200))

    # Get histogram and seperate into RGB channels
    i1hist = numpy.array(i1.histogram()).astype('float32')
    i1r, i1b, i1g = i1hist[0:256], i1hist[256:256*2], i1hist[256*2:]
    # Re bin the histogram from 256 bins to 48 for each channel
    i1rh = numpy.array([sum(i1r[i*16:16*(i+1)]) for i in range(16)]).astype('float32')
    i1bh = numpy.array([sum(i1b[i*16:16*(i+1)]) for i in range(16)]).astype('float32')
    i1gh = numpy.array([sum(i1g[i*16:16*(i+1)]) for i in range(16)]).astype('float32')
    # Combine all the channels back into one array
    i1histbin = numpy.ravel([i1rh, i1bh, i1gh]).astype('float32')

    # Same steps for the second image
    i2hist = numpy.array(i2.histogram()).astype('float32')
    i2r, i2b, i2g = i2hist[0:256], i2hist[256:256*2], i2hist[256*2:]
    i2rh = numpy.array([sum(i2r[i*16:16*(i+1)]) for i in range(16)]).astype('float32')
    i2bh = numpy.array([sum(i2b[i*16:16*(i+1)]) for i in range(16)]).astype('float32')
    i2gh = numpy.array([sum(i2g[i*16:16*(i+1)]) for i in range(16)]).astype('float32')
    i2histbin = numpy.ravel([i2rh, i2bh, i2gh]).astype('float32')

    return cv2.compareHist(i1histbin, i2histbin, 0)
