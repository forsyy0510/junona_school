# Чеклист микроразметки для проверки VIKON

## ✅ Проверка наличия атрибутов

### Главный контейнер
- [x] `<div itemscope itemtype="https://schema.org/EducationalOrganization">`
- [x] `<h1 itemprop="name">`

### Раздел "Основные сведения"
- [x] `itemprop="mainInfo"`
- [x] `itemscope itemtype="https://schema.org/EducationalOrganization"`
- [x] `itemprop="fullName"`
- [x] `itemprop="shortName"`
- [x] `itemprop="regDate"`
- [x] `itemprop="address"`
- [x] `itemprop="telephone"`
- [x] `itemprop="email"`
- [x] `itemprop="workTime"`
- [x] `itemprop="uchredLaw"`
- [x] `itemprop="nameUchred"`

### Раздел "Структура и органы управления"
- [x] `itemprop="organizationStructure"`
- [x] `itemscope itemtype="https://schema.org/Organization"`
- [x] `itemprop="organizationUnit"`
- [x] `itemprop="managementBodies"`
- [x] `itemscope itemtype="https://schema.org/ItemList"`
- [x] `itemprop="managementBody"`

### Раздел "Документы"
- [x] `itemprop="documents"`
- [x] `itemscope itemtype="https://schema.org/ItemList"`
- [x] `itemprop="document"` на каждом файле
- [x] `itemscope itemtype="https://schema.org/MediaObject"` на каждом файле
- [x] `itemprop="contentUrl"` на ссылках

### Раздел "Образование"
- [x] `itemprop="educationalCredentialAwarded"`
- [x] `itemscope itemtype="https://schema.org/EducationalProgram"`
- [x] `itemprop="educationItem"`

### Раздел "Лицензия"
- [x] `itemprop="licenseDocLink"`
- [x] `itemscope itemtype="https://schema.org/MediaObject"`

### Раздел "Аккредитация"
- [x] `itemprop="accreditationDocLink"`
- [x] `itemscope itemtype="https://schema.org/MediaObject"`

### Раздел "Изображения"
- [x] `itemprop="photos"`
- [x] `itemscope itemtype="https://schema.org/ImageGallery"`
- [x] `itemprop="photo"` на каждом изображении
- [x] `itemscope itemtype="https://schema.org/ImageObject"` на каждом изображении
- [x] `itemprop="contentUrl"` на изображениях

## ⚠️ Что нужно проверить

1. **Все разделы должны иметь `itemscope` и `itemtype`**
2. **Все поля должны иметь соответствующие `itemprop` атрибуты**
3. **Структура вложенности должна быть правильной**
4. **Раздел "Образование" должен быть создан в базе данных**

## 🔍 Как проверить

1. Откройте страницу раздела в браузере
2. Просмотрите исходный код (Ctrl+U)
3. Найдите все `itemscope`, `itemtype`, `itemprop`
4. Убедитесь, что они присутствуют на всех разделах

## 📝 Команды для проверки

```bash
# Проверка наличия микроразметки в HTML
curl -s https://site-junona.onrender.com/sveden/common | grep -o 'itemscope\|itemtype\|itemprop' | wc -l

# Должно быть достаточно атрибутов (более 50)
```

