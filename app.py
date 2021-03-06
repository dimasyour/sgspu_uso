from modulefinder import packagePathMap
from operator import ge
from os import error
from unittest import removeResult
from flask import Flask, render_template, session, request, redirect, url_for, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_manager, login_user, LoginManager, login_required, logout_user, current_user
from sqlalchemy import table
from models import *
from hashlib import md5
from datetime import datetime
from fpdf import FPDF
import json
import random
import string
import os
from werkzeug.utils import secure_filename
import pymongo

UPLOAD_FOLDER = '/img/photo/'
DEPARTMENT = [
    ['СГСПУ-1', 'ФМФИ', 'Факультет математики, физики и информатики'],
    ['СГСПУ-2', 'ФПСО', 'Факультет психологии и специального образования'],
    ['СГСПУ-3', 'ФКИ', 'Факультет культуры и искусства'],
    ['СГСПУ-4', 'ИФ', 'Исторический факультет'],
    ['СГСПУ-5', 'ФФ', 'Филологический факультет'],
    ['СГСПУ-6', 'ФИЯ', 'Факультет иностранных языков'],
    ['СГСПУ-7', 'ФЭУС', 'Факультет экономики, управления и сервиса'],
    ['СГСПУ-8', 'ФФКиС', 'Факультет физической культуры и спорта'],
    ['СГСПУ-9', 'ФНО', 'Факультет начального образования'],
    ['СГСПУ-10', 'ЕГФ', 'Естественно-географический факультет'],
]

app = Flask(__name__)
app.config['SECRET_KEY'] = '1911'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    #print("Сессия пользователя активна")
    return User.query.get(int(user_id))


# TODO: Добавить html-страницу "неавторизованности"
@login_manager.unauthorized_handler
def unauthorized_callback():
    print('"Вы не авторизированы!"')
    return redirect(url_for("user_login"))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/user_login', methods=["POST", "GET"])
def user_login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        curr_user = User.query.filter_by(email=email).first()
        if curr_user:
            hashpass = md5(password.encode('utf-8'))
            md5_hashpass = hashpass.hexdigest()
            if md5_hashpass == curr_user.password:
                login_user(curr_user)
                session["id"] = curr_user.id
                print(curr_user.email + " " + curr_user.password)
                return redirect(url_for("profile"))
            else:
                print("Неверная пара логина и пароля!")
                return redirect(url_for("user_login"))
        else:
            print("Такого пользователя не существует!")
            return redirect(url_for("user_login"))
    else:
        if session.get("id"):
            return redirect(url_for("user_page"))
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        username = db(request.form['username'])
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']  # TODO: ошибка при одинаковом эмейле
        region = request.form['region']
        password = request.form['password']  # TODO: Добавить проверку пароля
        level = request.form['you']
        hashpass = md5(password.encode('utf-8'))
        md5_hashpass = hashpass.hexdigest()
        avatar = request.form['avatar']  # TODO:добавить фото профиля
        print(avatar)
        if level == 0:
            department = '-'
        else:
            department = ''
        newUser = User(username=username, firstname=firstname, lastname=lastname, email=email,
                       uzName='', level=level, password=md5_hashpass, department=department, region=region, avatar='none.jpg')
        db.session.add(newUser)
        db.session.commit()
        print(newUser.firstname + " " + newUser.lastname + " " +
              newUser.email + " " + newUser.uzName + " " + str(newUser.level))
        # TODO: страница или сообщение успешной регистрации
        return redirect(url_for("user_login"))
    else:
        return render_template('register.html')

@app.route('/user_logout', methods=['GET', 'POST'])
@login_required
def user_logout():
    session.pop("id", None)
    logout_user()
    print("Пользователь вышел")
    return redirect(url_for('index'))


@app.route("/user")
@login_required
def user_page():
    user_id = current_user.id
    data_math = math_plus()
    data_math_all = math_all(data_math)
    result = db.session.execute(
        f'SELECT id, username, firstname, lastname, email, uzName, level FROM user WHERE id = {user_id};')
    return render_template('user.html', id_user=current_user.id, firstname=current_user.firstname, info=result, data=data_math, data2=data_math_all)


