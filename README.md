# coffe_shop_analysis_project

## ER-диаграмма

![ER-диаграмма базы данных Urban Coffee](docs/er-diagram.png)

## Аналитические запросы

Все запросы реализованы в виде представлений (VIEW) в базе данных.
Исходный код запросов находится в папке `sql/`.

| Представление | Назначение |
|:---|:---|
| `v_abc_analysis` | ABC-анализ товаров по выручке |


Чтобы создать представления, выполните:
```bash
psql -U coffee_analyst -d urban_coffee -f sql/abc_analysis.sql
```