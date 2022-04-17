__author__ = 'dev'
from flask import Flask, render_template, url_for, jsonify, Blueprint, request, redirect, send_from_directory
import logging
from werkzeug.utils import secure_filename
from datetime import date
import pdb
import os
import math
import requests
import json
import re

logging.basicConfig(filename='mdsbugs.log',level=logging.DEBUG)
logging.info('Start of Main logging')

MOBILE_FONT = 36
MOBILE_WIDGET_SCALE = 2
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class MainBlueprint(Blueprint):
    def __init__(self, blueprintname, name):
        super().__init__(blueprintname,name)

main_blueprint = MainBlueprint('main_Blueprint',__name__)

from DBHelper import DBHelper

UPLOAD_FOLDER = './templates/public/images'
#UPLOAD_FOLDER = '/var/www/mydefensiblespace.org/html/templates/public/images'


dbhelper = DBHelper()
app = Flask(__name__, static_url_path='/public')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def cityLatLongRecord(county, city):
    found =False
    lat = 38.0
    lng = -122.0
    prog = re.compile(r'^([a-zA-Z\s]+).+\s+(\d+\.\d+)\s(\d+\.\d+)$')
    with app.open_resource('../public/assets/{}_latlongs.txt'.format(county),'rt') as fr:
    #if os.path.exists("./templates/public/assets/{}_latlongs.txt".format(county)):
        #with open("./templates/public/assets/{}_latlongs.txt".format(county),'r') as fr:
        for loc in fr:
            #m = re.search(r'^([a-zA-Z\s]+).+[^\d]+(\d+\.\d+)\s(\d+\.\d+)$',loc)
            m = prog.search(loc)
            if m:
                if m.group(1).lower() == city.lower():
                    lat = float(m.group(2))
                    lng = -float(m.group(3))
                    found = True
                    break;
    return lat, lng, found

def getweatherapi(lon,lat):
    #lat, lon, found = cityLatLongRecord(county,city)
    #found = False
    #if not found:
    #    return 0, 0, '?', [], [], []
    onecallurl = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=hourly,minutely&appid=1afefa2f7805b4ee4451d826a33f59f7".format(lat,lon)
    response = requests.get(onecallurl)
    data = response.json()
    current = data['current']
    currentemp = current['temp']
    currentemp = (currentemp - 273.15) * 9/5 + 32 # (temp - 273.15) * 9/5 + 32
    currenthumidity = current['humidity']
    currentweather = current['weather'][0]['main']
    wind = current['wind_speed']

    daily = data['daily']
    temps = [((d['temp']['max'] - 273.15) * 9/5 + 32) for d in daily]
    humidities = [d['humidity'] for d in daily]
    weather = [d['weather'][0]['main'] for d in daily]

    #url = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid=1afefa2f7805b4ee4451d826a33f59f7".format(lat,lon)
    # sanrafaelurl = "https://api.openweathermap.org/data/2.5/weather?lat=37.9735&lon=-122.5311&appid=1afefa2f7805b4ee4451d826a33f59f7"
    # response = requests.get(sanrafaelurl)
    # #pdb.set_trace()
    # data = response.json()
    # main = data['main']
    # temp = main['temp']
    # temp = (temp - 273.15) * 9/5 + 32 # (temp - 273.15) * 9/5 + 32
    # humidity = main['humidity']
    # wind = data['wind']
    return currentemp, currenthumidity, currentweather, temps, humidities, weather

# @main_blueprint.route('/weather/<string:city>')
# def getweather(city):
#     currentemp, currenthumidity, currentweather, temps, humidities, weather  = getweatherapi(city)
#     return jsonify({'temp':temp, 'humidity':humidity, 'wind':wind})

@main_blueprint.route('/html/<string:html>')
def showhtml(html):
    return render_template("staticpages/"+ html + ".html")

@main_blueprint.route('/forum')
def gotoforum():
    return redirect("https://mydefensiblespace.net/board/index.php")

@main_blueprint.route('/showparcel')
def showparcel():
    fp = open("mydefensible276ArroroRd.geojson",'r')
    geostring = fp.read()
    return geostring

def getbusinesses(county):
    sql = "SELECT name, address, city FROM users WHERE role = 'business' and county = '{}'".format(county)
    res = dbhelper.dbFetchAll(sql)
    return res

@main_blueprint.route('/showfirewise/<string:county>/<string:city>/<string:community>')
def showfirewise(county, city, community):
    return render_template("MyDefCommMapView.html",county=county, city=city, community=community.upper())


@main_blueprint.route('/adminmydefensiblespace')
def adminmydefensiblespace():
    data = dbhelper.dbFetchAll("SELECT name FROM counties WHERE statefp = '06';")
    counties = [d[0] for d in data]
    return render_template("adminMyDefComm.html",county='placer', counties=counties)


@main_blueprint.route('/getcommunities/<string:county>', methods=['GET','POST'])
def getcommunities(county):
    data = dbhelper.dbFetchAll("SELECT DISTINCT(community) FROM USERS WHERE LOWER(county) = '{}'".format(county.lower()))
    return jsonify(data)


@main_blueprint.route('/getcommunitiesctygeo/<string:county>', methods=['GET','POST'])
def getcommunitiesctygeo(county):
    try:
        data = dbhelper.dbFetchAll("SELECT DISTINCT(community) FROM {}_parcels".format(county))
    except:
        data = []
    sql = """SELECT ST_AsGeoJSON(geom) as geometry
        FROM counties WHERE statefp = '{}' and LOWER(name) = '{}'""".format('06', county.lower())
    ctyboundary = dbhelper.getData(sql)
    #pdb.set_trace()
    return jsonify({'mdscoms':data, 'ctyboundary':ctyboundary})


@main_blueprint.route('/getcommunityparcels/<string:county>/<string:firewise>', methods=['GET','POST'])
def getcommunityparcels(county, firewise):
    data = {}
    #pdb.set_trace()
    try:
        data = dbhelper.getCountyFirewiseCommunity(county, firewise)
    except Exception as e:
        logging.info('Error '+str(e))
    return jsonify(data)

@main_blueprint.route('/logout', methods=['GET', 'POST'])
@main_blueprint.route('/', methods=['GET', 'POST'])
def greetings():
    return render_template("greeting.html")


