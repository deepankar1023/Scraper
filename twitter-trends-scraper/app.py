from flask import Flask, render_template, jsonify
from utils.scraper import TwitterScraper
from utils.database import MongoDB
from datetime import datetime
import uuid
from bson import ObjectId  # For handling MongoDB ObjectId
from flask.json.provider import DefaultJSONProvider

# Custom JSON Provider for Flask to handle ObjectId and datetime
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Initialize Flask app
app = Flask(__name__)
app.json = CustomJSONProvider(app)

# Initialize TwitterScraper and MongoDB
scraper = TwitterScraper()
db = MongoDB()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape')
def scrape_trends():
    unique_id = str(uuid.uuid4())
    trends = scraper.get_trends()

    if trends:
        data = {
            'unique_id': unique_id,
            'trend1': trends[0] if len(trends) > 0 else None,
            'trend2': trends[1] if len(trends) > 1 else None,
            'trend3': trends[2] if len(trends) > 2 else None,
            'trend4': trends[3] if len(trends) > 3 else None,
            'trend5': trends[4] if len(trends) > 4 else None,
            'timestamp': datetime.now(),
            'ip_address': scraper.current_ip
        }

        # Insert data into MongoDB
        inserted_id = db.insert_trends(data)

        # Add the inserted ID to the response data
        data['inserted_id'] = str(inserted_id)

        return jsonify({'status': 'success', 'data': data})

    return jsonify({'status': 'error', 'message': 'Failed to scrape trends'})

if __name__ == '__main__':
    app.run(debug=True)
