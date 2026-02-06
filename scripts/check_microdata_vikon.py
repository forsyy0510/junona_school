#!/usr/bin/env python3
"""
Скрипт для проверки микроразметки (itemprop атрибутов) на страницах сайта
Полностью повторяет функциональность проверки VIKON с сайта https://db-nica.ru/ekspress-proverka
Проверяет соответствие "Методическим рекомендациям представления информации об образовательной организации 
в открытых источниках с учетом соблюдения требований законодательства в сфере образования 2024 года" (МР-2024)
"""

import sys
import os
from collections import defaultdict
import re
import json

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

# Полный список обязательных разделов согласно МР-2024
REQUIRED_SECTIONS = {
    'main': {
        'name': 'Основные сведения',
        'endpoint': 'main',
        'url_pattern': '/sveden/common',
        'main_itemprop': 'mainInfo',
        'main_itemtype': 'https://schema.org/EducationalOrganization',
        'required_attrs': ['fullName', 'shortName', 'regDate', 'address', 'telephone', 'email', 'workTime'],
        'optional_attrs': ['url', 'copy', 'uchredLaw'],
        'nested': {
            'uchredLaw': {
                'required': ['nameUchred', 'addressUchred', 'telUchred', 'mailUchred', 'websiteUchred'],
                'itemscope': True,
                'itemtype': 'https://schema.org/Organization'
            }
        }
    },
    'structure': {
        'name': 'Структура и органы управления образовательной организацией',
        'endpoint': 'structure',
        'url_pattern': '/sveden/struct',
        'main_itemprop': ['structOrgUprav', 'filInfo', 'repInfo', 'managementBodies'],
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': {
            'structOrgUprav': ['name', 'fio', 'post'],
            'filInfo': ['nameFil', 'fioFil', 'postFil'],
            'repInfo': ['nameRep', 'fioRep', 'postRep'],
            'managementBodies': ['managementBody']
        },
        'optional_attrs': {
            'structOrgUprav': ['addressStr', 'site', 'email', 'divisionClauseDocLink'],
            'filInfo': ['addressFil', 'websiteFil', 'emailFil', 'divisionClauseDocLink'],
            'repInfo': ['addressRep', 'websiteRep', 'emailRep', 'divisionClauseDocLink']
        }
    },
    'documents': {
        'name': 'Документы',
        'endpoint': 'documents',
        'url_pattern': '/sveden/document',
        'main_itemprop': 'documents',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': ['document'],
        'optional_attrs': ['ustavDocLink', 'licenseDocLink', 'accreditationDocLink', 'localActStud', 
                          'localActOrder', 'localActCollec', 'reportEduDocLink', 'prescriptionDocLink',
                          'priemDocLink', 'modeDocLink', 'tekKontrolDocLink', 'perevodDocLink', 'vozDocLink'],
        'document_structure': {
            'itemscope': True,
            'itemtype': 'https://schema.org/MediaObject',
            'required_attrs': ['contentUrl']
        }
    },
    'education': {
        'name': 'Образование',
        'endpoint': 'education',
        'url_pattern': '/sveden/education',
        'main_itemprop': 'eduAccred',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': ['eduOp'],
        'optional_attrs': ['eduAdOp', 'educationPlan', 'educationSchedule', 'eduChislenEl', 'languageEl', 'graduateJob']
    },
    'standards': {
        'name': 'Образовательные стандарты и требования',
        'endpoint': 'standards',
        'url_pattern': '/sveden/eduStandarts',
        'main_itemprop': 'eduStandards',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': [],
        'optional_attrs': ['eduFedDoc', 'eduStandartDoc', 'eduFedTreb', 'eduStandartTreb']
    },
    'management': {
        'name': 'Руководство. Педагогический (научно-педагогический) состав',
        'endpoint': 'management',
        'url_pattern': '/sveden/managers',
        'main_itemprop': 'management',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': ['rucovodstvo'],
        'optional_attrs': ['rucovodstvoZam'],
        'nested': {
            'rucovodstvo': {
                'required': ['fio', 'post', 'telephone', 'email'],
                'itemscope': True,
                'itemtype': 'https://schema.org/Person'
            },
            'rucovodstvoZam': {
                'required': [],
                'itemscope': True,
                'itemtype': 'https://schema.org/Person'
            }
        }
    },
    'teachers': {
        'name': 'Педагогический состав',
        'endpoint': 'teachers',
        'url_pattern': '/sveden/employees',
        'main_itemprop': 'teachingStaff',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': [],
        'optional_attrs': ['teacher', 'qualification'],
        'teacher_structure': {
            'itemscope': True,
            'itemtype': 'https://schema.org/Person',
            'required_attrs': ['fio', 'post']
        }
    },
    'facilities': {
        'name': 'Материально-техническое обеспечение и оснащенность образовательного процесса',
        'endpoint': 'facilities',
        'url_pattern': '/sveden/objects',
        'main_itemprop': 'facilities',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': [],
        'optional_attrs': ['purposeCab', 'purposeLibr', 'purposeSport', 'purposeFacil', 'ovz']
    },
    'scholarships': {
        'name': 'Стипендии и иные виды материальной поддержки',
        'endpoint': 'scholarships',
        'url_pattern': '/sveden/grants',
        'main_itemprop': 'scholarships',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': [],
        'optional_attrs': ['grant', 'support', 'localAct']
    },
    'paid-services': {
        'name': 'Платные образовательные услуги',
        'endpoint': 'paid-services',
        'url_pattern': '/sveden/paid_edu',
        'main_itemprop': 'paidEduServices',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': [],
        'optional_attrs': ['paidEdu', 'paidDog', 'paidSt', 'service']
    },
    'finance': {
        'name': 'Финансово-хозяйственная деятельность',
        'endpoint': 'finance',
        'url_pattern': '/sveden/budget',
        'main_itemprop': 'financialActivity',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': [],
        'optional_attrs': ['volume', 'finPost', 'finRas', 'finPlanDocLink']
    },
    'vacancies': {
        'name': 'Вакантные места для приема (перевода) обучающихся',
        'endpoint': 'vacancies',
        'url_pattern': '/sveden/vacant',
        'main_itemprop': 'vacantPlaces',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': [],
        'optional_attrs': ['vacant']
    },
    'international': {
        'name': 'Международное сотрудничество',
        'endpoint': 'international',
        'url_pattern': '/sveden/inter',
        'main_itemprop': 'internationalCooperation',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': [],
        'optional_attrs': ['internationalDog', 'partner']
    },
    'food': {
        'name': 'Организация питания в образовательной организации',
        'endpoint': 'food',
        'url_pattern': '/sveden/catering',
        'main_itemprop': 'cateringOrganization',
        'main_itemtype': 'https://schema.org/ItemList',
        'required_attrs': [],
        'optional_attrs': ['meals']
    }
}

