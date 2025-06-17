from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from models import db, MultiplyRecord 

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mysql+pymysql://root:cVeNAZGwWHptohkIyPQjyoWZOHKIkXld@mysql.railway.internal:3306/railway"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Создаём таблицы сразу при инициализации модуля
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return "Hello World!"


##############
@app.route('/api/multiply', methods=['POST'])
def multiply():
    print("Raw request data:", request.data) 
    data = request.get_json()
    if not data or 'number' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    number = data['number']
    result = number * 150
    record = MultiplyRecord(input=number, result=result)
    db.session.add(record)
    db.session.commit()

    return jsonify({'result': result})  # Возвращаем JSON с результатом

@app.route('/api/records', methods=['GET'])
def get_records():
    recs = MultiplyRecord.query.order_by(MultiplyRecord.id.desc()).all()
    return jsonify([r.to_dict() for r in recs])
##############















if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