@app.route("/profile")
@login_required
def profile():
    data_math = math_plus()
    data_math_all = math_all(data_math)
    level_array = ['Незарегистрирован', 'Пользователь', 'Профорг',
                   'Председатель профбюро факультета', 'Председатель ППОС', 'Управляющий']
    cursor = db.session.execute(
        f'SELECT id, username, firstname, lastname, email, uzName, level, department, avatar FROM user WHERE id = {current_user.id};')
    result = cursor.fetchone()
    return render_template('profile.html', info=result, data=data_math, level_array=level_array, data2=data_math_all)


@app.route('/update_photo', methods=['GET', 'POST'])
@login_required
def update_photo():
    if request.method == 'POST':
        if 'upload_photo' in request.form:
            if 'photo' not in request.files:
                flash('Нет файловой части', category='danger')
                return redirect(url_for("settings"))
            file = request.files['photo']
            if file.filename == '':
                flash('Файл не выбран', category='danger')
                return redirect(url_for("settings"))
            try:
                if file and allowed_file(file.filename):
                    extension = secure_filename(
                        file.filename).rsplit('.', 1)[1]
                    new_file_name = generate_string(16)
                    file.save(os.path.join('static/uploads/avatar',
                              new_file_name + '.' + extension))
                    path = new_file_name + '.' + extension
                    db.session.execute(
                        f"UPDATE user SET avatar = '{path}' WHERE id = {current_user.id};")
                    db.session.commit()
                    # db.user.update_one({"_id": str(current_user.id), {"$set": {"avatar": path}})
                    flash('Фотография успешно обновленна', category='success')
                    return redirect(url_for("settings"))
                else:
                    flash('Недопустимое расширение файла', category='danger')
                    return redirect(url_for("settings"))
            except:
                flash('Ошибка загрузки файла', category='danger')
                return redirect(url_for("settings"))


