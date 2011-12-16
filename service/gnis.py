'''
Created on Oct 17, 2011

@author: mvexel
'''

import sys
import web
import psycopg2
from random import sample
import simplejson as json

urls = (
    '/(.*)/(.*)', 'getgnis'
)

app = web.application(urls, globals(), autoreload=False)
session = web.session.Session(app, web.session.DiskStore('/tmp/sessions'), initializer={'seen': []})
application = app.wsgifunc()

class getgnis:
    def GET(self, lon, lat):
        if not lon and lat: 
            return "no no"
        conn = psycopg2.connect("host=localhost dbname=osm user=osm password=osm")
        cur = conn.cursor()
        for i in (0.01,0.02,0.05,0.1):
            strBox = '\'BOX(%f %f, %f %f)\'::box2d' % (float(lon)-i, float(lat)-i, float(lon)+i, float(lat)+i)
            sys.stderr.write(strBox)
            querysql = "SELECT id, tags->'name',tags->'gnis:Class',ST_X(geom),ST_Y(geom) FROM nodes WHERE geom && %s AND tags ? 'gnis:id' AND version <= 2" % (strBox)
            sys.stderr.write(querysql)
            cur.execute(querysql)
            recs = cur.fetchall()
            if len(recs) > 0:
                rec = sample(recs,1)
                if rec[0] in session.seen:
                    continue
                session.seen.append(rec[0])
                return json.dumps(rec, len(session.seen))
        return json.dumps([])

def put(self, change):
        pass

if __name__ == "__main__":
    app.run()