def find_elements_with_itemprop(soup, itemprop_value):
    """Найти все элементы с указанным itemprop"""
    return soup.find_all(attrs={'itemprop': itemprop_value})

def check_main_container(soup):
    """Проверить наличие главного контейнера EducationalOrganization"""
    issues = []
    
    # Ищем главный контейнер
    main_container = soup.find(attrs={'itemtype': 'https://schema.org/EducationalOrganization'})
    
    if not main_container:
        issues.append({
            'type': 'error',
            'message': 'Главный контейнер с itemtype="https://schema.org/EducationalOrganization" не найден',
            'severity': 'critical'
        })
    else:
        # Проверяем наличие itemscope
        if not main_container.get('itemscope'):
            issues.append({
                'type': 'error',
                'message': 'Главный контейнер должен иметь атрибут itemscope',
                'severity': 'critical'
            })
        
        # Проверяем наличие itemprop="name" на заголовке
        name_element = main_container.find(attrs={'itemprop': 'name'})
        if not name_element:
            issues.append({
                'type': 'warning',
                'message': 'Не найден элемент с itemprop="name" внутри главного контейнера',
                'severity': 'medium'
            })
    
    return issues, main_container is not None

def check_section_exists(soup, section_config):
    """Проверить наличие раздела на странице"""
    issues = []
    found = False
    
    # Проверяем наличие главного itemprop раздела
    main_itemprop = section_config.get('main_itemprop')
    if isinstance(main_itemprop, list):
        # Если несколько возможных главных тегов
        for prop in main_itemprop:
            elements = find_elements_with_itemprop(soup, prop)
            if elements:
                found = True
                break
    else:
        elements = find_elements_with_itemprop(soup, main_itemprop)
        if elements:
            found = True
    
    if not found:
        issues.append({
            'type': 'error',
            'message': f"Раздел '{section_config['name']}' не найден на странице",
            'severity': 'critical',
            'itemprop': main_itemprop if not isinstance(main_itemprop, list) else main_itemprop[0]
        })
    
    return issues, found

