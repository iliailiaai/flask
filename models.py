from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MultiplyRecord(db.Model):
    __tablename__ = 'multiply_records'
    id     = db.Column(db.Integer, primary_key=True)
    input  = db.Column(db.Integer, nullable=False)
    result = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {"id": self.id, "input": int(self.input), "result": int(self.result)}



"""
class User(db.Model):
    __tablename__ = 'users'
    id_email = db.Column(db.String, primary_key=True)
    user_data = db.relationship("UserData", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserData(db.Model):
    __tablename__ = 'user_data'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String, db.ForeignKey('users.id_email'), nullable=False, unique=True)

    purpose = db.Column(db.String(100))
    gender = db.Column(db.String(20))
    level = db.Column(db.String(50))
    frequency = db.Column(db.Integer)
    trauma = db.Column(db.String(255))
    muscles = db.Column(db.String(255))
    age = db.Column(db.Integer)

    user = db.relationship("User", back_populates="user_data")
"""