@main_blueprint.route('/d1818', methods=['GET', 'POST'])
def diagnostic():
    results = ""
    if request.method.upper() == "POST":
        logging.info("Submitting SQL Query")
        try:
            sqltext = request.form.get('sqltext')
            if 'select' in sqltext.lower():
                results = dbhelper.dbFetchAll(sqltext)
            else:
                results = dbhelper.dbExecute(sqltext)
        except Exception as e:
            results = "sql call "+str(e);
            logging.error("sql call "+str(e))
        return render_template('diagnostic.html', sqltext=sqltext, queryresult=str(results))
    else:
        return render_template('diagnostic.html', sqltext="", queryresult="")


@main_blueprint.route('/loginmobile', methods=['GET', 'POST'])
@main_blueprint.route('/mobile', methods=['GET', 'POST'])
def loginmobile():
    print("logging in")
    if request.method.upper() == "POST":
        results = None
        logging.info("User is submitting credentials.")

        try:
            username = request.form.get('username')
            password = request.form.get('password')
            print("loging in ",username)
            sql = "SELECT address, city, state,community, role, county, avatar FROM users WHERE username = '{}' and password = '{}'"\
                                          .format(username, password)
            print(sql)
            results = dbhelper.dbFetchOne(sql)
        except Exception as e:
            print("Login api failed",str(e))
            logging.error("Login api failed "+str(e))

        if not results:
            print("no results")
            return render_template("indexmobile.html")

        try:
            address = results[0]
            city = results[1]
            role = results[4]
            county = results[5]
            avatar = results[6]
            sql = "SELECT xcoord, ycoord FROM {}_parcels WHERE UPPER(sit_city) = '{}' and UPPER(sit_full_s) = '{}'".format(county, city.upper(), address.upper())
            print(sql)
            xyresults = dbhelper.dbFetchOne(sql)
        except Exception as e:
            logging.error("Fetching parcel lat long failed "+str(e))
            return render_template("indexmobile.html", fontsize=MOBILE_FONT)

        print(xyresults)
        if not xyresults:
            return render_template("indexmobile.html")

        xcoord = xyresults[0]
        ycoord = xyresults[1]

        try:
            zone5 = dbhelper.dbFetchOne("SELECT status FROM {}_zone5 WHERE UPPER(sit_city) = '{}' and UPPER(sit_full_s) = '{}'".format(county, city.upper(), address.upper()))[0]
            zone30 = dbhelper.dbFetchOne("SELECT status FROM {}_zone30 WHERE UPPER(sit_city) = '{}' and UPPER(sit_full_s) = '{}'".format(county, city.upper(), address.upper()))[0]
            zone100 = dbhelper.dbFetchOne("SELECT status FROM {}_zone100 WHERE UPPER(sit_city) = '{}' and UPPER(sit_full_s) = '{}'".format(county, city.upper(), address.upper()))[0]
        except:
            zone5 = "none"
            zone30 = "none"
            zone100 = "none"

        #pdb.set_trace()
        if role == "leader":
            community=results[3]
            communitymembers = dbhelper.dbFetchAll("SELECT address,city FROM users WHERE UPPER(community) = '{}'".format(community.upper()))
            communitymembersJSON = [{'address':item[0], 'city':item[1]} for item in communitymembers]
        else:
            communitymembersJSON = []
        if results:
            communityresults = dbhelper.dbFetchAll("SELECT DISTINCT(community) FROM users WHERE county = '{}'".format(county))
            citycommunities = [c[0] for c in communityresults]
            member = role.lower() == "member" or role.lower() == "leader"
            if role == 'business':
                cities = dbhelper.dbFetchAll("SELECT * FROM {}_cities;".format(county))
                cities = [c[0] for c in cities]

                return render_template("worksubmission.html", message="", cities=cities, county=county, avatar=avatar)

            return render_template("homemobile.html", address=address, city=city, state=results[2], username=username.upper(),xcoord=xcoord, ycoord=ycoord, \
                                   community=results[3], role=role, county=county, members=communitymembersJSON, member=member, citycommunities=citycommunities,
                                   zone5=zone5, zone30=zone30, zone100=zone100, fontsize=MOBILE_FONT, widgetscale=MOBILE_WIDGET_SCALE)
        else:
            return render_template("indexmobil.html", fontsize=MOBILE_FONT)
    else:
        logging.info("User is opening logging page")
        return render_template("indexmobile.html", fontsize=MOBILE_FONT)


@main_blueprint.route('/logview/<string:user>', methods=['GET','POST'])
def logview(user):
    return render_template("logview.html", user=user)

@main_blueprint.route('/logviewmobile/<string:user>', methods=['GET','POST'])
def logviewmobile(user):
    return render_template("logviewmobile.html", user=user)


@main_blueprint.route('/mapview/<string:user>', methods=['GET','POST'])
def mapview(user):
    res = dbhelper.dbFetchOne("select address, city, community, county from users where upper(username) = '{}'".format(user.upper()))
    #pdb.set_trace()
    address = res[0]
    city = res[1]
    community = res[2]
    county = res[3]
    return render_template("mapmobile.html", county=county, city=city, address=address, community=community, username=user,fontsize=MOBILE_FONT)

@main_blueprint.route('/loginrest', methods=['GET', 'POST'])
def loginrest():
    return jsonify({"success":"true"})

