import pybullet as p
import time
import pybullet_data

from zencad.libs.obj_writer import write_as_obj_wavefront

import zencad
import zencad.lazifier

from zencad import *

from pybullet import JOINT_REVOLUTE, JOINT_PRISMATIC, JOINT_SPHERICAL, JOINT_FIXED

@zencad.lazifier.lazy.file_creator("outpath")
def volumed_collision_do(model, inpath, outpath, logpath, alpha=0.05, resolution=100000):			
	p.vhacd(inpath, outpath, logpath, 
		alpha = 0.0005,
		resolution=10000) 
	#	convexhullApproximation=0,
	#	mode = 0,
	#	convexhullDownsampling=16,
	#	planeDownsampling=16,
	#	depth=32,
	#	beta = 0.0005,
	#	gamma= 0.0005 )

def volumed_collision(model, alpha=0.05, resolution=100000):
	inpath = os.path.join(zencad.lazifier.lazy.cache.tmpdir(), model.__lazyhexhash__[12:] + "collision" + ".obj")
	outpath = os.path.join(zencad.lazifier.lazy.cache.tmpdir(), model.__lazyhexhash__[12:] + "collision.vhacd" + ".obj")
	logpath = os.path.join(zencad.lazifier.lazy.cache.tmpdir(), model.__lazyhexhash__[12:] + "collision.log" + ".txt")
	
	nodes, triangles = zencad.triangulate(model, 0.01)
	write_as_obj_wavefront(inpath, nodes, triangles)
	volumed_collision_do(model, inpath, outpath, logpath, alpha, resolution)
	return outpath

def make_mesh(model):
	nodes, triangles = zencad.triangulate(model, 0.01)
	meshpath = os.path.join(zencad.lazifier.lazy.cache.tmpdir(), model.__lazyhexhash__[12:] + ".obj")
	write_as_obj_wavefront(meshpath, nodes, triangles)
	return meshpath

def evaluate_shape_inertia(model, mass=None):
	if mass is None:
		mass = model.mass()
		inertia_diagonal = model.principal_inertia_moments()
	else:
		mass = mass
		measmass = model.mass()
		inertia_diagonal = [ m/measmass*mass for m in model.principal_inertia_moments() ]

	inertia_axes = model.principal_inertia_axes()

	res = inertia_axes[2].cross(inertia_axes[0])
	res = res.dot(inertia_axes[1])
	
	if res >= 0:
		inertia_diagonal = inertia_diagonal[0], inertia_diagonal[1], inertia_diagonal[2]
		inertia_frame = transformation(point3(0,0,0), inertia_axes[0], inertia_axes[2])
		inertia_frame = translate(*model.center()) * inertia_frame
	else:
		inertia_diagonal = inertia_diagonal[2], inertia_diagonal[1], inertia_diagonal[0]
		inertia_frame = transformation(point3(0,0,0), inertia_axes[2], inertia_axes[0])
		inertia_frame = translate(*model.center()) * inertia_frame

	return mass, inertia_frame, inertia_diagonal

