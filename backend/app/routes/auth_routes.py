from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if User.find_by_email(data['email']):
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User.create(data)
        access_token = create_access_token(identity=data['email'])
        
        return jsonify({
            'message': 'User created successfully',
            'token': access_token,
            'user': {
                'email': user['email'],
                'name': user['name']
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.find_by_email(data['email'])
        
        if not user or not User.verify_password(user['password'], data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        access_token = create_access_token(identity=data['email'])
        
        return jsonify({
            'message': 'Login successful',
            'token': access_token,
            'user': {
                'email': user['email'],
                'name': user['name']
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user = get_jwt_identity()
    user = User.find_by_email(current_user)
    return jsonify({
        'email': user['email'],
        'name': user['name']
    }), 200