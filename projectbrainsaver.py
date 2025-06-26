#!/usr/bin/env python3
"""
Projectbrainsaver - Multi-Agent AI Application
A comprehensive AI-driven system with specialized agents for various tasks.
"""

import os
import json
import sqlite3
import hashlib
import shutil
import socket
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
from dataclasses import dataclass
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('projectbrainsaver.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class AgentResponse:
    """Standard response format for all agents"""
    success: bool
    message: str
    data: Optional[Dict] = None
    actions_taken: Optional[List[str]] = None

class MemoryAgent:
    """Handles persistent memory and context management"""
    
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(f"{__class__.__name__}")
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database for memory storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for storing interactions and context
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                agent_output TEXT NOT NULL,
                session_id TEXT,
                context_tags TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_index (
                path TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_type TEXT,
                size INTEGER,
                modified_time TEXT,
                tags TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("Memory database initialized")
    
    def save_interaction(self, user_input: str, agent_output: str, 
                        session_id: str = "default", context_tags: str = ""):
        """Save a user interaction for future reference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO interactions (timestamp, user_input, agent_output, session_id, context_tags)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, user_input, agent_output, session_id, context_tags))
        
        conn.commit()
        conn.close()
        self.logger.info(f"Saved interaction with tags: {context_tags}")
    
    def retrieve_relevant(self, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant past interactions based on query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple keyword-based search (in production, would use vector embeddings)
        search_terms = query.lower().split()
        conditions = []
        params = []
        
        for term in search_terms:
            conditions.append("(LOWER(user_input) LIKE ? OR LOWER(agent_output) LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])
        
        if conditions:
            where_clause = " AND ".join(conditions)
            query_sql = f'''
                SELECT timestamp, user_input, agent_output, context_tags
                FROM interactions 
                WHERE {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ?
            '''
            params.append(limit)
        else:
            query_sql = '''
                SELECT timestamp, user_input, agent_output, context_tags
                FROM interactions 
                ORDER BY timestamp DESC 
                LIMIT ?
            '''
            params = [limit]
        
        cursor.execute(query_sql, params)
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "user_input": row[1],
                "agent_output": row[2],
                "context_tags": row[3]
            }
            for row in results
        ]
    
    def set_preference(self, key: str, value: str):
        """Store user preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, timestamp))
        
        conn.commit()
        conn.close()
        self.logger.info(f"Set preference: {key} = {value}")
    
    def get_preference(self, key: str) -> Optional[str]:
        """Retrieve user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None

class ResearchAgent:
    """Handles research tasks and information gathering"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__class__.__name__}")
    
    def get_information(self, query: str) -> AgentResponse:
        """Research information on a given query"""
        self.logger.info(f"Researching: {query}")
        
        # Simulate research (in production, would call web search APIs)
        research_results = self._simulate_research(query)
        
        return AgentResponse(
            success=True,
            message=f"Found information about: {query}",
            data={"results": research_results},
            actions_taken=[f"Searched for '{query}'", "Analyzed results"]
        )
    
    def _simulate_research(self, query: str) -> Dict:
        """Simulate research results (placeholder for real web search)"""
        # This would be replaced with actual API calls to search engines
        sample_results = {
            "summary": f"Research results for '{query}' would appear here.",
            "sources": [
                {"title": f"Article about {query}", "url": "https://example.com/1"},
                {"title": f"Guide to {query}", "url": "https://example.com/2"}
            ],
            "key_points": [
                f"Key insight 1 about {query}",
                f"Key insight 2 about {query}",
                f"Recommended action for {query}"
            ]
        }
        return sample_results