def check_itemscope_itemtype(soup, itemprop_value, expected_itemtype):
    """Проверить наличие itemscope и itemtype для главного тега"""
    issues = []
    
    elements = find_elements_with_itemprop(soup, itemprop_value)
    if not elements:
        return issues
    
    for element in elements:
        # Проверяем, что это главный тег (не дочерний)
        parent_with_itemscope = element.find_parent(attrs={'itemscope': True})
        if parent_with_itemscope and parent_with_itemscope.get('itemprop') != itemprop_value:
            continue  # Это дочерний элемент, пропускаем
        
        if not element.get('itemscope'):
            issues.append({
                'type': 'error',
                'message': f"Главный тег '{itemprop_value}' должен иметь атрибут 'itemscope'",
                'severity': 'critical',
                'itemprop': itemprop_value
            })
        elif element.get('itemtype') != expected_itemtype:
            issues.append({
                'type': 'error',
                'message': f"Главный тег '{itemprop_value}' должен иметь itemtype='{expected_itemtype}'",
                'severity': 'critical',
                'itemprop': itemprop_value
            })
    
    return issues

def check_required_attributes(soup, section_config, main_itemprop):
    """Проверить наличие обязательных атрибутов"""
    issues = []
    found_attrs = defaultdict(list)
    
    # Находим все элементы с itemprop
    all_itemprop_elements = soup.find_all(attrs={'itemprop': True})
    for element in all_itemprop_elements:
        itemprop_value = element.get('itemprop')
        if itemprop_value:
            found_attrs[itemprop_value].append(element)
    
    # Проверяем обязательные атрибуты
    required_attrs = section_config.get('required_attrs', [])
    
    if isinstance(required_attrs, dict):
        # Если required_attrs - это словарь (для разных подразделов)
        for sub_itemprop, attrs in required_attrs.items():
            # Проверяем, что подраздел существует
            sub_elements = find_elements_with_itemprop(soup, sub_itemprop)
            if not sub_elements:
                continue
            
            for attr in attrs:
                if attr not in found_attrs:
                    issues.append({
                        'type': 'error',
                        'message': f"Обязательный атрибут '{attr}' не найден в разделе '{sub_itemprop}'",
                        'severity': 'high',
                        'itemprop': attr,
                        'parent': sub_itemprop
                    })
    else:
        # Если required_attrs - это список
        for attr in required_attrs:
            if attr not in found_attrs:
                issues.append({
                    'type': 'error',
                    'message': f"Обязательный атрибут '{attr}' не найден в разделе '{main_itemprop}'",
                    'severity': 'high',
                    'itemprop': attr,
                    'parent': main_itemprop
                })
    
    return issues, found_attrs

def check_nested_structure(soup, parent_itemprop, nested_config):
    """Проверить вложенную структуру"""
    issues = []
    
    parent_elements = find_elements_with_itemprop(soup, parent_itemprop)
    if not parent_elements:
        return issues
    
    for parent in parent_elements:
        # Проверяем itemscope и itemtype для родителя
        if nested_config.get('itemscope') and not parent.get('itemscope'):
            issues.append({
                'type': 'error',
                'message': f"Родительский тег '{parent_itemprop}' должен иметь атрибут 'itemscope'",
                'severity': 'critical',
                'itemprop': parent_itemprop
            })
        
        expected_itemtype = nested_config.get('itemtype')
        if expected_itemtype and parent.get('itemtype') != expected_itemtype:
            issues.append({
                'type': 'error',
                'message': f"Родительский тег '{parent_itemprop}' должен иметь itemtype='{expected_itemtype}'",
                'severity': 'critical',
                'itemprop': parent_itemprop
            })
        
        # Проверяем наличие дочерних атрибутов
        required_child_attrs = nested_config.get('required', [])
        for child_attr in required_child_attrs:
            child_in_parent = parent.find(attrs={'itemprop': child_attr})
            if not child_in_parent:
                issues.append({
                    'type': 'error',
                    'message': f"Дочерний тег '{child_attr}' не найден внутри '{parent_itemprop}'",
                    'severity': 'high',
                    'itemprop': child_attr,
                    'parent': parent_itemprop
                })
    
    return issues

