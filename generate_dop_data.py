# -*- coding: utf-8 -*-
"""
Created on Thu Apr 02 13:30:42 2020

@author: MAM29521

This script contains various functions utilized in the DOP analysis
"""

import datetime
import numpy as np
from datetime import timedelta
import time
import multiprocessing as mp

import utils.almanac2xyz_lnav as nav2xyz
from utils import utils
from utils import frames as frames
from utils import TimeConversionToolbox as tconv

import os

RFC_3339_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DATE_FORMAT = RFC_3339_FORMAT

# function to grab LNAV subframe 1-3 data
def lnavsf123(tlower, tupper, prn, client):
    '''
    This function builds the querys for LNAV SF1-3 data, queries the provided
    database, and returns the LNAV SF1-3 data

    Input:
        tlower - lower bound of time to query the database
                 formatted as: YYYY-MM-DDTHH:mm:ssZ (UTC)
                 where YYYY = year (4 digits)
                       MM = month number (2 digits)
                       DD = day of month (2 digits)
                       HH = hour (2 digits)
                       mm = minute (2 digits)
                       ss = seconds (2 digits)

        tupper - upper bound to time to query the database
                 formatted as: YYYY-MM-DDTHH:mm:ssZ (UTC)

        prn - PRN for which to query SF1-3 data

        client - InfluxDBClient client object to connect InfluxDB to query
                 the LNAV SF1-3 data

    Output:
        outDict - dictionary holding the LNAV SF1-3 data
        sf1_iodc - SF1 IODC value
        sf2_iode - SF2 IODE value
        sf3_iode - SF3 IODE value
    '''

    # dictionary to store LNAV subframe 1-3 data
    outDict = {}

    # LNAV subframe 1 data to query
    query_sf1 = 'SELECT "sv_signal_health", "toc", "tow_count_message",' + \
                ' "iodc"' + \
                ' FROM "nav_subframe1" WHERE time > \'%s\' and ' % tlower + \
                'time <= \'%s\' AND ("prn"=\'%s\')' % (tupper, prn)

    # LNAV subframe 2 data to query
    query_sf2 = 'SELECT "crs", "cuc", "cus", "delta_n", "e", "m0",' + \
                ' "roota", "toe", "iode"' + \
                ' FROM "nav_subframe2" WHERE time > \'%s\' and ' % tlower + \
                'time <= \'%s\' AND ("prn"=\'%s\')' % (tupper, prn)

    # LNAV subframe 3 data to query
    query_sf3 = 'SELECT "cic", "cis", "crc",' + \
                ' "i0", "i_dot", "iode",' + \
                ' "lomega", "omega0", "omega_dot"' + \
                ' FROM "nav_subframe3" WHERE time > \'%s\' and ' % tlower + \
                'time <= \'%s\' AND ("prn"=\'%s\')' % (tupper, prn)

    # Query the database for the LNAV subframe 1 data
    # result is a ResultSet Object
    result = client.query(query_sf1)

    points = result.get_points()

    for point in points:
        # add subframe1 data to dictionary
        outDict.update(point)

        # get subframe 1 IODC value
        sf1_iodc = point['iodc']

    # Query the database for the LNAV subframe 2 data
    # result is a ResultSet Object
    result = client.query(query_sf2)

    points = result.get_points()

    for point in points:
        # add subframe2 data to dictionary
        outDict.update(point)

        # get subframe 2 IODE value
        sf2_iode = point['iode']

    # Query the database for the LNAV subframe 3 data
    # result is a ResultSet Object
    result = client.query(query_sf3)

    points = result.get_points()

    for point in points:
        # add subframe 3 data to dictionary
        outDict.update(point)

        # get subframe 2 IODE value
        sf3_iode = point['iode']

    # return SF1-3 data dictionary and SF1-3 IODC, IODE values
    return outDict, sf1_iodc, sf2_iode, sf3_iode


