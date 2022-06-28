"""
This python file is used for reading and preparing the VEMMIS data

Created by: Bob van Dillen
Date: 22-11-2021
"""

import datetime
import pandas as pd
import numpy as np
import os
import bluesky as bs
from bluesky.tools import aero
from bluesky.tools.geo import qdrpos
from bluesky.tools.aero import kts, ft

"""
Classes
"""


class VEMMISRead:
    """
    Class definition: Read and prepare the VEMMIS data
    Methods:
            read_data():        Read vemmis csv files
            delete_nan():       Delete data points with NaN in the relevant columns
            convert_data():     Convert data to correct data types and determine the actual time
            get_credeltime():   Get the create and delete time (first and last data point)
            relevant_data():    Select relevant data
            get_coordinates():  Calculate coordinates from x and y position
            get_altitude():     Determine altitude from MODE_C
            get_cas():          Determine the calibrated airspeed
            merge_data():       Merge flights data into the other data, to get e.g. callsign
            sort_data():        Sort the data by time
            get_simtime():      Determine the simulation time and optionally apply the fixed update rate
            get_datetime():     Get the date and time for the simulation
            get_initial():      Get the initial commands
            get_trackdata():    Get the track data for the simulation

    Created by: Bob van Dillen
    Date: 22-11-2021
    """

    def __init__(self, data_path, date0=None, time0=None, deltat=None):
        self.data_path = data_path

        self.date0 = date0
        self.time0 = time0

        self.deltat = deltat

        self.lat0 = 52+18/60+29/3600
        self.lon0 = 4+45/60+51/3600

        self.flights = None
        self.flighttimes = None
        self.tracks = None
        self.flightdata = None
        self.routedata = None
        self.trackdata = None
        self.takeoffs = None
        self.landings = None

        self.datetime0 = None

        self.read_data()
        self.delete_nan()
        self.convert_data()
        self.get_credeltime()
        self.relevant_data()
        self.get_coordinates()
        self.get_altitude()
        self.get_cas()
        self.merge_data()
        self.sort_data()
        self.get_simtime()

    def read_data(self):
        """
        Function: Read vemmis csv files
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 22-11-2021
        """

        for root, dirs, files in os.walk(self.data_path):
            # Loop over files
            for file in files:
                if file.upper().startswith('FLIGHTS'):
                    # Read flight data
                    self.flights = pd.read_csv(self.data_path+'\\'+file, sep=';')
                elif file.upper().startswith('FLIGHTTIMES'):
                    # Read flight times data
                    self.flighttimes = pd.read_csv(self.data_path+'\\'+file, sep=';')
                elif file.upper().startswith('TRACK'):
                    # Read track data
                    self.tracks = pd.read_csv(self.data_path+'\\'+file, sep=';')
                elif file.upper().startswith('TAKEOFFS'):
                    # Read take-off data
                    self.takeoffs = pd.read_csv(self.data_path+'\\'+file, sep=';')
                elif file.upper().startswith('LANDINGS'):
                    # Read landing data
                    self.landings = pd.read_csv(self.data_path+'\\'+file, sep=';')

    def delete_nan(self):
        """
        Function: Delete data points with NaN in the relevant columns
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date = 25-11-2021
        """

        # Flight data
        self.flights = self.flights.dropna(subset=['FLIGHT_ID', 'CALLSIGN', 'SSR', 'ICAO_ACTYPE', 'ADEP', 'DEST',
                                                   'STATUS'])

        # Track data
        self.tracks = self.tracks.dropna(subset=['TIME', 'X', 'Y', 'MODE_C', 'SPEED', 'HEADING',
                                                 'FLIGHT_ID', 'T_START', 'T_END'])

        # Flight times data
        self.flighttimes = self.flighttimes.dropna(subset=['FLIGHT_ID', 'LOCATION_TYPE',
                                                           'LOCATION_NAME', 'TIME_TYPE', 'TIME'])

    def convert_data(self):
        """
        Function: Convert data to correct data types and determine the actual time
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date = 22-11-2021
        """

        # Flight data
        self.flights['T_UPDATE'] = pd.to_datetime(self.flights['T_UPDATE'], format="%d-%m-%Y %H:%M:%S")
        self.flights['T0'] = pd.to_datetime(self.flights['T0'], format="%d-%m-%Y %H:%M:%S")
        self.flights['SSR'] = self.flights['SSR'].astype(int)

        # Track data
        self.tracks['TIME'] = pd.to_timedelta(self.tracks['TIME']/100, unit='seconds')
        self.tracks['X'] = self.tracks['X'].astype('str').str.replace(',', '.').astype('float')
        self.tracks['Y'] = self.tracks['Y'].astype('str').str.replace(',', '.').astype('float')
        self.tracks['MODE_C'] = self.tracks['MODE_C'].astype('str').str.replace(',', '.').astype('float')
        self.tracks['TRK_ROCD'] = self.tracks['TRK_ROCD'].astype('str').str.replace(',', '.').astype('float')
        self.tracks['T_UPDATE'] = pd.to_datetime(self.tracks['T_UPDATE'], format="%d-%m-%Y %H:%M:%S")
        self.tracks['T_START'] = pd.to_datetime(self.tracks['T_START'], format="%d-%m-%Y %H:%M:%S")
        self.tracks['T_END'] = pd.to_datetime(self.tracks['T_END'], format="%d-%m-%Y %H:%M:%S")
        # Compute actual time
        self.tracks['ACTUAL_TIME'] = self.tracks['T_START'] + self.tracks['TIME']

    def get_credeltime(self):
        """
        Function: Get the create and delete time (first and last data point)
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 17-1-2022
        """

        # Sort on time
        self.tracks.sort_values(by=['ACTUAL_TIME'], inplace=True)

        # Get time first data point
        time_create = self.tracks[['FLIGHT_ID', 'ACTUAL_TIME']].drop_duplicates(subset='FLIGHT_ID', keep='first')
        time_create.rename(columns={'ACTUAL_TIME': 'TIME_START'}, inplace=True)
        # Get time last data point
        time_delete = self.tracks[['FLIGHT_ID', 'ACTUAL_TIME']].drop_duplicates(subset='FLIGHT_ID', keep='last')
        time_delete.rename(columns={'ACTUAL_TIME': 'TIME_END'}, inplace=True)

        # Add to create and delete time to flights data
        self.flights = pd.merge(self.flights, time_create, on='FLIGHT_ID')
        self.flights = pd.merge(self.flights, time_delete, on='FLIGHT_ID')

    def relevant_data(self):
        """
        Function: Select relevant data
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 22-11-2021
        """

        # Cancelled flights
        indx_delete = self.flights.index[self.flights['STATUS'].str.contains('CANCELLED')]
        self.flights.drop(indx_delete, inplace=True)
        # Drop duplicates
        self.flights.drop_duplicates(subset='FLIGHT_ID', keep='first', inplace=True)

        # Waypoints
        self.flighttimes = self.flighttimes.loc[self.flighttimes['TIME_TYPE'] == 'ACTUAL']
        self.flighttimes = self.flighttimes.loc[self.flighttimes['LOCATION_TYPE'] == 'RP']

        # Start time
        if self.date0 and self.time0:
            # Convert to datetime
            self.date0 = self.date0.split('-')
            self.time0 = datetime.datetime.strptime(self.time0, '%H:%M:%S')
            self.time0 = self.time0.replace(year=int(self.date0[2]),
                                            month=int(self.date0[1]),
                                            day=int(self.date0[0]))

            # Apply start time
            self.tracks = self.tracks.loc[self.tracks['ACTUAL_TIME'] >= self.time0]

    def get_coordinates(self):
        """
        Function: Calculate coordinates from x and y position
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date = 22-11-2021
        """

        # Compute distance in nm
        self.tracks['LATITUDE'] = self.tracks['X']/128
        self.tracks['LONGITUDE'] = self.tracks['Y']/128

        # Compute angle
        qdr = np.degrees(np.arctan2(self.tracks['LATITUDE'], self.tracks['LONGITUDE']))
        qdr = np.where(qdr < 0, qdr+360, qdr)
        # Compute distance from ARP
        d = np.array(np.sqrt(self.tracks['LATITUDE']**2 + self.tracks['LONGITUDE']**2))

        # Compute latitude and longitude, based on distance and angle from ARP
        self.tracks['LATITUDE'], self.tracks['LONGITUDE'] = qdrpos(self.lat0, self.lon0, qdr, d)

    def get_altitude(self):
        """
        Function: Determine altitude from MODE_C
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date = 22-11-2021
        """

        self.tracks['ALTITUDE'] = self.tracks['MODE_C']*100

    def get_cas(self):
        """
        Function: Determine the calibrated airspeed
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 20-1-2022
        """

        # Assume TAS = GS
        self.tracks['CAS'] = aero.vtas2cas(self.tracks['SPEED']*aero.kts, self.tracks['ALTITUDE']*aero.ft)/aero.kts

    def merge_data(self):
        """
        Function: Merge flights data into the other data, to get e.g. callsign
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date = 22-11-2021
        """

        # Add first data point to flight data
        self.flightdata = pd.merge(self.flights, self.tracks[['FLIGHT_ID', 'ACTUAL_TIME', 'LATITUDE', 'LONGITUDE',
                                                              'HEADING', 'ALTITUDE', 'CAS']], on='FLIGHT_ID')
        self.flightdata.sort_values(by=['ACTUAL_TIME'], inplace=True)
        self.flightdata.drop_duplicates(subset='FLIGHT_ID', keep='first', inplace=True)
        # Add SID to flight data
        self.flightdata = pd.merge(self.flightdata, self.takeoffs[['FLIGHT_ID', 'SID', 'RUNWAY']],
                                   on='FLIGHT_ID', how='left')
        self.flightdata.rename(columns={'RUNWAY': 'RUNWAY_OUT'}, inplace=True)
        # Add ARR to flight data
        self.flightdata = pd.merge(self.flightdata, self.landings[['FLIGHT_ID', 'STACK']],
                                   on='FLIGHT_ID', how='left')

        # Add callsign to route data
        self.routedata = pd.merge(self.flighttimes, self.flights[['FLIGHT_ID', 'CALLSIGN']], on='FLIGHT_ID')

        # Add callsign to track data
        self.trackdata = pd.merge(self.tracks, self.flights[['FLIGHT_ID', 'CALLSIGN']], on='FLIGHT_ID')

    def sort_data(self):
        """
        Function: Sort the data by time
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date = 22-11-2021
        """

        # Sort
        self.flightdata.sort_values(by=['TIME_START'], inplace=True)
        self.trackdata.sort_values(by=['ACTUAL_TIME'], inplace=True)

        # Take out first and last data point for safe aircraft create/delete
        indx_first = list(self.trackdata.index[~self.trackdata.duplicated(subset='FLIGHT_ID', keep='first')])
        indx_last = list(self.trackdata.index[~self.trackdata.duplicated(subset='FLIGHT_ID', keep='last')])
        self.trackdata.drop(indx_first+indx_last, inplace=True)

        # Select flights that have data points
        flightids = self.trackdata['FLIGHT_ID'].unique()
        self.flightdata = self.flightdata.loc[self.flightdata['FLIGHT_ID'].isin(flightids)]

        # Sort again
        self.flightdata.sort_values(by=['TIME_START'], inplace=True)
        self.trackdata.sort_values(by=['ACTUAL_TIME'], inplace=True)

    def get_simtime(self):
        """
        Function: Determine the simulation time and optionally apply the fixed update rate
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date = 22-11-2021
        """

        # Get initial date and time
        self.datetime0 = min(self.trackdata['ACTUAL_TIME'])

        # Compute simulation time
        self.flightdata['SIM_START'] = (self.flightdata['TIME_START'] - self.datetime0).dt.total_seconds()
        self.flightdata['SIM_START'][self.flightdata['SIM_START'] < 0] = 0
        self.flightdata['SIM_END'] = (self.flightdata['TIME_END'] - self.datetime0).dt.total_seconds()
        self.trackdata['SIM_TIME'] = (self.trackdata['ACTUAL_TIME'] - self.datetime0).dt.total_seconds()

        # Apply fixed update rate
        if self.deltat:
            self.flightdata['SIM_START'] = (self.flightdata['SIM_START'] / self.deltat).apply(np.ceil) * self.deltat
            self.flightdata['SIM_END'] = (self.flightdata['SIM_END'] / self.deltat).apply(np.ceil) * self.deltat
            self.trackdata['SIM_TIME'] = (self.trackdata['SIM_TIME'] / self.deltat).apply(np.ceil) * self.deltat
            self.trackdata.drop_duplicates(subset=['SIM_TIME', 'CALLSIGN'], keep='last', inplace=True)

    # def get_wpts(self, callsign, time_create, orig, dest):
    #     """
    #     Function: Get the commands string for adding the waypoints
    #     Args:
    #         callsign:       callsign [str]
    #         time_create:    simulation time of aircraft create [float]
    #         orig:           origin [str]
    #         dest:           destination [str]
    #     Returns:
    #         strlst:         list with strings for adding waypoints
    #
    #     Created: Bob van Dillen
    #     Date: 1-12-2021
    #     """
    #
    #     route = self.routedata.loc[self.routedata['CALLSIGN'] == callsign]
    #
    #     strlst = []
    #     tlst = []
    #     wptstr = ""
    #     for wpt in range(len(route)):
    #         wptname = route['LOCATION_NAME'].iloc[wpt]
    #         wpttime = route['SIM_TIME'].iloc[wpt]
    #         if wpttime > time_create and wptname != orig and wptname != dest:
    #             if len(strlst) == 0:
    #                 strlst.append("ADDWPT "+callsign+", "+wptname)
    #                 tlst.append(time_create+0.01)  # Add 0.01 to ensure the right order
    #                 wptstr = callsign+" AFTER "+wptname+" ADDWPT "
    #             else:
    #                 strlst.append(wptstr+wptname)
    #                 tlst.append(tlst[-1]+0.01)  # Add 0.01 to ensure the right order
    #                 wptstr = callsign+" AFTER "+wptname+" ADDWPT "
    #
    #     return strlst, tlst

    def get_datetime(self):
        """
        Function: Get the date and time for the simulation
        Args: -
        Returns:
            day:    day of the simulation [int]
            month:  month of the simulation [int]
            year:   year of the simulation [int]
            time:   time of the simulation [str]

        Created by: Bob van Dillen
        Date = 25-11-2021
        """

        datetime_start = self.datetime0
        day = datetime_start.day
        month = datetime_start.month
        year = datetime_start.year
        time = datetime_start.strftime("%H:%M:%S")

        return day, month, year, time

    def get_initial(self, swdatafeed, typesim=[]):
        """
        Function: Get the initial commands
        Args:
            swdatafeed:     add aircraft to datafeed [bool]
            typesim:        flighttypes that need to be simulated (no data feed) [list]
        Returns:
            cmds:           initial commands [list]
            cmdst:          simulation time of the initial commands [list]

        Created by: Bob van Dillen
        Date: 20-1-2022
        """

        simday, simmonth, simyear, simtime = self.get_datetime()

        # Initial commands
        cmds = ["DATE "+str(simday)+", "+str(simmonth)+", "+str(simyear)+", "+simtime]
        cmdst = [0.]

        # Flight data
        acid         = self.flightdata['CALLSIGN']
        actype       = self.flightdata['ICAO_ACTYPE']
        aclat        = self.flightdata['LATITUDE'].astype(str)
        aclon        = self.flightdata['LONGITUDE'].astype(str)
        achdg        = self.flightdata['HEADING'].astype(str)
        acalt        = self.flightdata['ALTITUDE'].astype(str)
        acspd        = self.flightdata['CAS'].astype(str)
        acorig       = self.flightdata['ADEP']
        acdest       = self.flightdata['DEST']
        acflighttype = self.flightdata['FLIGHT_TYPE']
        acwtc        = self.flightdata['WTC']
        acssr        = self.flightdata['SSR'].astype(str)

        # Commands
        # Create
        cmds  += list("CRE "+acid+", "+actype+", " + aclat+", "+aclon+", "+achdg+", "+acalt+", "+acspd)
        cmdst += list(self.flightdata['SIM_START'])

        # Origin
        cmds  += list("ORIG "+acid+", "+acorig)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # Destination
        cmds  += list("DEST "+acid+", "+acdest)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # Flight type
        cmds  += list("FLIGHTTYPE "+acid+", "+acflighttype)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # WTC
        cmds  += list("WTC "+acid+", "+acwtc)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # SSR Code
        cmds  += list("SSRCODE "+acid+", "+acssr)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # SID
        outbound = self.flightdata.dropna(subset=['SID'])
        cmds    += list("SID "+outbound['CALLSIGN']+", "+outbound['SID']+", OFF")
        cmdst   += list(outbound['SIM_START'] + 0.01)

        # ARR
        inbound = self.flightdata.dropna(subset=['STACK'])
        cmds   += list("ARR "+inbound['CALLSIGN']+", "+inbound['STACK']+", OFF")
        cmdst  += list(inbound['SIM_START'] + 0.01)

        # Delete route
        cmds  += list("DELRTE "+acid)
        cmdst += list(self.flightdata['SIM_START'] + 0.02)

        # Data feed dependent commands
        if swdatafeed:
            datafeed = self.flightdata[['CALLSIGN', 'FLIGHT_TYPE', 'SIM_START', 'SIM_END']]

            # Take out flights that need to be simulated
            if 'INBOUND' in typesim:
                datafeed = datafeed.loc[datafeed['FLIGHT_TYPE'] != 'INBOUND']
            if 'OUTBOUND' in typesim:
                datafeed = datafeed.loc[datafeed['FLIGHT_TYPE'] != 'OUTBOUND']
            if 'REGIONAL' in typesim:
                datafeed = datafeed.loc[datafeed['FLIGHT_TYPE'] != 'REGIONAL']

            # Create commands for data feed flights
            # Set data feed
            cmds        += list("SETDATAFEED "+datafeed['CALLSIGN']+", VEMMIS")
            cmdst       += list(datafeed['SIM_START'] + 0.01)

            # Delete
            cmds   += list("DEL "+datafeed['CALLSIGN'])
            cmdst  += list(datafeed['SIM_END'])

        # Sort
        command_df = pd.DataFrame({'COMMAND': cmds, 'TIME': cmdst})
        command_df = command_df.sort_values(by=['TIME'])
        cmds = list(command_df['COMMAND'])
        cmdst = list(command_df['TIME'])

        return cmds, cmdst

    def get_initial_tbar(self):
        """
        Function: Get the initial commands for the T-Bar simulation
        Args: -
        Returns:
            cmds:   initial commands [list]
            cmdst:  simulation time of the initial commands [list]

        Created by: Bob van Dillen
        Date: 20-1-2022
        """

        simday, simmonth, simyear, simtime = self.get_datetime()

        # Initial commands
        cmds = ["DATE "+str(simday)+", "+str(simmonth)+", "+str(simyear)+", "+simtime]
        cmdst = [0.]

        # Flight data
        self.flightdata = self.flightdata.loc[self.flightdata['RUNWAY_OUT'] != '36L']  # No 36L departure
        acid         = self.flightdata['CALLSIGN']
        actype       = self.flightdata['ICAO_ACTYPE']
        aclat        = self.flightdata['LATITUDE'].astype(str)
        aclon        = self.flightdata['LONGITUDE'].astype(str)
        achdg        = self.flightdata['HEADING'].astype(str)
        acalt        = self.flightdata['ALTITUDE'].astype(str)
        acspd        = self.flightdata['CAS'].astype(str)
        acorig       = self.flightdata['ADEP']
        acdest       = self.flightdata['DEST']
        acflighttype = self.flightdata['FLIGHT_TYPE']
        acwtc        = self.flightdata['WTC']
        acssr        = self.flightdata['SSR'].astype(str)

        # Commands
        # Create
        cmds  += list("CRE "+acid+", "+actype+", "+aclat+", "+aclon+", "+achdg+", "+acalt+", "+acspd)
        cmdst += list(self.flightdata['SIM_START'])

        # Origin
        cmds  += list("ORIG "+acid+", "+acorig)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # Destination
        cmds  += list("DEST "+acid+", "+acdest)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # Flight type
        cmds  += list("FLIGHTTYPE "+acid+", "+acflighttype)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # WTC
        cmds  += list("WTC "+acid+", "+acwtc)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # SSR Code
        cmds  += list("SSRCODE "+acid+", "+acssr)
        cmdst += list(self.flightdata['SIM_START'] + 0.01)

        # SID
        outbound = self.flightdata.dropna(subset=['SID'])
        cmds    += list("SID "+outbound['CALLSIGN']+", "+outbound['SID']+", OFF")
        cmdst   += list(outbound['SIM_START'] + 0.01)

        # Split into inbound and other traffic
        inbound = self.flightdata.loc[self.flightdata['FLIGHT_TYPE'] == 'INBOUND']
        other = self.flightdata.loc[self.flightdata['FLIGHT_TYPE'] != 'INBOUND']

        # Split into entry sectors
        # Sector 1
        sector1 = inbound.loc[inbound['LATITUDE'] >= 52.51121388888889]
        #print(sector1)
        sector1 = sector1.loc[sector1['LONGITUDE'] >= 4.764166666666667]
        #print(sector1)
        # Sector 2
        sector2 = inbound.loc[inbound['LATITUDE'] < 52.51121388888889]
        #print(sector2)
        sector2 = sector2.loc[sector2['LONGITUDE'] >= 4.764166666666667]
        #print(sector2)
        # Sector 3/4
        sector34 = inbound.loc[inbound['LATITUDE'] <= 52.447925]
        print(sector34)
        sector34 = sector34.loc[sector34['LONGITUDE'] < 4.764166666666667]
        #bla = sector34.loc[]
        print(sector34)
        # Sector 3
        sector3 = inbound.loc[inbound['LATITUDE'] <= 51.746687]
        sector3 = sector3.loc[sector3['LONGITUDE'] < 4.764166666666667]
        sector3 = sector3.loc[sector3['LONGITUDE'] > 2.727561]
        # Sector 4
        sector4 = inbound.loc[inbound['LATITUDE'] <= 52.447925]
        sector4 = sector4.loc[sector4['LATITUDE'] > 51.746687]
        sector4 = sector4.loc[sector4['LONGITUDE'] < 4.764166666666667]
        # Sector 5
        sector5 = inbound.loc[inbound['LATITUDE'] > 52.447925]
        sector5 = sector5.loc[sector5['LONGITUDE'] < 4.764166666666667]

        # Arrival
        cmds  += list("ARR "+sector1['CALLSIGN']+", NIRSI_AM603")
        cmdst += list(sector1['SIM_START'] + 0.01)

        cmds  += list("ARR "+sector2['CALLSIGN']+", NIRSI_AM603")
        cmdst += list(sector2['SIM_START'] + 0.01)

        #cmds  += list("ARR "+sector34['CALLSIGN']+", NIRSI_RIVER")
        #cmdst += list(sector34['SIM_START'] + 0.01)

        cmds += list("ARR " + sector3['CALLSIGN'] + ", NIRSI_AM603")
        cmdst += list(sector3['SIM_START'] + 0.01)

        cmds += list("ARR " + sector4['CALLSIGN'] + ", NIRSI_AM603")
        cmdst += list(sector4['SIM_START'] + 0.01)

        cmds  += list("ARR "+sector5['CALLSIGN']+", NIRSI_AM603")
        cmdst += list(sector5['SIM_START'] + 0.01)

        inother = other.dropna(subset=['STACK'])
        cmds   += list("ARR "+inother['CALLSIGN']+", "+inother['STACK']+", OFF")
        cmdst  += list(inother['SIM_START'] + 0.01)

        # Data feed dependent commands
        cmds  += list("SETDATAFEED "+other['CALLSIGN']+", VEMMIS")
        cmdst += list(other['SIM_START'] + 0.01)

        # Track label
        cmds  += list("TRACKLABEL "+other['CALLSIGN']+", OFF")
        cmdst += list(other['SIM_START'] + 0.01)

        # SSR label
        cmds  += list("SSRLABEL "+other['CALLSIGN']+", ON")
        cmdst += list(other['SIM_START'] + 0.01)

        # Delete route
        cmds  += list("DELRTE "+other['CALLSIGN'])
        cmdst += list(other['SIM_START'] + 0.02)

        # Delete
        cmds  += list("DEL "+other['CALLSIGN'])
        cmdst += list(other['SIM_END'])

        # Sort
        command_df = pd.DataFrame({'COMMAND': cmds, 'TIME': cmdst})
        command_df = command_df.sort_values(by=['TIME'])
        cmds = list(command_df['COMMAND'])
        cmdst = list(command_df['TIME'])

        return cmds, cmdst

    def get_trackdata(self):
        """
        Function: Get the track data for the simulation
        Args: -
        Returns:
            simt:       simulation time [array(float)]
            simt_i:     indices with the same simulation time [lst(lst(int))]
            flightid:   flight id [array(int/float)]
            id:         callsign [lst(str)]
            actype:     aircraft type [lst(str)]
            lat:        latitude [array(float)]
            lon:        longitude [array(float)]
            hdg:        heading [array(float)]
            alt:        altitude [array(float)]
            spd:        ground speed [array(float)]

        Created by: Bob van Dillen
        Date = 22-11-2021
        """

        simt = np.array(self.trackdata['SIM_TIME'])
        # Get the number of data points with the same time stamp
        unique, count = np.unique(simt, return_counts=True)
        simt_count = np.repeat(count, count)

        acid = list(self.trackdata['CALLSIGN'])
        lat = np.array(self.trackdata['LATITUDE'])
        lon = np.array(self.trackdata['LONGITUDE'])
        hdg = np.array(self.trackdata['HEADING'])
        alt = np.array(self.trackdata['ALTITUDE'])*aero.ft
        spd = np.array(self.trackdata['SPEED'])*aero.kts
        return simt, simt_count, acid, lat, lon, hdg, alt, spd


