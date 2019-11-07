import pika
import multiprocessing
import mysql.connector
from os import environ
mysqlHost = environ['mysqlhost']
mysqlUser = environ['mysqluser']
mysqlpass = environ['mysqlpass']
mysqldatab = environ['mysqldb']


class beehive(multiprocessing.Process):

    def DBCon():
        return mysql.connector.connect(host=mysqlHost, user=mysqlUser, passwd=mysqlpass, database=mysqldatab)

    def callbees(self, ch, method, properties, body):
        try:
            stoken,FToken = body.split(":")
            globaldb = self.DBCon()
            search = globaldb.cursor(buffered=True)
            search.execute("""UPDATE Search \
                            SET matched = REPLACE(matched, '%s:', ''), \
                            unmatched = concat(ifnull(unmatched,""),"%s:") \
                            WHERE stoken='%s'""" % (FToken, FToken, stoken) )
            globaldb.commit()
            search.close()
            globaldb.close()
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception,e:
            print e

    def run(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(mysqlHost))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.callbees, queue='misc')
        print 'start consuming'
        self.channel.start_consuming()


if __name__ == '__main__':
    bees = []
    for bee in range(3):
        p = beehive()
        bees.append(p)
        p.start()
    for j in bees:
        j.join()











