#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
#
#	RMG Website - A Django-powered website for Reaction Mechanism Generator
#
#	Copyright (c) 2011 Prof. William H. Green (whgreen@mit.edu) and the
#	RMG Team (rmg_dev@mit.edu)
#
#	Permission is hereby granted, free of charge, to any person obtaining a
#	copy of this software and associated documentation files (the 'Software'),
#	to deal in the Software without restriction, including without limitation
#	the rights to use, copy, modify, merge, publish, distribute, sublicense,
#	and/or sell copies of the Software, and to permit persons to whom the
#	Software is furnished to do so, subject to the following conditions:
#
#	The above copyright notice and this permission notice shall be included in
#	all copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#	DEALINGS IN THE SOFTWARE.
#
################################################################################

"""
Provides template tags for rendering statmech models in various ways.
"""

# Register this module as a Django template tag library
from django import template
register = template.Library()

from django.utils.safestring import mark_safe

import numpy

from rmgweb.main.tools import getLaTeXScientificNotation, getStructureMarkup
from rmgweb.main.models import UserProfile

from rmgpy.quantity import Quantity
from rmgpy.statmech import *

################################################################################

@register.filter
def render_states_math(states, user=None):
    """
    Return a math representation of the given `states` using jsMath. If a 
    `user` is specified, the user's preferred units will be used; otherwise 
    default units will be used.
    """
    # Define other units and conversion factors to use
    if user and user.is_authenticated():
        user_profile = UserProfile.objects.get(user=user)
        Tunits = str(user_profile.temperatureUnits)
        Eunits = str(user_profile.energyUnits)
    else:
        Tunits = 'K'
        Eunits = 'kcal/mol'
    Tfactor = Quantity(1, Tunits).getConversionFactorFromSI()
    Efactor = Quantity(1, Eunits).getConversionFactorFromSI()
    
    # The string that will be returned to the template
    result = ''
    
    result += '<table class="reference">\n'

    hindIndex = 0
    for mode in states.modes:
        if isinstance(mode, Translation):
            result += '<tr>'
            result += r'    <td colspan="2" class="section">External translation</td>'
            result += '</tr>\n'
            result += '<tr>'
            result += r'    <td class="label">Mass (g/mol):</td>'
            result += r'    <td>{0:g}</td>'.format(mode.mass.value * 1000.)
            result += '</tr>\n'
        
        elif isinstance(mode, RigidRotor):
            result += '<tr>'
            result += r'    <td colspan="2" class="section">External rotation</td>'
            result += '</tr>\n'
            result += '<tr>'
            result += r'    <td class="label">Linearity:</td>'
            result += r'    <td>{0}</td>'.format(mode.linear)
            result += '</tr>\n'
            result += '<tr>'
            result += r'    <td class="label">Moments of inertia (amu&times;&Aring;^2):</td>'
            if mode.inertia.isArray():
                inertia = ', '.join(['{0:.1f}'.format(I * constants.Na * 1e23) for I in mode.inertia.values])
            else:
                inertia = '{0:.1f}'.format(mode.inertia.value * constants.Na * 1e23)
            result += r'    <td>{0!s}</td>'.format(inertia)
            result += '</tr>\n'
            result += '<tr>'
            result += r'    <td class="label">Symmetry number:</td>'
            result += r'    <td>{0:d}</td>'.format(mode.symmetry)
            result += '</tr>\n'
        
        elif isinstance(mode, HarmonicOscillator):
            result += '<tr>'
            result += r'    <td colspan="2" class="section">Vibrations</td>'
            result += '</tr>\n'
            result += '<tr>'
            frequencies = ', '.join(['{0:.1f}'.format(freq) for freq in mode.frequencies.values])
            result += r'    <td class="label" class="section">Frequencies (cm^-1):</td>'
            result += r'    <td>{0!s}</td>'.format(frequencies)
            result += '</tr>\n'
    
        elif isinstance(mode, HinderedRotor):
            hindIndex += 1
            result += '<tr>'
            result += r'    <td colspan="2" class="section">Hindered rotor #{0:d}:</td>'.format(hindIndex)
            result += '</tr>\n'
            if mode.fourier:
                fourierA = ', '.join(['{0:g}'.format(a_k) for a_k in mode.fourier.values[0,:]])  
                fourierB = ', '.join(['{0:g}'.format(b_k) for b_k in mode.fourier.values[1,:]])
                result += '<tr>'
                result += r'    <td colspan="2"><span class="math">V(\phi) = A + \sum_k \left( a_k \cos k \phi + b_k \sin k \phi \right)</span></td>'
                result += '</tr>\n'
                result += '<tr>'
                result += r'    <td class="label"><span class="math">a_k</span></td>'
                result += r'    <td>{0}</td>'.format(fourierA)
                result += '</tr>\n'
                result += '<tr>'
                result += r'    <td class="label"><span class="math">b_k</span></td>'
                result += r'    <td>{0}</td>'.format(fourierB)
                result += '</tr>\n'
            else:
                result += '<tr>'
                result += r'    <td colspan="2"><span class="math">V(\phi) = \frac{1}{2} V_0 \left[1 - \cos \left( \sigma \phi \right) \right]</span></td>'
                result += '</tr>\n'
                result += '<tr>'
                result += r'    <td class="label">Barrier height ({0!s}):</td>'.format(Eunits)
                result += r'    <td>{0:.2f}</td>'.format(mode.barrier.value * Efactor)
                result += '</tr>\n'
            result += '<tr>'
            result += r'    <td class="label">Moment of inertia (amu&times;&Aring;^2):</td>'
            result += r'    <td>{0:.1f}</td>'.format(mode.inertia.value * constants.Na * 1e23)
            result += '</tr>\n'
            result += '<tr>'
            result += r'    <td class="label">Symmetry number:</td>'
            result += r'    <td>{0:d}</td>'.format(mode.symmetry)
            result += '</tr>\n'

    result += '<tr>'
    result += r'    <td colspan="2" class="section">Electronic</td>'
    result += '</tr>\n'
    result += '<tr>'
    result += r'    <td class="label">Spin multiplicity:</td>'
    result += r'    <td>{0:d}</td>'.format(states.spinMultiplicity)
    result += '</tr>\n'

    result += '</table>\n'

    return mark_safe(result)

