import jwt
import datetime
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
import pymongo
from flask_cors import CORS
import os
from bson import ObjectId

# Подключение к MongoDB
uri = 'mongodb+srv://bober25:121212adadad@govno.2cqxu.mongodb.net/'
client = pymongo.MongoClient(uri)
db = client['test2']
users_collection = db['With_ID_test_2(11.12)']

# Указываем папку с фронтендом, используя относительный путь
app = Flask(__name__, static_folder='dist')  # Относительный путь для статики

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
        return jsonify({'message': 'No token'}), 401

    try:
        token = token.replace('Bearer ', '')  # Убираем префикс Bearer
    except Exception:
        return jsonify({'message': 'Токен имеет не тот формат'}), 401

    try:
        # Проверяем токен
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token['user_id']

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Токен истёк'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Неверный токен'}), 401
    except Exception as e:
        return jsonify({'message': 'Error'}), 401
    
    # Возвращаем защищённые данные (например, информацию о пользователе)
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    return jsonify({'message': 'Good access', 'user_id': str(user['_id'])}), 200

@app.route('/<path:path>', methods=['GET'])
def catch_all(path):
    if path.startswith("api"):  # API-запросы обрабатываются отдельно
        return jsonify({'message': 'API доступен'}), 404
    
    # Проверяем авторизацию
    token = request.headers.get('Authorization')
    if token:
        token = token.replace('Bearer ', '')  # Убираем префикс Bearer

        try:
            # Декодируем токен и проверяем его
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = decoded_token['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Токен истёк'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Неверный токен'}), 401

        # Пользователь авторизован — отправляем файл index.html
        return send_from_directory(os.path.join(app.root_path, 'dist'), 'index.html')

    else:
        # Если токен не найден, редиректим на страницу логина или возвращаем ошибку
        return jsonify({'message': 'No token'}), 401





if __name__ == '__main__':
    # Для Railway нужно запускать с host='0.0.0.0', чтобы сервер был доступен извне
    app.run(debug=True, host='0.0.0.0', port=5000)
