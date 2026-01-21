import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Ensure the correct path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    app = QApplication(sys.argv)
    
    # Setup basic style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
