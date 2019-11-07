
import threading
import pika
import mysql.connector
import cv2
from imutils import resize,paths
import face_recognition
import os
import pickle
from os import environ
mysqlHost = environ['mysqlhost']
mysqlUser = environ['mysqluser']
mysqlpass = environ['mysqlpass']
mysqldatab = environ['mysqldb']

class HiveWorkers(threading.Thread):

    def DBCon(self):
        return mysql.connector.connect(host=mysqlHost, user=mysqlUser, passwd=mysqlpass, database=mysqldatab)



    def callbees(self, ch, method, properties, body):
        globaldb = self.DBCon()
        search = globaldb.cursor(buffered=True)
        query = "SELECT Age,gender from Augface where FaceToken='%s'" % body
        values = (body)
        search.execute(query)
        age,gender = search.fetchone()

        imagePaths = list(paths.list_images("./uploads/" + str(age) +"/"+str(gender)+ "/" + body + "/"))
        print imagePaths
        knownEncodings = []
        knownNames = []
        for (i, imagePath) in enumerate(imagePaths):
            print("Processing AugImage #{}/{}".format(i + 1, len(imagePaths)))
            name = imagePath.split(os.path.sep)[-1]
            print name
            print imagePath
            try:
                image1 = cv2.imread(imagePath)
                image = resize(image1, width=800)
            except:
                image = cv2.imread(imagePath)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="cnn")
            print boxes
            encodings = face_recognition.face_encodings(rgb, boxes)
            if len(encodings) > 0:
                for encoding in encodings:
                    knownEncodings.append(encoding)
                    knownNames.append(body)
                print("encoding...Please wait....")
                data = {"encodings": knownEncodings, "names": knownNames}
                f = open("uploads/" + str(age) + "/"+str(gender)+"/" + body + "/augtrain.train", "wab")
                f.write(pickle.dumps(data))
                f.close()
            else:
                print "NOT TRAINNED"
        try:
            globaldb = self.DBCon()
            search = globaldb.cursor(buffered=True)
            query = """UPDATE Augface SET Status = %s where FaceToken = %s"""
            args = (2, body)
            search.execute(query, args)
            globaldb.commit()

            search.close()
            globaldb.close()
        except:
            print "Models trainned but db not updated with status"
        print 'Models trainned'
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __init__(self):
            threading.Thread.__init__(self)

    def run(self):
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(mysqlHost))
            self.channel = self.connection.channel()
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(self.callbees, queue='Gpu-train')
            print 'start consuming'
            self.channel.start_consuming()

for _ in range(4):
        print 'launch thread'
        td = HiveWorkers()
        td.start()
