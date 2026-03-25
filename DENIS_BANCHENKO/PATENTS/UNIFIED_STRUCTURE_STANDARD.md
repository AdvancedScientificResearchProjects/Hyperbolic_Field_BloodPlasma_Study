# 🎯 UNIFIED PATENT REPOSITORY STRUCTURE STANDARD
# ЕДИНЫЙ СТАНДАРТ СТРУКТУРЫ ПАТЕНТНОГО РЕПОЗИТОРИЯ

**Version / Версия:** 4.0
**Effective Date / Дата вступления:** 24 March 2026
**Applies To / Применяется к:** ALL Kazpatent patent repositories

---

## 🌐 CRITICAL BILINGUAL STANDARD / КРИТИЧЕСКИЙ ДВУЯЗЫЧНЫЙ СТАНДАРТ

### ⚠️ ABSOLUTE RULE #1: BILINGUAL ORDER / АБСОЛЮТНОЕ ПРАВИЛО №1: ДВУЯЗЫЧНЫЙ ПОРЯДОК

**ENGLISH FIRST, THEN RUSSIAN - EVERYWHERE!**
**АНГЛИЙСКИЙ ПЕРВЫЙ, ЗАТЕМ РУССКИЙ - ВЕЗДЕ!**

| Element / Элемент | ❌ WRONG / НЕПРАВИЛЬНО | ✅ CORRECT / ПРАВИЛЬНО |
|------------------|------------------------|------------------------|
| **Issue Titles** | RU then EN / RU потом EN | **EN then RU / EN потом RU** |
| **Table Headers** | `Name / ФИО` | **`Name / ФИО`** (EN first!) |
| **Section Headers** | `Документы / Documents` | **`Documents / Документы`** (EN first!) |
| **Status** | `Завершено / Complete` | **`Complete / Завершено`** (EN first!) |

**CRITICAL EXAMPLE / КРИТИЧЕСКИЙ ПРИМЕР:**

❌ **WRONG ISSUE TITLE / НЕПРАВИЛЬНОЕ НАЗВАНИЕ ISSUE:**
```
📋 KZ327274 - Система Оценки Произведений Искусства / System for Evaluating Works of Art
```

✅ **CORRECT ISSUE TITLE / ПРАВИЛЬНОЕ НАЗВАНИЕ ISSUE:**
```
📋 KZ327274 - System for Evaluating Works of Art / Система Оценки Произведений Искусства
```

**WHY THIS MATTERS FOR INVESTORS:**
- International investors read English first
- Consistency across ALL repositories
- Professional appearance
- Easy scanning and navigation

---

### ⚠️ ABSOLUTE RULE #2: CORRESPONDENCE DOCUMENTATION / АБСОЛЮТНОЕ ПРАВИЛО №2: ДОКУМЕНТАЦИЯ ПЕРЕПИСКИ

**EVERY REPOSITORY MUST HAVE CORRESPONDENCE_FLOW_EN_RU.md!**
**КАЖДЫЙ РЕПОЗИТОРИЙ ДОЛЖЕН ИМЕТЬ CORRESPONDENCE_FLOW_EN_RU.md!**

**Purpose / Назначение:**
- **EN:** Complete bilingual record of all Kazpatent correspondence for investors
- **RU:** Полная двуязычная запись всей переписки с Казпатент для инвесторов

**Required Elements / Обязательные Элементы:**

1. **Mermaid Sequence Diagram** - Visual flow of all correspondence
2. **Detailed Chronology** - Each document with EN/RU description
3. **Summary Table** - All correspondence with barcodes
4. **Response Time Analysis** - Shows deadlines were met
5. **Investor Guide** - How to read the correspondence

**Location / Расположение:**
```
<Repository>/correspondence/CORRESPONDENCE_FLOW_EN_RU.md
```

**Gold Standard Example / Золотой Стандарт Пример:**
- See: `Kazpatent_Axionetic_Sensing_Reactions_Platform_in_Art_Patent/correspondence/CORRESPONDENCE_FLOW_EN_RU.md`

---

### ⚠️ ABSOLUTE RULE #4: MANDATORY VERIFICATION / АБСОЛЮТНОЕ ПРАВИЛО №4: ОБЯЗАТЕЛЬНАЯ ПРОВЕРКА

**BEFORE MARKING TASK AS COMPLETE / ПЕРЕД ТЕМ КАК ОТМЕТИТЬ ЗАДАЧУ КАК ЗАВЕРШЕННУЮ:**

**CRITICAL VERIFICATION CHECKLIST / КРИТИЧЕСКИЙ КОНТРОЛЬНЫЙ СПИСОК ПРОВЕРКИ:**

1. **✅ Check EVERY repository / Проверить КАЖДЫЙ репозиторий**
   - Open EACH of the 5 patent repositories / Открыть КАЖДЫЙ из 5 патентных репозиториев
   - Verify structure matches ASRP.art / Проверить соответствие структуры ASRP.art
   - Check EVERY folder / Проверить КАЖДУЮ папку

2. **✅ Check EVERY Issue / Проверить КАЖДЫЙ Issue**
   - Open EVERY Issue in repository / Открыть КАЖДЫЙ Issue в репозитории
   - Verify ALL tables are bilingual (EN/RU) / Проверить ЧТО ВСЕ таблицы двуязычные (EN/RU)
   - Verify ALL links work / Проверить ЧТО ВСЕ ссылки работают
   - Verify ALL documents have links / Проверить ЧТО ВСЕ документы имеют ссылки

