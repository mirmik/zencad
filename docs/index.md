---
layout: default
---

# ZenCad

## Description
ZenCad библиотека создания 3д CAD моделей.  
ZenCad использует ядро OpenCascade, скриптовый стиль OpenScad и язык общего назначения Python.  

## Installation

### Install dependies

{% highlight sh %}
	sudo apt install qt5-default  
	sudo apt install liboce-*  
{% endhighlight %}

### Install with pip

{% highlight sh %}
	pip install zencad
{% endhighlight %}

### Get source code

{% highlight sh %}
	git clone https://github.com/mirmik/zencad
{% endhighlight %}

## Usage

### Simple example

Нарисуем параллелепипед:
{% highlight python %}
	import zencad
	import zencad.solid as solid
	from zencad.widget import *
	
	box = solid.box(300, 200, 100, center = True)
	
	display(box)
	show()
{% endhighlight %}

### Second simple example
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