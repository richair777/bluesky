""" Show the trackmiles to go of all a/c in a bar """

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

    tm_tg = trackmiles_bar()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'TRACKMILESBAR',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'gui',
        }

    # init_plugin() should always return a configuration dict.
    return config


'''
Classes
'''


class trackmiles_bar(core.Entity):
    """
    Definition: Class used to initialize and update the DTG rangebar
    Methods:
        show_rangebar():    Initialize ac symbols on rangebar + label (acid)
        update_rangebar():  Update the position of the ac symbols + label
    """
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.trackmiles_bar = None

        bs.net.actnodedata_changed.connect(self.update_trackmilesbar)

    @stack.command(name='TRACKMILESBAR')
    def show_trackmilesbar(self):
        """

        """

        if not self.initialized:
            # Get current node data
            actdata = bs.net.get_nodedata()

            # Class to access Traffic graphics
            self.trackmiles_bar = Traffic()

            # Initialize plugin t-bar aircraft and label
            self.trackmiles_bar.plugin_rangebar(blocksize=(8, 1), position=(0.5, 3))

            # Update label with current data
            rawlabel = ''
            for idx in range(len(actdata.acdata.id)):
                rawlabel += 8*' '

            self.trackmiles_bar.tbar_lbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))

            # Initialization completed
            self.initialized = True
        else:
            self.trackmiles_bar.show_tbar_ac = not self.trackmiles_bar.show_tbar_ac

    def update_trackmilesbar(self, nodeid, nodedata, changed_elems):
        """

        """
        if self.initialized:
            if 'ACDATA' in changed_elems:
                # Update label & coordinates
                rawlabel = ''
                lon = []
                lat = []

                for idx in range(len(nodedata.acdata.id)):
                    acid = nodedata.acdata.id[idx]
                    dtg = nodedata.acdata.trackmiles[idx]
                    lat_ac = nodedata.acdata.lat[idx]
                    lon_ac = nodedata.acdata.lon[idx]
                    alt_ac = nodedata.acdata.selalt[idx]
                    if dtg > 100:
                        latd = None
                        lond = None
                        rawlabel += 8*' '
                    elif 52.4796277778 < lat_ac < 52.688125 and 4.34225 < lon_ac < 4.7281416667:
                        latd = None
                        lond = None
                        rawlabel += 8 * ' '
                    elif alt_ac < 500:
                        latd = None
                        lond = None
                        rawlabel += 8 * ' '
                    else:
                        latd, lond = geo.kwikpos(51.57070200000000, 2.25580600000000, 90, dtg)
                        rawlabel += '%-8s' % acid[:8]
                        #rawlabel += '%-3' % dtg
                    lon.append(lond)
                    lat.append(latd)

                self.trackmiles_bar.tbar_lbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))
                self.trackmiles_bar.tbar_lon.update(np.array(lon, dtype=np.float32))
                self.trackmiles_bar.tbar_lat.update(np.array(lat, dtype=np.float32))
