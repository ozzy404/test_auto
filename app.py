from flask import Flask, request, jsonify
from flask_cors import CORS
import g4f
import time
import os

app = Flask(__name__)
CORS(app)

# Секретний ключ можна встановити через змінні оточення в Render
API_KEY = os.getenv('API_KEY', 'your_secret_key_here')

@app.route('/')
def home():
    return "Test Helper API is running!"

@app.route('/get_answer', methods=['POST'])
def get_answer():
    # Перевірка API ключа
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        data = request.json
        if not data or 'question' not in data or 'answers' not in data:
            return jsonify({"error": "Missing required data"}), 400

        question = data['question']
        answers = data['answers']
        
        # Формуємо промпт для моделі
        prompt = f"""Питання: {question}
Варіанти відповідей:
{chr(10).join(f'{i+1}. {answer}' for i, answer in enumerate(answers))}

Дай тільки букву правильної відповіді (a, b, c або d) без пояснень."""

        # Додаємо повторні спроби у випадку помилки
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Отримуємо відповідь від моделі
                response = g4f.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    stream=False
                )
                
                # Перевіряємо, чи відповідь є рядком
                if isinstance(response, str):
                    answer_text = response.strip().lower()
                else:
                    answer_text = str(response).strip().lower()
                
                # Знаходимо першу літеру a, b, c або d у відповіді
                for char in answer_text:
                    if char in ['a', 'b', 'c', 'd']:
                        answer_index = ord(char) - ord('a')
                        if 0 <= answer_index < len(answers):
                            return jsonify({"answer": answers[answer_index]})
                
                time.sleep(1)
                continue
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    raise e
        
        return jsonify({"error": "Could not get valid answer after multiple attempts"}), 400
            
    except Exception as e:
        print(f"Error in get_answer: {str(e)}")
        return jsonify({"error": f"API Error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)