3. **✅ Check EVERY table / Проверить КАЖДУЮ таблицу**
   - EVERY header has EN/RU / КАЖДЫЙ заголовок имеет EN/RU
   - EVERY cell has correct data / КАЖДАЯ ячейка имеет правильные данные
   - NO "Pending" if documents uploaded / НЕТ "Pending" если документы загружены
   - ALL uploaded documents have DIRECT links / ВСЕ загруженные документы имеют ПРЯМЫЕ ссылки

4. **✅ Check abbreviations / Проверить сокращения**
   - Russian abbreviation matches Russian name / Русское сокращение соответствует русскому названию
   - English abbreviation matches English name / Английское сокращение соответствует английскому названию
   - NO mixing languages in abbreviations / НЕТ смешивания языков в сокращениях

5. **✅ Check visual diagrams / Проверить визуальные схемы**
   - Mermaid diagrams present / Диаграммы Mermaid присутствуют
   - Flow charts match ASRP.art standard / Блок-схемы соответствуют стандарту ASRP.art
   - All correspondence visually represented / Вся переписка визуально представлена
   - Timeline diagrams included / Диаграммы временной шкалы включены
   - Payment timeline diagrams included / Диаграммы временной шкалы платежей включены

6. **✅ RE-CHECK EVERYTHING / ПЕРЕПРОВЕРИТЬ ВСЁ**
   - Go through ALL checks AGAIN / Пройти ВСЕ проверки СНОВА
   - Then AGAIN / Затем ЕЩЁ РАЗ
   - Do NOT stop until EVERYTHING is perfect / НЕ останавливаться пока ВСЁ не будет идеально

**⚠️ NEVER STOP UNTIL 100% COMPLIANT / НИКОГДА НЕ ОСТАНАВЛИВАЙСЯ ПОКА НЕ БУДЕТ 100% СООТВЕТСТВИЯ**

---

### ⚠️ ABSOLUTE RULE #4.1: ISSUE TABLE BILINGUAL REQUIREMENTS / АБСОЛЮТНОЕ ПРАВИЛО №4.1: ТРЕБОВАНИЯ К ДВУЯЗЫЧНЫМ ТАБЛИЦАМ В ISSUE

**EVERY Issue MUST have:**
**КАЖДЫЙ Issue ДОЛЖЕН ИМЕТЬ:**

1. **✅ ALL table headers bilingual / ВСЕ заголовки таблиц двуязычные**
   - Format: `English / Русский`
   - Example: `Document Type / Тип Документа`
   - Example: `Status / Статус`
   - Example: `Direct Link / Прямая Ссылка`

2. **✅ ALL status values bilingual / ВСЕ значения статуса двуязычные**
   - Example: `✅ Paid / Оплачено`
   - Example: `⏳ Pending / Ожидается`
   - Example: `✅ Uploaded / Загружено`

3. **✅ ALL links DIRECT to files / ВСЕ ссылки ПРЯМЫЕ на файлы**
   - Format: `[📄 View PDF](https://github.com/.../blob/main/path/to/file.pdf)`
   - NOT: `[📄 View PDF](payment-receipts/)` ← leads to folder, not file!
   - MUST lead to actual file, not folder!

4. **✅ Mermaid diagrams included / Диаграммы Mermaid включены**
   - `sequenceDiagram` for correspondence flow / sequenceDiagram для потока переписки
   - `timeline` for payment/timeline / timeline для платежей/временной шкалы
   - `flowchart` for process flow / flowchart для процесса

5. **✅ Corporate contact info / Корпоративная контактная информация**
   - Email: info@asrp.tech (NOT personal email!)
   - Company: ТОО "Перспективные Научно-Исследовательские Разработки"

**❌ WRONG EXAMPLES / НЕПРАВИЛЬНЫЕ ПРИМЕРЫ:**

```markdown
❌ | Document | Link |
   ^ Only English!

❌ [📄 View PDF](payment-receipts/)
   ^ Leads to folder, not file!

❌ [📄 View PDF](https://github.com/.../issues/5)
   ^ Leads back to same issue, circular link!
```

**✅ CORRECT EXAMPLES / ПРАВИЛЬНЫЕ ПРИМЕРЫ:**

```markdown
✅ | Document Type / Тип Документа | Direct Link / Прямая Ссылка |

✅ [📄 View PDF](https://github.com/denisbanchenko/Kazpatent_Inspira-X_Respiratory_Analysis_Patent/blob/main/payment-receipts/2025-09-17_Payment_KZ2025-0914.1_FilingFee_6096.16KZT_EPAY934135.pdf)
   ^ Direct link to actual PDF file!
```

---

### ⚠️ ABSOLUTE RULE #2.1: ISSUE TABLE BILINGUAL STANDARD / АБСОЛЮТНОЕ ПРАВИЛО №2.1: ДВУЯЗЫЧНЫЙ СТАНДАРТ ТАБЛИЦ В ISSUE

**EVERY WORD in EVERY table header MUST be bilingual!**
**КАЖДОЕ СЛОВО в КАЖДОМ заголовке таблицы ДОЛЖНО быть двуязычным!**

**❌ WRONG EXAMPLES FROM ISSUE #7 (Fractal Repo):**

