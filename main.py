from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from models import db, MultiplyRecord, User, UserData, ProgramModel, WorkoutModel, ExerciseModel, ExerciseHistory, ActualExercise, PerformedExercise, CompletedDates
from openai import OpenAI
from datetime import datetime, timedelta, date
import re
from dataclasses import dataclass
from typing import Union, List

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


@dataclass
class Exercise:
    name: str
    weight: Union[float, str]  # вес может быть числом или строкой "?"
    sets: int
    reps: Union[int, str]  # повторения могут быть числом или текстом (например, "Держаться 30 секунд")
    rest_min: str

@dataclass
class Workout:
    number: int
    exercises: List[Exercise]
    rest_days: int

@dataclass
class Program:
    workouts: List[Workout]

    def add_workout(self, workout: Workout):
        self.workouts.append(workout)

    def clear_workouts(self):
        self.workouts.clear()

# Функция для парсинга
def parse_program(text: str) -> Program:
    program_parsed = Program(workouts=[])

    # Разделяем текст на отдельные тренировки
    workouts_text = text.split("///Тренировка")[1:]  # Пропускаем текст до первой тренировки
    for workout_text in workouts_text:
        # Извлекаем номер тренировки
        workout_number_match = re.search(r"(\d+) день", workout_text)
        if not workout_number_match:
            continue
        workout_number = int(workout_number_match.group(1))

        # Ищем упражнения
        exercises = []
        exercise_matches = re.findall(
            r"\d+\.\s+([^\n]+)\.\n-Вес:\s*([^\n]+)\n-Подходов:\s*(\d+)\n-Повторений:\s*([^\n]+)\n-Отдых между подходами:\s*([\d.]+)",
            workout_text
        )
        for match in exercise_matches:
            name, weight, sets, reps, rest_min = match
            weight = float(weight) if weight.replace(".", "", 1).isdigit() else weight
            sets = int(sets)
            reps = int(reps) if reps.isdigit() else reps
            rest_min = str(rest_min)
            exercises.append(Exercise(name=name, weight=weight, sets=sets, reps=reps, rest_min=rest_min))

        # Ищем количество дней отдыха
        rest_days_match = re.search(r"\*\*\*Дней для отдыха для следующей тренировки:\s*(\d+)", workout_text)
        rest_days = int(rest_days_match.group(1)) if rest_days_match else 0

        # Создаем тренировку и добавляем её в программу
        workout = Workout(number=workout_number, exercises=exercises, rest_days=rest_days)
        program_parsed.add_workout(workout)

    return program_parsed



def compute_schedule(workouts: List[WorkoutModel], creation_date: date, diff_weeks: Int) -> List[dict]:
    """
    Для каждого WorkoutModel в `workouts` считаем фактическую дату:
      current_date = creation_date для первой тренировки,
      затем current_date += rest_days + 1
    И прекращаем, как только current_date >= следующий понедельник.
    Возвращаем список словарей {'day': int, 'workout_number': int}.
    """
    schedule = []
    # находим дату следующего понедельника
    # weekday(): Пн=0, Вт=1, ..., Вс=6
    days_till_mon = ((7 - creation_date.weekday()) % 7 or 7) + 7 + (7 * diff_weeks)
    week_boundary = creation_date + timedelta(days=days_till_mon)

    current = creation_date
    idx = 0               # индекс в workouts
    n = len(workouts)
    
    # Пока не перешли границу следующего понедельника
    while current < week_boundary:
        # если воскресенье — переносим на понедельник
        if current.weekday() == 6:
            current = current + timedelta(days=1)
        
        w = workouts[idx % n]   # берем по кругу
        schedule.append({
            'day': current.day,
            'workout_number': w.number
        })
        # готовим дату следующей тренировки
        current = current + timedelta(days=w.rest_days + 1)
        idx += 1
        
    print(schedule)

    return schedule

def get_week_difference(start_date: date, end_date: date) -> int:
    """
    Точная разница в ISO-неделях между двумя датами.
    """
    start_iso = start_date.isocalendar()
    end_iso = end_date.isocalendar()

    # считаем количество недель от начала ISO-эпохи (год * 53 + номер недели)
    total_start_weeks = start_iso[0] * 53 + start_iso[1]
    total_end_weeks = end_iso[0] * 53 + end_iso[1]

    return total_end_weeks - total_start_weeks


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

    program_parsed = parse_program(reply)

    # создаём программу
    prog = ProgramModel(user_email=email)
    db.session.add(prog)
    
    # для каждой тренировки из dataclass
    for w in program_parsed.workouts:
        w_model = WorkoutModel(
            number=w.number,
            rest_days=w.rest_days
        )
        # привязываем через relationship
        prog.workouts.append(w_model)
    
        # для каждого упражнения
        for ex in w.exercises:
            ex_model = ExerciseModel(
                name=str(ex.name),
                weight=str(ex.weight),
                sets=ex.sets,
                reps=str(ex.reps),
                rest_min=ex.rest_min
            )
            # тоже через relationship
            w_model.exercises.append(ex_model)
    
    # единый коммит в конце
    db.session.commit()
    
    return jsonify({"program": reply})


