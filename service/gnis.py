'''
Created on Oct 17, 2011

@author: mvexel
'''
import os
import web
import psycopg2
from random import shuffle
import simplejson as json
import logging

urls = (
    '/(.*)/(.*)', 'getgnis'
)


done = 0

app = web.application(urls, globals())
pwd = os.path.dirname(__file__)
session = web.session.Session(app, web.session.DiskStore(os.path.join(pwd, 'sessions')), initializer={'unseen': [], 'seen': [], 'distances': [float(2**i)/100 for i in range(0,5)], 'coord': (0.0, 0.0)})
application = app.wsgifunc()

logging.basicConfig(filename='/tmp/debug.log',level=logging.DEBUG)

class getgnis:
    def GET(self, longitude, latitude):
        logging.debug('----------------------------------------')
        coord = float(longitude), float(latitude)
        logging.debug('distances %s' % session.distances)
        logging.debug('coord in: %s session: %s' % (coord, session.coord))
        if coord != session.coord:
            logging.debug('killing session')
            self.initsession(coord)
        session.coord = coord
        logging.debug('moving along')
        if len(session.unseen) > 0:
            logging.debug('still got %i points' % len(session.unseen))
            return self.nextgnispoint()
        else:
            while len(session.unseen) == 0 and len(session.distances) > 0:
                distance = session.distances.pop(0)
                logging.debug('going to fetch points for distance %f' % distance)
                for pt in self.getgnispoints(distance, coord):
                    if pt not in session.seen:
                        session.unseen.append(pt)
                    else:
                        logging.debug('seen %s' % str(pt))
                logging.debug('session unseen is now %i' % len(session.unseen))
            if len(session.unseen) == 0:
                logging.debug('exhausted..')
                return json.dumps([])
            return self.nextgnispoint()

    def getgnispoints(self, distance, coord):
        logging.debug('going to fetch points...')
        conn = psycopg2.connect("host=localhost dbname=osm user=osm password=osm")
        cur = conn.cursor()
        strBox = '\'BOX(%f %f, %f %f)\'::box2d' % (
                coord[0]-distance/2, 
                coord[1]-distance/2, 
                coord[0]+distance/2, 
                coord[1]+distance/2)
        querysql = "SELECT id, tags->'name',tags->'gnis:Class',ST_X(geom),\
                ST_Y(geom) FROM nodes WHERE geom && %s AND \
                tags ? 'gnis:id' AND version <= 2" % (strBox)
        logging.debug(querysql)
        cur.execute(querysql)
        results = cur.fetchall()
        logging.debug('got %i results' % len(results))
        return results

    def nextgnispoint(self):
            shuffle(session.unseen)
            nextup = session.unseen.pop()
            session.seen.append(nextup)
            return json.dumps(nextup)

    def initsession(self, coord):
        session.unseen = []
        session.distances = [float(2**i)/100 for i in range(0,5)]
        session.coord = (0.0,0.0)

if __name__ == "__main__":
    app.run()
