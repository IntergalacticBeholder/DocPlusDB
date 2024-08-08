import psycopg2
import xlwt

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from config import *


class Main_Window(QMainWindow):
    def __init__(self):
        super(Main_Window, self).__init__()
        self.resize(1000, 750)
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle('DocPlusDB')
        self.setWindowIcon(QtGui.QIcon('logo.png'))
        self.centralwidget.setFont(QtGui.QFont("Times", 10))
        self.search_groupe = QtWidgets.QGroupBox('Поиск', self.centralwidget)

        self.btn_clear = QtWidgets.QPushButton(self.search_groupe)
        self.btn_clear.setText("Очистить")
        self.btn_clear.clicked.connect(self.start_clear)
        self.btn_clear.setFixedWidth(100)

        self.btn_search = QtWidgets.QPushButton(self.search_groupe)
        self.btn_search.setText("Поиск")
        self.btn_search.setFixedWidth(100)
        self.btn_search.clicked.connect(self.start_search)

        self.btn_save = QtWidgets.QPushButton(self.search_groupe)
        self.btn_save.setText("Сохранить")
        self.btn_save.setEnabled(False)
        self.btn_save.setFixedWidth(100)
        self.btn_save.clicked.connect(self.save_table)


        self.table = QtWidgets.QTableWidget(self.search_groupe)
        self.table.setMinimumHeight(150)
        self.table.sortByColumn(2, QtCore.Qt.AscendingOrder)
        self.table.itemDoubleClicked.connect(self.equipment_show)

        self.search = QtWidgets.QLineEdit(self.search_groupe)

        self.search_for_what = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what.setMinimumWidth(130)
        self.search_for_what.addItems(['Всё', 'По Адресу', 'По Оборудованию', 'По Имени'])
        self.search_for_what.currentTextChanged.connect(self.sfw2)

        self.search_for_what2 = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what2.setMinimumWidth(250)
        self.search_for_what2.currentTextChanged.connect(self.sfw3)

        self.search_for_what3 = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what3.setMinimumWidth(150)

        self.layout = QGridLayout(self.centralwidget)
        self.layout.addWidget(self.search_groupe, 0, 0)
        self.layout_search = QGridLayout(self.search_groupe)
        self.layout_search.addWidget(self.search_for_what, 0, 0)
        self.layout_search.addWidget(self.search_for_what2, 0, 1)
        self.layout_search.addWidget(self.search_for_what3, 0, 2)
        self.layout_search.addWidget(self.search, 0, 3)
        self.layout_search.addWidget(self.btn_search, 0, 4)
        self.layout_search.addWidget(self.table, 1, 0, 1, 5)
        self.layout_search.addWidget(self.btn_save, 3, 0)
        self.layout_search.addWidget(self.btn_clear, 3, 4)


        #Добавление
        self.add_groupe = QtWidgets.QGroupBox('Добавление', self.centralwidget)
        self.add_groupe.setGeometry(10, 630, 880, 160)

        self.add_lable_address = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_address.setText('Адрес:')

        self.add_CB_address = QtWidgets.QComboBox(self.add_groupe)
        self.add_CB_address.setFixedWidth(300)
        self.add_CB_address.currentTextChanged.connect(self.add_room)

        self.add_lable_room = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_room.setText('Кабинет:')

        self.add_CB_room = QtWidgets.QComboBox(self.add_groupe)
        self.add_CB_room.setFixedWidth(300)

        self.add_lable_type = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_type.setText('Оборудование:')

        self.add_CB_type = QtWidgets.QComboBox(self.add_groupe)
        self.add_CB_type.setFixedWidth(300)
        self.add_CB_type.currentTextChanged.connect(self.sfw2)

        self.add_lable_name = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_name.setText('Наименование:')

        self.add_name = QtWidgets.QLineEdit(self.add_groupe)
        self.add_name.setFixedWidth(300)

        self.add_lable_sn = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_sn.setText('Серийный номер:')

        self.add_sn = QtWidgets.QLineEdit(self.add_groupe)
        self.add_sn.setFixedWidth(300)

        self.add_lable_date = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_date.setText('Год выпуска:')

        self.add_date = QtWidgets.QLineEdit(self.add_groupe)
        self.add_date.setFixedWidth(300)

        self.btn_add = QtWidgets.QPushButton(self.add_groupe)
        self.btn_add.setFixedWidth(100)
        self.btn_add.setText("Добавить")
        self.btn_add.clicked.connect(self.start_add)

        self.btn_add_clear = QtWidgets.QPushButton(self.add_groupe)
        self.btn_add_clear.setFixedWidth(100)
        self.btn_add_clear.setText("Очистить")
        self.btn_add_clear.clicked.connect(self.start_add_clear)

        self.add_groupe.setEnabled(True)
        self.add_groupe.setCheckable(True)

        self.layout.addWidget(self.add_groupe, 1, 0)
        self.layout_add = QGridLayout(self.add_groupe)
        self.layout_add.addWidget(self.add_lable_address, 0, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_CB_address, 1, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_room, 2, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_CB_room, 3, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_type, 4, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_CB_type, 5, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_name, 0, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_name, 1, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_sn, 2, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_sn, 3, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_date, 4, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_date, 5, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.btn_add, 1, 200, alignment = QtCore.Qt.AlignRight)
        self.layout_add.addWidget(self.btn_add_clear, 5, 200, alignment = QtCore.Qt.AlignRight)

        self.add_all()

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
                    x = ','.join(map(str, x))
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    self.add_CB_address.addItems(x.split(','))

                    #"""Выбор Типа"""
                    cur.execute("SELECT type FROM types "
                                "ORDER BY type ASC ")
                    x = cur.fetchall()
                    x = ','.join(map(str, x))
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    self.add_CB_type.addItems(x.split(','))

                    cur.execute("SELECT DISTINCT name FROM names")
                    x = cur.fetchall()
                    #print(x)
                    x = ','.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    completer = QCompleter(x.split(','))
                    self.add_name.setCompleter(completer)
                    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

            except Exception as e:
                error = QMessageBox()
                error.setWindowTitle("Ошибка")
                error.setText("Что-то пошло не так")
                error.setIcon(QMessageBox.Warning)
                error.setStandardButtons(QMessageBox.Ok)
                error.setDetailedText(f'Error {e}')
                print(f'Error {e}')
                error.exec_()
            finally:
                if con:
                    con.close()

    #"""Добавление комнаты, относительно улицы"""
    def add_room(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                cur.execute(f"SELECT "
                            f"address.room "
                            f"FROM address "
                            f"INNER JOIN streets ON street_id = streets.id "
                            f"WHERE streets.street = '{str(self.add_CB_address.currentText())}' "
                            f"ORDER BY room ASC ")
                x = cur.fetchall()
                x = ','.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                # print(x.split(','))
                self.add_CB_room.clear()
                self.add_CB_room.addItems(x.split(','))
        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            pass

    #"""Настройки поиска"""
    def sfw2(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                #"""Поиск без фильтров"""
                if self.search_for_what.currentText() == 'Всё':
                    self.search.setEnabled(False)
                    self.search_for_what2.setEnabled(False)
                    self.search_for_what3.setEnabled(False)
                    self.search_for_what2.clear()

                #"""Поиск по адресу"""

                elif self.search_for_what.currentText() == 'По Адресу':
                    self.search.setEnabled(False)
                    self.search_for_what2.setEnabled(True)
                    self.search_for_what3.setEnabled(True)
                    self.search_for_what2.clear()
                    cur.execute("SELECT street FROM streets")
                    x = cur.fetchall()
                    #print(x)
                    x = ','.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    self.search_for_what2.addItems(x.split(','))
                    #self.sfw3()

                #"""Поиск по типу"""
                elif self.search_for_what.currentText() == 'По Оборудованию':
                    self.search.setEnabled(False)
                    self.search_for_what2.setEnabled(True)
                    self.search_for_what3.setEnabled(False)
                    self.search_for_what2.clear()
                    cur.execute("SELECT type FROM types "
                                "ORDER BY type ASC ")
                    x = cur.fetchall()
                    #print(x)
                    x = ','.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    self.search_for_what2.addItems(x.split(','))

                #"""Поиск по имени"""
                elif self.search_for_what.currentText() == 'По Имени':
                    self.search.setEnabled(True)
                    self.search_for_what2.setEnabled(False)
                    self.search_for_what3.setEnabled(False)
                    cur.execute("SELECT DISTINCT name FROM names")
                    x = cur.fetchall()
                    #print(x)
                    x = ','.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    completer = QCompleter(x.split(','))
                    self.search.setCompleter(completer)
                    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                    self.search_for_what2.clear()
        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            if con:
                con.close()

    def sfw3(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                self.search_for_what3.clear()
                cur.execute(f"SELECT "
                            f"address.room "
                            f"FROM address "
                            f""
                            f"INNER JOIN streets ON street_id = streets.id "
                            f"WHERE streets.street = '{str(self.search_for_what2.currentText())}' "
                            f"ORDER BY room ASC "
                            )
                x = cur.fetchall()
                #print(x)
                x = ','.join(map(str, x))
                #print(x)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                #print(x.split(','))
                self.search_for_what3.addItems(x.split(','))
        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            if con:
                con.close()

    #"""Очистка таблицы"""
    def start_clear(self):
        self.table.clearContents()

    #"""Кнопка Поиска"""
    def start_search(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                #"""Кнопка поиска без фильтров"""
                if self.search_for_what.currentText() == 'Всё':
                    cur.execute(
                        "SELECT equipments.id, streets.street, address.room, types.type, names.name, names.sn, names.date "
                        "FROM equipments "
                        "INNER JOIN address ON address.id = equipments.address_id "
                        "INNER JOIN types ON types.id = equipments.type_id "
                        "INNER JOIN names ON names.id = equipments.name_id "
                        "INNER JOIN streets ON street_id = streets.id;")

                #"""Кнопка поиска по адресу"""
                elif self.search_for_what.currentText() == 'По Адресу':
                    self.table.clearContents()
                    cur.execute(
                        f"SELECT equipments.id, streets.street, address.room, types.type, names.name, names.sn, names.date "
                        f"FROM equipments "
                        f"INNER JOIN address ON address.id = equipments.address_id "
                        f"INNER JOIN types ON types.id = equipments.type_id "
                        f"INNER JOIN names ON names.id = equipments.name_id "
                        f"INNER JOIN streets ON street_id = streets.id "
                        f"WHERE streets.street = '{str(self.search_for_what2.currentText())}' AND address.room = '{str(self.search_for_what3.currentText())}'")

                #"""Кнопка поиска по типу"""
                elif self.search_for_what.currentText() == 'По Оборудованию':
                    self.table.clearContents()
                    cur.execute(
                        f"SELECT equipments.id, streets.street, address.room, types.type, names.name, names.sn, names.date "
                        f"FROM equipments "
                        f"INNER JOIN address ON address.id = equipments.address_id "
                        f"INNER JOIN types ON types.id = equipments.type_id "
                        f"INNER JOIN names ON names.id = equipments.name_id "
                        f"INNER JOIN streets ON street_id = streets.id "
                        f"WHERE types.type = '{str(self.search_for_what2.currentText())}'")

                #"""Кнопка поиска по имени"""
                elif self.search_for_what.currentText() == 'По Имени':
                    cur.execute(
                        f"SELECT equipments.id, streets.street, address.room, types.type, names.name, names.sn, names.date "
                        f"FROM equipments "
                        f"INNER JOIN address ON address.id = equipments.address_id "
                        f"INNER JOIN types ON types.id = equipments.type_id "
                        f"INNER JOIN names ON names.id = equipments.name_id "
                        f"INNER JOIN streets ON street_id = streets.id "
                        f"WHERE to_tsvector(name) @@ plainto_tsquery('{str(self.search.text())}')"
                    )
                data = cur.fetchall()
                a = len(data)  # rows
                b = len(data[0])  # columns
                #print(data, data[0])
                self.table.setColumnCount(b)
                self.table.setRowCount(a)
                self.table.setSortingEnabled(False)
                for j in range(a):
                    for i in range(b):
                        item = QtWidgets.QTableWidgetItem(str(data[j][i]))
                        self.table.setItem(j, i, item)
                self.table.setHorizontalHeaderLabels(
                        ['id', 'Адрес', 'Кабинет', 'Оборудование', 'Наименование', 'С/Н', 'Год выпуска'])
                self.table.setSortingEnabled(True)
                self.table.sortByColumn(1, QtCore.Qt.AscendingOrder)

                self.table.resizeColumnsToContents()
                self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
                self.btn_save.setEnabled(True)

        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            if con:
                con.close()

    #"""Кнопка добавления"""
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
                    f"SELECT id "
                    f"FROM streets "
                    f"WHERE street = '{str(self.add_CB_address.currentText())}'"
                )
                id_street = cur.fetchall()
                id_street = ','.join(map(str, id_street))
                for r in (('(', ''), (',)', '')):
                    id_street = id_street.replace(*r)
                #print(f"Улица_id: {id_street}")


                #"""ID Адресса"""
                cur.execute(
                    f"SELECT id "
                    f"FROM address "
                    f"WHERE room = '{str(self.add_CB_room.currentText())}' AND street_id = '{id_street}'"
                )
                id_address = cur.fetchall()
                id_address = ','.join(map(str, id_address))
                for r in (('(', ''), (',)', '')):
                    id_address = id_address.replace(*r)
                print(f"Комната_id: {id_address}")



                #"""ID Типа оборудования"""
                cur.execute(
                    f"SELECT id "
                    f"FROM types "
                    f"WHERE type = '{str(self.add_CB_type.currentText())}'"
                )
                id_type = cur.fetchall()
                id_type = ','.join(map(str, id_type))
                for r in (('(', ''), (',)', '')):
                    id_type = id_type.replace(*r)
                print(f"Тип_id: {id_type}")

                cur.execute(
                    f"INSERT INTO names ( "
                    f"id, name, sn, date) "
                    f"VALUES (DEFAULT, '{str(self.add_name.text())}', '{str(self.add_sn.text())}', '{str(self.add_date.text())}')"
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
                        f"INSERT INTO equipments ( "
                        f"id, address_id, type_id, name_id) "
                        f"VALUES (DEFAULT, '{id_address}', '{id_type}', '{id_name}')"
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
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            if con:
                con.close()

    def start_add_clear(self):
        self.add_name.clear()
        self.add_sn.clear()
        self.add_date.clear()

    #"""Кнопка сохранения"""
    def save_table(self):
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        heads = ['id', 'Адрес', 'Кабинет', 'Оборудование', 'Наименование', 'С/Н', 'Год выпуска']
        name, _ = QFileDialog.getSaveFileName(self, 'Сохранить', '.', 'Excel(*.xls)')
        # if not name:
        #     error = QMessageBox.information(self, 'Внимание!', 'Укажите имя файла')
        #     return
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Список оборудования')
        for colx in range(cols):
            width = 3000 + colx * 500
            ws.col(colx).width = width
        data = []
        for row in range(rows):
            items = []
            for col in range(cols):
                    items.append(self.table.item(row, col).text())
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
            i += 1
        wb.save(name)

    #"""Показать Данные оборудовани"""
    def equipment_show(self):

        row = self.table.currentIndex().row()
        global index
        index = self.table.model().index(row, 0).data()
        print(index)
        self.equipment_window = Equipment_Window()
        self.equipment_window.show()


#"""Информационное окно"""
class Equipment_Window(QtWidgets.QWidget):
    def __init__(self):
        super(Equipment_Window, self).__init__()
        self.resize(700, 450)
        self.centralwidget = QtWidgets.QWidget(self)
        self.setWindowTitle('Данные')
        self.setWindowIcon(QtGui.QIcon('logo.png'))
        self.centralwidget.setFont(QtGui.QFont("Times", 10))
        self.layout = QGridLayout(self.centralwidget)

        self.lable_address = QtWidgets.QLabel(self.centralwidget)
        self.lable_address.setText("Адрес:")
        self.layout.addWidget(self.lable_address, 0, 0)
        self.address = QtWidgets.QComboBox(self.centralwidget)
        self.address.currentTextChanged.connect(self.room_info)

        self.lable_room = QtWidgets.QLabel(self.centralwidget)
        self.lable_room.setText("Кабинет:")
        self.layout.addWidget(self.lable_room, 2, 0)
        self.room = QtWidgets.QComboBox(self.centralwidget)
        self.layout.addWidget(self.room, 3, 0)
        self.room.setEnabled(False)
        self.lable_type = QtWidgets.QLabel(self.centralwidget)
        self.lable_type.setText("Оборудование:")
        self.layout.addWidget(self.lable_type, 4, 0)
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

        self.table = QtWidgets.QTableWidget(self.centralwidget)
        self.layout.addWidget(self.table, 6, 0, 4, 4)
        self.table.setMinimumHeight(50)

        self.btn_change = QtWidgets.QPushButton(self.centralwidget)
        self.btn_change.setText("Изменить")
        #self.btn_change.setEnabled(False)
        self.btn_change.clicked.connect(self.change_equipment)
        self.layout.addWidget(self.btn_change, 1, 3)

        self.btn_save = QtWidgets.QPushButton(self.centralwidget)
        self.btn_save.setText("Сохранить")
        #self.btn_change.setEnabled(False)
        self.btn_save.clicked.connect(self.save_change)
        self.layout.addWidget(self.btn_save, 3, 3)
        self.btn_save.setEnabled(False)

        self.btn_cansel = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cansel.setText("Отменить")
        #self.btn_change.setEnabled(False)
        self.btn_cansel.clicked.connect(self.cansel)
        self.layout.addWidget(self.btn_cansel, 5, 3)
        self.btn_cansel.setEnabled(False)

        self.btn_add = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add.setText("Добавить запись")
        self.btn_add.setEnabled(False)
        self.layout.addWidget(self.btn_add, 11, 3)


        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                #"""Выдача инфы"""

                #"""Адрес"""
                cur.execute("SELECT street FROM streets")
                x = cur.fetchall()
                x = ','.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                self.address.addItems(x.split(','))
                self.layout.addWidget(self.address, 1, 0)
                cur.execute(
                    "SELECT streets.id "
                    "FROM equipments "
                    "INNER JOIN address ON address.id = equipments.address_id "
                    "INNER JOIN streets ON street_id = streets.id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                address = cur.fetchall()
                #print(address)
                address = ','.join(map(str, address))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    address = str(address.replace(*r))
                    print(address)
                self.address.setCurrentIndex(int(address)-1)
                self.address.setEnabled(False)

                #"""Кабинет"""


                #"""Оборудование"""
                cur.execute("SELECT type FROM types")
                x = cur.fetchall()
                x = ','.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                self.type.addItems(x.split(','))
                self.layout.addWidget(self.type, 5, 0)
                cur.execute(
                    "SELECT types.type "
                    "FROM equipments "
                    "INNER JOIN types ON types.id = equipments.type_id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                type = cur.fetchall()
                type = ','.join(map(str, type))
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
                    f"WHERE equipments.id = '{str(index)}'"
                )
                name = cur.fetchall()
                name = ','.join(map(str, name))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    name = str(name.replace(*r))
                #print(name)
                self.name.setText(f"{str(name)}")
                self.layout.addWidget(self.name, 1, 1)
                self.name.setMinimumWidth(250)
                self.name.setEnabled(False)

                #"""Серийный номер"""
                cur.execute(
                    "SELECT names.sn "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.name_id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                sn = cur.fetchall()
                sn = ','.join(map(str, sn))
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
                    f"WHERE equipments.id = '{str(index)}'"
                )
                date = cur.fetchall()
                date = ','.join(map(str, date))
                for r in (("(Decimal('", ''), ("'),)", '')):
                    date = str(date.replace(*r))
                #print(date)
                self.date.setText(f"{str(date)}")
                self.layout.addWidget(self.date, 5, 1)
                self.date.setEnabled(False)

        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            pass

    def change_equipment(self):
        self.address.setEnabled(True)
        self.room.setEnabled(True)
        self.type.setEnabled(True)
        self.name.setEnabled(True)
        self.sn.setEnabled(True)
        self.date.setEnabled(True)
        self.btn_save.setEnabled(True)
        self.btn_cansel.setEnabled(True)
        self.btn_change.setEnabled(False)

    def room_info(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                cur.execute(f"SELECT "
                            f"address.room "
                            f"FROM address "
                            f"INNER JOIN streets ON street_id = streets.id "
                            f"WHERE streets.street = '{str(self.address.currentText())}'")
                x = cur.fetchall()
                x = ','.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                self.room.clear()
                self.room.addItems(x.split(','))
                cur.execute(
                    "SELECT address.room "
                    "FROM equipments "
                    "INNER JOIN address ON address.id = equipments.address_id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                room = cur.fetchall()
                room = ','.join(map(str, room))
                #print(room)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    room = str(room.replace(*r))
                self.room.setCurrentText(room)
        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            pass

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
                self.cansel()




        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            pass

    def cansel(self):
        self.btn_change.setEnabled(True)
        self.btn_save.setEnabled(False)
        self.btn_cansel.setEnabled(False)
        self.address.setEnabled(False)
        self.room.setEnabled(False)
        self.type.setEnabled(False)
        self.name.setEnabled(False)
        self.sn.setEnabled(False)
        self.date.setEnabled(False)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main_window = Main_Window()
    main_window.show()
    sys.exit(app.exec_())