def check_document_structure(soup, section_config):
    """Проверить структуру документов"""
    issues = []
    
    document_elements = find_elements_with_itemprop(soup, 'document')
    if not document_elements:
        return issues
    
    doc_structure = section_config.get('document_structure', {})
    if not doc_structure:
        return issues
    
    for doc_element in document_elements:
        # Проверяем itemscope
        if doc_structure.get('itemscope') and not doc_element.get('itemscope'):
            issues.append({
                'type': 'error',
                'message': 'Элемент документа должен иметь атрибут itemscope',
                'severity': 'high',
                'itemprop': 'document'
            })
        
        # Проверяем itemtype
        expected_itemtype = doc_structure.get('itemtype')
        if expected_itemtype and doc_element.get('itemtype') != expected_itemtype:
            issues.append({
                'type': 'error',
                'message': f"Элемент документа должен иметь itemtype='{expected_itemtype}'",
                'severity': 'high',
                'itemprop': 'document'
            })
        
        # Проверяем обязательные атрибуты внутри документа
        required_attrs = doc_structure.get('required_attrs', [])
        for attr in required_attrs:
            if not doc_element.find(attrs={'itemprop': attr}):
                issues.append({
                    'type': 'error',
                    'message': f"Внутри элемента документа должен быть атрибут '{attr}'",
                    'severity': 'high',
                    'itemprop': attr,
                    'parent': 'document'
                })
    
    return issues

def check_table_structure(soup):
    """Проверить табличную структуру данных"""
    issues = []
    
    tables = soup.find_all('table', class_='info-table')
    if not tables:
        grids = soup.find_all(class_='form-data-grid')
        if grids:
            issues.append({
                'type': 'warning',
                'message': "Используется старая структура 'form-data-grid' вместо таблиц",
                'severity': 'medium'
            })
        return issues
    
    for table in tables:
        rows = table.find_all('tr')
        if not rows:
            issues.append({
                'type': 'warning',
                'message': 'Таблица не содержит строк',
                'severity': 'low'
            })
        else:
            for row in rows:
                nested_tables = row.find_all('table')
                if nested_tables:
                    continue
                
                cells = row.find_all(['td', 'th'], recursive=False)
                if len(cells) != 2 and len(cells) > 0:
                    has_colspan = any(cell.get('colspan') for cell in cells)
                    if not has_colspan and len(cells) != 2:
                        issues.append({
                            'type': 'warning',
                            'message': f'Строка таблицы должна содержать 2 ячейки, найдено: {len(cells)}',
                            'severity': 'low'
                        })
    
    return issues

def check_section_compliance(soup, section_config):
    """Полная проверка соответствия раздела требованиям МР-2024"""
    all_issues = []
    stats = {
        'section_exists': False,
        'main_itemprop_found': False,
        'itemscope_correct': False,
        'itemtype_correct': False,
        'required_attrs_found': 0,
        'total_itemprop': 0,
        'total_itemscope': 0,
        'total_tables': 0
    }
    
    # Проверяем главный контейнер на каждой странице
    main_container_issues, _ = check_main_container(soup)
    all_issues.extend(main_container_issues)
    
    # Статистика
    stats['total_itemprop'] = len(soup.find_all(attrs={'itemprop': True}))
    stats['total_itemscope'] = len(soup.find_all(attrs={'itemscope': True}))
    stats['total_tables'] = len(soup.find_all('table', class_='info-table'))
    
    # Проверяем наличие раздела
    section_issues, section_exists = check_section_exists(soup, section_config)
    all_issues.extend(section_issues)
    stats['section_exists'] = section_exists
    
    if not section_exists:
        return all_issues, stats
    
    # Проверяем главный itemprop
    main_itemprop = section_config.get('main_itemprop')
    if isinstance(main_itemprop, list):
        main_itemprop = main_itemprop[0]  # Берем первый для проверки
    
    main_itemtype = section_config.get('main_itemtype')
    
    # Проверяем itemscope и itemtype
    itemscope_issues = check_itemscope_itemtype(soup, main_itemprop, main_itemtype)
    all_issues.extend(itemscope_issues)
    
    if not itemscope_issues:
        stats['itemscope_correct'] = True
        stats['itemtype_correct'] = True
        stats['main_itemprop_found'] = True
    
    # Проверяем обязательные атрибуты
    required_issues, found_attrs = check_required_attributes(soup, section_config, main_itemprop)
    all_issues.extend(required_issues)
    stats['required_attrs_found'] = len(section_config.get('required_attrs', [])) - len(required_issues)
    
    # Проверяем вложенные структуры
    nested_config = section_config.get('nested', {})
    for parent_itemprop, nested_conf in nested_config.items():
        nested_issues = check_nested_structure(soup, parent_itemprop, nested_conf)
        all_issues.extend(nested_issues)
    
    # Проверяем структуру документов
    if section_config.get('document_structure'):
        doc_issues = check_document_structure(soup, section_config)
        all_issues.extend(doc_issues)
    
    # Проверяем структуру таблиц
    table_issues = check_table_structure(soup)
    all_issues.extend(table_issues)
    
    return all_issues, stats

