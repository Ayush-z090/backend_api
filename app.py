import os
from flask import Flask,request,jsonify,make_response
from pymongo import MongoClient
from dotenv import find_dotenv,load_dotenv
from pprint import pprint
from flask_cors import CORS
from bson.json_util import dumps,loads
import datetime
from flask_cors import CORS

from flask_jwt_extended import (
    set_access_cookies,JWTManager, create_access_token, get_jwt_identity, jwt_required
)

# find and load the .env variable here
load_dotenv(find_dotenv())
# creating an app 
app = Flask(__name__,instance_relative_config=True)

# cors setup so that the http reques can come from certain origin--done only for testing mode
CORS(app, supports_credentials=True)

jwt = JWTManager(app)


# creating default secret key
app.config.from_mapping(
    SECRET_KEY="dev",
    JWT_SECRET_KEY ="testing one",
    JWT_TOKEN_LOCATION=["cookies"] ,
    JWT_ACCESS_COOKIE_NAME="access_token_cookie",
    JWT_COOKIE_SECURE=False,
    JWT_COOKIE_CSRF_PROTECT=False,
    JWT_COOKIE_SAMESITE="None"
)

# accessing the env variable
password = os.environ.get("MONGODB_PWD")

# api url
connectionAPi_string = f"mongodb+srv://ayushsemwal:{password}@clustertesting.p5emx.mongodb.net/?retryWrites=true&w=majority&appName=ClusterTesting"

# asscess reff of cluster in mongodb
client = MongoClient(connectionAPi_string)
# assinign the databse collection to db
db = client['attendanceProject']
''' for teseting*********

# db["Students"].insert_one({"name":"johny deep","data":{
#     "message":"let me check",
#     "vals":[1,2,3]
# }})

dird = {"$push":{"data.vals":90}}

db["Students"].update_one({"name":"johny deep"},dird)
#***************
'''
@app.route('/')
def test():
    return "<h1> server is running on http://127.0.0.1:5000</h1>"

@app.route("/users",methods=["POST"])
def insert_user():
    try:
        # accepts user data
        userData=request.json
        userRole = userData["role"] # assign userRole to make the approach easier

        # check if userRole is valid collection or not and whether the user is alreafy in that database collection
        if userRole == "Students" and not db[userRole].find_one({"dataUserId":userData["dataUserId"]}):
            # need to add extra data to user for future development
            extraStu_data = {
                            "attendance_status":{
                                                    "M":"",
                                                    "E":""
                                                },
                            "totall_attendance":{
                                                    "M":0,
                                                    "E":0,
                                                    "days":0},
                                "sessional_year": None
                            }
            
            # inserting userdata from fetch and the extradata in a single dict using asterrxk operater to expand or spread the key value pairs
            db[userRole].insert_one({**userData,**extraStu_data})

            return jsonify({"message":"added user data succesfully","status":"OK"})
        
        # same approach for collection teachers

        elif userRole == "Teachers" and not db[userRole].find_one({"dataUserId":userData["dataUserId"]}):

            print("techer emter")
            extraTea_data={
                        "isSess":{
                                "status":False,
                                "sessional_year":None,
                                "sess_users":[]
                        }
            }

            db[userRole].insert_one({**userData,**extraTea_data})
            return jsonify({"message":"added user data succesfully","status":"OK"})

        else:
            print("Fail")
            return jsonify({"message":"user already exist","status":"found"})
        
        
        

    except Exception as e:
        print("error",e)
        return jsonify({"message":"iternal server error" ,"status":"worse"})
    




@app.route('/login',methods=["POST"])
def login():
    data = request.json

    password = data['password']
    
    student_paw = db["Students"].find_one({"dataUserId":data['id']},{"password":1,"role":1,"name":1,"course":1})

    teacher_paw = db["Teachers"].find_one({"dataUserId":data['id']},{"password":1,"role":1,"name":1,"course":1,"isSess":1})

    user = student_paw if student_paw  else teacher_paw if teacher_paw else None

    print(user)
    if not user:
        return jsonify({"message":"user with id %s didnt exist"%data['id'],"status":"notFound"})
    
    # user["_id"]=str(user['_id'])
    access_token = create_access_token(identity=dumps({"_id":user["_id"],"role":user["role"]}))


    if user["password"] and user["password"] == password:
        response = make_response(
            jsonify(
                {"message":"login successfull",
                 "status":"OK",
                 "role":user['role'],
                 "course":user["course"],
                 "isSess":user["isSess"],
                 "name":user["name"]
                 }))
        
        response.set_cookie("access_token_cookie",access_token,httponly=True,secure=True,samesite="None",max_age=3600 *1000)
        return response

    else:
        return jsonify({"message":"wrong password","status":"notFound"})
    


@app.route("/update",methods=["POST"])
@jwt_required()
def update():
    print("start")
    updateValues = request.json
    print(updateValues)
    print("start")
    token = get_jwt_identity()
    parsedToken = loads(token)
    result = db[parsedToken["role"]].update_one(
        {"_id":parsedToken["_id"]},
        updateValues
        )
    
    # print(result,"lplp")
    
    if result.matched_count == 0:
        return jsonify({"message":"user dosnt exist ","status":"notFound"})

    if result.modified_count > 0:
        return jsonify({"message":"updated succefully","status":"OK"})
    
    return jsonify({"message":"wrong requess","status":"error"})

@app.route('/read',methods=["GET","POST"])
@jwt_required(optional=True)
def info():
    data=get_jwt_identity()
    parseData = loads(data)
    print("method",parseData)

    if request.method == "GET":
        userDataField = db[parseData['role']].find_one({"_id": parseData["_id"]},{"_id":0})
        return dumps({"message":"user found","data":(userDataField)})

    if request.method=="POST":
        readFields = request.json
        print(readFields)
        userReadData = db[parseData['role']].find_one({"_id": parseData["_id"]},{"_id":0,**readFields})
        print(userReadData)
        return dumps({"message":"miketsting","val":userReadData})


# ...........glbal call............

@jwt.invalid_token_loader
def invalid_token_callback(reason):
    return jsonify({"msg": "Invalid token", "reason": reason}), 422

@jwt.unauthorized_loader
def missing_token_callback(reason):
    return jsonify({"msg": "Missing token", "reason": reason}), 422



if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True) 