@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    print("logging in")
    if request.method.upper() == "POST":
        results = None
        logging.info("User is submitting credentials.")

        try:
            username = request.form.get('username')
            password = request.form.get('password')
            print("loging in ",username)
            sql = "SELECT address, city, state, community, role, county, name, avatar FROM users WHERE username = '{}' and password = '{}'"\
                                          .format(username, password)
            print(sql)
            results = dbhelper.dbFetchOne(sql)
        except Exception as e:
            print("Login api failed",str(e))
            logging.error("Login api failed "+str(e))

        if not results:
            print("no results")
            return render_template("index.html")

        try:
            address = results[0]
            city = results[1]
            state = results[2]
            role = results[4]
            county = results[5]
            name = results[6]
            avatar = results[7]
            sql = "SELECT xcoord, ycoord FROM {}_parcels WHERE UPPER(sit_city) = '{}' and UPPER(sit_full_s) = '{}'".format(county, city.upper(), address.upper())
            print(sql)
            xyresults = dbhelper.dbFetchOne(sql)
        except Exception as e:
            logging.error("Fetching parcel lat long failed "+str(e))
            return render_template("index.html")

        print(xyresults)
        if not xyresults:
            return render_template("index.html")

        xcoord = xyresults[0]
        ycoord = xyresults[1]

        try:
            zone5 = dbhelper.dbFetchOne("SELECT status FROM {}_zone5 WHERE UPPER(sit_city) = '{}' and UPPER(sit_full_s) = '{}'".format(county, city.upper(), address.upper()))[0]
            zone30 = dbhelper.dbFetchOne("SELECT status FROM {}_zone30 WHERE UPPER(sit_city) = '{}' and UPPER(sit_full_s) = '{}'".format(county, city.upper(), address.upper()))[0]
            zone100 = dbhelper.dbFetchOne("SELECT status FROM {}_zone100 WHERE UPPER(sit_city) = '{}' and UPPER(sit_full_s) = '{}'".format(county, city.upper(), address.upper()))[0]
        except:
            zone5 = "none"
            zone30 = "none"
            zone100 = "none"

        #pdb.set_trace()
        if role == "leader":
            community=results[3]
            communitymembers = dbhelper.dbFetchAll("SELECT address,city FROM users WHERE UPPER(community) = '{}'".format(community.upper()))
            communitymembersJSON = [{'address':item[0], 'city':item[1]} for item in communitymembers]
        else:
            communitymembersJSON = []
        if results:
            communityresults = dbhelper.dbFetchAll("SELECT DISTINCT(community) FROM users WHERE county = '{}'".format(county))
            citycommunities = [c[0] for c in communityresults]
            member = role.lower() == "member" or role.lower() == "leader"

            currentemp, currenthumidity, currentweather, temps, humidities, weather  = getweatherapi(xcoord,ycoord)
            minspan = min(len(temps),len(humidities))
            forecast = [{"temp":round(temps[i],0),"humidity":humidities[i],"weather":weather[i]} for i in range(minspan)]

            if role == 'business':
                cities = dbhelper.dbFetchAll("SELECT * FROM {}_cities;".format(county))
                #pdb.set_trace()
                cities = [[float(c[0]),float(c[1]),c[2]] for c in cities]
                return render_template("worksubmission.html", temp=int(currentemp), humidity=currenthumidity,currentweather=currentweather, forecast=forecast,
                    message="",city=city,county=county.lower(),communities=citycommunities, cities=cities, name=name, state=state, role=role, community='none', username=username, avatar=avatar)

            businesses = getbusinesses(county)

            sql = """SELECT ST_AsGeoJSON(geom) as geometry
                FROM counties WHERE statefp = '{}' and LOWER(name) = '{}'""".format('06', county.lower())
            ctyboundary = dbhelper.getData(sql)
            

            return render_template("home.html",temp=int(currentemp), humidity=currenthumidity,currentweather=currentweather, forecast=forecast, ctyboundary=ctyboundary,
                                address=address, city=city, state=results[2], username=username.upper(),xcoord=xcoord, ycoord=ycoord, \
                                community=results[3], role=role, county=county, members=communitymembersJSON, member=member, citycommunities=citycommunities,
                                zone5=zone5, zone30=zone30, zone100=zone100, businesses=businesses)

        else:
            return render_template("index.html")
    else:
        logging.info("User is opening logging page")
        return render_template("index.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @main_blueprint.route('/submitworkperformed2/<string:county>', methods=['GET', 'POST'])
# def workperformed2(county):
#     data = request.get_json()
#     #pdb.set_trace()
#     name = data['name']
#     bizcity = data['bizcity']
#     streetname = data['streetname']
#     streetnumber = data['streetnumber']
#     streetsuffix = data['street_suffix']
#     str_dir = data['str_dir']
#     county = data['county']
#
#     if str_dir == 'NONE':
#         streetaddress = "{} {} {}".format(streetnumber,streetname,streetsuffix)
#     else:
#         streetaddress = "{} {} {} {}".format(streetnumber,str_dir,streetname,streetsuffix)
#     city = data['cityselect']
#     status = data['status']
#     state = data['state']
#     zip = data['zip']
#     description = data['description']
#     datestr = str(date.today())
#
#     filename = None
#
#     # Needs db additional columns and filenaming scheme and bizfolder
#     try:
#         if 'file' in request.files:
#             file = request.files['file']
#             if not file.filename == '':
#                 if file and allowed_file(file.filename):
#                     filename = secure_filename(file.filename)
#                     file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#     except Exception as e:
#         print("File Save Failed",str(e))
#
#     sql1 = "INSERT INTO workdone (bizname, bizcity, description, streetaddress, city, state, zipcode, county, date, status)\
#     VALUES ('{}', '{}', '{}', '{}', '{}','{}',  \
#     '{}', '{}', '{}', '{}')".format(name, bizcity, description, streetaddress, city, state, zip, county, datestr, status)
#
#     dbhelper.dbExecute(sql1)
#
#     return jsonify({'success':True,'message':''})




@main_blueprint.route('/workdone4member/<string:county>', methods=['GET','POST'])
def workdone4member(county):
    data = request.get_json()
    #name = data['name']
    sql = """
        SELECT wd.bizname, wd.bizcity, cp.XCOORD, cp.YCOORD FROM workdone as wd
        JOIN {}_parcels as cp ON wd.streetaddress = cp.SIT_FULL_S and wd.city = cp.SIT_CITY
         WHERE wd.county = '{}';
    """.format(county, county)
    workdone = dbhelper.dbFetchAll(sql)
    coordinates = [{'LON':float(c[-2]),'LAT':float(c[-1]),'props':c[0:2]} for c in workdone]
    workdone = [w[0:2] for w in workdone]
    return jsonify({'workdone':workdone, 'coordinates':coordinates})


@main_blueprint.route('/workreportedbymembers/<string:county>', methods=['GET','POST'])
def workReportedByMembers(county):
    data = request.get_json()
    city = data['city']
    address = data['address']
    community = data['community']
    # current
    sql = """select DISTINCT(address),xcoord, ycoord, avatar, community,  sit_city ,zone5, zone30, zone100, landscapeservice from
    (select DISTINCT(users.address), landscapeservice, avatar,zone5,zone30,zone100, date from memberlog as ml
    JOIN users ON users.address = ml.address ORDER BY date DESC) as q1
    JOIN {}_parcels as pp ON q1.address = pp.sit_full_s WHERE lower(pp.sit_city) = '{}';""".format(county.lower(),city.lower())
    # improvment:
    sql2 = """select mladdress, xcoord, ycoord, biz_avatar, community,  sit_city ,zone5, zone30, zone100, landscapeservice from
    (select DISTINCT(ml.address) as mladdress, landscapeservice, users.avatar as biz_avatar,zone5,zone30,zone100, date from memberlog as ml
    JOIN users ON ml.landscapeservice LIKE CONCAT(users.bizname,'%') ORDER BY date DESC) as q1
    JOIN {}_parcels as pp ON q1.mladdress = pp.sit_full_s WHERE lower(pp.sit_city) = '{}';""".format(county.lower(),city.lower())

    print("sql2",sql2)
    workdone = dbhelper.dbFetchAll(sql)
    coordinates = [[float(c[1]),float(c[2])] for c in workdone] #[{'LON':float(c[-2]),'LAT':float(c[-1]),'props':c[0:2]} for c in workdone]
    avatars = [c[3] for c in workdone]
    communities = [c[4] for c in workdone]
    status = [c[6:9] for c in workdone]
    workdone = [[w[0],w[4],w[5],w[9]] for w in workdone]
    print(sql)
    return jsonify({'workdone':workdone, 'coordinates':coordinates, 'avatars':avatars, 'communities':communities, 'status':status})

# BIZ FORM VERSION
@main_blueprint.route('/submitworkperformed', methods=['GET', 'POST'])
def workperformed():
    message = "SUBMITTED"
    if request.method == "POST":
        name = request.form.get('name')
        bizcity = request.form.get('bizcity')
        streetname = request.form.get('streetname')
        streetnumber = request.form.get('streetnumber')
        streetsuffix = request.form.get('street_suffix')
        county = request.form.get('county')
        streetaddress = "{} {} {}".format(streetnumber,streetname,streetsuffix)
        city = request.form.get('cityselect')
        status = request.form.get('status')
        state = request.form.get('state')
        zip = request.form.get('zip')
        description = request.form.get('description')
        datestr = str(date.today())
        filename = None
        # Needs db additional columns and filenaming scheme and bizfolder
        pdb.set_trace()
        before = ""
        after = ""
        try:
            if len(request.files) > 0:
                if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], name)):
                    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'],name))
                for name in request.files:
                    file = request.files[name]
                    if name == 'photobefore':
                        before = file.filename
                    if name == 'photoafter':
                        after = file.filename
                    if not file.filename == '':
                        if file and allowed_file(file.filename):
                            filename = secure_filename(file.filename)
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], name, filename))
                            #file.save(os.path.join("./",filename))
        except Exception as e:
            message = "dir:" + os.getcwd() + " error:" + str(e)

        sql1 = "INSERT INTO workdone (bizname, bizcity, description, streetaddress, city, state, zipcode, county, date, status, photobefore, photoafter)\
        VALUES ('{}', '{}', '{}', '{}', '{}','{}', '{}', '{}', '{}', '{}',  \
        '{}', '{}' )".format(name, bizcity, description, streetaddress, city, state, zip, county, datestr, status, before, after)
        dbhelper.dbExecute(sql1)
        #return render_template("worksubmission.html", message="",city=city,county=county)
    else:
        return redirect('/login')
    return message