```markdown
❌ WRONG - Only English:
| Document Type | Status |
|--------------|--------|
| Application Form | ⏳ Pending |

❌ WRONG - Mixed:
| Document Type / Тип документа | Status |
|------------------------------|--------|
| Application Form | ⏳ Pending |
```

**✅ CORRECT FORMAT:**

```markdown
✅ CORRECT - EVERY word is bilingual:
| Document Type / Тип Документа | Status / Статус |
|------------------------------|-----------------|
| Application Form / Заявление | ⏳ Pending / Ожидается |
| Description / Описание | ⏳ Pending / Ожидается |
| Claims / Формула | ⏳ Pending / Ожидается |
| Abstract / Реферат | ⏳ Pending / Ожидается |
| Correspondence / Переписка | ⏳ Pending / Ожидается |
| Payments / Платежи | ⏳ Pending / Ожидается |
| Figures / Чертежи | ⏳ Pending / Ожидается |
```

**❌ WRONG EXAMPLES FROM ISSUE #5 (Fractal Repo):**

```markdown
❌ WRONG - Only English:
| Name | Role | Responsibilities |
|------|------|----------------|
| BANCHENKO DENIS | Co-Inventor | Hyperbolic field physics |
```

**✅ CORRECT FORMAT:**

```markdown
✅ CORRECT - EVERY word is bilingual:
| Имя / Name | Роль / Role | Обязанности / Responsibilities |
|------------|-------------|-------------------------------|
| БАНЧЕНКО ДЕНИС ЮРЬЕВИЧ / BANCHENKO DENIS YURIEVICH | Соавтор / Co-Inventor | Физика гиперболических полей / Hyperbolic field physics |
| ОВСЯННИКОВА ВАЛЕРИЯ АЛЕКСАНДРОВНА / OVSEANNICOVA VALERIA ALEXANDROVNA | Соавтор / Co-Inventor | Биомедицинские протоколы / Biomedical protocols |
| КАПУСТИН МИХАЙЛО МИХАЙЛОВИЧ / KAPUSTIN MYKHAILO MYKHALOVICH | Соавтор / Co-Inventor | Системы управления / Control systems |
```

**CRITICAL CHECKLIST FOR EVERY ISSUE TABLE / КРИТИЧЕСКИЙ КОНТРОЛЬНЫЙ СПИСОК ДЛЯ КАЖДОЙ ТАБЛИЦЫ В ISSUE:**

- [ ] **EVERY column header** has BOTH EN and RU / КАЖДЫЙ заголовок столбца имеет И EN И RU
- [ ] **EVERY cell** has BOTH EN and RU (where applicable) / КАЖДАЯ ячейка имеет И EN И RU (где применимо)
- [ ] **NO English-only** headers / НЕТ заголовков только на английском
- [ ] **NO Russian-only** headers / НЕТ заголовков только на русском
- [ ] **EN first, then RU** / СНЧАЛА EN, затем RU

**COMMON WORDS THAT MUST BE BILINGUAL / ОБЫЧНЫЕ СЛОВА, КОТОРЫЕ ДОЛЖНЫ БЫТЬ ДВУЯЗЫЧНЫМИ:**

| English | Russian | Correct Header / Правильный Заголовок |
|---------|---------|--------------------------------------|
| Name | Имя/ФИО | `Name / ФИО` |
| Role | Роль | `Role / Роль` |
| Responsibilities | Обязанности | `Responsibilities / Обязанности` |
| Document | Документ | `Document / Документ` |
| Type | Тип | `Type / Тип` |
| Status | Статус | `Status / Статус` |
| Date | Дата | `Date / Дата` |
| Description | Описание | `Description / Описание` |
| Link | Ссылка | `Link / Ссылка` |
| File | Файл | `File / Файл` |
| Total | Всего | `Total / Всего` |
| Uploaded | Загружено | `Uploaded / Загружено` |
| Pending | Ожидается | `Pending / Ожидается` |

---

### ⚠️ ABSOLUTE RULE #3: DOCUMENT PRESERVATION / АБСОЛЮТНОЕ ПРАВИЛО №3: СОХРАНЕНИЕ ДОКУМЕНТОВ

**NEVER DELETE DOCUMENTS - EVER!**
**НИКОГДА НЕ УДАЛЯЙТЕ ДОКУМЕНТЫ - НИКОГДА!**

| Action / Действие | ❌ WRONG | ✅ CORRECT |
|------------------|----------|------------|
| **Reorganizing** | Delete old files | **Move to `archive/`** |
| **Renaming** | `git rm` + new file | **`git mv` old new** |
| **Updating** | Replace file | **Keep old, add new version** |

**VIOLATION CONSEQUENCES / ПОСЛЕДСТВИЯ НАРУШЕНИЯ:**
- ❌ Loss of official patent documents
- ❌ Need to re-upload everything
- ❌ Wasted hours of work
- ❌ Broken links in issues

---

## 🏷️ PROJECT NAMING & BRANDING STANDARD / СТАНДАРТ ИМЕНОВАНИЯ И БРЕНДИНГА ПРОЕКТОВ

### ⚠️ CRITICAL RULE / КРИТИЧЕСКОЕ ПРАВИЛО:

**ALL project names MUST follow the unified format across:**
**ВСЕ названия проектов ДОЛЖНЫ следовать единому формату:**
- Repository names / Названия репозиториев
- README titles / Заголовки README
- Issue titles / Названия Issue
- Document headers / Заголовки документов

