# Атрибуты микроразметки согласно методическим рекомендациям

## Структура микроразметки

Согласно методическим рекомендациям, все разделы должны иметь правильную микроразметку Schema.org.

### Главный контейнер

```html
<div class="section-container" itemscope itemtype="https://schema.org/EducationalOrganization">
    <h1 itemprop="name">{{ section.title }}</h1>
```

### Разделы с микроразметкой

#### 1. Основные сведения
```html
<div class="form-data-section" itemprop="mainInfo" itemscope itemtype="https://schema.org/EducationalOrganization">
    <h2>Сведения об образовательной организации</h2>
    <!-- Поля с itemprop: fullName, shortName, regDate, address, telephone, email -->
</div>
```

#### 2. Структура и органы управления
```html
<div class="form-data-section" itemprop="organizationStructure" itemscope itemtype="https://schema.org/Organization" role="list">
    <h2>Структурные подразделения образовательной организации</h2>
    <!-- Элементы с itemprop: organizationUnit -->
</div>

<div class="form-data-section" itemprop="managementBodies" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Органы управления образовательной организацией</h2>
    <!-- Элементы с itemprop: managementBody -->
</div>
```

#### 3. Документы
```html
<div class="form-data-section" itemprop="documents" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Документы</h2>
    <!-- Элементы с itemprop: document, itemscope itemtype="https://schema.org/MediaObject" -->
</div>
```

#### 4. Образование
```html
<div class="form-data-section" itemprop="educationalCredentialAwarded" itemscope itemtype="https://schema.org/EducationalProgram" role="list">
    <h2>Образование</h2>
    <!-- Элементы с itemprop: educationItem -->
</div>
```

#### 5. Образовательные стандарты
```html
<div class="form-data-section" itemprop="eduStandards" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Образовательные стандарты и требования</h2>
</div>
```

#### 6. Руководство
```html
<div class="form-data-section" itemprop="management" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Руководство</h2>
    <!-- Элементы с itemprop: director, directorPhone, deputyManagement, deputy -->
</div>
```

#### 7. Педагогический состав
```html
<div class="form-data-section" itemprop="teachers" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Педагогический состав</h2>
    <!-- Элементы с itemprop: teacher -->
</div>
```

#### 8. Материально-техническое обеспечение
```html
<div class="form-data-section" itemprop="facilities" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Материально-техническое обеспечение и оснащенность образовательного процесса. Доступная среда</h2>
</div>
```

#### 9. Стипендии и меры поддержки
```html
<div class="form-data-section" itemprop="scholarships" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Стипендии и меры поддержки обучающихся</h2>
    <!-- Элементы с itemprop: supportMeasure -->
</div>
```

#### 10. Платные образовательные услуги
```html
<div class="form-data-section" itemprop="paidEduServices" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Платные образовательные услуги</h2>
    <!-- Элементы с itemprop: service -->
</div>
```

#### 11. Финансово-хозяйственная деятельность
```html
<div class="form-data-section" itemprop="financialActivity" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Финансово-хозяйственная деятельность</h2>
    <!-- Элементы с itemprop: report -->
</div>
```

#### 12. Вакантные места
```html
<div class="form-data-section" itemprop="vacantPlaces" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Вакантные места для приема (перевода) обучающихся</h2>
</div>
```

#### 13. Международное сотрудничество
```html
<div class="form-data-section" itemprop="internationalCooperation" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Международное сотрудничество</h2>
    <!-- Элементы с itemprop: partner -->
</div>
```

#### 14. Организация питания
```html
<div class="form-data-section" itemprop="cateringOrganization" itemscope itemtype="https://schema.org/ItemList" role="list">
    <h2>Организация питания в образовательной организации</h2>
</div>
```

### Документы и файлы

```html
<div class="file-item" role="listitem" itemprop="document" itemscope itemtype="https://schema.org/MediaObject">
    <a href="..." itemprop="contentUrl">Скачать документ</a>
</div>
```

### Изображения

```html
<div class="photo-item" role="listitem" itemprop="photo" itemscope itemtype="https://schema.org/ImageObject">
    <img src="..." itemprop="contentUrl" alt="...">
</div>
```

## Важные замечания

1. **Все разделы** должны быть вложены в главный контейнер с `itemscope itemtype="https://schema.org/EducationalOrganization"`

2. **Каждый раздел** должен иметь:
   - `itemprop` атрибут (связь с родительским контейнером)
   - `itemscope` и `itemtype` (определение типа данных раздела)
   - `role="list"` для списковых разделов

3. **Все элементы списков** должны иметь:
   - `role="listitem"`
   - Соответствующий `itemprop` атрибут

4. **Документы и изображения** должны иметь:
   - `itemscope itemtype="https://schema.org/MediaObject"` или `https://schema.org/ImageObject`
   - `itemprop="contentUrl"` для ссылок

## Проверка

После добавления микроразметки проверьте:
1. Все разделы имеют `itemscope` и `itemtype`
2. Все поля имеют соответствующие `itemprop` атрибуты
3. Структура вложенности правильная
4. Используются правильные типы Schema.org