# BIZ Calls
@main_blueprint.route('/workdone/<string:county>', methods=['GET','POST'])
def workdone(county):
    data = request.get_json()
    name = data['name']
    try:
        sql = """
            SELECT DISTINCT(wd.streetaddress,wd.city), cp.sit_full_s, cp.sit_city, wd.bizname ,wd.bizcity ,wd.description  ,wd.state ,wd.zipcode
           ,wd.status ,wd.date ,wd.county, wd.photobefore, wd.photoafter, cp.XCOORD, cp.YCOORD FROM workdone as wd
            JOIN {}_parcels as cp ON lower(wd.streetaddress) = lower(cp.SIT_FULL_S) and lower(wd.city) = lower(cp.SIT_CITY)
             WHERE wd.county = '{}' and wd.bizname = '{}' ORDER BY wd.date DESC;
        """.format(county, county, name)
        print(sql)
        workdone = dbhelper.dbFetchAll(sql)
        avatar = dbhelper.dbFetchOne("SELECT avatar FROM users where bizname = '{}'".format(name))
        coordinates = [{'LON':float(c[-2]),'LAT':float(c[-1]),'props':c[1:12]} for c in workdone]
        workdata = [{'address':w[1],'city':w[2],'description':w[5],'status':w[8],'photobefore':w[11],'photoafter':w[12]} for w in workdone]
        html = render_template("workdone.html",workdone=workdata)
    except:
        sql = "SELECT * from workdone WHERE bizname = {}".format(name)
        workdone = dbhelper.dbFetchAll(sql)
        html = render_template("workdone.html",workdone=workdata)
        avatar = "None"
        workdata = workdone
        coordinates = []
    return jsonify({'workdone':html, 'workdata':workdata, 'coordinates':coordinates, 'avatar':avatar})

# <thead><tr><th>Z1</th><th>Z2</th><th>Z3</th><th>EXPENSES</th><th>COMMENTS</th><th>SERVICE</th><th>DATE</th></tr><thead>
def getmymembers(user):
    members = []
    community = ""
    community = dbhelper.dbFetchOne("SELECT community from users where upper(username)='{}'".format(user.upper()))
    if len(community) > 0:
        members = dbhelper.dbFetchAll("Select username, name, address from users where upper(community) ='{}'".format(community[0].upper()))
        community = community[0]
    return members,community


@main_blueprint.route('/memberlog_photo/<string:county>/<string:user>', methods=['GET','POST'])
def memberlog_photo(county,user):
    before = ""
    after = ""
    address = request.form.get('address')
    city = request.form.get('city')
    date = request.form.get('date')
    try:
        if len(request.files) > 0:
            if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'],user)):
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'],user))
            for name in request.files:
                file = request.files[name]
                if name == 'photobefore':
                    before = file.filename
                if name == 'photoafter':
                    after = file.filename
                if not file.filename == '':
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], user, filename))
            sql = """UPDATE memberlog SET photobefore = '{}', photoafter = '{}'
                WHERE address = '{}' and city = '{}' and date = '{}'""".format(before, after, address, city, date)
    except Exception as e:
        print("File Save Failed",str(e))
    return render_template("home.html")


