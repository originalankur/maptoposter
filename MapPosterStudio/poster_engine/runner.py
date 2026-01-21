import os
import subprocess
import sys
from PySide6.QtCore import QThread, Signal

class PosterGenerator(QThread):
    progress_update = Signal(str)  # Emits stdout lines or status messages
    finished_success = Signal(str) # Emits output filename
    finished_error = Signal(str)   # Emits error message

    def __init__(self, city, country, theme, distance, output_file, dpi, title=None, subtitle=None, tagline=None, fast_mode=False):
        super().__init__()
        self.city = city
        self.country = country
        self.theme = theme
        self.distance = distance
        self.output_file = output_file
        self.dpi = dpi
        self.title = title
        self.subtitle = subtitle
        self.tagline = tagline
        self.fast_mode = fast_mode
        self._is_cancelled = False
        self._process = None

    def run(self):
        # Locate create_map_poster.py
        # Assumed to be in ProjectRoot/create_map_poster.py
        # This file is ProjectRoot/MapPosterStudio/poster_engine/runner.py
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        script_path = os.path.join(base_dir, 'create_map_poster.py')

        if not os.path.exists(script_path):
            self.finished_error.emit(f"Script not found at: {script_path}")
            return

        # Prepare command
        cmd = [
            sys.executable,
            script_path,
            '--city', self.city,
            '--country', self.country,
            '--theme', self.theme,
            '--distance', str(self.distance),
            '--dpi', str(self.dpi),
        ]

        if self.title:
            cmd.extend(['--title', self.title])
        
        if self.subtitle:
            cmd.extend(['--subtitle', self.subtitle])

        if self.tagline:
            cmd.extend(['--tagline', self.tagline])

        if self.output_file:
            cmd.extend(['--output', self.output_file])
        
        if self.fast_mode:
            cmd.append('--fast')

        # We need to capture output to know when it's done or if it failed
        # and to show progress.
        try:
            # Using Popen to read stdout in real-time
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # Force Python to use UTF-8 for IO to avoid charmap errors with checkmarks
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8', # Ensure utf-8 decoding
                cwd=base_dir, # Run from project root so it finds 'themes' and 'fonts'
                startupinfo=startupinfo,
                env=env
            )

            recent_output = []
            
            for line in self._process.stdout:
                if self._is_cancelled:
                    self._process.terminate()
                    break
                
                line = line.strip()
                if line:
                    self.progress_update.emit(line)
                    recent_output.append(line)
                    if len(recent_output) > 15:
                        recent_output.pop(0)

            self._process.wait()
            
            if self._process.returncode == 0:
                # If success, the output file should be what we requested
                self.finished_success.emit(self.output_file)
            else:
                error_context = "\n".join(recent_output)
                self.finished_error.emit(f"Process failed with exit code {self._process.returncode}\n\nLast output:\n{error_context}")

        except Exception as e:
            self.finished_error.emit(str(e))

    def cancel(self):
        self._is_cancelled = True
        if self._process:
            self._process.terminate()
