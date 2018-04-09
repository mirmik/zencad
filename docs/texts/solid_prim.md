---
layout : default
---

# CSG Примитивы

##Box
{% highlight python %}
cube(size = [x,y,z], center = True/False);
cube(size =  x ,     center = True/False);
{% endhighlight %}

##Sphere
{% highlight python %}
solid.sphere(r = radius)
{% endhighlight %}

##Cylinder
{% highlight python %}
cylinder(h = height, r = radius, center = True/False);
{% endhighlight %}

##Cone
{% highlight python %}
cone(h = height, r1 = botRadius, r2 = topRadius);
{% endhighlight %}