@main_blueprint.route('/memberlog/<string:county>', methods=['GET','POST'])
def memberlog(county):
    #pdb.set_trace()
    data = request.get_json()
    city = data['city']
    address = data['address']
    user = data['username']
    sql = "SELECT zone5, zone30, zone100, expenditures, comments,landscapeservice, date, satisfaction, photobefore, photoafter FROM memberlog WHERE city = '{}' and address = '{}'".format(city, address)
    memberlog = dbhelper.dbFetchAll(sql)
    memberlog = [[f[0][0],f[1][0],f[2][0],f[3],f[4],f[5],str(f[6])[0:10],f[7],f[8],f[9]] for f in memberlog]
    members,community = getmymembers(user)
    members2 = [{"username":m[0],"name":m[1]} for m in members]
    return jsonify({'memberlog':memberlog,  'community':community, 'mymembers':members2})


@main_blueprint.route('/memberlogmobile/<string:user>', methods=['GET','POST'])
def memberlogmobile(user):
    #pdb.set_trace()
    sql = "SELECT city, address, county from users where username = '{}'".format(user.lower())
    res = dbhelper.dbFetchOne(sql)
    city = res[0]
    county = res[2]
    address= res[1]
    print(sql)
    sql = "SELECT zone5, zone30, zone100, expenditures, comments, landscapeservice, date FROM memberlog WHERE city = '{}' and address = '{}'".format(city, address)
    memberlog = dbhelper.dbFetchAll(sql)
    memberlog = [(f[0][0],f[1][0],f[2][0],f[3],f[4],f[5],f[6]) for f in memberlog]
    #pdb.set_trace()
    return jsonify({'memberlog':memberlog})


@main_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        streetname = request.form.get('streetname')
        streetnumber = request.form.get('streetnumber')
        streetsuffix = request.form.get('street_suffix')
        str_dir = request.form.get('str_dir')
        if str_dir == 'NONE':
            streetaddress = "{} {} {}".format(streetnumber,streetname,streetsuffix)
        else:
            streetaddress = "{} {} {} {}".format(streetnumber,str_dir, streetname, streetsuffix)

        city = request.form.get('cityselect')
        state = request.form.get('state')
        zip = request.form.get('zip')
        password = request.form.get('password')
        community = request.form.get('community')
        county = request.form.get('county')
        role = request.form.get('role')

        sql = "SELECT * FROM {}_parcels WHERE lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), streetaddress.lower())
        results = dbhelper.dbFetchAll(sql)
        print(sql)
        if len(results) == 0:
            return render_template("register.html", message="Address entered does not match any known address")

        sql1 = "INSERT INTO users (name, username, email, address, city, state, zip, county, password, community, role)\
        VALUES ('{}', '{}', '{}', '{}', '{}','{}',  \
        '{}', '{}', '{}', '{}', '{}')".format(name, username, email, streetaddress, city, state, zip, county, password, community, role)
        sql2 = "UPDATE {}_parcels SET community = '{}' WHERE lower(sit_full_s) = '{}' and lower(sit_city) = '{}'".format(county, community.lower(), streetaddress.lower(), city.lower())
        # sql2 = "UPDATE {}_parcels SET community_name = '{}' WHERE lower(sit_city) = '{}' and lower(sit_full_s) LIKE '%{}%' and lower(sit_full_s) LIKE '{} %'".format(county, community.lower(), city.lower(), streetname.lower(), streetnumber.lower())
        # sql3 = "INSERT INTO {0}_zone30 SELECT 0, sit_full_s, sit_city, ST_BUFFER(ST_SetSRID(geom, 4326),.0000824) \
        # FROM {0}_bldgs_inter WHERE sit_city = '{1}' and sit_full_s = '{2}';".format(county, city, streetaddress)
        # sql4 = "INSERT INTO {0}_zone5 SELECT 0, sit_full_s, sit_city, ST_BUFFER(ST_SetSRID(geom, 4326),.0000137) \
        # FROM {0}_bldgs_inter WHERE lower(sit_city) = '{1}' and lower(sit_full_s) = '{2}';".format(county.lower(), city.lower(), streetaddress.lower())
        sql3 = "UPDATE {}_zone5 SET community = '{}' WHERE lower(sit_full_s) = '{}' and lower(sit_city) = '{}'".format(county, community.lower(), streetaddress.lower(), city.lower())
        sql4 = "UPDATE {}_zone30 SET community = '{}' WHERE lower(sit_full_s) = '{}' and lower(sit_city) = '{}'".format(county, community.lower(), streetaddress.lower(), city.lower())
        sql5 = "UPDATE {}_zone100 SET community = '{}' WHERE lower(sit_full_s) = '{}' and lower(sit_city) = '{}'".format(county, community.lower(), streetaddress.lower(), city.lower())
        print(sql1, sql2, sql3, sql4, sql5)
        #dbhelper.dbTransaction([sql1, sql2, sql3, sql4])
        dbhelper.dbTransaction([sql1, sql2, sql3, sql4, sql5])
        #dbhelper.dbExecute(sql1)
        #dbhelper.dbExecute(sql2)
        #citycommunities = ["Firesafe", "Firewall", "KeepUsSafe"]
        #member = role.lower() == "member" or role.lower() == "leader"
        #return render_template("home.html", address=address,city=city, state=results[2], username=username.upper(),xcoord=xcoord, ycoord=ycoord, \
        #                           community=results[3], role=role, county=county, members=communitymembersJSON, member=member, citycommunities=citycommunities)
        return redirect("/login")
    else:
        return render_template("register.html", message="")


@main_blueprint.route('/registerbiz', methods=['GET', 'POST'])
def registerbiz():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        streetname = request.form.get('streetname')
        streetnumber = request.form.get('streetnumber')
        streetsuffix = request.form.get('street_suffix')
        #streetaddress = request.form.get('sit_full_s')
        str_dir = request.form.get('str_dir')
        if str_dir == 'NONE':
            streetaddress = "{} {} {}".format(streetnumber,streetname,streetsuffix)
        else:
            streetaddress = "{} {} {} {}".format(streetnumber,str_dir,streetname,streetsuffix)
        city = request.form.get('cityselect')
        state = request.form.get('state')
        zip = request.form.get('zip')
        password = request.form.get('password')

        county = request.form.get('county')
        description = request.form.get('description')
        role = "business"
        #pdb.set_trace()
        sql = "SELECT * FROM {}_parcels WHERE lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), streetaddress.lower())
        results = dbhelper.dbFetchAll(sql)
        print(sql)

        if len(results) == 0:
            return render_template("registerbiz.html", message="Address entered does not match any known address")
        sql1 = "INSERT INTO users (name, username, email, address, city, state, zip, county, password, role, description)\
        VALUES ('{}', '{}', '{}', '{}', '{}','{}',  \
        '{}', '{}', '{}', '{}', '{}')".format(name, username, email, streetaddress, city, state, zip, county, password, role, description)

        dbhelper.dbExecute(sql1)
        return redirect("/login")
    else:
        return render_template("registerbiz.html", message="")


