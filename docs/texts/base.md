---
layout : default
---

# Базовые понятия

# Базовые объекты

## Point  
Объект типа точка. Является аргументом многих операций.
Может быть отображен.
{% highlight python %}
zencad.point(x, y, z)
zencad.pnt(x, y, z)
zencad.point([x,y,z])
{% endhighlight %}

Example:
{% highlight python %}
zencad.point(20, 20, 10)
{% endhighlight %}
![point.png](../images/point.png)