def generate_vikon_report(sections_data):
    """Сгенерировать отчет в формате VIKON"""
    report = {
        'summary': {
            'total_sections': len(sections_data),
            'sections_ok': 0,
            'sections_with_errors': 0,
            'sections_with_warnings': 0,
            'total_errors': 0,
            'total_warnings': 0
        },
        'sections': []
    }
    
    for section_data in sections_data:
        section_report = {
            'name': section_data['name'],
            'endpoint': section_data['endpoint'],
            'url': section_data['url'],
            'status': 'ok',  # ok, error, warning
            'issues': {
                'errors': [],
                'warnings': []
            },
            'stats': section_data['stats']
        }
        
        # Разделяем проблемы на ошибки и предупреждения
        for issue in section_data['issues']:
            if issue['type'] == 'error':
                section_report['issues']['errors'].append(issue)
                report['summary']['total_errors'] += 1
            elif issue['type'] == 'warning':
                section_report['issues']['warnings'].append(issue)
                report['summary']['total_warnings'] += 1
        
        # Определяем статус раздела
        if section_report['issues']['errors']:
            section_report['status'] = 'error'
            report['summary']['sections_with_errors'] += 1
        elif section_report['issues']['warnings']:
            section_report['status'] = 'warning'
            report['summary']['sections_with_warnings'] += 1
        else:
            section_report['status'] = 'ok'
            report['summary']['sections_ok'] += 1
        
        report['sections'].append(section_report)
    
    return report

def print_vikon_report(report):
    """Вывести отчет в формате VIKON"""
    print("=" * 80)
    print("ПРОВЕРКА СООТВЕТСТВИЯ МЕТОДИЧЕСКИМ РЕКОМЕНДАЦИЯМ МР-2024")
    print("Аналог проверки VIKON (https://db-nica.ru/ekspress-proverka)")
    print("=" * 80)
    print()
    
    # Итоговая статистика
    summary = report['summary']
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Всего разделов проверено: {summary['total_sections']}")
    print(f"   ✅ Разделов без проблем: {summary['sections_ok']}")
    print(f"   ❌ Разделов с ошибками: {summary['sections_with_errors']}")
    print(f"   ⚠️  Разделов с предупреждениями: {summary['sections_with_warnings']}")
    print(f"   Всего ошибок: {summary['total_errors']}")
    print(f"   Всего предупреждений: {summary['total_warnings']}")
    print()
    
    # Детальный отчет по разделам
    print("=" * 80)
    print("ДЕТАЛЬНЫЙ ОТЧЕТ ПО РАЗДЕЛАМ:")
    print("=" * 80)
    print()
    
    for section in report['sections']:
        status_icon = "✅" if section['status'] == 'ok' else "❌" if section['status'] == 'error' else "⚠️"
        print(f"{status_icon} {section['name']} ({section['endpoint']})")
        print(f"   URL: {section['url']}")
        
        if section['issues']['errors']:
            print(f"   ❌ Ошибок: {len(section['issues']['errors'])}")
            for error in section['issues']['errors']:
                print(f"      • {error['message']}")
        
        if section['issues']['warnings']:
            print(f"   ⚠️  Предупреждений: {len(section['issues']['warnings'])}")
            for warning in section['issues']['warnings']:
                print(f"      • {warning['message']}")
        
        print(f"   📊 Статистика:")
        stats = section.get('stats', {})
        print(f"      - Атрибутов itemprop: {stats.get('total_itemprop', 0)}")
        print(f"      - Элементов с itemscope: {stats.get('total_itemscope', 0)}")
        print(f"      - Таблиц: {stats.get('total_tables', 0)}")
        print()

