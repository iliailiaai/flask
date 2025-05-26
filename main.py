from flask import Flask, request, jsonify
from flask_cors import CORS  # Импорт CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "Hello World!"

# Обработка POST-запроса
@app.route('/api/multiply', methods=['POST'])
def multiply():
    print("Raw request data:", request.data) 
    data = request.get_json()  # Получаем JSON из тела запроса
    if not data or 'number' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    
    number = data['number']  # Извлекаем переданное число
    result = number * 150   
    return jsonify({'result': result})  # Возвращаем JSON с результатом

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Приложение слушает порт 5000
