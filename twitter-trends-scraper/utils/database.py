# utils/database.py

from pymongo import MongoClient
from datetime import datetime
import logging
from config.config import MONGODB_URI, DB_NAME

class MongoDB:
    """
    Handler for MongoDB operations for storing Twitter trends
    """
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.setup_logging()
        try:
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[DB_NAME]
            self.collection = self.db['config']
            self.logger.info("Successfully connected to MongoDB")
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('MongoDB')
    
    def insert_trends(self, data):
        """
        Insert trend data into MongoDB
        
        Args:
            data: Dictionary containing trend data with fields:
                - unique_id: Unique identifier for the scrape
                - trend1-5: The trending topics
                - timestamp: When the data was collected
                - ip_address: IP used for scraping
        """
        try:
            # Add metadata
            data['created_at'] = datetime.now()
            
            # Insert document
            result = self.collection.insert_one(data)
            self.logger.info(f"Successfully inserted trends with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            self.logger.error(f"Failed to insert trends: {str(e)}")
            raise
    
    def get_latest_trends(self, limit=10):
        """
        Get the most recent trend entries
        
        Args:
            limit: Number of entries to return
        Returns:
            List of trend documents
        """
        try:
            return list(self.collection
                       .find({})
                       .sort('created_at', -1)
                       .limit(limit))
        except Exception as e:
            self.logger.error(f"Failed to fetch latest trends: {str(e)}")
            raise
    
    def get_trends_by_id(self, unique_id):
        """
        Get trend entry by its unique ID
        
        Args:
            unique_id: The unique identifier of the scrape
        Returns:
            Trend document or None if not found
        """
        try:
            return self.collection.find_one({'unique_id': unique_id})
        except Exception as e:
            self.logger.error(f"Failed to fetch trends by ID: {str(e)}")
            raise

    def cleanup_old_records(self, days=30):
        """
        Remove records older than specified days
        
        Args:
            days: Number of days to keep records for
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            result = self.collection.delete_many({
                'created_at': {'$lt': cutoff_date}
            })
            self.logger.info(f"Removed {result.deleted_count} old records")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old records: {str(e)}")
            raise

if __name__ == '__main__':
    # Test database connection and operations
    try:
        db = MongoDB()
        print("Successfully connected to MongoDB")
        
        # Test insert
        test_data = {
            'unique_id': 'test-123',
            'trend1': 'Test Trend 1',
            'trend2': 'Test Trend 2',
            'trend3': 'Test Trend 3',
            'trend4': 'Test Trend 4',
            'trend5': 'Test Trend 5',
            'timestamp': datetime.now(),
            'ip_address': '127.0.0.1'
        }
        db.insert_trends(test_data)
        print("Successfully inserted test data")
        
    except Exception as e:
        print(f"Error: {str(e)}")