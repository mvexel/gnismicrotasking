'''
Created on Oct 17, 2011

@author: mvexel
'''

import web
import psycopg2
from random import shuffle
import simplejson as json

urls = (
    '/(.*)/(.*)', 'getgnis'
)


done = 0

app = web.application(urls, globals(), autoreload=False)
session = web.session.Session(app, web.session.DiskStore('/tmp/sessions'), initializer={'unseen': [], 'distances': [2^i/100 for i in range(0,5)], 'longitude': 0.0, 'latitude': 0.0})
application = app.wsgifunc()

class getgnis:
    def GET(self, longitude, latitude):
        if longitude != session.longitude or latitude != session.latitude:
            del session.unseen[:]
        session.longitude = longitude
        session.latitude = latitude
        if len(session.unseen) > 0:
            shuffle(session.unseen)
            return json.dumps(session.unseen.pop())
        else:
            while len(session.unseen) == 0 and len(session.distances) > 0:
                distance = session.distances.pop(0)
                session.unseen = self.getgnispoints(distance, longitude, latitude)
            if len(session.unseen) == 0:
                return json.dumps([])
            shuffle(session.unseen)
            return json.dumps(session.unseen.pop())

    def put(self, change):
        pass

    def getgnispoints(self, distance, longitude, latitude):
        conn = psycopg2.connect("host=localhost dbname=osm user=osm password=osm")
        cur = conn.cursor()
        strBox = '\'BOX(%f %f, %f %f)\'::box2d' % (float(longitude)-distance/2, float(latitude)-distance/2, float(longitude)+distance/2, float(latitude)+distance/2)
        querysql = "SELECT id, tags->'name',tags->'gnis:Class',ST_X(geom),ST_Y(geom) FROM nodes WHERE geom && %s AND tags ? 'gnis:id' AND version <= 2" % (strBox)
        cur.execute(querysql)
        return cur.fetchall()

if __name__ == "__main__":
    app.run()