@app.route('/profile/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        data_math = math_plus()
        data_math_all = math_all(data_math)
        cursor = db.session.execute(
            f'SELECT id, username, firstname, lastname, email, uzName, level, department, avatar FROM user WHERE id = {current_user.id};')
        result = cursor.fetchone()
        return render_template('profile/settings.html', info=result, data=data_math, level=current_user.level, array_department=DEPARTMENT)


@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():

    if 'add_event' in request.form and request.method == 'POST':
        name = request.form['name']
        info = request.form['info']
        sfera = request.form['sfera']
        level = int(request.form['level'])
        dateStart = request.form['dateStart']
        dateEnd = request.form['dateEnd']
        dateRegStart = request.form['dateRegStart']
        dateRegEnd = request.form['dateRegEnd']
        if current_user.level < 3 and level == 1:
            newEvent = Event(name=name, info=info, level=level, sfera=sfera, dateStart=dateStart, own=current_user.id,
                             dateEnd=dateEnd, dateRegStart=dateRegStart, dateRegEnd=dateRegEnd, moderator=3, status=0, id_str=generate_string(16))
        elif current_user.level < 3 and level == 2:
            newEvent = Event(name=name, info=info, level=level, sfera=sfera, dateStart=dateStart, own=current_user.id,
                             dateEnd=dateEnd, dateRegStart=dateRegStart, dateRegEnd=dateRegEnd, moderator=4, status=0, id_str=generate_string(16))
        elif current_user.level == 3 and level == 1:
            newEvent = Event(name=name, info=info, level=level, sfera=sfera, dateStart=dateStart, own=current_user.id,
                             dateEnd=dateEnd, dateRegStart=dateRegStart, dateRegEnd=dateRegEnd, moderator=3, status=1, id_str=generate_string(16))
        elif current_user.level == 3 and level == 2:
            newEvent = Event(name=name, info=info, level=level, sfera=sfera, dateStart=dateStart, own=current_user.id,
                             dateEnd=dateEnd, dateRegStart=dateRegStart, dateRegEnd=dateRegEnd, moderator=4, status=0, id_str=generate_string(16))
        elif current_user.level > 3 and level <= 2:
            newEvent = Event(name=name, info=info, level=level, sfera=sfera, dateStart=dateStart, own=current_user.id,
                             dateEnd=dateEnd, dateRegStart=dateRegStart, dateRegEnd=dateRegEnd, moderator=4, status=1, id_str=generate_string(16))
        else:
            print('Ошибка добавления мероприятия!')
            redirect(url_for("add_event"))
        db.session.add(newEvent)
        db.session.commit()
        return redirect(url_for("profile"))
    else:
        cursor = db.session.execute(
            f'SELECT id, username, firstname, lastname, email, uzName, level, avatar FROM user WHERE id = {current_user.id};')
        result = cursor.fetchone()
        return render_template('add_event.html', info=result)


@app.route("/request_events", methods=['GET'])
@login_required
def request_events():
    if current_user.level >= 3:
        if current_user.level == 3:
            moderator_str = f'(event.moderator = 3)'
        else:
            moderator_str = f'(event.moderator = 3 OR event.moderator = 4)'
        table = request.args.get('table')
        cursor = db.session.execute(
            f'SELECT id, username, firstname, lastname, email, uzName, level, avatar FROM user WHERE id = {current_user.id};')
        result = cursor.fetchone()
        if table == 'neob' or table is None:
            heading = 'Необработанные'
            cursor = db.session.execute(
                f"SELECT event.id, event.name, event.info, event.sfera, event.level, event.dateStart, event.dateEnd, event.dateRegStart, event.dateRegEnd, event.own, event.moderator, event.status, event.id_str, user.username, user.firstname, user.lastname FROM event JOIN user ON (event.own = user.id) WHERE {moderator_str} AND (event.status = 0)")
        elif table == 'ob':
            heading = 'Обработанные'
            cursor = db.session.execute(
                f"SELECT event.id, event.name, event.info, event.sfera, event.level, event.dateStart, event.dateEnd, event.dateRegStart, event.dateRegEnd, event.own, event.moderator, event.status, event.id_str, user.username, user.firstname, user.lastname FROM event JOIN user ON (event.own = user.id) WHERE {moderator_str} AND (event.status = 1 OR event.status = 2)")
        elif table == 'cancel':
            heading = 'Отклоннёные'
            cursor = db.session.execute(
                f"SELECT event.id, event.name, event.info, event.sfera, event.level, event.dateStart, event.dateEnd, event.dateRegStart, event.dateRegEnd, event.own, event.moderator, event.status, event.id_str, user.username, user.firstname, user.lastname FROM event JOIN user ON (event.own = user.id) WHERE {moderator_str} AND (event.status = 2)")
        elif table == 'agree':
            heading = 'Принятые'
            cursor = db.session.execute(
                f"SELECT event.id, event.name, event.info, event.sfera, event.level, event.dateStart, event.dateEnd, event.dateRegStart, event.dateRegEnd, event.own, event.moderator, event.status, event.id_str, user.username, user.firstname, user.lastname FROM event JOIN user ON (event.own = user.id) WHERE {moderator_str} AND (event.status = 1)")
        else:
            heading = 'Необработанные'
            cursor = db.session.execute(
                f"SELECT event.id, event.name, event.info, event.sfera, event.level, event.dateStart, event.dateEnd, event.dateRegStart, event.dateRegEnd, event.own, event.moderator, event.status, event.id_str, user.username, user.firstname, user.lastname FROM event JOIN user ON (event.own = user.id) WHERE {moderator_str} AND (event.status = 0)")
        result_events = cursor.fetchall()
        return render_template('request_events.html', info=result, events=result_events, heading=heading)
    else:
        print('Доступ запрещен!')
        return redirect(url_for("profile"))


@app.route('/levelup', methods=['GET', 'POST'])
@login_required
def levelup():
    if 'levelup' in request.form:
        if request.method == 'POST':
            user_id = str(request.form['user_id'])
            level = str(request.form['level'])
            if current_user.level < int(level):
                newLevelup_request = Levelup_request(
                    user_id=current_user.id, levelup=level, status=0)
                db.session.add(newLevelup_request)
                db.session.commit()
                print('Заявка отправлена')
                return redirect(url_for("user_page"))
    elif 'level_edit' in request.form and current_user.id == 1:
        if request.method == 'POST':
            user_id = str(request.form['user_id'])
            level = str(request.form['level'])
            if current_user.level < int(level):
                print('Недостаточно прав')
                return redirect(url_for("user_page"))
            else:
                db.session.execute(
                    f'UPDATE user SET level = {level} WHERE id = {user_id};')
                db.session.commit()
                return redirect(url_for("admin"))
        else:
            user_id = current_user.id
            result = db.session.execute(
                f'SELECT id, level FROM user WHERE id = {user_id};')
            res = result.fetchall()[0]
            return render_template('levelup.html', level_now=res)
    else:
        user_id = current_user.id
        result = db.session.execute(
            f'SELECT id, level FROM user WHERE id = {user_id};')
        res = result.fetchall()[0]
        return render_template('levelup.html', level_now=res)


@app.route("/admin")
@login_required
def admin():
    if current_user.id == 1:
        result = db.session.execute(
            f'SELECT id, firstname, lastname, email, uzName, level FROM user;')
        return render_template('admin.html', firstname=current_user.firstname, info=result)
    else:
        print('Недостаточно прав')  # TODO: Добавить сообщение об ошибке
        return redirect(url_for("user_page"))


@app.route('/level_edit', methods=['GET', 'POST'])
@login_required
def level_edit():
    if request.method == 'GET' and current_user.id == 1:
        id_user = request.args['id']
        result = db.session.execute(
            f'SELECT id, firstname, lastname, email, uzName, level FROM user WHERE id = {id_user};')
        return render_template('level_edit.html', user=current_user.level, info=result.fetchall()[0])
    else:
        print('Недостаточно прав')  # TODO: Добавить сообщение об ошибке
        return redirect(url_for("user_page"))


@app.route("/level_request", methods=['GET'])
@login_required
def level_request():
    user_id = request.args.get("id")
    if request.method == 'GET' and not user_id is None:
        user_id = request.args['id']
        id_z = request.args['id_z']
        solution = request.args['solution']
        if solution == 'yes':
            user_levelup = db.session.execute(
                f'SELECT * FROM levelup_request WHERE user_id = {user_id};')
            if not user_levelup:
                return redirect(url_for("user"))
            else:
                up = user_levelup.fetchall()[-1]
                if current_user.level > int(up.levelup):
                    db.session.execute(
                        f'UPDATE user SET level = {up.levelup} WHERE id = {user_id};')
                    db.session.commit()
                    db.session.execute(
                        f'UPDATE levelup_request SET status = 1 WHERE id = {id_z};')
                    db.session.commit()
                    result = db.session.execute(
                        f"SELECT levelup_request.id, user.id, user.firstname, user.lastname, user.level, levelup_request.levelup, levelup_request.status FROM user JOIN levelup_request ON levelup_request.user_id = user.id WHERE user.uzName = '{current_user.uzName}';")
                    # TODO: Очистить строку адресную как-то
                    return render_template('level_request.html', info=result)
                else:
                    print('Недостаточно прав')
                    return redirect(url_for("admin"))
        else:
            db.session.execute(
                f'UPDATE levelup_request SET status = 2 WHERE id = {id_z};')
            db.session.commit()
            result = db.session.execute(
                f"SELECT levelup_request.id, user.id, user.firstname, user.lastname, user.level, levelup_request.levelup, levelup_request.status FROM user JOIN levelup_request ON levelup_request.user_id = user.id WHERE user.uzName = '{current_user.uzName}';")
            return render_template('level_request.html', info=result)
    elif request.method == 'GET':
        result = db.session.execute(
            f"SELECT levelup_request.id, user.id, user.firstname, user.lastname, user.level, levelup_request.levelup, levelup_request.status FROM user JOIN levelup_request ON levelup_request.user_id = user.id WHERE user.uzName = '{current_user.uzName}';")
        return render_template('level_request.html', info=result)
    else:
        return redirect(url_for("admin"))


@app.route("/events", methods=['GET', 'POST'])
@login_required
def events():
    result = db.session.execute(
        f"SELECT * FROM event WHERE uzName = '{current_user.uzName}';")
    return render_template('events.html', info=result)


@app.route('/event-1', methods=['GET'])
def event_1():
    if request.method == 'GET':
        event_id = request.args['id']
        # result = db.session.execute(
        #     f"SELECT * FROM event WHERE id = {id} LIMIT 1;")
        # event = Event.query.get(event_id)
        cursor = db.session.execute(
            f"SELECT event.id, event.name, event.sfera, event.dateStart, event.nagrada, event.uzName, event.status, event.moderator, event.levelE, event.own, event.dateEnd, event.dateRegStart, event.dateRegEnd, enroll.status FROM event JOIN enroll ON event.id = enroll.event_id WHERE enroll.user_id = '{current_user.id}' AND event.id = '{event_id}';")
        result = cursor.fetchone()
        if result is None:
            cursor = db.session.execute(
                f"SELECT * FROM event WHERE id = {event_id} LIMIT 1;")
            result = cursor.fetchone()
            return render_template('event.html', info=result)
        else:
            return render_template('event.html', info=result)
    else:
        return redirect(url_for("events"))


@app.route('/event', methods=['GET'])
def event():
    id_str = request.args.get('id_str')
    if request.method == 'GET' and not id_str is None:
        cursor_check = db.session.execute(
            f"SELECT * FROM event WHERE id_str = '{id_str}';")
        if cursor_check.fetchone() is not None:
            cursor = db.session.execute(
                f'SELECT id, username, firstname, lastname, email, uzName, level, avatar, department FROM user WHERE id = {current_user.id};')
            result = cursor.fetchone()
            cursor = db.session.execute(
                f"SELECT * FROM event WHERE id_str = '{id_str}';")
            event = cursor.fetchone()
            return render_template('event.html', info=result, event=event)
        else:
            print('Такого мероприятия не существует!')
            return redirect(url_for("profile"))
    else:
        return redirect(url_for("profile"))


@app.route('/request_event', methods=['GET', 'POST'])
def request_event():
    id_str = request.args.get('id_str')
    if not id_str is None:
        if request.method == 'POST':
            solution = request.form['solution']
            # TODO: проверка на обработанное мероприятие
            if solution == 'agree':
                db.session.execute(
                    f"UPDATE event SET status = 1 WHERE id_str = '{id_str}';")
                db.session.commit()
                return redirect(url_for("request_events"))
            elif solution == 'disagree':
                db.session.execute(
                    f"UPDATE event SET status = 2 WHERE id_str = '{id_str}';")
                db.session.commit()
                return redirect(url_for("request_events"))
            else:
                print('Ошибка')
                return redirect(url_for("request_events"))
        else:
            cursor_check = db.session.execute(
                f"SELECT * FROM event WHERE id_str = '{id_str}';")
            if cursor_check.fetchone() is not None:
                cursor = db.session.execute(
                    f'SELECT id, username, firstname, lastname, email, uzName, level, avatar, department FROM user WHERE id = {current_user.id};')
                result = cursor.fetchone()
                cursor = db.session.execute(
                    f"SELECT * FROM event WHERE id_str = '{id_str}';")
                event = cursor.fetchone()
                return render_template('request_event.html', info=result, event=event)
            else:
                print('Такого мероприятия не существует!')
                return redirect(url_for("profile"))
    else:
        return redirect(url_for("profile"))


@app.route("/profile/my_events", methods=['GET', 'POST'])
@login_required
def my_events():
    result = db.session.execute(
        f"SELECT * FROM event WHERE own = '{current_user.id}';")
    return render_template('profile/my_events.html', info=result)


@app.route("/profile/events_request", methods=['GET', 'POST'])
@login_required
def events_request():
    id = request.args.get('id')
    if request.method == 'GET' and not id is None:
        id = request.args['id']
        solution = request.args['solution']
        event = Event.query.get(id)
        if solution == 'yes' and current_user.level >= event.levelE:
            db.session.execute(
                f'UPDATE event SET status = 1 WHERE id = {id};')
            db.session.commit()
            return render_template('event.html', info=event)
        elif solution == 'yes' and current_user.level <= event.levelE:
            print('Недостаточно прав')
            return redirect(url_for("/profile/events_request"))
        else:
            db.session.execute(
                f'UPDATE event SET status = 2 WHERE id = {id};')
            db.session.commit()
            return render_template('event.html', info=event)
    else:
        query_string = f"SELECT * FROM event WHERE moderator <= '{current_user.level}' AND uzName = '{current_user.uzName}' AND status = 0;"
        cursor = db.session.execute(query_string)
        result = cursor.fetchall()
        return render_template('profile/events_request.html', info=result)


@app.route("/enroll", methods=['GET', 'POST'])
@login_required
def enroll():
    if request.method == 'POST':
        event_id = int(request.form['event_id'])
        dateReg = datetime.today().strftime('%Y-%m-%d')
        newEnroll = Enroll(event_id=event_id,
                           user_id=current_user.id, dateReg=dateReg, status=0)
        db.session.add(newEnroll)
        db.session.commit()
        return redirect(url_for("my_calend"))
    else:
        return redirect(url_for("user_page"))


@app.route("/profile/calend", methods=['GET', 'POST'])
@login_required
def my_calend():
    result = db.session.execute(
        f"SELECT enroll.event_id, event.name, event.sfera, event.dateStart, event.dateEnd, event.dateRegStart, event.dateRegEnd, enroll.dateReg, enroll.status FROM enroll JOIN event ON event.id = enroll.event_id WHERE enroll.user_id = '{current_user.id}';")
    return render_template('profile/calend.html', info=result)


@app.route("/profile/event", methods=['GET', 'POST'])
@login_required
def my_event():
    event_id = request.args.get('event_id')
    user_id = request.args.get('user_id')
    solution = request.args.get('solution')
    if request.method == 'GET' and not solution is None:
        event_id = request.args['event_id']
        user_id = request.args['user_id']
        solution = request.args['solution']
        event = Event.query.get(event_id)
        if solution == 'yes' and current_user.level >= event.levelE:
            db.session.execute(
                f"UPDATE enroll SET status = 1 WHERE event_id = '{event_id}' AND user_id = '{user_id}';")
            db.session.commit()
            cursor = db.session.execute(
                f"SELECT event.id, event.name, event.sfera, event.uzName, event.own, enroll.user_id, enroll.event_id, enroll.status, enroll.dateReg FROM event JOIN enroll ON event.id = enroll.event_id WHERE event.id = '{event_id}' ORDER BY enroll.dateReg;")
            result = cursor.fetchall()
            return render_template('profile/event.html', info=result)
        elif solution == 'yes' and current_user.level <= event.levelE:
            print('Недостаточно прав')
            cursor = db.session.execute(
                f"SELECT event.id, event.name, event.sfera, event.uzName, event.own, enroll.user_id, enroll.event_id, enroll.status, enroll.dateReg FROM event JOIN enroll ON event.id = enroll.event_id WHERE event.id = '{event_id}' ORDER BY enroll.dateReg;")
            result = cursor.fetchall()
            return render_template('profile/event.html', info=result)
        else:
            db.session.execute(
                f"UPDATE enroll SET status = 0 WHERE event_id = '{event_id}' AND user_id = '{user_id}';")
            db.session.commit()
            cursor = db.session.execute(
                f"SELECT event.id, event.name, event.sfera, event.uzName, event.own, enroll.user_id, enroll.event_id, enroll.status, enroll.dateReg FROM event JOIN enroll ON event.id = enroll.event_id WHERE event.id = '{event_id}' ORDER BY enroll.dateReg;")
            result = cursor.fetchall()
            return render_template('profile/event.html', info=result)
    else:
        event_id = request.args['event_id']
        cursor = db.session.execute(
            f"SELECT event.id, event.name, event.sfera, event.uzName, event.own, enroll.user_id, enroll.event_id, enroll.status, enroll.dateReg FROM event JOIN enroll ON event.id = enroll.event_id WHERE event.id = '{event_id}' ORDER BY enroll.dateReg;")
        result = cursor.fetchall()
        return render_template('profile/event.html', info=result)


@app.route("/api/events/all", methods=['GET'])
def allBoardGames():
    client = pymongo.MongoClient("mongodb+srv://dimasyour:2010Dima@events.j6srk.mongodb.net/events?retryWrites=true&w=majority")
    db = client.events
    col = db.event
    events = col.find({},{'_id': 0})
    allEvents = []
    for event in events:
        allEvents.append(event["name"])
    print(allEvents)
    return '<h1>heelo</h2>'


def math_plus():
    sfera_array = ['Общественная', 'Творческая', 'Спортивная', 'Научная']
    status_array = [0, 1, 2]
    result = []
    for sfera in range(len(sfera_array)):
        result.append([])
        result[sfera].append(sfera_array[sfera])
        for status in range(len(status_array)):
            cursor = db.session.execute(
                f"SELECT count(*) FROM event WHERE own = '{current_user.id}' AND sfera = '{sfera_array[sfera]}' AND status = {status}")
            result[sfera].append(cursor.fetchone()[0])
    sum_event = 0
    for i in range(len(result)):
        for j in range(len(result[i])):
            if result[i][j] != 0 and j != 0:
                sum_event = sum_event + result[i][j]
        result[i].append(sum_event)
        sum_event = 0
    return result


def math_all(Arr):
    sum_success = 0
    sum_progressing = 0
    sum_cancel = 0
    for i in Arr:
        sum_progressing = sum_progressing + i[1]
        sum_success = sum_success + i[2]
        sum_cancel = sum_cancel + i[3]
    result = [sum_progressing, sum_success, sum_cancel]
    return result


def generate_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    rand_string = ''.join(random.sample(letters_and_digits, length))
    return rand_string


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}



if __name__ == '__main__':
    print("Веб-приложение запущено!")
    app.run(port=5000, debug=True)
