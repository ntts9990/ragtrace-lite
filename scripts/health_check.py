#!/usr/bin/env python3
"""
Health check script for RAGTrace Lite

This script performs comprehensive health checks on the RAGTrace Lite system.
"""

import os
import sys
import json
import sqlite3
import psutil
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple


class HealthChecker:
    """Comprehensive health checker for RAGTrace Lite"""
    
    def __init__(self):
        self.results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": self._get_version(),
            "checks": {}
        }
    
    def _get_version(self) -> str:
        """Get RAGTrace Lite version"""
        try:
            from ragtrace_lite import __version__
            return __version__
        except:
            return "unknown"
    
    def check_database(self) -> Tuple[bool, str]:
        """Check database connectivity and health"""
        try:
            db_path = os.getenv("DATABASE_PATH", "./data/ragtrace_lite.db")
            if not Path(db_path).exists():
                return False, "Database file not found"
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if len(tables) < 2:
                return False, f"Missing tables. Found: {len(tables)}"
            
            # Check recent evaluations
            cursor.execute("""
                SELECT COUNT(*) FROM evaluation_runs 
                WHERE created_at > datetime('now', '-1 day')
            """)
            recent_count = cursor.fetchone()[0]
            
            conn.close()
            return True, f"OK (Recent evaluations: {recent_count})"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def check_llm_api(self, provider: str) -> Tuple[bool, str]:
        """Check LLM API connectivity"""
        try:
            if provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    return False, "API key not configured"
                
                # Simple connectivity check
                url = "https://generativelanguage.googleapis.com/v1beta/models"
                headers = {"x-goog-api-key": api_key}
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    return True, "OK"
                else:
                    return False, f"API returned {response.status_code}"
                    
            elif provider == "hcx":
                api_key = os.getenv("CLOVA_STUDIO_API_KEY")
                if not api_key:
                    return False, "API key not configured"
                
                # HCX doesn't have a simple health endpoint
                # Just check if key exists
                return True, "API key configured"
                
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def check_disk_space(self) -> Tuple[bool, str]:
        """Check available disk space"""
        try:
            usage = psutil.disk_usage('/')
            free_gb = usage.free / (1024 ** 3)
            percent_used = usage.percent
            
            if percent_used > 90:
                return False, f"Critical: {percent_used}% used"
            elif percent_used > 80:
                return True, f"Warning: {percent_used}% used"
            else:
                return True, f"OK ({free_gb:.1f} GB free)"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def check_memory(self) -> Tuple[bool, str]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 ** 2)
            percent_used = memory.percent
            
            if percent_used > 90:
                return False, f"Critical: {percent_used}% used"
            elif percent_used > 80:
                return True, f"Warning: {percent_used}% used"
            else:
                return True, f"OK ({available_mb:.0f} MB available)"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def check_dependencies(self) -> Tuple[bool, str]:
        """Check if all required dependencies are available"""
        try:
            required = [
                "ragas",
                "pandas", 
                "numpy",
                "requests",
                "pydantic"
            ]
            
            missing = []
            for module in required:
                try:
                    __import__(module)
                except ImportError:
                    missing.append(module)
            
            if missing:
                return False, f"Missing: {', '.join(missing)}"
            else:
                return True, "All dependencies available"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        
        # Database check
        db_ok, db_msg = self.check_database()
        self.results["checks"]["database"] = {
            "status": "ok" if db_ok else "error",
            "message": db_msg
        }
        if not db_ok:
            self.results["status"] = "unhealthy"
        
        # LLM API checks
        for provider in ["gemini", "hcx"]:
            api_ok, api_msg = self.check_llm_api(provider)
            self.results["checks"][f"llm_{provider}"] = {
                "status": "ok" if api_ok else "error",
                "message": api_msg
            }
            # Don't mark as unhealthy if just one LLM is down
        
        # System checks
        disk_ok, disk_msg = self.check_disk_space()
        self.results["checks"]["disk_space"] = {
            "status": "ok" if disk_ok else "error",
            "message": disk_msg
        }
        if not disk_ok and "Critical" in disk_msg:
            self.results["status"] = "unhealthy"
        
        memory_ok, memory_msg = self.check_memory()
        self.results["checks"]["memory"] = {
            "status": "ok" if memory_ok else "error",
            "message": memory_msg
        }
        if not memory_ok and "Critical" in memory_msg:
            self.results["status"] = "unhealthy"
        
        # Dependencies check
        deps_ok, deps_msg = self.check_dependencies()
        self.results["checks"]["dependencies"] = {
            "status": "ok" if deps_ok else "error",
            "message": deps_msg
        }
        if not deps_ok:
            self.results["status"] = "unhealthy"
        
        return self.results


def main():
    """Main entry point"""
    checker = HealthChecker()
    results = checker.run_all_checks()
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    if results["status"] == "healthy":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()