def get_lnavsf123_dict(PRNList, epochl, epoch, client):
    '''
    This dictionary gets the LNAV SF 1-3 data for user requested PRNs and
    returns a dictionary of the SF1-3 data for each PRN

    Input:
        PRNList - List of PRNs for which to query databse for SF1-3 data

        epochl - lower bound of time to query the database
                 Format: python datetime object holding year, month, day,
                         hour, minute, second

        epoch - upper bound of time to query the database
                Format: python datetime object holding year, month, day,
                         hour, minute, second

        client - InfluxDBClient client object to connect InfluxDB to query
                 the LNAV SF1-3 data

    Output:
        prnDic - Dictionary holding the LNAV SF 1-3 data for each PRN in
                 PRNList that is healthy and for for which IODC and IODE
                 values in SF1-3 are equivalent.

                 The prnDic keys are the PRNs. The values are the dictionaries
                 returned by the database query that contain SF1-3 data via
                 the call to the lnavsf123 function.
    '''

    # empty dictionary to hold SF1-3 nav message data for each PRN
    prnDic = {}

    # lower bound on query time; expressed in a format acceptable by influx
    tlower = '%4d-%02d-%02dT%02d:%02d:%02dZ' % (epochl.year, epochl.month,
                                                epochl.day, epochl.hour,
                                                epochl.minute, epochl.second)

    # upper bound on query time; expressed in a format acceptable by influx
    tupper = '%4d-%02d-%02dT%02d:%02d:%02dZ' % (epoch.year, epoch.month,
                                                epoch.day, epoch.hour,
                                                epoch.minute, epoch.second)

    # query the database for SF1-3 data for each PRN
    for prn in PRNList:

        # query the database for SF1-3 data
        sfDataDict, sf1_iodc, sf2_iode, sf3_iode = lnavsf123(tlower,
                                                   tupper, prn, client)

        # Per IS-GPS-200, Section 20.3.3.4.1, the IODC value in SF1 and IODE values
        # in SF2 and SF3 must all match. Otherwise, a data set cutover has occurred
        # and SF1, SF2, and SF3 data for the same dataset must be collected
        # SF1-3 are transmitted every 30 seconds, so if there is a data set cutover
        # checking the database at least 30 seconds before the time in question
        # should give SF1-3 from the same dataset.

        # Check that IODC and IODE values in SF1-3 are the same:

        # if IODC and IODE values in SF1-3 match, add the SF1-3 data to the PRN
        # dctionary for the current PRN
        if sf1_iodc == sf2_iode and sf1_iodc == sf3_iode and sf2_iode == sf3_iode:
            prnDic[prn] = sfDataDict

        # if the IODC and IODE values in SF1-3 do not match, search the database
        # 5 minutes in the past to see if SF1-3 IODC and IODE values were the same
        # during that time. Otherwise, exclude this PRN from the DOP solution
        elif sf1_iodc != sf2_iode or sf1_iodc != sf3_iode or sf2_iode != sf3_iode:
            print('IODC/IODE discrepancy for PRN: ', prn)

            # query the database again 5 minutes in the past to see if IODE and
            # IODC values in SF1-3 are the same
            epoch_recheck = epoch - timedelta(seconds=300)
            epochl_recheck = epoch_recheck - timedelta(seconds=30)

            # lower bound on query time; expressed in a format acceptable by influx
            tlower_recheck = '%4d-%02d-%02dT%02d:%02d:%02dZ' % (epochl_recheck.year,
                             epochl_recheck.month, epochl_recheck.day, epochl_recheck.hour,
                             epochl_recheck.minute, epochl_recheck.second)

            # upper bound on query time; expressed in a format acceptable by influx
            tupper_recheck = '%4d-%02d-%02dT%02d:%02d:%02dZ' % (epoch_recheck.year,
                              epoch_recheck.month, epoch_recheck.day, epoch_recheck.hour,
                              epoch_recheck.minute, epoch_recheck.second)

            # query the database for SF1-3 data
            sfDataDict_rc, sf1_iodc_rc, sf2_iode_rc, sf3_iode_rc = lnavsf123(tlower_recheck,
                                                                tupper_recheck, prn, client)

            # if IODC and IODE values in SF1-3 match, add the SF1-3 data to the PRN
            # dictionary for the current PRN
            if sf1_iodc_rc == sf2_iode_rc and sf1_iodc_rc == sf3_iode_rc and sf2_iode_rc == sf3_iode_rc:
                prnDic[prn] = sfDataDict_rc

    # Check satellite health and remove unhealthy satellites from the PRN
    # dictionary to exclude unhealthy satellites from the DOP solution
    #for prn in prnDic.keys(): # doesn't work for Python 3
    for prn in list(prnDic):
        # sv health bits converted to an integer
        sv_health = int(str(prnDic[prn]['sv_signal_health']), 2)
        # if satellite is unhealthy
        if sv_health > 0:
            print('The following PRN is unhealthy: ', prn)
            #del prnDic[prn]
            prnDic.pop(prn)

    # return the dictionary holding the SF1-3 data for each PRN
    return prnDic


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


