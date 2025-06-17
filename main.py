from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from models import db, MultiplyRecord, User, UserData

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



# Роут сохранения user + userdata
@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    if not data or 'id_email' not in data:
        return jsonify({'error': 'Missing id_email'}), 400

    email = data['id_email']
    # Попробуем найти существующего пользователя
    user = User.query.get(email)
    if not user:
        # Если нет — создаём
        user = User(id_email=email)
        user.user_data = UserData(
            user_email=email,
            purpose=data.get('purpose'),
            gender=data.get('gender'),
            level=data.get('level'),
            frequency=data.get('frequency'),
            trauma=data.get('trauma'),
            muscles=data.get('muscles'),
            age=data.get('age')
        )
        db.session.add(user)
        status_code = 201
    else:
        # Если есть — обновляем поля
        ud = user.user_data
        ud.purpose   = data.get('purpose',   ud.purpose)
        ud.gender    = data.get('gender',    ud.gender)
        ud.level     = data.get('level',     ud.level)
        ud.frequency = data.get('frequency', ud.frequency)
        ud.trauma    = data.get('trauma',    ud.trauma)
        ud.muscles   = data.get('muscles',   ud.muscles)
        ud.age       = data.get('age',       ud.age)
        status_code = 200  # OK — обновление

    db.session.commit()

    return jsonify({
        'id_email': user.id_email,
        'user_data': {
            'purpose': user.user_data.purpose,
            'gender': user.user_data.gender,
            # ... при необходимости возвращайте остальные поля
        }
    }), status_code










if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

