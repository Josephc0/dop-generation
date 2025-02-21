'''
#==================================================================
# PYTHON CODE FOR TIME CONVERSION BETWEEN DIFFERENT TIME SYSTEMS
# This code was developed in MATLAB by Michael R. Craymer. It was
# converted to Python to aid in the analysis for the L-Band Monitor.
#
# The open source code can be found at the following link:
#http://www.mathworks.com/matlabcentral/fileexchange/15285-geodetic-toolbox/content/geodetic/gps2jd.m
#
# Original Author: Michael R. Craymer
# Modified by: Mark Mendiola (SED/SASS/NGSD)
# Revised: 03/24/2020
#==================================================================
'''

# Import required modules
import numpy as np


class TimeConversion:
    # ======================================================================
    # Class handle conversions between various time systems
    # ======================================================================

    def __init__(self, epoch=None):
        self.epoch = epoch

    def cal2jd(self, yr, mn, dy):
        '''
        # =====================================================================
        # CAL2JD  Converts calendar date to Julian date using algorithm
        #   from "Practical Ephemeris Calculations" by Oliver Montenbruck
        #   (Springer-Verlag, 1989). Uses astronomical year for B.C. dates
        #   (2 BC = -1 yr). Non-vectorized version. See also DOY2JD, GPS2JD,
        #   JD2CAL, JD2DOW, JD2DOY, JD2GPS, JD2YR, YR2JD.
        #
        # Version: 2011-11-13
        #
        # Usage:   jd=cal2jd(yr,mn,dy)
        #
        # Input:   yr - calendar year (4-digit including century)
        #          mn - calendar month
        #          dy - calendar day (including factional day)
        #
        # Output:  jd - jJulian date
        #
        # Copyright (c) 2011, Michael R. Craymer
        # All rights reserved.
        # Email: mike@craymer.com
        # =====================================================================
        '''

        if (mn < 1 or mn > 12):
            raise ValueError('ValueError: Invalid input month "mn".' +
                             ' "mn" must be between 1 and 12')
            return

        if (dy < 1):
            if ((mn == 2 and dy > 29) or (any([x==mn for x in [3, 5, 9, 11]]) and dy > 30) or (dy > 31)):
                raise ValueError('ValueError: Invalid input day "dy".' +
                                 ' "dy" out of range for input month "mn"')
                return

        if (mn > 2):
            y = yr
            m = mn
        else:
            y = yr - 1
            m = mn + 12

        # Last day of Julian calendar (1582.10.04 Noon)
        date1 = 4.5 + 31*(10 + 12*1582)
        # First day of Gregorian calendar (1582.10.15 Noon)
        date2 = 15.5 + 31*(10 + 12*1582)
        date = dy + 31*(mn + 12*yr)
        if (date <= date1):
            b = -2
        elif (date >= date2):
            b = int(np.fix(y/400)) - int(np.fix(y/100))
        else:
            raise ValueError('ValueError: Invalid "date". Dates between' +
                             ' October 5 & 15, 1582 do not exist')
            return

        if (y > 0):
            jd = int(np.fix(365.25*y)) + int(np.fix(30.6001*(m+1))) + b + \
                 1720996.5 + dy
        else:
            jd = int(np.fix(365.25*y-0.75)) + int(np.fix(30.6001*(m+1))) + \
                 b + 1720996.5 + dy

        return jd

    def doy2jd(self, yr, doy):
        '''
        # =====================================================================
        # DOY2JD  Converts year and day of year to Julian date.
        #   Non-vectorized version. See also CAL2JD, GPS2JD,
        #   JD2CAL, JD2DOW, JD2DOY, JD2GPS, JD2YR, YR2JD.
        #
        # Version: 24 Apr 99
        #
        # Usage:   jd=doy2jd(yr,doy)
        #
        # Input:    yr - year
        #          doy - day of year
        # Output:  jd  - Julian date
        #
        # Copyright (c) 2011, Michael R. Craymer
        # All rights reserved.
        # Email: mike@craymer.com
        # =====================================================================
        '''

        jd = self.cal2jd(yr, 1, 0) + doy
        return jd

    def jd2mjd(self, jd):
        '''
        # =====================================================================
        # JD2MJD  Converts Julian Date to Modified Julian Date.
        #   Non-vectorized version. See also CAL2JD, DOY2JD, GPS2JD,
        #   JD2CAL, JD2DOW, JD2DOY, JD2GPS, JD2YR, MJD2JD, YR2JD.
        #
        # Version: 2010-03-25
        #
        # Usage:   mjd=jd2mjd(jd)
        #
        # Input:   jd  - Julian date
        # Output:  mjd - Modified Julian date
        #
        # Copyright (c) 2011, Michael R. Craymer
        # All rights reserved.
        # Email: mike@craymer.com
        # =====================================================================
        '''

        mjd = jd - 2400000.5
        return mjd

    def jd2gps(self, jd):
        '''
        # =====================================================================
        # JD2GPS  Converts Julian date to GPS week number (since
        #   1980.01.06) and seconds of week. Non-vectorized version.
        #   See also CAL2JD, DOY2JD, GPS2JD, JD2CAL, JD2DOW, JD2DOY,
        #   JD2YR, YR2JD.
        #
        # Version: 05 May 2010
        #
        # Usage:   [gpsweek,sow,rollover]=jd2gps(jd)
        #
        # Input:   jd       - Julian date
        #
        # Output:  gpsweek  - GPS week number
        #          sow      - seconds of week since 0 hr, Sun.
        #          rollover - number of GPS week rollovers (modulus 1024)
        #
        # Copyright (c) 2011, Michael R. Craymer
        # All rights reserved.
        # Email: mike@craymer.com
        # =====================================================================
        '''

        if (jd < 0):
            raise ValueError('ValueError: Invalid Julian Date "jd". Julian ' +
                             'date "jd" must be greater than or equal to zero')
            return

        jdgps = self.cal2jd(1980, 1, 6)  # beginning of GPS week numbering
        nweek = int(np.fix((jd - jdgps)/7))
        sow = (jd - (jdgps + nweek*7)) * 3600*24
        rollover = int(np.fix(nweek/1024))  # rollover every 1024 weeks
        #%gpsweek = mod(nweek,1024);
        gpsweek = nweek

        return [gpsweek, sow, rollover]

    def gps2jd(self, gpsweek, sow, rollover):
        '''
        # =====================================================================
        # GPS2JD  Converts GPS week number (since 1980.01.06) and
        #   seconds of week to Julian date. Non-vectorized version.
        #   See also CAL2JD, DOY2JD, JD2CAL, JD2DOW, JD2DOY, JD2GPS,
        #   JD2YR, YR2JD.
        #
        # Version: 28 Sep 03
        # Usage:   jd=gps2jd(gpsweek,sow,rollover)
        #
        # Input:   gpsweek  - GPS week number
        #          sow      - seconds of week since 0 hr, Sun (default=0)
        #          rollover - number of GPS week rollovers (default=0)
        # Output:  jd       - Julian date
        #
        # Copyright (c) 2011, Michael R. Craymer
        # All rights reserved.
        # Email: mike@craymer.com
        # =====================================================================
        '''

        if gpsweek <= 0:
            raise ValueError('ValueError: Invalid GPS week number "gpsweek".' +
                             ' GPS week must be greater than or equal to zero')
            return

        # beginning of GPS week numbering
        jdgps = self.cal2jd(1980, 1, 6)
        # account for rollovers every 1024 weeks
        nweek = gpsweek + 1024*rollover
        # compute the Julian date
        jd = jdgps + nweek*7 + sow/3600./24.

        return jd

    def jd2cal(self, jd):
        '''
        # ======================================================================
        # JD2CAL  Converts Julian date to calendar date using algorithm
        #   from "Practical Ephemeris Calculations" by Oliver Montenbruck
        #   (Springer-Verlag, 1989). Must use astronomical year for B.C.
        #   dates (2 BC = -1 yr). Non-vectorized version. See also CAL2JD,
        #   DOY2JD, GPS2JD, JD2DOW, JD2DOY, JD2GPS, JD2YR, YR2JD.
        # Version: 24 Apr 99
        # Usage:   [yr, mn, dy]=jd2cal(jd)
        # Input:   jd - Julian date
        # Output:  yr - year of calendar date
        #          mn - month of calendar date
        #          dy - day of calendar date (including decimal)

        # Copyright (c) 2011, Michael R. Craymer
        # All rights reserved.
        # Email: mike@craymer.com
        # ======================================================================
        '''

        if jd < 0:
            raise ValueError('ValueError: Invalid Julian Date "jd". Julian ' +
                             'date "jd" must be greater than or equal to zero')
            return

        a = np.fix(jd + 0.5)
        if a < 2299161:
            c = a + 1524
        else:
            b = np.fix((a - 1867216.25) / 36524.25)
            c = a + b - np.fix(b/4.) + 1525
        d = np.fix((c - 122.1)/365.25)
        e = np.fix(365.25*d)
        f = np.fix((c - e) / 30.6001)
        dy = c - e - np.fix(30.6001*f) + np.remainder((jd + 0.5), a)
        mn = f - 1 - 12*np.fix(f/14.)
        yr = d - 4715 - np.fix((7 + mn)/10.)

        return [yr, mn, dy]
    
    def sec2hms(self, seconds):
        '''
        function to convert seconds in a day to hour, minute, sec
        
        Input:  seconds - seconds of day (0-86400)
        
        Output: hr - hour of the day (0-24)
                minute - minute into the hour (0-60)
                sec - seconds into the minute (0-60)           
        '''
        
        minute, sec = divmod(seconds, 60)
        hour, minute = divmod(minute, 60)
        
        return [hour, minute, sec]

    def jd2ymdhms(self, jd):
        '''
        function to convert a Julian Date to the equivalent
        year, month, day, hour, minute, sec
        
        Input:  jd - Julian Date
            
        Output: yr - Year of calendar date
                mn - Month of calendar date
                day - Day of calendar date
                hr - Hour of calendar date
                minute - Minute of calendar date
                sec - Second of calendar date
        '''
        
        # find the year, month, and fractional day
        [yr, mn, dy] = self.jd2cal(jd)

        # find the integer day
        day = dy//1

        # find the fractional part of the day
        dy_frac = dy - day

        # convert the fractin part of the day to seconds
        soday = dy_frac*86400

        # find the hour, min, sec into the day
        [hr, minute, sec] = self.sec2hms(soday)

        # return the calendar date
        return [int(yr), int(mn), int(day), int(hr), int(minute), sec]

    def jday(self, yr, mn, dy, hr, minute, sec):
        '''
        function to compute the Julian date given the year, month, day,
        hour, min, sec
        
        Input:  yr - Year of calendar date
                mn - Month of calendar date
                day - Day of calendar date
                hr - Hour of calendar date
                minute - Minute of calendar date
                sec - Second of calendar date
            
        Output: jd - Julian Date
        '''
        # Compute the fractional day
        day_frac = hr*3600. + minute*60 + sec
        day_frac = day_frac/86400.0 + dy

        # compute the Juian Date
        jd = self.cal2jd(yr, mn, day_frac)

        return jd