import csv
import re
from collections import Counter
import openpyxl
from openpyxl.styles import Font, Border, Side
from string import ascii_uppercase
from matplotlib import pyplot as plt
import numpy as np
from jinja2 import Environment, FileSystemLoader
import pdfkit


class DataSet:
    """Выполняет вычисления для данного csv файла с вакансии с сайта HH"

    Attributes:
        CURRENCY_TO_RUB (dict): Словарь конвертации валют
        name (str): Название файла
        prof (str): Название профессии
        vac (list): Список вакансий
        dict_naming (dict): Словарь колонки - индексы
        salary_dynamic (dict): Словарь зарплат по годам
        count_dynamic (dict): Словарь количества вакансий по годам
        salary_prof_dynamic (dict): Словарь уровня зарплат по годам для выбранной профессии prof
        prof_count (dict): Словарь количества вакансий по годам для выбранной профессии prof
        salary_city (dict): Словарь уровня зарплат по городам
        most (dict): Словарь доли ваканий по городам
        city_count (dict): Словарь количества городов
    """
    CURRENCY_TO_RUB = {
        "AZN": 35.68,
        "BYR": 23.91,
        "EUR": 59.90,
        "GEL": 21.74,
        "KGS": 0.76,
        "KZT": 0.13,
        "RUR": 1,
        "UAH": 1.64,
        "USD": 60.66,
        "UZS": 0.0055,
    }

    def __init__(self, name, prof):
        """Иницилиазирует объект DataSet, создаёт нужные словари для дальшейших вычислений

        Args:
            name (str): Название файла
            prof (str): Название профессии
        """
        self.file_name = name
        self.prof = prof
        self.vac, self.header = self.csv_reader()
        DataSet.make_chunks(self.vac, self.header)
        self.vac = self.csv_filer(self.vac)
        self.dict_naming, self.salary_dynamic, self.count_dynamic, self.salary_prof_dynamic, self.city_count, self.prof_count, self.years = DataSet.count(
            self.vac, self.header, self.prof)
        self.salary_city = DataSet.calculate_city(self.vac, self.header, self.dict_naming, self.city_count)
        self.salary_dynamic, self.count_dynamic, self.salary_prof_dynamic, self.prof_count, self.salary_city, self.most = DataSet.last_summ(
            self.salary_dynamic, self.salary_prof_dynamic, self.salary_city, self.city_count, self.count_dynamic,
            self.prof_count)

    def csv_reader(self):
        """Считывает csv-файл name

        Returns:
            data (list): Считанные профессии
            data[0] (list): Заголовки столбцов
        """
        f = open(self.file_name, encoding='utf-8-sig')
        csv_list = csv.reader(f)
        data = [x for x in csv_list]
        return data, data[0]

    @staticmethod
    def csv_filer(vac):
        """Обрабатывает csv-файл name: удаляет из него html-теги, удаляет неправильные столбцы

        Returns:
            vac (list): Список очищенных вакансий
        """
        all_vac = [x for x in vac[1:] if '' not in x and len(x) == len(vac[0])]
        vac = [[DataSet.clean(y) for y in x] for x in all_vac]
        return vac

    @staticmethod
    def clean(text):
        """Очищает строку от html-тегов и лишних пробелов

        Args:
            text (str): Строка, которую нужно отчистить от html-тегов и лишних пробелов

        Returns:
            str: Строка, очищенная от html-т    егов и лишних пробелов
        """
        example = re.compile(r'<[^>]+>')
        s = example.sub('', text).replace(' ', ' ').replace('\xa0', ' ').strip()
        return re.sub(" +", " ", s)

    @staticmethod
    def count(vac, header, prof):
        """Выполняет счёт по вакансиям

        """
        dict_naming = {}
        for i in range(len(header)):
            dict_naming[header[i]] = i
        salary_dynamic = {}
        count_dynamic = {}
        salary_prof_dynamic = {}
        city_count = {}
        prof_count = {}
        years = {}

        for item in vac:
            year = int(item[dict_naming['published_at']].split('-')[0])
            if year not in years:
                years[year] = year
            for i in range(len(item)):
                if header[i] == 'salary_from':
                    salary = (float(item[i]) + float(item[i + 1])) / 2
                    if item[dict_naming['salary_currency']] != 'RUR':
                        salary *= DataSet.CURRENCY_TO_RUB[item[dict_naming['salary_currency']]]
                    if year not in salary_dynamic:
                        salary_dynamic[year] = []
                    salary_dynamic[year].append(int(salary))
                    if year not in salary_prof_dynamic:
                        salary_prof_dynamic[year] = []
                    if prof in item[0]: salary_prof_dynamic[year].append(int(salary))
                    if year not in prof_count:
                        prof_count[year] = 0
                    if prof in item[0]: prof_count[year] += 1
                city = item[dict_naming['area_name']]
                if city not in city_count:
                    city_count[city] = 0
                city_count[city] += 1
            if year not in count_dynamic:
                count_dynamic[year] = 0
            count_dynamic[year] += 1
        return dict_naming, salary_dynamic, count_dynamic, salary_prof_dynamic, city_count, prof_count, years

    @staticmethod
    def calculate_city(vac, header, dict_naming, city_count):
        """Выполняет счет по городам

        """
        salary_city = {}
        for item in vac:
            for i in range(len(item)):
                if header[i] == 'salary_from':
                    salary = (float(item[i]) + float(item[i + 1])) / 2
                    city = item[dict_naming['area_name']]
                    if item[dict_naming['salary_currency']] != 'RUR':
                        salary *= DataSet.CURRENCY_TO_RUB[item[dict_naming['salary_currency']]]
                    if city_count[city] >= int(sum(city_count.values()) * 0.01):
                        if city not in salary_city:
                            salary_city[city] = []
                        salary_city[city].append(int(salary))
        return salary_city

    @staticmethod
    def last_summ(salary_dynamic, salary_prof_dynamic, salary_city, city_count, count_dynamic, prof_count):
        """ Решающая сумма всех словарей
            """
        for key in salary_dynamic:
            salary_dynamic[key] = sum(salary_dynamic[key]) // len(salary_dynamic[key])

        for key in salary_prof_dynamic:
            salary_prof_dynamic[key] = sum(salary_prof_dynamic[key]) // max(len(
                salary_prof_dynamic[key]), 1)

        for key in salary_city:
            salary_city[key] = sum(salary_city[key]) // len(salary_city[key])

        salary_city = dict(Counter(salary_city).most_common(10))
        most = {k: float('{:.4f}'.format(v / sum(city_count.values()))) for k, v in city_count.items()}
        most = dict(Counter(most).most_common(10))
        most = {k: v for k, v in most.items() if v >= 0.01}
        return salary_dynamic, count_dynamic, salary_prof_dynamic, prof_count, salary_city, most

    def show(self):
        """Печатает на экран все словари с данными

        """
        print('Динамика уровня зарплат по годам:', self.salary_dynamic)
        print('Динамика количества вакансий по годам:', self.count_dynamic)
        print('Динамика уровня зарплат по годам для выбранной профессии:', self.salary_prof_dynamic)
        print('Динамика количества вакансий по годам для выбранной профессии:', self.prof_count)
        print('Уровень зарплат по городам (в порядке убывания):', self.salary_city)
        print('Доля вакансий по городам (в порядке убывания):', self.most)

    @staticmethod
    def make_chunks(vac, header):
        was = []
        dict_naming = {}
        for i in range(len(header)):
            dict_naming[header[i]] = i
        for item in vac:
            if item == header:
                continue
            year = item[dict_naming['published_at']].split('-')[0]
            with open(f'files/{year}.csv', 'a', encoding='utf-8-sig', newline='') as file:
                writer = csv.writer(file)
                if year not in was:
                    writer.writerow(header)
                    was.append(year)
                writer.writerow(item)