def compute_percentile(values, weights, indicesList, percentile):
    '''
    This function computes the xth weighted percentile for a given metric;
    for example the 95th percentile.

    Input:
        values - array holding the values of the metric in question. This array
                 is not necessarily sorted.

        weights - an array holding the weights for the values array

        indicesList - a list holding the indices of the sorted values array

        percentile - the xth percentile the user wants to compute

    Output:
        The value in the values array corresponding to the xth percentile
    '''

    # initialize the weighted sum
    sum_weight = 0.0

    # step through the sorted values array and increment the weighted sum until
    # it is equivalent to the xth percentile
    for idx in indicesList:
        # increment the weighted sum
        sum_weight += weights[idx]

        # if the weighted sum meets the xth percentile value, exit the loop
        if sum_weight >= percentile:
            break

    # return the xth percentile value
    return values[idx]


def compute_rms(values, weights):
    '''
    This function computes the weihted RMS (root-mean-square) of a given
    metric

    Input:
        values - array holding the values of the metric in question

        weights - an array holding the weights for the values array

    Output:
        rms - the weighted RMS of the metric in the values array
    '''

    # initialize the RMS sum
    rms_sum = 0.0

    # step through the values array and sum the weighted square of the values
    for i, val in enumerate(values):
        rms_sum = rms_sum + weights[i]*val*val

    # compute and return the RMS
    rms = np.sqrt(rms_sum/np.sum(weights))

    return rms


