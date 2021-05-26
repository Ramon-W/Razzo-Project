from flask import Flask, redirect, Markup, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from flask import render_template
from bson.objectid import ObjectId
from mongosanitizer.sanitizer import sanitize

import pprint
import os
import sys
import pymongo
from datetime import datetime, timedelta
from pytz import timezone
import pytz

app = Flask(__name__)

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

admin1='Azuthedog1'
admin2='DanaLearnsToCode'
admin3='MyDSWAccount'
admin4='Korkz'
admin5='Ponmo'
admin6='piemusician'
admin7='Ramon-W'

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], 
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],
    request_token_params={'scope': 'user:email'}, 
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' 
)
   
@app.context_processor
def inject_logged_in():
    return {'logged_in':('github_token' in session)}

@app.route('/')
def render_information():
    return render_template('information.html')

@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            if session['user_data']['login'] == admin1 or session['user_data']['login'] == admin2 or session['user_data']['login'] == admin3 or session['user_data']['login'] == admin4 or session['user_data']['login'] == admin5 or session['user_data']['login'] == admin6 or session['user_data']['login'] == admin7:
                message='You were successfully logged in as ' + session['user_data']['login'] + '. Don\'t forget to log out before exiting this wbesite.'
            else:
                session.clear()
                message='Please sign in with a valid admin account. You attempted to log in as ' + session['user_data']['login'] + '. This is not an admin account. To log in as an admin you may need to log out of Github before attempting to log in again.'
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.'
    session['username'] = 'admin'
    return render_template('login.html', message = message)

@app.route('/englishlearnerforum')
def render_english_learner_forum():
    connection_string = os.environ['MONGO_CONNECTION_STRING']
    db_name = os.environ['MONGO_DBNAME']
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['ELLU']
    postList = []
    bigString1 = ''
    bigString2 = ''
    if 'github_token' in session:
        for post in collection.find():
            bigString1 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewELLU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail') + '</i></td>')
            if(post.get('approved') == 'false'):
                bigString1 += '<td class="col4"><form action="/vetELL" method="post" class="inLine"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet</button></form> '
            else:
                bigString1 += '<td class="col4"><form action="/unvetELL" method="post" class="inLine"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span>Unvet</button></form> '
            bigString1 += '<button type="button" class="btn btn-danger btn-sm"><span class="glyphicon glyphicon-trash delete"></span>Delete</button><button type="button" class="btn btn-danger btn-sm cancel">Cancel</button> <form action="/deleteELL" method="post" class="inLine"><button type="submit" class="btn btn-danger btn-sm confirm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>'
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString1 += '<br><i>' + loc_dt + '</i></td></tr>'
            postList.insert(0, bigString1)
            bigString1 = ''
    else:
        for post in collection.find():
            if(post.get('approved') == 'true'):
                bigString1 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                               '<td class="col2"><form action="/viewELLU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>')
                if(post.get('anonymous') == 'true'):
                    bigString1 += '<td class="col3"><i>Anonymous Post</i></td>'
                else:
                    bigString1 += '<td class="col3"><i>' + post.get('parentName') + '</i></td>'
                utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                bigString1 += '<td class="col4"><i>' + loc_dt + '</i></td></tr>'
                postList.insert(0, bigString1)
                bigString1 = ''
    for item in postList:
        bigString1 += item
    postList.clear()
    collection = db['ELLA']
    if 'github_token' in session: 
        for post in collection.find():
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString2 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewELLA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col4"><form action="/deleteELL" method="post" class="inLine"><button type="submit" class="btn btn-danger btn-sm lineUp" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form><br><i>' + loc_dt + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ''
    else:
        for post in collection.find():
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString2 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewELLA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col4"><i>' + loc_dt + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ''
    for item in postList:
        bigString2 += item
    return render_template('englishlearnerforum.html', ELLUPosts = Markup(bigString1), ELLAPosts = Markup(bigString2))

