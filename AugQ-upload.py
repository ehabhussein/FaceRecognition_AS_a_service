import pika
import multiprocessing
import zipfile
import mysql.connector
import os
from os import environ
mysqlHost = environ['mysqlhost']
mysqlUser = environ['mysqluser']
mysqlpass = environ['mysqlpass']
mysqldatab = environ['mysqldb']


class beehive(multiprocessing.Process):
    def DBCon(self):
        return mysql.connector.connect(host=mysqlHost, user=mysqlUser, passwd=mysqlpass, database=mysqldatab)

    def callbees(self, ch, method, properties, body):
        filename,age,stoken,Ftoken,archivestatus,gender,rep,lat,lon = body.split(":")
        print stoken
        try:
            x = zipfile.ZipFile("uploads/%s/%s/%s/%s" %(age,gender,Ftoken,filename))
            x.extractall("uploads/%s/%s/%s/"%(age,gender,Ftoken))
            FList = os.listdir(os.getcwd()+"/uploads/%s/%s/%s/" %(age,gender,Ftoken))
            print FList
            FListC = FList[1:]
            m = 0
            for i in FListC:
                fileExtension = os.path.splitext(os.getcwd()+"/uploads/%s/%s/%s/"%(age,gender,Ftoken)+i)[1]
                os.rename(os.getcwd()+"/uploads/%s/%s/%s/"%(age,gender,Ftoken)+i, os.getcwd()+"/uploads/%s/%s/%s/"%(age,gender,Ftoken)+str(m) + fileExtension)
                m = m + 1
        except Exception,e:
            print "error Unzipping: ",e
        try:
            globaldb = self.DBCon()
            search = globaldb.cursor(buffered=True)
            if archivestatus == "0":
                query = """insert into Augface (StatusToken,Age,Status,FaceToken,gender,Reported,latitude,longitude) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"""
                vals =(stoken, age, 1,Ftoken,gender,rep,lat,lon)
                search.execute(query,vals)
                globaldb.commit()
            else:
                query = """UPDATE Augface SET StatusToken = %s , Status = %s where FaceToken = %s"""
                args = (stoken,1,Ftoken)
                search.execute(query,args)
                globaldb.commit()
            search.close()
            globaldb.close()
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(mysqlHost))
                self.channel = self.connection.channel()
                self.channel.basic_publish(exchange='Augbee', routing_key='gpu', body="%s" % Ftoken)
                self.connection.close()
                print "Sent To queue for training"
            except:
                print "Error sending to exchange"
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception, e:
            print "error inserting", e


    def run(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(mysqlHost))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.callbees, queue='Cpu-prep')
        print 'start consuming'
        self.channel.start_consuming()


if __name__ == '__main__':
    bees = []
    for bee in range(4):
        p = beehive()
        bees.append(p)
        p.start()
    for j in bees:
        j.join()
