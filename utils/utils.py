# -*- coding: utf-8 -*-
"""
Author: Mark Mendiola, The Aerospace COrporation

This script contains several functions utilized by program to compute GPS
contacts from user specified locations

The function "main" performs the visibility analysis
"""


from . import frames as frames
from . import TimeConversionToolbox as tt
from . import almanac2xyz_lnav as nav2xyz
import numpy as np


def sem_alm(sem_file):
    '''
    This function parses out a SEM Almanac file and returns the almanac data
    contained in the file for each GPS satellite

    See ICD-GPS-870 for SEM Almanac format/data in the almanac

    input:
         file - path/filename of the SEM Almanac

    output:
         week - Almanac GPS week number
         toa - Almanac time of applicability (GPS seconds of week)
         alm - dictionary of almanac data for each PRN
         prn2svn - dictionary containing PRN to SVN mapping

    Almanac data for each PRN contained in alm dictionary:
        ura - average URA number [unitless]
        ecc - eccentricity [unitless]
        incoff - inclincation offset relative to 0.3 semi-circles [semi-circles]
        raanrate - Rate of Right Ascension [semi-circles/second]
        roota - square root of semi-major axis [meters^1/2]
        glan - Geographic Longitude of Orbital Plane (i.e., RAAN0) [semi-circles]
        argp - Argument of Perigee [semi-circles]
        m0 - Mean Anomaly [semi-circles]
        af0 - Zeroth Order Clock Correction [seconds]
        af1 - First Order Clock Correction [seconds/second]
        health - Satellite Health [unitless]
        config - Satellite Configuration [unitless]
    '''

    # Open the SEM almanac file and extract the data
    f = open(sem_file, 'r')
    lines = f.readlines()
    f.close()

    # Number of almanac satellite records are in the first line
    line1 = lines[0].split()

    # number of records
    N = int(line1[0])

    # Almanac reference week number and time of applicability are in line 2
    line2 = lines[1].split()
    # week number (range 0-1023)
    week = int(line2[0])
    # time of applicability (time in the week)
    toa = int(line2[1])

    # dictionary to hold data for each PRN
    alm = {}

    # dictionary to hold PRN to SVN mapping
    prn2svn = {}

    # step through number of satellite records to grab each satellite's almanac
    # parameters
    for i in range(N):
        # starting index for current satellite almanac parameters
        idx = 9*i + 3

        # PRN number
        prn = int(lines[idx].split()[0])

        # SVN number
        svn = int(lines[idx + 1].split()[0])

        # Average URA number
        ura = int(lines[idx + 2].split()[0])

        # grab eccentricity, inclination offset, rate of right ascension
        record = lines[idx + 3].split()
        ecc = float(record[0])
        inco = float(record[1])
        raandot = float(record[2])

        # grab square root of semi-major axis, geographic longitude of orbital
        # plane, and argument of perigee
        record = lines[idx + 4].split()
        roota = float(record[0])
        glan = float(record[1])
        argp = float(record[2])

        # grab mean anomaly, zeroth order clock correction, and first order
        # clock correction
        record = lines[idx + 5].split()
        m0 = float(record[0])
        af0 = float(record[1])
        af1 = float(record[2])

        # grab satellite health
        health = int(lines[idx + 6].split()[0])

        # grab satellite configuration
        conf = int(lines[idx + 7].split()[0])

        # Store data in a dictionary per PRN
        alm[prn] = {'ura': ura, 'ecc': ecc, 'incoff': inco,
                    'raanrate': raandot, 'roota': roota, 'glan': glan,
                    'argp': argp, 'm0': m0, 'af0': af0, 'af1': af1,
                    'health': health, 'config': conf}

        # build prn to svn mapping
        prn2svn[prn] = svn

    # return almanac data
    return [week, toa, alm, prn2svn]


