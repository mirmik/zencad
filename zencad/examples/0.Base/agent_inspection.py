"""Small model suitable for ``zencad inspect`` examples."""

from zencad import box, cylinder, display, show


body = box(30, 20, 8, center=True)
mounting_hole = cylinder(3, 8).down(4)
display(body - mounting_hole)
show()
