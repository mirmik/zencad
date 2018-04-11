---
layout : default
---

# Траекторные Операции

## LinearExtrude  
Стандартная операция вытягивания трехмерного объекта из двумерного профиля.

{% highlight python %}
linear_extrude(f = face, v = (x,y,z))
linear_extrude(f = face, v = z)
{% endhighlight %}

Example:
{% highlight python %}
from zencad import *

pnts = points([
	(0,0),
	(0,20),
	(5,20),
	(10,10),
	(15,20),
	(20,20),
	(20,0),
	(15,0),
	(15,15),
	(10,5),
	(5,15),
	(5,0),	
])

f0 = polygon(pnts)
s0 = linear_extrude(f0, (10,1,10))
s1 = linear_extrude(f0, (5,1,10))
s2 = linear_extrude(f0, (0,0,10))

f1 = polygon(pnts).rotateX(gr(10)).up(30)
s3 = linear_extrude(f1, (0,0,10))

display(s0.right(20))
display(s1)
display(s2.left(20))
display(s3.right(40))
show()
{% endhighlight %}
![box.png](../images/linear_extrude.png)
