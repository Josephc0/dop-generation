# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 12:51:05 2019

@author: mam29521
"""

import numpy as np


def NavMsg2XYZ(rootA, ecc, inc, raan, raandot, argp, m0, wna, toa, wn, t,
               semicir=False):
    '''
    # ======================================================================
    # This function computes the cartesian position vector of a GPS satellite
    # in ECEF coordinates given almanac ephemeris parameters
    #
    # Compute Earth-fixed SV antenna phase center position
    # vector using the almanac orbital parameters
    # as specified in Section 20.3.3.5.2.1 and Table 20-IV of IS-GPS-200
    #
    # Per Section 20.3.3.5.2.1 of IS-GPS-200, the algorithm for SV ECEF
    # position determination using the almanac parameters is the same as the
    # algorithm used for the parameters in LNAV suframes 1-3. The parameters
    # appearing in the equations of Table 20-IV, but not included in the
    # content of the almanac, are set to 0 for SV position determination.
    #
    # Input:
    # rootA - square root of semi-major axis [meters^1/2]
    # ecc - orbit eccentricity [unitless]
    # inc - orbit inclination  [semi-circles or radians]
    # raan - Righ Ascension of Ascending Node [semi-circles or radians]
    # raandot - Rate of Right Ascension [semi-circles/second or radians/second]
    # argp - Argument of Perigee [semi-circles or radians]
    # m0 - Mean Anomaly at epoch [semi-circles or radians]
    # wna - Almanac GPS reference week number [range: 0-1023]
    # toa - Almanac time of applicability [GPS seconds of week]
    # wn - current week number [range: 0-1023]
    # t          - current time (GPS seconds of week)
    # semicir - boolean flag to toggle whether angles are input in semi-circles
    #           or radians
    #
    # Output:
    # Pos  - ECEF Position vector of GPS satellite (meters)
    # ======================================================================
    '''

    # Define constants per Table 20-IV of IS-GPS-200
    # Earth gravitational constant [m^3/s^2]
    GM = 3.986005e14
    rootGM = np.sqrt(GM)
    # Earth rotation rate [rad/sec]
    oedot = 7.2921151467e-5
    # ICD200 value of pi
    pi = 3.1415926535898
    twopi = 2*pi

    crs      = 0.0
    deln     = 0.0
    M0       = m0
    cuc      = 0.0
    ecc      = ecc
    cus      = 0.0
    rootA    = rootA
    toe      = toa
    cic      = 0.0
    Omega0   = raan
    cis      = 0.0
    i0       = inc
    crc      = 0.0
    argPer   = argp
    OmegaDot = raandot
    iDot     = 0.0

    # convert nav message ephemeris parameters to proper units. See IS-GPS-200
    # Table 20-III and 20-VI for the units of broadcast nav message parameters

    # Convert the following parameters with units of semi-circles to radians
    if semicir is True:
        deln = deln*pi
        M0 = M0*pi
        Omega0 = Omega0*pi
        i0 = i0*pi
        argPer = argPer*pi
        OmegaDot = OmegaDot*pi
        iDot = iDot*pi

    # time from almanac reference time
    dt = t - toa + (wn - wna)*604800.0

    # ignore time of week check for the almanac
    # Account for beginning/end of week crossovers
#    if dt > 302400:
#        dt = dt - 604800.
#    if dt < -302400:
#        dt = dt + 604800.

    # Step 1: Compute semi-major axis, computed mean motion, time from
    # ephemeris, and corrected mean motion:
    # Semi-major axis and mean motion
    A = rootA**2
    n0 = rootGM/(A*rootA)
    # Corrected Mean Motion
    n = n0 + deln

    # Step 2: compute eccentricity, argument of perigee, and Mean anomaly
    # if given alternative orbital elements: alpha, beta, gamma
    # Does not apply for standard nav message

    # Step 3: Compute Mean Anomaly at time t
    M = (M0 + n*dt) % twopi

    # Step 4: Compute Eccentric Anomaly, E, at time t by solving Kepler's
    # Equation using Newton iteration method:
    # Initialize Eccentric Anomaly
    EAnom = M + ecc*np.sin(M)
    # Max number of iterations and error tolerance
    TOL = 1e-13  # radians
    MAXIT = 20
    # Iteration count and convergence flag
    ITER = 0
    NFLAG = 0

    while (ITER < MAXIT or NFLAG == 0):
        sinE = np.sin(EAnom)
        cosE = np.cos(EAnom)

        Value = EAnom - ecc*sinE
        Deriv = 1. - ecc*cosE

        Delta = (M-Value)/Deriv

        # Update Eccentric Anomaly
        EAnom = EAnom + Delta

        # If Delta is small enough, exit.
        if (abs(Delta) < TOL):
            NFLAG = 1

        ITER = ITER + 1
        # End of while loop

    # Compute sine and cosine of Eccentric Anomaly
    cosE = np.cos(EAnom)
    sinE = np.sin(EAnom)

    # Step 5: Compute sine and cosine of true anomaly, v, at time t:
    cosv = (cosE-ecc)/(1-ecc*cosE)
    sinv = (np.sqrt(1-ecc**2)*sinE)/(1-ecc*cosE)

    # Step 6: Compute sine and cosine of argument of latitude, phi = v + w,
    # at time t
    # where w = argument of perigee:
    sinw    = np.sin(argPer)
    cosw    = np.cos(argPer)
    sinphi  = sinv*cosw + cosv*sinw
    cosphi  = cosv*cosw - sinv*sinw
    sin2phi = 2*sinphi*cosphi
    cos2phi = cosphi**2 - sinphi**2

    # Step 7: Compute argument of latitude correction, delu, radius correction,
    # delr, and correction to inclination, deli, at time t:
    delu = cuc*cos2phi + cus*sin2phi
    delr = crc*cos2phi + crs*sin2phi
    deli = cic*cos2phi + cis*sin2phi

    # Step 8: Compute sine and cosine of corrected argment of latitude,
    # u = phi+delu, corrected radius, r, and corrected inclination, i, at
    # time t:
    cosdelu = np.cos(delu)
    sindelu = np.sin(delu)
    sinu    = sinphi*cosdelu + cosphi*sindelu
    cosu    = cosphi*cosdelu - sinphi*sindelu

    # Corrected radius
    r = A*(1-ecc*cosE) + delr
    # Corrected inclination along with its sine and cosine
    i    = i0 + deli + iDot*dt
    cosi = np.cos(i)
    sini = np.sin(i)

    # Step 9: Compute Positions in orbital plane at time t:
    XP = r*cosu
    YP = r*sinu

    # Step 10: Compute corrected longitude of ascending node OMEGA, at time t
    # relative to ephemeris reference data time:
    OMEGA = Omega0 + (OmegaDot-oedot)*dt - oedot*toe
    # Restrict OMEGA to the interval [0,2pi]
    OMEGA = OMEGA % twopi
    # Cosine and sine of OMEGA
    cosO  = np.cos(OMEGA)
    sinO  = np.sin(OMEGA)

    # Step 11:  Compute Earth-centered, Earth-fixed coordinates at time t:
    Pos = np.array(np.zeros(3))

    Pos[0] = XP*cosO - YP*cosi*sinO
    Pos[1] = XP*sinO + YP*cosi*cosO
    Pos[2] = YP*sini

    # Return position of satellite in ECEF coordinates [meters]
    return Pos
