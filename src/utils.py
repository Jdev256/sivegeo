import io

class StreamlitStdoutRedirector:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.buffer = io.StringIO()

    def write(self, text):
        self.buffer.write(text)
        current_logs = self.buffer.getvalue()
        if current_logs.strip():
            self.placeholder.code(current_logs, language="text")

    def flush(self):
        pass