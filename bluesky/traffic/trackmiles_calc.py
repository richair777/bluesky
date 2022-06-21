

def get_hdg_changes(section_dir):
    hdg_change = []
    for i in range(1, len(section_dir)):
        hdg_change.append(section_dir[i] - section_dir[i-1])
    return hdg_change


