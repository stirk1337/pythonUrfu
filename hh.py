import requests
import json
import csv
from datetime import date, datetime
import re


def clean(text):
    example = re.compile(r'<[^>]+>')
    s = example.sub('', text).replace(' ', ' ').replace('\xa0', ' ').strip()
    return re.sub(" +", " ", s)


def get_hh_ru():
    today = date.today()
    rows = []
    for page in range(20):
        req = requests.get(
            f'https://api.hh.ru/vacancies?specialization=1&date_from={today}&date_to={today}&per_page=100&page={page}')
        data = req.content.decode()
        req.close()
        js = json.loads(data)
        for item in js['items']:
            if 'python' not in item['name'] and 'Python' not in item['name']:
                continue
            row = [item['name']]
            req = requests.get(
                f'https://api.hh.ru/vacancies/{item["id"]}')
            data = req.content.decode()
            req.close()
            js = json.loads(data)
            s = js['key_skills']
            row.append(clean(js['description']))
            skills = []
            for skill in s:
                skills.append(skill['name'])
            skills = str(skills).replace('[', '').replace(']', '')
            row.append(skills)
            row.append(item['employer']['name'])
            if item['salary'] is None:
                row.append('Не указан')
                row.append('Не указан')
                row.append('Не указан')
            else:
                row.append(item['salary']['from'])
                row.append(item['salary']['to'])
                row.append(item['salary']['currency'])
            row.append(item['area']['name'])
            row.append(item['published_at'])
            rows.append(row)

    return rows


if __name__ == '__main__':
    print(get_hh_ru())

