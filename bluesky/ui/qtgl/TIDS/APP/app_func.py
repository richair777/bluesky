from bluesky.ui.qtgl import console

'''
APPROACH
'''

def getid():
    if len(console.Console._instance.command_line) == 0:
        console.process_cmdline(console.Console._instance.id_history[-1])
        return
    else:
        console.process_cmdline("")
        return

appmain = [['a1', 'UCO',            'lambda: console.process_cmdline(" UCO ")'],
           ['a2', '36',             'lambda: None'],
           ['a3', '18',             'lambda: None'],
           ['a4', 'REL',            'lambda: None'],

           ['b1', 'HDG',            'lambda: console.process_cmdline(" HDG ")|'
                                    'lambda: show_basetid("apphdg", "apphdg")'],
           ['b2', 'POS',            'lambda: None'],
           ['b3', '',               None],
           ['b4', 'ACM',            'lambda: None'],

           ['c1', 'EFL',            'lambda: console.process_cmdline(" ALT FL")|'
                                    'lambda: show_basetid("appefl", "appefl")'],
           ['c2', 'TFL',            'lambda: None'],
           ['c3', 'LBL',            'lambda: None'],
           ['c4', 'ERA',            'lambda: None'],

           ['d1', 'SPD',            'lambda: console.process_cmdline(" SPD ")|'
                                    'lambda: show_basetid("appspd", "appspd")'],
           ['d2', 'DPL',            'lambda: None'],
           ['d3', '',               None],
           ['d4', 'RWY',            'lambda: None'],

           ['e1', 'REL',            'lambda: None'],
           ['e2', '',               None],
           ['e3', 'ATTN',           'lambda: None'],
           ['e4', 'UCO',            'lambda: console.process_cmdline(" UCO ")'],

           ['f1', 'COR',            'lambda: console.Console._instance.set_cmdline(console.Console._instance.command_line[:-1])'],
           ['f2', 'MAIN 2',         'lambda: None'],
           ['f3', 'APP\nMAPS',      'lambda: show_basetid("appmaps", "appmaps")'],
           ['f4', 'EXQ',            'lambda: console.Console._instance.stack(console.Console._instance.command_line)']]


apphdg = [['a1', 'ARTIP',       'lambda: console.process_cmdline("RIVER ")'],
          ['a2', 'SUGOL',       'lambda: console.process_cmdline("SUGOL ")'],
          ['a3', 'RIVER',       'lambda: console.process_cmdline("RIVER ")'],
          ['a4', '',            None],

          ['b1', '',            None],
          ['b2', '',            None],
          ['b3', '',            None],
          ['b4', '',            None],

          ['c1', '7',       'lambda: console.process_cmdline("7")'],
          ['c2', '4',       'lambda: console.process_cmdline("4")'],
          ['c3', '1',       'lambda: console.process_cmdline("1")'],
          ['c4', 'CLR',     'lambda: console.Console._instance.set_cmdline("")'],

          ['d1', '8',       'lambda: console.process_cmdline("8")'],
          ['d2', '5',       'lambda: console.process_cmdline("5")'],
          ['d3', '2',       'lambda: console.process_cmdline("2")'],
          ['d4', '0',       'lambda: console.process_cmdline("0")'],

          ['e1', '9',       'lambda: console.process_cmdline("9")'],
          ['e2', '6',       'lambda: console.process_cmdline("6")'],
          ['e3', '3',       'lambda: console.process_cmdline("3")'],
          ['e4', '',        None],

          ['f1', 'COR',     'lambda: console.Console._instance.set_cmdline(console.Console._instance.command_line[:-1])'],
          ['f2', 'EFL',     'lambda: console.process_cmdline(";")|'
                            'lambda: console.process_cmdline("ALT FL")|'
                            'lambda: apphdg.close()|'
                            'lambda: show_basetid("appefl", "appefl")'],
          ['f3', 'SPD',     'lambda: console.process_cmdline(";")|'
                            'lambda: console.process_cmdline("SPD")|'
                            'lambda: apphdg.close()|'
                            'lambda: show_basetid("appspd", "appspd")'],
          ['f4', 'EXQ',     'lambda: console.Console._instance.stack(console.Console._instance.command_line)|'
                            'lambda: apphdg.close()']]


