import os
import re
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QSlider, QSpinBox, 
    QCheckBox, QFileDialog, QMessageBox, QGroupBox, QScrollArea,
    QProgressBar, QFrame, QTabWidget, QFormLayout, QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QSettings
from PySide6.QtGui import QPixmap, QIcon, QAction, QPalette, QColor
from poster_engine.themes import get_available_themes
from poster_engine.runner import PosterGenerator

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MapPoster Studio")
        self.resize(1200, 850)
        self.settings = QSettings("MapPosterStudio", "App")
        
        # Load themes
        self.available_themes = get_available_themes()
        
        # State
        self.current_preview_path = None
        self.is_generating = False
        self.generator = None
        self.original_pixmap = None
        
        # Apply Dark Theme
        self.apply_dark_theme()
        
        # UI Setup
        self.setup_ui()
        
        # Load previous session or defaults
        self.load_settings()

    def apply_dark_theme(self):
        # Basic Fusion dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Main layout: Vertical (Splitter + Action Bar)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Splitter (Left Settings | Right Preview) ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)
        
        # 1. Left Panel: Tabs Container
        left_container = QWidget()
        left_container.setMinimumWidth(320)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        self.tabs = QTabWidget()
        
        # Tab 1: Basic
        self.tab_basic = QWidget()
        basic_layout = QVBoxLayout(self.tab_basic)
        basic_layout.setSpacing(15)
        
        loc_group = QGroupBox("Location")
        loc_form = QFormLayout()
        loc_form.setLabelAlignment(Qt.AlignLeft)
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("e.g. London")
        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("e.g. UK")
        loc_form.addRow("City:", self.city_input)
        loc_form.addRow("Country:", self.country_input)
        loc_group.setLayout(loc_form)
        
        self.btn_preview_shortcut = QPushButton("Generate Preview")
        self.btn_preview_shortcut.setToolTip("Quick preview generation")
        self.btn_preview_shortcut.clicked.connect(self.generate_preview)
        
        basic_layout.addWidget(loc_group)
        basic_layout.addWidget(self.btn_preview_shortcut)
        basic_layout.addStretch()
        
        # Tab 2: Style
        self.tab_style = QWidget()
        style_layout = QVBoxLayout(self.tab_style)
        style_layout.setSpacing(15)
        
        style_form = QFormLayout()
        style_form.setLabelAlignment(Qt.AlignLeft)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Custom", "Noir City", "Modern Minimal", "Retro Blueprint", "Cyberpunk Neon"])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.available_themes)
        
        # Radius
        radius_widget = QWidget()
        radius_row = QHBoxLayout(radius_widget)
        radius_row.setContentsMargins(0,0,0,0)
        self.radius_slider = QSlider(Qt.Horizontal)
        self.radius_slider.setRange(500, 50000)
        self.radius_slider.setSingleStep(500)
        self.radius_slider.setValue(15000)
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(500, 50000)
        self.radius_spin.setSingleStep(500)
        self.radius_spin.setValue(15000)
        self.radius_spin.setSuffix(" m")
        self.radius_spin.setFixedWidth(80)
        self.radius_slider.valueChanged.connect(self.radius_spin.setValue)
        self.radius_spin.valueChanged.connect(self.radius_slider.setValue)
        radius_row.addWidget(self.radius_slider)
        radius_row.addWidget(self.radius_spin)
        
        # DPI
        dpi_widget = QWidget()
        dpi_row = QHBoxLayout(dpi_widget)
        dpi_row.setContentsMargins(0,0,0,0)
        self.dpi_slider = QSlider(Qt.Horizontal)
        self.dpi_slider.setRange(72, 600)
        self.dpi_slider.setValue(300)
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        self.dpi_spin.setFixedWidth(60)
        self.dpi_slider.valueChanged.connect(self.dpi_spin.setValue)
        self.dpi_spin.valueChanged.connect(self.dpi_slider.setValue)
        dpi_row.addWidget(self.dpi_slider)
        dpi_row.addWidget(self.dpi_spin)
        
        style_form.addRow("Preset:", self.preset_combo)
        style_form.addRow("Theme:", self.theme_combo)
        style_form.addRow("Radius:", radius_widget)
        style_form.addRow("DPI:", dpi_widget)
        
        style_layout.addLayout(style_form)
        style_layout.addWidget(QLabel("<small style='color:gray'>Preview always uses 72 DPI</small>"))
        style_layout.addStretch()
        
        # Tab 3: Text
        self.tab_text = QWidget()
        text_layout = QVBoxLayout(self.tab_text)
        
        self.custom_text_check = QCheckBox("Enable Custom Text")
        self.custom_text_check.setChecked(False)
        self.custom_text_check.toggled.connect(self.toggle_custom_text)
        
        self.text_container = QWidget()
        text_form = QFormLayout(self.text_container)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Title")
        self.subtitle_input = QLineEdit()
        self.subtitle_input.setPlaceholderText("Subtitle")
        self.tagline_input = QLineEdit()
        self.tagline_input.setPlaceholderText("Tagline")
        self.auto_upper_check = QCheckBox("Auto-uppercase Subtitle")
        self.auto_upper_check.setChecked(True)
        
        text_form.addRow("Title:", self.title_input)
        text_form.addRow("Subtitle:", self.subtitle_input)
        text_form.addRow("", self.auto_upper_check)
        text_form.addRow("Tagline:", self.tagline_input)
        
        text_layout.addWidget(self.custom_text_check)
        text_layout.addWidget(self.text_container)
        text_layout.addStretch()
        
        # Add tabs
        self.tabs.addTab(self.tab_basic, "Basic")
        self.tabs.addTab(self.tab_style, "Style")
        self.tabs.addTab(self.tab_text, "Text")
        
        left_layout.addWidget(self.tabs)
        
        # 2. Right Panel: Preview
        right_container = QWidget()
        right_container.setMinimumWidth(600)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(0)
        
        # Zoom Toolbar (Top of Right Panel)
        zoom_bar = QWidget()
        zoom_bar.setStyleSheet("background-color: #2b2b2b;")
        zoom_layout = QHBoxLayout(zoom_bar)
        zoom_layout.setContentsMargins(10, 5, 10, 5)
        
        self.btn_fit = QPushButton("Fit")
        self.btn_50 = QPushButton("50%")
        self.btn_100 = QPushButton("100%")
        
        for btn in [self.btn_fit, self.btn_50, self.btn_100]:
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background-color: #444; border: none; padding: 4px 10px; color: #ddd; }
                QPushButton:checked { background-color: #2196F3; color: white; }
                QPushButton:hover { background-color: #555; }
            """)
        
        self.btn_fit.clicked.connect(lambda: self.set_zoom("Fit"))
        self.btn_50.clicked.connect(lambda: self.set_zoom(0.5))
        self.btn_100.clicked.connect(lambda: self.set_zoom(1.0))
        
        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self.btn_fit)
        zoom_layout.addWidget(self.btn_50)
        zoom_layout.addWidget(self.btn_100)
        zoom_layout.addStretch()
        
        right_layout.addWidget(zoom_bar)
        
        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        # Important for "Fit" mode:
        self.scroll_area.setWidgetResizable(True)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("Enter a city and click 'Generate Preview'")
        self.image_label.setStyleSheet("QLabel { color: #888; font-size: 16px; padding: 20px; }")
        # Ensure label scales contents in fit mode
        self.image_label.setScaledContents(False) 
        
        self.scroll_area.setWidget(self.image_label)
        right_layout.addWidget(self.scroll_area)
        
        # Add to Splitter
        self.splitter.addWidget(left_container)
        self.splitter.addWidget(right_container)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([360, 840])
        self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        main_layout.addWidget(self.splitter)
        
        # --- Bottom Section: Action Bar ---
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(56) # Fixed height as requested
        bottom_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Dark theme style for bottom bar
        bottom_bar.setStyleSheet("""
            QWidget { background-color: #222; border-top: 1px solid #444; }
            QLabel { color: #ccc; border: none; }
            QPushButton { background-color: #444; color: white; border: 1px solid #555; padding: 6px 12px; border-radius: 3px; }
            QPushButton:hover { background-color: #555; }
            QPushButton:disabled { background-color: #333; color: #666; }
            QProgressBar { background-color: #444; border: 1px solid #555; height: 10px; }
        """)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(15, 0, 15, 0) # Minimal vertical margin
        bottom_layout.setSpacing(10)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("margin-top: 0px; margin-bottom: 0px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.hide()
        
        self.btn_reset = QPushButton("Reset Defaults")
        self.btn_reset.clicked.connect(self.reset_defaults)
        
        self.btn_preview = QPushButton("Generate Preview")
        self.btn_preview.setStyleSheet("QPushButton { background-color: #2196F3; border: 1px solid #1976D2; font-weight: bold; } QPushButton:hover { background-color: #42A5F5; }")
        self.btn_preview.clicked.connect(self.generate_preview)
        
        self.btn_export = QPushButton("Export PNG")
        self.btn_export.setStyleSheet("QPushButton { background-color: #4CAF50; border: 1px solid #388E3C; font-weight: bold; } QPushButton:hover { background-color: #66BB6A; } QPushButton:disabled { background-color: #333; border: 1px solid #444; }")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_poster)
        
        self.btn_open_folder = QPushButton("Open Folder")
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_reset)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(self.btn_preview)
        bottom_layout.addWidget(self.btn_export)
        bottom_layout.addWidget(self.btn_open_folder)
        
        main_layout.addWidget(bottom_bar)
        
        self.zoom_mode = "Fit"
        self.update_zoom_buttons()
        self.toggle_custom_text(False) # Initialize state

    def toggle_custom_text(self, checked):
        self.text_container.setVisible(checked)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        self.settings.setValue("city", self.city_input.text())
        self.settings.setValue("country", self.country_input.text())
        self.settings.setValue("theme", self.theme_combo.currentText())
        self.settings.setValue("radius", self.radius_spin.value())
        self.settings.setValue("dpi", self.dpi_spin.value())
        self.settings.setValue("title", self.title_input.text())
        self.settings.setValue("subtitle", self.subtitle_input.text())
        self.settings.setValue("tagline", self.tagline_input.text())
        self.settings.setValue("auto_upper", self.auto_upper_check.isChecked())
        self.settings.setValue("enable_custom_text", self.custom_text_check.isChecked())
        # Save splitter state if needed, usually complicated with widget refs, skipping for simplicity

    def load_settings(self):
        if self.settings.value("city"):
            self.city_input.setText(self.settings.value("city"))
        if self.settings.value("country"):
            self.country_input.setText(self.settings.value("country"))
        
        theme = self.settings.value("theme")
        if theme:
            self.set_theme(theme)
            
        radius = self.settings.value("radius")
        if radius:
            self.radius_spin.setValue(int(radius))
            
        dpi = self.settings.value("dpi")
        if dpi:
            self.dpi_spin.setValue(int(dpi))
            
        if self.settings.value("title"):
            self.title_input.setText(self.settings.value("title"))
        if self.settings.value("subtitle"):
            self.subtitle_input.setText(self.settings.value("subtitle"))
        if self.settings.value("tagline"):
            self.tagline_input.setText(self.settings.value("tagline"))
            
        auto_upper = self.settings.value("auto_upper", type=bool)
        self.auto_upper_check.setChecked(True if auto_upper is None else auto_upper)
        
        enable_custom = self.settings.value("enable_custom_text", type=bool)
        self.custom_text_check.setChecked(False if enable_custom is None else enable_custom)

    def reset_defaults(self):
        self.city_input.clear()
        self.country_input.clear()
        self.preset_combo.setCurrentIndex(0) # Custom
        self.theme_combo.setCurrentIndex(0) # Default
        self.radius_spin.setValue(15000)
        self.dpi_spin.setValue(300)
        self.title_input.clear()
        self.subtitle_input.clear()
        self.tagline_input.clear()
        self.auto_upper_check.setChecked(True)
        self.custom_text_check.setChecked(False)
        self.status_label.setText("Defaults restored.")

    def apply_preset(self, preset_name):
        if preset_name == "Noir City":
            self.set_theme("noir")
            self.radius_spin.setValue(12000)
        elif preset_name == "Modern Minimal":
            self.set_theme("feature_based")
            self.radius_spin.setValue(10000)
        elif preset_name == "Retro Blueprint":
            self.set_theme("blueprint")
            self.radius_spin.setValue(8000)
        elif preset_name == "Cyberpunk Neon":
            self.set_theme("neon_cyberpunk")
            self.radius_spin.setValue(15000)

    def set_theme(self, theme_name):
        index = self.theme_combo.findText(theme_name)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

    def validate_input(self):
        if not self.city_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Please enter a city.")
            self.tabs.setCurrentWidget(self.tab_basic)
            self.city_input.setFocus()
            return False
        if not self.country_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Please enter a country.")
            self.tabs.setCurrentWidget(self.tab_basic)
            self.country_input.setFocus()
            return False
        return True

    def get_common_params(self):
        city = self.city_input.text().strip()
        country = self.country_input.text().strip()
        theme = self.theme_combo.currentText()
        distance = self.radius_spin.value()
        
        if self.custom_text_check.isChecked():
            title = self.title_input.text().strip()
            subtitle = self.subtitle_input.text().strip()
            tagline = self.tagline_input.text().strip()
            
            if self.auto_upper_check.isChecked() and subtitle:
                subtitle = subtitle.upper()
        else:
            title = None
            subtitle = None
            tagline = None
        
        return city, country, theme, distance, title, subtitle, tagline

    def sanitize_filename(self, name):
        # Keep alphanumerics, spaces, dashes, underscores
        clean = re.sub(r'[^a-zA-Z0-9 	-_]', '', name)
        return clean.strip().replace(' ', '_').lower()

    def toggle_ui(self, enable):
        self.btn_preview.setEnabled(enable)
        self.btn_preview_shortcut.setEnabled(enable)
        # Export only enabled if we have a preview and not generating
        self.btn_export.setEnabled(enable and self.current_preview_path is not None)
        
        self.city_input.setEnabled(enable)
        self.country_input.setEnabled(enable)
        self.is_generating = not enable
        if not enable:
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

    def generate_preview(self):
        if not self.validate_input():
            return
        
        city, country, theme, distance, title, subtitle, tagline = self.get_common_params()
        
        # Preview specific logic
        # 1. Sanitize city name for file
        safe_city = self.sanitize_filename(city)
        preview_filename = f"{safe_city}_preview.png"
        
        preview_file = os.path.abspath(os.path.join("output", preview_filename))
        if not os.path.exists("output"):
            os.makedirs("output")
            
        dpi = 72 # Fixed Low DPI for preview
        fast_mode = True 
        
        self.status_label.setText(f"Generating preview for {city}...")
        self.toggle_ui(False)
        
        self.generator = PosterGenerator(city, country, theme, distance, preview_file, dpi, title, subtitle, tagline, fast_mode)
        self.generator.progress_update.connect(self.update_status)
        self.generator.finished_success.connect(self.on_preview_ready)
        self.generator.finished_error.connect(self.on_error)
        self.generator.start()

    def export_poster(self):
        if not self.validate_input():
            return

        city, country, theme, distance, title, subtitle, tagline = self.get_common_params()
        
        # Export naming
        safe_city = self.sanitize_filename(city)
        safe_country = self.sanitize_filename(country)
        dpi = self.dpi_spin.value()
        
        default_name = f"{safe_city}_{safe_country}_{theme}_{distance}m_{dpi}dpi.png"
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Poster", os.path.join("output", default_name), "PNG Files (*.png)")
        
        if not output_path:
            return
            
        fast_mode = False
        
        self.status_label.setText(f"Exporting high-res poster...")
        self.toggle_ui(False)
        
        self.generator = PosterGenerator(city, country, theme, distance, output_path, dpi, title, subtitle, tagline, fast_mode)
        self.generator.progress_update.connect(self.update_status)
        self.generator.finished_success.connect(self.on_export_ready)
        self.generator.finished_error.connect(self.on_error)
        self.generator.start()

    def update_status(self, message):
        if len(message) > 60:
            message = message[:57] + "..."
        self.status_label.setText(message)

    def on_error(self, message):
        self.toggle_ui(True)
        self.status_label.setText("Error occurred.")
        QMessageBox.critical(self, "Generation Error", message)

    def on_preview_ready(self, file_path):
        self.toggle_ui(True)
        self.status_label.setText("Preview generated.")
        self.current_preview_path = file_path
        self.display_image(file_path)
        self.btn_export.setEnabled(True)

    def on_export_ready(self, file_path):
        self.toggle_ui(True)
        self.status_label.setText(f"Export complete.")
        QMessageBox.information(self, "Success", f"Poster saved to:\n{file_path}")

    def display_image(self, file_path):
        if not os.path.exists(file_path):
            return
        
        self.original_pixmap = QPixmap(file_path)
        self.update_image_view()

    def set_zoom(self, mode):
        self.zoom_mode = mode
        self.update_zoom_buttons()
        if self.current_preview_path:
            self.update_image_view()
            
    def update_zoom_buttons(self):
        self.btn_fit.setChecked(self.zoom_mode == "Fit")
        self.btn_50.setChecked(self.zoom_mode == 0.5)
        self.btn_100.setChecked(self.zoom_mode == 1.0)

    def update_image_view(self):
        if not hasattr(self, 'original_pixmap') or self.original_pixmap is None or self.original_pixmap.isNull():
            return
            
        if self.zoom_mode == "Fit":
            # In Fit mode, we let the scroll area layout handle the sizing via setWidgetResizable(True)
            # BUT QLabel needs to be told to scale its contents.
            # Actually, standard way:
            self.scroll_area.setWidgetResizable(True)
            # We scale the pixmap to the viewport size manually to look good?
            # Or just use setScaledContents(True) on label. 
            # setScaledContents(True) often leads to blurriness or aspect ratio issues if not handled carefully.
            # Better: Resize pixmap to fit viewport, update label.
            
            viewport_size = self.scroll_area.viewport().size()
            if viewport_size.isEmpty(): return # Avoid error on startup
            
            scaled_pixmap = self.original_pixmap.scaled(
                viewport_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            # Make sure label doesn't force expansion
            self.image_label.adjustSize()
            
        else:
            self.scroll_area.setWidgetResizable(False)
            scale = float(self.zoom_mode)
            new_size = self.original_pixmap.size() * scale
            self.image_label.setPixmap(self.original_pixmap.scaled(
                new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            self.image_label.resize(new_size)

    def open_output_folder(self):
        output_dir = os.path.abspath("output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        os.startfile(output_dir)

    def resizeEvent(self, event):
        if self.zoom_mode == "Fit":
            self.update_image_view()
        super().resizeEvent(event)
