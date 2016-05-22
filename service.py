import xbmc
import json
import cal
import sys

""" Set your username and password for http://www.pogdesign.co.uk/cat """

USERNAME = 'myname'
PASS = 'mypass'

""""""

qGetWatchedEps = {"jsonrpc": "2.0", "id": 1,
                  "method": "VideoLibrary.GetEpisodes",
                  "params": {"filter": {"field": "playcount", "operator": "greaterthan", "value": "0"},
                             "properties": ["showtitle", "season", "episode", "firstaired", "playcount"]}}

def json_query(query):
    try:
        xbmc_request = json.dumps(query)
        result = xbmc.executeJSONRPC(xbmc_request)
        return json.loads(result)['result']
    except:
        return {}


def log(msg):
    xbmc.log('pogdesign-sync: ' + msg)


def lists_equal(l1, l2):
    if len(l1) != len(l2):
        return False

    if all(x in l2 for x in l1):
        return True


class EpMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)

    def onScanFinished(self, database):
        if database == 'video':
            Main.library_updated = True


class Main:
    def __init__(self):
        Main.library_updated = False
        self.Monitor = EpMonitor(self)
        self.eps_marked = []
        self.eps_watched = []
        self.run()

    def get_watched_eps(self):
        query_result = json_query(qGetWatchedEps)
        if 'episodes' in query_result:
            ret = query_result['episodes']
            lst = []
            for d in ret:
                lst.append([d['showtitle'], d['season'], d['episode'], d['firstaired']])
            return sorted(lst, key=lambda show: show[0])
        else:
            return []

    def full_sync(self):
        calendar = cal.Calendar()
        calendar.login(USERNAME, PASS)  # login to calendar
        self.eps_watched = self.get_watched_eps()  # get watched eps from library
        if not self.eps_watched:
            log('Library does not contain any "watched" episodes. There is nothing to update.')
        else:
            if not lists_equal(self.eps_watched, self.eps_marked):
                log('Library has been changed. Performing full sync.....')
                try:
                    for el in self.eps_watched:
                        epid = calendar.get_epid(el[0], el[1], el[2])
                        calendar.mark_watched(epid)  # mark them in calendar
                    self.eps_marked = self.eps_watched  # update list with already marked episodes
                    log('Full sync has been performed.')
                except:
                    log('Error while sending request to the calendar.')

    def run(self):
        # Initial full scan and sync:
        self.full_sync()

        while not xbmc.abortRequested:
            xbmc.sleep(500)
            if Main.library_updated:
                Main.library_updated = False
                self.full_sync()


if __name__ == '__main__':
    xbmc.sleep(2000)
    Main()
