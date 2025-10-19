"""Terminal interface implementation for command-line interaction."""

import sys
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from ai_browser_agent.interfaces.user_interface import UserInterface, UserMessage, UserPrompt, MessageType
from ai_browser_agent.models.task import Task, TaskStatus


class TerminalInterface(UserInterface):
    """Terminal-based user interface for command-line interaction."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._current_task: Optional[Task] = None
        self._status_lock = threading.Lock()
        # StatusReporter will be set externally to avoid circular imports
        
    def display_message(self, message: UserMessage) -> None:
        """Display a formatted message to the user via terminal."""
        timestamp = message.timestamp or datetime.now().strftime("%H:%M:%S")
        
        # Color codes for different message types
        colors = {
            MessageType.INFO: "\033[94m",      # Blue
            MessageType.WARNING: "\033[93m",   # Yellow
            MessageType.ERROR: "\033[91m",     # Red
            MessageType.SUCCESS: "\033[92m",   # Green
            MessageType.STATUS: "\033[96m",    # Cyan
            MessageType.PROMPT: "\033[95m"     # Magenta
        }
        
        reset_color = "\033[0m"
        color = colors.get(message.message_type, "")
        
        # Format message with timestamp and type
        type_label = message.message_type.value.upper()
        formatted_message = f"{color}[{timestamp}] {type_label}: {message.content}{reset_color}"
        
        print(formatted_message)
        
        # Add to history
        self.add_to_history(message)
    
    def get_user_input(self, prompt: UserPrompt) -> str:
        """Get input from the user via terminal with proper handling."""
        try:
            # Display prompt with formatting
            prompt_msg = UserMessage(
                content=prompt.question,
                message_type=MessageType.PROMPT
            )
            self.display_message(prompt_msg)
            
            # Handle different input types
            if prompt.input_type == "confirmation":
                return self._get_confirmation_input(prompt)
            elif prompt.input_type == "choice" and prompt.options:
                return self._get_choice_input(prompt)
            else:
                return self._get_text_input(prompt)
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            return ""
        except EOFError:
            print("\nEnd of input reached.")
            return ""
    
    def _get_text_input(self, prompt: UserPrompt) -> str:
        """Get text input from user."""
        while True:
            try:
                user_input = input("> ").strip()
                
                if not user_input and prompt.is_required and not prompt.default_value:
                    print("This field is required. Please enter a value.")
                    continue
                
                return user_input or prompt.default_value or ""
                
            except (KeyboardInterrupt, EOFError):
                if not prompt.is_required:
                    return prompt.default_value or ""
                raise
    
    def _get_confirmation_input(self, prompt: UserPrompt) -> str:
        """Get yes/no confirmation from user."""
        valid_yes = ['y', 'yes', 'true', '1']
        valid_no = ['n', 'no', 'false', '0']
        
        while True:
            try:
                user_input = input("(y/n) > ").strip().lower()
                
                if user_input in valid_yes:
                    return "yes"
                elif user_input in valid_no:
                    return "no"
                elif not user_input and prompt.default_value:
                    return prompt.default_value
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
                    
            except (KeyboardInterrupt, EOFError):
                return prompt.default_value or "no"
    
    def _get_choice_input(self, prompt: UserPrompt) -> str:
        """Get choice input from user with numbered options."""
        if not prompt.options:
            return self._get_text_input(prompt)
        
        # Display options
        print("Available options:")
        for i, option in enumerate(prompt.options, 1):
            print(f"  {i}. {option}")
        
        while True:
            try:
                user_input = input("Enter choice number or text > ").strip()
                
                # Try to parse as number
                try:
                    choice_num = int(user_input)
                    if 1 <= choice_num <= len(prompt.options):
                        return prompt.options[choice_num - 1]
                    else:
                        print(f"Please enter a number between 1 and {len(prompt.options)}.")
                        continue
                except ValueError:
                    pass
                
                # Check if input matches an option
                for option in prompt.options:
                    if user_input.lower() == option.lower():
                        return option
                
                # If no match and not required, return input
                if not prompt.is_required:
                    return user_input
                
                print("Invalid choice. Please select from the available options.")
                
            except (KeyboardInterrupt, EOFError):
                return prompt.default_value or ""
    
    def display_status(self, status: Dict[str, Any]) -> None:
        """Display formatted status information."""
        with self._status_lock:
            status_type = status.get("type", "general")
            content = status.get("content", "")
            
            if status_type == "task_progress":
                self._display_task_progress(status)
            elif status_type == "execution_step":
                self._display_execution_step(status)
            else:
                status_msg = UserMessage(
                    content=content,
                    message_type=MessageType.STATUS
                )
                self.display_message(status_msg)
    
    def _display_task_progress(self, status: Dict[str, Any]) -> None:
        """Display task progress with progress bar."""
        task_id = status.get("task_id", "Unknown")
        progress = status.get("progress", 0.0)
        current_step = status.get("current_step", "")
        
        # Create progress bar
        bar_length = 30
        filled_length = int(bar_length * progress / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        progress_text = f"Task {task_id}: [{bar}] {progress:.1f}%"
        if current_step:
            progress_text += f" - {current_step}"
        
        status_msg = UserMessage(
            content=progress_text,
            message_type=MessageType.STATUS
        )
        self.display_message(status_msg)
    
    def _display_execution_step(self, status: Dict[str, Any]) -> None:
        """Display execution step information."""
        step_name = status.get("step_name", "Unknown Step")
        step_status = status.get("step_status", "running")
        details = status.get("details", "")
        
        status_icons = {
            "running": "⏳",
            "completed": "✅",
            "failed": "❌",
            "waiting": "⏸️"
        }
        
        icon = status_icons.get(step_status, "•")
        content = f"{icon} {step_name}"
        if details:
            content += f" - {details}"
        
        msg_type = MessageType.SUCCESS if step_status == "completed" else MessageType.STATUS
        if step_status == "failed":
            msg_type = MessageType.ERROR
        
        status_msg = UserMessage(
            content=content,
            message_type=msg_type
        )
        self.display_message(status_msg)
    
    def start_interface(self) -> None:
        """Start the terminal interface with welcome message."""
        self.is_active = True
        
        welcome_msg = UserMessage(
            content="AI Browser Agent Terminal Interface Started",
            message_type=MessageType.SUCCESS
        )
        self.display_message(welcome_msg)
        
        # Display usage instructions
        instructions = [
            "Commands:",
            "  - Enter task descriptions in natural language",
            "  - Type 'help' for more information",
            "  - Type 'quit' or 'exit' to stop the agent",
            "  - Use Ctrl+C to cancel current operation"
        ]
        
        for instruction in instructions:
            info_msg = UserMessage(
                content=instruction,
                message_type=MessageType.INFO
            )
            self.display_message(info_msg)
    
    def stop_interface(self) -> None:
        """Stop the terminal interface with goodbye message."""
        self.is_active = False
        
        goodbye_msg = UserMessage(
            content="AI Browser Agent Terminal Interface Stopped",
            message_type=MessageType.INFO
        )
        self.display_message(goodbye_msg)
    
    def display_task_report(self, task: Task) -> None:
        """Display a formatted task completion report."""
        print("\n" + "="*60)
        print("TASK EXECUTION REPORT")
        print("="*60)
        
        # Task basic info
        print(f"Task ID: {task.id}")
        print(f"Description: {task.description}")
        print(f"Status: {task.status.value.upper()}")
        print(f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if task.completed_at:
            duration = task.completed_at - task.created_at
            print(f"Completed: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Duration: {duration}")
        
        # Progress information
        if task.execution_plan:
            progress = task.get_progress_percentage()
            print(f"Progress: {progress:.1f}%")
            
            # Step details
            print(f"\nExecution Steps ({len(task.execution_plan.steps)} total):")
            for i, step in enumerate(task.execution_plan.steps, 1):
                status_icon = "✅" if step.is_completed else "❌" if step.error_message else "⏳"
                print(f"  {i}. {status_icon} {step.description}")
                
                if step.error_message:
                    print(f"     Error: {step.error_message}")
                elif step.execution_time:
                    print(f"     Execution time: {step.execution_time:.2f}s")
        
        # Results
        if task.result:
            print(f"\nResults:")
            for key, value in task.result.items():
                print(f"  {key}: {value}")
        
        # Error information
        if task.error_message:
            print(f"\nError: {task.error_message}")
        
        print("="*60 + "\n")
    
    def display_confirmation_prompt(self, action_description: str, is_destructive: bool = False) -> bool:
        """Display a confirmation prompt for potentially destructive actions."""
        if is_destructive:
            warning_msg = UserMessage(
                content="⚠️  DESTRUCTIVE ACTION DETECTED ⚠️",
                message_type=MessageType.WARNING
            )
            self.display_message(warning_msg)
        
        prompt = UserPrompt(
            question=f"Do you want to proceed with: {action_description}?",
            input_type="confirmation",
            default_value="no" if is_destructive else "yes"
        )
        
        response = self.get_user_input(prompt)
        return response.lower() in ['y', 'yes', 'true', '1']
    
    def set_current_task(self, task: Task) -> None:
        """Set the current task being executed."""
        self._current_task = task
    
    def get_current_task(self) -> Optional[Task]:
        """Get the current task being executed."""
        return self._current_task