---

### 📋 OFFICIAL PROJECT NAMES / ОФИЦИАЛЬНЫЕ НАЗВАНИЯ ПРОЕКТОВ

| Short Code (EN) | Short Code (RU) | Full English Name | Full Russian Name | Emoji | Repository Name |
|-----------------|-----------------|------------------|-------------------|-------|-----------------|
| **ASRP.art** | **ПНИР.Искусство** | Axionetic Sensing Reactions Platform in Art | Платформа ноогенетического измерения реакций на искусство | 🧬 | `Kazpatent_Axionetic_Sensing_Reactions_Platform_in_Art_Patent` |
| **Fractal HFS** | **Фрактальная ГСФ** | Fractal Biomedical Hyperbolic Field System | Фрактальная биомедицинская система гиперболических полей | 🔬 | `Kazpatent_Fractal_Biomedical_System_Patent` |
| **GFS** | **ГСП** | Global Forecasting System | Глобальная система прогнозирования | 📊 | `Kazpatent_Global_Forecasting_System_Patent` |
| **Biophotonic** | **Биофотонная** | Biophotonic Optical Neurodiagnostic System | Биофотонная оптическая нейродиагностическая система | 🧬 | `Kazpatent_Biophotonic_Neurodiagnostic_System_Patent` |

---

### 🏷️ REPOSITORY NAMING RULE / ПРАВИЛО ИМЕНОВАНИЯ РЕПОЗИТОРИЕВ

**⚠️ CRITICAL RULE / КРИТИЧЕСКОЕ ПРАВИЛО:**

**ALL patent repositories MUST use FULL English name (no abbreviations)!**
**ВСЕ патентные репозитории ДОЛЖНЫ использовать ПОЛНОЕ английское название (без сокращений)!**

**Format / Формат:**
```
Kazpatent_<Full_English_Name>_Patent
```

| Wrong / Неправильно | Correct / Правильно |
|---------------------|---------------------|
| ❌ `Kazpatent_Inspira-X_Patent` | ✅ `Kazpatent_Inspira-X_Respiratory_Analysis_Patent` |
| ❌ `Kazpatent_GFS_Patent` | ✅ `Kazpatent_Global_Forecasting_System_Patent` |
| ❌ `Kazpatent_Fractal_Patent` | ✅ `Kazpatent_Fractal_Biomedical_System_Patent` |

**Russian Translation / Русский Перевод:**
- Repository name is in English / Название репозитория на английском
- Russian name used in README / Русское название используется в README
- Example: Inspira-X (EN) → Инспира-Х (RU) / Пример: Inspira-X (EN) → Инспира-Х (RU)

**Note on Russian Letters / Примечание о Русских Буквах:**
- Use Russian letter Х (Kha) NOT Latin X / Используйте русскую букву Х (Ха) НЕ латинскую X
- Example: Инспира-Х (correct) NOT Инспира-Икс (wrong)

---

### 📊 ISSUE DESCRIPTION REQUIREMENTS / ТРЕБОВАНИЯ К ОПИСАНИЮ ISSUE

**⚠️ CRITICAL RULE / КРИТИЧЕСКОЕ ПРАВИЛО:**

**ALL Issues MUST have FULL description with tables, links, and structure!**
**ВСЕ Issue ДОЛЖНЫ иметь ПОЛНОЕ описание с таблицами, ссылками и структурой!**

---

### 🌐 BILINGUAL TABLE HEADERS RULE / ПРАВИЛО ДВУЯЗЫЧНЫХ ЗАГОЛОВКОВ ТАБЛИЦ

**⚠️ CRITICAL RULE / КРИТИЧЕСКОЕ ПРАВИЛО:**

**EVERY table header MUST be bilingual (EN/RU) - EVERY WORD!**
**КАЖДЫЙ заголовок таблицы ДОЛЖЕН быть двуязычным (EN/RU) - КАЖДОЕ СЛОВО!**

**Format / Формат:**
```markdown
| English / Русский | English / Русский | English / Русский |
|-------------------|-------------------|-------------------|
| Content / Содержание | Content / Содержание | Content / Содержание |
```

**✅ CORRECT / ПРАВИЛЬНО:**
```markdown
| Date / Дата | Event / Событие | Barcode / Штрихкод | Status / Статус |
|-------------|-----------------|-------------------|-----------------|
| 2025-09-20 | Application Filed / Подача Заявки | 3675364 | ✅ Complete |
```

**❌ WRONG / НЕПРАВИЛЬНО:**
```markdown
| Date | Event | Barcode | Status |
|------|-------|---------|--------|
| 2025-09-20 | Application Filed | 3675364 | ✅ Complete |
```

