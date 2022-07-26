"""
This python file is used to create traffic variables used by the LVNL

Created by: Bob van Dillen
Date: 24-12-2021
"""


import numpy as np
from numpy import ndarray

import bluesky as bs
from bluesky.core import Entity, timed_function
from bluesky.tools import misc, geo, aero
from bluesky import stack
from bluesky.traffic import trackmiles_calc, activewpdata
from bluesky.tools.misc import degto180

"""
Classes
"""


class LVNLVariables(Entity):
    """
    Definition: Class containing variables used by LVNL
    Methods:
        create():           Create an aircraft
        update():           Update LVNL variables
        selucocmd():        Set UCO for aircraft
        selrelcmd():        Set REL for aircraft
        setarr():           Set the arrival/stack
        setautolabel():     Set automatic label selection
        setflighttype():    Set the flight type
        setils():           Set the ILS route
        setmlabel():        Set the micro label
        setrwy():           Set the runway
        setsid():           Set the SID
        setssr():           Set the SSR code
        setssrlabel():      Set the SSR label
        settracklabel():    Set the track label
        setwtc():           Set the wtc

    Created by: Bob van Dillen
    Date: 24-12-2021
    """
    dtg_tbar: ndarray

    def __init__(self):
        super().__init__()

        self.swautolabel = False  # Auto label change

        #for calculating trackmiles along a route
        self.tmc2 = trackmiles_calc.TrackmilesCalculation()

        with self.settrafarrays():
            self.arr        = []                           # Arrival/Stack
            self.autolabel  = np.array([], dtype=np.bool)  # Auto label change
            self.dtg_tbar   = np.array([])                 # Distance to T-Bar point
            self.flighttype = []                           # Flight type
            self.mlbl       = np.array([], dtype=np.bool)  # Show micro label
            self.rel        = np.array([], dtype=np.bool)  # Release
            self.rwy        = []                           # Runway
            self.sid        = []                           # SID
            self.ssr        = np.array([], dtype=np.int)   # SSR code
            self.ssrlbl     = []                           # Show SSR label
            self.tracklbl   = np.array([], dtype=np.bool)  # Show track label
            self.uco        = np.array([], dtype=np.bool)  # Under Control
            self.wtc        = []                           # Wake Turbulence Category
            self.trackmiles = np.array([])                 # Distance to go along route
            self.man_intervention = np.array([], dtype=np.bool) # Manual intervention for VNR

    def create(self, n=1):
        """
        Function: Create an aircraft
        Args:
            n:  number of aircraft
        Returns: -

        Created by: Bob van Dillen
        Date: 12-1-2022
        """

        super().create(n)

        self.autolabel[-n:] = True
        self.tracklbl[-n:]  = True
        self.mlbl[-n:]      = False

    def get_trackmiles(self, idx):
        own_lat = bs.traf.lat[idx]
        own_lon = bs.traf.lon[idx]
        own_tas = bs.traf.tas[idx]
        own_hdg = bs.traf.hdg[idx]
        wpt_lat = bs.traf.actwp.lat[idx]
        wpt_lon = bs.traf.actwp.lon[idx]
        route = bs.traf.ap.route
        tm_remaining_curve = 0.0
        tm_remaining_straight = 0.0

        dist_to_next_curve = trackmiles_calc.get_dist_to_next_wpt_curve(bs.traf, idx)
        dist_to_next_straight = trackmiles_calc.get_dist_to_next_wpt_straight(bs.traf, idx)
        if len(route[idx].wpname) > 1:
            for i in range(0, len(route[idx].wpname) - 1):
                # Determine the next waypoint so we can loop around the remaining waypoints for data
                if route[idx].wpname[i] == route[idx].wpname[route[idx].iactwp]:
                    j = i
                    tm_remaining_straight = trackmiles_calc.get_remaining_route_dist_straight(route[idx], j)
                    tm_remaining_curve = trackmiles_calc.get_remaining_route_dist_curve(route[idx], j)

        dist_to_next_curve = trackmiles_calc.get_dist_to_next_wpt_curve(bs.traf, idx)

        #building blocks for total distance to go
        hdg = np.radians(own_hdg)
        brg = np.radians(geo.kwikqdrdist(own_lat, own_lon, wpt_lat, wpt_lon)[0])
        lnav = bs.traf.swlnav[idx]

        #dist_straight = np.sqrt((np.square(dtg)) - 2.*r*dtg*np.cos(1.57-delta_hdg)) #D dubbel accent
        #gamma_acc = np.arctan(r/dist_straight)

        # When on the route between wpts, calculate trackmiles the classic way

        if np.abs(degto180(np.degrees(hdg)%360. - np.degrees(brg)%360.)) < 1.0 or not lnav or self.man_intervention[idx]:
            distance_to_go = dist_to_next_curve + tm_remaining_curve
            #distance_to_go = dist_to_next_straight + tm_remaining_straight

            bs.traf.dist_ref[idx] = bs.traf.distflown[idx] / 1852
            bs.traf.dtg_ref[idx] = distance_to_go

            if not lnav:
                self.man_intervention[idx] = True

            if np.abs(degto180(np.degrees(hdg)%360. - np.degrees(brg)%360.)) < 1.0:
                self.man_intervention[idx] = False

        # When in a flyby turn, estimate dtg by using the subtracting the flown distance from
        # a reference dtg, until the a/c is on the straight line to the new wpt
        else:
            distance_to_go = bs.traf.dtg_ref[idx] + bs.traf.dist_ref[idx] - bs.traf.distflown[idx]/1852

        return distance_to_go

    @timed_function(name='lvnlvars', dt=0.1)
    def update(self):
        """
        Function: Update LVNL variables
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 1-2-2022
        """

        # --------------- Automatic label selection ---------------

        if self.swautolabel:

            if bs.scr.atcmode == 'APP':
                # Indices
                itracklbl = np.nonzero(bs.traf.alt <= 7467.6)[0]
                issrlbl = np.setdiff1d(np.arange(len(bs.traf.id)), itracklbl)
                iautolabel = np.nonzero(self.autolabel)[0]
                itracklbl = np.intersect1d(itracklbl, iautolabel)
                issrlbl = np.intersect1d(issrlbl, iautolabel)

                # Set labels
                self.tracklbl[itracklbl] = True
                self.tracklbl[issrlbl] = False

                ssrlbl = np.array(self.ssrlbl)
                ssrlbl[itracklbl] = ''
                ssrlbl[issrlbl] = 'C'
                self.ssrlbl = ssrlbl.tolist()

            elif bs.scr.atcmode == 'ACC':
                # Indices
                itracklbl = np.nonzero(np.logical_and(bs.traf.alt <= 7467.6, bs.traf.alt >= 2438.4))[0]
                issrlbl = np.setdiff1d(np.arange(len(bs.traf.id)), itracklbl)
                iautolabel = np.nonzero(self.autolabel)[0]
                itracklbl = np.intersect1d(itracklbl, iautolabel)
                issrlbl = np.intersect1d(issrlbl, iautolabel)

                # Set labels
                self.tracklbl[itracklbl] = True
                self.tracklbl[issrlbl] = False

                ssrlbl = np.array(self.ssrlbl)
                ssrlbl[itracklbl] = ''
                ssrlbl[issrlbl] = 'C'
                self.ssrlbl = ssrlbl.tolist()

        # --------------- T-Bar DTG ---------------

        inirsi = misc.get_indices(self.arr, "NIRSI_RIVER")
        #print (inirsi)
        inirsi_gal1 = misc.get_indices(self.arr, "NIRSI_GAL01")
        #print(inirsi_gal1)
        inirsi_gal2 = misc.get_indices(self.arr, "NIRSI_GAL02")
        inirsi_603 = misc.get_indices(self.arr, "NIRSI_AM603")

        self.dtg_tbar[inirsi] = geo.kwikdist_matrix(bs.traf.lat[inirsi], bs.traf.lon[inirsi],
                                                         np.ones(len(inirsi)) * 52.58387777777778,
                                                         np.ones(len(inirsi)) * 4.513372222222222)

        #print("idx", type(inirsi_603))
        #print(type(bs.traf.lat))
        #print(type(bs.traf.id))

        self.dtg_tbar[inirsi_gal1] = geo.kwikdist_matrix(bs.traf.lat[inirsi_gal1], bs.traf.lon[inirsi_gal1],
                                                         np.ones(len(inirsi_gal1))*52.47962777777778,
                                                         np.ones(len(inirsi_gal1))*4.513372222222222)
        #self.dtg_tbar[inirsi_gal1] = geo.kwikdist_matrix(bs.traf.lat[inirsi_gal1], bs.traf.lon[inirsi_gal1],
        #                                                 np.ones(len(inirsi_gal1)) * 52.58387777777778,
        #                                                 np.ones(len(inirsi_gal1)) * 4.513372222222222)

        #self.dtg_tbar[inirsi_gal2] = geo.kwikdist_matrix(bs.traf.lat[inirsi_gal2], bs.traf.lon[inirsi_gal2],
        #                                                 np.ones(len(inirsi_gal2))*52.58375277777778,
        #                                                 np.ones(len(inirsi_gal2))*4.342225)

        self.dtg_tbar[inirsi_gal2] = geo.kwikdist_matrix(bs.traf.lat[inirsi_gal2], bs.traf.lon[inirsi_gal2],
                                                         np.ones(len(inirsi_gal2)) * 52.58387777777778,
                                                         np.ones(len(inirsi_gal2)) * 4.513372222222222)

        #self.dtg_tbar[inirsi_603] = geo.kwikdist_matrix(bs.traf.lat[inirsi_603], bs.traf.lon[inirsi_603],
        #                                                np.ones(len(inirsi_603))*52.68805555555555,
        #                                                np.ones(len(inirsi_603))*4.513333333333334)

        self.dtg_tbar[inirsi_603] = geo.kwikdist_matrix(bs.traf.lat[inirsi_603], bs.traf.lon[inirsi_603],
                                                         np.ones(len(inirsi_603)) * 52.58387777777778,
                                                         np.ones(len(inirsi_603)) * 4.513372222222222)

        # print(self.dtg_tbar[inirsi_gal2])
        # print(inirsi_gal2)
        # print(inirsi_gal1)
        # print(inirsi_603)
        # print(self.dtg_tbar[inirsi_gal1])
        # print(self.dtg_tbar[inirsi_603])

        self.trackmiles = np.ones(len(self.arr))
        bla = bs.traf.ap.route
        for i in range(0, len(self.trackmiles)):
           self.trackmiles[i] = self.get_trackmiles(i)
        #print ("bla: ", bla[1].wpname)

        return

    @stack.command(name='UCO')
    def selucocmd(self, idx: 'acid'):
        """
        Function: Set UCO for aircraft
        Args:
            idx:    index for traffic arrays
        Returns: -
        """

        # Autopilot modes (check if there is a route)
        if bs.traf.ap.route[idx].nwp > 0:
            # Enable autopilot modes
            bs.traf.swlnav[idx] = True
            bs.traf.swvnav[idx] = True
            bs.traf.swvnavspd[idx] = True
        else:
            # Set current heading/altitude/speed
            bs.traf.selhdg[idx] = bs.traf.hdg[idx]
            bs.traf.selalt[idx] = bs.traf.alt[idx]
            bs.traf.selspd[idx] = bs.traf.cas[idx]
            # Disable autopilot modes
            bs.traf.swlnav[idx] = False
            bs.traf.swvnav[idx] = False
            bs.traf.swvnavspd[idx] = False

        # Labels
        self.tracklbl[idx] = True
        self.ssrlbl[idx] = ''

        # Set UCO/REL
        bs.traf.trafdatafeed.uco(idx)
        self.uco[idx] = True
        self.rel[idx] = False

    @stack.command(name='REL',)
    def setrelcmd(self, idx: 'acid'):
        """
        Function: Set REL for aircraft
        Args:
            idx:    index for traffic arrays
        Returns: -

        Created by: Bob van Dillen
        """

        # Autopilot modes
        bs.traf.swlnav[idx] = True
        bs.traf.swvnav[idx] = True
        bs.traf.swvnavspd[idx] = True

        # Labels
        self.tracklbl[idx] = False
        self.ssrlbl[idx] = 'C'

        # Set UCO/REL
        self.uco[idx] = False
        self.rel[idx] = True

    @stack.command(name='ARR', brief='ARR CALLSIGN ARRIVAL/STACK (ADDWPTS [ON/OFF])', aliases=('STACK',))
    def setarr(self, idx: 'acid', arr: str = '', addwpts: 'onoff' = True):
        """
        Function: Set the arrival/stack
        Args:
            idx:        index for traffic arrays [int]
            arr:        arrival/stack [str]
            addwpts:    add waypoints [bool]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        """

        self.arr[idx] = arr.upper()

        if addwpts:
            acid = bs.traf.id[idx]
            cmd = 'PCALL LVNL/Routes/ARR/'+arr.upper()+' '+acid
            stack.stack(cmd)

    @stack.command(name='AUTOLABEL', brief='AUTOLABEL (ON/OFF or ACID or ACID ON/OFF)')
    def setautolabel(self, *args):
        """
        Function: Set automatic label selection
        Args:
            *args:  arguments [tuple]
        Returns: -

        Created by: Bob van Dillen
        Date: 27-2-2022
        """

        # No arguments
        if len(args) == 0:
            self.swautolabel = not self.swautolabel

        # ON/OFF
        if args[0].upper() == 'ON':
            self.swautolabel = True
        elif args[0].upper() == 'OFF':
            self.swautolabel = False

        # ACID
        elif bs.traf.id2idx(args[0]) > 0:
            idx = bs.traf.id2idx(args[0])

            # Other arguments
            if len(args) > 1:

                # ON/OFF
                if args[1].upper() == 'ON':
                    self.autolabel[idx] = True
                elif args[1].upper() == 'OFF':
                    self.autolabel[idx] = False
                else:
                    return False, 'AUTOLABEL: Not a valid input'

            else:
                self.autolabel[idx] = not self.autolabel[idx]

        else:
            return False, 'AUTOLABEL: Not a valid input'

    @stack.command(name='FLIGHTTYPE', brief='FLIGHTTYPE CALLSIGN TYPE')
    def setflighttype(self, idx: 'acid', flighttype: str):
        """
        Function: Set the flight type
        Args:
            idx:        index for traffic arrays [int]
            flighttype: flight type [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        """

        if isinstance(flighttype, str):
            self.flighttype[idx] = flighttype.upper()

    @stack.command(name='ILS', brief='ILS CALLSIGN RWY', aliases=('STACK',))
    def setils(self, idx: 'acid', rwy: str):
        """
        Function: Set the ILS route
        Args:
            idx:        index for traffic arrays [int]
            rwy:        runway [str]
        Returns: -

        Created by: Mitchell de Keijzer
        Date: 16-02-2022
        """

        acid = bs.traf.id[idx]
        cmd = 'PCALL LVNL/Routes/ARR/ILS_' + rwy + ' ' + acid
        stack.stack(cmd)

    @stack.command(name='MICROLABEL', brief='MICROLABEL CALLSIGN')
    def setmlabel(self, idx: 'acid'):
        """
        Function: Set the micro label
        Args:
            idx:    index for traffic arrays [int]
        Returns: -

        Created by: Bob van Dillen
        Date: 24-1-2022
        """

        self.mlbl[idx] = not self.mlbl[idx]

    @stack.command(name='RWY', brief='RWY CALLSIGN RUNWAY', aliases=('RW',))
    def setrwy(self, idx: 'acid', rwy: str):
        """
        Function: Set the runway
        Args:
            idx:    index for traffic arrays [int]
            rwy:    runway [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        """

        if isinstance(rwy, str):
            self.rwy[idx] = rwy.upper()

    @stack.command(name='SID', brief='SID CALLSIGN SID')
    def setsid(self, idx: 'acid', sid: str = '', addwpts: 'onoff' = True):
        """
        Function: Set the SID
        Args:
            idx:    index for traffic arrays [int]
            sid:    SID [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        Edited by: Mitchell de Keijzer
        Date: 25-02-2022
        Changes: small bug fix, added scenario files to scenario/lvnl/routes/sid
        """

        self.sid[idx] = sid.upper()

        if addwpts:
            acid = bs.traf.id[idx]
            cmd = 'PCALL LVNL/Routes/SID/'+sid.upper()+' '+acid
            stack.stack(cmd)

    @stack.command(name='SSRCODE', brief='SSRCODE CALLSIGN SSR')
    def setssr(self, idx: 'acid', ssr: float):
        """
        Function: Set the SSR code
        Args:
            idx:    index for traffic arrays [int]
            ssr:    SSR code [int]
        Returns: -

        Created by: Bob van Dillen
        Date: 25-1-2022
        """

        self.ssr[idx] = int(ssr)

    @stack.command(name='SSRLABEL', brief='SSRLABEL CALLSIGN')
    def setssrlabel(self, idx: 'acid', *args):
        """
        Function: Set the SSR label
        Args:
            idx:        index for traffic arrays [int]
            *args:      arguments [tuple]
        Returns: -

        Created by: Bob van Dillen
        Date: 24-1-2022
        """

        # No arguments passed
        if len(args) == 0:
            if self.ssrlbl[idx]:
                self.ssrlbl[idx] = ''
            else:
                self.ssrlbl[idx] = 'C'
            self.autolabel[idx] = False

        # Switch on/off
        elif args[0].upper() == 'ON' or args[0].upper() == 'TRUE':
            self.ssrlbl[idx] = 'C'
            self.autolabel[idx] = False
        elif args[0].upper() == 'OFF' or args[0].upper() == 'FALSE':
            self.ssrlbl[idx] = ''
            self.autolabel[idx] = False

        # Switch modes on/off
        else:
            for ssrmode in args:
                ssrmode = ssrmode.upper()

                # Check if it is a valid mode
                if ssrmode in ['A', 'C', 'ACID']:
                    # Get active modes
                    if self.ssrlbl[idx]:
                        actmodes = self.ssrlbl[idx].split(';')
                    else:
                        actmodes = []

                    # Remove/Append
                    if ssrmode in actmodes:
                        actmodes.remove(ssrmode)
                    else:
                        actmodes.append(ssrmode)

                    # Reconstruct ssrlbl
                    ssrlbl = ''
                    for mode in actmodes:
                        ssrlbl += mode+';'
                    ssrlbl = ssrlbl[:-1]  # Leave out last ';'

                    self.ssrlbl[idx] = ssrlbl
                    self.autolabel[idx] = False

            else:
                return False, 'SSRLABEL: Not a valid SSR label item'

    @stack.command(name='TRACKLABEL', brief='TRACKLABEL CALLSIGN')
    def settracklabel(self, idx: 'acid', *args):
        """
        Function: Set the track label
        Args:
            idx:        index for traffic arrays [int]
            *args:      arguments [tuple]
        Returns: -

        Created by: Bob van Dillen
        Date: 24-1-2022
        """

        # No arguments passed
        if len(args) == 0:
            self.tracklbl[idx] = not self.tracklbl[idx]
            self.autolabel[idx] = False

        # Switch on/off
        elif args[0].upper() == 'ON' or args[0].upper() == 'TRUE':
            self.tracklbl[idx] = True
            self.autolabel[idx] = False
        elif args[0].upper() == 'OFF' or args[0].upper() == 'FALSE':
            self.tracklbl[idx] = False
            self.autolabel[idx] = False

        else:
            return False, 'TRACKLABEL: Not a valid argument'

    @stack.command(name='WTC', brief='WTC CALLSIGN WTC')
    def setwtc(self, idx: 'acid', wtc: str = ''):
        """
        Function: Set the wtc
        Args:
            idx:    index for traffic arrays [int]
            wtc:    wtc [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        """

        if isinstance(wtc, str):
            self.wtc[idx] = wtc.upper()
