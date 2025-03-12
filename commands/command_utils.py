# commands/command_utils.py
def command_mode(mode: str):
    """Decorator to set the execution mode for a command (server, dm, or both)."""
    def decorator(func):
        func.command_mode = mode
        return func
    return decorator