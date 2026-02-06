#!/usr/bin/env python3
"""
Скрипт для проверки микроразметки (itemprop атрибутов) на страницах сайта
Проверяет наличие обязательных атрибутов и правильность их структуры
"""

import sys
import os
from collections import defaultdict
import re

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Ошибка: библиотека beautifulsoup4 не установлена")
    print("Установите её командой: pip install beautifulsoup4")
    sys.exit(1)

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from info.models import InfoSection

# Ожидаемые атрибуты для каждого раздела
EXPECTED_ATTRIBUTES = {
    'main': {
        'mainInfo': {
            'required': ['fullName', 'shortName', 'regDate', 'address', 'telephone', 'email', 'workTime'],
            'optional': ['url', 'copy', 'uchredLaw'],
            'nested': {
                'uchredLaw': ['nameUchred', 'addressUchred', 'telUchred', 'mailUchred', 'websiteUchred']
            }
        }
    },
    'structure': {
        'structOrgUprav': {
            'required': ['name', 'fio', 'post'],
            'optional': ['addressStr', 'site', 'email', 'divisionClauseDocLink']
        },
        'filInfo': {
            'required': ['nameFil', 'fioFil', 'postFil'],
            'optional': ['addressFil', 'websiteFil', 'emailFil', 'divisionClauseDocLink']
        },
        'repInfo': {
            'required': ['nameRep', 'fioRep', 'postRep'],
            'optional': ['addressRep', 'websiteRep', 'emailRep', 'divisionClauseDocLink']
        }
    },
    'documents': {
        'documents': {
            'required': ['document'],
            'optional': ['ustavDocLink', 'licenseDocLink', 'accreditationDocLink', 'localActStud', 
                        'localActOrder', 'localActCollec', 'reportEduDocLink', 'prescriptionDocLink',
                        'priemDocLink', 'modeDocLink', 'tekKontrolDocLink', 'perevodDocLink', 'vozDocLink']
        }
    },
    'education': {
        'eduAccred': {
            'required': ['eduOp'],
            'optional': ['eduAdOp', 'educationPlan', 'educationSchedule', 'eduChislenEl', 'languageEl', 'graduateJob']
        }
    },
    'standards': {
        'eduStandards': {
            'required': [],
            'optional': ['eduFedDoc', 'eduStandartDoc', 'eduFedTreb', 'eduStandartTreb']
        }
    },
    'management': {
        'management': {
            'required': ['rucovodstvo'],
            'optional': ['rucovodstvoZam'],
            'nested': {
                'rucovodstvo': ['fio', 'post', 'telephone', 'email'],
                'rucovodstvoZam': []
            }
        }
    },
    'teachers': {
        'teachingStaff': {
            'required': [],
            'optional': ['teacher', 'qualification']
        }
    },
    'facilities': {
        'facilities': {
            'required': [],
            'optional': ['purposeCab', 'purposeLibr', 'purposeSport', 'purposeFacil', 'ovz']
        }
    },
    'scholarships': {
        'scholarships': {
            'required': [],
            'optional': ['grant', 'support', 'localAct']
        }
    },
    'paid-services': {
        'paidEduServices': {
            'required': [],
            'optional': ['paidEdu', 'paidDog', 'paidSt', 'service']
        }
    },
    'finance': {
        'financialActivity': {
            'required': [],
            'optional': ['volume', 'finPost', 'finRas', 'finPlanDocLink']
        }
    },
    'vacancies': {
        'vacantPlaces': {
            'required': [],
            'optional': ['vacant']
        }
    },
    'international': {
        'internationalCooperation': {
            'required': [],
            'optional': ['internationalDog', 'partner']
        }
    },
    'food': {
        'cateringOrganization': {
            'required': [],
            'optional': ['meals']
        }
    }
}

def find_elements_with_itemprop(soup, itemprop_value):
    """Найти все элементы с указанным itemprop"""
    return soup.find_all(attrs={'itemprop': itemprop_value})

