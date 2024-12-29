import jwt
import datetime
import zipfile
from flask import Flask, send_file, request, jsonify, send_from_directory, redirect, url_for
import pymongo
from flask_cors import CORS
import os
from bson import ObjectId
import json

# Подключение к MongoDB
uri = 'mongodb+srv://bober25:121212adadad@govno.2cqxu.mongodb.net/'
client = pymongo.MongoClient(uri)
db = client['test2']
users_collection = db['With_ID_test_2(11.12)']

users_collection_answers = db['With_ID_Answers_2(11.12)']

# Указываем папку с фронтендом, используя относительный путь
app = Flask(__name__, static_folder='dist')

CORS(app, origins=[""])
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
        return redirect('')

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

@app.route('/api/main_months', methods=['POST']) #получение на выходе всех доступных ilichey (объединение в один); Для тебя - Для тебя - отправляешь данные в формате {"password": "BM2is44DFs"} - получаешь все доступные ильичи для пользователя (если у чела 10,11 - то в объединённом ильиче не будет других месяцев)
def get_months():
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

        gett_data = request.get_json()
        if 'password' in gett_data:
            got_password = gett_data['password']
        else:
            return jsonify({'message': 'Нет пароля'}), 401
        
        user = users_collection.find_one({'password': got_password})
        if not user:
            return jsonify({'message': 'Пользователь не найден'}), 404
        
        months_post = user.get('date')
        if isinstance(months_post, list):
            months = months_post
        
        folder_path = os.path.join(app.root_path, 'Sorted_months')
        if not os.path.exists(folder_path):
            return jsonify({'message': f'Папка {folder_path} не найдена'}), 404

        available_months = []
        for month in months:
            # Форматируем название папки с ведущим нулём
            month_folder = month.zfill(2)
            month_folder_path = os.path.join(folder_path, month_folder)
            # Проверяем существует ли папка с таким названием
            if os.path.isdir(month_folder_path):
                available_months.append(month_folder)
        
        if not available_months:
            return jsonify({'message': 'Нет доступных папок для указанных месяцев'}), 404
        
        combined_data = []
        for month in available_months:
            month_folder_path = os.path.join(folder_path, month)
            json_file_path = os.path.join(month_folder_path, 'ilich.json')
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                combined_data.extend(data)
        
        return jsonify(combined_data), 200
        
    else:
        # Если токен не найден, редиректим на страницу логина или возвращаем ошибку
        return  jsonify({'message': 'Неверный токен'}), 401

    
    
