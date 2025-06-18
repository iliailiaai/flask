from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from models import db, MultiplyRecord, User, UserData
from openai import OpenAI

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mysql+pymysql://root:cVeNAZGwWHptohkIyPQjyoWZOHKIkXld@mysql.railway.internal:3306/railway"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

client = OpenAI(
    api_key="sk-kiTWnBf109fi4oZtecJrFPoCTp2FvJW1",
    base_url="https://api.proxyapi.ru/openai/v1",
)

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



@app.route('/compile_program', methods=['POST'])
def compile_program():
    data = request.get_json()
    email = data.get('id_email')
    if not email:
        return jsonify({'error': 'Missing id_email'}), 400

    # Ищем пользователя в базе
    user = User.query.get(email)
    if not user or not user.user_data:
        return jsonify({'error': 'User not found or missing user_data'}), 404

    # Достаём нужные поля из user_data
    ud = user.user_data
    purpose   = ud.purpose or "не указано"
    gender    = ud.gender or "не указано"
    level     = ud.level or "не указано"
    frequency = ud.frequency or "не указано"
    trauma    = ud.trauma or "не указано"
    muscles   = ud.muscles or "не указано"
    age       = ud.age or "не указано"
        
    first_prompt = f"""Составь программу силовых тренировок для человека с такими показателями:  
    Цель: { purpose }
    Пол: { gender }
    Уровень подготовки: { level }
    Сколько раз в неделю может заниматься: { frequency }
    Были ли травмы: { trauma }
    Группы мышц, на которых сделать фокус: { muscles }
    Возраст: { age }

    Ничего не пиши перед описанием плана тренировок. Если тебе нужно сообщить что-то дополнительно, пиши это в конце.

    Не используй диапазоны, такие как 8-10, пиши точное число. Если нужно указать дробное значение, используй точки (например, 1.5).
    
    Время для отдыха пиши в минутах.

    Если не знаешь, какой вес в упражнении прописать пользователю, пиши: "?".
    
    Если упражнение с гантелями, указывай об этом в названии упражнения.

    Ответ выдавай строго в таком виде, но можешь написать доп. информацию после перечисления тренировок (При этом тренировок на неделе и упражнений в тренировке может быть несколько, их число ты должен выбрать сам на основании данных о человеке, для которого составляется тренировка):   

    ///Тренировка 1 день.

    1. Название упражнения.
    -Вес:
    -Подходов:
    -Повторений:
    -Отдых между подходами:

    ***Дней для отдыха для следующей тренировки:


    ///Тренировка 2 день.

    1. Название упражнения.
    -Вес:
    -Подходов:
    -Повторений:
    -Отдых между подходами:

    ***Дней для отдыха для следующей тренировки:


    """
    
    # Отправляем в OpenAI
    user_messages = [{"role": "user", "content": first_prompt}]

    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=user_messages
    )

    reply = chat_completion.choices[0].message.content
    print(reply)
    user_messages.append({"role": "assistant", "content": reply})
    
    return jsonify({"program": reply})









if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

