# Быстрая справка по тегам микроразметки

**Источник:** Методические рекомендации 2024  
**Полный отчет:** `docs/MICRODATA_COMPLETE_REPORT.md`

---

## Главный контейнер (обязателен)

```html
<div itemscope itemtype="https://schema.org/EducationalOrganization">
    <h1 itemprop="name">...</h1>
</div>
```

---

## Разделы и их теги

| № | Раздел | Endpoint | Контейнер | Элементы |
|---|--------|----------|-----------|----------|
| 1 | Основные сведения | `main` | `itemprop="mainInfo"`<br>`itemtype="EducationalOrganization"` | `fullName`, `shortName`, `regDate`, `address`, `telephone`, `email`, `workTime`<br>`uchredLaw` → `nameUchred`, `addressUchred`, `telUchred`, `mailUchred`, `websiteUchred`<br>`licenseDocLink`, `accreditationDocLink`<br>`addressPlaceSet`, `addressPlaceDop`, `addressPlaceOpp`, `addressPlacePrac`, `addressPlacePodg`, `addressPlaceGia` |
| 2 | Структура | `structure` | `itemprop="organizationStructure"`<br>`itemtype="Organization"`<br>`role="list"` | `itemprop="organizationUnit"`<br>`role="listitem"` |
| 2 | Органы управления | `structure` | `itemprop="managementBodies"`<br>`itemtype="ItemList"`<br>`role="list"` | `itemprop="managementBody"`<br>`role="listitem"` |
| 3 | Документы | `documents` | `itemprop="documents"`<br>`itemtype="ItemList"`<br>`role="list"` | `itemprop="document"`<br>`itemscope itemtype="MediaObject"`<br>`itemprop="contentUrl"`<br>`role="listitem"` |
| 4 | Образование | `education` | `itemprop="educationalCredentialAwarded"`<br>`itemtype="EducationalProgram"`<br>`role="list"` | `itemprop="educationItem"`<br>`role="listitem"` |
| 5 | Стандарты | `standards` | `itemprop="eduStandards"`<br>`itemtype="ItemList"`<br>`role="list"` | `role="listitem"` |
| 6 | Руководство | `management` | `itemprop="management"`<br>`itemtype="ItemList"`<br>`role="list"` | `itemprop="director"`, `directorPhone`<br>`itemprop="deputyManagement"` или `deputy`<br>`role="listitem"` |
| 7 | Педагогический состав | `teachers` | `itemprop="teachers"`<br>`itemtype="ItemList"`<br>`role="list"` | `itemprop="teacher"`<br>`role="listitem"` |
| 8 | МТО | `facilities` | `itemprop="facilities"`<br>`itemtype="ItemList"`<br>`role="list"` | `role="listitem"` |
| 9 | Стипендии | `scholarships` | `itemprop="scholarships"`<br>`itemtype="ItemList"`<br>`role="list"` | `itemprop="supportMeasure"`<br>`role="listitem"` |
| 10 | Платные услуги | `paid-services` | `itemprop="paidEduServices"`<br>`itemtype="ItemList"`<br>`role="list"` | `itemprop="service"`<br>`role="listitem"` |
| 11 | Финансы | `finance` | `itemprop="financialActivity"`<br>`itemtype="ItemList"`<br>`role="list"` | `itemprop="report"`<br>`role="listitem"` |
| 12 | Вакансии | `vacancies` | `itemprop="vacantPlaces"`<br>`itemtype="ItemList"`<br>`role="list"` | `role="listitem"` |
| 13 | Международное сотрудничество | `international` | `itemprop="internationalCooperation"`<br>`itemtype="ItemList"`<br>`role="list"` | `itemprop="partner"`<br>`role="listitem"` |
| 14 | Питание | `food` | `itemprop="cateringOrganization"`<br>`itemtype="ItemList"`<br>`role="list"` | `role="listitem"` |

---

## Общие правила

### Контейнеры разделов
- `itemprop="<название>"` - связь с родителем
- `itemscope` - начало элемента
- `itemtype="https://schema.org/<Тип>"` - тип данных
- `role="list"` - для списковых разделов

### Элементы списков
- `role="listitem"` - обязателен
- `itemprop="<название>"` - связь с контейнером

### Документы
```html
<div role="listitem" itemprop="document" itemscope itemtype="https://schema.org/MediaObject">
    <a href="..." itemprop="contentUrl">...</a>
</div>
```

### Изображения
```html
<div role="listitem" itemprop="photo" itemscope itemtype="https://schema.org/ImageObject">
    <img src="..." itemprop="contentUrl" alt="...">
</div>
```

---

## Статус реализации

- ✅ **Реализовано:** Разделы 1-4 (28.6%)
- ⚠️ **Требуется:** Разделы 5-14 (71.4%)

---

**Для детальной информации см. `docs/MICRODATA_COMPLETE_REPORT.md`**

