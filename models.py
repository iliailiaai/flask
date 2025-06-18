from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MultiplyRecord(db.Model):
    __tablename__ = 'multiply_records'
    id     = db.Column(db.Integer, primary_key=True)
    input  = db.Column(db.Integer, nullable=False)
    result = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {"id": self.id, "input": int(self.input), "result": int(self.result)}



class User(db.Model):
    __tablename__ = 'users'
    id_email = db.Column(db.String(100), primary_key=True)
    user_data = db.relationship("UserData", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserData(db.Model):
    __tablename__ = 'user_data'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100), db.ForeignKey('users.id_email'), nullable=False, unique=True)

    purpose = db.Column(db.String(100))
    gender = db.Column(db.String(20))
    level = db.Column(db.String(50))
    frequency = db.Column(db.Integer)
    trauma = db.Column(db.String(255))
    muscles = db.Column(db.String(255))
    age = db.Column(db.Integer)

    user = db.relationship("User", back_populates="user_data")


class ProgramModel(db.Model):
    __tablename__ = 'programs'
    id        = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100), db.ForeignKey('users.id_email'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    workouts = db.relationship('WorkoutModel', back_populates='program', cascade='all, delete-orphan')


class WorkoutModel(db.Model):
    __tablename__ = 'workouts'
    id         = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    number     = db.Column(db.Integer, nullable=False)
    rest_days  = db.Column(db.Integer, default=0)

    program   = db.relationship('ProgramModel', back_populates='workouts')
    exercises = db.relationship('ExerciseModel', back_populates='workout', cascade='all, delete-orphan')


class ExerciseModel(db.Model):
    __tablename__ = 'exercises'
    id         = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workouts.id'), nullable=False)

    name      = db.Column(db.String(255), nullable=False)
    weight    = db.Column(db.String(20), nullable=False)  # строка, чтобы принять "?" или "12.5"
    sets      = db.Column(db.Integer, nullable=False)
    reps      = db.Column(db.String(40), nullable=False)  # строка, чтобы принять текстовые варианты
    rest_min  = db.Column(db.String(20), nullable=False)

    workout = db.relationship('WorkoutModel', back_populates='exercises')