@app.route('/specialeducationforum')
def render_special_education_forum():
    connection_string = os.environ['MONGO_CONNECTION_STRING']
    db_name = os.environ['MONGO_DBNAME']
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['SEU']
    postList = []
    bigString1 = ''
    bigString2 = ''
    if 'github_token' in session:
        for post in collection.find():
            bigString1 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewSEU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail') + '</i></td>')
            if(post.get('approved') == 'false'):
                bigString1 += '<td class="col4"><form action="/vetSE" method="post" class="inLine"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet</button></form> '
            else:
                bigString1 += '<td class="col4"><form action="/unvetSE" method="post" class="inLine"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span>Unvet</button></form> '
            bigString1 += '<form action="/deleteSE" method="post" class="inLine"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>'
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString1 += '</button></form><br><i>' + loc_dt + '</i></td></tr>'
            postList.insert(0, bigString1)
            bigString1 = ''
    else:
        for post in collection.find():
            if(post.get('approved') == 'true'):
                bigString1 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                               '<td class="col2"><form action="/viewSEU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>')
                if(post.get('anonymous') == 'true'):
                    bigString1 += '<td class="col3"><i>Anonymous Post</i></td>'
                else:
                    bigString1 += '<td class="col3"><i>' + post.get('parentName') + '</i></td>'
                utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                bigString1 += '<td class="col4"><i>' + loc_dt + '</i></td></tr>'
                postList.insert(0, bigString1)
                bigString1 = ''
    for item in postList:
        bigString1 += item
    postList.clear()
    collection = db['SEA']
    if 'github_token' in session: 
        for post in collection.find():
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString2 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewSEA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col4"><form action="/deleteSE" method="post" class="inLine"><button type="submit" class="btn btn-danger btn-sm lineUp" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form><br><i>' + loc_dt + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ''
    else:
        for post in collection.find():
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString2 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewSEA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col4"><i>' + loc_dt + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ''
    for item in postList:
        bigString2 += item
    return render_template('specialeducationforum.html', SEUPosts = Markup(bigString1), SEAPosts = Markup(bigString2))

