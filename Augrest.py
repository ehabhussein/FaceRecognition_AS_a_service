from flask import Flask, request, jsonify
import werkzeug
from imutils import resize
import face_recognition
import pickle
import cv2
import os
from pyzbar import pyzbar
from flask_restplus import Api,Resource,reqparse
import mysql.connector
from uuid import uuid4
import pika
import numpy
from os import environ
mysqlHost = environ['mysqlhost']
mysqlUser = environ['mysqluser']
mysqlpass = environ['mysqlpass']
mysqldatab = environ['mysqldb']
app = Flask(__name__)
api = Api(app)

UPLOAD_FOLDER = 'uploads/'
MISSING_FOLDER = 'MISSING/'
app.config['ALLOWED_EXTENSIONS'] = set(['zip','png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MISSING_FOLDER'] = MISSING_FOLDER


def retuuid():
    return uuid4()


def DBCon():
    return mysql.connector.connect(host=mysqlHost, user=mysqlUser, passwd=mysqlpass, database=mysqldatab)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


###################################################################################################

@api.doc(description='Upload an image to search for matches accross our databases',params={'Auhtorization': {'name': 'Auhtorization',
                              'in': 'header',
                              'type': 'string',
                              'description': 'Auhtorization header'},\
                 'filename':{'name': 'filename',
                              'type': 'file',
                              'in': 'formData',
                              'description': 'file to be uploaded'},\
                 'age_range_id':'The age range required for searching',\
                 'lat':'current lat GPS coordinates',\
                 'lon':'current lon GPS coordinates',\
                 'pri':'Prioritiy of the search. 100 and > goto GPU .... < 100 goto CPU',\
                 'gender':'female=0 , male =1',\
                 'stoken':'search token sent with request to have the ability to track in the databases'})
class FaceSearcher(Resource):
    def post(self):
        #print "im frere"
        try:
            parse = reqparse.RequestParser()
            parse.add_argument('Auhtorization', location='headers', required=True)
            parse.add_argument('filename', type=werkzeug.datastructures.FileStorage, location='files',required=True)
            parse.add_argument('age_range_id', dest='age_range_id')
            parse.add_argument('lat',dest='lat')
            parse.add_argument('lon',dest='lon')
            parse.add_argument('pri', dest='pri')
            parse.add_argument('gender',dest='gender', required=True)
            parse.add_argument('stoken', dest='stoken')
            args = parse.parse_args()
            if args['Auhtorization'] != "58ff72d1-25e6-441b-8638-49b2dd6d8e8c":
                return jsonify(error="Unauthorized")
            uploaded_files = args['filename']
            Age = args['age_range_id'] if args['age_range_id'] else "0"
            lat = args['lat'] if args['lat'] else "0"
            lon = args['lon'] if  args['lon'] else "0"
            pri = args['pri'] if args['pri'] else "0"
            gender = args['gender']
            filename = werkzeug.secure_filename(uploaded_files.filename)
            stoken = args['stoken']
            try:
                os.makedirs(app.config['MISSING_FOLDER'] + Age +"/"+gender+ "/" + stoken)
                uploaded_files.save(app.config['MISSING_FOLDER'] + Age +"/"+gender+ "/" + stoken + "/" + filename)
                try:
                    image1 = cv2.imread(app.config['MISSING_FOLDER'] + Age + "/" +gender+"/"+ stoken + "/" + filename)
                    image = resize(image1, width=800)
                except:
                    image = cv2.imread(app.config['MISSING_FOLDER'] + Age + "/" +gender+"/"+ stoken + "/" + filename)
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                boxes = face_recognition.face_locations(rgb, model="cnn")
                knownEncodings = []
                knownNames = []
                encodings = face_recognition.face_encodings(rgb, boxes)
                if len(encodings) > 0:
                    for encoding in encodings:
                        knownEncodings.append(encoding)
                        knownNames.append(stoken)
                    data = {"encodings": knownEncodings, "names": knownNames}
                    f = open(app.config['MISSING_FOLDER'] + Age + "/" + gender+"/"+stoken + "/augtrain.train", "wb")
                    f.write(pickle.dumps(data))
                    f.close()
                    # add set into databases the status of the trained subject
                else:
                    return "NOT TRAINNED, No faces found"
                connection = pika.BlockingConnection(pika.ConnectionParameters(mysqlHost))
                channel = connection.channel()
                channel.basic_publish(exchange='Augbee', routing_key='Gsearch' if int(pri) >= 100 else 'Csearch', properties=pika.BasicProperties(priority=int(pri)),
                                          body="%s:%s:%s:%s:%s:%s:%s" % (filename, Age, stoken, lat, lon, pri, gender))
                connection.close()
                try:
                    globaldb = DBCon()
                    search = globaldb.cursor(buffered=True)
                    query = """insert into Search (stoken,age,lat,lon,gender,status,searching) VALUES(%s,%s,%s,%s,%s,%s)"""
                    vals = (stoken, Age, lat, lon, gender,1,1)
                    search.execute(query, vals)
                    globaldb.commit()
                except Exception,e:
                    return jsonify(error=e)#"Error inserting into search database")
                return jsonify(status='queued')
            except Exception, e:
                return jsonify(Error=e)
        except Exception,e:
            return jsonify(error="something broke while searching:%s"%e)


###############################################################################################3
@api.doc(description='Barcode and QRcode image recognition',params={'Auhtorization': {'name': 'Auhtorization',
                              'in': 'header',
                              'type': 'string',
                              'description': 'Auhtorization header'},\
                 'filename':{'name': 'filename',
                              'type': 'file',
                              'in': 'formData',
                              'description': 'file to be uploaded'}})

class BarQR(Resource):
        def post(self):
            try:
                parse = reqparse.RequestParser()
                parse.add_argument('Auhtorization', location='headers',required=True)
                parse.add_argument('filename', type=werkzeug.datastructures.FileStorage, location='files',required=True)
                args = parse.parse_args()
                if args['Auhtorization'] != "58ff72d1-25e6-441b-8638-49b2dd6d8e8c":
                    print request.remote_addr
                    return jsonify(error="Unauthorized")
                uploaded_files = args['filename']
                nparr = numpy.fromstring(uploaded_files.read(), numpy.uint8)
                image1 = cv2.imdecode(numpy.fromstring(nparr, numpy.uint8), cv2.IMREAD_UNCHANGED)
                #image = resize(image1)
                barcodes = pyzbar.decode(image1)
                print len(barcodes)
                if len(barcodes) > 0:
                    for barcode in barcodes:
                            barcodeData = barcode.data.decode("utf-8")
                            barcodeType = barcode.type
                            return jsonify(type=barcodeType, data=barcodeData)
                else:
                    return jsonify(error="no barcodes detected")
            except Exception,e:
                            return jsonify(error=str(e))

################################################################################

@api.doc(description='Upload and enroll a person in our database , this uses a Zip filed full of images. once uploaded it is sent to training',\
         params={'Auhtorization': {'name': 'Auhtorization',
                              'in': 'header',
                              'type': 'string',
                              'description': 'Auhtorization header',
                                'required':True},\
                 'filename':{'name': 'filename',
                              'type': 'file',
                              'in': 'formData',
                              'description': 'Zipfile to be uploaded'},\
                 'age_range_id':'The age range required for searching',\
                 'new':'existing =1 , new =0',\
                 'gender':'female=0, male =1',\
                 'pri':'Prioritiy of the search. 100 and > goto GPU .... < 100 goto CPU',\
                 'gender':'female=0 , male =1',\
                 'type':'is it a face , passport photo m...etc ... unimplemented yet.',\
                 'ftoken':'facetoken'})
class uploadImages(Resource):
        def post(self):
                stoken = uuid4()
                parse = reqparse.RequestParser()
                parse.add_argument('Auhtorization', location='headers',required=True)
                parse.add_argument('filename', type=werkzeug.datastructures.FileStorage, location='files',required=True)
                parse.add_argument('ftoken', dest='ftoken',required=True)
                parse.add_argument('age_range_id',dest='age_range_id',required=True)
                parse.add_argument('new',dest="new",required=True)
                parse.add_argument('gender',dest='gender',required=True)
                parse.add_argument('type', dest='type')
                parse.add_argument('pri', dest='pri', required=True)
                #parse.add_argument('rep',dest='rep')
                #parse.add_argument('lon',dest='lon')
                #parse.add_argument('lat',dest='lat')
                args = parse.parse_args()
                if args['Auhtorization'] != "58ff72d1-25e6-441b-8638-49b2dd6d8e8c":
                    return jsonify(error="Unauthorized")
                file = args['filename']
                gender = args['gender']
                name = args['ftoken']
                age = args['age_range_id']
                archivestatus = args['new']
                #adding long lat for testing purposes remove later along with reported
                rep = 0
                lon = 0
                lat = 0
                pri = 0
                if file and allowed_file(file.filename):
                        try:
                            os.makedirs(app.config['UPLOAD_FOLDER']+age+"/"+gender+"/"+werkzeug.secure_filename(name))
                        except Exception,e:
                           print e
                        filename = werkzeug.secure_filename(file.filename)
                        print filename, name , age
                        file.save(os.path.join(app.config['UPLOAD_FOLDER']+age+"/"+gender+"/"+name+"/"+filename))
                        connection = pika.BlockingConnection(pika.ConnectionParameters(mysqlHost))
                        channel = connection.channel()
                        channel.basic_publish(exchange='Augbee',routing_key='upload',body="%s:%s:%s:%s:%s:%s:%s:%s:%s"%(filename,age,stoken,name,archivestatus,gender,rep,lat,lon))
                        connection.close()
                        return jsonify(status="ok")
                else:
                        return jsonify(Error="File type not allowed")




#############################################################################33
@api.doc(description='The status of a person: 0= uploaded , 1 = queued , 2 = trainning , 3 = trained',params={'Auhtorization': {'name': 'Auhtorization',
                              'in': 'header',
                              'type': 'string',
                              'description': 'Auhtorization Header'},\
                'stoken': {'name': 'stoken',
                              'type': 'string',
                              'description': 'search Token'},

                 })
class Tstatus(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('Auhtorization', location='headers',required=True)
        parse.add_argument('SToken', dest='SToken',required=True)
        args = parse.parse_args()
        if args['Auhtorization'] != "58ff72d1-25e6-441b-8638-49b2dd6d8e8c":
            return jsonify(error="Unauthorized")
        globaldb = DBCon()
        search = globaldb.cursor(buffered=True)
        search.execute("SELECT Status from Augface where StatusToken='%s' OR FaceToken='%s'"%(args['SToken'],args['SToken']))
        try:
            result = search.fetchone()[0]
            search.close()
            globaldb.close()
        except:
            try:
                search.execute(
                    "SELECT status from Search where StatusToken='%s'" % werkzeug.secure_filename(args['SToken']))
                result = search.fetchone()[0]
                search.close()
                globaldb.close()
            except:
                return jsonify(error="*Not in DB*")
        if result:
                return jsonify(status=result)
        else:
                return jsonify(error="Not in DBs")




###############################################################################3
@api.doc(description='Mark a person as Reported so he can be searched',params={'Auhtorization': {'name': 'Auhtorization',
                              'in': 'header',
                              'type': 'string',
                              'description': 'Auhtorization Header'},\
                'lon': {'name': 'lon',
                              'type': 'string',
                              'description': 'Longitute'},\
                'lat': {'name': 'lat',
                              'type': 'string',
                              'description': 'Latitude'},\
                'ftoken': {'name': 'ftoken',
                              'type': 'string',
                              'description': 'Face Token'},

                 })
class Taken(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('Auhtorization', location='headers',required=True)
        parse.add_argument('ftoken', dest='ftoken',required=True)
        parse.add_argument("lon",dest='lon')
        parse.add_argument('lat',dest='lat')
        args = parse.parse_args()
        if args['Auhtorization'] != "58ff72d1-25e6-441b-8638-49b2dd6d8e8c":
            return jsonify(error="Unauthorized")
        globaldb = DBCon()
        search = globaldb.cursor(buffered=True)
        try:
            search.execute("UPDATE Augface SET Reported=%s,longitude=%s,latitude=%s where FaceToken='%s'" % \
                           (1,args['lon'],args['lat'],args['ftoken']))
            globaldb.commit()
            search.close()
            globaldb.close()
            return jsonify(status="ok")
        except Exception,e:
            return jsonify(error=e)


####################################################################################

@api.doc(description='Remove a person from the Reported  status',params={'Auhtorization': {'name': 'Auhtorization',
                              'in': 'header',
                              'type': 'string',
                              'description': 'Auhtorization Header'},\
                'ftoken': {'name': 'ftoken',
                              'type': 'string',
                              'description': 'Face Token'},

                 })
class report_cancel(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('Auhtorization', location='headers',required=True)
        parse.add_argument('ftoken', dest='ftoken',required=True)
        args = parse.parse_args()
        if args['Auhtorization'] != "58ff72d1-25e6-441b-8638-49b2dd6d8e8c":
            return jsonify(error="Unauthorized")
        globaldb = DBCon()
        search = globaldb.cursor(buffered=True)
        try:
            search.execute("UPDATE Augface SET Reported=%s where FaceToken='%s'" %(0, args['ftoken']))
            globaldb.commit()
            search.close()
            globaldb.close()
            return jsonify(status="ok")
        except:
            return jsonify(error="Unknown FaceToken")


#########################################################################################################


@api.doc(description='Remove a facetoken from a match that was invalid',params={'Auhtorization': {'name': 'Auhtorization',
                              'in': 'header',
                              'type': 'string',
                              'description': 'Auhtorization Header'},\
                'stoken': {'name': 'stoken',
                              'type': 'string',
                              'description': 'Search Token'},\
                'ftoken': {'name': 'ftoken',
                              'type': 'string',
                              'description': 'Face Token'},

                 })
class unmatch(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('Auhtorization', location='headers', required=True)
        parse.add_argument('FToken', dest='FToken', required=True)
        parse.add_argument('stoken', dest='stoken', required=True)
        args = parse.parse_args()
        if args['Auhtorization'] != "58ff72d1-25e6-441b-8638-49b2dd6d8e8c":
            return jsonify(error="Unauthorized")
        try:

            connection = pika.BlockingConnection(pika.ConnectionParameters(mysqlHost))
            channel = connection.channel()
            channel.basic_publish(exchange='Augbee', routing_key='misc',
                                  body="%s:%s" % (args['stoken'], args['FToken']))
            connection.close()
            return jsonify(status="ok")
        except Exception,e:
            return jsonify(error=e)



###################################################################################
@api.doc(description='Get a full report in regards to the search status accross the entire database',params={'Auhtorization': {'name': 'Auhtorization',
                              'in': 'header',
                              'type': 'string',
                              'description': 'Auhtorization Header'}})
class status(Resource):
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('Auhtorization', location='headers', required=True)
        args = parse.parse_args()
        if args['Auhtorization'] != "58ff72d1-25e6-441b-8638-49b2dd6d8e8c":
            return jsonify(error="Unauthorized")
        globaldb = DBCon()
        search = globaldb.cursor(buffered=True)
        search.execute("SELECT id,status,stoken,matched from Search")
        row_headers = [x[0] for x in search.description]
        fetall = search.fetchall()
        json_data = []
        for result in fetall:
            json_data.append(dict(zip(row_headers, result)))
        return jsonify(json_data)


##################################################################

@api.doc(description='Remove a person from being searched',params={'Auhtorization': {'name': 'Auhtorization',
                                   'in': 'header',
                                   'type': 'string',
                                   'description': 'Auhtorization Header'}, \
                 'stoken': {'name': 'stoken',
                            'type': 'string',
                            'description': 'Search Token'}})
class stop_searching_person(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('Auhtorization', location='headers', required=True)
        parse.add_argument('stoken', dest='stoken', required=True)
        args = parse.parse_args()
        if args['Auhtorization'] != "58ff72d1-25e6-441b-8638-49b2dd6d8e8c":
            return jsonify(error="Unauthorized")
        globaldb = DBCon()
        search = globaldb.cursor(buffered=True)
        try:
            search.execute("UPDATE Search SET searching=0 where stoken='%s'" % (args['stoken']))
            globaldb.commit()
            search.close()
            globaldb.close()
            return jsonify(status="ok")
        except:
            return jsonify(error="Unknown stoken")



if __name__ == '__main__':
        api.add_resource(BarQR, '/service/barcode/identify')
        api.add_resource(uploadImages, '/service/peoplefinder/train')
        api.add_resource(FaceSearcher, '/service/peoplefinder/search')
        api.add_resource(Tstatus,'/service/peoplefinder/status')
        api.add_resource(Taken,'/service/peoplefinder/report')
        api.add_resource(report_cancel, '/service/peoplefinder/report/cancel')
        api.add_resource(unmatch,"/service/peoplefinder/unmatch")
        api.add_resource(status, "/service/peoplefinder/search/status")
        api.add_resource(stop_searching_person, "/service/peoplefinder/search/unsearch")
        app.run(host="0.0.0.0",port=int("5002"),debug=True, threaded=True)