def check_nested_structure(soup, parent_itemprop, child_itemprops):
    """Проверить, что дочерние теги находятся внутри главного тега"""
    parent_elements = find_elements_with_itemprop(soup, parent_itemprop)
    issues = []
    
    for parent in parent_elements:
        # Проверяем, что у родителя есть itemscope
        if not parent.get('itemscope'):
            issues.append(f"Главный тег '{parent_itemprop}' должен иметь атрибут 'itemscope'")
        
        # Проверяем наличие дочерних тегов внутри родителя
        for child_prop in child_itemprops:
            child_in_parent = parent.find(attrs={'itemprop': child_prop})
            if not child_in_parent:
                issues.append(f"Дочерний тег '{child_prop}' не найден внутри главного тега '{parent_itemprop}'")
            else:
                # Проверяем, что дочерний элемент действительно внутри родителя
                if not is_descendant(child_in_parent, parent):
                    issues.append(f"Дочерний тег '{child_prop}' найден, но не находится внутри главного тега '{parent_itemprop}'")
    
    return issues

def is_descendant(child, parent):
    """Проверить, является ли child потомком parent"""
    current = child.parent
    while current:
        if current == parent:
            return True
        current = current.parent
    return False

def check_section_microdata(soup, endpoint):
    """Проверить микроразметку для конкретного раздела"""
    issues = []
    found_attributes = defaultdict(list)
    
    # Находим все элементы с itemprop
    all_itemprop_elements = soup.find_all(attrs={'itemprop': True})
    
    for element in all_itemprop_elements:
        itemprop_value = element.get('itemprop')
        if itemprop_value:
            found_attributes[itemprop_value].append(element)
    
    # Проверяем ожидаемые атрибуты для раздела
    if endpoint in EXPECTED_ATTRIBUTES:
        section_attrs = EXPECTED_ATTRIBUTES[endpoint]
        
        for main_attr, config in section_attrs.items():
            # Проверяем наличие главного тега
            main_elements = find_elements_with_itemprop(soup, main_attr)
            if not main_elements:
                issues.append(f"⚠️  Главный тег '{main_attr}' не найден")
            else:
                # Проверяем обязательные дочерние теги
                for required_attr in config.get('required', []):
                    if required_attr not in found_attributes:
                        issues.append(f"❌ Обязательный атрибут '{required_attr}' не найден в разделе '{main_attr}'")
                    else:
                        # Проверяем структуру вложенности
                        if 'nested' in config and main_attr in config['nested']:
                            nested_attrs = config['nested'][main_attr]
                            if required_attr in nested_attrs:
                                nested_issues = check_nested_structure(soup, main_attr, [required_attr])
                                issues.extend(nested_issues)
                
                # Проверяем вложенные структуры
                if 'nested' in config:
                    for parent_attr, child_attrs in config['nested'].items():
                        nested_issues = check_nested_structure(soup, parent_attr, child_attrs)
                        issues.extend(nested_issues)
    
    # Проверяем наличие itemscope и itemtype где необходимо
    # Только для главных тегов текущего раздела
    if endpoint in EXPECTED_ATTRIBUTES:
        section_attrs = EXPECTED_ATTRIBUTES[endpoint]
        for main_attr in section_attrs.keys():
            main_elements = find_elements_with_itemprop(soup, main_attr)
            for element in main_elements:
                # Проверяем, что это действительно главный тег текущего раздела
                # (не дочерний элемент другого раздела)
                parent_with_itemscope = element.find_parent(attrs={'itemscope': True})
                if parent_with_itemscope and parent_with_itemscope.get('itemprop') != main_attr:
                    # Это дочерний элемент другого раздела, пропускаем
                    continue
                
                # Для раздела management: rucovodstvo и rucovodstvoZam - это дочерние элементы management,
                # а не главные теги, поэтому не проверяем их как главные
                if endpoint == 'management' and main_attr in ['rucovodstvo', 'rucovodstvoZam']:
                    # Проверяем, что они находятся внутри management
                    parent_management = element.find_parent(attrs={'itemprop': 'management'})
                    if not parent_management:
                        # Если они не внутри management, это может быть проблема структуры
                        continue
                    # Они должны иметь itemscope, так как это вложенные структуры
                    if not element.get('itemscope'):
                        issues.append(f"⚠️  Тег '{main_attr}' должен иметь атрибут 'itemscope'")
                    elif not element.get('itemtype'):
                        issues.append(f"⚠️  Тег '{main_attr}' с 'itemscope' должен иметь атрибут 'itemtype'")
                    continue
                
                if not element.get('itemscope'):
                    issues.append(f"⚠️  Главный тег '{main_attr}' должен иметь атрибут 'itemscope'")
                elif not element.get('itemtype'):
                    issues.append(f"⚠️  Главный тег '{main_attr}' с 'itemscope' должен иметь атрибут 'itemtype'")
    
    # Проверяем все элементы с itemscope на наличие itemtype
    for element in soup.find_all(attrs={'itemscope': True}):
        if not element.get('itemtype'):
            itemprop_value = element.get('itemprop', 'неизвестный')
            issues.append(f"⚠️  Элемент с 'itemscope' (itemprop='{itemprop_value}') должен иметь атрибут 'itemtype'")
    
    return issues, found_attributes

