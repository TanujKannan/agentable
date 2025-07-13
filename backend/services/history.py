import sqlite3
import json
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime

class RunHistory:
    """
    Simple SQLite-based history storage for run data.
    Uses in-memory database that wipes on restart.
    """
    
    def __init__(self):
        # Use in-memory database that wipes on restart
        self.db = sqlite3.connect(':memory:', check_same_thread=False)
        self.lock = threading.Lock()
        
        # Create table for storing run history
        self.db.execute('''
            CREATE TABLE runs (
                id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                pipeline_data TEXT,
                result TEXT,
                status TEXT,
                timestamp TEXT,
                duration_seconds INTEGER
            )
        ''')
        self.db.commit()
    
    def save_run(self, run_id: str, prompt: str, pipeline_data: Optional[Dict[str, Any]] = None, 
                 result: Optional[str] = None, status: str = 'running', duration_seconds: Optional[int] = None):
        """Save or update a run in the history"""
        with self.lock:
            pipeline_json = json.dumps(pipeline_data) if pipeline_data else None
            timestamp = datetime.now().isoformat()
            
            # Try to update existing run first
            cursor = self.db.execute('SELECT id FROM runs WHERE id = ?', (run_id,))
            if cursor.fetchone():
                # Update existing run
                self.db.execute('''
                    UPDATE runs 
                    SET pipeline_data = COALESCE(?, pipeline_data),
                        result = COALESCE(?, result),
                        status = ?,
                        duration_seconds = COALESCE(?, duration_seconds)
                    WHERE id = ?
                ''', (pipeline_json, result, status, duration_seconds, run_id))
            else:
                # Insert new run
                self.db.execute('''
                    INSERT INTO runs (id, prompt, pipeline_data, result, status, timestamp, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (run_id, prompt, pipeline_json, result, status, timestamp, duration_seconds))
            
            self.db.commit()
    
    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent runs, most recent first"""
        with self.lock:
            cursor = self.db.execute('''
                SELECT id, prompt, pipeline_data, result, status, timestamp, duration_seconds
                FROM runs 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            runs = []
            for row in cursor.fetchall():
                run_id, prompt, pipeline_json, result, status, timestamp, duration = row
                
                # Parse pipeline data back to dict
                pipeline_data = None
                if pipeline_json:
                    try:
                        pipeline_data = json.loads(pipeline_json)
                    except json.JSONDecodeError:
                        pass
                
                runs.append({
                    'id': run_id,
                    'prompt': prompt,
                    'pipeline_data': pipeline_data,
                    'result': result,
                    'status': status,
                    'timestamp': timestamp,
                    'duration_seconds': duration
                })
            
            return runs
    
    def get_run_by_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific run by ID"""
        with self.lock:
            cursor = self.db.execute('''
                SELECT id, prompt, pipeline_data, result, status, timestamp, duration_seconds
                FROM runs 
                WHERE id = ?
            ''', (run_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            run_id, prompt, pipeline_json, result, status, timestamp, duration = row
            
            # Parse pipeline data back to dict
            pipeline_data = None
            if pipeline_json:
                try:
                    pipeline_data = json.loads(pipeline_json)
                except json.JSONDecodeError:
                    pass
            
            return {
                'id': run_id,
                'prompt': prompt,
                'pipeline_data': pipeline_data,
                'result': result,
                'status': status,
                'timestamp': timestamp,
                'duration_seconds': duration
            }
    
    def clear_history(self):
        """Clear all history (useful for testing)"""
        with self.lock:
            self.db.execute('DELETE FROM runs')
            self.db.commit()

# Global history instance
history = RunHistory()