appefl = [['a1', '',        None],
          ['a2', '090',     'lambda: console.process_cmdline("90 ")'],
          ['a3', '',        None],
          ['a4', '',        None],

          ['b1', '130',     'lambda: console.process_cmdline("130 ")'],
          ['b2', '',        None],
          ['b3', '',        None],
          ['b4', '',        None],

          ['c1', '7',       'lambda: console.process_cmdline("7")'],
          ['c2', '4',       'lambda: console.process_cmdline("4")'],
          ['c3', '1',       'lambda: console.process_cmdline("1")'],
          ['c4', 'CLR',     'lambda: console.Console._instance.set_cmdline("")'],

          ['d1', '8',       'lambda: console.process_cmdline("8")'],
          ['d2', '5',       'lambda: console.process_cmdline("5")'],
          ['d3', '2',       'lambda: console.process_cmdline("2")'],
          ['d4', '0',       'lambda: console.process_cmdline("0")'],

          ['e1', '9',       'lambda: console.process_cmdline("9")'],
          ['e2', '6',       'lambda: console.process_cmdline("6")'],
          ['e3', '3',       'lambda: console.process_cmdline("3")'],
          ['e4', '',        None],

          ['f1', 'COR',     'lambda: console.Console._instance.set_cmdline(console.Console._instance.command_line[:-1])'],
          ['f2', 'HDG',     'lambda: console.process_cmdline(";")|'
                            'lambda: console.process_cmdline("HDG ")|'
                            'lambda: appefl.close()|'
                            'lambda: show_basetid("apphdg", "apphdg")'],
          ['f3', 'SPD',     'lambda: console.process_cmdline(";")|'
                            'lambda: console.process_cmdline("SPD ")|'
                            'lambda: appefl.close()|'
                            'lambda: show_basetid("appspd", "appspd")'],
          ['f4', 'EXQ',     'lambda: console.Console._instance.stack(console.Console._instance.command_line)|'
                            'lambda: appefl.close()']]


appspd = [['a1', '250',     'lambda: console.process_cmdline("250 ")'],
          ['a2', '180',     'lambda: console.process_cmdline("180 ")'],
          ['a3', 'FAS',     None],
          ['a4', 'STD',     None],

          ['b1', '220',     'lambda: console.process_cmdline("220 ")'],
          ['b2', '160',     'lambda: console.process_cmdline("160 ")'],
          ['b3', '',        None],
          ['b4', '',        None],

          ['c1', '7',       'lambda: console.process_cmdline("7")'],
          ['c2', '4',       'lambda: console.process_cmdline("4")'],
          ['c3', '1',       'lambda: console.process_cmdline("1")'],
          ['c4', 'CLR',     'lambda: console.Console._instance.set_cmdline("")'],

          ['d1', '8',       'lambda: console.process_cmdline("8")'],
          ['d2', '5',       'lambda: console.process_cmdline("5")'],
          ['d3', '2',       'lambda: console.process_cmdline("2")'],
          ['d4', '0',       'lambda: console.process_cmdline("0")'],

          ['e1', '9',       'lambda: console.process_cmdline("9")'],
          ['e2', '6',       'lambda: console.process_cmdline("6")'],
          ['e3', '3',       'lambda: console.process_cmdline("3")'],
          ['e4', '',        None],

          ['f1', 'COR',     'lambda: console.Console._instance.set_cmdline(console.Console._instance.command_line[:-1])'],
          ['f2', 'HDG',     'lambda: console.process_cmdline(";")|'
                            'lambda: console.process_cmdline("HDG ")|'
                            'lambda: appspd.close()|'
                            'lambda: show_basetid("apphdg", "apphdg")'],
          ['f3', 'EFL',     'lambda: console.process_cmdline(";")|'
                            'lambda: console.process_cmdline("ALT FL")|'
                            'lambda: appspd.close()|'
                            'lambda: show_basetid("appefl", "appefl")'],
          ['f4', 'EXQ',     'lambda: console.Console._instance.stack(console.Console._instance.command_line)|'
                            'lambda: appspd.close()']]