**⚠️ EVERY WORD MUST BE BILINGUAL / КАЖДОЕ СЛОВО ДОЛЖНО БЫТЬ ДВУЯЗЫЧНЫМ:**
- ❌ `Date` → ✅ `Date / Дата`
- ❌ `Event` → ✅ `Event / Событие`
- ❌ `Barcode` → ✅ `Barcode / Штрихкод`
- ❌ `Status` → ✅ `Status / Статус`
- ❌ `Name` → ✅ `Name / ФИО`
- ❌ `Country` → ✅ `Country / Страна`
- ❌ `Role` → ✅ `Role / Роль`
- ❌ `Purpose` → ✅ `Purpose / Назначение`
- ❌ `Title` → ✅ `Title / Название`
- ❌ `Link` → ✅ `Link / Ссылка`
- ❌ `Document` → ✅ `Document / Документ`
- ❌ `Amount` → ✅ `Amount / Сумма`
- ❌ `Payment ID` → ✅ `Payment ID / ID Платежа`
- ❌ `Total` → ✅ `Total / Всего`
- ❌ `Uploaded` → ✅ `Uploaded / Загружено`
- ❌ `Pending` → ✅ `Pending / Ожидается`

**This applies to ALL tables in ALL Issues / Это применяется ко ВСЕМ таблицам во ВСЕХ Issue**

**Required Elements / Обязательные Элементы:**

1. **Status Badge / Значок Статуса:**
   ```markdown
   **Status / Статус:** ✅ Complete / Завершено
   **Last Updated / Последнее обновление:** 24 March 2026
   **Total Files / Всего файлов:** 4 documents
   ```

2. **Document Table / Таблица Документов:**
   ```markdown
   | # | Date / Дата | Document / Документ | Barcode / Штрихкод | Link / Ссылка |
   |---|-------------|---------------------|-------------------|---------------|
   | 1 | 2025-09-24 | Payment Notice | 3679220 | [View](link) |
   ```

3. **Repository Structure / Структура Репозитория:**
   ```markdown
   ```
   Repository/
   ├── 📄 README.md
   ├── 📁 docs/
   ├── 📁 correspondence/
   └── 📁 payment-receipts/
   ```
   ```

4. **Related Issues Table / Таблица Связанных Issue:**
   ```markdown
   | Issue / Issue | Title / Название | Purpose / Назначение |
   |--------------|-----------------|---------------------|
   | **#1** | Application | Examination status |
   ```

5. **Footer / Подвал:**
   ```markdown
   **All documents organized • Все документы организованы**  
   **24 March 2026 • email@example.com**  
   **Repository:** https://github.com/...
   ```

**❌ WRONG / НЕПРАВИЛЬНО:**
- Empty Issue body / Пустое тело Issue
- No tables / Нет таблиц
- No links / Нет ссылок
- No structure / Нет структуры

**✅ CORRECT / ПРАВИЛЬНО:**
- Full description with tables / Полное описание с таблицами
- Direct links to documents / Прямые ссылки на документы
- Repository structure diagram / Диаграмма структуры репозитория
- Related issues table / Таблица связанных issue
- Footer with contact info / Подвал с контактной информацией

---

### 🌐 BILINGUAL NAMING RULE / ПРАВИЛО ДВУЯЗЫЧНЫХ НАЗВАНИЙ

**⚠️ CRITICAL RULE / КРИТИЧЕСКОЕ ПРАВИЛО:**

**ALL Issue titles MUST be FULLY BILINGUAL - Russian AND English!**
**ВСЕ названия Issue ДОЛЖНЫ быть ПОЛНОСТЬЮ ДВУЯЗЫЧНЫМИ - Русский И Английский!**

**Format / Формат:**
```
[EMOJI] Russian Title / English Title (Russian status / English status)
```

| Wrong / Неправильно | Correct / Правильно |
|---------------------|---------------------|
| ❌ `📋 KZ327274 - Система Оценки Произведений Искусства (Отозвано)` | ✅ `📋 KZ327274 - Система Оценки Произведений Искусства / System for Evaluating Works of Art (Отозвано / Withdrawn)` |
| ❌ `📋 KZ327274 - System for Evaluating Works of Art (Withdrawn)` | ✅ `📋 KZ327274 - Система Оценки Произведений Искусства / System for Evaluating Works of Art (Отозвано / Withdrawn)` |
| ❌ Russian ONLY | ✅ Russian / English |
| ❌ English ONLY | ✅ Russian / English |

**✅ CORRECT FORMAT / ПРАВИЛЬНЫЙ ФОРМАТ:**
```
📋 KZ327274 - Система Оценки Произведений Искусства / System for Evaluating Works of Art (Отозвано / Withdrawn)
🟡 KZ380648 - Платформа Ноогенетического Измерения Реакций / Platform for Noogenetic Measurement of Reactions
🌍 PCT412362 - Платформа Ноогенетического Измерения / Platform for Noogenetic Measurement (PCT International)
📅 Временная Шкала и Дедлайны / Timeline and Deadlines
💰 Платежи и Кредитный Баланс / Payments and Credit Balance
📥 ВХОДЯЩИЕ - Репозиторий Документов / INCOMING - Document Repository
```

**Key Rules / Ключевые Правила:**
1. **BOTH languages REQUIRED** / **ОБА языка ОБЯЗАТЕЛЬНЫ**
2. **Russian FIRST, then English** / **Русский ПЕРВЫЙ, затем Английский**
3. **Separate with `/`** / **Разделять через `/`**
4. **NO `_EN_RU` suffix** / **БЕЗ суффикса `_EN_RU`**

---

### 🚫 NO _EN_RU SUFFIX RULE / ПРАВИЛО ОТСУТСТВИЯ СУФФИКСА _EN_RU

**⚠️ CRITICAL RULE / КРИТИЧЕСКОЕ ПРАВИЛО:**

