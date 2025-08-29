import Quartz

def get_window_list():
    window_list = []
    window_info_list = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for window_info in window_info_list:
        window_list.append(window_info)
    return window_list


def get_window_with_title(title):
    for window in get_window_list():
        window_title = window.get('kCGWindowName', 'No Title')
        if window_title == title:
            return window
    return None



def getGameCoordinates(gameName = 'Slay the Spire'):
    window_game = get_window_with_title(gameName)
    game_coordinates = [x for x in window_game['kCGWindowBounds'].values()]
    return game_coordinates # [left, height, top, width] 
