from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Date

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
    actual_exercises = db.relationship("ActualExercise", back_populates="user", cascade="all, delete-orphan")

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


class CompletedDates(db.Model):
    __tablename__ = 'completed_dates'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100), db.ForeignKey('users.id_email'), nullable=False)

    date_      = db.Column('date', db.Date, nullable=False) 


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

    
class ActualExercise(db.Model):
    __tablename__ = 'actual_exercise'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(100), db.ForeignKey('users.id_email'), nullable=False)
    value = db.Column(db.Integer, nullable=False)

    user = db.relationship("User", back_populates="actual_exercises")


class ExerciseHistory(db.Model):
    __tablename__ = 'exercise_history'
    id          = db.Column(db.Integer, primary_key=True)
    user_email  = db.Column(db.String(100), db.ForeignKey('users.id_email'), nullable=False)
    name        = db.Column(db.String(255), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Все выполненные события по этому упражнению
    performed = db.relationship(
        'PerformedExercise',
        back_populates='exercise',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.UniqueConstraint('user_email', 'name', name='uq_user_exercise'),
    )


class PerformedExercise(db.Model):
    __tablename__ = 'performed_exercise'
    id                  = db.Column(db.Integer, primary_key=True)
    exercise_history_id = db.Column(db.Integer, db.ForeignKey('exercise_history.id'), nullable=False)
    performed_at        = db.Column(db.DateTime, default=datetime.utcnow)
    weight              = db.Column(db.String(20), nullable=True)
    sets                = db.Column(db.Integer, nullable=False)
    reps                = db.Column(db.String(40), nullable=False)

    exercise = db.relationship('ExerciseHistory', back_populates='performed')