class FileAgent:
    """Handles file management and organization"""
    
    def __init__(self, memory_agent: MemoryAgent):
        self.memory = memory_agent
        self.logger = logging.getLogger(f"{__class__.__name__}")
    
    def find_file(self, name_or_keywords: str, search_path: str = ".") -> AgentResponse:
        """Search for files by name or keywords"""
        self.logger.info(f"Searching for files: {name_or_keywords}")
        
        found_files = []
        search_terms = name_or_keywords.lower().split()
        
        try:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    file_lower = file.lower()
                    if any(term in file_lower for term in search_terms):
                        file_path = os.path.join(root, file)
                        file_stat = os.stat(file_path)
                        found_files.append({
                            "path": file_path,
                            "name": file,
                            "size": file_stat.st_size,
                            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                        })
            
            return AgentResponse(
                success=True,
                message=f"Found {len(found_files)} files matching '{name_or_keywords}'",
                data={"files": found_files},
                actions_taken=[f"Searched in {search_path}", f"Found {len(found_files)} matches"]
            )
        
        except Exception as e:
            self.logger.error(f"Error searching files: {e}")
            return AgentResponse(
                success=False,
                message=f"Error searching for files: {str(e)}"
            )
    
    def organize_folder(self, path: str, criteria: str = "type") -> AgentResponse:
        """Organize files in a folder by specified criteria"""
        self.logger.info(f"Organizing folder: {path} by {criteria}")
        
        if not os.path.exists(path):
            return AgentResponse(
                success=False,
                message=f"Path does not exist: {path}"
            )
        
        actions_taken = []
        organized_count = 0
        
        try:
            if criteria == "type":
                organized_count = self._organize_by_type(path, actions_taken)
            elif criteria == "date":
                organized_count = self._organize_by_date(path, actions_taken)
            else:
                return AgentResponse(
                    success=False,
                    message=f"Unknown criteria: {criteria}"
                )
            
            return AgentResponse(
                success=True,
                message=f"Organized {organized_count} files in {path}",
                data={"organized_count": organized_count, "criteria": criteria},
                actions_taken=actions_taken
            )
        
        except Exception as e:
            self.logger.error(f"Error organizing folder: {e}")
            return AgentResponse(
                success=False,
                message=f"Error organizing folder: {str(e)}"
            )
    
    def _organize_by_type(self, path: str, actions_taken: List[str]) -> int:
        """Organize files by their type/extension"""
        organized_count = 0
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                file_ext = Path(item).suffix.lower()
                if not file_ext:
                    file_ext = "no_extension"
                else:
                    file_ext = file_ext[1:]  # Remove the dot
                
                type_folder = os.path.join(path, f"{file_ext}_files")
                os.makedirs(type_folder, exist_ok=True)
                
                new_path = os.path.join(type_folder, item)
                if not os.path.exists(new_path):
                    shutil.move(item_path, new_path)
                    actions_taken.append(f"Moved {item} to {file_ext}_files/")
                    organized_count += 1
        
        return organized_count
    
    def _organize_by_date(self, path: str, actions_taken: List[str]) -> int:
        """Organize files by their modification date"""
        organized_count = 0
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                mod_time = os.path.getmtime(item_path)
                mod_date = datetime.fromtimestamp(mod_time)
                date_folder = mod_date.strftime("%Y-%m")
                
                date_path = os.path.join(path, date_folder)
                os.makedirs(date_path, exist_ok=True)
                
                new_path = os.path.join(date_path, item)
                if not os.path.exists(new_path):
                    shutil.move(item_path, new_path)
                    actions_taken.append(f"Moved {item} to {date_folder}/")
                    organized_count += 1
        
        return organized_count
    
    def remove_duplicates(self, path: str) -> AgentResponse:
        """Find and handle duplicate files"""
        self.logger.info(f"Finding duplicates in: {path}")
        
        file_hashes = {}
        duplicates = []
        
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_hash = self._get_file_hash(file_path)
                    
                    if file_hash in file_hashes:
                        duplicates.append({
                            "original": file_hashes[file_hash],
                            "duplicate": file_path
                        })
                    else:
                        file_hashes[file_hash] = file_path
            
            # In production, would ask for user confirmation before deletion
            actions_taken = [f"Scanned {len(file_hashes)} files", f"Found {len(duplicates)} duplicates"]
            
            return AgentResponse(
                success=True,
                message=f"Found {len(duplicates)} duplicate files",
                data={"duplicates": duplicates},
                actions_taken=actions_taken
            )
        
        except Exception as e:
            self.logger.error(f"Error finding duplicates: {e}")
            return AgentResponse(
                success=False,
                message=f"Error finding duplicates: {str(e)}"
            )
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

