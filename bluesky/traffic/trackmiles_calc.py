import bluesky as bs
import numpy as np
from bluesky.tools import geo, aero
from bluesky.tools.aero import nm, g0
from bluesky.tools.misc import degto180

class TrackmilesCalculation:
    def __init__(self):
        self.dist_flown_ref = -999.0
        self.prev_turn_dist = -999.0
        self.prev_turn_rad = -999.0

    def set_new_distflown_ref(self, curr_dist_flown, turn_dist, turn_rad):
        self.dist_flown_ref = curr_dist_flown/1852
        self.prev_turn_dist = turn_dist/1852
        self.prev_turn_rad = turn_rad / 1852
        #print ("new ref: ", self.dist_flown_ref)
        return

    def update(self):
        bla =1
        #print("update dist ref: ", self.dist_flown_ref)
        #print("update prev turn dist: ", self.prev_turn_dist)

    def get_distflown_ref(self):
        return self.dist_flown_ref

    def get_prev_turn_dist(self):
        return self.prev_turn_dist

    def get_prev_turn_rad(self):
        return self.prev_turn_rad


def get_hdg_changes(section_dir):
    hdg_change = []
    for i in range(1, len(section_dir)):
        hdg_change.append(section_dir[i] - section_dir[i-1])
    return hdg_change

def get_adhoc_dist_flown(gs):
    #print ("gs, dt: ", gs, bs.sim.simdt)
    dist_flown = gs * bs.sim.simdt
    return dist_flown

def get_remaining_route_dist_straight(route, j):
    tm_remaining = 0.
    for i in range(j, len(route.wpname) - 1):
        # Pure section distances point to point
        section_distance = geo.kwikdist(route.wplat[i], route.wplon[i],
                                        route.wplat[i + 1], route.wplon[i + 1])

        tm_remaining += section_distance

    print("tm_remaining: ", tm_remaining)
    return tm_remaining

def get_remaining_route_dist_curve(route, j):
    tm_remaining = 0.
    # calculate the straight sections first
    for i in range(j, len(route.wpname) - 1):
        section_distance = geo.kwikdist(route.wplat[i], route.wplon[i],
                                        route.wplat[i + 1], route.wplon[i + 1])

        tm_remaining += section_distance

    # Now we are going to subtract the distance before and after wpt to turn
    #
    for i in range(j+1, len(route.wpname) - 1):
        dir_in = geo.kwikqdrdist(route.wplat[i - 1], route.wplon[i - 1], route.wplat[i],
                        route.wplon[i])[0]
        dir_out = geo.kwikqdrdist(route.wplat[i], route.wplon[i], route.wplat[i+1],
                                      route.wplon[i+1])[0]

        wpt_tas = aero.cas2tas(route.wpspd[i], route.wpalt[i])
        turn_dist = calcturn(wpt_tas, 0.436, dir_in, dir_out, -999.)[0] / 1852

        turn_rad = calcturn(wpt_tas, 0.436, dir_in, dir_out, -999.)[1]
        arc_dist = turn_rad * np.radians(np.abs(dir_out - dir_in)) / 1852
        # we now have the ingredients to account for the flyby waypoints
        tm_remaining = tm_remaining + arc_dist - 2 * turn_dist


    print("tm rem curve: ", tm_remaining)
    return tm_remaining

def get_wpt_dirs_inout(route):
    dir_in = []
    dir_out = []
    for i in range(1, len(route.wpname) - 1):
        dir_in.append(geo.kwikqdrdist(route.wplat[i-1], route.wplon[i-1], route.wplat[i],
                                      route.wplon[i])[0])
        dir_out.append(geo.kwikqdrdist(route.wplat[i], route.wplon[i], route.wplat[i+1],
                                      route.wplon[i+1])[0])

    #print("dirs: ", dir_in, dir_out)

# Calculate turn distance and radius (stolen from activewpdata)
def calcturn(tas,bank,wpqdr,next_wpqdr,turnradnm=-999.):
    """Calculate distance to wp where to start turn and turn radius in meters"""

    # Calculate turn radius using current speed or use specified turnradius
    turnrad = np.where(turnradnm+0.*tas<0.,
                       tas * tas / (np.maximum(0.01, np.tan(bank)) * g0),
                       turnradnm*nm)

    # turndist is in meters
    turndist = np.abs(turnrad * np.tan(np.radians(0.5 * np.abs(degto180(wpqdr%360. - next_wpqdr%360.)))))

    return turndist,turnrad