@app.route('/api/question_months', methods=['POST']) #мне приходят folder_ID; Для тебя - Для тебя - отправляешь данные в формате {"password": "BM2is44DFs","folder": "40621"} - получаешь содержимое 40621.json
def get_questions():
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
        
        data_folder = request.get_json()
        passwo = data_folder['password']
        folder_id = data_folder['folder']
        user = users_collection.find_one({'password': passwo})
        if not user:
            return jsonify({'message': 'Пользователь не найден'}), 404
        
        months_post = user.get('date')
        if isinstance(months_post, list):
            months_from_bd = months_post
        
        months_folder_path = os.path.join(app.root_path, 'Sorted_months')
        months_from_bd = user.get('date')

        for month_folder in os.listdir(months_folder_path):
            if month_folder in months_from_bd:
                month_folder_path = os.path.join(months_folder_path, month_folder)
                folder_path = os.path.join(month_folder_path, folder_id)
                if os.path.exists(folder_path):
                    json_file_path = os.path.join(folder_path, f'{folder_id}.json')
                    if os.path.exists(json_file_path):
                        with open(json_file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            return jsonify(data), 200

        return jsonify({'message': f'Вам не доступно'}), 403

    else:
        return  jsonify({'message': 'Неверный токен'}), 401

@app.route('/api/question_inside', methods=['POST']) #мне приходят folder_ID и question_ID; Для тебя - отправляешь данные в формате {"password": "BM2is44DFs","folder": "40621","question": "10750575"} - получаешь содержимое 10750575.json
def get_questions_inside():
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
        
        data_folder = request.get_json()
        passwo = data_folder['password']
        folder_id = data_folder['folder']
        quest_id = data_folder['question']
        user = users_collection.find_one({'password': passwo})
        if not user:
            return jsonify({'message': 'Пользователь не найден'}), 404
        
        months_post = user.get('date')
        if isinstance(months_post, list):
            months_from_bd = months_post
        
        months_folder_path = os.path.join(app.root_path, 'Sorted_months')
        months_from_bd = user.get('date')

        for month_folder in os.listdir(months_folder_path):
            if month_folder in months_from_bd:
                month_folder_path = os.path.join(months_folder_path, month_folder)
                folder_path = os.path.join(month_folder_path, folder_id)
                if os.path.exists(folder_path):
                    json_file_path = os.path.join(folder_path, f'{quest_id}.json')
                    if os.path.exists(json_file_path):
                        with open(json_file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            return jsonify(data), 200

        return jsonify({'message': f'Ошибка при исполнении или вам не доступно'}), 403
        
            

    else:
        return  jsonify({'message': 'Неверный токен'}), 401

@app.route('/api/answer_to_bd', methods=['POST']) #принимаю - password(пароль), folder(папку), question(циферки), answer_id (циферки - кодовое для именно этого вопроса) и answer (ответ пользователя именно на этот вопрос)
def answers_to_bd():
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
        
        data_folder = request.get_json()
        passwo = data_folder['password']
        folder_id = data_folder['folder']
        quest_id = data_folder['question']
        answer_id = data_folder['answer_id']
        user_answer = data_folder['answer']
        correct = data_folder['correct']
        user = users_collection.find_one({'password': passwo})
        if not user:
            return jsonify({'message': 'Пользователь не найден'}), 404
        
        # Проверяем, есть ли у пользователя доступ к этому вопросу
        months_post = user.get('date')
        if isinstance(months_post, list):
            months_from_bd = months_post
    
        months_folder_path = os.path.join(app.root_path, 'Sorted_months')
        months_from_bd = user.get('date')

        for month_folder in os.listdir(months_folder_path):
            if month_folder in months_from_bd:
                month_folder_path = os.path.join(months_folder_path, month_folder)
                folder_path = os.path.join(month_folder_path, folder_id)
                if os.path.exists(folder_path):
                    json_file_path = os.path.join(folder_path, f'{quest_id}.json')
                    if os.path.exists(json_file_path):
                        with open(json_file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            questions = data.get('questions', [])
                            for question in questions:
                                if question['id'] == int(answer_id):
                                    # Вопрос найден, записываем ответ
                                    existing_user = users_collection_answers.find_one({
                                        'user_password': passwo
                                    })
                                    if existing_user:
                                        # Проверяем, существует ли уже ответ на этот вопрос
                                        answers = existing_user.get('answers', [])
                                        for answer in answers:
                                            if answer['folder_id'] == folder_id and answer['quest_id'] == quest_id and answer['answer_id'] == answer_id:
                                                # Обновляем существующий ответ
                                                answer['answer'] = user_answer
                                                users_collection_answers.update_one({
                                                    'user_password': passwo
                                                }, {'$set': existing_user})
                                                return jsonify({'message': 'Ответ обновлен'}), 200
                                        # Добавляем новый ответ
                                        answers.append({
                                            'folder_id': folder_id,
                                            'quest_id': quest_id,
                                            'answer_id': answer_id,
                                            'answer': user_answer,
                                            'correct': correct
                                        })
                                        users_collection_answers.update_one({
                                            'user_password': passwo
                                        }, {'$set': existing_user})
                                        return jsonify({'message': 'Ответ добавлен'}), 200
                                    else:
                                        # Создаем новый документ для пользователя
                                        user_data = {
                                            'user_password': passwo,
                                            'answers': [
                                                {
                                                    'folder_id': folder_id,
                                                    'quest_id': quest_id,
                                                    'answer_id': answer_id,
                                                    'answer': user_answer,
                                                    'correct': correct
                                                }
                                            ]
                                        }
                                        users_collection_answers.insert_one(user_data)
                                        return jsonify({'message': 'Ответ записан'}), 200
                            return jsonify({'message': 'Такого вопроса не существует'}), 404
                    return jsonify({'message': 'Такого вопроса не существует'}), 404
        return jsonify({'message': f'Ошибка при исполнении или вам не доступно'}), 403
        
    else:
        return  jsonify({'message': 'Неверный токен'}), 401


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # Проверка: если файл существует в папке 'dist', возвращаем его как статику
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    
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
        return send_from_directory(app.static_folder, 'index.html')

    else:
        # Если токен не найден, редиректим на страницу логина или возвращаем ошибку
        return  send_from_directory(app.static_folder, 'index.html')



def user_search():
    data = request.get_json()
    password = data.get('password')
    user = users_collection.find_one({'password': password})
    
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

if __name__ == '__main__':
    # Для Railway нужно запускать с host='0.0.0.0', чтобы сервер был доступен извне
    app.run(debug=True, host='localhost', port=5000)
