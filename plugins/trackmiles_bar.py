""" Show the trackmiles to go of all a/c in a bar """

import numpy as np
import bluesky as bs
from bluesky import settings, stack, core
from bluesky.tools import geo, misc
from bluesky.ui import palette
from bluesky.ui.qtgl import glhelpers as glh
from bluesky.ui.qtgl import console
from bluesky.ui.qtgl.gltraffic import Traffic, leading_zeros
from bluesky.tools.aero import nm, kts


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
            self.trackmiles_bar.plugin_rangebar(blocksize=(8, 3), position=(1.2, 3))

            # Update label with current data
            rawlabel = ''
            for idx in range(len(actdata.acdata.id)):
                rawlabel += 8*' '

            self.trackmiles_bar.tbar_lbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))

            # Initialization completed
            self.initialized = True
        else:
            self.trackmiles_bar.show_tbar_ac = not self.trackmiles_bar.show_tbar_ac

    def get_intrailsep_from_next_in_seq(self, dtg, dtg_list):
        intrailsep = -1
        for i in range(len(dtg_list)):
            dist = dtg - dtg_list[i]
            if dist <= 0:
                break
            else:
                intrailsep = dist

        return intrailsep

    def update_trackmilesbar(self, nodeid, nodedata, changed_elems):
        """

        """
        if self.initialized:
            if 'ACDATA' in changed_elems:
                # Update label & coordinates
                rawlabel = ''
                lon = []
                lat = []

                # Sort the trackmiles for the sequence and in trail separations
                sorted_tm = np.sort(nodedata.acdata.trackmiles)
                # print('tm sort: ', sorted_tm)
                # intrail_sep = np.ones(len(nodedata.acdata.trackmiles)-1)
                # print(intrail_sep)
                # for i in range(0,len(nodedata.acdata.id)-1):
                #     intrail_sep[i] = sorted_tm[i+1] - sorted_tm[i]

                for idx in range(len(nodedata.acdata.id)):
                    acid = nodedata.acdata.id[idx]
                    gs = nodedata.acdata.gs[idx]
                    dtg = nodedata.acdata.trackmiles[idx]
                    lat_ac = nodedata.acdata.lat[idx]
                    lon_ac = nodedata.acdata.lon[idx]
                    alt_ac = nodedata.acdata.selalt[idx]
                    if dtg > 100:
                        latd = None
                        lond = None
                        rawlabel += 8*' '
                    elif alt_ac < 500:
                        latd = None
                        lond = None
                        rawlabel += 8 * ' '
                    else:
                        latd, lond = geo.kwikpos(51.57070200000000, 2.25580600000000, 90, dtg)
                        rawlabel += '%-8s' % acid[:8]
                        if nodedata.acdata.trackmiles[idx] == min(nodedata.acdata.trackmiles):
                            rawlabel += 8*' '
                        else:
                            intrailsep = self.get_intrailsep_from_next_in_seq(nodedata.acdata.trackmiles[idx],
                                                                         sorted_tm)

                            rawlabel += '%-8.1f' % intrailsep
                        gs_kts = gs/kts
                        rawlabel += '%-8.0f' % gs_kts

                    lon.append(lond)
                    lat.append(latd)

                self.trackmiles_bar.tbar_lbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))
                self.trackmiles_bar.tbar_lon.update(np.array(lon, dtype=np.float32))
                self.trackmiles_bar.tbar_lat.update(np.array(lat, dtype=np.float32))
