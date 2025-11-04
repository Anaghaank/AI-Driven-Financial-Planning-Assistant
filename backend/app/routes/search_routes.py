from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.models.bank import Bank
from datetime import datetime, timedelta
from dateutil import parser
import re

search_bp = Blueprint('search', __name__)

@search_bp.route('/api/transactions/search', methods=['GET'])
@jwt_required()
def search_transactions():
    """
    Advanced transaction search with multiple filters
    
    Query Parameters:
    - q: Search query (text search in description)
    - category: Filter by category (can be multiple, comma-separated)
    - type: income or expense
    - bank_id: Filter by bank account
    - min_amount: Minimum amount
    - max_amount: Maximum amount
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - tags: Filter by tags (comma-separated)
    - sort_by: date, amount, category (default: date)
    - sort_order: asc, desc (default: desc)
    - page: Page number (default: 1)
    - limit: Results per page (default: 50)
    """
    try:
        current_user = get_jwt_identity()
        
        # Build MongoDB query
        query = {'user_id': current_user}
        
        # Text search in description
        search_text = request.args.get('q', '').strip()
        if search_text:
            # Case-insensitive regex search
            query['description'] = {'$regex': search_text, '$options': 'i'}
        
        # Category filter (support multiple categories)
        categories = request.args.get('category', '').strip()
        if categories:
            category_list = [c.strip() for c in categories.split(',')]
            query['category'] = {'$in': category_list}
        
        # Transaction type filter
        txn_type = request.args.get('type', '').strip()
        if txn_type in ['income', 'expense']:
            query['type'] = txn_type
        
        # Bank account filter
        bank_id = request.args.get('bank_id', '').strip()
        if bank_id:
            query['bank_id'] = bank_id
        
        # Amount range filter
        min_amount = request.args.get('min_amount', '').strip()
        max_amount = request.args.get('max_amount', '').strip()
        
        if min_amount or max_amount:
            query['amount'] = {}
            if min_amount:
                try:
                    query['amount']['$gte'] = float(min_amount)
                except ValueError:
                    pass
            if max_amount:
                try:
                    query['amount']['$lte'] = float(max_amount)
                except ValueError:
                    pass
        
        # Date range filter
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                try:
                    start = parser.parse(start_date)
                    query['date']['$gte'] = start
                except:
                    pass
            if end_date:
                try:
                    end = parser.parse(end_date)
                    # Include the entire end date
                    end = end.replace(hour=23, minute=59, second=59)
                    query['date']['$lte'] = end
                except:
                    pass
        
        # Tags filter
        tags = request.args.get('tags', '').strip()
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            query['tags'] = {'$in': tag_list}
        
        # Sorting
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'desc')
        
        sort_field = sort_by if sort_by in ['date', 'amount', 'category'] else 'date'
        sort_direction = -1 if sort_order == 'desc' else 1
        
        # Pagination
        try:
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 50))
        except ValueError:
            page = 1
            limit = 50
        
        # Ensure reasonable limits
        page = max(1, page)
        limit = min(max(1, limit), 100)  # Max 100 per page
        
        skip = (page - 1) * limit
        
        # Execute query
        from app.config.database import mongo
        
        # Get total count
        total_count = mongo.db.transactions.count_documents(query)
        
        # Get transactions
        transactions = list(
            mongo.db.transactions.find(query)
            .sort(sort_field, sort_direction)
            .skip(skip)
            .limit(limit)
        )
        
        # Format results
        for txn in transactions:
            txn['_id'] = str(txn['_id'])
            if isinstance(txn.get('date'), datetime):
                txn['date'] = txn['date'].isoformat()
            if isinstance(txn.get('created_at'), datetime):
                txn['created_at'] = txn['created_at'].isoformat()
            if 'bank_id' in txn and txn['bank_id']:
                txn['bank_id'] = str(txn['bank_id'])
        
        # Calculate summary
        summary = calculate_search_summary(transactions)
        
        # Pagination info
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'transactions': transactions,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'per_page': limit,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'summary': summary,
            'filters_applied': {
                'search_query': search_text if search_text else None,
                'categories': category_list if categories else None,
                'type': txn_type if txn_type else None,
                'bank_id': bank_id if bank_id else None,
                'amount_range': {
                    'min': float(min_amount) if min_amount else None,
                    'max': float(max_amount) if max_amount else None
                } if min_amount or max_amount else None,
                'date_range': {
                    'start': start_date if start_date else None,
                    'end': end_date if end_date else None
                } if start_date or end_date else None
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def calculate_search_summary(transactions):
    """Calculate summary statistics for search results"""
    if not transactions:
        return {
            'total_income': 0,
            'total_expense': 0,
            'net': 0,
            'count': 0,
            'average_transaction': 0
        }
    
    total_income = sum(t['amount'] for t in transactions if t.get('type') == 'income')
    total_expense = sum(t['amount'] for t in transactions if t.get('type') == 'expense')
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'net': total_income - total_expense,
        'count': len(transactions),
        'average_transaction': (total_income + total_expense) / len(transactions) if transactions else 0
    }


