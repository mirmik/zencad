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

def evaluate_shape_inertia(model, mass=None, scale_factor=1):
	if mass == 0:
		return 0, nulltrans(), (0,0,0)

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

	mass = mass / scale_factor**3
	inertia_diagonal = [ i / scale_factor**5 for i in inertia_diagonal ]
	inertia_frame = (
		translate((inertia_frame.translation()*(1/scale_factor))) 
		* inertia_frame.rotation().to_transformation())

	#print(mass)
	#print(inertia_diagonal)
	#print(inertia_frame)

	if mass == 0:
		mass = 1e-6

	return mass, inertia_frame, inertia_diagonal

class pybullet_shape_bind:
	def __init__(self, simulation, model, collision, location=zencad.nulltrans(), mass=None, 
		link_models=[],
		link_masses=None,
		link_collisions=[],
		link_locations=[],
		link_parents=[],
		link_axes=[],
		link_joint_types=[],
		interactives=None,
		base_interactive=None
	):
		self.interactives = interactives
		self.base_interactive=base_interactive
		self.simulation = simulation
		SF = self.simulation.scale_factor

		SF_trans = scale(1/SF, center=(0,0,0))
		self.SF_trans = SF_trans
		self.SF_trans_inverse = SF_trans.inverse()
		location = SF_trans * location

		if model:
			self.model = evalcache.unlazy_if_need(model)
			self.collision = evalcache.unlazy_if_need(collision)
	
			if isinstance(self.model, pyservoce.Shape):
				self.mass, self.inertia_frame, self.inertia_diagonal = evaluate_shape_inertia(self.model, mass, scale_factor = self.simulation.scale_factor)
				self.meshpath = make_mesh(model)
			else:
				raise Exception("unresolved model type")
	
			if isinstance(self.collision, pyservoce.Shape):
				self.meshpath2 = make_mesh(model)
			elif isinstance(self.collision, str):
				self.meshpath2 = collision
			else:
				raise Exception("unresolved model type")

			self.visualShapeId = p.createVisualShape(shapeType=p.GEOM_MESH, fileName=self.meshpath, meshScale=[1/SF,1/SF,1/SF])
			self.collisionShapeId = p.createCollisionShape(shapeType=p.GEOM_MESH, fileName=self.meshpath2, meshScale=[1/SF,1/SF,1/SF])
			
		else:
			self.model=None
			self.mass = None
			self.collisionShapeId=None
			self.visualShapeId=None
			self.inertia_frame=nulltrans()

	
		self.link_locations = link_locations
		self.link_visual_paths = []
		self.link_collision_paths = []
		self.link_masses = []
		self.link_inertia_frame = []
		self.link_inertia_diagonal = []

		self.link_locations = [ SF_trans * l for l in link_locations ]

		self.link_models = [ evalcache.unlazy_if_need(l) for l in link_models ]

		if len(link_collisions) != 0:
			self.link_collisions = [ evalcache.unlazy_if_need(l) for l in link_collisions ]
		else:
			self.link_collisions= self.link_models
			link_collisions= link_models

		need_inertia_re = link_masses is not None

		for i in range(len(link_models)):
			if isinstance(self.link_models[i], pyservoce.Shape):
				if not link_collisions[i].is_nullshape():
					koeff = link_masses[i] if need_inertia_re else None
					lmass, linertia_frame, linertia_diagonal = evaluate_shape_inertia(self.link_models[i], koeff, self.simulation.scale_factor)
					self.link_masses.append(lmass)
					self.link_inertia_frame.append(linertia_frame)
					self.link_inertia_diagonal.append(linertia_diagonal)
					self.link_visual_paths.append(p.createVisualShape(shapeType=p.GEOM_MESH, fileName=make_mesh(link_models[i]), meshScale=[1/SF,1/SF,1/SF]))
				else:
					self.link_masses.append(0)
					self.link_inertia_frame.append(nulltrans())
					self.link_inertia_diagonal.append((0,0,0))
					self.link_visual_paths.append(None)
			else:
				raise Exception("unresolved model type")
	
			if isinstance(self.link_collisions[i], pyservoce.Shape):
				if not link_collisions[i].is_nullshape():
					self.link_collision_paths.append(p.createCollisionShape(shapeType=p.GEOM_MESH, fileName=make_mesh(link_collisions[i]), meshScale=[1/SF,1/SF,1/SF]))
				else:
					self.link_collision_paths.append(None)
			elif isinstance(collision, str):
				self.link_collision_paths.append(collision)
			else:
				raise Exception("unresolved model type")

		#scale
		#self.mass = self.mass / self.simulation.scale_factor
		#self.inertia_diagonal = [ v / self.simulation.scale_factor**2 for v in self.inertia_diagonal ]

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
				linkMasses = self.link_masses,
				linkPositions = [ p.translation() for p in self.link_locations ],
				linkOrientations = [ p.rotation() for p in self.link_locations ],
				linkInertialFramePositions = [ p.translation() for p in self.link_inertia_frame ],
				linkInertialFrameOrientations = [ p.rotation() for p in self.link_inertia_frame ],
				linkParentIndices = link_parents,
				linkJointTypes=link_joint_types,
				linkJointAxis=link_axes
			)
		else:
			self.boxId = p.createMultiBody(	
				baseMass=1e-10,
				basePosition = location.translation(),
				baseOrientation = location.rotation(),
				linkVisualShapeIndices = self.link_visual_paths,
				linkCollisionShapeIndices = self.link_collision_paths,
				linkMasses = self.link_masses,
				linkPositions = [ p.translation() for p in self.link_locations ],
				linkOrientations = [ p.rotation() for p in self.link_locations ],
				linkInertialFramePositions = [ p.translation() for p in self.link_inertia_frame ],
				linkInertialFrameOrientations = [ p.rotation() for p in self.link_inertia_frame ],
				linkParentIndices = link_parents,
				linkJointTypes=link_joint_types,
				linkJointAxis=link_axes
			)

		self.index_map = { i: int(p.getJointInfo(self.boxId, i)[1][5:]) - 1 for i in range(len(self.link_models)) }

		#info = p.getLinkStates(self.boxId, range(len(self.link_models)))
		#print()
		#for i in range(len(info)):
		#	print(info[i-1][1])
		#for i in range(len(info)):
		#	print(self.link_locations[i])
		#	print(self.link_inertia_frame[i])
		#exit()

		rollingFriction = 40
		spinningFriction = 0.004
		lateralFriction = 0.004
		anisotropicFriction=0.001
		frictionAnchor = 0
		jointDamping = 0.1
		linearDamping=0.1
		angularDamping=0.1

		contactStiffness = -1
		contactDamping = -1

		if model:
			p.changeDynamics(self.boxId, -1, 
				linearDamping=linearDamping, 
				angularDamping=angularDamping,
				jointDamping=jointDamping,
				#lateralFriction = lateralFriction,
				#spinningFriction=spinningFriction,
				#rollingFriction=rollingFriction,
				#frictionAnchor = frictionAnchor,
				#anisotropicFriction=anisotropicFriction,
				restitution=0,
				contactDamping=contactDamping,
				contactStiffness=contactStiffness,
				localInertiaDiagonal = self.inertia_diagonal,
				maxJointVelocity=10e5)

		for i in range(len(link_models)):
			p.changeDynamics(self.boxId, self.index_map[i], 
				linearDamping=linearDamping, 
				angularDamping=angularDamping,
				jointDamping=jointDamping,
				#lateralFriction = lateralFriction,
				#spinningFriction=spinningFriction,
				#rollingFriction=rollingFriction,
				#frictionAnchor = frictionAnchor,
				#anisotropicFriction=anisotropicFriction,
				restitution=0,
				contactDamping=contactDamping,
				contactStiffness=contactStiffness,
				#spinningFriction=0.001,
				#rollingFriction=rollingFriction,
				localInertiaDiagonal = self.link_inertia_diagonal[i],
				#localInertiaDiagonal = self.link_inertia_diagonal[i],
				maxJointVelocity=10e5)



	def bind_to_scene(self, scene, color=zencad.default_color):
		if self.base_interactive:
			self.ctr=disp(self.base_interactive)
			#self.link_ctr = []
			for u in self.interactives: 
				if isinstance(u, zencad.assemble.kinematic_unit):
					u.simulation_start_pose = u.coord
			#	self.link_ctr.append(self.interactives[i])

		else:
			if self.model:
				self.ctr = disp(self.model, scene=scene, color=color)
			self.link_ctr = []
			for m in self.link_models:
				self.link_ctr.append(disp(m, scene=scene, color=color))
			self.update()
			
		return self

	def update(self):
		self_inertia_frame = self.inertia_frame# * self.SF_trans_inverse

		if self.model:
			cubePos, cubeOrn = p.getBasePositionAndOrientation(self.boxId)
			rot = pyservoce.quaternion(*cubeOrn).to_transformation()
			
			tr = (translate(*cubePos) * rot 
			* self_inertia_frame.rotation().to_transformation().inverse() 
			* translate(vector3(self_inertia_frame.translation())).inverse()
			)
			
			#self.ctr.relocate(self.SF_trans_inverse * tr)
			tr = translate(tr.translation() * self.simulation.scale_factor) * tr.rotation().to_transformation()
			self.ctr.relocate(tr)

		if self.base_interactive is None:
			info = p.getLinkStates(self.boxId, range(len(self.link_models)))
	
			for i in range(len(info)):
				info_node = info[self.index_map[i]]
				rot = pyservoce.quaternion(*info_node[1]).to_transformation()
				
				tr = (translate(*info_node[0]) * rot 
				* self.link_inertia_frame[i].rotation().to_transformation().inverse() 
				* translate(vector3(self.link_inertia_frame[i].translation())).inverse()
				)
				
				tr = translate(tr.translation() * self.simulation.scale_factor) * tr.rotation().to_transformation()
				self.link_ctr[i].relocate(tr)

		else:
			def set_kinematic_pose(u):
				if isinstance(u, zencad.assemble.kinematic_unit):
					info = p.getJointState(u.pybullet_base.boxId, u.simulation_hint2)
					pose=info[0]
					u.set_coord(pose + u.simulation_start_pose)
			zencad.assemble.for_each_unit(self.base_interactive, set_kinematic_pose)

			self.base_interactive.location_update()


	def velocity(self):
		spd = p.getBaseVelocity(self.boxId)
		return vector3(spd[0]), vector3(spd[1])

	def set_velocity(self, lin=(0,0,0), ang=(0,0,0)):
		lin = [ x/self.simulation.scale_factor for x in lin ]  
		p.resetBaseVelocity(self.boxId, lin, ang)