def azel(user, target, llh=True, degrees=True):
    '''
    This function computes azimuth and elevation angles between a user and
    a target

    input:
         user - location of user in LLH (latitude, longitude, height)
                or XYZ ECEF (meters) coordinates
         target - location of tartet in Cartesian ECEF coordinates (meters)
         llh - Toggles whether user location is input in LLH or XYZ coordinates
         degrees - If user coordinates are LLH, toggles whether
                   latitude/longitude are input in degrees or radians

    output:
        az - user-to-target azimuth angle [degrees]
        el - user-to-target elevation angle [degrees]
    '''

    # if user location is in lat, lon, altitude
    if llh:
        if degrees:
            lat_r = np.deg2rad(user[0])
            lon_r = np.deg2rad(user[1])

            user_llh = [lat_r, lon_r, user[2]]
        else:
            user_llh = user

        # compute user cartesian ecef coordinates
        user_ecef = frames.llh2ecef(user, degrees)

    # if user locatio is in cartesian ECEF coordinates
    else:
        user_ecef = user

        # compute user lat, lon, height
        user_llh = frames.ecef2llh(user_ecef, degrees=False)
        lat_r = user_llh[0]
        lon_r = user_llh[1]

    # compute user to target position vector in ECEF
    los = target - user_ecef
    # user to target line of sight unit vector
    los = los/np.linalg.norm(los)

    # user ECEF coordinates unit vector
    user_ecef_hat = user_ecef/np.linalg.norm(user_ecef)

    # elevation angle
    elev = np.arcsin(los.dot(user_ecef_hat))

    # compute line if sight unit vector in East-North-Up coordinates
    los_enu = frames.ecef2enu(target - user_ecef, user_llh, degrees=False)

    # compute azimuth angle
    az = np.arctan2(los_enu[0], los_enu[1])

    # az, el in degrees
    az = np.rad2deg(az)
    el = np.rad2deg(elev)

    return [az, el]


def calc_dop(origin, sat_locs):
    '''
    This function computes the DOP metrics for a user that has visibility
    to at least 4 PNT sources.

    Input:
        origin - user location (latitude [deg], longitude [deg], height [m])

        sat_locs - list of satellite positions visible to the user in
                 ECEF (x, y, z) in meters

    Output:
        GDOP, PDOP, HDOP, VDOP, TDOP
    '''

    # User location in Latitude, Longitude, Height
    origin_llh = origin

    # Initialize the geometry matrix
    H = np.matrix(np.ones([len(sat_locs), 4]))

    # loop through the visible satellites
    for i, sat in enumerate(sat_locs):
        # Find the user to satellite relative location in the ENU frame
        # ENU origin frame is the user location
        stn_enu = frames.ecef2enu(sat, origin_llh, degrees=True)

        # Find the line of sight unit vector in the ENU frame
        enu_uv = stn_enu/np.linalg.norm(stn_enu)
        # store the line of sight unit vector in the geometry matrix
        H[i, 0:3] = [-enu_uv]

    # Calculate the error covariance matrix
    HTH = np.matmul(H.T, H)
    G = np.linalg.inv(HTH)

    # Grag the diagonal elements of the error covariance matrix
    diag = np.array(G.diagonal())[0]

    # Calculate the DOP metrics using the diagonal
    gdop = np.sqrt(np.sum(diag))
    pdop = np.sqrt(np.sum(diag[0:3]))
    hdop = np.sqrt(np.sum(diag[0:2]))
    vdop = np.sqrt(np.sum(diag[2]))
    tdop = np.sqrt(np.sum(diag[3]))

    # Return the DOP metrics
    return gdop, pdop, hdop, vdop, tdop