def check_table_structure(soup):
    """Проверить, что данные отображаются в табличной структуре"""
    issues = []
    
    # Проверяем наличие таблиц
    tables = soup.find_all('table', class_='info-table')
    if not tables:
        # Проверяем наличие form-data-grid (старая структура)
        grids = soup.find_all(class_='form-data-grid')
        if grids:
            issues.append("⚠️  Используется старая структура 'form-data-grid' вместо таблиц")
    
    # Проверяем структуру таблиц
    for table in tables:
        rows = table.find_all('tr')
        if not rows:
            issues.append("⚠️  Таблица не содержит строк")
        else:
            for row in rows:
                # Пропускаем строки с вложенными таблицами (например, таблица учредителя)
                nested_tables = row.find_all('table')
                if nested_tables:
                    continue  # Пропускаем строки с вложенными таблицами
                
                cells = row.find_all(['td', 'th'], recursive=False)  # Только прямые дочерние ячейки
                if len(cells) != 2 and len(cells) > 0:  # Игнорируем пустые строки
                    # Проверяем, не является ли это строкой с colspan
                    has_colspan = any(cell.get('colspan') for cell in cells)
                    if not has_colspan and len(cells) != 2:
                        issues.append(f"⚠️  Строка таблицы должна содержать 2 ячейки, найдено: {len(cells)}")
    
    return issues