class pybullet_shape_bind:
	def __init__(self, model, collision, location=zencad.nulltrans(), mass=None, 
		link_models=[],
		link_collisions=[],
		link_locations=[],
		link_parents=[],
		link_axes=[],
		link_joint_types=[]
	):
		if model:
			self.model = evalcache.unlazy_if_need(model)
			self.collision = evalcache.unlazy_if_need(collision)
	
			if isinstance(self.model, pyservoce.Shape):
				self.mass, self.inertia_frame, self.inertia_diagonal = evaluate_shape_inertia(self.model, mass)
				self.meshpath = make_mesh(model)
			else:
				raise Exception("unresolved model type")
	
			if isinstance(self.collision, pyservoce.Shape):
				self.meshpath2 = make_mesh(model)
			elif isinstance(self.collision, str):
				self.meshpath2 = collision
			else:
				raise Exception("unresolved model type")

			self.visualShapeId = p.createVisualShape(shapeType=p.GEOM_MESH, fileName=self.meshpath)
			self.collisionShapeId = p.createCollisionShape(shapeType=p.GEOM_MESH, fileName=self.meshpath2)
		else:
			self.model=None
			self.mass = None
			self.collisionShapeId=None
			self.visualShapeId=None
			self.inertia_frame=nulltrans()

	
		self.link_locations = link_locations
		self.link_visual_paths = []
		self.link_collision_paths = []
		self.link_mass = []
		self.link_inertia_frame = []
		self.link_inertia_diagonal = []

		self.link_models = [ evalcache.unlazy_if_need(l) for l in link_models ]

		if len(link_collisions) != 0:
			self.link_collisions = [ evalcache.unlazy_if_need(l) for l in link_collisions ]
		else:
			self.link_collisions= self.link_models
			link_collisions= link_models

		for i in range(len(link_models)):
			if isinstance(self.link_models[i], pyservoce.Shape):
				lmass, linertia_frame, linertia_diagonal = evaluate_shape_inertia(self.link_models[i], None)
				self.link_mass.append(lmass)
				self.link_inertia_frame.append(linertia_frame)
				self.link_inertia_diagonal.append(linertia_diagonal)
				self.link_visual_paths.append(p.createVisualShape(shapeType=p.GEOM_MESH, fileName=make_mesh(link_models[i])))
			else:
				raise Exception("unresolved model type")
	
			if isinstance(self.link_collisions[i], pyservoce.Shape):
				self.link_collision_paths.append(p.createCollisionShape(shapeType=p.GEOM_MESH, fileName=make_mesh(link_collisions[i])))
			elif isinstance(collision, str):
				self.link_collision_paths.append(collision)
			else:
				raise Exception("unresolved model type")

		if model:
			self.boxId = p.createMultiBody(
				baseMass=self.mass,
				baseCollisionShapeIndex=self.collisionShapeId,
				baseVisualShapeIndex=self.visualShapeId,
				basePosition = location.translation(),
				baseOrientation = location.rotation(),
				baseInertialFramePosition = self.inertia_frame.translation(),
				baseInertialFrameOrientation = self.inertia_frame.rotation(),
	
				linkVisualShapeIndices = self.link_visual_paths,
				linkCollisionShapeIndices = self.link_collision_paths,
				linkMasses = self.link_mass,
				linkPositions = [ p.translation() for p in self.link_locations ],
				linkOrientations = [ p.rotation() for p in self.link_locations ],
				linkInertialFramePositions = [ p.translation() for p in self.link_inertia_frame ],
				linkInertialFrameOrientations = [ p.rotation() for p in self.link_inertia_frame ],
				linkParentIndices = link_parents,
				linkJointTypes=[p.JOINT_REVOLUTE] * len(link_models),
				linkJointAxis=[0] * len(link_models)
			)
		else:
			self.boxId = p.createMultiBody(	
				baseMass=1e-10,
				basePosition = location.translation(),
				baseOrientation = location.rotation(),
				linkVisualShapeIndices = self.link_visual_paths,
				linkCollisionShapeIndices = self.link_collision_paths,
				linkMasses = self.link_mass,
				linkPositions = [ p.translation() for p in self.link_locations ],
				linkOrientations = [ p.rotation() for p in self.link_locations ],
				linkInertialFramePositions = [ p.translation() for p in self.link_inertia_frame ],
				linkInertialFrameOrientations = [ p.rotation() for p in self.link_inertia_frame ],
				linkParentIndices = link_parents,
				linkJointTypes=link_joint_types,
				linkJointAxis=link_axes
			)


		if model:
			p.changeDynamics(self.boxId, -1, 
				linearDamping=0, 
				angularDamping=0.005,
				#spinningFriction=0.001,
				#rollingFriction=0.001,
				localInertiaDiagonal = self.inertia_diagonal,
				maxJointVelocity=1e10)

		for i in range(len(link_models)):
			p.changeDynamics(self.boxId, i, 
				linearDamping=0, 
				angularDamping=0.005,
				#spinningFriction=0.001,
				#rollingFriction=0.001,
				localInertiaDiagonal = self.link_inertia_diagonal[i],
				maxJointVelocity=1e10)



	def bind_to_scene(self, scene, color=zencad.default_color):
		if self.model:
			self.ctr = disp(self.model, scene=scene, color=color)
		self.link_ctr = []
		for m in self.link_models:
			self.link_ctr.append(disp(m, scene=scene, color=color))
		return self

	def update(self):
		if self.model:
			cubePos, cubeOrn = p.getBasePositionAndOrientation(self.boxId)
			rot = pyservoce.quaternion(*cubeOrn).to_transformation()
			
			tr = (translate(*cubePos) * rot 
			* self.inertia_frame.rotation().to_transformation().inverse() 
			* translate(vector3(self.inertia_frame.translation())).inverse()
			)
			
			self.ctr.relocate(tr)

		info = p.getLinkStates(self.boxId, range(len(self.link_models)))
		#print(info)
		#print(len(info))
		#print(len(info[0]))
		#exit()

		for i in range(len(info)):
			rot = pyservoce.quaternion(*info[i][1]).to_transformation()
			
			tr = (translate(*info[i][0]) * rot 
			* self.link_inertia_frame[i].rotation().to_transformation().inverse() 
			* translate(vector3(self.link_inertia_frame[i].translation())).inverse()
			)
			
			self.link_ctr[i].relocate(tr)


	def velocity(self):
		spd = p.getBaseVelocity(self.boxId)
		return vector3(spd[0]), vector3(spd[1])

	def set_velocity(self, lin=(0,0,0), ang=(0,0,0)):
		p.resetBaseVelocity(self.boxId, lin, ang)


