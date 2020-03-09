#!/usr/bin/env python3

from zencad import *
import zencad.internal_models

SIDE=250
HEIGHT=10 
BORDER=10 
BSIDE=SIDE-BORDER*2
BCELL = BSIDE/8

board = zencad.assemble.unit()

board.add_shape(
	box(SIDE,SIDE,HEIGHT, center=True).up(HEIGHT/2) 
	- box(SIDE-BORDER*2,SIDE-BORDER*2,HEIGHT/2, center=True).up(HEIGHT/4 + HEIGHT/2)
	, color=color(0.6,0.4,0.2))

disp(board)

cell = box(BSIDE/8,BSIDE/8,HEIGHT/2).move(-SIDE/2+BORDER,-SIDE/2+BORDER,HEIGHT*2/4)

red_cell = disp(cell, color.white)
green_cell = disp(cell, color.black)

multitrans([ translate(i*BCELL,j*BCELL) for i in range(8) for j in range(8) if (i+j)%2==0 ])(red_cell)
multitrans([ translate(i*BCELL,j*BCELL) for i in range(8) for j in range(8) if (i+j)%2==1 ])(green_cell)

def ctrans(x,y):
	return translate(
		-BSIDE/2 + BCELL/2 + BCELL * x,
		-BSIDE/2 + BCELL/2 + BCELL * y,
		HEIGHT) 

knight00 = disp(zencad.internal_models.knight()).transform(ctrans(0, 1))
knight01 = disp(zencad.internal_models.knight()).transform(ctrans(0, 6))
knight10 = disp(zencad.internal_models.knight()).transform(ctrans(7, 1))
knight11 = disp(zencad.internal_models.knight()).transform(ctrans(7, 6))


show()