---
layout: default
---

# zencad

Description
===========
ZenCad библиотека создания 3д CAD моделей.
ZenCad использует ядро OpenCascade, скриптовый стиль OpenScad и язык общего назначения Python.

Installation
============
Установка зависимостей
----------------------
{% highlight sh %}
	sudo apt install qt5-default  
	sudo apt install liboce-*  
{% endhighlight %}

Установка с помощью pip
-----------------------
{% highlight sh %}
	pip install zencad
{% endhighlight %}

Установка исходников
--------------------
{% highlight sh %}
	git clone https://github.com/mirmik/zencad
{% endhighlight %}

Usage
=====
Простой пример
--------------
Нарисуем параллелепипед:
{% highlight python %}
	import zencad
	import zencad.solid as solid
	from zencad.widget import *
	
	box = solid.box(300, 200, 100, center = True)
	
	display(box)
	show()
{% endhighlight %}

Чуть усложним:
{% highlight python %}
	import zencad
	import zencad.solid as solid
	from zencad.widget import *
	
	box = solid.box(300, 200, 100, center = True)
	sphere = solid.sphere(100).up(100)
	
	union = box + sphere
	
	display(union)
	show()
{% endhighlight %}