def compute_dop_grid(prn_alm_Dic, wna, toa, propEpoch, longrid, latgrid, elev_mask,
                     dop_grid_out_file, writeFiles=False):
    '''
    This function computes the DOP metrics for a rectangular grid provided by
    the user.

    Input:
        prn_alm_Dic - Dictionary holding almanac data for each PRN
        wna - Almanac GPS week number
        toa - Almanac time of applicability (GPS seconds of week) 
        prop_Epoch - Epoch at which to compute the DOP metrics (list)
                     List Format: [year, month, day, hour, minute, sec]
        longrid - np array of the longitude grid values [degrees]
        latgrid - np arrray of the latitude grid values [degrees]
        elev_mask - Elevation angle above which satellites are considered
                    visible [deg]
        dop_grid_out_file - file to output DOP metrics to for each latitude,
                            longitude grid point
        writeFiles - boolean flag. Toggles whether DOP metrics should be
                     written to a text file

    Output:
        dop_grid - np array containing the DOP metrics for each latitude,
                   longitude grid point. This array is used to plot the DOP
                   metrics in Python, if desired
                   Shape: (LengthLatitudeGrid, LengthLongitudeGrid, 6)
                           Last Dimenstion contains: GDOP, PDOP, HDOP, VDOP,
                                                     TDOP, NumVisSats
        dop_grid2 - np array containing the DOP metrics for each latitude,
                   longitude grid point. This array is used to compute
                   the DOP metric stats for the whole grid
                   Shape: (LengthLatitudeGrid*LengthLongitudeGrid, 8)
                           Last Dimenstion contains: Latitude [deg],
                                                     Longitude [deg], GDOP,
                                                     PDOP, HDOP, VDOP,
                                                     TDOP, NumVisSats
    '''
    
    # semi-circles to radians conversion factor
    pi = 3.1415926535898  # ICD200 value of pi

    # Determine the numer of GPS satellites for which legacy navigation message
    # data was extracted from the GDAP database
    nsats = int(len(prn_alm_Dic.keys()))

    # Determine the time at which to evaluate the navigation message
    year = propEpoch[0]
    month = propEpoch[1]
    day = propEpoch[2]
    hr = propEpoch[3]
    mnt = propEpoch[4]
    sec = propEpoch[5]
    t_curr = hr*3600 + mnt*60 + sec

    # Convert the time to a Julian Date
    jdmsg = tconv.TimeConversion().cal2jd(year, month, day + t_curr/86400.)

    # Convert the time to GPS time (GPS week and seconds of week)
    gpswk, sow, rollover = tconv.TimeConversion().jd2gps(jdmsg)

    # Initialize an array to hold satellite ECEF positions for all GPS satellites
    satPosArray = np.zeros((nsats, 3))

    i = 0

    # TODO
    # compute satellite positions from navigation message for each GPS satellite
    for prn in prn_alm_Dic.keys():
        # extract orbital elements from almanac
        # NOTE: angles are in semi-circles. Multiply by pi to convert to
        # radians
        msg2use = prn_alm_Dic[prn]
        rootA = msg2use["roota"] 
        ecc = msg2use["ecc"]
        # NOTE: inclination = reference inclination (0.3 semi-circles)
        #                     + inclination offset
        # See Table 20-VI of ICD200
        inc = (msg2use["incoff"] + 0.3)*pi
        raan = msg2use["glan"]*pi
        raandot = msg2use["raanrate"]*pi 
        argp = msg2use["argp"] *pi
        m0 = msg2use["m0"] *pi

        # satellite position in ECEF coordinates [meters]
        # TODO
        satPos = nav2xyz.NavMsg2XYZ(
            rootA, 
            ecc, 
            inc, 
            raan, 
            raandot, 
            argp, 
            m0, 
            wna, 
            toa, 
            gpswk % 1024, 
            sow, 
            semicir=False)

        # store the satellite position in the GPS satellite position array
        satPosArray[i, :] = satPos
        i = i + 1

    # Create a grid to hold DOP metrics and number of visible satellites
    dop_grid = np.zeros((len(latgrid), len(longrid), 6))

    dop_grid2 = np.zeros((len(latgrid)*len(longrid), 8))

    # check total grid run time
    start_grid_time = time.time()

    # create array to store run time for each grid point
    grid_p_runtime = np.zeros(len(latgrid)*len(longrid))

    # create array to store run time for each dop computation
    dop_p_runtime = np.zeros(len(latgrid)*len(longrid))

    # compute the dop metrics at each grid point, using a separate process
    # for each latitude
    pool = mp.Pool()
    results = list(pool.map(compute_dop_grid_row,
                            [(row, latgrid, longrid, nsats, satPosArray, elev_mask)
                            for row in np.arange(0, len(latgrid))]))

    for row in range(len(latgrid)):
        for col in range(len(longrid)):
            curr_idx = row * len(longrid) + col
            dop_grid2[curr_idx][0] = latgrid[row]
            dop_grid2[curr_idx][1] = longrid[col]
            grid_p_runtime[curr_idx] = results[row][0][col]
            dop_p_runtime[curr_idx] = results[row][1][col]
            dop_grid[row][col][0] = dop_grid2[curr_idx][2] = results[row][2][col]
            dop_grid[row][col][1] = dop_grid2[curr_idx][3] = results[row][3][col]
            dop_grid[row][col][2] = dop_grid2[curr_idx][4] = results[row][4][col]
            dop_grid[row][col][3] = dop_grid2[curr_idx][5] = results[row][5][col]
            dop_grid[row][col][4] = dop_grid2[curr_idx][6] = results[row][6][col]
            dop_grid[row][col][4] = dop_grid2[curr_idx][6] = results[row][6][col]
            dop_grid[row][col][5] = dop_grid2[curr_idx][7] = results[row][7][col]


    # if the grid DOP metrics should be output to a file
    if writeFiles:
        dop_grid_f = open(dop_grid_out_file, 'w')
        # write file header for each column
        dop_grid_f.write('LatitudeDegrees LongitudeDegrees GDOP PDOP HDOP'
                         + ' VDOP TDOP NumInView\n')
        for idx in dop_grid2:
            lat, lon, gdop, pdop, hdop, vdop, tdop, nvis = idx
            # write to dop grid output file
            dop_grid_f.write('%.2f %.2f %.2f %.2f %.2f %.2f %.2f %d\n'
                                 % (lat, lon, gdop, pdop, hdop, vdop, tdop,
                                    nvis))
        # Close the output file
        dop_grid_f.close()

    # run time statistics for each grid point
    min_p_time = np.min(grid_p_runtime)
    avg_p_time = np.mean(grid_p_runtime)
    max_p_time = np.max(grid_p_runtime)
    std_p_time = np.std(grid_p_runtime)
    var_p_time = np.var(grid_p_runtime)
    med_p_time = np.median(grid_p_runtime)

    # determine the total grid run time
    grid_runtime = time.time() - start_grid_time

    # print the run time stats
    print('Runtime statistics for all the processsing for each grid point:')
    print('total grid runtime (seconds): ', grid_runtime)
    print('min grid point time (seconds): ', min_p_time)
    print('mean grid point time (seconds): ', avg_p_time)
    print('max grid point time (seconds): ', max_p_time)
    print('std grid point time (seconds): ', std_p_time)
    print('variance grid point time (seconds): ', var_p_time)
    print('median grid point time (seconds): ', med_p_time)
    print('\n')
    print('Runtime statistics for just the DOP computation for each grid point:')
    print('min grid point dop runtime (seconds): ', np.min(dop_p_runtime))
    print('mean grid point dop runtime (seconds): ', np.mean(dop_p_runtime))
    print('max grid point dop runtime (seconds): ', np.max(dop_p_runtime))
    print('std grid point dop runtime (seconds): ', np.std(dop_p_runtime))
    print('variance grid point dop runtime (seconds): ', np.var(dop_p_runtime))
    print('median grid point dop runtime (seconds): ', np.median(dop_p_runtime))

    # return the dop grids containing the statistics
    return dop_grid, dop_grid2


