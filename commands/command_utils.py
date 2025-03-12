# commands/command_utils.py
def command_mode(mode: str):
    """Decorator to set the execution mode for a command (server, dm, or both)."""
    def decorator(func):
        func.command_mode = mode  # Attach mode to the raw function

        # If this function is a commands.Command object, ensure the attribute is preserved
        if hasattr(func, "__discord_command__"):
            func.__discord_command__.command_mode = mode
        
        return func
    return decorator