@app.route('/get_program/<email>', methods=['GET'])
def get_program(email):
    # Находим последнюю (или единственную) программу пользователя
    prog = ProgramModel.query \
        .filter_by(user_email=email) \
        .order_by(ProgramModel.created_at.desc()) \
        .first()

    if not prog:
        return jsonify({'error': 'Program not found'}), 404

    # Собираем workouts
    workouts_list = []
    for w in prog.workouts:
        exercises_list = []
        for ex in w.exercises:
            exercises_list.append({
                'name': ex.name,
                'weight': ex.weight,
                'sets': ex.sets,
                'reps': str(ex.reps),
                'rest_min': str(ex.rest_min),
            })
        workouts_list.append({
            'number': w.number,
            'rest_days': w.rest_days,
            'exercises': exercises_list
        })

    # Теперь у нас есть объект prog: ProgramModel с полем created_at и списком prog.workouts
    creation_date = prog.created_at.date()  # datetime -> date
    current_date = date.today()

    diff_weeks = get_week_difference(creation_date, current_date)
    print(diff_weeks)
    
    schedule = compute_schedule(prog.workouts, creation_date, diff_weeks)

    # Формируем итоговый JSON
    result = {
        'id_email': email,
        'workouts': workouts_list,
        'schedule': schedule
    }
    return jsonify(result), 200


@app.route('/check_program/<email>', methods=['GET'])
def check_program(email):
    # Находим последнюю (или единственную) программу пользователя
    prog = ProgramModel.query \
        .filter_by(user_email=email) \
        .order_by(ProgramModel.created_at.desc()) \
        .first()

    print(f"Есть ли программа у {email} - {bool(prog)}")

    return jsonify({'has_program': bool(prog)})


def get_or_create_exercise_history(user_email: str, raw_name: str) -> ExerciseHistory:
    name = raw_name.strip().lower()

    # 1) Сначала ищем точное совпадение
    existing = ExerciseHistory.query.filter_by(
        user_email=user_email,
        name=name
    ).first()
    if existing:
        return existing

    # 2) Простое fuzzy-поисковое совпадение (contains)
    fuzzy = ExerciseHistory.query.filter(
        ExerciseHistory.user_email == user_email,
        ExerciseHistory.name.contains(name)
    ).first()
    if fuzzy:
        return fuzzy

    # 3) Если нет — создаём новую запись
    new = ExerciseHistory(user_email=user_email, name=name)
    db.session.add(new)
    db.session.flush()
    return new


@app.route('/save_exercise/<email>', methods=['POST'])
def save_exercise(email):
    """
    Ожидает JSON:
    {
      "name": "Жим штанги лежа",
      "weight": 60.0,
      "sets": 4,
      "reps": 8
    }
    """
    data = request.get_json()
    name             = data.get('name')
    weight           = data.get('weight')
    sets             = data.get('sets')
    reps             = data.get('reps')
    workout_number   = data.get('workout_number')
    actual_exercise  = data.get('actual_exercise')

    # Проверяем обязательные поля
    if not all([email, name, weight, sets, reps]):
        return jsonify({'error': 'Missing fields'}), 400

    # 1) Находим или создаём ExerciseHistory
    eh = get_or_create_exercise_history(email, name)

    # 2) Создаём PerformedExercise
    pe = PerformedExercise(
        exercise_history_id=eh.id,
        weight=weight,
        sets=sets,
        reps=reps
    )
    db.session.add(pe)

        # 2) Обновляем запись в "программе тренировок"
    #    а) находим программу пользователя
    prog = ProgramModel.query \
        .filter_by(user_email=email) \
        .order_by(ProgramModel.created_at.desc()) \
        .first()
    if prog:
        # б) находим нужную тренировку по её порядковому номеру
        workout = next(
            (w for w in prog.workouts if w.number == workout_number),
            None
        )
        if workout:
            # в) получаем список упражнений этой тренировки
            exercises = workout.exercises
            idx = actual_exercise - 1  # actual_exercise — 1‑based
            if 0 <= idx < len(exercises):
                # г) правим вес
                exercises[idx].weight = str(weight)
            else:
                return jsonify({'error': 'actual_exercise out of range'}), 400
        else:
            return jsonify({'error': 'Workout not found'}), 404
    else:
        return jsonify({'error': 'Program not found'}), 404

    db.session.commit()

    print(f"Упражнение сохранено, вес {pe.weight}")

    return jsonify({'weight': pe.weight}), 201



@app.route('/add_date/<email>', methods=['POST'])
def add_date(email):
    data = request.get_json()
    date_ = data.get('date')
    if not date_:
        return jsonify({'error': 'Missing field `date`'}), 400

    try:
        new_date = datetime.strptime(date_, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Сохраняем новую дату
    cd = CompletedDates(user_email=email, date_=new_date)
    db.session.add(cd)

    # Находим границу — понедельник две недели назад
    today = datetime.utcnow().date()
    monday_this_week = today - timedelta(days=today.weekday())
    boundary = monday_this_week - timedelta(weeks=2)

    # Удаляем старые записи
    CompletedDates.query.filter(
        CompletedDates.user_email == email,
        CompletedDates.date_ < boundary
    ).delete(synchronize_session=False)

    db.session.commit()

    return jsonify({'date': new_date.isoformat()}), 201


@app.route("/get_completed_dates/<email>", methods=["GET"])
def get_completed_dates(email):
    # Получаем все даты по email из таблицы CompletedDate
    completed = CompletedDates.query.filter_by(user_email=email).all()

    # Преобразуем результат в нужный формат
    completed_dates = [{"date": c.date_.strftime("%Y-%m-%d")} for c in completed]

    print(completed_dates)

    return jsonify({"completed_dates": completed_dates})




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

