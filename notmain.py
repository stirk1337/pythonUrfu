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
import decimal

class DataSet:
    def __init__(self, name, prof):
        self.CURRENCY_TO_RUB = {
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
        self.file_name = name
        self.prof = prof
        self.vac, self.header = self.csv_reader()
        self.vac = self.csv_filer()
        self.dict_naming = {}
        for i in range(len(self.header)):
            self.dict_naming[self.header[i]] = i
        self.salary_dynamic = {}
        self.count_dynamic = {}
        self.salary_prof_dynamic = {}
        self.city_count = {}
        self.salary_city = {}
        self.prof_count = {}
        self.most = {}
        self.years = {}

    def csv_reader(self):
        f = open(self.file_name, encoding='utf-8-sig')
        csv_list = csv.reader(f)
        data = [x for x in csv_list]
        return data, data[0]

    def csv_filer(self):
        all_vac = [x for x in self.vac[1:] if '' not in x and len(x) == len(self.vac[0])]
        vac = [[self.clean(y) for y in x] for x in all_vac]
        return vac

    @staticmethod
    def clean(text):
        example = re.compile(r'<[^>]+>')
        s = example.sub('', text).replace(' ', ' ').replace('\xa0', ' ').strip()
        return re.sub(" +", " ", s)

    def calculations(self):
        for item in self.vac:
            year = int(item[self.dict_naming['published_at']].split('-')[0])
            if year not in self.years:
                self.years[year] = year
            for i in range(len(item)):
                if self.header[i] == 'salary_from':
                    salary = (float(item[i]) + float(item[i + 1])) / 2
                    if item[self.dict_naming['salary_currency']] != 'RUR':
                        salary *= self.CURRENCY_TO_RUB[item[self.dict_naming['salary_currency']]]
                    if year not in self.salary_dynamic:
                        self.salary_dynamic[year] = []
                    self.salary_dynamic[year].append(int(salary))
                    if year not in self.salary_prof_dynamic:
                        self.salary_prof_dynamic[year] = []
                    if prof in item[0]: self.salary_prof_dynamic[year].append(int(salary))
                    if year not in self.prof_count:
                        self.prof_count[year] = 0
                    if prof in item[0]: self.prof_count[year] += 1
                city = item[self.dict_naming['area_name']]
                if city not in self.city_count:
                    self.city_count[city] = 0
                self.city_count[city] += 1
            if year not in self.count_dynamic:
                self.count_dynamic[year] = 0
            self.count_dynamic[year] += 1

        for item in self.vac:
            for i in range(len(item)):
                if self.header[i] == 'salary_from':
                    salary = (float(item[i]) + float(item[i + 1])) / 2
                    city = item[self.dict_naming['area_name']]
                    if item[self.dict_naming['salary_currency']] != 'RUR':
                        salary *= self.CURRENCY_TO_RUB[item[self.dict_naming['salary_currency']]]
                    if self.city_count[city] >= int(sum(self.city_count.values()) * 0.01):
                        if city not in self.salary_city:
                            self.salary_city[city] = []
                        self.salary_city[city].append(int(salary))

        for key in self.salary_dynamic:
            self.salary_dynamic[key] = sum(self.salary_dynamic[key]) // len(self.salary_dynamic[key])

        for key in self.salary_prof_dynamic:
            self.salary_prof_dynamic[key] = sum(self.salary_prof_dynamic[key]) // max(len(
                self.salary_prof_dynamic[key]), 1)

        for key in self.salary_city:
            self.salary_city[key] = sum(self.salary_city[key]) // len(self.salary_city[key])

        self.salary_city = dict(Counter(self.salary_city).most_common(10))
        self.most = {k: float('{:.4f}'.format(v / sum(self.city_count.values()))) for k, v in self.city_count.items()}
        self.most = dict(Counter(self.most).most_common(10))
        self.most = {k: v for k, v in self.most.items() if v >= 0.01}

    def show(self):
        print('Динамика уровня зарплат по годам:', self.salary_dynamic)
        print('Динамика количества вакансий по годам:', self.count_dynamic)
        print('Динамика уровня зарплат по годам для выбранной профессии:', self.salary_prof_dynamic)
        print('Динамика количества вакансий по годам для выбранной профессии:', self.prof_count)
        print('Уровень зарплат по городам (в порядке убывания):', self.salary_city)
        print('Доля вакансий по городам (в порядке убывания):', self.most)


class report:
    def __init__(self, data):
        self.data = data

    def generate_excel(self, filename):
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


inp = input('Введите название файла: ')
prof = input('Введите название профессии: ')
data = DataSet(inp, prof)
data.calculations()
todo = input('Введите данные для печати: ')
if todo == 'Вакансии':
    data.show()
elif todo == 'Статистика':
    rep = report(data)
    rep.generate_pdf("report.pdf")