**NEVER add `_EN_RU` suffix to Issue titles!**
**НИКОГДА не добавляйте суффикс `_EN_RU` к названиям Issue!**

| Wrong / Неправильно | Correct / Правильно |
|---------------------|---------------------|
| ❌ `📥 INBOX - Document Repository_EN_RU` | ✅ `📥 INBOX - Document Repository / Репозиторий документов` |
| ❌ `Timeline_EN_RU` | ✅ `Timeline & Deadlines / Сроки и дедлайны` |
| ❌ `Issue_Title_EN_RU` | ✅ `Issue_Title / Название_На_Русском` |

**Reason / Причина:**
- Issue titles are ALREADY bilingual (EN/RU) with `/` separator
- `_EN_RU` suffix is REDUNDANT and creates visual noise
- Названия Issue УЖЕ двуязычные с разделителем `/`
- Суффикс `_EN_RU` ИЗБЫТОЧЕН и создаёт визуальный шум

---

### 📊 BILINGUAL TABLES RULE / ПРАВИЛО ДВУЯЗЫЧНЫХ ТАБЛИЦ

**⚠️ CRITICAL RULE / КРИТИЧЕСКОЕ ПРАВИЛО:**

**ALL tables MUST be fully bilingual - BOTH headers AND content!**
**ВСЕ таблицы ДОЛЖНЫ быть полностью двуязычными - ОБА заголовки И содержимое!**

| Wrong / Неправильно | Correct / Правильно |
|---------------------|---------------------|
| ❌ `Name / ФИО` `Role / Роль` `Responsibilities / Обязанности` | ✅ `Имя / Name` `Роль / Role` `Обязанности / Responsibilities` |
| ❌ English headers with Russian content | ✅ Russian headers FIRST, then English |
| ❌ Mixed languages in same column | ✅ Consistent language per column |

**Table Format Standard / Стандарт Формата Таблиц:**

```markdown
✅ CORRECT / ПРАВИЛЬНО:
| Имя / Name | Роль / Role | Обязанности / Responsibilities |
|------------|-------------|-------------------------------|
| БАНЧЕНКО ДЕНИС ЮРЬЕВИЧ | Соавтор | Физика гиперболических полей |
| BANCHENKO DENIS YURIEVICH | Co-Inventor | Hyperbolic field physics |

❌ WRONG / НЕПРАВИЛЬНО:
| Name / ФИО | Role / Роль | Responsibilities / Обязанности |
|------------|-------------|-------------------------------|
| BANCHENKO DENIS YURIEVICH / БАНЧЕНКО ДЕНИС ЮРЬЕВИЧ | Co-Inventor / Соавтор | ...
```

**Key Rules / Ключевые Правила:**
1. **Russian FIRST** / **Русский ПЕРВЫЙ** - Russian language comes first in headers
2. **Separate rows** / **Отдельные строки** - One row per language OR fully bilingual cells
3. **No mixing** / **Без смешивания** - Don't mix languages in same cell with `/`

---

### ABBREVIATION TRANSLATIONS / ПЕРЕВОД АББРЕВИАТУР:**

| English Abbreviation | Russian Abbreviation | Full Russian Name |
|---------------------|---------------------|-------------------|
| **HFS** (Hyperbolic Field System) | **ГСФ** (Гиперболических Полей Система) | Фрактальная ГСФ |
| **GFS** (Global Forecasting System) | **ГСП** (Глобальная Система Прогнозирования) | ГСП |
| **ASRP** (Advanced Scientific Research Projects) | **ПНИР** (Платформа Ноогенетического Измерения Реакций) | ПНИР.Искусство |

---

### 📝 README TITLE FORMAT / ФОРМАТ ЗАГОЛОВКОВ README

```markdown
# [EMOJI] Short Name EN / Short Name RU

> **English:** Full English Name
> **Русский:** Полное русское название
```

**✅ CORRECT EXAMPLES / ПРАВИЛЬНЫЕ ПРИМЕРЫ:**

```markdown
# 🧬 ASRP.art / ПНИР.Искусство

> **English:** Axionetic Sensing Reactions Platform in Art
> **Русский:** Платформа ноогенетического измерения реакций на искусство
```

```markdown
# 🔬 Fractal HFS / Фрактальная ГСФ

> **English:** Fractal Biomedical Hyperbolic Field System
> **Русский:** Фрактальная биомедицинская система гиперболических полей
```

```markdown
# 📊 GFS / ГСП

> **English:** Global Forecasting System
> **Русский:** Глобальная система прогнозирования
```

```markdown
# 🧬 Biophotonic / Биофотонная

> **English:** Biophotonic Optical Neurodiagnostic System
> **Русский:** Биофотонная оптическая нейродиагностическая система
```

### Examples / Примеры:

**✅ CORRECT / ПРАВИЛЬНО:**
```markdown
# 🧬 ASRP.art Patent Portfolio / Патентный Портфель ASRP.art

> **English:** Axionetic Sensing Reactions Platform in Art
> **Русский:** Платформа аксионетического сенсоринга реакций на искусство
```

```markdown
# 🔬 Fractal HFS Patent Portfolio / Патентный Портфель Fractal HFS

> **English:** Fractal Biomedical Hyperbolic Field System
> **Русский:** Фрактальная биомедицинская система гиперболических полей
```

