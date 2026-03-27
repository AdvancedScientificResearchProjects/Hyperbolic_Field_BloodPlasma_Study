# 📊 Patient Data Hub / Хаб Данных Пациентов

**Hyperbolic Field Blood Plasma Study / Исследование Кровяной Плазмы Гиперболических Полей**

---

## 🎯 QUICK NAVIGATION / БЫСТРАЯ НАВИГАЦИЯ

| 📁 **Patients / Пациенты** | 📊 **Statistics / Статистика** | 📋 **Protocols / Протоколы** |
|----------------------------|--------------------------------|------------------------------|
| [All Patients](#patient-datasets--наборы-данных-пациентов) | [Dataset Stats](#dataset-statistics--статистика-наборов-данных) | [Protocol EN/RU](../reports/experiment_protocol_en.md) |

---

## 📊 DATASET OVERVIEW / ОБЗОР НАБОРОВ ДАННЫХ

```mermaid
pie title Total Photos by Patient / Всего Фото по Пациентам
    "Patient 01 / Пациент 01" : 13
    "Patient 02 / Пациент 02" : 25
    "Patient 03 / Пациент 03" : 16
    "Patient 04 / Пациент 04" : 4
    "Patient 05 / Пациент 05" : 10
    "Patient 06 / Пациент 06" : 3
    "Patient 07 / Пациент 07" : 30
```

| Metric / Метрика | Value / Значение |
|------------------|------------------|
| **👥 Total Patients / Всего Пациентов** | 7 |
| **📸 Total Photographs / Всего Фотографий** | 101 images / 101 изображение |
| **🧪 Total Samples / Всего Образцов** | 33 samples / 33 образца |
| **⏰ Experiment Period / Период Эксперимента** | Jan 24 — Feb 7, 2026 / 24 янв — 7 фев 2026 |
| **🌡️ Temperature / Температура** | 17°C constant / постоянно |

---

## ⏰ CHANNEL EXPLANATION / ОБЪЯСНЕНИЕ КАНАЛОВ

```mermaid
flowchart LR
    A[🩸 Plasma Samples<br/>Образцы Плазмы] --> B[⏸️ Control<br/>Контроль<br/>No exposure]
    A --> C[⏩ Channel 19<br/>Канал 19<br/>Time Acceleration]
    A --> D[⏪ Channel 21<br/>Канал 21<br/>Time Deceleration]
    
    style B fill:#5fcdff
    style C fill:#ff9ff3
    style D fill:#54a0ff
```

| Channel / Канал | Icon / Иконка | Effect / Эффект | Description / Описание |
|-----------------|---------------|-----------------|------------------------|
| **Control / Контроль** | ⏸️ | No exposure | Baseline coagulation / Нормальное свёртывание |
| **Channel 19 / Канал 19** | ⏩ | Time Acceleration | Samples appear "older" / Образцы выглядят "старше" |
| **Channel 21 / Канал 21** | ⏪ | Time Deceleration | Samples appear "younger" / Образцы выглядят "моложе" |

---

## 📁 PATIENT DATASETS / НАБОРЫ ДАННЫХ ПАЦИЕНТОВ

### Complete Patient Directory / Полный Каталог Пациентов

| # | Patient / Пациент | Photos / Фото | Date / Дата | Blood Group / Группа Крови | Key Feature / Ключевая Особенность | Link / Ссылка |
|---|-------------------|---------------|-------------|---------------------------|-----------------------------------|---------------|
| 1 | **Patient 01 / Пациент 01** | 📸 13 | 2026-01-24 | II+ | First experiment / Первый эксперимент | [📂 View](patient-01/photos/) |
| 2 | **Patient 02 / Пациент 02** | 📸 25 | 2026-01-28 | III+ | Petri dish time-lapse / Чашка Петри | [📂 View](patient-02/photos/) |
| 3 | **Patient 03 / Пациент 03** | 📸 16 | 2026-01-29 | IV- | Rapid coagulation / Быстрое свёртывание | [📂 View](patient-03/photos/) |
| 4 | **Patient 04 / Пациент 04** | 📸 4 | 2026-01-30 | IV+ | No clots in Ch21 / Без сгустков в Ch21 | [📂 View](patient-04/photos/) |
| 5 | **Patient 05 / Пациент 05** | 📸 10 | 2026-01-31 | no data | Night session / Ночная сессия | [📂 View](patient-05/photos/) |
| 6 | **Patient 06 / Пациент 06** | 📸 3 | 2026-02-01 | I+ | Smallest dataset / Самый маленький | [📂 View](patient-06/photos/) |
| 7 | **Patient 07 / Пациент 07** | 📸 30 | 2026-02-07 | no data | Largest dataset / Самый большой | [📂 View](patient-07/photos/) |

---

## ⏰ EXPERIMENT TIMELINE / ВРЕМЕННАЯ ШКАЛА ЭКСПЕРИМЕНТА

```mermaid
timeline
    title Complete Experiment Timeline / Полная Временная Шкала Эксперимента
    section January 2026 / Январь 2026
        Jan 24 : Patient 01<br/>13 photos, II+
        Jan 28 : Patient 02<br/>25 photos, III+
        Jan 29 : Patient 03<br/>16 photos, IV-
        Jan 30 : Patient 04<br/>4 photos, IV+
        Jan 31 : Patient 05<br/>10 photos
    section February 2026 / Февраль 2026
        Feb 01 : Patient 06<br/>3 photos, I+
        Feb 07 : Patient 07<br/>30 photos
```

---

## 📊 DATASET STATISTICS / СТАТИСТИКА НАБОРОВ ДАННЫХ

### Photo Count by Patient / Количество Фото по Пациентам

```mermaid
barChart
    title Photos per Patient / Фото на Пациента
    x-axis Patient / Пациент
    y-axis Count / Количество
    bar P01 : 13
    bar P02 : 25
    bar P03 : 16
    bar P04 : 4
    bar P05 : 10
    bar P06 : 3
    bar P07 : 30
```

### Sample Type Distribution / Распределение Типов Образцов

```mermaid
pie title Total Samples by Type / Всего Образцов по Типам
    "⏸️ Control / Контроль" : 11
    "⏩ Channel 19 / Канал 19" : 11
    "⏪ Channel 21 / Канал 21" : 11
```

---

## 🔬 KEY FINDINGS / КЛЮЧЕВЫЕ НАХОДКИ

| Finding / Находка | Channel / Канал | Significance / Значимость |
|-------------------|-----------------|---------------------------|
| **37% fewer clots / 37% меньше сгустков** | ⏩ Channel 19 | Samples appear "older" / Образцы "старше" |
| **42% smaller clot area / 42% меньше площадь** | ⏩ Channel 19 | Accelerated lifecycle / Ускоренный цикл |
| **Only lysis case / Единственный случай лизиса** | ⏩ Channel 19 | Clot decomposition / Разложение сгустка |
| **No clots in one sample / Без сгустков в одном образце** | ⏪ Channel 21 | Delayed coagulation / Замедленное свёртывание |
| **Statistically significant p=0.027 / Статистически значимо** | All / Все | Gemini analysis / Анализ Gemini |

---

## 🔗 NAVIGATION LINKS / ССЫЛКИ НАВИГАЦИИ

| Resource / Ресурс | Link / Ссылка |
|-------------------|---------------|
| **🏠 Main README / Главный README** | [View / Просмотр](../../README.md) |
| **📊 Original Research / Оригинальное Исследование** | [View / Просмотр](../) |
| **📄 Reports / Отчёты** | [View / Просмотр](../reports/) |
| **🔬 Issues / Задачи** | [View / Просмотр](https://github.com/AdvancedScientificResearchProjects/Hyperbolic_Field_BloodPlasma_Study/issues) |

---

## 📞 CONTACT / КОНТАКТЫ

| Role / Роль | Name / Имя | Email |
|-------------|------------|-------|
| **Lead Researcher / Ведущий Исследователь** | Ovseannikova Valeria / Овсянникова Валерия | valeriaovseannicova@asrp.tech |
| **Program Director / Директор Программы** | Banchenko Denis / Банченко Денис | denisbanchenko@asrp.tech |

---

**Last Updated / Последнее Обновление:** 2026-03-26 | **Data Hub Version / Версия Хаба Данных:** 1.0

**© 2026 Advanced Scientific Research Projects (ASRP) / Перспективные Научно-Исследовательские Разработки**