def compute_dop_grid_row(arg_list):
    row, latgrid, longrid, nsats, satPosArray, elev_mask = arg_list

    grid_p_runtime_row = np.zeros(len(longrid))
    dop_p_runtime_row = np.zeros(len(longrid))
    gdop_row = np.zeros(len(longrid))
    pdop_row = np.zeros(len(longrid))
    hdop_row = np.zeros(len(longrid))
    vdop_row = np.zeros(len(longrid))
    tdop_row = np.zeros(len(longrid))
    nvis_row = np.zeros(len(longrid))

    for col in np.arange(0, len(longrid)):
        # check the run time for each grid point
        start_point_time = time.time()

        # latitude and longitude in radians
        lat_r = np.deg2rad(latgrid[row])
        lon_r = np.deg2rad(longrid[col])

        # user latitude, longitude, height coordinates [deg, deg, meters]
        llh = [latgrid[row], longrid[col], 0.0]

        # user ECEF coordinates in meters
        user_ecef = frames.llh2ecef(llh, degrees=True)

        # local vertical unit vector in ECEF coordinates
        uhat = np.array([np.cos(lat_r)*np.cos(lon_r),
                            np.cos(lat_r)*np.sin(lon_r), np.sin(lat_r)])

        # list to hold number of visible satellites at each grid point
        vis_sats = []

        # find the satellites visible to the user at each grid point
        for i in range(0, nsats, 1):
            # user to satellite line of sight vector
            los = satPosArray[i, :] - user_ecef

            # user to satellite line of sight unit vector
            los = los/np.linalg.norm(los)

            # user ECEF coordinates unit vector
            #user_ecef_hat = user_ecef/np.linalg.norm(user_ecef)

            # find the elevation angle of the satellite from the user
            elev = np.arcsin(los.dot(uhat))

            #elev = np.arcsin(los.dot(user_ecef_hat))

            # if the elevation angle is greater than the elevation mask,
            # use the satellite for the DOP solution
            if elev >= np.deg2rad(elev_mask):
                vis_sats.append(satPosArray[i, :])

        # Determine the number of visible satellites
        nvis = len(vis_sats)

        # fill DOP grid point with nans if < 4 satellites are visible (i.e.,
        # no DOP solution exists)
        if nvis < 4:
            gdop = np.nan
            pdop = np.nan
            hdop = np.nan
            vdop = np.nan
            tdop = np.nan

        # compute the DOP metrics if 4 or more satellites are visible
        if len(vis_sats) >= 4:
            # check the run time for each grid point
            start_dop_time = time.time()
            gdop, pdop, hdop, vdop, tdop = calc_dop(llh, vis_sats)
            dop_p_runtime_row[col] = time.time() - start_dop_time

        # fill the DOP grid point with computed DOP metrics
        # this dop grid can be used to create plots of the DOP metrics
        # using the python matplotlib.pyplot contourf function
        gdop_row[col] = gdop
        pdop_row[col] = pdop
        hdop_row[col] = hdop
        vdop_row[col] = vdop
        tdop_row[col] = tdop
        nvis_row[col] = nvis

        # this dop grid is needed to compute the dop stats
        # dop_grid2[curr_idx, 0] = latgrid[row]
        # dop_grid2[curr_idx, 1] = longrid[col]
        # dop_grid2[curr_idx, 2] = gdop
        # dop_grid2[curr_idx, 3] = pdop
        # dop_grid2[curr_idx, 4] = hdop
        # dop_grid2[curr_idx, 5] = vdop
        # dop_grid2[curr_idx, 6] = tdop
        # dop_grid2[curr_idx, 7] = nvis

        # remove the list with the visible number of satellites before going
        # to the next grid point
        del vis_sats[:]

        # determine run time for the grid point
        grid_p_runtime_row[col] = time.time() - start_point_time
    return grid_p_runtime_row, dop_p_runtime_row, gdop_row, pdop_row, hdop_row, vdop_row, tdop_row, nvis_row