**❌ WRONG / НЕПРАВИЛЬНО:**
```markdown
# Kazpatent Patent Application: Fractal Biomedical Hyperbolic Field System
## Патентная заявка: Фрактальная Биомедицинская Система Гиперболических Полей
```

---

### 🎨 STANDARD EMOJIS / СТАНДАРТНЫЕ ЭМОДЗИ

| Category / Категория | Emoji | Usage / Использование |
|---------------------|-------|----------------------|
| **Neuro/Brain** | 🧬 | ASRP.art (neuro-art analysis) |
| **Medical/Bio** | 🔬 | Fractal HFS, Biophotonic |
| **Forecast/Data** | 📊 | GFS |
| **Patent** | 📋 | Applications, documents |
| **Money** | 💰 | Payments, fees |
| **Time** | 📅 | Timeline, deadlines |
| **Upload** | 📥 | INBOX, uploads |
| **Connection** | 🔗 | Project links |

---

## ⚠️ CRITICAL DOCUMENT PRESERVATION RULE / КРИТИЧЕСКОЕ ПРАВИЛО СОХРАНЕНИЯ ДОКУМЕНТОВ

### 🚫 NEVER DELETE DOCUMENTS / НИКОГДА НЕ УДАЛЯЙТЕ ДОКУМЕНТЫ

**ABSOLUTE RULE / АБСОЛЮТНОЕ ПРАВИЛО:**
- ❌ **NEVER** delete documents from repository / **НИКОГДА** не удаляйте документы из репозитория
- ❌ **NEVER** remove files without explicit user confirmation / **НИКОГДА** не удаляйте файлы без явного подтверждения пользователя
- ✅ **ALWAYS** preserve all uploaded documents / **ВСЕГДА** сохраняйте все загруженные документы
- ✅ **ALWAYS** move to `archive/` if reorganization needed / **ВСЕГДА** перемещайте в `archive/` если нужна реорганизация

### 📁 DOCUMENT REORGANIZATION / РЕОРГАНИЗАЦИЯ ДОКУМЕНТОВ

When restructuring folders / При реструктуризации папок:

1. **MOVE, DON'T DELETE** / **ПЕРЕМЕЩАЙТЕ, НЕ УДАЛЯЙТЕ**
   - Move old documents → `archive/` folder
   - Never remove from git history / Никогда не удаляйте из git истории

2. **PRESERVE GIT HISTORY** / **СОХРАНЯЙТЕ GIT ИСТОРИЮ**
   - Use `git mv` for renames / Используйте `git mv` для переименований
   - Never use `git rm` on documents / Никогда не используйте `git rm` на документах

3. **DOCUMENT EVOLUTION** / **ЭВОЛЮЦИЯ ДОКУМЕНТОВ**
   - Old versions → `archive/versions/`
   - New versions → appropriate folders / Новые версии → соответствующие папки

**💀 VIOLATION CONSEQUENCES / ПОСЛЕДСТВИЯ НАРУШЕНИЯ:**
- Loss of official patent documents / Потеря официальных патентных документов
- Need to re-upload all documents / Необходимость повторной загрузки всех документов
- Wasted hours of work / Потеря часов работы

---

## 📁 STANDARD DIRECTORY STRUCTURE / СТАНДАРТНАЯ СТРУКТУРА КАТАЛОГОВ

```
Kazpatent_<ProjectName>_Patent/
│
├── 📄 ROOT FILES / КОРНЕВЫЕ ФАЙЛЫ
│   ├── README.md                      # Main repository description
│   ├── DOCUMENT_INDEX_EN_RU.md        # Complete document registry
│   ├── DOCUMENT_UPLOAD_TRACKER.md     # Upload status tracker
│   └── .gitignore                     # Git ignore rules
│
├── 📂 docs/                           # CORE PATENT DOCUMENTS
│   ├── applications/                  # Application forms (Заявления)
│   ├── descriptions/                  # Description of invention (Описания)
│   ├── claims/                        # Claims (Формула изобретения)
│   ├── abstracts/                     # Abstracts (Рефераты)
│   └── drawings/                      # Drawings/Figures (Чертежи)
│
├── 📂 correspondence/                 # OFFICIAL CORRESPONDENCE
│   ├── incoming/                      # From Kazpatent (Входящие)
│   └── outgoing/                      # From applicant (Исходящие)
│
├── 📂 payment-receipts/               # PAYMENT DOCUMENTS
│   ├── filing-fees/                   # Filing fee receipts
│   ├── exam-fees/                     # Examination fee receipts
│   └── maintenance-fees/              # Maintenance fee receipts
│
├── 📂 legal/                          # LEGAL DOCUMENTS
│   ├── assignments/                   # Rights assignments
│   ├── licenses/                      # License agreements
│   └── disputes/                      # Dispute documents
│
├── 📂 translations/                   # TRANSLATION DOCUMENTS
│   ├── en/                            # English versions
│   └── ru/                            # Russian versions
│
├── 📂 INBOX/                          # NEW DOCUMENTS (to be sorted)
│   └── .gitkeep                       # Placeholder
│
└── 📂 archive/                        # ARCHIVED DOCUMENTS (old versions)
    └── .gitkeep                       # Placeholder
```

---

## 📝 DOCUMENT NAMING CONVENTION / КОНВЕНЦИЯ ИМЕНОВАНИЯ ДОКУМЕНТОВ

### Format / Формат:
```
YYYY-MM-DD_DocumentType_ApplicationNumber_Version_Description_Language.ext
```

