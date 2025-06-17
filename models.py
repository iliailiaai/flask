from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MultiplyRecord(db.Model):
    __tablename__ = 'multiply_records'
    id     = db.Column(db.Integer, primary_key=True)
    input  = db.Column(db.Integer, nullable=False)
    result = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {"id": self.id, "input": int(self.input), "result": int(self.result)}