class pybullet_simulation:
	def __init__(self, gravity=(0,0,0), plane=True, gui=False):
		if not gui:
			self.client = p.connect(p.DIRECT)
		else:
			self.client = p.connect(p.GUI)
			
		p.setRealTimeSimulation(1) 
		#p.setTimeStep(0.01) 
		self.binds = []
		self.set_gravity(gravity)

		self.library_included = False

		self.plane = plane
		if self.plane:
			idx = p.createCollisionShape(p.GEOM_PLANE)
			self.plane_index = p.createMultiBody(
				baseMass=0,	
				baseCollisionShapeIndex=idx)
			
	def set_plane_friction(self, koeff):
		if self.plane:
			p.changeDynamics(self.plane_index, -1, 
				#lateralFriction = koeff
				#spinningFriction = koeff
				#rollingFriction = koeff
			)

	def set_gravity(self, x, y=None, z=None):
		v = zencad.util.vector3(x,y,z)
		p.setGravity(*v)
		
	def add_body(self, 
		model=None, 
		location=nulltrans(),
		mass=None,
		collision=None, 
		scene=zencad.default_scene(), color=zencad.default_color):

		if collision is None:
			collision = model

		bind = pybullet_shape_bind(
			model=model, 
			collision=collision,
			location=location,
			mass=mass).bind_to_scene(scene,color)

		self.binds.append(bind)
		return bind

	def add_multibody(self, 
		base_model=None, 
		base_collision=None,
		base_location=nulltrans(),

		link_models=[],
		link_collisions=[],
		link_parents=[],
		link_locations=[], 
		link_axes=[], 
		link_joint_types=[],
		scene=zencad.default_scene(), color=zencad.default_color
		):

		if base_collision is None:
			base_collision = base_model

		bind = pybullet_shape_bind(
			model=base_model, 
			collision=base_collision,
			location=base_location,
		
			link_models=link_models,
			link_collisions=link_collisions,
			link_parents=link_parents,
			link_locations=link_locations,
			link_axes=link_axes,
			link_joint_types=link_joint_types
		).bind_to_scene(scene,color)

		self.binds.append(bind)
		return bind

	def include_library(self):
		if self.library_included is False:
			self.library_included = True
			p.setAdditionalSearchPath(pybullet_data.getDataPath())

	def step(self):
		for o in self.binds:
			o.update()
		p.stepSimulation()