class report:
    """Класс, генерирующий отчеты: excel-таблицы, графики, и pdf файл

    Attributes:
        data (DataSet): Все данные для визуализации
    """

    def __init__(self, data):
        """Инициализурует класс report

        Args:
            data (DataSet): Данные для визуализации
        """
        self.data = data

    def generate_excel(self, filename):
        """Генерирует excel-файл: 2 книги. Первая книга содержит статистику по годам, а вторая статистику по городам

        Args:
            filename (str): Название файла, который будет сгенерирован

        Returns:
            ws1 (Worksheet): Книга1 (статистика по годам)
            ws2 (Worksheet): Книга2 (статистика по городам)

        """
        workbook = openpyxl.Workbook()
        ws1 = workbook.active
        ws1.title = "Статистика по годам"
        ws2 = workbook.create_sheet("Статистика по городам")
        font_bold = Font(bold=True)
        border = Border(
            left=Side(border_style="thin", color="000000"),
            right=Side(border_style="thin", color="000000"),
            top=Side(border_style="thin", color="000000"),
            bottom=Side(border_style="thin", color="000000"),
        )
        titles_ws1 = ["Год", 'Средняя зарплата', f'Средняя зарплата - {self.data.prof}', 'Количество вакансий',
                      f'Количество вакансий - {self.data.prof}']
        titles_ws2 = ['Город', 'Уровень зарплат', "Город", 'Доля вакансий']
        dicts_ws1 = [self.data.years, self.data.salary_dynamic, self.data.salary_prof_dynamic, self.data.count_dynamic,
                     self.data.prof_count]
        lists_ws2 = [self.data.salary_city.keys(), self.data.salary_city.values(), self.data.salary_city.keys(),
                     self.data.most.values()]
        widths_ws1 = []
        widths_ws2 = []
        for item in dicts_ws1:
            widths_ws1.append(max(item, key=lambda x: len(str(x))))
        for item in lists_ws2:
            widths_ws2.append(max(item, key=lambda x: len(str(x))))
        for i in range(5):
            column = ascii_uppercase[i] + "1"
            ws1[column].font = font_bold
            ws1[column].border = border
            ws1[column] = titles_ws1[i]
            ws1.column_dimensions[ascii_uppercase[i]].width = max(len(titles_ws1[i]), len(str(widths_ws1[i]))) + 2
            n = 2
            for key in dicts_ws1[i]:
                column = ascii_uppercase[i] + str(n)
                ws1[column] = dicts_ws1[i][key]
                ws1[column].border = border
                n += 1

        alph = "ABDE"
        ws2.column_dimensions["C"].width = 2
        for i in range(4):
            column = alph[i] + "1"
            ws2[column].font = font_bold
            ws2[column].border = border
            ws2[column] = titles_ws2[i]
            ws2.column_dimensions[alph[i]].width = max(len(titles_ws2[i]), len(str(widths_ws2[i]))) + 2
            n = 2
            for item in lists_ws2[i]:
                column = alph[i] + str(n)
                if i == 3:
                    ws2[column].number_format = '0.00%'
                ws2[column] = item
                ws2[column].border = border
                n += 1
        workbook.save(filename)
        return ws1, ws2

    def generate_image(self, filename):
        """Генерирует график, основанный на data

        Args:
            filename (str): Название файла, который будет сгенерирован

        """
        width = 0.4
        fontsize = 8
        fig, axs = plt.subplots(2, 2, figsize=(9, 6))

        x = np.array(list(self.data.years.values()))
        g1 = list(self.data.salary_dynamic.values())
        g2 = list(self.data.salary_prof_dynamic.values())
        axs[0, 0].set_title('Уровень зарплат по годам', fontsize=fontsize)
        axs[0, 0].bar(x - width / 2, g1, width, label='средняя з/п')
        axs[0, 0].bar(x + width / 2, g2, width, label=f'з/п {self.data.prof}')
        axs[0, 0].set_xticks(x)
        axs[0, 0].set_xticklabels(x, fontsize=8, rotation=90)
        axs[0, 0].tick_params(axis="y", labelsize=8)
        axs[0, 0].legend(fontsize=fontsize)
        axs[0, 0].grid(axis='y')

        x = np.array(list(self.data.years.values()))
        g1 = list(self.data.count_dynamic.values())
        g2 = list(self.data.prof_count.values())
        axs[0, 1].set_title('Количество вакансий по годам', fontsize=fontsize)
        axs[0, 1].bar(x - width / 2, g1, width, label='Количество вакансий')
        axs[0, 1].bar(x + width / 2, g2, width, label=f'Количество вакансий {self.data.prof}')
        axs[0, 1].set_xticks(x)
        axs[0, 1].set_xticklabels(x, fontsize=8, rotation=90)
        axs[0, 1].tick_params(axis="y", labelsize=8)
        axs[0, 1].legend(fontsize=fontsize)
        axs[0, 1].grid(axis='y')

        y = list(self.data.salary_city.keys())
        y = [k.replace('-', '-\n').replace(' ', '\n') for k in y]
        g1 = list(self.data.salary_city.values())
        axs[1, 0].set_title('Уровень зарплат по городам', fontsize=fontsize)
        axs[1, 0].barh(y, g1, width + 0.3)
        axs[1, 0].set_yticks(y)
        axs[1, 0].set_yticklabels(y, fontsize=6, ha="right")
        axs[1, 0].tick_params(axis="x", labelsize=8)
        axs[1, 0].grid(axis='x')
        axs[1, 0].invert_yaxis()

        axs[1, 1].set_title('Доля вакансий по городам', fontsize=fontsize)
        axs[1, 1].pie([1 - sum(self.data.most.values())] + list(self.data.most.values()),
                      labels=['Другие'] + list(self.data.most.keys()), textprops={'fontsize': 6})

        plt.tight_layout()
        fig.show()
        fig.savefig(filename)

    def generate_pdf(self, filename):
        """Генерирует pdf, основанный на графике и excel таблицах.
        Вся информарция сначала парситься в html, а из html в pdf.

        Args:
            filename (str): Название файла, который будет сгенерирован

        """
        config = pdfkit.configuration(wkhtmltopdf=r'D:\wkhtmltopdf\bin\wkhtmltopdf.exe')
        options = {
            "enable-local-file-access": None
        }
        rep.generate_image("graph.png")
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("pdf_template.html")

        ws1, ws2 = self.generate_excel("report.xlsx")
        items1 = []
        items2 = []
        items3 = []
        for i in range(2, 18):
            row = dict()
            row['first'] = ws1["A" + str(i)].value
            row['second'] = ws1["B" + str(i)].value
            row['third'] = ws1["C" + str(i)].value
            row['four'] = ws1["D" + str(i)].value
            row['five'] = ws1["E" + str(i)].value
            items1.append(row)
        for i in range(2, 12):
            row = dict()
            row['first'] = ws2["A" + str(i)].value
            row['second'] = ws2["B" + str(i)].value
            items2.append(row)
        for i in range(2, 12):
            row = dict()
            row['first'] = ws2["D" + str(i)].value
            row['second'] = "{:.2%}".format(ws2["E" + str(i)].value).replace(".", ",")
            items3.append(row)
        pdf_template = template.render({'prof': self.data.prof, 'items1': items1, 'items2': items2, 'items3': items3})
        pdfkit.from_string(pdf_template, filename, configuration=config, options=options)


if __name__ == '__main__':

    inp = input('Введите название файла: ')
    prof = input('Введите название профессии: ')
    data = DataSet(inp, prof)
    todo = input('Введите данные для печати: ')
    if todo == 'Вакансии':
        data.show()
    elif todo == 'Статистика':
        rep = report(data)
        rep.generate_pdf("report.pdf")