class simulation:
	def __init__(self, scale_factor=1, gravity=(0,0,0), plane=False, gui=False, 
			time_step=1/240, substeps=2):
		self.scale_factor = scale_factor

		if not gui:
			self.client = p.connect(p.DIRECT)
		else:
			self.client = p.connect(p.GUI)

		p.setPhysicsEngineParameter(
			numSubSteps=substeps,
			contactSlop=0,
			useSplitImpulse=True)
			
		if time_step:
			p.setTimeStep(time_step) 
		self.binds = []
		self.set_gravity(*gravity)

		self.library_included = False

		self.plane = plane
		if self.plane:
			idx = p.createCollisionShape(p.GEOM_PLANE)
			self.plane_index = p.createMultiBody(
				baseMass=0,	
				baseCollisionShapeIndex=idx)
			self.set_plane_friction()
			
	def set_plane_friction(self):
		if self.plane:
			p.changeDynamics(self.plane_index, -1, 
				#linearDamping=0.01, 
				#angularDamping=0.005#,
				#lateralFriction = 0.0001,
				#contactDamping=0.0001,
				#contactStiffness=0.0001
				#spinningFriction=0.001,
				#rollingFriction=0.001)
			)

	def volumed_collision(self, model):
		return volumed_collision(zencad.scale(1/self.scale_factor)(model))

	def set_gravity(self, x, y=None, z=None):
		v = zencad.util.vector3(x,y,z)
		#v = v * self.scale_factor
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
			mass=mass,
			simulation=self).bind_to_scene(scene,color)

		self.binds.append(bind)
		return bind

	def add_multibody(self, 
		base_model=None, 
		base_collision=None,
		base_location=nulltrans(),
		base_mass=None,

		link_models=[],
		link_masses = None,
		link_collisions=[],
		link_parents=[],
		link_locations=[], 
		link_axes=[], 
		link_joint_types=[],
		interactives=None,
		base_interactive=None,
		scene=zencad.default_scene(), color=zencad.default_color
		):

		if base_collision is None:
			base_collision = base_model

		bind = pybullet_shape_bind(
			model=base_model, 
			collision=base_collision,
			location=base_location,
			mass=base_mass,
		
			link_models=link_models,
			link_masses=link_masses,
			link_collisions=link_collisions,
			link_parents=link_parents,
			link_locations=link_locations,
			link_axes=link_axes,
			link_joint_types=link_joint_types,
			simulation=self,
			interactives=interactives,
			base_interactive=base_interactive
		).bind_to_scene(scene,color)

		self.binds.append(bind)
		return bind

	def include_library(self):
		if self.library_included is False:
			self.library_included = True
			p.setAdditionalSearchPath(pybullet_data.getDataPath())

	def step(self):
		p.stepSimulation()
		for o in self.binds:
			o.update()

	def _bind_assemble_tasks(self, u, tasks, parent_index, pjoint, paxis, root):
		class t:
			def __init__(self, parent, model, location,
					joint_type, joint_axis, parent_index):
				self.parent = parent
				self.model = model
				self.location = location
				self.joint_type = joint_type
				self.joint_axis = joint_axis
				self.parent_index = parent_index

		ubody = u.union_shape()
		if ubody.is_nullshape() and len(u.childs) == 0:
			raise Exception("kintranslator: finite node cannot be nullshape")

		tasks.append(t(u, ubody, u.location, pjoint, paxis, parent_index))
		current_index = len(tasks)

		u.current_index = current_index

		for c in u.childs:
			pjoint=p.JOINT_FIXED
			paxis=(0,0,0)

			if isinstance(u, zencad.assemble.rotator):
				pjoint=p.JOINT_REVOLUTE
				paxis=vector3(u.axis) #u.location(vector3(u.axis))

			index = self._bind_assemble_tasks(c, tasks, current_index, 
				pjoint=pjoint, paxis=paxis,
				root=root)

			if isinstance(u, zencad.assemble.rotator):
				u.simulation_hint = index

		return current_index
	
	def _prepare_motors(self, u, ret):
		if isinstance(u, zencad.assemble.rotator):
			p.setJointMotorControl2(ret.boxId, 
				ret.index_map[u.simulation_hint-1], 
				p.VELOCITY_CONTROL, 
				targetVelocity=0, force=0)

			u.simulation_hint2 = ret.index_map[u.simulation_hint - 1]
			u.pybullet_base=ret

		u.current_index2 = ret.index_map[u.current_index - 1]

		for c in u.childs:
			self._prepare_motors(c, ret)

	def add_assemble(self, root, fixed_base=False): 
		childs = root.childs
		tasks = []

		root.location_update()
		ubody = root.union_shape()	

		for c in root.childs:
			self._bind_assemble_tasks(c, tasks, parent_index=0, 
				pjoint=p.JOINT_FIXED, paxis=(0,0,0), root=root)


		link_models = [ t.model for t in tasks ]
		link_locations = [ t.location for t in tasks ]
		joint_types = [ t.joint_type for t in tasks ]
		joint_axis = [ t.joint_axis for t in tasks ]
		joint_parents = [ t.parent_index for t in tasks ]
		interactives = [ t.parent for t in tasks ]
		base_interactive = root

		#print(joint_parents)

		mass = None
		if fixed_base:
			mass = 0


		ret = self.add_multibody(
			base_model=ubody, 
			base_location=root.location,
			base_mass =mass,

			link_models = link_models,
			link_locations = link_locations,

			link_joint_types = joint_types,
			link_axes = joint_axis,
			link_parents = joint_parents,

			interactives = interactives,
			base_interactive=base_interactive)

		for c in root.childs:
			self._prepare_motors(c, ret)

		ret.links_number = len(link_models)
		return ret

	def set_force(self, base, hint, force):
		p.setJointMotorControl2(bodyUniqueId=base.boxId, 
			jointIndex=base.index_map[hint-1],
			controlMode=p.TORQUE_CONTROL,
			force =force)
