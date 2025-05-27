from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mysql+pymysql://root:cVeNAZGwWHptohkIyPQjyoWZOHKIkXld@mysql.railway.internal:3306/railway"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class MultiplyRecord(db.Model):
    __tablename__ = 'multiply_records'
    id     = db.Column(db.Integer, primary_key=True)
    input  = db.Column(db.Float, nullable=False)
    result = db.Column(db.Float, nullable=False)
    def to_dict(self):
        return {"id": self.id, "input": self.input, "result": self.result}

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return "Hello World!"

@app.route('/api/multiply', methods=['POST'])
def multiply():
    data = request.get_json()
    if not data or 'number' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    number = float(data['number'])
    result = number * 150

    record = MultiplyRecord(input=number, result=result)
    db.session.add(record)
    db.session.commit()

    return jsonify(record.to_dict()), 201

@app.route('/api/records', methods=['GET'])
def get_records():
    recs = MultiplyRecord.query.order_by(MultiplyRecord.id.desc()).all()
    return jsonify([r.to_dict() for r in recs])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

