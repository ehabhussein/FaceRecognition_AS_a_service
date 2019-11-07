import pika
import threading
import face_recognition
import pickle
import mysql.connector
from os import environ
mysqlHost = environ['mysqlhost']
mysqlUser = environ['mysqluser']
mysqlpass = environ['mysqlpass']
mysqldatab = environ['mysqldb']

class HiveWorkers(threading.Thread):
    def DBCon(self):
        return mysql.connector.connect(host=mysqlHost, user=mysqlUser, passwd=mysqlpass, database=mysqldatab)

    def querybuild(self,radius,lat,lon,gender):
       return """SELECT 
       id,FaceToken,Age,gender,longitude,latitude
  FROM (
 SELECT z.latitude, z.longitude,Age,FaceToken,id,Reported,gender,Status,
        p.radius,
        p.distance_unit
                 * DEGREES(ACOS(COS(RADIANS(p.latpoint))
                 * COS(RADIANS(z.latitude))
                 * COS(RADIANS(p.longpoint - z.longitude))
                 + SIN(RADIANS(p.latpoint))
                 * SIN(RADIANS(z.latitude)))) AS distance
  FROM Augface AS z
  JOIN (   
        SELECT  %s  AS latpoint,  %s AS longpoint,
                %s AS radius,      111.045 AS distance_unit
    ) AS p ON 1=1
  WHERE z.latitude
     BETWEEN p.latpoint  - (p.radius / p.distance_unit)
         AND p.latpoint  + (p.radius / p.distance_unit)
    AND z.longitude
     BETWEEN p.longpoint - (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint))))
         AND p.longpoint + (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint)))) 
 ) AS d
 WHERE distance <= radius AND Reported=1 AND gender=%s AND Status=2 
 ORDER by distance"""%(lat,lon,radius,gender)

    def facefinder(self,lostP,findmeData,stoken,search_id, face_id,phase):
        toler = 0.5
        hits = 0
        globaldb = self.DBCon()
        search = globaldb.cursor(buffered=True)
        for encoding in lostP['encodings']:
            matches = face_recognition.compare_faces(findmeData["encodings"], encoding, tolerance=toler)
            if True in matches:
                hits +=1
        if hits > 0:
            search.execute("""update `Search` set matched = concat(ifnull(matched,""),"%s:") where stoken='%s'"""%(lostP['names'][0],stoken))
            globaldb.commit()
            print "updated the DB with match"
            hits =1
            print "Match found:" ,face_id
        else:
            hits = 0
        print "this is search_id: ", search_id[0]
        search.execute(
            "insert into search_trained_status (search_id, trained_id, phase,is_match) values (%s,%s,%s,%d) " % (search_id[0], face_id, phase,hits))
        globaldb.commit()
        search.close()
        globaldb.close()

    def callbees(self, ch, method, properties, body):
        filename, Age, stoken, lat, lon, pri, gender = body.split(":")
        globaldb = self.DBCon()
        search = globaldb.cursor(buffered=True)
        optisearch = globaldb.cursor(buffered=True)
        optisearch.execute("select searching from Search where stoken='%s'"%stoken)
        if '0' in str(optisearch.fetchone()):
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return 1
        self.findme = open('MISSING/'+Age+"/"+gender+"/"+stoken+"/"+"augtrain.train")
        self.findmeData = pickle.load(self.findme)
        phase = 0
        if int(properties.priority) >=200:
            search.execute(self.querybuild(100.0,lat,lon,gender))
            phase = 3
            pri = 151
        elif int(properties.priority) < 200 and int(properties.priority) >= 150:
            search.execute(self.querybuild(500.0, lat, lon, gender))
            phase = 4
            pri = 100
        elif int(properties.priority) < 150 and int(properties.priority) >= 100:
            search.execute("select id,FaceToken,Age,gender,longitude,latitude from Augface \
                            where age=%s and gender=%s and Reported=1 and Status=2" %(Age,gender))
            phase = 5
            pri = 99

        #get the search id from the search token
        optisearch.execute("select id from Search where stoken='%s'" %(str(stoken)))
        search_id = optisearch.fetchone()

        try:
            for row in search:
                face_id, FaceToken1, Age1, gender1, longitude1, latitude1 = row
                optisearch.execute("select id from search_trained_status where search_id='%s' and trained_id='%s' and phase='%s'"%(search_id[0], face_id, phase))
                match_exists = optisearch.fetchone()
                if match_exists: continue

                self.lostPT = open('uploads/'+str(Age1)+"/"+str(gender1)+"/"+FaceToken1+"/"+"augtrain.train")
                self.lostP =  pickle.load(self.lostPT)
                self.facefinder(self.lostP,self.findmeData,stoken,search_id,face_id,phase)
                self.findme.close()
                self.lostPT.close()
            optisearch.close()
            search.close()
            globaldb.close()
            connection = pika.BlockingConnection(pika.ConnectionParameters(mysqlHost))
            channel = connection.channel()
            channel.basic_publish(exchange='Augbee', routing_key='Gsearch' if int(pri) >= 100 else 'Csearch',
                                  properties=pika.BasicProperties(priority=int(pri)),
                                  body="%s:%s:%s:%s:%s:%s:%s" % (filename, Age, stoken, lat, lon, pri, gender))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception,e:
            print e
            print "No Matches against search criteria"


    def run(self):
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(mysqlHost))
            self.channel = self.connection.channel()
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(self.callbees, queue='Gpu-search')
            print 'start consuming'
            self.channel.start_consuming()

for _ in range(5):
        print 'launch thread'
        td = HiveWorkers()
        td.start()
