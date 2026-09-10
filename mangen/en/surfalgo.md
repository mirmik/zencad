# Classes of surfaces. 

-----------------
## Surface classes.
The following surface classes exist in ZenCad: 

* Face 
* Surface 

--------------------
## Find normal
Returns a `Vector3` normal at parameters _u_, _v_. `Face.normal()` defaults both parameters to zero; `Surface.normal(u, v)` requires both parameters.

Сигнатура:
```python
face.normal()
surface.normal(0, 0)
```

