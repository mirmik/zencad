<div class="home-hero">
<h1>ZenCad.</h1>
<p class="home-tagline">Скриптовый CAD для праведных прогеров.</p>
<img src="../images/generic/zencad-logo.png" alt="Модель ZenCad: куб со сферическими вырезами">
</div>

## Что это?

ZenCad — параметрическое 3D-моделирование на Python с геометрическим ядром OpenCascade. Скрипт создаёт точную BREP-геометрию, которую можно показать, проверить и экспортировать без ручного построения в редакторе.

ZenCad подходит для прототипирования, подготовки моделей к 3D-печати и построения геометрии по расчётам Python. Инструкции для разработки и установки находятся на странице [Установка](installation.html).

## Быстрый старт

Установка и запуск редактора:

```sh
python3 -m pip install "zencad[gui]"
zencad
```

Сохраните модель в Python-файл и откройте его в редакторе:

```python
import zencad as z

model = z.box(200, center=True) - z.sphere(120) + z.sphere(60)
z.display(model)
z.show()
```

## Ссылки

- [Исходный код на GitHub](https://github.com/mirmik/zencad)
- [Пакет на PyPI](https://pypi.org/project/zencad/)
- [Миграция с ZenCad 1](migration.html)
