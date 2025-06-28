import os
import subprocess
from typing import Dict, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)

class Terminal:
    """Enhanced terminal tool with proper directory handling."""
    
    def __init__(self):
        self.name = "Terminal"
        self.description = "Execute terminal commands"
        
    async def execute(self, command: str, working_dir: str = None) -> Dict[str, Any]:
        """Execute command with proper working directory handling."""
        try:
            # Ensure working directory exists
            if working_dir:
                os.makedirs(working_dir, exist_ok=True)
                
            logger.info(f"Executing command: {command} in {working_dir or 'current directory'}")
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            response = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
            if result.returncode == 0:
                logger.info(f"Command succeeded: {command}")
            else:
                logger.warning(f"Command failed with code {result.returncode}: {command}")
                
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return {
                "success": False,
                "error": "Command timed out after 30 seconds"
            }
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