################################################################################

@register.filter
def get_states_data(states, user=None):
    """
    Generate and return a set of :math:`k(T,P)` data suitable for plotting
    using Highcharts. If a `user` is specified, the user's preferred units
    will be used; otherwise default units will be used.
    """
    
    # Define other units and conversion factors to use
    if user and user.is_authenticated():
        user_profile = UserProfile.objects.get(user=user)
        Tunits = str(user_profile.temperatureUnits)
        Eunits = str(user_profile.energyUnits)
    else:
        Tunits = 'K'
        Eunits = 'kcal/mol'
    Tfactor = Quantity(1, Tunits).getConversionFactorFromSI()
    Efactor = Quantity(1, Eunits).getConversionFactorFromSI()
    Qunits = ''
    Qfactor = 1.0
    rhounits = 'per cm^-1' 
    rhofactor = constants.h * constants.c * 100 * constants.Na
    phiunits = 'rad' 
    phifactor = 1.0
    Vunits = Eunits
    Vfactor = Efactor
        
    # Generate data to use for plots
    Tdata = []; Qdata = []
    for T in numpy.arange(10, 2001, 10):
        Tdata.append(T * Tfactor)
        Qdata.append(states.getPartitionFunction(T) * Qfactor)
    
    Edata = numpy.arange(0, 400001, 1000, numpy.float)
    rhodata = states.getDensityOfStates(Edata)
    Edata = list(Edata * Efactor)
    rhodata = list(rhodata * rhofactor)
    
    phidata = numpy.arange(0, 2*math.pi, math.pi/200)
    Vdata = []
    for mode in states.modes:
        if isinstance(mode, HinderedRotor):
            Vdata.append(list(mode.getPotential(phidata) * Vfactor))
    phidata = list(phidata * phifactor)
    
    return mark_safe("""
Tlist = {0};
Qlist = {1};
Elist = {2};
rholist = {3};
philist = {4};
Vlist = {5};
Tunits = "{6}";
Qunits = "{7}";
Eunits = "{8}";
rhounits = "{9}";
phiunits = "{10}";
Vunits = "{11}";
    """.format(
        Tdata, 
        Qdata, 
        Edata, 
        rhodata, 
        phidata, 
        Vdata,
        Tunits, 
        Qunits, 
        Eunits, 
        rhounits, 
        phiunits, 
        Vunits,
    ))