def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Проверка микроразметки в формате VIKON')
    parser.add_argument('--output', '-o', type=str, help='Сохранить отчет в файл (JSON)')
    parser.add_argument('--endpoint', '-e', type=str, help='Проверить только указанный раздел')
    parser.add_argument('--format', '-f', choices=['text', 'json', 'both'], default='text',
                       help='Формат вывода отчета')
    args = parser.parse_args()
    
    app = create_app()
    
    with app.app_context():
        # Получаем разделы для проверки
        sections_to_check = []
        if args.endpoint:
            if args.endpoint in REQUIRED_SECTIONS:
                sections_to_check.append((args.endpoint, REQUIRED_SECTIONS[args.endpoint]))
            else:
                print(f"❌ Раздел '{args.endpoint}' не найден в списке обязательных разделов")
                return
        else:
            sections_to_check = list(REQUIRED_SECTIONS.items())
        
        if not sections_to_check:
            print("❌ Разделы для проверки не найдены")
            return
        
        # Создаем тестовый клиент
        client = app.test_client()
        
        # Проверяем главный контейнер на каждой странице
        # (он должен быть на всех страницах раздела "Сведения")
        
        # Проверяем каждый раздел
        sections_data = []
        
        for endpoint, section_config in sections_to_check:
            section_data = {
                'name': section_config['name'],
                'endpoint': endpoint,
                'url': section_config['url_pattern'],
                'issues': [],
                'stats': {}
            }
            
            try:
                # Получаем HTML страницы
                url = section_config['url_pattern']
                response = client.get(url, follow_redirects=True)
                
                if response.status_code != 200:
                    section_data['issues'].append({
                        'type': 'error',
                        'message': f'Страница недоступна (HTTP {response.status_code})',
                        'severity': 'critical'
                    })
                    # Инициализируем пустую статистику
                    section_data['stats'] = {
                        'section_exists': False,
                        'main_itemprop_found': False,
                        'itemscope_correct': False,
                        'itemtype_correct': False,
                        'required_attrs_found': 0,
                        'total_itemprop': 0,
                        'total_itemscope': 0,
                        'total_tables': 0
                    }
                    sections_data.append(section_data)
                    continue
                
                html_content = response.data.decode('utf-8')
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Проверяем соответствие раздела
                issues, stats = check_section_compliance(soup, section_config)
                section_data['issues'] = issues
                section_data['stats'] = stats
                
            except Exception as e:
                section_data['issues'].append({
                    'type': 'error',
                    'message': f'Ошибка при проверке: {str(e)}',
                    'severity': 'critical'
                })
                # Инициализируем пустую статистику при ошибке
                if 'stats' not in section_data or not section_data['stats']:
                    section_data['stats'] = {
                        'section_exists': False,
                        'main_itemprop_found': False,
                        'itemscope_correct': False,
                        'itemtype_correct': False,
                        'required_attrs_found': 0,
                        'total_itemprop': 0,
                        'total_itemscope': 0,
                        'total_tables': 0
                    }
            
            sections_data.append(section_data)
        
        # Генерируем отчет
        report = generate_vikon_report(sections_data)
        
        # Выводим отчет
        if args.format in ['text', 'both']:
            print_vikon_report(report)
        
        # Сохраняем в файл
        if args.output:
            if args.format in ['json', 'both']:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                print(f"\n📄 JSON отчет сохранен в файл: {args.output}")
            else:
                # Сохраняем текстовый отчет
                with open(args.output, 'w', encoding='utf-8') as f:
                    # Переопределяем print для записи в файл
                    import sys
                    original_stdout = sys.stdout
                    sys.stdout = f
                    print_vikon_report(report)
                    sys.stdout = original_stdout
                print(f"\n📄 Текстовый отчет сохранен в файл: {args.output}")

if __name__ == '__main__':
    main()

