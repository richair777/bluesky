""" Trackmiles test """
from random import randint
import numpy as np
import bluesky as bs
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import core, stack, traf  #, settings, navdb, sim, scr, tools
from bluesky.tools import geo
from bluesky.ui.qtgl.gltraffic import Traffic, leading_zeros

### Initialization function of your plugin. Do not change the name of this
### function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():
    ''' Plugin initialisation function. '''
    # Instantiate our example entity
    track_miles = Trackmiles()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'TRACKMILES',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'gui',
        }

    # init_plugin() should always return a configuration dict.
    return config


### Entities in BlueSky are objects that are created only once (called singleton)
### which implement some traffic or other simulation functionality.
### To define an entity that ADDS functionality to BlueSky, create a class that
### inherits from bluesky.core.Entity.
### To replace existing functionality in BlueSky, inherit from the class that
### provides the original implementation (see for example the asas/eby plugin).
class Trackmiles(core.Entity):
    ''' Example new entity object for BlueSky. '''
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.trackmileslbl = None
        self.bla = 987
        self.distance_to_go = []

        # Set update function
        bs.net.actnodedata_changed.connect(self.update_trackmiles)

    def create(self, n=1):
        ''' This function gets called automatically when new aircraft are created. '''
        # Don't forget to call the base class create when you reimplement this function!
        super().create(n)

    # Functions that need to be called periodically can be indicated to BlueSky
    # with the timed_function decorator
    @core.timed_function(name='trackmiles', dt=5)
    def update(self):
        ''' Periodic update function for our example entity. '''
        #stack.stack('ECHO Example update: creating a random aircraft')
        #stack.stack('MCRE 1')

        stack.stack('ECHO Next waypoint is: ')
        stack.stack('nextw klm123')

        self.own_lat = traf.lat
        self.own_lon = traf.lon
        self.wpt_lat = traf.actwp.lat
        self.wpt_lon = traf.actwp.lon
        self.ble = traf.actwp.lon
        self.iets = traf.actwp.curleglen
        route = traf.ap.route
        print(route[0].wpname)

        tm_total = 0.0
        for i in range(0, len(route[0].wpname) - 1):
            if route[0].wpname[i] == route[0].wpname[route[0].iactwp]:
                j = i

        for i in range(j, len(route[0].wpname) - 1):
            # print (i, route[0].wpname[i])
            section_distance = geo.kwikdist(route[0].wplat[i], route[0].wplon[i], route[0].wplat[i + 1],
                                            route[0].wplon[i + 1])
            tm_total = tm_total + section_distance


        self.distance_to_go = tm_total + geo.kwikdist(self.own_lat, self.own_lon, self.wpt_lat, self.wpt_lon)
        print(self.distance_to_go)
        print("Route: ", route[0].wpname)
        print("Next waypoint: ", route[0].wpname[route[0].iactwp])
        #print("Distance to go: %.1f NM" %self.distance_to_go)


        if route[0].wpname[route[0].iactwp] == "NIRSI":
            print("Volgende waypoint is NIRSI")

    # You can create new stack commands with the stack.command decorator.
    # By default, the stack command name is set to the function name.
    # The default argument type is a case-sensitive word. You can indicate different
    # types using argument annotations. This is done in the below function:
    # - The acid argument is a BlueSky-specific argument with type 'acid'.
    #       This converts callsign to the corresponding index in the traffic arrays.
    # - The count argument is a regular int.
    @stack.command(name='SHOWTRACKMILES',)
    def showtrackmiles(self):
        # Check if we need to initialize
        if not self.initialized:
            # Get current node data
            actdata = bs.net.get_nodedata()

            # Class to access Traffic graphics
            self.trackmileslbl = Traffic()

            # Initialize plugin label
            self.trackmileslbl.plugin_init(blocksize=(3, 1), position=(1, 7))

            # Update label with current data
            rawlabel = ''
            for idx in range(len(actdata.acdata.id)):
                rawlabel += 3*' '

            self.trackmileslbl.pluginlbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))

            # Initialization completed
            self.initialized = True
        else:
            self.trackmileslbl.show_pluginlabel = not self.trackmileslbl.show_pluginlabel

    def update_trackmiles(self, nodeid, nodedata, changed_elems):
        """
        Function: Update T-Bar graphics
        Args:
            nodeid:         Node identifier []
            nodedata:       Node data [class]
            changed_elems:  Changed elements [list]
        Returns: -

        Created by: Bob van Dillen
        Date: 25-2-2022
        """

        if self.initialized:
            if 'ACDATA' in changed_elems:
                # Update TM label
                rawlabel = ''
                #self.update()
                for idx in range(len(nodedata.acdata.id)):
                    acid = nodedata.acdata.id[idx]
                    if self.distance_to_go:
                        dtg = self.distance_to_go[0]
                    else:
                        dtg = self.bla

                    tracklbl = nodedata.acdata.tracklbl[idx]

                    #if tracklbl and dtg != 0. and acid == console.Console._instance.id_select:
                    if tracklbl and dtg != 0.:
                        rawlabel += '%-3s' % leading_zeros(dtg)[:3]
                    else:
                        rawlabel += 3*' '
                self.trackmileslbl.pluginlbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))

    @stack.command
    def nextw(self, acid: 'acid'):
        bla = traf
        bli = self.distance_to_go
        #print (self.own_lat, self.wpt_lat, self.iets)
        return True, f'The result for {traf.id[acid]} is set to {bli} NM.'