### Examples / Примеры:
```
2025-11-08_Application_KZ2025-1095.1_v1_Original_RU.pdf
2025-11-08_Description_KZ2025-1095.1_v1_Original_RU.docx
2026-01-06_Incoming_KZ2025-1095.1_FormalExamQuery_Barcode3805316.pdf
2026-02-06_Outgoing_KZ2025-1095.1_ResponseToFormalExam.pdf
```

---

## 🐛 GITHUB ISSUES & MILESTONES STANDARD / СТАНДАРТ ISSUE И ВЕХ

### ⚠️ CRITICAL RULE / КРИТИЧЕСКОЕ ПРАВИЛО:

**ALL Issue titles MUST be bilingual (EN/RU) starting with English:**
**ВСЕ названия Issue ДОЛЖНЫ быть двуязычными (EN/RU) начиная с английского:**

```
[CATEGORY] English Title / Русский Название
```

### Issue Categories / Категории Issue:

| Category / Категория | Format / Формат | Example / Пример |
|---------------------|-----------------|------------------|
| **Application Documents** | `📋 Application: English / Русский` | `📋 Application: KZ 2025/1095.1 - Complete Application Package / Полный Пакет Заявки` |
| **Formal Examination** | `🔍 Formal Exam: English / Русский` | `🔍 Formal Exam: Response to Query #1 / Ответ на Запрос #1` |
| **Payment Documents** | `💰 Payment: English / Русский` | `💰 Payment: Filing Fee Receipt / Квитанция Пошлины` |
| **Correspondence** | `📨 Correspondence: English / Русский` | `📨 Correspondence: Incoming from Kazpatent / Входящее от Казпатент` |
| **Missing Documents** | `🔴 Missing: English / Русский` | `🔴 Missing: Payment Receipts / Квитанции об Оплате` |

### Milestone Naming / Названия Вех

**ALL Milestone names MUST be bilingual (EN/RU):**

```
Milestone N: English Title / Русский Название
```

### Milestone Examples / Примеры Вех:

| Milestone / Веха | Format / Формат |
|-----------------|-----------------|
| **Milestone 1** | `Milestone 1: Application Filing / Подача Заявки` |
| **Milestone 2** | `Milestone 2: Formal Examination / Формальная Экспертиза` |
| **Milestone 3** | `Milestone 3: Substantive Examination / Экспертиза по Существу` |
| **Milestone 4** | `Milestone 4: Patent Grant / Выдача Патента` |

### Label Standard / Стандарт Меток

**ALL labels MUST be bilingual where applicable:**

| Label / Метка | Color / Цвет | Description / Описание |
|--------------|--------------|----------------------|
| `📄 documents/документы` | #1D76DB | Document-related issues |
| `💰 payment/оплата` | #2ECC71 | Payment receipts |
| `🔍 examination/экспертиза` | #F39C12 | Examination process |
| `📨 correspondence/переписка` | #9B59B6 | Official letters |
| `🔴 missing/отсутствует` | #E74C3C | Missing documents |
| `✅ complete/завершено` | #27AE60 | Completed tasks |
| `⏳ pending/в ожидании` | #F1C40F | Pending actions |

---

## 📊 DOCUMENT INDEX STRUCTURE / СТРУКТУРА ИНДЕКСА ДОКУМЕНТОВ

Each `DOCUMENT_INDEX_EN_RU.md` must contain:

1. **Header Information:**
   - Application number(s) / Номер(а) заявки(ок)
   - Filing date(s) / Дата(ы) подачи
   - Last updated date / Дата последнего обновления
   - Total file count / Общее количество файлов

2. **Document Chronology Table / Хронологическая таблица:**
   - Grouped by date / Сгруппировано по датам
   - Status indicators: ✅ Uploaded/Загружено, ⏳ Pending/Ожидается, 🔴 Missing/Отсутствует

3. **Folder Structure Diagram / Диаграмма структуры папок**

4. **Status Summary / Сводка статусов:**
   - Total documents / Всего документов
   - Uploaded count / Загружено
   - Pending count / Ожидается

---

## ✅ COMPLIANCE CHECKLIST / КОНТРОЛЬНЫЙ СПИСОК СООТВЕТСТВИЯ

### Directory Structure / Структура каталогов:
- [ ] All repositories have identical root structure
- [ ] All use `docs/applications/`, `docs/descriptions/`, `docs/claims/`, `docs/abstracts/`, `docs/drawings/`
- [ ] All use `correspondence/incoming/` and `correspondence/outgoing/`
- [ ] All have `INBOX/` folder for new uploads
- [ ] All have `archive/` folder for old versions

### Documentation / Документация:
- [ ] All documents follow naming convention
- [ ] All have `DOCUMENT_INDEX_EN_RU.md`
- [ ] All have `DOCUMENT_UPLOAD_TRACKER.md`
- [ ] All have `README.md` with bilingual EN/RU support

### GitHub Issues & Milestones / Issue и Вехи:
- [ ] **ALL Issue titles are bilingual (EN/RU) starting with English**
- [ ] **ALL Milestone names are bilingual (EN/RU)**
- [ ] Standard labels applied to all Issues
- [ ] Issues organized by category

---

**Maintained by / Поддерживается:** ASRP Patent Management System
**Contact / Контакт:** denisbanchenko@asrp.tech