class VEMMISSource:
    """
    Class definition: VEMMIS data as data source for data feed
    Methods:
        reset():            Reset variables
        replay():           Read and process track data for replay mode
        initial():          Take initial aircraft positions from VEMMIS
        update_trackdata(): Update the track data for the current simulation time

    Created by: Bob van Dillen
    Date: 14-1-2022
    """

    def __init__(self):
        self.i_next = 0
        self.t_next = 0.

        self.i_max = 0
        self.running = False

        self.simt = np.array([])
        self.simt_count = np.array([])
        self.acid = []
        self.lat = np.array([])
        self.lon = np.array([])
        self.hdg = np.array([])
        self.alt = np.array([])
        self.gs = np.array([])

    def reset(self):
        """
        Function: Reset variables
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 17-1-2022
        """

        self.i_next = 0
        self.t_next = 0.

        self.i_max = 0
        self.running = False

        self.simt = np.array([])
        self.simt_count = np.array([])
        self.acid = []
        self.lat = np.array([])
        self.lon = np.array([])
        self.hdg = np.array([])
        self.alt = np.array([])
        self.gs = np.array([])

    def replay(self, datapath, date0, time0):
        """
        Function: Read and process track data for replay mode
        Args:
            datapath:   path to the folder containing the files [str]
            date0:      start date [str]
            time0:      start time [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 14-1-2022
        """

        # Prepare the data
        bs.scr.echo('Preparing data from ' + datapath + ' ...')
        vemmisdata = VEMMISRead(datapath, date0, time0, deltat=0.5)
        # Load flight data
        bs.scr.echo('Loading flight data ...')

        # initialize t-bar by uncommenting the second line below
        #commands, commandstime = vemmisdata.get_initial(swdatafeed=True)
        commands, commandstime = vemmisdata.get_initial_tbar()

        # Load track data
        bs.scr.echo('Loading track data ...')
        trackdata = vemmisdata.get_trackdata()
        self.simt = trackdata[0]
        self.simt_count = trackdata[1]
        self.acid = trackdata[2]
        self.lat = trackdata[3]
        self.lon = trackdata[4]
        self.hdg = trackdata[5]
        self.alt = trackdata[6]
        self.gs = trackdata[7]

        # Get the index and the SIM_TIME of the next data point
        self.i_next = 0
        self.t_next = self.simt[0]

        # Last data point
        self.i_max = len(self.simt) - 1
        self.running = True

        bs.scr.echo('Done')

        return commands, commandstime

    @staticmethod
    def playback(datapath, date0, time0):
        """
        Function: Take initial aircraft positions from VEMMIS
        Args:
            datapath:   path to the folder containing the files [str]
            date0:      start date [str]
            time0:      start time [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 14-1-2022
        """

        # Prepare the data
        bs.scr.echo('Preparing data from ' + datapath + ' ...')
        vemmisdata = VEMMISRead(datapath, date0, time0, deltat=0.5)

        # Load flight data
        bs.scr.echo('Loading flight data ...')
        commands, commandstime = vemmisdata.get_initial(swdatafeed=False)

        bs.scr.echo('Done')

        return commands, commandstime

    def update_trackdata(self, simtime):
        """
        Function: Update the track data for the current simulation time
        Args:
            simtime:    simulation time [float]
        Returns:
            ids:        callsigns [list]
            lat:        latitudes [array]
            lon:        longitudes [array]
            hdg:        headings [array]
            alt:        altitudes [array]
            gs:         ground speeds [array]

        Created by: Bob van Dillen
        Date: 14-1-2022
        """

        # Set running
        running = True

        # Check if the next data point is reached
        if self.t_next <= simtime:
            # Commands
            cmds = []

            # Track data index
            ac_count = self.simt_count[self.i_next]
            i0 = self.i_next  # First index
            im = self.i_next + ac_count  # Last index + 1 for slicing (e.g. i=1; ac_count=2, therefore [1:3])

            ids = self.acid[i0: im]
            lat = self.lat[i0: im]
            lon = self.lon[i0: im]
            hdg = self.hdg[i0: im]
            alt = self.alt[i0: im]
            gs = self.gs[i0: im]

            # Check for last data point
            if im <= self.i_max:
                self.i_next = im
                self.t_next = self.simt[im]
            else:
                running = False
        else:
            cmds = []
            ids = []
            lat = np.array([])
            lon = np.array([])
            hdg = np.array([])
            alt = np.array([])
            gs = np.array([])

        return running, cmds, ids, lat, lon, hdg, alt, gs


"""
Run
"""


if __name__ == '__main__':
    path = os.path.expanduser("~") + r"\PycharmProjects\bluesky\scenario\vemmis212207"
    v = VEMMISRead(path, deltat=0.5)