@app.route('/adminLog')
def render_admin_log():
    connection_string = os.environ['MONGO_CONNECTION_STRING']
    db_name = os.environ['MONGO_DBNAME']
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['LOG']
    cursor = collection.find({})
    bigString = ''
    logList = []
    for item in cursor:
        utc_dt = datetime(int(item.get('dateTime').strftime("%Y")), int(item.get('dateTime').strftime("%m")), int(item.get('dateTime').strftime("%d")), int(item.get('dateTime').strftime("%H")), int(item.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
        loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
        if int(loc_dt.strftime("%H")) > 12:
            hour = str(int(loc_dt.strftime("%H")) - 12)
            loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
        else:
            hour = str(int(loc_dt.strftime("%H")))
            loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M AM PT")
        bigString += '<tr><td class="logContent"><span class="timeColor">' + loc_dt + '</span>: ' + item.get('action') + '<br></td></tr>'
        logList.insert(0, bigString)
        bigString = ''
    for item in logList:
        bigString += item
    return render_template('adminlog.html', log = Markup(bigString))

def add_admin_log(dateTime, action):
    connection_string = os.environ['MONGO_CONNECTION_STRING']
    db_name = os.environ['MONGO_DBNAME']
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['LOG']
    collection.insert_one({'dateTime': dateTime, 'action': action})

@app.route('/userSubmitPostELL', methods=['GET','POST'])
def user_submit_post_ELL():
    if request.method == 'POST':
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLU']
        content = request.form['userMessage']
        content = content.replace('\\"', '')
        content = Markup(content[1:len(content)-1])
        sanitize(content)
        if request.form['userEmail'] == '':
            email = 'Email not provided'
        else:
            email = request.form['userEmail']
        post = {'postTitle': request.form['userTitle'], 'parentName': request.form['userName'], 'studentNameGrade': request.form['userStudent'], 'parentEmail': email, 'anonymous': request.form['anon'], 'dateTime': datetime.now(), 'postContent': content, 'approved': 'false'}
        collection.insert_one(post)
        post = collection.find_one({'postTitle': request.form['userTitle'], 'parentName': request.form['userName'], 'studentNameGrade': request.form['userStudent'], 'parentEmail': email, 'anonymous': request.form['anon'], 'postContent': content})
        action = request.form['userName'] + '<span class="createColor"> posted </span><b><a href="https://razzoforumproject.herokuapp.com/viewELLU?thread=' + str(post.get('_id')) + '">' + request.form['userTitle'] + '</a></b> in english language learner forum'
        add_admin_log(datetime.now(), action)
    return render_english_learner_forum()

@app.route('/adminSubmitPostELL', methods=['GET', 'POST']) #Same as above, except no name, student name and grade, no anonymous, etc.
def admin_submit_post_ELL():
    if request.method == 'POST':
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLA']
        content = request.form['adminMessage']
        content = content.replace('\\"', '')
        content = Markup(content[1:len(content)-1])
        sanitize(content)
        post = {'postTitle': request.form['adminTitle'], 'adminName': request.form['adminName'], 'dateTime': datetime.now(), 'postContent': content}#put all info here using variables
        collection.insert_one(post)
        post = collection.find_one({'postTitle': request.form['adminTitle'], 'adminName': request.form['adminName'], 'postContent': content})
        action = request.form['adminName'] + '<span class="createColor"> posted </span><b><a href="https://razzoforumproject.herokuapp.com/viewELLA?thread=' + str(post.get('_id')) + '">' + request.form['adminTitle'] + '</a></b> in english language learner forum'
        add_admin_log(datetime.now(), action)
    return render_english_learner_forum() #this will also copy the code from def render_english_learner_forum from above.
    
@app.route('/userSubmitPostSE', methods=['GET', 'POST'])
def user_submit_post_SE():
    if request.method == 'POST':
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEU']
        content = request.form['userMessage']
        content = content.replace('\\"', '')
        content = Markup(content[1:len(content)-1])
        sanitize(content)
        if request.form['userEmail'] == '':
            email = 'Email not provided'
        else:
            email = request.form['userEmail']
        post = {'postTitle': request.form['userTitle'], 'parentName': request.form['userName'], 'studentNameGrade': request.form['userStudent'], 'parentEmail': email, 'anonymous': request.form['anon'], 'dateTime': datetime.now(), 'postContent': content, 'approved': 'false'}
        post = collection.insert_one(post)
        post = collection.find_one({'postTitle': request.form['userTitle'], 'parentName': request.form['userName'], 'studentNameGrade': request.form['userStudent'], 'parentEmail': email, 'anonymous': request.form['anon'], 'postContent': content})
        action = request.form['userName'] + '<span class="createColor"> posted </span><b><a href="https://razzoforumproject.herokuapp.com/viewSEU?thread=' + str(post.get('_id')) + '">' + request.form['userTitle'] + '</a></b> in special education forum'
        add_admin_log(datetime.now(), action)
    return render_special_education_forum()

@app.route('/adminSubmitPostSE', methods=['GET', 'POST'])
def admin_submit_post_SE():
    if request.method == 'POST':
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEA']
        content = request.form['adminMessage']
        content = content.replace('\\"', '')
        content = Markup(content[1:len(content)-1])
        sanitize(content)
        post = {'postTitle': request.form['adminTitle'], 'adminName': request.form['adminName'], 'dateTime': datetime.now(), 'postContent': content}#put all info here using variables
        post = collection.insert_one(post)
        post = collection.find_one({'postTitle': request.form['adminTitle'], 'adminName': request.form['adminName'], 'postContent': content})
        action = request.form['adminName'] + '<span class="createColor"> posted </span><b><a href="https://razzoforumproject.herokuapp.com/viewSEA?thread=' + str(post.get('_id')) + '">' + request.form['adminTitle'] + '</a></b> in special education forum'
        add_admin_log(datetime.now(), action)
    return render_special_education_forum()

@app.route('/submitComment', methods=['GET', 'POST'])
def submit_comment():
    if request.method == 'POST':
        objectIDPost = request.form['ID']
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEA']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        keyList = list(post.keys())
        if 'comment' in keyList[-1]:
            lastNumber = keyList[-1]
            lastNumber = lastNumber.replace('comment', '')
            lastNumber = str(int(lastNumber) + 1)
        else:
            lastNumber = '0'
        if 'github_token' in session:
            content = request.form['adminMessage']
            content = content.replace('\\"', '')
            content = Markup(content[1:len(content)-1])
            sanitize(content)
            post['comment' + lastNumber] = {'adminName': request.form['adminName'], 'dateTime': datetime.now(), 'postContent': content}
            collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
        else:
            content = request.form['userMessage']
            content = content.replace('\\"', '')
            content = Markup(content[1:len(content)-1])
            sanitize(content)
            post['comment' + lastNumber] = {'parentName': request.form['userName'], 'studentNameGrade': request.form['userStudent'], 'anonymous': request.form['anon'], 'dateTime': datetime.now(), 'postContent': content, 'approved': 'false'}
            collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
    if collection == db['SEA']:
        if 'github_token' in session:
            action = request.form['adminName'] + '<span class="createColor"> commented </span>on <b><a href="https://razzoforumproject.herokuapp.com/viewSEA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
            add_admin_log(datetime.now(), action)
        else:
            action = request.form['userName'] + '<span class="createColor"> commented </span>on <b><a href="https://razzoforumproject.herokuapp.com/viewSEA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
            add_admin_log(datetime.now(), action)
        return view_SEA(objectIDPost)
    elif collection == db['SEU']:
        if 'github_token' in session:
            action = request.form['adminName'] + '<span class="createColor"> commented </span>on <b><a href="https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
            add_admin_log(datetime.now(), action)
        else:
            action = request.form['userName'] + '<span class="createColor"> commented </span>on <b><a href="https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
            add_admin_log(datetime.now(), action)
        return view_SEU(objectIDPost)
    elif collection == db['ELLA']:
        if 'github_token' in session:
            action = request.form['adminName'] + '<span class="createColor"> commented </span>on <b><a href="https://razzoforumproject.herokuapp.com/viewELLA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
            add_admin_log(datetime.now(), action)
        else:
            action = request.form['userName'] + '<span class="createColor"> commented </span>on <b><a href="https://razzoforumproject.herokuapp.com/viewELLA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
            add_admin_log(datetime.now(), action)
        return view_ELLA(objectIDPost)
    elif collection == db['ELLU']:
        if 'github_token' in session:
            action = request.form['adminName'] + '<span class="createColor"> commented </span>on <b><a href="https://razzoforumproject.herokuapp.com/viewELLU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
            add_admin_log(datetime.now(), action)
        else:
            action = request.form['userName'] + '<span class="createColor"> commented </span>on <b><a href="https://razzoforumproject.herokuapp.com/viewELLU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
            add_admin_log(datetime.now(), action)
        return view_ELLU(objectIDPost)
    return render_template('information.html')

@app.route('/deleteComment', methods=['GET', 'POST'])
def delete_comment():
    if request.method == 'POST':
        objectIDPost = request.form['delete']
        comment = request.form['comment']
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]       
        collection = db['SEU']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if collection == db['SEA']:
            if post.get(comment, {}).get('adminName') != None:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('adminName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewSEA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum<br>' + post.get(comment, {}).get('postContent')
                post.pop(comment, None)
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
                add_admin_log(datetime.now(), action)
            else:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('parentName') + ' / ' + post.get(comment, {}).get('studentNameGrade') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewSEA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum<br>' + post.get(comment, {}).get('postContent')
                post.pop(comment, None)
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
                add_admin_log(datetime.now(), action)
            return view_SEA(objectIDPost)
        elif collection == db['SEU']:
            if post.get(comment, {}).get('adminName') != None:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('adminName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum<br>' + post.get(comment, {}).get('postContent')
                post.pop(comment, None)
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
                add_admin_log(datetime.now(), action)
            else:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('parentName') + ' / ' + post.get(comment, {}).get('studentNameGrade') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum<br>' + post.get(comment, {}).get('postContent')
                post.pop(comment, None)
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
                add_admin_log(datetime.now(), action)
            return view_SEU(objectIDPost)
        elif collection == db['ELLA']:
            if post.get(comment, {}).get('adminName') != None:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('adminName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewELLA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum<br>' + post.get(comment, {}).get('postContent')
                post.pop(comment, None)
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
                add_admin_log(datetime.now(), action)
            else:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('parentName') + ' / ' + post.get(comment, {}).get('studentNameGrade') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewELLA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum<br>' + post.get(comment, {}).get('postContent')
                post.pop(comment, None)
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
                add_admin_log(datetime.now(), action)
            return view_ELLA(objectIDPost)
        elif collection == db['ELLU']:
            if post.get(comment, {}).get('adminName') != None:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('adminName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewELLU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum<br>' + post.get(comment, {}).get('postContent')
                post.pop(comment, None)
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
                add_admin_log(datetime.now(), action)
            else:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('parentName') + ' / ' + post.get(comment, {}).get('studentNameGrade') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewELLU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum<br>' + post.get(comment, {}).get('postContent')
                post.pop(comment, None)
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
                add_admin_log(datetime.now(), action)
            return view_ELLU(objectIDPost)
    return render_template('information.html')

@app.route('/vetComment', methods=['GET', 'POST'])
def vet_comment():
    if request.method == 'POST':
        objectIDPost = request.form['vet']
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEU']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        post[request.form['comment']]['approved'] = 'true'
        collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
        if collection == db['SEA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewSEA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
            add_admin_log(datetime.now(), action)
            return view_SEA(objectIDPost)
        elif collection == db['SEU']:
            action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
            add_admin_log(datetime.now(), action)
            return view_SEU(objectIDPost)
        elif collection == db['ELLA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewELLA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
            add_admin_log(datetime.now(), action)
            return view_ELLA(objectIDPost)
        elif collection == db['ELLU']:
            action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewELLU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
            add_admin_log(datetime.now(), action)
            return view_ELLU(objectIDPost)
    return render_template('information.html')
        
    
@app.route('/unvetComment', methods=['GET', 'POST'])
def unvet_comment():
    if request.method == 'POST':
        objectIDPost = request.form['vet']
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEU']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        post[request.form['comment']]['approved'] = 'false'
        collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
        if collection == db['SEA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewSEA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
            add_admin_log(datetime.now(), action)
            return view_SEA(objectIDPost)
        elif collection == db['SEU']:
            action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
            add_admin_log(datetime.now(), action)
            return view_SEU(objectIDPost)
        elif collection == db['ELLA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewELLA?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
            add_admin_log(datetime.now(), action)
            return view_ELLA(objectIDPost)
        elif collection == db['ELLU']:
            action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <b><a href="https://razzoforumproject.herokuapp.com/viewELLU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
            add_admin_log(datetime.now(), action)
            return view_ELLU(objectIDPost)
    return render_template('information.html')

@app.route('/viewSEA')
def reroute_view_SEA():
    objectIDPost = request.args['thread']
    return view_SEA(objectIDPost)

@app.route('/viewSEU')
def reroute_view_SEU():
    objectIDPost = request.args['thread']
    return view_SEU(objectIDPost)

@app.route('/viewELLA')
def reroute_view_ELLA():
    objectIDPost = request.args['thread']
    return view_ELLA(objectIDPost)

@app.route('/viewELLU')
def reroute_view_ELLU():
    objectIDPost = request.args['thread']
    return view_ELLU(objectIDPost)

def view_SEA(objectIDPost):
    connection_string = os.environ['MONGO_CONNECTION_STRING']
    db_name = os.environ['MONGO_DBNAME']
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['SEA']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime('%H')) > 12:
        hour = str(int(loc_dt.strftime('%H')) - 12)
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
    else:
        hour = str(int(loc_dt.strftime('%H')))
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
    displayName = post.get('adminName')
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session:
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b> / ' + post.get('comment' + str(i), {}).get('studentNameGrade') + '<br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                if post.get('comment' + str(i), {}).get('adminName') == None:
                    bigString += '<div class="rightAlign">'
                    if(post.get('comment' + str(i), {}).get('approved') == 'false'):
                        bigString += '<form action="/vetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet</button></form> '
                    else:
                        bigString += '<form action="/unvetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span>Unvet</button></form> '
                bigString += '<form action="/deleteComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>'
                bigString += '</div></td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                else:
                    if post.get('comment' + str(i), {}).get('approved') == 'true':
                        if post.get('comment' + str(i), {}).get('anonymous') == 'true':
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = displayName, information = '', time = loc_dt, content = Markup(postContent), _id = objectIDPost, comments = Markup(bigString))

def view_SEU(objectIDPost):
    connection_string = os.environ['MONGO_CONNECTION_STRING']
    db_name = os.environ['MONGO_DBNAME']
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['SEU']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime('%H')) > 12:
        hour = str(int(loc_dt.strftime('%H')) - 12)
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
    else:
        hour = str(int(loc_dt.strftime('%H')))
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
    if 'github_token' in session:
        parentName = post.get('parentName')
        studentNameGrade = post.get('studentNameGrade')
        parentEmail = post.get('parentEmail')
        if parentEmail == '':
            parentEmail = 'Email not provided'
    else:
        if post.get('anonymous') == 'false':
            parentName = post.get('parentName')
        else:
            parentName = 'Anonymous Post'
        studentNameGrade = ''
        parentEmail = ''
    info = ' / ' + studentNameGrade + ' / ' + parentEmail
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b> / ' + post.get('comment' + str(i), {}).get('studentNameGrade') + '<br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                if post.get('comment' + str(i), {}).get('adminName') == None:
                    bigString += '<div class="rightAlign">'
                    if(post.get('comment' + str(i), {}).get('approved') == 'false'):
                        bigString += '<form action="/vetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet</button></form> '
                    else:
                        bigString += '<form action="/unvetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span>Unvet</button></form> '
                bigString += '<form action="/deleteComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>'
                bigString += '</div></td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                else:
                    if post.get('comment' + str(i), {}).get('approved') == 'true':
                        if post.get('comment' + str(i), {}).get('anonymous') == 'true':
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = loc_dt, content = Markup(postContent), _id = objectIDPost, comments = Markup(bigString))

def view_ELLA(objectIDPost):
    connection_string = os.environ['MONGO_CONNECTION_STRING']
    db_name = os.environ['MONGO_DBNAME']
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['ELLA']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime('%H')) > 12:
        hour = str(int(loc_dt.strftime('%H')) - 12)
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
    else:
        hour = str(int(loc_dt.strftime('%H')))
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
    displayName = post.get('adminName')
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b> / ' + post.get('comment' + str(i), {}).get('studentNameGrade') + '<br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                if post.get('comment' + str(i), {}).get('adminName') == None:
                    if(post.get('comment' + str(i), {}).get('approved') == 'false'):
                        bigString += '<form action="/vetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet</button></form> '
                    else:
                        bigString += '<form action="/unvetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span>Unvet</button></form> '
                bigString += '<form action="/deleteComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>'
                bigString += '</td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                else:
                    if post.get('comment' + str(i), {}).get('approved') == 'true':
                        if post.get('comment' + str(i), {}).get('anonymous') == 'true':
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = displayName, information = '', time = loc_dt, content = Markup(postContent), _id = objectIDPost, comments = Markup(bigString))

def view_ELLU(objectIDPost):
    connection_string = os.environ['MONGO_CONNECTION_STRING']
    db_name = os.environ['MONGO_DBNAME']
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['ELLU']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime('%H')) > 12:
        hour = str(int(loc_dt.strftime('%H')) - 12)
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
    else:
        hour = str(int(loc_dt.strftime('%H')))
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
    if 'github_token' in session:
        parentName = post.get('parentName')
        studentNameGrade = post.get('studentNameGrade')
        parentEmail = post.get('parentEmail')
        if parentEmail == '':
            parentEmail = 'Email not provided'
    else:
        if post.get('anonymous') == 'false':
            parentName = post.get('parentName')
        else:
            parentName = 'Anonymous Post'
        studentNameGrade = ''
        parentEmail = ''
    info = ' / ' + studentNameGrade + ' / ' + parentEmail
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b> / ' + post.get('comment' + str(i), {}).get('studentNameGrade') + '<br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                if post.get('comment' + str(i), {}).get('adminName') == None:
                    bigString += '<div class="rightAlign">'
                    if(post.get('comment' + str(i), {}).get('approved') == 'false'):
                        bigString += '<form action="/vetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet</button></form> '
                    else:
                        bigString += '<form action="/unvetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span>Unvet</button></form> '
                bigString += '<form action="/deleteComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>'
                bigString += '</div></td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                else:
                    if post.get('comment' + str(i), {}).get('approved') == 'true':
                        if post.get('comment' + str(i), {}).get('anonymous') == 'true':
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = loc_dt, content = Markup(postContent), _id = objectIDPost, comments = Markup(bigString))

@app.route('/deleteSE', methods=['GET', 'POST'])
def delete_SE():
    if request.method == 'POST':
        objectIDPost = request.form['delete'] #delete post
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEA']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
            name = post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail')
        else:
            name = post.get('adminName')
        collection.delete_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span><b>' + post.get('postTitle') + '</b> by ' + name + ' in english language learner forum<br>' + post.get('postContent')
        add_admin_log(datetime.now(), action)
    return render_special_education_forum()

@app.route('/deleteELL', methods=['GET', 'POST'])
def delete_ELL():
    if request.method == 'POST':
        objectIDPost = request.form['delete'] #delete post
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLA']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
            name = post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail')
        else:
            name = post.get('adminName')
        collection.delete_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span><b>' + post.get('postTitle') + '</b> by ' + name + ' in english language learner forum<br>' + post.get('postContent')
        add_admin_log(datetime.now(), action)
    return render_english_learner_forum()

@app.route('/vetELL', methods=['GET', 'POST'])
def vet_ELL():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] #vet and unvet posts
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLU']
        collection.find_one_and_update({'_id': ObjectId(objectIDPost)},
                                       {'$set': {'approved': 'true'}})
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span><b><a href="https://razzoforumproject.herokuapp.com/viewELLU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
        add_admin_log(datetime.now(), action)
    return render_english_learner_forum()
                                             