def compute_dop_stats(dop_grid, dop_stats_out_file, writeStats=True):
    '''
    This function computes the DOP stats for the grid

    Input:
        dop_grid - np array containing the DOP metrics for the grid. Obtained
                   via a call to the compute_dop_grid function
        dop_stats_out_file - file to write the DOP stats to
        writeStats - boolean flag. Toggles wether the DOP statistics are
                     written to the dop_stats_out_file

    Output:
        dop_stats_dic - array containing the statistics for each DOP metric
    '''

    # if writing the statistics to an output file
    if writeStats:
        dop_stats_f = open(dop_stats_out_file, 'w')
        # write the file column header
        dop_stats_f.write('GDOP, PDOP, HDOP, VDOP, TDOP, NumInView\n')

    # sort through the DOP grid to find the statistics: p50, p95, p98, max, rms
    # weight the statistics by equal area (i.e, by the cosine of the latitude)

    # total weight
    total_weight = np.sum(np.cos(np.deg2rad(dop_grid[:, 0])))

    # 50th percentile
    median = 0.5*total_weight
    # 95th percentile
    pct95 = 0.95*total_weight
    # 98th percentile
    pct98 = 0.98*total_weight

    # array to hold the statistics for each DOP metric
    dop_stats = np.zeros((5, 6))

    dop_stats_dic = {}

    metric = ['GDOP', 'PDOP', 'HDOP', 'VDOP', 'TDOP', 'IN VIEW']

    # list of each of the computed statistics
    stat = ['MED', 'P95', 'P98', 'RMS', 'MAX']

    # array to hold the weights for each grid point. The weight of each grid
    # point is the area enclosed by each grid point
    lat_weights = np.cos(np.deg2rad(dop_grid[:, 0]))

    # compute the statistics for each DOP metric
    for j in range(2, 8, 1):
        # Find the indices that sorth the given DOP metric in ascending order
        dop_idx_sort = np.argsort(dop_grid[:, j])

        # compute the 50th percentile
        dop_p50 = compute_percentile(dop_grid[:, j], lat_weights,
                                     dop_idx_sort, median)

        # compute the 95th percentile
        dop_p95 = compute_percentile(dop_grid[:, j], lat_weights,
                                     dop_idx_sort, pct95)

        # compute the 98th percentile
        dop_p98 = compute_percentile(dop_grid[:, j], lat_weights,
                                     dop_idx_sort, pct98)

        # compute the RMS
        dop_rms = compute_rms(dop_grid[:, j], lat_weights)

        # compute the maximum
        dop_max = np.max(dop_grid[:, j])

        # store the statitics for each metric in an array
