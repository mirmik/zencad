---
layout: default
---

# ZenCad

## Description
ZenCad библиотека создания 3д CAD моделей.  
ZenCad использует ядро OpenCascade, скриптовый стиль OpenScad и язык общего назначения Python.  

## Installation

### Install with pip

```sh
pip install zencad
```

## Usage

### Simple example

Нарисуем параллелепипед:
```python
import zencad

m = zencad.box(300, 200, 100, center = True)

display(box)
show()
```

### Second simple example
```python
import zencad

box = zencad.box(300, 200, 100, center = True)
sphere = zencad.sphere(100).up(100)

union = box + sphere

display(union)
show()
```