@main_blueprint.route('/business', methods=['GET','POST'])
def showbusinessform():
    return render_template("worksubmission.html", message="", county="")


@main_blueprint.route('/register/getcountycities/<string:county>', methods=['GET'])
def getcountycities(county):
    data = dbhelper.dbFetchAll("SELECT DISTINCT(SIT_CITY) FROM {}_parcels".format(county))
    #pdb.set_trace()
    return jsonify({'cities':[c[0] for c in data]})


# @app.route('/home')
# def showtest():
#     print(url_for("static",filename="images/rural.jpg"))
#     return render_template("home.html", bckimage=url_for("static",filename="images/Camp_Fire_oli_2018312_Landsat.jpg"))


@main_blueprint.route('/showstructures/<string:county>/<string:city>', methods=['POST'])
def showstructures(county, city):
    data = request.get_json()
    #pdb.set_trace()
    xcoord = data['xcoord']
    ycoord = data['ycoord']
    #radius = data['radius']  # TODO: add this in
    geodata = dbhelper.getStructures(county, city.upper(), xcoord, ycoord)
    return geodata


@main_blueprint.route('/showcity/<string:county>/<string:city>', methods=['POST'])
def showcity(county, city):
    data = request.get_json()
    #pdb.set_trace()
    xcoord = data['xcoord']
    ycoord = data['ycoord']
    #radius = data['radius'] # TODO: add this in
    geodata = dbhelper.getCityParcels(county, city.upper(), xcoord, ycoord)
    return geodata


@main_blueprint.route('/showdefensiblespace/<string:county>/<string:city>', methods=['POST'])
def showDefensibleSpace(county, city):
    data = request.get_json()
    #pdb.set_trace()
    xcoord = data['xcoord']
    ycoord = data['ycoord']
    #radius = data['radius'] # TODO: add this in
    geodata = dbhelper.getDefensibleSpace(county, city.upper(), xcoord, ycoord)
    #print("showDefensibleSpace",geodata)
    return geodata


@main_blueprint.route('/getlatlonfromaddress/<string:county>', methods=['POST'])
def getlatlonfromaddress(county):
    data = request.get_json()
    address = data['address']
    city = data['city']
    #pdb.set_trace()
    sql = "select XCOORD, YCOORD from {}_parcels WHERE lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county.lower(),city.lower(),address.lower())
    res = dbhelper.dbFetchOne(sql)
    zone5 = showMYzone5(county,city)
    zone30 = showMYzone30(county,city)
    zone100 = showMYzone100(county,city)
    sql = "SELECT sit_full_s, ST_AsGeoJSON(geom) as geometry  FROM {}_parcels WHERE \
    lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), address.lower())
    geodata = dbhelper.getData(sql)
    return jsonify({'longitude':float(res[0]), 'latitude':float(res[1]),'zone5':zone5,'zone30':zone30,'zone100':zone100, 'parcel':geodata})

@main_blueprint.route('/getparcelat/<string:county>', methods=['POST'])
def getparcelAt(county):
    data = request.get_json()
    xcoord = data['lng']
    ycoord = data['lat']
    city = data['city']

    #county = "placer"
    # sql1 = """WITH
    #        pt AS (
    #            SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
    #        )
    #     SELECT sit_full_s, sit_city, sit_state, sit_zip, xcoord, ycoord
    #     FROM {}_parcels, pt as b
    #     WHERE UPPER(sit_city) = '{}' and ST_Covers(geom, b.geog);""".format(xcoord,ycoord,county.lower(),city.upper())

    sqlalt = """
        SELECT sit_full_s, sit_city, sit_state, sit_zip, xcoord, ycoord
        FROM {}_parcels
        WHERE UPPER(SIT_CITY) = '{}' and maxx > {} and minx < {}
        and maxy > {} and miny < {};
        """.format(county.lower(),city.upper(),xcoord,xcoord,ycoord,ycoord)

    print(sqlalt)
    addressdata = dbhelper.dbFetchAll(sqlalt)
    if len(addressdata) > 0:
        dist = 9999999
        address = None
        for a in addressdata:
            ln = float(a[4])
            lg = float(a[5])
            d = math.sqrt((xcoord - ln)**2 + (ycoord - lg)**2)
            if dist > d:
                dist = d
                address = a
        if address:
            addressdata = list(address[0:4]) + [float(address[4]),float(address[5])]
    return jsonify({'address':addressdata})


@main_blueprint.route('/showneighborhood/<string:county>/<string:city>', methods=['POST'])
def showneighborhood(county, city):
    data = request.get_json()
    xcoord = data['xcoord']
    ycoord = data['ycoord']
    distance = 1609*float(data['distance'])
    sql = """
        WITH
           pt AS (
               SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
           )
        SELECT ST_AsGeoJSON(geom) as geometry
        FROM {}_parcels, pt as b
        WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(ST_SetSRID(geom,4326), b.geog, {});""".format(xcoord, ycoord, county, city.upper(), distance)
    print(sql)
    geodata = dbhelper.getData(sql)
    return geodata


@main_blueprint.route('/getlocalfireshistory/<string:county>', methods=['POST'])
def getMyLocalFireHistory(county):
    data = request.get_json()
    xcoord = data['xcoord']
    ycoord = data['ycoord']

    distance = 1609*float(data['distance'])
    sql = """
        WITH
           pt AS (
               SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
           )
        SELECT ST_AsGeoJSON(ST_Transform (st_setsrid(geom,3310), 4326)) as geometry
        FROM {}firehistory, pt as b
        WHERE ST_DWithin(geom, b.geog, {});""".format(xcoord, ycoord, county, distance)
    geodata = dbhelper.getData(sql)
    return geodata


@main_blueprint.route('/countyfirehistory/<string:county>', methods=['GET','POST'])
def getCountyFireHistory(county):
    data = request.get_json()
    sql = """
        SELECT fire_name, year_, gis_acres, alarm_date, cont_date, cause, ST_AsGeoJSON(ST_Transform (st_setsrid(geom,3310), 4326)) as geometry
        FROM {}firehistory ORDER BY gis_acres DESC;""".format(county)
    print(sql)
    geodata = dbhelper.getData(sql)
    return geodata