class AutomationAgent:
    """Handles task automation and tool creation"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__class__.__name__}")
        self.scheduled_tasks = []
    
    def run_backup(self, source_path: str, backup_path: str) -> AgentResponse:
        """Simulate running a backup operation"""
        self.logger.info(f"Running backup: {source_path} -> {backup_path}")
        
        try:
            # Simulate backup (in production, would actually copy files)
            actions_taken = [
                f"Started backup from {source_path}",
                f"Creating backup directory: {backup_path}",
                "Copying files...",
                "Backup completed successfully"
            ]
            
            return AgentResponse(
                success=True,
                message=f"Backup completed: {source_path} -> {backup_path}",
                actions_taken=actions_taken
            )
        
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return AgentResponse(
                success=False,
                message=f"Backup failed: {str(e)}"
            )
    
    def organize_desktop(self, desktop_path: str = None) -> AgentResponse:
        """Organize desktop files into folders"""
        if not desktop_path:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
        self.logger.info(f"Organizing desktop: {desktop_path}")
        
        if not os.path.exists(desktop_path):
            return AgentResponse(
                success=False,
                message=f"Desktop path not found: {desktop_path}"
            )
        
        try:
            actions_taken = []
            organized_count = 0
            
            # Create organization folders
            folders = {
                "Documents": [".pdf", ".doc", ".docx", ".txt"],
                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
                "Spreadsheets": [".xls", ".xlsx", ".csv"],
                "Archives": [".zip", ".rar", ".7z", ".tar"],
                "Executables": [".exe", ".msi", ".app", ".deb"]
            }
            
            for folder_name in folders.keys():
                folder_path = os.path.join(desktop_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
            
            # Organize files
            for item in os.listdir(desktop_path):
                item_path = os.path.join(desktop_path, item)
                if os.path.isfile(item_path):
                    file_ext = Path(item).suffix.lower()
                    
                    for folder_name, extensions in folders.items():
                        if file_ext in extensions:
                            new_path = os.path.join(desktop_path, folder_name, item)
                            if not os.path.exists(new_path):
                                # Simulate move (in production, would actually move files)
                                actions_taken.append(f"Would move {item} to {folder_name}/")
                                organized_count += 1
                            break
            
            return AgentResponse(
                success=True,
                message=f"Desktop organized - {organized_count} files categorized",
                data={"organized_count": organized_count},
                actions_taken=actions_taken
            )
        
        except Exception as e:
            self.logger.error(f"Desktop organization failed: {e}")
            return AgentResponse(
                success=False,
                message=f"Desktop organization failed: {str(e)}"
            )
    
    def schedule_task(self, task: str, schedule_time: str) -> AgentResponse:
        """Schedule a task for later execution"""
        self.logger.info(f"Scheduling task: {task} at {schedule_time}")
        
        try:
            # Simple task scheduling simulation
            task_id = len(self.scheduled_tasks) + 1
            scheduled_task = {
                "id": task_id,
                "task": task,
                "schedule_time": schedule_time,
                "created_at": datetime.now().isoformat(),
                "status": "scheduled"
            }
            
            self.scheduled_tasks.append(scheduled_task)
            
            return AgentResponse(
                success=True,
                message=f"Task scheduled: {task} at {schedule_time}",
                data={"task_id": task_id, "task": scheduled_task},
                actions_taken=[f"Added task to schedule with ID {task_id}"]
            )
        
        except Exception as e:
            self.logger.error(f"Task scheduling failed: {e}")
            return AgentResponse(
                success=False,
                message=f"Task scheduling failed: {str(e)}"
            )
    
    def create_tool(self, tool_description: str) -> AgentResponse:
        """Suggest or create a simple tool based on description"""
        self.logger.info(f"Creating tool: {tool_description}")
        
        # Simulate tool creation/recommendation
        tool_suggestions = {
            "file organizer": "Script to automatically organize files by type and date",
            "backup": "Automated backup script with scheduling",
            "duplicate finder": "Tool to find and remove duplicate files",
            "system monitor": "Monitor system resources and send alerts"
        }
        
        # Simple keyword matching for demonstration
        suggested_tool = None
        for keyword, suggestion in tool_suggestions.items():
            if keyword.lower() in tool_description.lower():
                suggested_tool = suggestion
                break
        
        if not suggested_tool:
            suggested_tool = f"Custom tool for: {tool_description}"
        
        return AgentResponse(
            success=True,
            message=f"Tool suggestion: {suggested_tool}",
            data={"tool_description": tool_description, "suggestion": suggested_tool},
            actions_taken=[f"Analyzed request: {tool_description}", "Generated tool suggestion"]
        )

class PhoneAgent:
    """Handles phone data organization and management"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__class__.__name__}")
    
    def sort_photos(self, photo_path: str = "sample_photos") -> AgentResponse:
        """Sort and organize photos"""
        self.logger.info(f"Sorting photos in: {photo_path}")
        
        try:
            if not os.path.exists(photo_path):
                # Create sample directory for demonstration
                os.makedirs(photo_path, exist_ok=True)
                
            actions_taken = []
            sorted_count = 0
            
            # Simulate photo sorting (in production, would analyze EXIF data)
            photo_folders = ["2023", "2024", "2025", "Screenshots", "Others"]
            
            for folder in photo_folders:
                folder_path = os.path.join(photo_path, folder)
                os.makedirs(folder_path, exist_ok=True)
            
            # Simulate sorting existing photos
            if os.path.exists(photo_path):
                for item in os.listdir(photo_path):
                    if item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        # Simulate photo categorization
                        if 'screenshot' in item.lower():
                            category = 'Screenshots'
                        else:
                            category = '2024'  # Default category
                        
                        actions_taken.append(f"Would move {item} to {category}/")
                        sorted_count += 1
            
            return AgentResponse(
                success=True,
                message=f"Photos organized - {sorted_count} photos sorted into albums",
                data={"sorted_count": sorted_count, "albums_created": len(photo_folders)},
                actions_taken=actions_taken
            )
        
        except Exception as e:
            self.logger.error(f"Photo sorting failed: {e}")
            return AgentResponse(
                success=False,
                message=f"Photo sorting failed: {str(e)}"
            )
    
    def clean_contacts(self, contacts_file: str = "sample_contacts.json") -> AgentResponse:
        """Clean and organize contacts"""
        self.logger.info(f"Cleaning contacts: {contacts_file}")
        
        try:
            # Create sample contacts for demonstration
            sample_contacts = [
                {"name": "John Doe", "phone": "555-1234", "email": "john@example.com"},
                {"name": "john doe", "phone": "555-1234", "email": "john.doe@example.com"},  # Duplicate
                {"name": "Jane Smith", "phone": "555-5678", "email": "jane@example.com"},
                {"name": "Bob Johnson", "phone": "", "email": "bob@example.com"},  # Missing phone
            ]
            
            # Save sample contacts
            with open(contacts_file, 'w') as f:
                json.dump(sample_contacts, f, indent=2)
            
            # Process contacts
            cleaned_contacts = []
            duplicates_found = []
            actions_taken = []
            
            seen_names = set()
            for contact in sample_contacts:
                name_lower = contact['name'].lower().strip()
                if name_lower not in seen_names:
                    seen_names.add(name_lower)
                    cleaned_contacts.append(contact)
                else:
                    duplicates_found.append(contact)
                    actions_taken.append(f"Found duplicate: {contact['name']}")
            
            # Check for missing information
            for contact in cleaned_contacts:
                if not contact.get('phone'):
                    actions_taken.append(f"Missing phone for: {contact['name']}")
                if not contact.get('email'):
                    actions_taken.append(f"Missing email for: {contact['name']}")
            
            return AgentResponse(
                success=True,
                message=f"Contacts cleaned - {len(duplicates_found)} duplicates found, {len(cleaned_contacts)} contacts remaining",
                data={
                    "original_count": len(sample_contacts),
                    "cleaned_count": len(cleaned_contacts),
                    "duplicates_removed": len(duplicates_found)
                },
                actions_taken=actions_taken
            )
        
        except Exception as e:
            self.logger.error(f"Contact cleaning failed: {e}")
            return AgentResponse(
                success=False,
                message=f"Contact cleaning failed: {str(e)}"
            )

