""" Show the DTG of all a/c in a horizontal bar """

import numpy as np
import bluesky as bs
from bluesky import settings, stack, core
from bluesky.tools import geo, misc
from bluesky.ui import palette
from bluesky.ui.qtgl import glhelpers as glh
from bluesky.ui.qtgl import console
from bluesky.ui.qtgl.gltraffic import Traffic, leading_zeros


### Initialization function of the plugin
def init_plugin():
    ''' Plugin initialisation function. '''

    dtg = tbar_ac()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'RANGEBAR',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'gui',
        }

    # init_plugin() should always return a configuration dict.
    return config


'''
Classes
'''


class tbar_ac(core.Entity):
    """
    Definition: Class used to initialize and update the DTG rangebar
    Methods:
        show_rangebar():    Initialize ac symbols on rangebar + label (acid)
        update_rangebar():  Update the position of the ac symbols + label
    """
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.tbar_ac = None

        bs.net.actnodedata_changed.connect(self.update_rangebar)

    @stack.command(name='RANGEBAR')
    def show_rangebar(self):
        """
        Function: Initialize ac symbols on rangebar + label (acid)
        Args: -
        Returns: -

        Created by: Mitchell de Keijzer
        Date: 17-03-2022
        """

        if not self.initialized:
            # Get current node data
            actdata = bs.net.get_nodedata()

            # Class to access Traffic graphics
            self.tbar_ac = Traffic()

            # Initialize plugin t-bar aircraft and label
            self.tbar_ac.plugin_rangebar(blocksize=(8, 1), position=(0.5, 3))

            # Update label with current data
            rawlabel = ''
            for idx in range(len(actdata.acdata.id)):
                rawlabel += 8*' '

            self.tbar_ac.tbar_lbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))

            # Initialization completed
            self.initialized = True
        else:
            self.tbar_ac.show_tbar_ac = not self.tbar_ac.show_tbar_ac

    def update_rangebar(self, nodeid, nodedata, changed_elems):
        """
        Function: Update the position of the ac symbols + label
        Args:
            nodeid:         Node identifier []
            nodedata:       Node data [class]
            changed_elems:  Changed elements [list]
        Returns: -

        Created by: Mitchell de Keijzer
        Date: 17-03-2022
        """
        if self.initialized:
            if 'ACDATA' in changed_elems:
                # Update label & coordinates
                rawlabel = ''
                lon = []
                lat = []

                for idx in range(len(nodedata.acdata.id)):
                    acid = nodedata.acdata.id[idx]
                    dtg = nodedata.acdata.dtg[idx]
                    lat_ac = nodedata.acdata.lat[idx]
                    lon_ac = nodedata.acdata.lon[idx]
                    alt_ac = nodedata.acdata.selalt[idx]
                    if dtg > 60:
                        latd = None
                        lond = None
                        rawlabel += 8*' '
                    elif 52.4796277778 < lat_ac < 52.688125 and 4.34225 < lon_ac < 4.7281416667:
                        latd = None
                        lond = None
                        rawlabel += 8 * ' '
                    elif alt_ac < 1700:
                        latd = None
                        lond = None
                        rawlabel += 8 * ' '
                    else:
                        latd, lond = geo.kwikpos(51.57070200000000, 2.25580600000000, 90, dtg)
                        rawlabel += '%-8s' % acid[:8]
                        #rawlabel += '%-3' % dtg
                    lon.append(lond)
                    lat.append(latd)

                self.tbar_ac.tbar_lbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))
                self.tbar_ac.tbar_lon.update(np.array(lon, dtype=np.float32))
                self.tbar_ac.tbar_lat.update(np.array(lat, dtype=np.float32))