@main_blueprint.route('/countyfirethreat/<string:county>', methods=['GET','POST'])
def countyfirethreat(county):
    sql = """
        SELECT haz_code, haz_class, ST_AsGeoJSON(ST_Transform (st_setsrid(geom,3310), 4326)) as geometry
        FROM {}_firethreat ;""".format(county)
    geodata = dbhelper.getData(sql)
    return geodata

@main_blueprint.route('/getmaillistsendfile/<string:county>/<string:city>', methods=['POST'])
def getMaillistSendFile(county, city):
    xcoord = float(request.form.get('xcoord'))
    ycoord = float(request.form.get('ycoord'))
    distance = 1609*float(float(request.form.get('distance')))
    sql = """
        WITH
           pt AS (
               SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
           )
        SELECT SIT_FULL_S, SIT_CITY, STATE, SIT_ZIP4
        FROM {}_parcels, pt as b
        WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(ST_SetSRID(geom,4326), b.geog, {});""".format(xcoord, ycoord, county, city.upper(), distance)
    results = dbhelper.dbFetchAll(sql)
    print(results)
    rootpath = os.getcwd()
    try:
        if not os.path.exists(os.path.join(rootpath, "temp")):
            os.makedirs(os.path.join(rootpath, "temp"))
        filepath = os.path.join(rootpath, "temp", "maillist.csv")
        with open(filepath,'w') as fw:
            for row in results:
                try:
                    fw.write(",".join(row) + "\n")
                except:
                    pass
            fw.close()
    except Exception as e:
        logging.error(str(e))
        return redirect('/login')

    return send_from_directory(os.path.join(rootpath, "temp"), "maillist.csv")


@main_blueprint.route('/getmaillist/<string:county>/<string:city>', methods=['POST'])
def getMaillist(county, city):
    xcoord = float(request.form.get('xcoord'))
    ycoord = float(request.form.get('ycoord'))
    distance = 1609*float(float(request.form.get('distance')))
    community = request.form.get('community')  # usee exclude existing members of users community
    city = request.form.get('city')
    # if community == '':
    sql = """
        WITH
           pt AS (
               SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
           )
        SELECT SIT_FULL_S, SIT_CITY, STATE, SIT_ZIP
        FROM {}_parcels, pt as b
        WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(ST_SetSRID(geom,4326), b.geog, {}) ORDER BY SIT_FULL_S;""".format(xcoord, ycoord, county, city.upper(), distance)
    # else:
    #     sql = """
    #         WITH
    #            pt AS (
    #                SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
    #            )
    #         SELECT SIT_FULL_S, SIT_CITY, STATE, SIT_ZIP
    #         FROM {}_parcels, pt as b
    #         WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(geom, b.geog, {}) and LOWER(community) != '{}' ORDER BY SIT_FULL_S;""".format(xcoord, ycoord, county, city.upper(), distance, community.lower())
    results = dbhelper.dbFetchAll(sql)
    print(results)
    rootpath = os.getcwd()
    resultarray = []
    for row in results:
        try:
            rowtext = ",".join(row)
            resultarray.append(rowtext)
        except:
            print("bad record")
    resulttext = "\n".join(resultarray)
    #return send_from_directory(os.path.join(rootpath, "temp","maillist.csv"))
    return render_template("maillist.html",resulttext=resulttext)


@main_blueprint.route('/getmaillist2/<string:county>/<string:city>', methods=['POST'])
def getMaillist2(county, city):
    data = request.get_json()
    xcoord = float(data['xcoord'])
    ycoord = float(data['ycoord'])
    distance = 1609*float(float(data['distance']))
    #pdb.set_trace()
    community = data['community']  # usee exclude existing members of users community
    city = data['city']
    # if community == '':
    sql = """
        WITH
           pt AS (
               SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
           )
        SELECT SIT_FULL_S, SIT_CITY, STATE, SIT_ZIP
        FROM {}_parcels, pt as b
        WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(ST_SetSRID(geom,4326), b.geog, {}) ORDER BY SIT_FULL_S;""".format(xcoord, ycoord, county, city.upper(), distance)
    # else:
    #     sql = """
    #         WITH
    #            pt AS (
    #                SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
    #            )
    #         SELECT SIT_FULL_S, SIT_CITY, STATE, SIT_ZIP
    #         FROM {}_parcels, pt as b
    #         WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(geom, b.geog, {}) and LOWER(community) != '{}' ORDER BY SIT_FULL_S;""".format(xcoord, ycoord, county, city.upper(), distance, community.lower())
    results = dbhelper.dbFetchAll(sql)
    return jsonify({"maillist":results})


@main_blueprint.route('/showmyparcel/<string:county>/<string:city>', methods=['POST'])
def showMYParcel(county, city):
    data = request.get_json()
    address = data['address']
    sql = "SELECT sit_full_s, ST_AsGeoJSON(geom) as geometry  FROM {}_parcels WHERE \
    lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), address.lower())
    geodata = dbhelper.getData(sql)
    return geodata




@main_blueprint.route('/changeprofile/<string:user>', methods=['POST'])
def changeprofile(user):
    role = request.form.get('role')
    community = request.form.get('community')
    if role == "business":
        bizname = request.form.get('bizname')
        description = request.form.get('description')
        sql = "UPDATE users SET role = '{}', community = '{}', bizname = '{}' WHERE username = '{}'".format(role, community, user, bizname)
    else:
        sql = "UPDATE users SET role = '{}', community = '{}' WHERE username = '{}'".format(role, community, user)
    #changeavatar = request.form.get('changeavatar')
    #pdb.set_trace()

    # if changeavatar == 'on' and 'file' in request.files:
    #     file = request.files['file']
    #     if file.filename == '':
    #         return redirect(request.url)
    #     if not os.path.exists('./templates/public/images/users/{}'.format(user)):
    #         os.makedirs('./templates/public/images/users/{}'.format(user))
    #     if file and allowed_file(file.filename):
    #         filename = secure_filename(file.filename)
    #         #file.save(os.path.join("./templates/public/images/users",user, filename))
    #         sql = "UPDATE users SET role = '{}', community = '{}', avatar = '{}' WHERE username = '{}'".format(role,community, filename, user)
    dbhelper.dbExecute(sql)
    return redirect("/login")