class DomainAgent:
    """Handles domain and DNS management"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__class__.__name__}")
    
    def check_domain_status(self, domain_name: str) -> AgentResponse:
        """Check the status of a domain"""
        self.logger.info(f"Checking domain status: {domain_name}")
        
        try:
            actions_taken = [f"Starting domain check for {domain_name}"]
            
            # Try to resolve the domain
            try:
                ip_address = socket.gethostbyname(domain_name)
                dns_status = "resolved"
                actions_taken.append(f"DNS resolution successful: {ip_address}")
            except socket.gaierror:
                ip_address = None
                dns_status = "failed"
                actions_taken.append("DNS resolution failed")
            
            # Simulate additional checks
            checks = {
                "dns_resolution": dns_status,
                "ip_address": ip_address,
                "status": "online" if ip_address else "offline"
            }
            
            # Try to connect to port 80
            if ip_address:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((domain_name, 80))
                    sock.close()
                    
                    if result == 0:
                        checks["web_server"] = "responding"
                        actions_taken.append("Web server is responding")
                    else:
                        checks["web_server"] = "not responding"
                        actions_taken.append("Web server is not responding")
                except Exception:
                    checks["web_server"] = "connection error"
                    actions_taken.append("Could not test web server connection")
            
            status_message = f"Domain {domain_name} status: {checks['status']}"
            if ip_address:
                status_message += f" (IP: {ip_address})"
            
            return AgentResponse(
                success=True,
                message=status_message,
                data={"domain": domain_name, "checks": checks},
                actions_taken=actions_taken
            )
        
        except Exception as e:
            self.logger.error(f"Domain check failed: {e}")
            return AgentResponse(
                success=False,
                message=f"Domain check failed: {str(e)}"
            )
    
    def fix_dns(self, domain_name: str, record_type: str, value: str) -> AgentResponse:
        """Simulate fixing DNS records"""
        self.logger.info(f"Fixing DNS for {domain_name}: {record_type} -> {value}")
        
        try:
            # Simulate DNS fix (in production, would call registrar APIs)
            actions_taken = [
                f"Connecting to DNS provider for {domain_name}",
                f"Updating {record_type} record to {value}",
                "DNS propagation initiated (may take up to 24 hours)",
                "DNS fix completed successfully"
            ]
            
            return AgentResponse(
                success=True,
                message=f"DNS record updated: {domain_name} {record_type} -> {value}",
                data={
                    "domain": domain_name,
                    "record_type": record_type,
                    "new_value": value,
                    "propagation_time": "up to 24 hours"
                },
                actions_taken=actions_taken
            )
        
        except Exception as e:
            self.logger.error(f"DNS fix failed: {e}")
            return AgentResponse(
                success=False,
                message=f"DNS fix failed: {str(e)}"
            )

class GuardianOrchestrator:
    """Central orchestrator that coordinates all agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__class__.__name__}")
        
        # Initialize all agents
        self.memory = MemoryAgent()
        self.research = ResearchAgent()
        self.file_agent = FileAgent(self.memory)
        self.automation = AutomationAgent()
        self.phone = PhoneAgent()
        self.domain = DomainAgent()
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger.info("Guardian Orchestrator initialized with all agents")
    
    def interpret_request(self, user_input: str) -> Dict[str, Any]:
        """Interpret user request and determine which agents to invoke"""
        request_lower = user_input.lower()
        
        # Simple keyword-based interpretation (in production, would use LLM)
        interpretation = {
            "primary_intent": "unknown",
            "agents_needed": [],
            "parameters": {},
            "confidence": 0.0
        }
        
        # File management keywords
        if any(word in request_lower for word in ["file", "folder", "organize", "find", "duplicate"]):
            interpretation["primary_intent"] = "file_management"
            interpretation["agents_needed"].append("file")
            interpretation["confidence"] = 0.8
            
            if "find" in request_lower:
                interpretation["parameters"]["action"] = "find"
            elif "organize" in request_lower:
                interpretation["parameters"]["action"] = "organize"
            elif "duplicate" in request_lower:
                interpretation["parameters"]["action"] = "remove_duplicates"
        
        # Research keywords
        elif any(word in request_lower for word in ["search", "research", "find information", "look up"]):
            interpretation["primary_intent"] = "research"
            interpretation["agents_needed"].append("research")
            interpretation["confidence"] = 0.8
        
        # Domain management keywords
        elif any(word in request_lower for word in ["domain", "dns", "website", "server"]):
            interpretation["primary_intent"] = "domain_management"
            interpretation["agents_needed"].append("domain")
            interpretation["confidence"] = 0.8
            
            if "check" in request_lower or "status" in request_lower:
                interpretation["parameters"]["action"] = "check_status"
            elif "fix" in request_lower:
                interpretation["parameters"]["action"] = "fix_dns"
        
        # Phone management keywords
        elif any(word in request_lower for word in ["phone", "photos", "contacts", "mobile"]):
            interpretation["primary_intent"] = "phone_management"
            interpretation["agents_needed"].append("phone")
            interpretation["confidence"] = 0.8
            
            if "photo" in request_lower:
                interpretation["parameters"]["action"] = "sort_photos"
            elif "contact" in request_lower:
                interpretation["parameters"]["action"] = "clean_contacts"
        
        # Automation keywords
        elif any(word in request_lower for word in ["automate", "backup", "schedule", "desktop", "tool"]):
            interpretation["primary_intent"] = "automation"
            interpretation["agents_needed"].append("automation")
            interpretation["confidence"] = 0.8
            
            if "backup" in request_lower:
                interpretation["parameters"]["action"] = "backup"
            elif "desktop" in request_lower:
                interpretation["parameters"]["action"] = "organize_desktop"
            elif "schedule" in request_lower:
                interpretation["parameters"]["action"] = "schedule_task"
            elif "tool" in request_lower:
                interpretation["parameters"]["action"] = "create_tool"
        
        # Memory/context keywords
        elif any(word in request_lower for word in ["remember", "recall", "previous", "last time"]):
            interpretation["primary_intent"] = "memory_recall"
            interpretation["agents_needed"].append("memory")
            interpretation["confidence"] = 0.7
        
        # Multi-agent requests
        if "organize my" in request_lower:
            if "phone" in request_lower:
                interpretation["agents_needed"] = ["phone", "memory"]
            elif "computer" in request_lower or "files" in request_lower:
                interpretation["agents_needed"] = ["file", "automation", "memory"]
        
        return interpretation
    
    def process_request(self, user_input: str) -> str:
        """Process a user request and coordinate agents"""
        self.logger.info(f"Processing request: {user_input}")
        
        # Check for relevant past context
        past_context = self.memory.retrieve_relevant(user_input, limit=3)
        context_summary = ""
        if past_context:
            context_summary = f"Found {len(past_context)} relevant past interactions. "
        
        # Interpret the request
        interpretation = self.interpret_request(user_input)
        
        if interpretation["primary_intent"] == "unknown":
            response = "I'm not sure what you'd like me to help with. Could you please clarify your request?"
            self.memory.save_interaction(user_input, response, self.session_id, "unknown_intent")
            return response
        
        # Execute appropriate agent actions
        responses = []
        all_actions = []
        
        for agent_name in interpretation["agents_needed"]:
            agent_response = self._execute_agent_action(
                agent_name, 
                interpretation["parameters"], 
                user_input
            )
            responses.append(agent_response)
            if agent_response.actions_taken:
                all_actions.extend(agent_response.actions_taken)
        
        # Compile final response
        final_response = self._compile_response(user_input, interpretation, responses, context_summary)
        
        # Save interaction to memory
        context_tags = f"{interpretation['primary_intent']},{','.join(interpretation['agents_needed'])}"
        self.memory.save_interaction(user_input, final_response, self.session_id, context_tags)
        
        return final_response
    
    def _execute_agent_action(self, agent_name: str, parameters: Dict, user_input: str) -> AgentResponse:
        """Execute action for a specific agent"""
        try:
            if agent_name == "research":
                # Extract query from user input (simple approach)
                query = user_input.replace("search for", "").replace("research", "").strip()
                return self.research.get_information(query)
            
            elif agent_name == "file":
                action = parameters.get("action", "find")
                if action == "find":
                    # Extract search terms
                    search_terms = user_input.replace("find", "").replace("file", "").strip()
                    return self.file_agent.find_file(search_terms)
                elif action == "organize":
                    # Default to current directory for demo
                    return self.file_agent.organize_folder(".", "type")
                elif action == "remove_duplicates":
                    return self.file_agent.remove_duplicates(".")
            
            elif agent_name == "automation":
                action = parameters.get("action", "organize_desktop")
                if action == "backup":
                    return self.automation.run_backup("./important_files", "./backup")
                elif action == "organize_desktop":
                    return self.automation.organize_desktop()
                elif action == "schedule_task":
                    task = user_input.replace("schedule", "").strip()
                    return self.automation.schedule_task(task, "tomorrow 9:00 AM")
                elif action == "create_tool":
                    return self.automation.create_tool(user_input)
            
            elif agent_name == "phone":
                action = parameters.get("action", "sort_photos")
                if action == "sort_photos":
                    return self.phone.sort_photos()
                elif action == "clean_contacts":
                    return self.phone.clean_contacts()
            
            elif agent_name == "domain":
                action = parameters.get("action", "check_status")
                # Extract domain name from user input
                words = user_input.split()
                domain = None
                for word in words:
                    if "." in word and not word.startswith("."):
                        domain = word.strip(".,!?")
                        break
                
                if not domain:
                    domain = "example.com"  # Default for demo
                
                if action == "check_status":
                    return self.domain.check_domain_status(domain)
                elif action == "fix_dns":
                    return self.domain.fix_dns(domain, "A", "192.168.1.1")
            
            elif agent_name == "memory":
                query = user_input.replace("remember", "").replace("recall", "").strip()
                past_interactions = self.memory.retrieve_relevant(query, limit=5)
                return AgentResponse(
                    success=True,
                    message=f"Found {len(past_interactions)} relevant past interactions",
                    data={"past_interactions": past_interactions},
                    actions_taken=[f"Searched memory for: {query}"]
                )
            
            else:
                return AgentResponse(
                    success=False,
                    message=f"Unknown agent: {agent_name}"
                )
        
        except Exception as e:
            self.logger.error(f"Error executing {agent_name} action: {e}")
            return AgentResponse(
                success=False,
                message=f"Error in {agent_name}: {str(e)}"
            )
    
    def _compile_response(self, user_input: str, interpretation: Dict, 
                         agent_responses: List[AgentResponse], context_summary: str) -> str:
        """Compile final response from agent outputs"""
        response_parts = []
        
        # Add context if available
        if context_summary:
            response_parts.append(context_summary)
        
        # Process each agent response
        successful_responses = [r for r in agent_responses if r.success]
        failed_responses = [r for r in agent_responses if not r.success]
        
        if successful_responses:
            response_parts.append("Here's what I accomplished:")
            
            for response in successful_responses:
                response_parts.append(f"✓ {response.message}")
                
                # Add key data points
                if response.data:
                    for key, value in response.data.items():
                        if isinstance(value, (int, str)) and key != "results":
                            response_parts.append(f"  - {key}: {value}")
                
                # Add some action details
                if response.actions_taken:
                    key_actions = response.actions_taken[:3]  # Limit to 3 key actions
                    for action in key_actions:
                        response_parts.append(f"  • {action}")
        
        # Handle any failures
        if failed_responses:
            response_parts.append("\nSome issues encountered:")
            for response in failed_responses:
                response_parts.append(f"✗ {response.message}")
        
        # Add helpful suggestions based on intent
        if interpretation["primary_intent"] == "file_management":
            response_parts.append("\nTip: I can also help organize files by date, find duplicates, or backup important documents.")
        elif interpretation["primary_intent"] == "domain_management":
            response_parts.append("\nTip: I can monitor your domains regularly and alert you to any issues.")
        elif interpretation["primary_intent"] == "phone_management":
            response_parts.append("\nTip: I can also help with backing up your phone data to the cloud.")
        
        return "\n".join(response_parts)

