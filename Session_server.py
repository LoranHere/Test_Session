import jwt
import datetime
from flask import Flask, request, jsonify, send_from_directory
import pymongo
from flask_cors import CORS
import os

# Подключение к MongoDB
uri = 'mongodb+srv://bober25:121212adadad@govno.2cqxu.mongodb.net/'
client = pymongo.MongoClient(uri)
db = client['test2']
users_collection = db['With_ID_test_2(11.12)']

app = Flask(__name__)

CORS(app, origins=["https://comeback-front-production.up.railway.app"])

# Секретный ключ для подписи JWT
app.config['SECRET_KEY'] = 'supersecretkey'

# Функция для создания токена
def generate_token(user_id):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=48)  # Токен действителен 48 часов
    token = jwt.encode(
        {'user_id': str(user_id), 'exp': expiration_time},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    return token

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    password = data.get('password')

    # Найдем пользователя в базе данных по паролю
    user = users_collection.find_one({'password': password})
    
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    token = generate_token(user['_id'])
    return jsonify({'token': token}), 200

# Защищённый маршрут, доступный только для авторизованных пользователей
@app.route('/api/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')  # Получаем токен из заголовка
    
    if not token:
        return jsonify({'message': 'Токен не предоставлен'}), 403
    
    try:
        # Проверяем токен
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Токен истёк'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Неверный токен'}), 401
    
    # Возвращаем защищённые данные (например, информацию о пользователе)
    user = users_collection.find_one({'_id': pymongo.ObjectId(user_id)})
    return jsonify({'message': 'Доступ разрешён', 'user_id': str(user['_id'])}), 200

# Обработчик для отдачи index.html для всех путей, кроме API
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET'])
def catch_all(path):
    if not path.startswith('api'):  # Все пути, которые не начинаются с 'api', передаем на фронтенд
        return send_from_directory(os.path.join(app.dist), 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
