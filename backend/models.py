from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    voter_id = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.Enum('voter', 'admin'), default='voter')

    blockchain_address = db.Column(db.String(255), nullable=True)
    blockchain_private_key = db.Column(db.String(255), nullable=True)   # <-- REQUIRED

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Election(db.Model):
    __tablename__ = 'elections'
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Candidate(db.Model):
    __tablename__ = 'candidates'
    id = db.Column(db.Integer, primary_key=True)
    candidate_number = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(100))
    party = db.Column(db.String(100))
    age = db.Column(db.Integer)
    qualification = db.Column(db.String(200))
    description = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)

    votes = db.relationship('Vote', backref='candidate', lazy=True)

class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    tx_hash = db.Column(db.String(200))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'election_id', name='unique_vote'),
    )
