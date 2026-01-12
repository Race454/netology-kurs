from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///advertisements.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Advertisement(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    owner = db.Column(db.String(100), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'owner': self.owner
        }

with app.app_context():
    db.create_all()

def validate_advertisement_data(data, require_all=True):
    errors = []
    
    if require_all:
        required_fields = ['title', 'description', 'owner']
        for field in required_fields:
            if field not in data:
                errors.append(f"Поле '{field}' обязательно для заполнения")
    
    if 'title' in data and (not data['title'] or len(data['title']) > 100):
        errors.append("Заголовок не может быть пустым и должен быть не длиннее 100 символов")
    
    if 'description' in data and not data['description']:
        errors.append("Описание не может быть пустым")
    
    if 'owner' in data and not data['owner']:
        errors.append("Владелец не может быть пустым")
    
    return errors

@app.route('/api/advertisements', methods=['POST'])
def create_advertisement():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Необхдимо предоставить данные в формате JSON'}), 400
    
    errors = validate_advertisement_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    advertisement = Advertisement(
        title=data['title'],
        description=data['description'],
        owner=data['owner']
    )
    
    db.session.add(advertisement)
    db.session.commit()
    
    return jsonify({
        'message': 'Объявление успешно создано',
        'advertisement': advertisement.to_dict()
    }), 201

@app.route('/api/advertisements', methods=['GET'])
@app.route('/api/advertisements/<string:ad_id>', methods=['GET'])
def get_advertisement(ad_id=None):
    if ad_id:
        advertisement = Advertisement.query.get(ad_id)
        
        if not advertisement:
            return jsonify({'error': 'Объявление не найдено'}), 404
        
        return jsonify(advertisement.to_dict()), 200
    else:
        query = Advertisement.query
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        advertisements = query.paginate(page=page, per_page=per_page, error_out=False)
        
        result = {
            'advertisements': [ad.to_dict() for ad in advertisements.items],
            'total': advertisements.total,
            'page': page,
            'per_page': per_page,
            'pages': advertisements.pages
        }
        
        return jsonify(result), 200

@app.route('/api/advertisements/<string:ad_id>', methods=['PUT'])
def update_advertisement(ad_id):
    advertisement = Advertisement.query.get(ad_id)
    
    if not advertisement:
        return jsonify({'error': 'Объявление не найдено'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Необходимо предоставить данные в формате JSON'}), 400
    
    errors = validate_advertisement_data(data, require_all=False)
    if errors:
        return jsonify({'errors': errors}), 400
    
    if 'title' in data:
        advertisement.title = data['title']
    
    if 'description' in data:
        advertisement.description = data['description']
    
    if 'owner' in data:
        advertisement.owner = data['owner']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Объявление успешно обновлено',
        'advertisement': advertisement.to_dict()
    }), 200

# PATCH 
@app.route('/api/advertisements/<string:ad_id>', methods=['PATCH'])
def partial_update_advertisement(ad_id):
    advertisement = Advertisement.query.get(ad_id)
    
    if not advertisement:
        return jsonify({'error': 'Объявление не найдено'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Необходимо предоставить данные в формате JSON'}), 400
    
    errors = validate_advertisement_data(data, require_all=False)
    if errors:
        return jsonify({'errors': errors}), 400
    
    if 'title' in data:
        advertisement.title = data['title']
    
    if 'description' in data:
        advertisement.description = data['description']
    
    if 'owner' in data:
        advertisement.owner = data['owner']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Объявление успешно обновлено',
        'advertisement': advertisement.to_dict()
    }), 200

# DELETE
@app.route('/api/advertisements/<string:ad_id>', methods=['DELETE'])
def delete_advertisement(ad_id):
    advertisement = Advertisement.query.get(ad_id)
    
    if not advertisement:
        return jsonify({'error': 'Объявление не найдено'}), 404
    
    db.session.delete(advertisement)
    db.session.commit()
    
    return jsonify({'message': 'Объявление успешно удалено'}), 200

@app.route('/')
def index():
    return jsonify({
        'message': 'Привет мир!',
        'endpoints': {
            'GET /api/advertisements': 'Получить все объявления',
            'GET /api/advertisements/<id>': 'Получить конкретное объявление',
            'POST /api/advertisements': 'Создать новое объявление',
            'PUT /api/advertisements/<id>': 'Полное обновление объявления',
            'PATCH /api/advertisements/<id>': 'Частичное обновление объявления',
            'DELETE /api/advertisements/<id>': 'Удалить объявление'
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)