from PyQt6.QtCore import pyqtSignal, QUrl, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import QDialog, QPushButton, QWidget, QTextEdit, QComboBox, QMessageBox
from src.user_interface.scraping_ui import scrapeCRKN
from src.utility.upload import upload_and_process_file
from src.utility.settings_manager import Settings
import os

settings_manager = Settings()


class settingsPage(QDialog):
    _instance = None
    # # Should emit signal to the settings for saving the institution
    institutionSelected = pyqtSignal(str)

    @classmethod
    def get_instance(cls, arg):
        if not cls._instance:
            cls._instance = cls(arg)
        return cls._instance
    
    @classmethod
    def replace_instance(cls, arg1):
        if cls._instance:
            # Remove the previous instance's reference from its parent widget
            cls._instance.setParent(None)
            # Explicitly delete the previous instance
            del cls._instance
            print("Deleting instance")
        cls._instance = cls(arg1)
        return cls._instance

    def __init__(self, widget):
        super(settingsPage, self).__init__()
        self.language_value = settings_manager.get_setting("language").lower()
        ui_file = os.path.join(os.path.dirname(__file__), f"{self.language_value}_settingsPage.ui")
        loadUi(ui_file, self)

        self.backButton2 = self.findChild(QPushButton, 'backButton')  # finding child pushButton from the parent class
        self.backButton2.clicked.connect(self.backToStartScreen2)
        self.widget = widget
        self.original_widget_values = None

        # Upload Button
        self.uploadButton = self.findChild(QPushButton, 'uploadButton')
        self.uploadButton.clicked.connect(self.upload_button_clicked)

        # Update Button
        self.updateButton = self.findChild(QPushButton, "updateCRKN")
        self.updateButton.clicked.connect(scrapeCRKN)

        self.update_CRKN_button()

        # Finding the combobox for the institution
        self.institutionSelection = self.findChild(QComboBox, 'institutionSelection')
        self.institutionSelection.activated.connect(self.save_institution)
        self.populate_institutions()
        self.set_institution(settings_manager.get_setting("institution"))

        # Find the Push Button for manage local database
        self.manageDatabaseButton = self.findChild(QPushButton, 'manageDatabase')
        self.manageDatabaseButton.clicked.connect(self.show_manage_local_databases_popup)

        # Finding the combobox for the SaveButton
        self.saveSettingsButton = self.findChild(QPushButton, 'saveSettings')
        self.saveSettingsButton.setToolTip("Click to save the settings")
        self.saveSettingsButton.clicked.connect(self.save_selected)

        # Finding the linkButton from the QPushButton class
        self.openLinkButton = self.findChild(QPushButton, 'helpButton')
        self.openLinkButton.setToolTip("Click to open the link")
        self.openLinkButton.clicked.connect(self.open_link)

        # Finding the languageButton from the QPushButton class
        self.languageSelection = self.findChild(QComboBox,'languageSetting') 
        self.languageSelection.activated.connect(self.save_language)
        self.languageSelection.setCurrentIndex(0 if settings_manager.get_setting("language") == "English" else 1)

        current_crkn_url = settings_manager.get_setting("CRKN_url")
        self.crknURL = self.findChild(QTextEdit, 'crknURL')
        self.crknURL.setPlainText(current_crkn_url)

        self.set_current_settings_values()

    def update_CRKN_button(self):
        # Grey out the Update CRKN button if Allow_CRKN is False
        allow_crkn = settings_manager.get_setting("allow_CRKN")
        if allow_crkn != "True":
            self.updateButton.setEnabled(False)

    def open_link(self):
        # Get the link from the settings manager or define it directly
        link = settings_manager.get_setting("github_link")

        # Open the link in the default web browser
        QDesktopServices.openUrl(QUrl(link))

    def backToStartScreen2(self):
        self.widget.removeWidget(self.widget.currentWidget())


    def populate_institutions(self):
        # Clear the existing items in the combo box
        self.institutionSelection.clear()

        # Get the list of institutions from the settings manager
        institutions = settings_manager.get_institutions()
        # print("institutions:", institutions)  # TEST to make sure

        # Populate the combo box with institution names
        self.institutionSelection.addItems(institutions)

    def set_institution(self, institution_value):
        # Iterate over the items in the combo box
        for index in range(self.institutionSelection.count()):
            if self.institutionSelection.itemText(index) == institution_value:
                # Set the current index to the item that matches the desired value
                self.institutionSelection.setCurrentIndex(index)
                break

    # Testing to save institution working
    def save_selected(self):
        self.save_institution()
        self.save_language()
        self.save_CRKN_URL()
        # self.addInstitution()      
        self.reset_app()

    def save_language(self):
        current_language = settings_manager.get_setting("language")
        selected_language = self.languageSetting.currentIndex()
        reply = QMessageBox.question(None, "Language Change" if current_language == "English" else "Changement de langue", 
                                     "Are you sure you want to change your language setting?" if current_language == "English" else "Êtes-vous sûr de vouloir modifier votre paramètre de langue ?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            settings_manager.set_language("English" if selected_language == 0 else "French")   
        self.reset_app() 
    
    def save_institution(self):
        selected_institution = self.institutionSelection.currentText()
        settings_manager.set_institution(selected_institution)
        self.reset_app()

    def save_CRKN_URL(self):
        crkn_url = self.findChild(QTextEdit, 'crknURL').toPlainText()

        if len(crkn_url.split("/")) < 3:
            QMessageBox.warning(self, "Incorrect URL format", "Incorrect URL format.\nEnsure URL begins with http:// or https://.",QMessageBox.StandardButton.Ok)
            return
        settings_manager.set_crkn_url(crkn_url)

    def keyPressEvent(self, event):
        # Override keyPressEvent method to ignore Escape key event
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()  # Ignore the Escape key event
        else:
            super().keyPressEvent(event)

    def addInstitution(self):
        """
        Used to add the institution currently in the settings page text field
        """
        add_institution_text = self.institutionSelection.currentText()
        
        all_institutions = settings_manager.get_institutions()
        if add_institution_text in all_institutions:
            QMessageBox.warning(self, "Duplicate institution", "The entered institution already exists.", QMessageBox.StandardButton.Ok)
            return

        # Add the new institution to the settings
        settings_manager.add_local_institution(add_institution_text)
        
    def reset_app(self):        
        widget_count = self.widget.count()
        for i in range(widget_count):
            current_widget = self.widget.widget(i)
            new_widget_instance = type(current_widget).replace_instance(self.widget)
            self.widget.insertWidget(i, new_widget_instance)
            self.widget.removeWidget(current_widget)
            current_widget.deleteLater()
        
        # Set the current index to the last widget added
        self.widget.setCurrentIndex(widget_count - 1)

    def update_all_sizes(self):
        """
        This was made by ChatGPT, do not sue me. 
        -Ethan
        Feb 27, 2024 
        """
        original_width = 1200
        original_height = 800
        new_width = self.width() + 25
        new_height = self.height()

        if self.original_widget_values is None:
            # If it's the first run, store the original values
            self.original_widget_values = {}
            for widget in self.findChildren(QWidget):
                self.original_widget_values[widget] = {
                    'geometry': widget.geometry(),
                    'font_size': widget.font().pointSize() if isinstance(widget, (QTextEdit, QComboBox)) else None
                }

        # Iterate through every widget loaded using loadUi
        for widget, original_values in self.original_widget_values.items():
            # Calculate new geometry and size for each widget
            x = int(original_values['geometry'].x() * (new_width / original_width))
            y = int(original_values['geometry'].y() * (new_height / original_height))
            width = int(original_values['geometry'].width() * (new_width / original_width))
            height = int(original_values['geometry'].height() * (new_height / original_height))

            # Set the new geometry and size
            widget.setGeometry(x, y, width, height)

            # If the widget is a QTextEdit or QComboBox, adjust font size
            if isinstance(widget, (QTextEdit, QComboBox)):
                font = widget.font()
                original_font_size = original_values['font_size']
                if original_font_size is not None:
                    font.setPointSize(int(original_font_size * (new_width / original_width)))
                widget.setFont(font)

    def resizeEvent(self, event):
        # Override the resizeEvent method to call update_all_sizes when the window is resized
        super().resizeEvent(event)
        self.update_all_sizes()

    def upload_button_clicked(self):
        upload_and_process_file()


    def set_current_settings_values(self):
        # Set the current language selection
        current_language = settings_manager.get_setting("language")
        language_index = self.languageSelection.findText(current_language, Qt.MatchFlag.MatchFixedString)
        if language_index >= 0:
            self.languageSelection.setCurrentIndex(language_index)

        # Set the current CRKN URL
        current_crkn_url = settings_manager.get_setting("CRKN_url")
        self.crknURL.setPlainText(current_crkn_url)

        # Set the current institution selection
        current_institution = settings_manager.get_setting("institution")
        institution_index = self.institutionSelection.findText(current_institution, Qt.MatchFlag.MatchFixedString)
        if institution_index >= 0:
            self.institutionSelection.setCurrentIndex(institution_index)

        # Update the state of the CRKN update button
        self.update_CRKN_button()

    def show_manage_local_databases_popup(self):
        from src.user_interface.manageDatabase import ManageLocalDatabasesPopup
        popup = ManageLocalDatabasesPopup(self)
        popup.exec()


#Error i am encountering right now is based on the adding of institution and checking out if they already exist.
#saving currently is not working as when clicked will shit down the application.
# I have to make the things working.

