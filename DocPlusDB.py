import os
import psycopg2
import xlwt
import json
import io
import textwrap
import requests
import subprocess
import time

from appdirs import user_config_dir
from psycopg2 import OperationalError

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QColor

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path


config_dir = user_config_dir("MyApp", "MyCompany")  # MyApp — имя приложения, MyCompany — имя разработчика
os.makedirs(config_dir, exist_ok=True)  # Создаем директорию, если её нет
config_path = os.path.join(config_dir, "config.json")  # Путь к файлу конфигурации


def load_config():
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

# Загружаем конфигурацию
config = load_config()

def save_config(config):
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

if not config:
    config = {
        "host": "10.10.0.63",
        "user": "postgres",
        "password": "admin",
        "db_name": "docplus",
        "port": "5432"
    }
    save_config(config)

# Извлекаем данные из конфигурации
host = config["host"]
user = config["user"]
password = config["password"]
db_name = config["db_name"]
port = config["port"]

# Версия
current_version = "2.1.1"
# Права админа
admin = None

#"""Автообновление"""
class AutoUpdater(QMainWindow):
    def __init__(self, current_version, local_exe="DocPlusDB.exe", new_exe="DocPlusDB_new.exe"):
        super(AutoUpdater, self).__init__()
        self.github_raw_url = "https://raw.githubusercontent.com/GarvelLoken1/DocPlusDB/main"
        self.current_version = current_version
        self.local_exe = local_exe
        self.new_exe = new_exe

        # """Для ошибок"""
        self.show_error = Show_Error()

        self.setFixedSize(250, 130)
        self.centralwidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle('Обновление')
        self.setWindowIcon(QtGui.QIcon(resource_path('logo.png')))
        self.font = QtGui.QFont("Times", 10)
        self.centralwidget.setFont(self.font)
        self.layout = QGridLayout(self.centralwidget)

        # Текст
        self.lable_update = QLabel()
        self.layout.addWidget(self.lable_update, 0, 0, 1, 2)

        # Прогрессбар
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.layout.addWidget(self.progress_bar, 1, 0, 1, 2)

        # Кнопка "Подключиться"
        self.btn_update = QPushButton("Обновить")
        self.btn_update.clicked.connect(self.download_and_replace)
        self.layout.addWidget(self.btn_update, 2, 0, 1, 1)

        # Кнопка "Отмена"
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.cancel)
        self.layout.addWidget(self.btn_cancel, 2, 1, 1, 1)


    def cancel(self):
        self.close()

    #"""Проверка версии и запуск обновления"""
    def check_for_update(self):

        try:
            remote_version = requests.get(f"{self.github_raw_url}/version.txt", timeout=5).text.strip()
            if remote_version != self.current_version:
                self.lable_update.setText(f"Найдена новая версия ({remote_version})!\n"
                                   f"Ваша версия {current_version}\n"
                                   f"Обновить?")
                print(f"Найдена новая версия:{remote_version}/{current_version}")
                self.show()
            else:
                print("Установлена последняя версия.")
                self.close()
        except Exception as e:
            self.show_error.show_error(e)

    #"""Скачивание новой версии и запуск"""
    def download_and_replace(self):
        try:
            self.lable_update.setText("Скачивание новой версии...")
            print("Скачивание новой версии...")
            self.btn_update.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            exe_url = f"https://github.com/GarvelLoken1/DocPlusDB/releases/latest/download/DocPlusDB.exe"
            with requests.get(exe_url, stream=True, timeout=10) as r:
                r.raise_for_status()
                total_length = int(r.headers.get('content-length', 0))
                downloaded = 0

                with open(self.new_exe, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = int((downloaded / total_length) * 100)
                        self.progress_bar.setValue(percent)
                        QtWidgets.QApplication.processEvents()  # обновить GUI
            print("Перезагрузка...")
            subprocess.Popen([self.new_exe])
            sys.exit()
        except Exception as e:
            self.show_error.show_error(e)

    #"""Заменяет старую версию новой и перезапускает"""
    def finalize_update(self):
        try:
            time.sleep(1)
            if os.path.exists(self.local_exe):
                os.remove(self.local_exe)
            os.rename(self.new_exe, self.local_exe)
            print("Обновление завершено. Перезапуск...")
            subprocess.Popen([self.local_exe])
            sys.exit()
        except Exception as e:
            self.show_error.show_error(e)

    #"""Проверка имени файла для переименования"""
    def run(self):

        if getattr(sys, 'frozen', False):
            if os.path.basename(sys.executable) == self.new_exe:
                self.finalize_update()
            else:
                self.check_for_update()
        else:
            self.check_for_update()

#"""Окно настроек"""
class Settings_Window(QMainWindow):
    def __init__(self, config):
        super(Settings_Window, self).__init__()
        self.config = config
        self.initial_size = (308, 197)
        self.resize(*self.initial_size)
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle('Вход')
        self.setWindowIcon(QtGui.QIcon(resource_path('logo.png')))
        self.centralwidget.setFont(QtGui.QFont("Times", 10))

        #"""Для ошибок"""
        self.show_error = Show_Error()

        self.layout = QVBoxLayout(self.centralwidget)

        # Логин
        self.lable_login = QLabel("Пользователь:")
        self.layout.addWidget(self.lable_login)
        self.login = QtWidgets.QComboBox(self.centralwidget)
        self.layout.addWidget(self.login)
        self.login.addItems(['Администратор', 'Пользователь'])
        self.login.currentTextChanged.connect(self.password_enable)

        # Пароль
        self.lable_login_password = QLabel("Пароль:")
        self.layout.addWidget(self.lable_login_password)
        self.login_password = QtWidgets.QLineEdit(self.centralwidget)
        self.login_password.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.login_password)


        # Кнопка "Подключиться"
        self.btn_connect = QPushButton("Подключиться")
        self.btn_connect.clicked.connect(self.connect)
        self.layout.addWidget(self.btn_connect)

        # Клавиша Enter
        self.Enter_Key = QShortcut(Qt.Key_Return, self)
        self.Enter_Key.activated.connect(self.connect)

        # Клавиша F1
        self.F1_Key = QShortcut(Qt.Key_F1, self)
        self.F1_Key.activated.connect(self.fast_connect)

        # Выйти
        self.btn_exit = QtWidgets.QPushButton("Выйти")
        self.btn_exit.clicked.connect(self.exit)
        self.layout.addWidget(self.btn_exit)

        ### "Настройки подключения"

        # Кнопка с иконкой стрелки
        self.toggle_button = QToolButton(self.centralwidget)
        self.toggle_button.setText("Настройки подключения")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)  # Стрелка вправо для свернутого состояния
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet("QToolButton { border: none; text-align: left; }")
        self.toggle_button.clicked.connect(self.toggle_settings)
        self.layout.addWidget(self.toggle_button)

        # Контейнер для виджетов настроек
        self.settings_container = QWidget(self.centralwidget)
        self.settings_layout = QGridLayout(self.settings_container)

        # Добавляем виджеты в контейнер настроек
        self.lable_ip = QLabel("Адрес:")
        self.settings_layout.addWidget(self.lable_ip, 0, 0)
        self.ip = QtWidgets.QLineEdit(self.centralwidget)
        self.settings_layout.addWidget(self.ip, 1, 0)
        self.ip.setText(host)
        self.ip.setEnabled(False)

        self.lable_port = QLabel("Порт:")
        self.settings_layout.addWidget(self.lable_port, 2, 0, alignment=Qt.AlignLeft)
        self.port = QtWidgets.QLineEdit(self.centralwidget)
        self.settings_layout.addWidget(self.port, 3, 0)
        self.port.setText(str(port))
        self.port.setEnabled(False)

        self.lable_db_name = QLabel("База:")
        self.settings_layout.addWidget(self.lable_db_name, 4, 0, alignment=Qt.AlignLeft)
        self.db_name = QtWidgets.QLineEdit(self.centralwidget)
        self.settings_layout.addWidget(self.db_name, 5, 0)
        self.db_name.setText(db_name)
        self.db_name.setEnabled(False)

        self.lable_user = QLabel("Пользователь:")
        self.settings_layout.addWidget(self.lable_user, 0, 1)
        self.user = QtWidgets.QLineEdit(self.centralwidget)
        self.settings_layout.addWidget(self.user, 1, 1)
        self.user.setText(user)
        self.user.setEnabled(False)

        self.lable_password = QLabel("Пароль:")
        self.settings_layout.addWidget(self.lable_password, 2, 1)
        self.password = QtWidgets.QLineEdit(self.centralwidget)
        self.settings_layout.addWidget(self.password, 3, 1)
        self.password.setText(password)
        self.password.setEnabled(False)

        self.btn_change = QPushButton("Изменить")
        self.btn_change.clicked.connect(self.change)
        self.settings_layout.addWidget(self.btn_change, 5, 1)
        self.btn_change.setHidden(False)

        self.btn_save = QtWidgets.QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save)
        self.settings_layout.addWidget(self.btn_save, 5, 1)
        self.btn_save.setHidden(True)

        # Изначально контейнер скрыт
        self.settings_container.setVisible(False)

        # Добавляем контейнер в основной макет
        self.layout.addWidget(self.settings_container)


    #"""Настройка настроек"""
    def toggle_settings(self):
        """Переключает видимость контейнера с настройками и изменяет размер окна"""
        is_visible = not self.settings_container.isVisible()
        self.settings_container.setVisible(is_visible)
        self.toggle_button.setArrowType(Qt.DownArrow if is_visible else Qt.RightArrow)

        # Принудительно обновляем интерфейс
        QApplication.processEvents()
        self.adjustSize()
        # Изменяем размер окна
        if is_visible:
            self.adjustSize()
        else:
            self.resize(308,197)

    #"""Подверждение пароля"""
    def password_enable(self):
        if self.login.currentText() == 'Пользователь':
            self.login_password.setEnabled(False)
        else:
            self.login_password.setEnabled(True)

    #"""Подключиться"""
    def connect(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                cur.execute(
                    f"SELECT users.password "
                    f"FROM users "
                    f"WHERE users.user = '{str(self.login.currentText())}'"
                )
                login_password = cur.fetchall()
                login_password = ','.join(map(str, login_password))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    #print(login_password)
                    login_password = str(login_password.replace(*r))
                print("Логин:", self.login.currentText())
                if self.login.currentText() == "Администратор":
                    if self.login_password.text() == login_password:
                        print("Пароль:", login_password)
                        global admin
                        admin = True
                        print("Права админа:", admin)
                        self.main_window = Main_Window()
                        self.main_window.show()
                        self.close()
                    else:
                        error = QMessageBox()
                        error.setWindowTitle("Ошибка")
                        error.setText("Неверный пароль!")
                        error.setIcon(QMessageBox.Warning)
                        error.setStandardButtons(QMessageBox.Ok)
                        error.exec_()
                else:
                    self.main_window = Main_Window()
                    self.main_window.show()
                    self.close()

        except Exception as e:
            self.show_error.show_error(e)

    #"""Быстрое подключение"""
    def fast_connect(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            global admin
            admin = True
            print("Права админа:", admin)
            self.main_window = Main_Window()
            self.main_window.show()
            self.close()
        except Exception as e:
            self.show_error.show_error(e)

    #"""Изменить"""
    def change(self):
        self.btn_change.setHidden(True)
        self.btn_save.setHidden(False)
        self.btn_connect.setEnabled(False)
        self.ip.setEnabled(True)
        self.port.setEnabled(True)
        self.db_name.setEnabled(True)
        self.user.setEnabled(True)
        self.password.setEnabled(True)

    #"""Сохранить"""
    def save(self):

        save_message = QMessageBox()
        save_message.setWindowTitle("Изменение")
        save_message.setText("Изменить настройки?")
        save_message.setIcon(QMessageBox.Question)
        save_message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        save_message.exec_()
        self.btn_connect.setEnabled(True)
        self.ip.setEnabled(False)
        self.port.setEnabled(False)
        self.db_name.setEnabled(False)
        self.user.setEnabled(False)
        self.password.setEnabled(False)
        self.btn_change.setHidden(False)
        self.btn_save.setHidden(True)
        if save_message.standardButton(save_message.clickedButton()) == QMessageBox.Yes:
            self.config["host"] = self.ip.text()
            self.config["port"] = self.port.text()
            self.config["db_name"] = self.db_name.text()
            self.config["user"] = self.user.text()
            self.config["password"] = self.password.text()

            # Сохраняем изменения в файл
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            global host, port, db_name, user, password
            host = self.config["host"]
            port = self.config["port"]
            db_name = self.config["db_name"]
            user = self.config["user"]
            password = self.config["password"]

            # Закрываем текущее окно настроек
            #self.close()
            change_message = QMessageBox()
            change_message.setWindowTitle("Успешно")
            change_message.setText("Данные изменены")
            change_message.setIcon(QMessageBox.Information)
            change_message.setStandardButtons(QMessageBox.Ok)
            change_message.exec_()
            print('УСПЕШНО ИЗМЕНЕНО!')
            new_login_window = Settings_Window(self.config)
            new_login_window.show()
        else:
            print('ОТМЕНА')
            change_message = QMessageBox()
            change_message.setWindowTitle("Отмена")
            change_message.setText("Данные НЕ изменены")
            change_message.setIcon(QMessageBox.Information)
            change_message.setStandardButtons(QMessageBox.Ok)
            change_message.exec_()

    #"""Выйти"""
    def exit(self):
        sys.exit(app.exec_())

#"""Главное окно"""
class Main_Window(QMainWindow):
    def __init__(self):
        super(Main_Window, self).__init__()
        self.resize(1400, 900)
        self.centralwidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle('DocPlusDB')
        self.setWindowIcon(QtGui.QIcon(resource_path('logo.png')))
        self.font = QtGui.QFont("Times", 10)
        self.centralwidget.setFont(self.font)
        self.tabs = QtWidgets.QTabWidget(self.centralwidget)
        self.tab_items = QtWidgets.QWidget()
        self.tab_repairs = QtWidgets.QWidget()
        self.tabs.addTab(self.tab_items, 'Оборудование')
        self.tabs.addTab(self.tab_repairs, 'Журнал')
        self.statusBar().showMessage(f"Версия {current_version} | © Максименко Н.А. | 2025")

        #"""Для ошибок"""
        self.show_error = Show_Error()

        #"""Таймер для таблицы"""
        self.resize_timer = QTimer()  # Таймер для отложенного пересчета
        self.resize_timer.setSingleShot(True)  # Таймер сработает только один раз
        self.resize_timer.timeout.connect(lambda: self.resize_rows_to_contents_tables(self.table))


        #"""Поиск"""
        self.search_groupe = QtWidgets.QGroupBox('Поиск', self.tab_items)

        #"""Кнопка Очистить"""
        self.btn_clear = QtWidgets.QPushButton(self.search_groupe)
        self.btn_clear.setText("Очистить")
        self.btn_clear.clicked.connect(lambda: self.start_clear(self.table))
        self.btn_clear.setFixedWidth(100)

        #"""Кнопка Поиска"""
        self.btn_search = QtWidgets.QPushButton(self.search_groupe)
        self.btn_search.setText("Поиск")
        #self.btn_search.setFixedWidth(100)
        self.btn_search.clicked.connect(lambda: self.start_search(self.table, self.search_for_what, self.search_for_what2,
                                                                  self.search_for_what3, self.search_for_what4, self.search_for_what5, self.search_for_what6,
                                                                  self.search, self.search2, self.start_resize_timer, self.resize_timer, self.btn_save, self.status_row_colors))

        #"""Кнопка Сохранить"""
        self.btn_save = QtWidgets.QPushButton(self.search_groupe)
        self.btn_save.setText("Сохранить")
        self.btn_save.setEnabled(False)
        self.btn_save.setFixedWidth(100)
        self.btn_save.clicked.connect(lambda: self.save_table(self.table))

        #"""Таблица"""
        self.table = QtWidgets.QTableWidget(self.search_groupe)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.itemDoubleClicked.connect(lambda: self.equipment_show(self.table))

        #"""Поисковая строка №1"""
        self.search = QtWidgets.QLineEdit(self.search_groupe)

        #"""Поисковая строка №2"""
        self.search2 = QtWidgets.QLineEdit(self.search_groupe)
        self.search2.setVisible(False)
        self.search2.setEnabled(False)

        #"""Фильтр поиска №1"""
        self.search_for_what = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what.setMinimumWidth(130)
        self.search_for_what.addItems(['Всё', 'По Адресу', 'По Оборудованию', 'По Имени', 'По Статусу'])
        self.search_for_what.currentTextChanged.connect(lambda: self.sfw2(
            self.search, self.search_for_what, self.search_for_what2, self.search_for_what3, self.btn_more_filters))
        self.search_for_what.currentTextChanged.connect(lambda: self.update_filters(self.search_for_what, self.search_for_what4, self.start_more_filters))
        self.search_for_what.currentTextChanged.connect(lambda: self.more_filters_visible(
            self.search_for_what, self.btn_more_filters, self.more_filters))

        #"""Фильтр поиска №2"""
        self.search_for_what2 = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what2.setMinimumWidth(350)
        self.search_for_what2.currentTextChanged.connect(lambda: self.sfw3(self.search_for_what, self.search_for_what2, self.search_for_what3))

        #"""Фильтр поиска №3"""
        self.search_for_what3 = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what3.setMinimumWidth(150)

        #"""Фильтр поиска №4"""
        self.search_for_what4 = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what4.setMinimumWidth(130)
        self.search_for_what4.addItems(['По Адресу', 'По Оборудованию', 'По Имени', 'По Статусу'])
        self.search_for_what4.currentTextChanged.connect(lambda: self.sfw2(
            self.search2, self.search_for_what4, self.search_for_what5, self.search_for_what6, self.btn_more_filters))
        self.search_for_what4.currentTextChanged.connect(lambda: self.update_filters(self.search_for_what, self.search_for_what4, self.start_more_filters))
        self.search_for_what4.setVisible(False)
        self.search_for_what4.setEnabled(False)

        #"""Фильтр поиска №5"""
        self.search_for_what5 = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what5.setMinimumWidth(350)
        self.search_for_what5.currentTextChanged.connect(lambda: self.sfw3(
            self.search_for_what4, self.search_for_what5, self.search_for_what6))
        self.search_for_what5.setVisible(False)
        self.search_for_what5.setEnabled(False)

        #"""Фильтр поиска №6"""
        self.search_for_what6 = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what6.setMinimumWidth(150)
        self.search_for_what6.setVisible(False)
        self.search_for_what6.setEnabled(False)

        #"""Кнопка развернуть доп фильтры"""
        self.btn_more_filters = QtWidgets.QPushButton(self.search_groupe)
        self.btn_more_filters.setFixedWidth(25)
        self.btn_more_filters.setText("+")
        self.btn_more_filters.clicked.connect(self.more_filters)
        self.start_more_filters = False

        #"""Слои"""
        self.layout = QGridLayout(self.centralwidget)
        self.layout.addWidget(self.tabs, 0, 0)
        self.layout_1 = QGridLayout(self.tab_items)
        self.layout_1.addWidget(self.search_groupe, 0, 0)
        self.layout_search = QGridLayout(self.search_groupe)
        self.layout_search.addWidget(self.search_for_what, 1, 1)
        self.layout_search.addWidget(self.search_for_what2, 1, 2)
        self.layout_search.addWidget(self.search_for_what3, 1, 3)
        self.layout_search.addWidget(self.search_for_what4, 2, 1)
        self.layout_search.addWidget(self.search_for_what5, 2, 2)
        self.layout_search.addWidget(self.search_for_what6, 2, 3)
        self.layout_search.addWidget(self.search, 1, 4)
        self.layout_search.addWidget(self.search2, 2, 4)
        self.layout_search.addWidget(self.btn_search, 1, 5, 1, 1)
        self.layout_search.addWidget(self.table, 3, 0, 1, 6)
        self.layout_search.addWidget(self.btn_save, 4, 0, 1, 2)
        self.layout_search.addWidget(self.btn_clear, 4, 5)
        self.layout_search.addWidget(self.btn_more_filters, 1, 0)


        ###"""ДОБАВЛЕНИЕ"""###

        self.add_groupe = QtWidgets.QGroupBox('Добавление', self.centralwidget)
        self.add_groupe.setGeometry(10, 630, 880, 160)

        #"""Улица"""
        self.add_lable_address = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_address.setText('Адрес:')
        self.add_CB_address = QtWidgets.QComboBox(self.add_groupe)
        self.add_CB_address.setFixedWidth(350)
        self.add_CB_address.currentTextChanged.connect(self.add_room_update)

        #"""Кабинет"""
        self.add_lable_room = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_room.setText('Кабинет:')
        self.add_CB_room = QtWidgets.QComboBox(self.add_groupe)
        self.add_CB_room.setVisible(True)
        self.add_LE_room = QtWidgets.QLineEdit(self.add_groupe)
        self.add_LE_room.setVisible(False)
        self.add_CB_room.setFixedWidth(350)
        self.add_LE_room.setFixedWidth(350)

        #"""Добавить кабинет"""
        self.btn_more_rooms = QtWidgets.QPushButton(self.search_groupe)
        self.btn_more_rooms.setFixedWidth(25)
        self.btn_more_rooms.setText("+")
        self.more_rooms_rule = False
        self.btn_more_rooms.clicked.connect(lambda: self.add_something_show("room"))


        #"""Тип оборудования"""
        self.add_lable_type = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_type.setText('Оборудование:')
        self.add_CB_type = QtWidgets.QComboBox(self.add_groupe)
        self.add_CB_type.setFixedWidth(350)
        self.add_CB_type.currentTextChanged.connect(lambda: self.sfw2(
            self.search, self.search_for_what, self.search_for_what2, self.search_for_what3, self.btn_more_filters))

        #"""Добавить тип оборудования"""
        self.btn_more_types = QtWidgets.QPushButton(self.search_groupe)
        self.btn_more_types.setFixedWidth(25)
        self.btn_more_types.setText("+")
        self.more_types_rule = False
        self.btn_more_types.clicked.connect(lambda: self.add_something_show("type"))


        #"""Имя"""
        self.add_lable_name = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_name.setText('Наименование:')
        self.add_name = QtWidgets.QLineEdit(self.add_groupe)
        self.add_name.setFixedWidth(350)

        #"""Серийный номер"""
        self.add_lable_sn = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_sn.setText('Серийный номер:')
        self.add_sn = QtWidgets.QLineEdit(self.add_groupe)
        self.add_sn.setFixedWidth(350)

        #"""Год выпуска"""
        self.add_lable_date = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_date.setText('Год выпуска:')
        self.add_date = QtWidgets.QLineEdit(self.add_groupe)
        self.add_date.setFixedWidth(350)

        #"""Кнопка Добавить"""
        self.btn_add = QtWidgets.QPushButton(self.add_groupe)
        self.btn_add.setFixedWidth(100)
        self.btn_add.setText("Добавить")
        self.btn_add.clicked.connect(self.start_add)

        #"""Кнопка Очистить"""
        self.btn_add_clear = QtWidgets.QPushButton(self.add_groupe)
        self.btn_add_clear.setFixedWidth(100)
        self.btn_add_clear.setText("Очистить")
        self.btn_add_clear.clicked.connect(self.start_add_clear)
        if not admin:
            self.add_groupe.setVisible(False)

        #"""Слои"""
        self.layout_1.addWidget(self.add_groupe, 1, 0)
        self.layout_add = QGridLayout(self.add_groupe)
        self.layout_add.setColumnStretch(4, 1)
        self.layout_add.addWidget(self.add_lable_address, 0, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_CB_address, 1, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_room, 2, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_CB_room, 3, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_LE_room, 3, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_type, 4, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_CB_type, 5, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.btn_more_rooms, 3, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.btn_more_types, 5, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_name, 0, 3, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_name, 1, 3, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_sn, 2, 3, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_sn, 3, 3, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_date, 4, 3, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_date, 5, 3, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.btn_add, 1, 4, alignment = QtCore.Qt.AlignRight)
        self.layout_add.addWidget(self.btn_add_clear, 5, 4, alignment = QtCore.Qt.AlignRight)


        ###"""ЖУРНАЛ"""


        #"""Таблица ремонтов"""
        self.table_repair = QtWidgets.QTableWidget(self.tab_repairs)
        self.table_repair.setMinimumHeight(150)

        #"""Таймнер для таблицы поиска ремонтв"""
        self.resize_timer_repair = QTimer()  # Таймер для отложенного пересчета
        self.resize_timer_repair.setSingleShot(True)  # Таймер сработает только один раз
        self.resize_timer_repair.timeout.connect(lambda: self.resize_rows_to_contents_tables(self.table_repair))

        #"""КНОПКА ПОИСКА РЕМОНТОВ"""
        self.btn_search_repair = QtWidgets.QPushButton(self.tab_repairs)
        self.btn_search_repair.setText("Поиск")
        self.btn_search_repair.setFixedWidth(100)
        self.btn_search_repair.clicked.connect(lambda: self.start_search(self.table_repair, self.search_for_what_repair, self.search_for_what_repair2,
                                                                         self.search_for_what_repair3, self.search_for_what_repair4, self.search_for_what_repair5, self.search_for_what_repair6,
                                                                         self.search_repair, self.search_repair2, self.start_resize_timer, self.resize_timer_repair, self.btn_save_repair, self.status_row_colors))

        #"""Фильтр поиска ремонтов №1"""
        self.search_for_what_repair = QtWidgets.QComboBox(self.tab_repairs)
        self.search_for_what_repair.setMinimumWidth(130)
        self.search_for_what_repair.addItems(['Всё', 'По Адресу', 'По Оборудованию', 'По Имени', 'По Статусу', 'По Типу Работ'])
        self.search_for_what_repair.currentTextChanged.connect(lambda: self.sfw2(
            self.search_repair, self.search_for_what_repair, self.search_for_what_repair2, self.search_for_what_repair3, self.btn_more_filters_repair))
        self.search_for_what_repair.currentTextChanged.connect(lambda: self.update_filters(self.search_for_what_repair, self.search_for_what_repair4, self.start_more_filters_repairs))
        self.search_for_what_repair.currentTextChanged.connect(lambda: self.more_filters_visible(
            self.search_for_what_repair, self.btn_more_filters_repair, self.more_filters_repair))

        #"""Фильтр поиска ремонтов №2"""
        self.search_for_what_repair2 = QtWidgets.QComboBox(self.tab_repairs)
        self.search_for_what_repair2.setMinimumWidth(250)
        self.search_for_what_repair2.currentTextChanged.connect(lambda: self.sfw3(
            self.search_for_what_repair, self.search_for_what_repair2, self.search_for_what_repair3))
        self.search_for_what_repair2.setEnabled(False)

        #"""Фильтр поиска ремонтов №3"""
        self.search_for_what_repair3 = QtWidgets.QComboBox(self.tab_repairs)
        self.search_for_what_repair3.setMinimumWidth(150)
        self.search_for_what_repair3.setEnabled(False)

        #"""Фильтр поиска ремонтов №4"""
        self.search_for_what_repair4 = QtWidgets.QComboBox(self.tab_repairs)
        self.search_for_what_repair4.setMinimumWidth(130)
        self.search_for_what_repair4.addItems(['По Адресу', 'По Оборудованию', 'По Имени', 'По Статусу', 'По Типу Работ'])
        self.search_for_what_repair4.currentTextChanged.connect(lambda: self.sfw2(
            self.search_repair2, self.search_for_what_repair4, self.search_for_what_repair5, self.search_for_what_repair6, self.btn_more_filters_repair))
        self.search_for_what_repair4.currentTextChanged.connect(lambda: self.update_filters(self.search_for_what_repair, self.search_for_what_repair4, self.start_more_filters_repairs))
        self.search_for_what_repair4.setVisible(False)
        self.search_for_what_repair4.setEnabled(False)

        #"""Фильтр поиска ремонтов №5"""
        self.search_for_what_repair5 = QtWidgets.QComboBox(self.tab_repairs)
        self.search_for_what_repair5.setMinimumWidth(350)
        self.search_for_what_repair5.currentTextChanged.connect(lambda: self.sfw3(
            self.search_for_what_repair4, self.search_for_what_repair5, self.search_for_what_repair6))
        self.search_for_what_repair5.setVisible(False)
        self.search_for_what_repair5.setEnabled(False)

        #"""Фильтр поиска ремонтов №6"""
        self.search_for_what_repair6 = QtWidgets.QComboBox(self.tab_repairs)
        self.search_for_what_repair6.setMinimumWidth(150)
        self.search_for_what_repair6.setVisible(False)
        self.search_for_what_repair6.setEnabled(False)

        #"""Поисковая строка ремонтов"""
        self.search_repair = QtWidgets.QLineEdit(self.tab_repairs)
        self.search_repair.setEnabled(False)
        self.table_repair.itemDoubleClicked.connect(lambda: self.equipment_show(self.table_repair))

        #"""Поисковая строка ремонтов №2"""
        self.search_repair2 = QtWidgets.QLineEdit(self.tab_repairs)
        self.search_repair2.setVisible(False)
        self.search_repair2.setEnabled(False)

        #"""КНОПКА ОЧИСТИТЬ"""
        self.btn_clear_repair = QtWidgets.QPushButton(self.tab_repairs)
        self.btn_clear_repair.setText("Очистить")
        self.btn_clear_repair.clicked.connect(lambda: self.start_clear(self.table_repair))
        self.btn_clear_repair.setFixedWidth(100)

        #"""Кнопка Сохранить"""
        self.btn_save_repair = QtWidgets.QPushButton(self.tab_repairs)
        self.btn_save_repair.setText("Сохранить")
        self.btn_save_repair.setFixedWidth(100)
        self.btn_save_repair.clicked.connect(lambda: self.save_table(self.table_repair))

        #"""Кнопка Развернуть Доп Фильтры"""
        self.btn_more_filters_repair = QtWidgets.QPushButton(self.tab_repairs)
        self.btn_more_filters_repair.setFixedWidth(25)
        self.btn_more_filters_repair.setText("+")
        self.btn_more_filters_repair.clicked.connect(self.more_filters_repair)
        self.start_more_filters_repairs = False

        #"""СЛОИ"""
        self.layout_repair = QGridLayout(self.tab_repairs)
        self.layout_repair.addWidget(self.btn_more_filters_repair, 1, 0)
        self.layout_repair.addWidget(self.search_for_what_repair, 1, 1)
        self.layout_repair.addWidget(self.search_for_what_repair2, 1, 2)
        self.layout_repair.addWidget(self.search_for_what_repair3, 1, 3)
        self.layout_repair.addWidget(self.search_for_what_repair4, 2, 1)
        self.layout_repair.addWidget(self.search_for_what_repair5, 2, 2)
        self.layout_repair.addWidget(self.search_for_what_repair6, 2, 3)
        self.layout_repair.addWidget(self.search_repair, 1, 4)
        self.layout_repair.addWidget(self.search_repair2, 2, 4)
        self.layout_repair.addWidget(self.btn_search_repair, 1, 5)
        self.layout_repair.addWidget(self.table_repair, 3, 0, 1, 6)
        self.layout_repair.addWidget(self.btn_save_repair, 4, 0, 1, 2)
        self.layout_repair.addWidget(self.btn_clear_repair, 4, 5, 1, 1)

        self.add_all()
        self.add_type_update()
        self.start_search(self.table, self.search_for_what, self.search_for_what2,
                                   self.search_for_what3, self.search_for_what4, self.search_for_what5,
                                   self.search_for_what6,
                                   self.search, self.search2, self.start_resize_timer, self.resize_timer, self.btn_save,
                                   self.status_row_colors)
        self.start_search(self.table_repair, self.search_for_what_repair, self.search_for_what_repair2,
                                   self.search_for_what_repair3, self.search_for_what_repair4,
                                   self.search_for_what_repair5, self.search_for_what_repair6,
                                   self.search_repair, self.search_repair2, self.start_resize_timer,
                                   self.resize_timer_repair, self.btn_save_repair, self.status_row_colors)
        self.more_filters_visible(self.search_for_what, self.btn_more_filters, self.more_filters)
        self.more_filters_visible(self.search_for_what_repair, self.btn_more_filters_repair, self.more_filters_repair)

    #"""Настройка добавления оборудования"""

    def add_all(self):
            try:
                con = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with con.cursor() as cur:

                    #"""Выбор Улицы"""
                    cur.execute("SELECT street FROM streets")
                    x = cur.fetchall()
                    x = ',,'.join(map(str, x))
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    self.add_CB_address.addItems(x.split(',,'))

                    #"""Имя"""
                    cur.execute("SELECT DISTINCT name FROM names")
                    x = cur.fetchall()
                    #print(x)
                    x = ',,'.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    completer = QCompleter(x.split(',,'))
                    self.add_name.setCompleter(completer)
                    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

            except Exception as e:
                self.show_error.show_error(e)

    #"""Обновление Добавление комнаты, относительно улицы"""
    def add_room_update(self):
        self.add_CB_room.clear()
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                cur.execute(
                    """
                    SELECT address.room 
                    FROM address 
                    INNER JOIN streets ON street_id = streets.id 
                    WHERE streets.street = %s
                    ORDER BY
                        regexp_replace(room, '\\d+', '', 'g'),
                        CAST(NULLIF(regexp_replace(room, '\\D+', '', 'g'), '') AS INTEGER)
                        """,
                            (
                                self.add_CB_address.currentText(),
                                )
                            )
                x = cur.fetchall()
                x = ',,'.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                # print(x.split(','))
                self.add_CB_room.addItems(x.split(',,'))
        except Exception as e:
            self.show_error.show_error(e)

    #"""Обновление оборудования"""
    def add_type_update(self):
        self.add_CB_type.clear()
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                cur.execute("SELECT type FROM types "
                            "ORDER BY type ASC ")
                x = cur.fetchall()
                x = ',,'.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                # print(x.split(','))
                self.add_CB_type.addItems(x.split(',,'))
        except Exception as e:
            self.show_error.show_error(e)

    #"""Очистка таблицы"""
    def start_clear(self, table):
        table.clearContents()

    #"""Кнопка Поиска"""
    def start_search(self, table, search_for_what, search_for_what2, search_for_what3, search_for_what4, search_for_what5, search_for_what6,
                     search, search2, start_resize_timer, resize_timer, btn_save, status_row_colors):
        #print('Создание таблицы 1')
        table.clearContents()
        table.clear()
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                if table == self.table:
                    query = f"""
                        SELECT equipments.id, streets.street, address.room, types.type, 
                               names.name, names.sn, names.date, status.status 
                        FROM equipments 
                        INNER JOIN address ON address.id = equipments.address_id 
                        INNER JOIN types ON types.id = equipments.type_id 
                        INNER JOIN names ON names.id = equipments.name_id 
                        INNER JOIN status ON status.id = equipments.status_id 
                        INNER JOIN streets ON street_id = streets.id 
                        
                    """
                else:
                    query = f"""
                        SELECT equipments.id, repairs.date, streets.street, address.room, types.type, 
                                names.name, names.sn, names.date, repairs.fault, repairs.repair, 
                                types_of_repairs.type_of_repair, status.status, repairs.repairman 
                        FROM repairs 
                        INNER JOIN equipments ON equipments.id = repairs.equipments_id 
                        INNER JOIN address ON address.id = equipments.address_id 
                        INNER JOIN types ON types.id = equipments.type_id 
                        INNER JOIN names ON names.id = equipments.name_id 
                        INNER JOIN streets ON street_id = streets.id 
                        INNER JOIN status ON status.id = repairs.status_id 
                        INNER JOIN types_of_repairs ON types_of_repairs.id = repairs.types_of_repairs_id 
                                        
                    """
                # Параметры для запроса
                params = []

                #"""Первый фильтр"""
                if search_for_what2.isEnabled():
                    search_field = {
                        'По Адресу': 'streets.street',
                        'По Оборудованию': 'types.type',
                        'По Имени': 'names.name',
                        'По Статусу': 'status.status',
                        'По Типу Работ': 'types_of_repairs.type_of_repair'
                    }.get(search_for_what.currentText())
                    query += f" WHERE {search_field} = %s"

                    # Добавление к параметрам для запроса по первому фильтру
                    params.append(str(search_for_what2.currentText()))

                    #"""Второй фильтр"""

                    if search_for_what3.isEnabled() and search_for_what3.currentText() != 'Всё':
                        search_field_2 = {
                            'По Адресу': 'address.room',
                        }.get(search_for_what.currentText())
                        query += f" AND {search_field_2} = %s"

                        # Добавление к параметрам для запроса по второму фильтру
                        params.append(str(search_for_what3.currentText()))

                    #"""Третий фильтр"""

                if search_for_what4.isEnabled() and search_for_what5.isEnabled():
                    search_field_3 = {
                        'По Адресу': 'streets.street',
                        'По Оборудованию': 'types.type',
                        'По Имени': 'names.name',
                        'По Статусу': 'status.status',
                        'По Типу Работ': 'types_of_repairs.type_of_repair'
                    }.get(search_for_what4.currentText())
                    query += f" AND {search_field_3} = %s"

                    #"""Четвертый фильтр"""

                    if search_for_what6.isEnabled() and search_for_what6.currentText() != 'Всё':
                        search_field_4 = {
                            'По Адресу': 'address.room',
                        }.get(search_for_what4.currentText())
                        query += f" AND {search_field_4} = %s"

                        # Добавление к параметрам для запроса по четвертому фильтру
                        params.append(str(search_for_what6.currentText()))

                    # Добавление к параметрам для запроса по третьему фильтру
                    params.append(str(search_for_what5.currentText()))


                if search.isEnabled():
                    query += " WHERE to_tsvector(name) @@ plainto_tsquery(%s)"
                    params.append(search.text())

                if search2.isEnabled():
                    query += " AND to_tsvector(name) @@ plainto_tsquery(%s)"
                    params.append(search2.text())
                query += f"""
                        ORDER BY
                        regexp_replace(room, '\\d+', '', 'g'),
                        CAST(NULLIF(regexp_replace(room, '\\D+', '', 'g'), '') AS INTEGER) """
                #print(query)
                cur.execute(query, tuple(params))

                #"""Формирование таблицы"""

                data = cur.fetchall()
                a = len(data)
                b = len(data[0]) if a > 0 else 0

                table.setRowCount(a)
                table.setColumnCount(b)
                table.setSortingEnabled(False)
                for j in range(a):
                    for i in range(b):
                        item = SmartItem(str(data[j][i]))
                        table.setItem(j, i, item)
                if table == self.table:
                    table.setHorizontalHeaderLabels(
                        ['id', 'Адрес', 'Кабинет', 'Оборудование', 'Наименование', 'С/Н', 'Г/В', 'Статус'])
                    table.horizontalHeader().setMaximumSectionSize(200)
                    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
                    table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
                    table.sortByColumn(1, QtCore.Qt.AscendingOrder)

                else:
                    table.setHorizontalHeaderLabels(
                        ['id', 'Дата', 'Адрес', 'Кабинет', 'Оборудование', 'Наименование', 'С/Н', 'Г/В',
                         'Неисправность', 'Работы', 'Тип', 'Статус', 'Выполнил'])
                    table.horizontalHeader().setMaximumSectionSize(130)
                    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
                    table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Stretch)
                    table.sortByColumn(1, QtCore.Qt.DescendingOrder)
                table.setSortingEnabled(True)
                self.font.setBold(True)
                table.horizontalHeader().setFont(self.font)
                table.resizeColumnsToContents()
                table.horizontalHeader().sectionResized.connect(lambda: start_resize_timer(resize_timer))
                if not admin:
                    table.hideColumn(0)
                table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
                btn_save.setEnabled(True)
                status_row_colors(table)


        except Exception as e:
            self.show_error.show_error(e)

    #"""Настройки поиска"""
    def sfw2(self, search, search_for_what, search_for_what_2, search_for_what_3, btn_more_filters):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                #"""Поиск без фильтров"""
                if search_for_what.currentText() == 'Всё':
                    search.setEnabled(False)
                    search_for_what_2.setEnabled(False)
                    search_for_what_3.setEnabled(False)
                    search_for_what_2.clear()
                    search_for_what_3.clear()
                    search.clear()
                    #self.more_filters()
                #"""Поиск по адресу"""

                elif search_for_what.currentText() == 'По Адресу':
                    search.setEnabled(False)
                    search_for_what_2.setEnabled(True)
                    search_for_what_3.setEnabled(True)
                    search_for_what_2.clear()
                    search_for_what_3.clear()
                    search.clear()
                    btn_more_filters.setVisible(True)
                    cur.execute("SELECT street FROM streets")
                    x = cur.fetchall()
                    #print(x)
                    x = ',,'.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    search_for_what_2.addItems(x.split(',,'))
                    #self.sfw3()

                #"""Поиск по типу"""
                elif search_for_what.currentText() == 'По Оборудованию':
                    search.setEnabled(False)
                    search_for_what_2.setEnabled(True)
                    search_for_what_3.setEnabled(False)
                    search_for_what_2.clear()
                    search_for_what_3.clear()
                    search.clear()
                    btn_more_filters.setVisible(True)
                    cur.execute("SELECT type FROM types "
                                "ORDER BY type ASC ")
                    x = cur.fetchall()
                    #print(x)
                    x = ',,'.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    search_for_what_2.addItems(x.split(',,'))

                #"""Поиск по имени"""
                elif search_for_what.currentText() == 'По Имени':
                    search.setEnabled(True)
                    search_for_what_2.setEnabled(False)
                    search_for_what_3.setEnabled(False)
                    search.setEnabled(True)
                    search_for_what_2.clear()
                    search_for_what_3.clear()
                    btn_more_filters.setVisible(True)
                    cur.execute("SELECT DISTINCT name FROM names")
                    x = cur.fetchall()
                    #print(x)
                    x = ',,'.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    completer = QCompleter(x.split(',,'))
                    search.setCompleter(completer)
                    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                    search_for_what_2.clear()

                #"""По статусу"""
                elif search_for_what.currentText() == 'По Статусу':
                    search.setEnabled(False)
                    search_for_what_2.setEnabled(True)
                    search_for_what_3.setEnabled(False)
                    search.setEnabled(False)
                    search_for_what_2.clear()
                    search_for_what_3.clear()
                    search.clear()
                    btn_more_filters.setVisible(True)
                    cur.execute("SELECT status FROM status "
                                "ORDER BY status ASC ")
                    x = cur.fetchall()
                    #print(x)
                    x = ',,'.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    search_for_what_2.addItems(x.split(',,'))

                elif search_for_what.currentText() == 'По Типу Работ':
                    search.setEnabled(False)
                    search_for_what_2.setEnabled(True)
                    search_for_what_3.setEnabled(False)
                    search_for_what_2.clear()
                    cur.execute("SELECT type_of_repair FROM types_of_repairs "
                                "ORDER BY type_of_repair ASC ")
                    x = cur.fetchall()
                    #print(x)
                    x = ',,'.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    search_for_what_2.addItems(x.split(',,'))
        except Exception as e:
            self.show_error.show_error(e)

    def sfw3(self, search_for_what, search_for_what_2, search_for_what_3):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                search_for_what_3.clear()
                cur.execute(
                    """
                    SELECT address.room 
                    FROM address 
                    INNER JOIN streets ON street_id = streets.id 
                    WHERE streets.street = %s 
                    ORDER BY
                        regexp_replace(room, '\\d+', '', 'g'),
                        CAST(NULLIF(regexp_replace(room, '\\D+', '', 'g'), '') AS INTEGER)
                        """,
                        (
                            search_for_what_2.currentText(),
                        )
                        )
                x = cur.fetchall()
                #print(x)
                x = ',,'.join(map(str, x))
                #print(x)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                #print(x.split(','))
                if search_for_what.currentText() == "По Адресу":
                    search_for_what_3.addItem('Всё')
                search_for_what_3.addItems(x.split(',,'))
        except Exception as e:
            self.show_error.show_error(e)

    #"""Кнопка Добавления"""
    def start_add(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:


                #"""ID Улицы"""
                cur.execute(
                    "SELECT id "
                    "FROM streets "
                    "WHERE street = %s",
                    (
                        self.add_CB_address.currentText(),
                    )
                )
                id_street = cur.fetchall()
                id_street = ',,'.join(map(str, id_street))
                for r in (('(', ''), (',)', '')):
                    id_street = id_street.replace(*r)
                #print(f"Улица_id: {id_street}")

                #"""ID Адресса"""
                cur.execute(
                    "SELECT id "
                    "FROM address "
                    "WHERE room = %s AND street_id = %s",
                    (
                        self.add_CB_room.currentText(),
                        id_street
                    )
                )
                id_address = cur.fetchall()
                id_address = ',,'.join(map(str, id_address))
                for r in (('(', ''), (',)', '')):
                    id_address = id_address.replace(*r)
                print(f"Комната_id: {id_address}")

                #"""ID Типа оборудования"""
                cur.execute(
                    "SELECT id "
                    "FROM types "
                    "WHERE type = %s",
                    (
                        self.add_CB_type.currentText(),
                    )
                )
                id_type = cur.fetchall()
                id_type = ',,'.join(map(str, id_type))
                for r in (('(', ''), (',)', '')):
                    id_type = id_type.replace(*r)
                print(f"Тип_id: {id_type}")

                #"""Имя"""
                cur.execute(
                    f"INSERT INTO names ( "
                    f"id, name, sn, date) "
                    f"VALUES (DEFAULT, %s, %s, %s)",
                    (
                        self.add_name.text(),
                        self.add_sn.text(),
                        self.add_date.text()
                    )
                )

                con.commit()
                print('Данные добавленны в names')

                cur.execute(
                    "SELECT DISTINCT ON (id) id "
                    "FROM names "
                    "ORDER BY id DESC"
                )
                id_name = cur.fetchall()
                id_name = str(id_name[0])
                #print(str(x[0]))
                for r in (('(', ''), (',)', '')):
                    id_name = id_name.replace(*r)
                print(f"Имя_id: {id_name}")

                add_message = QMessageBox()
                add_message.setWindowTitle("Добавление в базу")
                add_message.setText("Добавить в базу данных?")
                add_message.setIcon(QMessageBox.Question)
                add_message.setStandardButtons(QMessageBox.Cancel|QMessageBox.Ok)
                add_message.exec_()
                if add_message.standardButton(add_message.clickedButton()) == QMessageBox.Ok:
                    """Добавление в базу"""
                    cur.execute(
                        "INSERT INTO equipments ( "
                        "id, address_id, type_id, name_id) "
                        "VALUES (DEFAULT, %s, %s, %s)",
                        (
                            id_address,
                            id_type,
                            id_name
                        )
                    )
                    con.commit()
                    print('УСПЕШНО ДОБАВЛЕННО В БАЗУ!')
                    add_message = QMessageBox()
                    add_message.setWindowTitle("Успешно")
                    add_message.setText("Оборудование добавленно в базу")
                    add_message.setIcon(QMessageBox.Information)
                    add_message.setStandardButtons(QMessageBox.Ok)
                    add_message.exec_()
                else:
                    print('ОТМЕНА!')
                    add_message = QMessageBox()
                    add_message.setWindowTitle("Отмена")
                    add_message.setText("Оборудование НЕ добавленно в базу")
                    add_message.setIcon(QMessageBox.Information)
                    add_message.setStandardButtons(QMessageBox.Ok)
                    add_message.exec_()

        except Exception as e:
            self.show_error.show_error(e)

    #"""Кнопка Очистки"""
    def start_add_clear(self):
        self.add_name.clear()
        self.add_sn.clear()
        self.add_date.clear()

    #"""Кнопка Сохранения"""
    def save_table(self, table):
        rows = table.rowCount()
        cols = table.columnCount()
        if table == self.table:
            heads = ['id', 'Адрес', 'Кабинет', 'Оборудование', 'Наименование', 'С/Н', 'Год выпуска']
            name, _ = QFileDialog.getSaveFileName(self, 'Сохранить как', 'Таблица оборудования.xls', 'Excel(*.xls)')
        else:
            heads = ['id', 'Адрес', 'Кабинет', 'Оборудование', 'Наименование', 'С/Н', 'Год выпуска', 'Неисправность',
                     "Работы", "Тип", "Статус", "Выполнил"]
            name, _ = QFileDialog.getSaveFileName(self, 'Сохранить как', 'Таблица ремонтов.xls', 'Excel(*.xls)')
        #"""Отмена"""
        if not name:
            return

        wb = xlwt.Workbook()
        ws = wb.add_sheet('Список оборудования')
        for colx in range(cols):
            width = 3000 + colx * 500
            ws.col(colx).width = width
        data = []
        for row in range(rows):
            items = []
            for col in range(cols):
                    items.append(table.item(row, col).text())
            data.append(items)
        j = 0
        for n in heads:
            ws.write(0, j, n)
            j += 1
        i = 1
        for n in data:
            ws.write(i, 0, n[0])
            ws.write(i, 1, n[1])
            ws.write(i, 2, n[2])
            ws.write(i, 3, n[3])
            ws.write(i, 4, n[4])
            ws.write(i, 5, n[5])
            ws.write(i, 6, n[6])
            if table == self.table_repair:
                ws.write(i, 7, n[7])
                ws.write(i, 8, n[8])
                ws.write(i, 9, n[9])
                ws.write(i, 10, n[10])
                ws.write(i, 11, n[11])
            i += 1
        wb.save(name)

    #"""Таймер Для Пересчета Таблиц"""
    def start_resize_timer(self, resize_timer):
        resize_timer.start(1)

    #"""Пересчет Таблиц"""
    def resize_rows_to_contents_tables(self, table):
        table.setUpdatesEnabled(False)  # Отключаем обновление
        table.resizeRowsToContents()  # Пересчитываем высоту строк
        table.setUpdatesEnabled(True)  # Включаем обновление

    #"""Показать Данные Оборудования"""
    def equipment_show(self, table):

        row = table.currentIndex().row()
        global index
        index = table.model().index(row, 0).data()
        print("ID:", index)
        self.equipment_window = Equipment_Window()
        self.equipment_window.closed.connect(lambda: self.start_search(self.table, self.search_for_what, self.search_for_what2,
                                                                  self.search_for_what3, self.search_for_what4, self.search_for_what5, self.search_for_what6,
                                                                  self.search, self.search2, self.start_resize_timer, self.resize_timer, self.btn_save, self.status_row_colors))
        self.equipment_window.show()

    #"""Красим Табличку"""
    def status_row_colors(self, table):
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and item.text() == "Списано":
                    # Окрашиваем всю строку
                    for c in range(table.columnCount()):
                        cell = table.item(row, c) or QTableWidgetItem()
                        cell.setBackground(QColor(255, 235, 235))
                    break
                elif item and item.text() == "Исправно":
                    # Окрашиваем всю строку
                    for c in range(table.columnCount()):
                        cell = table.item(row, c) or QTableWidgetItem()
                        cell.setBackground(QColor(235, 255, 235))
                    break
                elif item and item.text() == "Неисправно":
                    # Окрашиваем всю строку
                    for c in range(table.columnCount()):
                        cell = table.item(row, c) or QTableWidgetItem()
                        cell.setBackground(QColor(255, 255, 235))
                    break
                elif item and item.text() == "Ввод в эксплуатацию":
                    # Окрашиваем всю строку
                    for c in range(table.columnCount()):
                        cell = table.item(row, c) or QTableWidgetItem()
                        cell.setBackground(QColor(235, 235, 255))
                    break

    #"""Видимость Кнопки "Больше Фильтров""""
    def more_filters_visible(self, search_for_what, btn_more_filters, more_filters):
        if search_for_what.currentText() == "Всё":
            btn_more_filters.setVisible(False)
            more_filters()
        else:
            btn_more_filters.setVisible(True)

    #"""Больше Фильтров"""
    def more_filters(self):
        if self.search_for_what4.isVisible() == False and self.btn_more_filters.isVisible() == True:
            self.btn_more_filters.setText("-")
            self.start_more_filters = True
            for x in [self.search_for_what4, self.search_for_what5]:
                x.setVisible(True)
                x.setEnabled(True)
            for x2 in [self.search_for_what6, self.search2]:
                x2.setVisible(True)
            self.search_for_what4.setCurrentIndex(0 if int(self.search_for_what.currentIndex()) != 1 else int(self.search_for_what.currentIndex()))
            self.update_filters(self.search_for_what, self.search_for_what4, self.start_more_filters)
        elif self.search_for_what4.isVisible() == True:
            self.btn_more_filters.setText("+")
            self.start_more_filters = False
            #print(self.start_more_filters)
            for x in [self.search_for_what4, self.search_for_what5, self.search_for_what6, self.search2]:
                x.setVisible(False)
                x.setEnabled(False)
            self.update_filters(self.search_for_what, self.search_for_what4, self.start_more_filters)

    #"""Больше Фильтров Ремонта"""
    def more_filters_repair(self):
        if self.search_for_what_repair4.isVisible() == False and self.btn_more_filters_repair.isVisible() == True:
            self.btn_more_filters_repair.setText("-")
            self.start_more_filters_repairs = True
            print(self.start_more_filters_repairs)
            for x in [self.search_for_what_repair4, self.search_for_what_repair5]:
                x.setVisible(True)
                x.setEnabled(True)
            for x2 in [self.search_for_what_repair6, self.search_repair2]:
                x2.setVisible(True)
            self.search_for_what_repair4.setCurrentIndex(0 if int(self.search_for_what_repair.currentIndex()) != 1 else int(self.search_for_what_repair.currentIndex()))
            self.update_filters(self.search_for_what_repair, self.search_for_what_repair4, self.start_more_filters_repairs)
        elif self.search_for_what_repair4.isVisible() == True:
            self.btn_more_filters_repair.setText("+")
            self.start_more_filters_repairs = False
            print(self.start_more_filters_repairs)
            for x in [self.search_for_what_repair4, self.search_for_what_repair5, self.search_for_what_repair6, self.search_repair2]:
                x.setVisible(False)
                x.setEnabled(False)
            self.update_filters(self.search_for_what_repair, self.search_for_what_repair4, self.start_more_filters_repairs)

    #"""Взаимоисключения Фильтров"""
    def update_filters(self, search_for_what, search_for_what4, start_more_filters):
        selected1 = search_for_what.currentText()
        selected2 = search_for_what4.currentText()
        for i in range(search_for_what4.count()):
            text = search_for_what4.itemText(i)
            if start_more_filters:
                search_for_what4.model().item(i).setEnabled(text != selected1)
            else:
                search_for_what4.model().item(i).setEnabled(True)

        for i in range(search_for_what.count()):
            text = search_for_what.itemText(i)
            if start_more_filters:
                search_for_what.model().item(i).setEnabled(text != selected2)
            else:
                search_for_what.model().item(i).setEnabled(True)

    #"""Показать Окно Добавления Комнаты и оборудования"""
    def add_something_show(self, add_something_rule):
        if add_something_rule == "room":
            self.more_rooms_rule = True
            #print(f"Добавление комнаты")
        elif add_something_rule == "type":
            self.more_types_rule = True
            #print(f"Добавление оборудования")
        self.add_something = Add_Something(self)
        self.add_something.show()

#"""Окно добавления кабинетов и типа оборудования"""
class Add_Something(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.setFixedSize(250, 100)
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.main_window = main_window
        if self.main_window.more_rooms_rule:
            self.title = "кабинет"

            print("Добавление комнаты")
        elif self.main_window.more_types_rule:
            self.title = "оборудование"
            print("Добавление оборудования")

        self.setWindowTitle(f"Добавить {str(self.title)}")
        self.setWindowIcon(QtGui.QIcon(resource_path('logo.png')))
        self.centralwidget.setFont(QtGui.QFont("Times", 10))
        self.layout = QGridLayout(self.centralwidget)

        self.add_something_LE = QtWidgets.QLineEdit(self.centralwidget)

        self.add_something_lable = QtWidgets.QLabel(self.centralwidget)
        self.add_something_lable.setText(f"Добавить {self.title} {'на ' + str(self.main_window.add_CB_address.currentText()) if self.main_window.more_rooms_rule else ''}")

        # """Для ошибок"""
        self.show_error = Show_Error()

        self.btn_add_something = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add_something.setText("Добавить")
        self.btn_add_something.clicked.connect(self.add_something)

        self.btn_cancel_add_something = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cancel_add_something.setText("Отмена")
        self.btn_cancel_add_something.clicked.connect(self.close)

        self.layout.addWidget(self.add_something_lable, 0, 0, 1, 2)
        self.layout.addWidget(self.add_something_LE, 1, 0, 1, 2)
        self.layout.addWidget(self.btn_add_something, 2, 0)
        self.layout.addWidget(self.btn_cancel_add_something, 2, 1)
        self.centralwidget.setLayout(self.layout)

        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                cur.execute("SELECT DISTINCT room FROM address" if self.main_window.more_rooms_rule else "SELECT DISTINCT type FROM types")
                x = cur.fetchall()
                # print(x)
                x = ',,'.join(map(str, x))
                # print(x)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                # print(x.split(','))
                completer_room = QCompleter(x.split(',,'))
                self.add_something_LE.setCompleter(completer_room)

        except Exception as e:
            self.show_error.show_error(e)

    def add_something(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                if self.main_window.more_rooms_rule:
                    cur.execute(
                        f"SELECT id "
                        f"FROM streets "
                        f"WHERE street = %s",
                        (
                            self.main_window.add_CB_address.currentText(),
                        )
                    )
                    id_street = cur.fetchall()
                    id_street = ',,'.join(map(str, id_street))
                    for r in (('(', ''), (',)', '')):
                        id_street = id_street.replace(*r)
                else:
                    pass


                add_message = QMessageBox()
                add_message.setWindowTitle(f"Добавление {self.title}")
                if self.main_window.more_rooms_rule:
                    add_message.setText(
                        f"Добавить кабинет {str(self.add_something_LE.text())} на {str(self.main_window.add_CB_address.currentText())}?")
                elif self.main_window.more_types_rule:
                    add_message.setText(
                        f"Добавить {str(self.add_something_LE.text())} в оборудование?")
                add_message.setIcon(QMessageBox.Question)
                add_message.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
                add_message.exec_()
                if add_message.standardButton(add_message.clickedButton()) == QMessageBox.Ok:

                    #"""Добавление в базу"""
                    if self.main_window.more_rooms_rule:
                        cur.execute(
                            "INSERT INTO address ( "
                            "id, street_id, room) "
                            "VALUES (DEFAULT, %s, %s)",
                            (
                                id_street,
                                self.add_something_LE.text()
                            )
                        )
                    elif self.main_window.more_types_rule:
                        cur.execute(
                            "INSERT INTO types ( "
                            "id, type) "
                            "VALUES (DEFAULT, %s)",
                            (
                                self.add_something_LE.text(),
                            )
                        )
                    con.commit()

                    add_message = QMessageBox()
                    add_message.setWindowTitle("Успешно!")
                    if self.main_window.more_rooms_rule:
                        print(
                            f"УСПЕШНО ДОБАВЛЕНН КАБИНЕТ {str(self.add_something_LE.text())} НА {str(self.main_window.add_CB_address.currentText())}!")
                        add_message.setText(f"Кабинет добавлен на {str(self.main_window.add_CB_address.currentText())}")
                    elif self.main_window.more_types_rule:
                        print(
                            f"УСПЕШНО ДОБАВЛЕННО ОБОРУДОВАНИЕ {str(self.add_something_LE.text())}!")
                        add_message.setText(f"Оборудование {str(self.add_something_LE.text())} добавленно!")
                    add_message.setIcon(QMessageBox.Information)
                    add_message.setStandardButtons(QMessageBox.Ok)
                    add_message.exec_()
                    self.add_something_LE.clear()
                else:
                    print('ОТМЕНА!')
                    add_message = QMessageBox()
                    add_message.setWindowTitle("Отмена")
                    add_message.setText("НЕ добавленно!!!")
                    add_message.setIcon(QMessageBox.Information)
                    add_message.setStandardButtons(QMessageBox.Ok)
                    add_message.exec_()
        except Exception as e:
            self.show_error.show_error(e)

    def cancel(self):
        self.close()

    def closeEvent(self, event):
        #"""Обновляем типы и кабинеты"""
        self.main_window.add_room_update()
        self.main_window.add_type_update()
        self.main_window.more_rooms_rule = False
        self.main_window.more_types_rule = False
        print(f"Добавление комнаты {self.main_window.more_rooms_rule}")
        print(f"Добавление оборудования {self.main_window.more_types_rule}")
        super().closeEvent(event)

#"""Информационное окно"""
class Equipment_Window(QMainWindow):
    #"""Сигнал закрытия окна"""
    closed = pyqtSignal()

    def __init__(self):
        super(Equipment_Window, self).__init__()
        self.resize(715, 450)
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.setWindowIcon(QtGui.QIcon(resource_path('logo.png')))
        self.centralwidget.setFont(QtGui.QFont("Times", 10))
        self.layout = QGridLayout(self.centralwidget)

        # """Для ошибок"""
        self.show_error = Show_Error()

        self.lable_address = QtWidgets.QLabel(self.centralwidget)
        self.lable_address.setText("Адрес:")
        self.layout.addWidget(self.lable_address, 0, 0)
        self.lable_address.setFixedHeight(15)
        self.address = QtWidgets.QComboBox(self.centralwidget)
        self.address.currentTextChanged.connect(self.room_info)

        self.lable_room = QtWidgets.QLabel(self.centralwidget)
        self.lable_room.setText("Кабинет:")
        self.layout.addWidget(self.lable_room, 2, 0)
        self.lable_room.setFixedHeight(15)
        self.room = QtWidgets.QComboBox(self.centralwidget)
        self.layout.addWidget(self.room, 3, 0)
        self.room.setEnabled(False)
        self.lable_type = QtWidgets.QLabel(self.centralwidget)
        self.lable_type.setText("Оборудование:")
        self.layout.addWidget(self.lable_type, 4, 0)
        self.lable_type.setFixedHeight(15)
        self.type = QtWidgets.QComboBox(self.centralwidget)

        self.lable_name = QtWidgets.QLabel(self.centralwidget)
        self.lable_name.setText("Наименование:")
        self.layout.addWidget(self.lable_name, 0, 1)
        self.name = QtWidgets.QLineEdit(self.centralwidget)

        self.lable_sn = QtWidgets.QLabel(self.centralwidget)
        self.lable_sn.setText("Серийный номер:")
        self.layout.addWidget(self.lable_sn, 2, 1)
        self.sn = QtWidgets.QLineEdit(self.centralwidget)

        self.lable_date = QtWidgets.QLabel(self.centralwidget)
        self.lable_date.setText("Год выпуска:")
        self.layout.addWidget(self.lable_date, 4, 1)
        self.date = QtWidgets.QLineEdit(self.centralwidget)

        self.lable_status = QtWidgets.QLabel(self.centralwidget)
        self.lable_status.setText("Статус:")
        self.layout.addWidget(self.lable_status, 6, 0)
        self.status = QtWidgets.QComboBox(self.centralwidget)

        self.table = QtWidgets.QTableWidget(self.centralwidget)
        self.layout.addWidget(self.table, 8, 0, 4, 4)
        self.table.setMinimumHeight(250)

        self.btn_change = QtWidgets.QPushButton(self.centralwidget)
        self.btn_change.setText("Изменить")
        if not admin:
            self.btn_change.setEnabled(False)
        self.btn_change.clicked.connect(self.change_equipment)
        self.layout.addWidget(self.btn_change, 1, 3)

        self.btn_save = QtWidgets.QPushButton(self.centralwidget)
        self.btn_save.setText("Сохранить")
        self.btn_save.clicked.connect(self.save_change)
        self.layout.addWidget(self.btn_save, 3, 3)
        self.btn_save.setEnabled(False)

        self.btn_cancel = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cancel.setText("Отменить")
        self.btn_cancel.clicked.connect(self.cancel)
        self.layout.addWidget(self.btn_cancel, 5, 3)
        self.btn_cancel.setEnabled(False)

        self.btn_add = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add.setText("Добавить запись")
        self.btn_add.clicked.connect(self.show_entry)
        self.layout.addWidget(self.btn_add, 12, 3)
        self.main_window = Main_Window()

        self.info()
        if not admin:
            self.btn_add.setEnabled(False)

    def info(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                ###"""ПОДХФАТ ИМЕНИ"""

                cur.execute(
                    "SELECT names.name "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.name_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                name = cur.fetchall()
                name = ',,'.join(map(str, name))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    name = str(name.replace(*r))
                self.setWindowTitle(f'Данные о "{name}"')

                ###"""ВЫДАЧА ИНФЫ"""

                #"""Адрес"""

                cur.execute("SELECT street FROM streets")
                x = cur.fetchall()
                x = ',,'.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                self.address.addItems(x.split(',,'))
                self.layout.addWidget(self.address, 1, 0)
                cur.execute(
                    "SELECT streets.id "
                    "FROM equipments "
                    "INNER JOIN address ON address.id = equipments.address_id "
                    "INNER JOIN streets ON street_id = streets.id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                address = cur.fetchall()
                #print(address)
                address = ',,'.join(map(str, address))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    address = str(address.replace(*r))
                    #print(address)
                self.address.setCurrentIndex(int(address)-1)
                self.address.setEnabled(False)

                #"""Кабинет"""


                #"""Оборудование"""

                cur.execute(
                    "SELECT type FROM types "
                    "ORDER BY type ASC"
                )
                x = cur.fetchall()
                x = ',,'.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                self.type.addItems(x.split(',,'))
                self.layout.addWidget(self.type, 5, 0)
                cur.execute(
                    "SELECT types.type "
                    "FROM equipments "
                    "INNER JOIN types ON types.id = equipments.type_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                type = cur.fetchall()
                type = ',,'.join(map(str, type))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    type = str(type.replace(*r))
                #print(type)
                self.type.setCurrentText(type)
                self.type.setEnabled(False)

                #"""Наименование"""

                cur.execute(
                    "SELECT names.name "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.name_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                name = cur.fetchall()
                name = ',,'.join(map(str, name))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    name = str(name.replace(*r))
                #print(name)
                cur.execute("SELECT DISTINCT name FROM names")
                x = cur.fetchall()
                # print(x)
                x = ',,'.join(map(str, x))
                # print(x)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                completer = QCompleter(x.split(',,'))
                self.name.setCompleter(completer)
                completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

                self.name.setText(f"{str(name)}")
                self.layout.addWidget(self.name, 1, 1)
                self.name.setMinimumWidth(250)
                self.name.setEnabled(False)

                #"""Серийный номер"""

                cur.execute(
                    "SELECT names.sn "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.name_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                sn = cur.fetchall()
                sn = ',,'.join(map(str, sn))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    sn = str(sn.replace(*r))
                #print(sn)
                self.sn.setText(f"{str(sn)}")
                self.layout.addWidget(self.sn, 3, 1)
                self.sn.setEnabled(False)

                #"""Дата создания"""

                cur.execute(
                    "SELECT names.date "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.name_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                date = cur.fetchall()
                date = ',,'.join(map(str, date))
                for r in (("(Decimal('", ''), ("'),)", '')):
                    date = str(date.replace(*r))
                #print(date)
                self.date.setText(f"{str(date)}")
                self.layout.addWidget(self.date, 5, 1)
                self.date.setEnabled(False)

                #"""Статус"""

                cur.execute(
                    "SELECT status FROM status "
                )
                x = cur.fetchall()
                x = ',,'.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                self.status.addItems(x.split(',,'))
                self.layout.addWidget(self.status, 7, 0)
                cur.execute(
                    "SELECT status.status "
                    "FROM equipments "
                    "INNER JOIN status ON status.id = equipments.status_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                status = cur.fetchall()
                status = ',,'.join(map(str, status))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    status = str(status.replace(*r))
                #print(type)
                self.status.setCurrentText(status)
                self.status.setEnabled(False)

                #"""РЕМОНТЫ"""

                cur.execute(
                    "SELECT repairs.id, repairs.date, repairs.fault, repairs.repair,  types_of_repairs.type_of_repair, status.status, repairs.repairman "
                    "FROM repairs "
                    "INNER JOIN equipments ON equipments.id = repairs.equipments_id "
                    "INNER JOIN status ON status.id = repairs.status_id "
                    "INNER JOIN types_of_repairs ON types_of_repairs.id = repairs.types_of_repairs_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                    #"ORDER BY LENGTH(date), room ASC ;"
                )
                data = cur.fetchall()
                a = len(data)  # rows
                b = len(data[0])  # columns
                self.table.setColumnCount(b)
                self.table.setRowCount(a)
                self.table.setSortingEnabled(False)
                for j in range(a):
                    for i in range(b):
                        item = QtWidgets.QTableWidgetItem(str(data[j][i]))
                        self.table.setItem(j, i, item)
                self.table.setHorizontalHeaderLabels(
                    ['Id', 'Дата', 'Неисправность',
                     'Работы', 'Тип работ', 'Статус', 'Выполнил'])
                self.table.setSortingEnabled(True)
                self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
                self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
                self.table.horizontalHeader().setMaximumSectionSize(200)
                self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
                self.table.sortByColumn(0, QtCore.Qt.DescendingOrder)

                self.table.resizeColumnsToContents()
                self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
                self.status_row_colors(self.table)
        except Exception as e:
            if not IndexError:
                self.show_error.show_error(e)

    #"""Изменить значения"""
    def change_equipment(self):
        for x in [self.address, self.room, self.type, self.name, self.sn, self.date, self.status, self.btn_save, self.btn_cancel]:
            x.setEnabled(True)
        self.btn_change.setEnabled(False)

    #"""Инфа о кабинете"""
    def room_info(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                cur.execute(
                    "SELECT address.room "
                    "FROM address "
                    "INNER JOIN streets ON street_id = streets.id "
                    "WHERE streets.street = %s" 
                    "ORDER BY regexp_replace(room, '\\d+', '', 'g'), CAST(NULLIF(regexp_replace(room, '\\D+', '', 'g'), '') AS INTEGER) ",
                    (
                        self.address.currentText(),
                    )
                )
                x = cur.fetchall()
                x = ',,'.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                self.room.clear()
                self.room.addItems(x.split(',,'))
                cur.execute(
                    "SELECT address.room "
                    "FROM equipments "
                    "INNER JOIN address ON address.id = equipments.address_id "
                    "WHERE equipments.id = %s "
                    "ORDER BY regexp_replace(room, '\\d+', '', 'g'), CAST(NULLIF(regexp_replace(room, '\\D+', '', 'g'), '') AS INTEGER) ",
                    (
                        index,
                    )
                )
                room = cur.fetchall()
                room = ',,'.join(map(str, room))
                #print(room)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    room = str(room.replace(*r))
                self.room.setCurrentText(room)
        except Exception as e:
            self.show_error.show_error(e)

    #"""Сохранить изменения"""
    def save_change(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                ###"""Редактирование значений"""
                ###"""Адрес и комната"""
                cur.execute(
                    f"SELECT streets.id "
                    f"From streets "
                    f"WHERE streets.street = '{str(self.address.currentText())}'"
                )
                street_id = cur.fetchall()
                street_id = ','.join(map(str, street_id))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    street_id = str(street_id.replace(*r))
                cur.execute(
                    f"SELECT address.id "
                    f"FROM address "
                    f"WHERE address.street_id = '{street_id}' AND address.room = '{str(self.room.currentText())}'"
                )
                address_id = cur.fetchall()
                address_id = ','.join(map(str, address_id))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    address_id = str(address_id.replace(*r))
                print(address_id)
                cur.execute(
                    f"UPDATE equipments "
                    f"SET address_id = '{address_id}' "
                    f"FROM address "
                    f"WHERE address.id = equipments.address_id AND equipments.id = {str(index)}"
                )

                ###"""Тип"""
                cur.execute(
                    f"SELECT types.id "
                    f"FROM types "
                    f"WHERE types.type = '{str(self.type.currentText())}'"
                )
                type_id = cur.fetchall()
                type_id = ','.join(map(str, type_id))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    type_id = str(type_id.replace(*r))
                cur.execute(
                    f"UPDATE equipments "
                    f"SET type_id = '{type_id}' "
                    f"FROM types "
                    f"WHERE types.id = equipments.type_id AND equipments.id = {str(index)}"
                )

                ###"""Имя"""
                cur.execute(
                    f"UPDATE names "
                    f"SET name = '{str(self.name.text())}' "
                    f"FROM equipments  "
                    f"WHERE names.id = equipments.name_id AND equipments.id = {str(index)}"
                )

                ###"""Серийник"""
                cur.execute(
                    f"UPDATE names "
                    f"SET sn = '{str(self.sn.text())}' "
                    f"FROM equipments  "
                    f"WHERE names.id = equipments.name_id AND equipments.id = {str(index)}"
                )

                ###"""Дата"""
                cur.execute(
                    f"UPDATE names "
                    f"SET date = '{str(self.date.text())}' "
                    f"FROM equipments  "
                    f"WHERE names.id = equipments.name_id AND equipments.id = {str(index)}"
                )

                ###"""Статус"""
                cur.execute(
                    f"SELECT status.id "
                    f"FROM status "
                    f"WHERE status.status = '{str(self.status.currentText())}'"
                )
                status_id = cur.fetchall()
                status_id = ','.join(map(str, status_id))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    status_id = str(status_id.replace(*r))
                cur.execute(
                    f"UPDATE equipments "
                    f"SET status_id = '{status_id}' "
                    f"FROM status "
                    f"WHERE status.id = equipments.status_id AND equipments.id = {str(index)}"
                )
                save_message = QMessageBox()
                save_message.setWindowTitle("Изменение")
                save_message.setText("Изменить данные?")
                save_message.setIcon(QMessageBox.Question)
                save_message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                save_message.exec_()
                if save_message.standardButton(save_message.clickedButton()) == QMessageBox.Yes:
                    con.commit()
                    print('УСПЕШНО ИЗМЕНЕНО!')
                    change_message = QMessageBox()
                    change_message.setWindowTitle("Успешно")
                    change_message.setText("Данные изменены")
                    change_message.setIcon(QMessageBox.Information)
                    change_message.setStandardButtons(QMessageBox.Ok)
                    change_message.exec_()
                else:
                    print('ОТМЕНА')
                    change_message = QMessageBox()
                    change_message.setWindowTitle("Отмена")
                    change_message.setText("Данные НЕ изменены")
                    change_message.setIcon(QMessageBox.Information)
                    change_message.setStandardButtons(QMessageBox.Ok)
                    change_message.exec_()
                self.cancel()

        except Exception as e:
            self.show_error.show_error(e)

    #"""Отмена"""
    def cancel(self):
        for x in [self.address, self.room, self.type, self.name, self.sn, self.date, self.status, self.btn_save, self.btn_cancel]:
            x.setEnabled(False)
        self.btn_change.setEnabled(True)

    #"""Добавить записть"""
    def show_entry(self):
        global index
        print(index)
        self.entry_window = Entry_Window()
        self.entry_window.closed.connect(self.info)
        self.entry_window.show()

    #"""Красим Табличку"""
    def status_row_colors(self, table):
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and item.text() == "Списано":
                    # Окрашиваем всю строку
                    for c in range(table.columnCount()):
                        cell = table.item(row, c) or QTableWidgetItem()
                        cell.setBackground(QColor(255, 235, 235))
                    break
                elif item and item.text() == "Исправно":
                    # Окрашиваем всю строку
                    for c in range(table.columnCount()):
                        cell = table.item(row, c) or QTableWidgetItem()
                        cell.setBackground(QColor(235, 255, 235))
                    break
                elif item and item.text() == "Неисправно":
                    # Окрашиваем всю строку
                    for c in range(table.columnCount()):
                        cell = table.item(row, c) or QTableWidgetItem()
                        cell.setBackground(QColor(255, 255, 235))
                    break
                elif item and item.text() == "Ввод в эксплуатацию":
                    # Окрашиваем всю строку
                    for c in range(table.columnCount()):
                        cell = table.item(row, c) or QTableWidgetItem()
                        cell.setBackground(QColor(235, 235, 255))
                    break

    #"""Запуск сигнала о закрытии"""
    def closeEvent(self, event):
        print("Закрытие'Equipment_Window'")
        self.closed.emit()  # Испускаем сигнал при закрытии
        self.close()
        super().closeEvent(event)
        self.main_window.start_search(self.main_window.table, self.main_window.search_for_what, self.main_window.search_for_what2,
                                    self.main_window.search_for_what3, self.main_window.search_for_what4, self.main_window.search_for_what5, self.main_window.search_for_what6,
                                    self.main_window.search, self.main_window.search2, self.main_window.start_resize_timer, self.main_window.resize_timer,
                                    self.main_window.btn_save, self.main_window.status_row_colors)
        self.main_window.start_search(self.main_window.table_repair, self.main_window.search_for_what_repair, self.main_window.search_for_what_repair2,
                                    self.main_window.search_for_what_repair3, self.main_window.search_for_what_repair4, self.main_window.search_for_what_repair5, self.main_window.search_for_what_repair6,
                                    self.main_window.search_repair, self.main_window.search_repair2, self.main_window.start_resize_timer, self.main_window.resize_timer_repair,
                                    self.main_window.btn_save_repair, self.main_window.status_row_colors)

#"""Окно ввода работ"""
class Entry_Window(QMainWindow):
    #"""Сигнал закрытия окна"""
    closed = pyqtSignal()

    def __init__(self):
        super(Entry_Window, self).__init__()
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        #self.setWindowTitle('Добавить запись к ')
        self.setWindowIcon(QtGui.QIcon(resource_path('logo.png')))
        self.font = QtGui.QFont("Times", 10)
        self.centralwidget.setFont(self.font)

        # """Для ошибок"""
        self.show_error = Show_Error()

        self.layout = QGridLayout(self.centralwidget)
        self.lable_fault = QtWidgets.QLabel(self.centralwidget)
        self.lable_fault.setText("Ошибка:")
        self.layout.addWidget(self.lable_fault, 0, 0)
        self.lable_fault.setFixedHeight(15)
        self.fault = QtWidgets.QLineEdit(self.centralwidget)
        self.layout.addWidget(self.fault, 1, 0, 1, 4)

        self.lable_repair = QtWidgets.QLabel(self.centralwidget)
        self.lable_repair.setText("Работы:")
        self.layout.addWidget(self.lable_repair, 2, 0)
        self.repair = QtWidgets.QLineEdit(self.centralwidget)
        self.layout.addWidget(self.repair, 3, 0, 1, 4)

        self.lable_type_of_repair = QtWidgets.QLabel(self.centralwidget)
        self.lable_type_of_repair.setText("Тип работ:")
        self.layout.addWidget(self.lable_type_of_repair, 4, 0)
        self.lable_type_of_repair.setFixedHeight(15)
        self.type_of_repair = QtWidgets.QComboBox(self.centralwidget)


        self.lable_status = QtWidgets.QLabel(self.centralwidget)
        self.lable_status.setText("Статус:")
        self.layout.addWidget(self.lable_status, 4, 1)
        self.status = QtWidgets.QComboBox(self.centralwidget)


        self.lable_repairman = QtWidgets.QLabel(self.centralwidget)
        self.lable_repairman.setText("Выполнил:")
        self.layout.addWidget(self.lable_repairman, 4, 2)
        self.repairman = QtWidgets.QLineEdit(self.centralwidget)
        self.repairman.setText("Максименко Н.А.")
        self.repairman_check_running = False
        self.repairman.editingFinished.connect(self.check_repairmain)


        self.lable_date = QtWidgets.QLabel(self.centralwidget)
        self.lable_date.setText("Дата:")
        self.layout.addWidget(self.lable_date, 4, 3)
        self.date = QDateEdit(self.centralwidget)
        self.date.setDisplayFormat("yyyy-MM-dd")
        self.date.setDate(QtCore.QDate.currentDate())
        self.layout.addWidget(self.date, 5, 3)

        self.btn_cancel = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cancel.setText("Отмена")
        self.btn_cancel.clicked.connect(self.cancel)
        self.layout.addWidget(self.btn_cancel, 7, 0, 1, 2)
        #self.btn_cancel.setFixedHeight(23)

        self.btn_add = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add.setText("Добавить запись")
        self.btn_add.clicked.connect(self.add_entry)
        self.layout.addWidget(self.btn_add, 8, 0, 1, 4)

        self.btn_generate_pdf = QtWidgets.QPushButton(self.centralwidget)
        self.btn_generate_pdf.setText("Создать PDF")
        self.btn_generate_pdf.clicked.connect(self.generate_pdf)
        self.layout.addWidget(self.btn_generate_pdf, 7, 2, 1, 2)

        self.update_repairman()

        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )

            ###"""Подхфат имени"""

            with con.cursor() as cur:
                cur.execute(
                    "SELECT names.name "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.name_id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                self.name = cur.fetchall()
                self.name = ','.join(map(str, self.name))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    self.name = str(self.name.replace(*r))
                self.setWindowTitle(f'Добавить запись к {self.name}')

                #"""Ошибка"""

                cur.execute("SELECT DISTINCT fault FROM repairs")
                x = cur.fetchall()
                # print(x)
                x = ',,'.join(map(str, x))
                # print(x)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                # print(x.split(','))
                self.completer_fault = QCompleter(x.split(',,'))
                self.fault.setCompleter(self.completer_fault)

                #"""Работы"""

                cur.execute("SELECT DISTINCT repair FROM repairs")
                x = cur.fetchall()
                # print(x)
                x = ',,'.join(map(str, x))
                #print(x)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                # print(x.split(','))
                completer_repair = QCompleter(x.split(',,'))
                self.repair.setCompleter(completer_repair)

                #"""Тип работ"""

                cur.execute(
                    "SELECT type_of_repair FROM types_of_repairs "
                )
                type_of_repair = cur.fetchall()
                type_of_repair = ',,'.join(map(str, type_of_repair))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    type_of_repair = str(type_of_repair.replace(*r))
                #print(type_of_repair)
                self.type_of_repair.addItems(type_of_repair.split(',,'))
                self.layout.addWidget(self.type_of_repair, 5, 0)

                #"""Статус"""

                cur.execute(
                    "SELECT status FROM status "
                    "ORDER BY status ASC "
                )
                status = cur.fetchall()
                status = ',,'.join(map(str, status))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    status = str(status.replace(*r))
                #print(type_of_repair)
                self.status.addItems(status.split(',,'))
                self.layout.addWidget(self.status, 5, 1)


        except Exception as e:
            self.show_error.show_error(e)

    #"""Отмена"""
    def cancel(self):
        self.close()

    #"""Обновление поля Исполнитель"""
    def update_repairman(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                cur.execute(
                    "SELECT name FROM repairmans "
                )
                cur.execute("SELECT DISTINCT name FROM repairmans")
                repairmain = cur.fetchall()
                # print(repairmain)
                repairmain = ',,'.join(map(str, repairmain))
                # print(repairmain)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    repairmain = repairmain.replace(*r)
                completer = QCompleter(repairmain.split(',,'))
                self.repairmain_selected = repairmain.split(',,')
                self.repairman.setCompleter(completer)
                completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                self.layout.addWidget(self.repairman, 5, 2)
        except Exception as e:
            self.show_error.show_error(e)

    #"""Проверка на наличие исполнителя в базе"""
    def check_repairmain(self):
        if self.repairman_check_running:
            return
        self.repairman_check_running = True
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                if self.repairman.text() not in self.repairmain_selected:
                    add_message = QMessageBox()
                    add_message.setWindowTitle("Внимание!")
                    add_message.setText("Такого исполнителя не существует! \nДобавить?")
                    add_message.setIcon(QMessageBox.Question)
                    add_message.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
                    add_message.exec_()
                    if add_message.standardButton(add_message.clickedButton()) == QMessageBox.Ok:
                        cur.execute(
                            f"INSERT INTO repairmans ( id, name) "
                            f"VALUES (DEFAULT, %s) ",
                            (
                                self.repairman.text(),
                            )
                        )
                        con.commit()
                        print('УСПЕШНО ДОБАВЛЕННО ИНЖЕНЕР!')

                        add_message = QMessageBox()
                        add_message.setWindowTitle("Успешно")
                        add_message.setText("Исполнитель добавлен")
                        add_message.setIcon(QMessageBox.Information)
                        add_message.setStandardButtons(QMessageBox.Ok)
                        add_message.exec_()
                    else:
                        print('ОТМЕНА!')
                        add_message = QMessageBox()
                        add_message.setWindowTitle("Отмена")
                        add_message.setText("Исполнитель НЕ добавлен!!!")
                        add_message.setIcon(QMessageBox.Information)
                        add_message.setStandardButtons(QMessageBox.Ok)
                        add_message.exec_()
                    self.update_repairman()
        except Exception as e:
            self.show_error.show_error(e)
        finally:
            self.repairman_check_running = False

    #"""Добавить запись"""
    def add_entry(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                # """ID Статуса"""

                cur.execute(
                    "SELECT id "
                    "FROM status "
                    "WHERE status = %s",
                    (
                        self.status.currentText(),
                    )
                )
                self.id_status = cur.fetchall()
                self.id_status = ',,'.join(map(str, self.id_status))
                for r in (('(', ''), (',)', '')):
                    self.id_status = self.id_status.replace(*r)
                print(f"Статус_id: {self.id_status}")

                # """ID Типа ремонта"""

                cur.execute(
                    "SELECT id "
                    "FROM types_of_repairs "
                    "WHERE type_of_repair = %s",
                    (
                        self.type_of_repair.currentText(),
                    )
                )
                id_type_of_repair = cur.fetchall()
                id_type_of_repair = ','.join(map(str, id_type_of_repair))
                for r in (('(', ''), (',)', '')):
                    id_type_of_repair = id_type_of_repair.replace(*r)
                print(f"Тип ремонта: {id_type_of_repair}")

                add_message = QMessageBox()
                add_message.setWindowTitle("Добавление в журнал")
                add_message.setText("Добавить в журнал?")
                add_message.setIcon(QMessageBox.Question)
                add_message.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
                add_message.exec_()
                if add_message.standardButton(add_message.clickedButton()) == QMessageBox.Ok:
                    #"""Добавление в журнал"""

                    cur.execute(
                        "INSERT INTO repairs ( "
                        "id, fault, repair, date, status_id, equipments_id, repairman, types_of_repairs_id) "
                        "VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            self.fault.text(),
                            self.repair.text(),
                            self.date.text(),
                            self.id_status,
                            index,
                            self.repairman.text(),
                            id_type_of_repair
                        )
                    )

                    """Добавление в оборудование"""
                    cur.execute(
                        "UPDATE equipments "
                        "SET status_id = %s "
                        "FROM status "
                        "WHERE status.id = equipments.status_id AND equipments.id = %s",
                        (
                            self.id_status,
                            index
                        )
                    )
                    #print(f"Ошибка: {str(self.fault.setPlainText())}, Ремонт: {str(self.repair.setPlainText())}, Дата: {str(self.date.text())}, Инженер: {str(self.repairman.text())}")
                    con.commit()

                    print('УСПЕШНО ДОБАВЛЕННО В ЖУРНАЛ!')

                    add_message = QMessageBox()
                    add_message.setWindowTitle("Успешно")
                    add_message.setText("Запись добавленна в журнал")
                    add_message.setIcon(QMessageBox.Information)
                    add_message.setStandardButtons(QMessageBox.Ok)
                    add_message.exec_()

                    #"""Создаем ПДФ"""
                    self.generate_pdf()

                    #self.close()
                else:
                    print('ОТМЕНА!')
                    add_message = QMessageBox()
                    add_message.setWindowTitle("Отмена")
                    add_message.setText("Запись НЕ добавленна в журнал!!!")
                    add_message.setIcon(QMessageBox.Information)
                    add_message.setStandardButtons(QMessageBox.Ok)
                    add_message.exec_()

        except Exception as e:
            self.show_error.show_error(e)

    #"""Создать ПДФ"""
    def generate_pdf(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                ###"""ВЫДАЧА ИНФЫ"""

                # """Оборудование"""

                cur.execute(
                    "SELECT types.type "
                    "FROM equipments "
                    "INNER JOIN types ON types.id = equipments.type_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                self.type = cur.fetchall()
                self.type = ',,'.join(map(str, self.type))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    self.type = str(self.type.replace(*r))
                # print(type)

                # """Серийный номер"""

                cur.execute(
                    "SELECT names.sn "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.name_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                self.sn = cur.fetchall()
                self.sn = ',,'.join(map(str, self.sn))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    self.sn = str(self.sn.replace(*r))
                # print(sn)


                # """Дата создания"""

                cur.execute(
                    "SELECT names.date "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.name_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                self.date_of_create = cur.fetchall()
                self.date_of_create = ',,'.join(map(str, self.date_of_create))
                for r in (("(Decimal('", ''), ("'),)", '')):
                    self.date_of_create = str(self.date_of_create.replace(*r))
                # print(date)

                # """Адрес"""

                cur.execute("SELECT street FROM streets")
                x = cur.fetchall()
                x = ',,'.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                cur.execute(
                    "SELECT streets.id "
                    "FROM equipments "
                    "INNER JOIN address ON address.id = equipments.address_id "
                    "INNER JOIN streets ON street_id = streets.id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                self.address = cur.fetchall()
                # print(address)
                self.address = ',,'.join(map(str, self.address))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    self.address = str(self.address.replace(*r))
                    # print(address)

                # """Кабинет"""
                cur.execute(
                    "SELECT address.room "
                    "FROM equipments "
                    "INNER JOIN address ON address.id = equipments.address_id "
                    "WHERE equipments.id = %s",
                    (
                        index,
                    )
                )
                self.room = cur.fetchall()
                self.room = ',,'.join(map(str, self.room))
                #print(room)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    self.room = str(self.room.replace(*r))


                # Шаблон PDF
                template_path = resource_path("template.pdf")

                # Читаем шаблон PDF
                reader = PdfReader(template_path)
                writer = PdfWriter()
                pdfmetrics.registerFont(TTFont('Times', 'Times.ttf'))

                # Создаем новый PDF с текстом поверх шаблона
                for page in reader.pages:
                    packet = io.BytesIO()
                    self.can = canvas.Canvas(packet, pagesize=letter)

                    def draw_wrapped_text(canvas, text, x, y, max_width, line_height):
                        """Разбивает текст на строки и рисует его с переносами."""
                        wrapped_text = textwrap.wrap(text, width=max_width)  # Разбиваем текст на строки
                        for line in wrapped_text:
                            canvas.drawString(x, y, line)  # Рисуем каждую строку
                            y -= line_height  # Перемещаемся на следующую строку

                    # Добавляем текст в определённые координаты

                    self.can.setFont('Times', 12)
                    self.can.drawString(120, 518, self.type)  # Координаты (x, y)
                    self.can.drawString(120, 505, self.name)
                    self.can.drawString(120, 492, self.sn)
                    if self.date_of_create == "0":
                        self.can.drawString(120, 479, "-")
                    else:
                        self.can.drawString(120, 479, self.date_of_create)

                    self.can.setFont('Helvetica', 18)
                    if self.type_of_repair.currentText() == "Ремонт":
                        self.can.drawString(60, 573, "✓")
                    elif self.type_of_repair.currentText() == "Списание":
                        self.can.drawString(60, 561, "✓")
                    elif self.type_of_repair.currentText() == "Диагностика":
                        self.can.drawString(194, 573, "✓")
                    elif self.type_of_repair.currentText() == "Перемещение":
                        self.can.drawString(194, 561, "✓")
                    elif self.type_of_repair.currentText() == "Ввод в эксплуатацию":
                        self.can.drawString(335, 573, "✓")
                    elif self.type_of_repair.currentText() == "ТО":
                        self.can.drawString(335, 561, "✓")

                    if self.address == "1":
                        self.can.drawString(121, 468, "✓")
                    elif self.address == "2":
                        self.can.drawString(210, 468, "✓")
                    elif self.address == "3":
                        self.can.drawString(298, 468, "✓")
                    elif self.address == "4":
                        self.can.drawString(375, 468, "✓")
                    elif self.address == "5":
                        self.can.drawString(458, 468, "✓")

                    if self.status.currentText() == "Исправно":
                        self.can.drawString(28, 321, "✓")
                        self.can.drawString(142, 215, "✓")
                    elif self.status.currentText() == "Неисправно":
                        self.can.drawString(28, 307, "✓")
                        self.can.drawString(274, 215, "✓")
                        self.can.setFont('Times', 12)
                        draw_wrapped_text(self.can, self.fault.text(), 40, 292, 90, 13)
                    elif self.status.currentText() == "Списано":
                        self.can.drawString(28, 307, "✓")
                        self.can.drawString(416, 215, "✓")
                        self.can.setFont('Times', 12)
                        draw_wrapped_text(self.can, self.fault.text(), 40, 292, 90, 13)
                    self.can.setFont('Times', 12)
                    self.can.drawString(120, 452, self.room)
                    draw_wrapped_text(self.can, self.fault.text(), 40, 425, 90, 13)
                    draw_wrapped_text(self.can, self.repair.text(), 40, 384, 90, 13)


                    self.can.save()

                    # Наложение текста на страницу шаблона
                    packet.seek(0)
                    new_pdf = PdfReader(packet)
                    page.merge_page(new_pdf.pages[0])
                    writer.add_page(page)

                #"""Сохраняем новый PDF"""
                pdf_path = self.next_AKT_BP()
                with open(pdf_path, "wb") as output_pdf:
                    writer.write(output_pdf)
                self.open_pdf(pdf_path)

        except Exception as e:
            self.show_error.show_error(e)


    #"""Последовательность ПДФ"""
    def next_AKT_BP(self):
        base_path = Path(resource_path("АКТ ВР.pdf"))
        folder = base_path.parent # Получаем директорию, где лежит файл
        for file in folder.glob("АКТ ВР*.pdf"):
            try:
                file.unlink()  # Пытаемся удалить
                print(f"Удалён: {file.name}")
            except PermissionError:
                print(f"Файл занят (открыт): {file.name}")
            except Exception as e:
                print(f"Ошибка при удалении {file.name}: {e}")
        if not base_path.exists():
            return base_path

        i = 1
        while True:
            new_path = base_path.with_name(f"АКТ ВР{i}.pdf")
            if not new_path.exists():
                return new_path
            i += 1

    #"""Открываем ПДФ"""
    def open_pdf(self, file_path):
        os.startfile(file_path)

    #"""Событие Закрытия Окна"""
    def closeEvent(self, event):
        print("Закрытие 'Entry_Window'")
        self.closed.emit()
        super().closeEvent(event)

#"""Ошибки"""
class Show_Error(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.error = QMessageBox()
        self.error.setWindowTitle("Упс!")
        self.style = QtWidgets.QApplication.style()
        self.icon = self.style.standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        self.error.setWindowIcon(self.icon)

    def show_error(self, e):
        #print(e)
        if isinstance(e, IndexError):
            self.error.setText("Пусто, ничего нет\n\n"
                               "Проверьте фильтры, скорее всего по таким параметрам ничего не находится")
        elif isinstance(e, ValueError):
            self.error.setText("Где-то указано неверное значение")
        elif isinstance(e, PermissionError):
            self.error.setText("Файл с Актом уже открыт\n"
                               "Закройте файл 'АКТ ВР.pdf'")
        elif isinstance(e, OperationalError):
            self.error.setText(
                    "Сервер недоступен\n\n"
                    "Проверьте:\n"
                    "1. Доступность сервера в сети\n"
                    "2. Настройки подключения\n"
                    "3. Работает ли PostgreSQL на сервере"
                )
        else:
            self.error.setText("Что-то пошло не так")
            self.error.setDetailedText(f'Error: {e}')
        self.error.setIcon(QMessageBox.Warning)
        self.error.setStandardButtons(QMessageBox.Ok)
        print(f'Error: {e}')
        self.error.exec_()

#"""Сортировка таблиц"""
class SmartItem(QtWidgets.QTableWidgetItem):
    def __init__(self, text):
        super().__init__(text)  # передаём текст в стандартный элемент
        self.value = self.try_parse(text)  # пытаемся превратить текст в число
    def try_parse(self, text):
        try:
            return float(text)  # если текст — число, превращаем в float (например, '10.5' → 10.5)
        except ValueError:
            return text  # если не получилось — просто оставляем как текст
    def __lt__(self, other):
        if isinstance(other, SmartItem):
            if isinstance(self.value, float) and isinstance(other.value, float):
                return self.value < other.value  # сравниваем как числа
            return str(self.text()) < str(other.text())  # иначе — как строки
        return super().__lt__(other)  # стандартное поведение, если что-то пошло не так
#"""Логотип"""

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    settings_window = Settings_Window(config)
    autoupdater = AutoUpdater(current_version)
    settings_window.show()
    autoupdater.run()
    sys.exit(app.exec_())