def main(year, month, day, tstep, elev_mask, sem_file, plot_dir, svn2block,
         stasLLH):
    '''
    This function is the main function that performs the GPS visibility
    analysis at user provided date and ground station locations

    Input:
        year - year to perform the analysis
        month - month number to perform the analysis
        day - day of the month to perform the analysis
        tstep - time step at which to compute metrics [seconds]
        elev_mask - Elevation angle below which satellites are not
                    considered visible [degrees]
        sem_file - SEM almanac containing the GPS satellites orbit states
        plot_dir - directory to store plots in
        svn2block - dictionary containing the SV number to satellite block
                    mapping. Format is {SVNum: 'block'}
        stasLLH - dictionary holding latitude, longitude, altitude coordiantes
                  for each station. Format is {'StaName': [lat,lon,alt]}

    Output:
        Gantt charts, GDOP plots, and number of visible satellites plots for
        each station. The plots are stored as .png file at the user provided
        output directory plot_dir

    '''

    # call python function to extract SEM almanac data
    wna, toa, alm, prn2svn = sem_alm(sem_file)

    # create time vector array to evaluate metric at
    t_vec = np.arange(0, 86400 + tstep, tstep)

    # number of time points evaluated
    N = len(t_vec)

    # create a dictionary for each station to hold look angles to each
    # satellite, DOP values, and number of visible satellites at each time step
    staData = {}
    for sta in stasLLH.keys():
        # create dictionary for each station
        staData[sta] = {}
        for prn in prn2svn.keys():
            staData[sta][prn] = np.zeros((N, 3))

        # add DOP values to dictionary for each station
        staData[sta]['gdop'] = np.zeros((N, 2))
        staData[sta]['pdop'] = np.zeros((N, 2))
        staData[sta]['hdop'] = np.zeros((N, 2))
        staData[sta]['vdop'] = np.zeros((N, 2))
        staData[sta]['tdop'] = np.zeros((N, 2))
        staData[sta]['vis'] = np.zeros((N, 2))

    # semi-circles to radians conversion factor
    pi = 3.1415926535898  # ICD200 value of pi

    # step through each time point and compute the DOP metrics and look angles
    # for each station
    for i, t_curr in enumerate(t_vec):
        # Convert the time to a Julian Date
        jdmsg = tt.TimeConversion().cal2jd(year, month, day + t_curr/86400.)

        # Convert the time to GPS time (GPS week and seconds of week)
        gpswk, sow, rollover = tt.TimeConversion().jd2gps(jdmsg)

        # Initialize array to hold satellite ECEF positions for all GPS
        # satellites
        satPosDict = {}

        # Compute ECEF position of each PRN
        for prn in alm.keys():
            # almanac data for current prn
            msg2use = alm[prn]

            # extract orbital elements from almanac
            # NOTE: angles are in semi-circles. Multiply by pi to convert to
            # radians
            rootA = msg2use['roota']
            ecc = msg2use['ecc']
            # NOTE: inclination = reference inclination (0.3 semi-circles)
            #                     + inclination offset
            # See Table 20-VI of ICD200
            inc = (msg2use['incoff'] + 0.3)*pi
            raan = msg2use['glan']*pi
            raandot = msg2use['raanrate']*pi
            argp = msg2use['argp']*pi
            m0 = msg2use['m0']*pi

            # satellite position in ECEF coordinates [meters]
            satPos = nav2xyz.NavMsg2XYZ(rootA, ecc, inc, raan, raandot, argp,
                                        m0, wna, toa, gpswk % 1024, sow,
                                        semicir=False)

            # store the satellite position in the GPS satellite position array
            satPosDict[prn] = satPos

        # compute visibility angles from each station to satellite
        for sta in stasLLH.keys():
            # list to hold number of visible satellites at each ground station
            vis_sats = []
            for prn in satPosDict.keys():
                # compute station to satellite azimuth and elevation angles
                az, el = azel(stasLLH[sta], satPosDict[prn], llh=True,
                              degrees=True)

                # add look angles to stations data dictionary
                staData[sta][prn][i, :] = np.array([t_curr, az, el])

                # if the elevation angle is greater than the elevation mask,
                # use the satellite for the DOP solution
                if el >= elev_mask:
                    vis_sats.append(satPosDict[prn])

            # Determine the number of visible satellites at current station
            nvis = len(vis_sats)

            # fill DOP grid point with nans if < 4 satellites are visible
            # (i.e., no DOP solution exists)
            if nvis < 4:
                gdop = np.nan
                pdop = np.nan
                hdop = np.nan
                vdop = np.nan
                tdop = np.nan

            # compute the DOP metrics if 4 or more satellites are visible
            if len(vis_sats) >= 4:
                gdop, pdop, hdop, vdop, tdop = calc_dop(stasLLH[sta], vis_sats)

            # add DOP values and number of visible satellites to station
            # dictionary
            staData[sta]['gdop'][i, :] = np.array([t_curr, gdop])
            staData[sta]['pdop'][i, :] = np.array([t_curr, pdop])
            staData[sta]['hdop'][i, :] = np.array([t_curr, hdop])
            staData[sta]['vdop'][i, :] = np.array([t_curr, vdop])
            staData[sta]['tdop'][i, :] = np.array([t_curr, tdop])
            staData[sta]['vis'][i, :] = np.array([t_curr, nvis])

    # sort PRN2SVN dictionary by SV number
    sorted_d = sorted(prn2svn.items(), key=lambda x: x[1])

    # Find visibility time periods of each satellite from each station to
    # create Gantt charts showing satellite visibility
    for sta in stasLLH.keys():
        # list to hold number of visible satellites at each ground station
        vis_sats = []
        for prn, svn in sorted_d:
            # grab data for current PRN for elevation angle > elevation mask
            # (i.e, find where the satellite is visible)
            look_ang = staData[sta][prn]
            look_ang = look_ang[look_ang[:, 2] >= elev_mask, :]

            # find the satellite block for the current satellite
            block = svn2block[svn]

            # compute time difference in look angles data array where elevation
            # is greater than elevation mask to determine if satellite is
            # visible more than once during the day
            diff = np.diff(look_ang, axis=0)

            # maximum time difference
            mdiff = np.max(diff[:, 0])

            # satellite is visible for one block of time during the day
            if mdiff <= tstep:
                # Find the hour, minute, second of satellite "rise"
                [hr_c, minute_c, sec_c] = tt.TimeConversion().sec2hms(look_ang[0, 0])
                # satellive visibility start time for Gantt chart
                start_time = '%4d-%02d-%02d %d:%02d:%02d' \
                             % (year, month, day, hr_c, minute_c, sec_c)
                # Find the hour, minute, second of satellite "set"
                [hr_c, minute_c, sec_c] = tt.TimeConversion().sec2hms(look_ang[-1, 0])
                # satellive visibility end time for Gantt chart
                end_time = '%4d-%02d-%02d %d:%02d:%02d' \
                           % (year, month, day, hr_c, minute_c, sec_c)

                # create dictionary to hold satellite visibility time period
                # start_ time is satellite rise time
                # end_time is satellite set time
                bar_dict = dict(Task='SVN %2d-PRN %2d'
                                % (svn, prn), Start='%s' % start_time,
                                Finish='%s' % end_time, Resource=block)
                # append satellite visible time to list of visible satellites
                vis_sats.append(bar_dict)

            # satellite is visible more than once during the day
            if mdiff > tstep:
                # determine indices of satellite visibility time periods in between
                # the first and last time points where the satellite is visible
                res = [idx for idx, val in enumerate(diff[:, 0]) if val > tstep]

                # create list to store end points of visibility time block
                t_list = []

                # first time point where the satellite is visible
                [hr_c, minute_c, sec_c] = tt.TimeConversion().sec2hms(look_ang[0, 0])

                # append the time point to t_list
                t_list.append([hr_c, minute_c, sec_c])

                # find visibility end points for time blocks in beetween the first
                # and last time points
                for i in range(0, len(res)):
                    [hr_c, minute_c, sec_c] = tt.TimeConversion().sec2hms(look_ang[res[i], 0])
                    t_list.append([hr_c, minute_c, sec_c])
                    [hr_c, minute_c, sec_c] = tt.TimeConversion().sec2hms(look_ang[res[i] + 1, 0])
                    t_list.append([hr_c, minute_c, sec_c])

                # last time point where the satellite is visible
                [hr_c, minute_c, sec_c] = tt.TimeConversion().sec2hms(look_ang[-1, 0])

                # append the time point to t_list
                t_list.append([hr_c, minute_c, sec_c])

                # go through the time list and determine where each visibility
                # time block begins/ends (i.e, satellite rise/set points)

                for j in range(len(res) + 1):
                    [hr_c, minute_c, sec_c] = t_list[2*j]
                    # satellive visibility start time for Gantt chart
                    start_time = '%4d-%02d-%02d %d:%02d:%02d' \
                                 % (year, month, day, hr_c, minute_c, sec_c)
                    # satellive visibility end time for Gantt chart
                    [hr_c, minute_c, sec_c] = t_list[2*j + 1]
                    end_time = '%4d-%02d-%02d %d:%02d:%02d' \
                               % (year, month, day, hr_c, minute_c, sec_c)

                    # create dictionary to hold satellite visibility time block
                    # start_ time is satellite rise time
                    # end_time is satellite set time
                    bar_dict = dict(Task='SVN %2d-PRN %2d' % (svn, prn),
                                    Start='%s' % start_time,
                                    Finish='%s' % end_time, Resource=block)

                    # append satellite visible time to list of visible satellites
                    vis_sats.append(bar_dict)

        # Differentiate satellite blocks on Gantt chart by using different colors
        # set colors = Resource (i.e, the satellite block)
        colors = {'IIR': 'rgb(30, 144, 255)',
                  'IIR-M': 'rgb(0, 128, 0)',
                  'IIF': 'rgb(114, 44, 121)',
                  'III': 'rgb(204, 85, 0)'}

        # Create Gantt chart
        fig = ff.create_gantt(vis_sats, colors=colors, index_col='Resource',
                              title='%s: Satellite Visibility' % sta,
                              show_colorbar=True, bar_width=0.3,
                              showgrid_x=True,
                              showgrid_y=True, height=600, width=900,
                              group_tasks=True)

        # save the Gantt chart as a .png file
        fig.write_image('%s/Gantt_Chart-%s-%4d-%02d-%02d.png'
                        % (plot_dir, sta, year, month, day))
    # -------------------------------------------------------------------------
    # plot DOP and number of satellites visible at each station
    # -------------------------------------------------------------------------
    for sta in stasLLH.keys():
        # close all figures
        plt.close('all')

        # Plot GDOP
        plt.figure(1, figsize=(9, 6))

        plt.plot(t_vec/3600.0, staData[sta]['gdop'][:, 1], color='dodgerblue',
                 lw=1.5, zorder=3)

        plt.title('%s: GDOP' % sta, fontweight='bold', fontsize=13)
        # Format axis labels:
        plt.ylabel('GDOP', fontweight='bold')
        plt.xlabel('%s-%2d-%4d (UTC)' % (month, day, year), fontweight='bold')
        plt.ylim(0, 10)
        plt.yticks(np.arange(0, 10 + .1, 1))
        plt.xlim(0, 24)
        plt.xticks(np.arange(0, 24 + .1, 3))
        plt.grid()

        # save figure as .png file
        plt.savefig('%s/%s_gdop.png' % (plot_dir, sta), dpi=300,
                    transparent=True, bbox_inches='tight')

        # plot number of satellite visible at station
        plt.figure(2, figsize=(9, 6))

        plt.plot(t_vec/3600.0, staData[sta]['vis'][:, 1], color='dodgerblue',
                 lw=1.5, zorder=3)

        plt.title('%s: Number of Visible GPS Satellites' % sta,
                  fontweight='bold', fontsize=13)
        # Format axis labels:
        plt.ylabel('Number of Visible Satellites', fontweight='bold')
        plt.xlabel('%s-%2d-%4d (UTC)' % (month, day, year), fontweight='bold')
        plt.ylim(0, 20)
        plt.yticks(np.arange(0, 20+.1, 2))
        plt.xlim(0, 24)
        plt.xticks(np.arange(0, 24+.1, 3))
        plt.grid()

        # save figure as .png file
        plt.savefig('%s/%s_nvis.png' % (plot_dir, sta), dpi=300,
                    transparent=True, bbox_inches='tight')