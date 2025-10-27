from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .config.database import init_db

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['JWT_SECRET_KEY'] = 'your-secret-key'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    JWTManager(app)
    init_db(app)
    
    # Register blueprints
    from .routes import auth_routes, transaction_routes, ai_routes, budget_routes, goal_routes, bank_routes
    
    app.register_blueprint(auth_routes.bp, url_prefix='/api/auth')
    app.register_blueprint(transaction_routes.bp, url_prefix='/api/transactions')
    app.register_blueprint(ai_routes.bp, url_prefix='/api/ai')
    app.register_blueprint(budget_routes.bp, url_prefix='/api/budgets')
    app.register_blueprint(goal_routes.bp, url_prefix='/api/goals')
    app.register_blueprint(bank_routes.bp, url_prefix='/api/banks')
    
    @app.route('/api/health')
    def health():
        return {'status': 'healthy', 'message': 'Financial Planning Assistant API'}
    
    return app