@main_blueprint.route('/changeprofile/<string:role>/<string:community>/<string:user>', methods=['GET'])
def changeprofilegett(role,community,user):
    return render_template("userprofile.html", role=role, community=community, user=user)


@main_blueprint.route('/showmystructures/<string:county>/<string:city>', methods=['POST'])
def showMYStructures(county, city):
    data = request.get_json()
    address = data['address']
    sql = "SELECT ST_AsGeoJSON(geom) as geometry  FROM {}_bldgs_inter WHERE \
    lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), address.lower())
    geodata = dbhelper.getData(sql)
    return geodata

@main_blueprint.route('/showzone100/<string:county>/<string:city>', methods=['POST'])
def showMYzone100(county, city):
    data = request.get_json()
    address = data['address']
    #sql = "SELECT status, ST_AsGeoJSON(geom) as geometry  FROM {0}_zone100 WHERE lower(sit_city) = '{1}' \
    #and ST_CONTAINS(geom, (SELECT geom FROM {0}_bldgs_inter WHERE lower(SIT_CITY) = '{1}' and lower(SIT_FULL_S) = '{2}' LIMIT 1))".format(county, city.lower(), address.lower())
    print('county',county)
    if county.lower() == 'marin':
        sql = "SELECT status, ST_AsGeoJSON(ST_Transform( ST_SetSRID(geom, 3494 ), 4326)) as geometry  FROM {}_zone100 WHERE \
        lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), address.lower())
    else:
        sql = "SELECT status, ST_AsGeoJSON(geom) as geometry  FROM {}_zone100 WHERE \
        lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), address.lower())
    geodata = dbhelper.getData(sql)
    #pdb.set_trace()
    return geodata

@main_blueprint.route('/showzone30/<string:county>/<string:city>', methods=['POST'])
def showMYzone30(county, city):
    data = request.get_json()
    address = data['address']
    print('county',county)
    if county.lower() == 'marin':
        sql = "SELECT status, ST_AsGeoJSON(ST_Transform( ST_SetSRID(geom, 3494 ), 4326)) as geometry  FROM {}_zone30 WHERE lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), address.lower())
    else:
        sql = "SELECT status, ST_AsGeoJSON(geom) as geometry  FROM {}_zone30 WHERE lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), address.lower())
    geodata = dbhelper.getData(sql)
    return geodata


@main_blueprint.route('/showzone5/<string:county>/<string:city>', methods=['POST'])
def showMYzone5(county, city):
    data = request.get_json()
    address = data['address']
    if county.lower() == 'marin':
        sql = "SELECT status, ST_AsGeoJSON(ST_Transform( ST_SetSRID(geom, 3494 ), 4326)) as geometry FROM {}_zone5 WHERE \
        lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), address.lower())
    else:
        sql = "SELECT status, ST_AsGeoJSON(geom) as geometry FROM {}_zone5 WHERE \
        lower(sit_city) = '{}' and lower(sit_full_s) = '{}'".format(county, city.lower(), address.lower())
    geodata = dbhelper.getData(sql)
    return geodata


@main_blueprint.route('/getfirewisecommunity/<string:county>/<string:city>/<string:mdscommunity>', methods=['GET'])
def getMDSCommunity(county, city, mdscommunity):
    print("called getfirewisecommunity")
    try:
        data = dbhelper.getMDSCommunity(county, city, mdscommunity)  # uses mdscommunity without sit_full_s
    except Exception as e:
        data = {}
        logging.info('Error '+str(e))
    return jsonify(data)

@main_blueprint.route('/communityparcels/<string:county>', methods=['POST'])
def getCommunityParcels(county):
    data = request.get_json()
    community = data['community']
    sql = f"SELECT sit_full_s, sit_city, ST_AsGeoJSON(geom) as geometry FROM {county}_parcels WHERE community = '{community}';"
    res = dbhelper.getData(sql)
    return jsonify(res)


# def getfirewisecommunity2(county, city, firewise): # for command line testing only
#     print("called getfirewisecommunity")
#     try:
#         data = dbhelper.getFirewiseCommunity(county, city.upper(), firewise)
#     except Exception as e:
#         logging.info('Error '+str(e))
#     return data


@main_blueprint.route('/getlocaladdresses/<string:county>/<string:city>', methods=['POST'])
def getlocaladdresses(county, city):
    data = request.get_json()
    xcoord = data['xcoord']
    ycoord = data['ycoord']
    localaddresses = dbhelper.getLocalAddressesNearby(county, city.upper(), xcoord, ycoord)
    return jsonify(localaddresses)


@main_blueprint.route('/myspaceupdate/<string:county>/<string:city>', methods=['POST'])
def myspaceupdate(county, city):
    data = request.get_json()
    z0 = data['z0']
    z1 = data['z1']
    z2 = data['z2']

    # TODO Add following four values to some new table
    landscapeservices = data['landscapeservice']
    landscapeused = data['landscapeused']
    #if landscapeused:
    satisfaction = data['satisfaction']
    #else:
        #satisfaction = -1
    address = data['address']
    expenditures = data['expenditures']
    comments = data['comments']
    datestr = str(date.today())

    sq10 = "UPDATE {}_zone5 SET status='{}' WHERE UPPER(SIT_CITY) = '{}' and UPPER(SIT_FULL_S) = '{}'".format(county, z0, city.upper(), address.upper())
    sq11 = "UPDATE {}_zone30 SET status='{}' WHERE UPPER(SIT_CITY) = '{}' and UPPER(SIT_FULL_S) = '{}'".format(county, z1, city.upper(), address.upper())
    sq12 = "UPDATE {}_zone100 SET status='{}' WHERE UPPER(SIT_CITY) = '{}' and UPPER(SIT_FULL_S) = '{}'".format(county, z2, city.upper(), address.upper())
    sql3 = "INSERT INTO memberlog (address, city, zone5, zone30, zone100,landscapeservice,expenditures,comments, date, satisfaction) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(address,city,z0,z1,z2,landscapeservices,expenditures,comments, datestr, satisfaction)
    #sql3 = "INSERT INTO memberlog (address, city, zone5, zone30, zone100,landscapeservice,expenditures,comments, date, satisfaction) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(address,city,z0,z1,z2,landscapeservices,expenditures,comments, datestr, satisfaction)

    dbhelper.dbTransaction([sq10, sq11, sq12, sql3])

    return jsonify({'success':True})