def generate_report(section, html_content):
    """Сгенерировать отчет для раздела"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    report = {
        'section': section.title,
        'endpoint': section.endpoint,
        'url': section.url,
        'issues': [],
        'found_attributes': {},
        'stats': {
            'total_itemprop': 0,
            'total_itemscope': 0,
            'total_tables': 0
        }
    }
    
    # Проверяем микроразметку
    issues, found_attributes = check_section_microdata(soup, section.endpoint)
    report['issues'].extend(issues)
    report['found_attributes'] = {k: len(v) for k, v in found_attributes.items()}
    
    # Проверяем структуру таблиц
    table_issues = check_table_structure(soup)
    report['issues'].extend(table_issues)
    
    # Статистика
    report['stats']['total_itemprop'] = len(soup.find_all(attrs={'itemprop': True}))
    report['stats']['total_itemscope'] = len(soup.find_all(attrs={'itemscope': True}))
    report['stats']['total_tables'] = len(soup.find_all('table', class_='info-table'))
    
    return report

def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Проверка микроразметки на страницах сайта')
    parser.add_argument('--output', '-o', type=str, help='Сохранить отчет в файл')
    parser.add_argument('--endpoint', '-e', type=str, help='Проверить только указанный раздел')
    args = parser.parse_args()
    
    app = create_app()
    
    with app.app_context():
        # Получаем разделы
        if args.endpoint:
            sections = InfoSection.query.filter_by(endpoint=args.endpoint).all()
            if not sections:
                print(f"❌ Раздел с endpoint '{args.endpoint}' не найден")
                return
        else:
            sections = InfoSection.query.all()
        
        if not sections:
            print("❌ Разделы не найдены в базе данных")
            return
        
        # Открываем файл для записи, если указан
        output_file = None
        if args.output:
            try:
                output_file = open(args.output, 'w', encoding='utf-8')
            except Exception as e:
                print(f"⚠️  Не удалось открыть файл для записи: {e}")
                output_file = None
        
        def print_output(text):
            """Вывести текст в консоль и файл"""
            print(text)
            if output_file:
                output_file.write(text + '\n')
        
        print_output("=" * 80)
        print_output("ПРОВЕРКА МИКРОРАЗМЕТКИ (ITEMPROP АТРИБУТОВ)")
        print_output("=" * 80)
        print_output("")
        
        all_issues = []
        total_sections = 0
        sections_with_issues = 0
        
        # Создаем тестовый клиент для рендеринга страниц
        client = app.test_client()
        
        for section in sections:
            total_sections += 1
            print_output(f"Проверка раздела: {section.title} ({section.endpoint})")
            print_output(f"URL: {section.url}")
            
            try:
                # Определяем правильный URL для раздела
                url = section.url
                
                # Если URL начинается с /sidebar/, это боковой раздел - используем как есть
                if url.startswith('/sidebar/'):
                    pass
                # Если URL начинается с /info/, заменяем на /sveden/
                elif url.startswith('/info/'):
                    endpoint_part = url.replace('/info/', '')
                    # Используем маппинг endpoint'ов
                    from info.routes import ENDPOINT_MAPPING
                    mapped_endpoint = ENDPOINT_MAPPING.get(endpoint_part, endpoint_part)
                    url = f'/sveden/{mapped_endpoint}'
                elif url.startswith('/sveden/'):
                    # URL уже правильный
                    pass
                elif url.startswith('/'):
                    # Старый формат URL или прямой endpoint, пробуем найти правильный
                    endpoint_part = url.lstrip('/')
                    from info.routes import ENDPOINT_MAPPING
                    # Обратный маппинг
                    reverse_mapping = {v: k for k, v in ENDPOINT_MAPPING.items()}
                    if section.endpoint in reverse_mapping:
                        url = f'/sveden/{reverse_mapping[section.endpoint]}'
                    elif section.endpoint in ENDPOINT_MAPPING.values():
                        # endpoint уже правильный
                        url = f'/sveden/{section.endpoint}'
                    else:
                        # Пробуем использовать endpoint напрямую
                        url = f'/sveden/{section.endpoint}'
                else:
                    # Если URL не начинается с /, используем endpoint
                    url = f'/sveden/{section.endpoint}'
                
                # Получаем HTML страницы с обработкой редиректов
                response = client.get(url, follow_redirects=True)
                if response.status_code != 200:
                    print_output(f"❌ Ошибка получения страницы {url}: {response.status_code}")
                    print_output("")
                    continue
                
                html_content = response.data.decode('utf-8')
                
                # Генерируем отчет
                report = generate_report(section, html_content)
                
                # Выводим результаты
                if report['issues']:
                    sections_with_issues += 1
                    print_output(f"⚠️  Найдено проблем: {len(report['issues'])}")
                    for issue in report['issues']:
                        print_output(f"   {issue}")
                        all_issues.append({
                            'section': section.title,
                            'endpoint': section.endpoint,
                            'issue': issue
                        })
                else:
                    print_output("✅ Проблем не найдено")
                
                # Статистика
                print_output(f"📊 Статистика:")
                print_output(f"   - Найдено атрибутов itemprop: {report['stats']['total_itemprop']}")
                print_output(f"   - Найдено itemscope: {report['stats']['total_itemscope']}")
                print_output(f"   - Найдено таблиц: {report['stats']['total_tables']}")
                
                if report['found_attributes']:
                    print_output(f"   - Найденные атрибуты: {', '.join(report['found_attributes'].keys())}")
                
                print_output("")
                
            except Exception as e:
                print_output(f"❌ Ошибка при проверке раздела: {e}")
                print_output("")
                all_issues.append({
                    'section': section.title,
                    'endpoint': section.endpoint,
                    'issue': f"Ошибка: {str(e)}"
                })
        
        # Итоговый отчет
        print_output("=" * 80)
        print_output("ИТОГОВЫЙ ОТЧЕТ")
        print_output("=" * 80)
        print_output(f"Всего разделов проверено: {total_sections}")
        print_output(f"Разделов с проблемами: {sections_with_issues}")
        print_output(f"Разделов без проблем: {total_sections - sections_with_issues}")
        print_output(f"Всего найдено проблем: {len(all_issues)}")
        print_output("")
        
        if all_issues:
            print_output("ДЕТАЛЬНЫЙ СПИСОК ПРОБЛЕМ:")
            print_output("-" * 80)
            for issue in all_issues:
                print_output(f"[{issue['section']} ({issue['endpoint']})] {issue['issue']}")
        else:
            print_output("✅ Все проверки пройдены успешно!")
        
        print_output("")
        print_output("=" * 80)
        
        if output_file:
            output_file.close()
            print(f"\n📄 Отчет сохранен в файл: {args.output}")

if __name__ == '__main__':
    main()