@search_bp.route('/api/transactions/quick-filters', methods=['GET'])
@jwt_required()
def get_quick_filters():
    """Get predefined quick filters"""
    current_user = get_jwt_identity()
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    quick_filters = {
        'today': {
            'name': 'Today',
            'start_date': today.isoformat(),
            'end_date': datetime.now().isoformat()
        },
        'yesterday': {
            'name': 'Yesterday',
            'start_date': (today - timedelta(days=1)).isoformat(),
            'end_date': today.isoformat()
        },
        'this_week': {
            'name': 'This Week',
            'start_date': (today - timedelta(days=today.weekday())).isoformat(),
            'end_date': datetime.now().isoformat()
        },
        'this_month': {
            'name': 'This Month',
            'start_date': today.replace(day=1).isoformat(),
            'end_date': datetime.now().isoformat()
        },
        'last_month': {
            'name': 'Last Month',
            'start_date': (today.replace(day=1) - timedelta(days=1)).replace(day=1).isoformat(),
            'end_date': today.replace(day=1).isoformat()
        },
        'last_30_days': {
            'name': 'Last 30 Days',
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': datetime.now().isoformat()
        },
        'last_90_days': {
            'name': 'Last 90 Days',
            'start_date': (today - timedelta(days=90)).isoformat(),
            'end_date': datetime.now().isoformat()
        },
        'this_year': {
            'name': 'This Year',
            'start_date': today.replace(month=1, day=1).isoformat(),
            'end_date': datetime.now().isoformat()
        }
    }
    
    return jsonify({
        'success': True,
        'quick_filters': quick_filters
    }), 200


@search_bp.route('/api/transactions/suggestions', methods=['GET'])
@jwt_required()
def get_search_suggestions():
    """Get search suggestions based on user's transaction history"""
    try:
        current_user = get_jwt_identity()
        query_text = request.args.get('q', '').strip()
        
        if not query_text or len(query_text) < 2:
            return jsonify({
                'success': True,
                'suggestions': []
            }), 200
        
        from app.config.database import mongo
        
        # Find matching descriptions
        descriptions = mongo.db.transactions.aggregate([
            {
                '$match': {
                    'user_id': current_user,
                    'description': {'$regex': query_text, '$options': 'i'}
                }
            },
            {
                '$group': {
                    '_id': '$description',
                    'count': {'$sum': 1},
                    'total_amount': {'$sum': '$amount'},
                    'category': {'$first': '$category'}
                }
            },
            {
                '$sort': {'count': -1}
            },
            {
                '$limit': 10
            }
        ])
        
        suggestions = []
        for item in descriptions:
            suggestions.append({
                'text': item['_id'],
                'count': item['count'],
                'category': item.get('category', 'Other'),
                'avg_amount': item['total_amount'] / item['count']
            })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@search_bp.route('/api/transactions/saved-searches', methods=['GET'])
@jwt_required()
def get_saved_searches():
    """Get user's saved search queries"""
    try:
        current_user = get_jwt_identity()
        
        from app.config.database import mongo
        saved_searches = list(mongo.db.saved_searches.find({'user_id': current_user}))
        
        for search in saved_searches:
            search['_id'] = str(search['_id'])
            if isinstance(search.get('created_at'), datetime):
                search['created_at'] = search['created_at'].isoformat()
        
        return jsonify({
            'success': True,
            'saved_searches': saved_searches
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@search_bp.route('/api/transactions/saved-searches', methods=['POST'])
@jwt_required()
def save_search():
    """Save a search query for later use"""
    try:
        current_user = get_jwt_identity()
        data = request.json
        
        if not data.get('name'):
            return jsonify({'error': 'Search name is required'}), 400
        
        from app.config.database import mongo
        
        saved_search = {
            'user_id': current_user,
            'name': data['name'],
            'filters': data.get('filters', {}),
            'created_at': datetime.utcnow()
        }
        
        result = mongo.db.saved_searches.insert_one(saved_search)
        saved_search['_id'] = str(result.inserted_id)
        
        return jsonify({
            'success': True,
            'message': 'Search saved successfully',
            'saved_search': saved_search
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@search_bp.route('/api/transactions/saved-searches/<search_id>', methods=['DELETE'])
@jwt_required()
def delete_saved_search(search_id):
    """Delete a saved search"""
    try:
        current_user = get_jwt_identity()
        
        from app.config.database import mongo
        from bson import ObjectId
        
        result = mongo.db.saved_searches.delete_one({
            '_id': ObjectId(search_id),
            'user_id': current_user
        })
        
        if result.deleted_count > 0:
            return jsonify({
                'success': True,
                'message': 'Saved search deleted successfully'
            }), 200
        else:
            return jsonify({'error': 'Saved search not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500