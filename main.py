import sys
from PyQt6.uic import loadUi
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.user_interface.startScreen import startScreen
from src.data_processing.database import connect_to_database, create_file_name_tables, close_database
from src.user_interface.scraping_ui import scrapeCRKN
from src.utility.settings_manager import Settings
from src.utility.logger import m_logger
import os


def main():
    m_logger.info("Application started")
    settings_manager = Settings()
    settings_manager.load_settings()
    language = settings_manager.get_setting("language")

    app = QApplication(sys.argv)
    app.setApplicationDisplayName("ePat")
    widget = QtWidgets.QStackedWidget()
    start = startScreen.get_instance(widget)  # Pass the widget to startScreen
    widget.addWidget(start)

    widget.addWidget(start)
    widget.setMinimumHeight(800)
    widget.setMinimumWidth(1200)
    widget.show()

    if not os.path.exists(f"{os.path.abspath(os.path.dirname(__file__))}/../utility/settings.json"):
        # First start up. Create settings file.
        # Need to put some code here with the settings.
        pass
    if not os.path.exists(f"{os.path.abspath(os.path.dirname(__file__))}/../utility/ebook_database.db"):
        # Create database and structure
        connection_obj = connect_to_database()
        create_file_name_tables(connection_obj)
        close_database(connection_obj)

    if settings_manager.get_setting('allow_CRKN') == "True":
        reply = QMessageBox.question(None, 'Update CRKN' if language == "English" else "Mettre à jour de RCDR",
                                     'Would you like to update CRKN database before proceeding?' if language == "English" else "Souhaitez-vous mettre à jour la base de données du RCDR avant de continuer ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            scrapeCRKN()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