#        dop_stats[:, j - 2] = np.array([dop_p50, dop_p95, dop_p98, dop_rms,
#                                       dop_max]).T

        # store metrics in dictionary
        dop_stats_dic[metric[j-2]] = {'MED': dop_p50, 'P95': dop_p95,
                                      'P98': dop_p98, 'RMS': dop_rms,
                                      'MAX': dop_max}

    # if writing the statistics to an output file
    if writeStats:
        # write the statistics to an output file
#        for si, s in enumerate(stat):
#            dop_stats_f.write('%s %4.2f %4.2f %4.2f %4.2f %4.2f %4.2f\n'
#                              % (s, dop_stats[si, 0], dop_stats[si, 1],
#                                 dop_stats[si, 2], dop_stats[si, 3],
#                                 dop_stats[si, 4], dop_stats[si, 5]))

        # write to file using the dictionary
        for s in stat:
            dop_stats_f.write('%s %4.2f %4.2f %4.2f %4.2f %4.2f %4.2f\n'
                             % (s, dop_stats_dic['GDOP'][s],
                                dop_stats_dic['PDOP'][s],
                                dop_stats_dic['HDOP'][s],
                                dop_stats_dic['VDOP'][s],
                                dop_stats_dic['TDOP'][s],
                                dop_stats_dic['IN VIEW'][s]))

    # list of each of the computed statistics
#    stat = ['MED', 'P95', 'P98', 'RMS', 'MAX']

    # if writing the statistics to an output file
    if writeStats:
        # Close the output files
        dop_stats_f.close()

    # return the dop stats dictionary
    return dop_stats_dic


if __name__ == "__main__":
    time_key = os.getenv('TIME_KEY', None)
    dt_time = datetime.datetime.strptime(time_key, RFC_3339_FORMAT)
    propEpoch = [dt_time.year, dt_time.month, dt_time.day, dt_time.hour, dt_time.minute, dt_time.second]
    # SEM almanac online source: https://www.navcen.uscg.gov/?pageName=gpsAlmanacs
    # SEM almanac file location
    sem_file = os.getenv('SEM_ALM_FILE', 'current_sem.txt')
    # DOP output file
    output_file = os.getenv('DOP_OUTPUT_FILE', 'dop_output.txt')
    longrid = np.linspace(-180, 180, 500 + 1)  # Latitude values in deg
    latgrid = np.linspace(-90, 90, 250 + 1)  # Longitude Value in deg
    
    # Elevation angle below which satellites are not considered visible
    elev_mask = 5.0  # degrees
    wna, toa, alm, prn2svn = utils.sem_alm(sem_file)
    dop_grid_for_plot, dop_grid_for_stats = compute_dop_grid(alm, wna, toa, propEpoch, longrid, latgrid, elev_mask, output_file, writeFiles=True)