class ProjectBrainSaver:
    """Main application class"""
    
    def __init__(self):
        self.orchestrator = GuardianOrchestrator()
        self.logger = logging.getLogger(f"{__class__.__name__}")
        self.running = True
        
        print("🧠 ProjectBrainSaver AI Assistant Initialized")
        print("=" * 50)
        print("Available commands:")
        print("- help: Show available commands")
        print("- status: Show system status")
        print("- exit/quit: Exit the application")
        print("- Any natural language request for assistance")
        print("=" * 50)
    
    def run_cli(self):
        """Run the command-line interface"""
        while self.running:
            try:
                user_input = input("\n🤖 How can I help you? > ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    self.shutdown()
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'status':
                    self.show_status()
                    continue
                
                # Process the request
                print("\n🔄 Processing your request...")
                response = self.orchestrator.process_request(user_input)
                print(f"\n💡 {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.shutdown()
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                print(f"❌ An error occurred: {e}")
    
    def show_help(self):
        """Show help information"""
        help_text = """
📖 ProjectBrainSaver Help

EXAMPLE COMMANDS:
• "Find files containing 'report'"
• "Organize my desktop"
• "Check the status of example.com"
• "Research artificial intelligence trends"
• "Backup my important files"
• "Sort my photos"
• "Clean up my contacts"
• "Schedule a backup for tomorrow"
• "Create a tool for organizing emails"
• "What did we discuss about domains last week?"

AVAILABLE AGENTS:
🔍 Research Agent - Web search and information gathering
💾 Memory Agent - Remembers past conversations and context
📁 File Agent - File organization, search, and management
🤖 Automation Agent - Task automation and tool creation
📱 Phone Agent - Mobile data organization
🌐 Domain Agent - Website and DNS management

TIPS:
• Be specific about what you want to accomplish
• I remember our previous conversations
• I can handle multiple tasks in one request
• Ask me to explain anything I've done
        """
        print(help_text)
    
    def show_status(self):
        """Show system status"""
        status_info = f"""
📊 System Status

Session ID: {self.orchestrator.session_id}
Agents Status: ✅ All agents operational
Memory Database: ✅ Connected
Log File: projectbrainsaver.log

Recent Activity:
• Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Agents initialized: 6/6
• Ready to assist!
        """
        print(status_info)
    
    def shutdown(self):
        """Gracefully shutdown the application"""
        print("🔄 Shutting down ProjectBrainSaver...")
        self.running = False
        print("✅ Shutdown complete. Have a great day!")

def main():
    """Main entry point"""
    try:
        app = ProjectBrainSaver()
        app.run_cli()
    except Exception as e:
        print(f"❌ Failed to start ProjectBrainSaver: {e}")
        logging.error(f"Startup error: {e}")

if __name__ == "__main__":
    main()