@app.route('/unvetELL', methods=['GET', 'POST'])
def unvet_ELL():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] #vet and unvet posts
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLU']
        collection.find_one_and_update({'_id': ObjectId(objectIDPost)},
                                       {'$set': {'approved': 'false'}})
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span><b><a href="https://razzoforumproject.herokuapp.com/viewELLU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in english language learner forum'
        add_admin_log(datetime.now(), action)
    return render_english_learner_forum()
                                             
@app.route('/vetSE', methods=['GET', 'POST'])
def vet_SE():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] #vet and unvet posts
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]       
        collection = db['SEU']
        collection.find_one_and_update({'_id': ObjectId(objectIDPost)},
                                       {'$set': {'approved': 'true'}})
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span><b><a href="https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
        add_admin_log(datetime.now(), action)
    return render_special_education_forum()
                                             
@app.route('/unvetSE', methods=['GET', 'POST'])
def unvet_SE():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] #vet and unvet posts
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEU']
        collection.find_one_and_update({'_id': ObjectId(objectIDPost)},
                                       {'$set': {'approved': 'false'}})
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span><b><a href="https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost + '">' + post.get('postTitle') + '</a></b> in special education forum'
        add_admin_log(datetime.now(), action)
    return render_special_education_forum()

#make sure the jinja variables use Markup 
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']

if __name__ == '__main__':
    app.run()
