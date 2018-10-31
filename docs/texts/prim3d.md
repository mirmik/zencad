---
layout : default
---

# 3d Примитивы

## Box  
{% highlight python %}
box(x, y, z, center = True/False);
box(size = (x,y,z), center = True/False);
box(size = x, center = True/False);
{% endhighlight %}

Example:
```python
zencad.box(size = [20, 20, 10], center = True)
```
![box.png](../images/box.png)

## Sphere  
{% highlight python %}
sphere(r = radius)
{% endhighlight %}

Example:
{% highlight python %}
zencad.sphere(r = 10)
{% endhighlight %}
![sphere.png](../images/sphere.png)

## Cylinder  
{% highlight python %}
cylinder(r = radius, h = height, center = True/False);
{% endhighlight %}

Example:
{% highlight python %}
zencad.cylinder(r = 10, h = 20)
zencad.cylinder(r = 10, h = 20, angle=50)
{% endhighlight %}
![cylinder.png](../images/cylinder.png) ![cylinder_sector.png](../images/cylinder_sector.png)

## Cone  
{% highlight python %}
cone(r1 = botRadius, r2 = topRadius, h = height, center = True/False);
{% endhighlight %}

Example:
{% highlight python %}
zencad.cone(r1 = 20, r2 = 10, h = 20, center = True)
{% endhighlight %}
![cone.png](../images/cone.png)

## Torus  
{% highlight python %}
torus(r1 = centralRadius, r2 = localRadius);
{% endhighlight %}

Example:
{% highlight python %}
zencad.torus(r1 = 10, r2 = 3);
{% endhighlight %}
![torus.png](../images/torus.png)