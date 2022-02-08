from app import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120),  nullable=False)
    firstname = db.Column(db.String(120),  nullable=False)
    lastname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    uzName = db.Column(db.String(120), nullable=False)
    level = db.Column(db.Integer,  nullable=False)
    password = db.Column(db.String(250), nullable=False)
    department = db.Column(db.String(120), nullable=False)
    region = db.Column(db.String(120), nullable=False)
    avatar = db.Column(db.String(120), nullable=False)
    
    def __repr__(self):
        return (f"User('{self.firstname}', '{self.username}', '{self.lastname}', '{self.email}' , '{self.uzName}' , '{self.level}' ,'{self.password}', '{self.department}', '{self.region}', '{self.avatar}')")


class Event(db.Model, UserMixin):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    info = db.Column(db.String(200))
    sfera = db.Column(db.String(120), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    dateStart = db.Column(db.String(120), nullable=False)
    dateEnd = db.Column(db.String(120), nullable=False)
    dateRegStart = db.Column(db.String(120), nullable=False)
    dateRegEnd = db.Column(db.String(120), nullable=False)
    own = db.Column(db.Integer, nullable=False)
    moderator = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    id_str = db.Column(db.String(120), nullable=False)
    
    def __repr__(self):
        return (f"Event('{self.name}', '{self.info}',  '{self.sfera}', '{self.level}', '{self.dateStart}', '{self.dateEnd}', '{self.dateRegStart}', '{self.dateRegEnd}', '{self.own}', '{self.moderator}', '{self.status}', '{self.id_str}')")


class Levelup_request(db.Model, UserMixin):
    __tablename__ = 'levelup_request'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,  nullable=False)
    levelup = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer)
    
    def __repr__(self):
        return (f"Levelup_request('{self.user_id}', '{self.levelup}', '{self.status}')")


class Enroll(db.Model, UserMixin):
    __tablename__ = 'enroll'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer,  nullable=False)
    dateReg = db.Column(db.String(120), nullable=False)
    status = db.Column(db.Integer,  nullable=False)
    
    def __repr__(self):
        return (f"Enroll('{self.event_id}', '{self.user_id}', '{self.dateReg}' ,'{self.status}')")