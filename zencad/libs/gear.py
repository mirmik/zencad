from zencad import *

def gear_profile(r, r_zub, N_zub, x_zub, paz_deep=None, n_tochek=20):
	"""
		r:         радиус без зуба
		r_zub:     радиус вместе с зубом
		N_zub:     количество зубов
		x_zub:     толщина конца зуба
		n_tochek:  количество точек в апроксимации эвольвенты
	"""

	# Максимальная длинна эвольвенты
	alfa = math.sqrt(r_zub**2 - r**2)/r
	# Угол дуги окружности, которую занимает эвольвента
	omega = math.asin((r*(math.sin(alfa) - alfa*math.cos(alfa)) )/ r_zub)
	# Угол дуги окружности, которую занимает зуб
	teta = 2*math.pi/N_zub
	# Угол смещения второй грани зуба относительно первой
	ax = 2*math.asin(x_zub/(2*r_zub))
	d =  - 2 * omega - ax
	
	#pnts=[]
	
	wires = []
	abases = []
	bbases = []
	
	for k in range(N_zub):
		apnts = []
		for j in range(0,n_tochek+1):
			a = j*alfa/n_tochek
			# Считаем точки эвольвенты первой грани
			x = r*(math.cos(a) + a*math.sin(a))
			y = r*(math.sin(a) - a*math.cos(a))
			# Добавляем точки первой эвольвенты относительно повернутой системы координат
			apnts.append(point3([
				x*math.cos(-k*teta) + y*math.sin(-k*teta),\
				-x*math.sin(-k*teta)+y*math.cos(-k*teta)
			]))
	
		bpnts = []
		for j in range(n_tochek,0,-1):
			a = j*alfa/n_tochek
			# Считаем точки эвольвенты второй грани
			x = r*(math.cos(a) + a*math.sin(a))
			y = -r*(math.sin(a) - a*math.cos(a))
			# Добавляем точки второй эвольвенты относительно повернутой системы координат
			bpnts.append(point3([
				x*math.cos(-k*teta +d) + y*math.sin(-k*teta+d),\
				-x*math.sin(-k*teta+d)+y*math.cos(-k*teta+d)
			]))
	
		# Создать эвольвентные рёбра зуба
		wires.append(interpolate(apnts))
		wires.append(interpolate(bpnts))

		# Создать рёбро вершины зуба
		wires.append(segment(apnts[-1], bpnts[0]))
		
		# Запомнить точки основания зубьев
		abases.append(apnts[0])
		bbases.append(bpnts[-1])
	
	if paz_deep is None:
		# Добавляем рёбра между основанием зубьев 
		wires.append(segment(abases[0], bbases[-1]))
		for k in range(N_zub - 1):
			wires.append(segment(abases[k+1], bbases[k]))
	
	else:
		spaz = None
		if isinstance(paz_deep, tuple):
			spaz = paz_deep[0]
			paz_deep = paz_deep[1]
		
			scl0 = scale((r_zub-spaz)/r_zub)
			
			abases2 = [ scl0(a) for a in abases ]
			bbases2 = [ scl0(b) for b in bbases ]

			for k in range(N_zub):
				wires.append(segment(abases[k], abases2[k]))
				wires.append(segment(bbases[k], bbases2[k]))	

			abases = abases2
			bbases = bbases2
			scl = scale((r_zub-paz_deep-spaz)/r_zub)
		else:
			scl = scale((r_zub-paz_deep)/r_zub)	

		# Добавляем проточку между основанием зубьев 
		abases2 = [ scl(a) for a in abases ]
		bbases2 = [ scl(b) for b in bbases ]

		wires.append(rounded_polysegment(r=paz_deep, 
			pnts=[abases[0], abases2[0], bbases2[-1], bbases[-1]]))

		for k in range(N_zub-1):
			wires.append(rounded_polysegment(r=paz_deep, 
				pnts=[abases[k+1], abases2[k+1], bbases2[k], bbases[k]]))

	evolv = sew(wires)

	return evolv