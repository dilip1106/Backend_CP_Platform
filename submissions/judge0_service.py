import requests
import time
from typing import Dict, Optional


class Judge0Service:
    """
    Service to interact with Judge0 CE Free API for code execution
    Using: https://ce.judge0.com (Free, no API key required)
    """
    
    # Language ID mapping for Judge0
    LANGUAGE_MAP = {
        'PYTHON': 71,      # Python 3.8.1
        'JAVA': 62,        # Java (OpenJDK 13.0.1)
        'CPP': 54,         # C++ (GCC 9.2.0)
        'C': 50,           # C (GCC 9.2.0)
        'JAVASCRIPT': 63,  # JavaScript (Node.js 12.14.0)
    }
    
    # Judge0 Status ID to Verdict mapping
    STATUS_MAP = {
        1: 'PENDING',                    # In Queue
        2: 'RUNNING',                    # Processing
        3: 'ACCEPTED',                   # Accepted
        4: 'WRONG_ANSWER',              # Wrong Answer
        5: 'TIME_LIMIT_EXCEEDED',       # Time Limit Exceeded
        6: 'COMPILATION_ERROR',         # Compilation Error
        7: 'RUNTIME_ERROR',             # Runtime Error (SIGSEGV)
        8: 'RUNTIME_ERROR',             # Runtime Error (SIGXFSZ)
        9: 'RUNTIME_ERROR',             # Runtime Error (SIGFPE)
        10: 'RUNTIME_ERROR',            # Runtime Error (SIGABRT)
        11: 'RUNTIME_ERROR',            # Runtime Error (NZEC)
        12: 'RUNTIME_ERROR',            # Runtime Error (Other)
        13: 'INTERNAL_ERROR',           # Internal Error
        14: 'RUNTIME_ERROR',            # Exec Format Error
    }
    
    def __init__(self):
        # Using free Judge0 CE API (no API key needed)
        self.base_url = 'https://ce.judge0.com'
        self.headers = {
            'Content-Type': 'application/json',
        }
    
    def get_language_id(self, language: str) -> int:
        """Get Judge0 language ID from our language enum"""
        return self.LANGUAGE_MAP.get(language, 71)  # Default to Python
    
    def submit_code(
        self,
        source_code: str,
        language: str,
        stdin: str = '',
        expected_output: str = '',
        time_limit: float = 20.0,
        memory_limit: int = 256000
    ) -> Optional[str]:
        """
        Submit code to Judge0 for execution
        
        Args:
            source_code: The source code to execute
            language: Programming language
            stdin: Standard input for the program
            expected_output: Expected output for verification
            time_limit: CPU time limit in seconds
            memory_limit: Memory limit in KB
        
        Returns:
            Token for the submission or None if failed
        """
        language_id = self.get_language_id(language)
        
        payload = {
            'source_code': source_code,
            'language_id': language_id,
            'stdin': stdin,
            'expected_output': expected_output,
            'cpu_time_limit': time_limit,
            'memory_limit': memory_limit,
        }
        
        try:
            # Using wait=false to get token, then poll for results
            url = f"{self.base_url}/submissions?base64_encoded=false&wait=false"
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 201:
                return response.json().get('token')
            else:
                print(f"Judge0 submission failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error submitting to Judge0: {str(e)}")
            return None
    
    def get_submission_result(self, token: str, max_retries: int = 10) -> Optional[Dict]:
        """
        Get the result of a submission by token
        
        Args:
            token: Submission token
            max_retries: Maximum number of retries
        
        Returns:
            Submission result dictionary or None if failed
        """
        try:
            url = f"{self.base_url}/submissions/{token}?base64_encoded=false"
            
            for _ in range(max_retries):
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    status_id = result.get('status', {}).get('id')
                    
                    # Status IDs: 1=In Queue, 2=Processing
                    if status_id not in [1, 2]:
                        return result
                
                time.sleep(1)  # Wait before retry
            
            return None
            
        except Exception as e:
            print(f"Error getting Judge0 result: {str(e)}")
            return None
    
    def execute_and_wait(
        self,
        source_code: str,
        language: str,
        stdin: str = '',
        expected_output: str = '',
        time_limit: float = 2.0,
        memory_limit: int = 256000
    ) -> Optional[Dict]:
        """
        Submit code and wait for result
        
        Returns:
            Execution result or None if failed
        """
        token = self.submit_code(
            source_code, language, stdin, 
            expected_output, time_limit, memory_limit
        )
        
        if not token:
            return None
        
        return self.get_submission_result(token)
    
    def parse_result(self, result: Dict) -> Dict:
        """
        Parse Judge0 result into our format
        
        Judge0 Status IDs:
        1: In Queue, 2: Processing, 3: Accepted, 4: Wrong Answer,
        5: Time Limit Exceeded, 6: Compilation Error, 7-12,14: Runtime Errors,
        13: Internal Error
        """
        status_id = result.get('status', {}).get('id')
        verdict = self.STATUS_MAP.get(status_id, 'INTERNAL_ERROR')
        
        return {
            'verdict': verdict,
            'execution_time': result.get('time'),  # in seconds
            'memory_used': result.get('memory'),   # in KB
            'stdout': result.get('stdout', ''),
            'stderr': result.get('stderr', ''),
            'compile_output': result.get('compile_output', ''),
            'message': result.get('message', ''),
            'status_description': result.get('status', {}).get('description', ''),
            'status_id': status_id,
        }