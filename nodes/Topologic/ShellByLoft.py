import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology

from . import Replication, ShellByFaces

def processItem(item):
	wires, tolerance = item
	faces = []
	for i in range(len(wires)-1):
		wire1 = wires[i]
		wire2 = wires[i+1]
		if wire1.Type() < topologic.Edge.Type() or wire2.Type() < topologic.Edge.Type():
			raise Exception("Shell.ByLoft - Error: the input topology is not the correct type.")
		if wire1.Type() == topologic.Edge.Type():
			w1_edges = [wire1]
		else:
			w1_edges = []
			_ = wire1.Edges(None, w1_edges)
		if wire2.Type() == topologic.Edge.Type():
			w2_edges = [wire2]
		else:
			w2_edges = []
			_ = wire2.Edges(None, w2_edges)
		if len(w1_edges) != len(w2_edges):
			raise Exception("Shell.ByLoft - Error: The two wires do not have the same number of edges.")
		for j in range (len(w1_edges)):
			e1 = w1_edges[j]
			e2 = w2_edges[j]
			e3 = None
			e4 = None
			try:
				e3 = topologic.Edge.ByStartVertexEndVertex(e1.StartVertex(), e2.StartVertex())
			except:
				e4 = topologic.Edge.ByStartVertexEndVertex(e1.EndVertex(), e2.EndVertex())
				faces.append(topologic.Face.ByExternalBoundary(topologic.Wire.ByEdges([e1, e2, e4])))
			try:
				e4 = topologic.Edge.ByStartVertexEndVertex(e1.EndVertex(), e2.EndVertex())
			except:
				e3 = topologic.Edge.ByStartVertexEndVertex(e1.StartVertex(), e2.StartVertex())
				faces.append(topologic.Face.ByExternalBoundary(topologic.Wire.ByEdges([e1, e2, e3])))
			if e3 and e4:
				e5 = topologic.Edge.ByStartVertexEndVertex(e1.StartVertex(), e2.EndVertex())
				faces.append(topologic.Face.ByExternalBoundary(topologic.Wire.ByEdges([e1, e5, e4])))
				faces.append(topologic.Face.ByExternalBoundary(topologic.Wire.ByEdges([e2, e5, e3])))
	return ShellByFaces.processItem(faces, tolerance)

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvShellByLoft(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Shell by lofting through the input Wires. The Wires must be open, non-branching, have the same edge orientation, have the same number of edges, and ordered
	"""
	bl_idname = 'SvShellByLoft'
	bl_label = 'Shell.ByLoft'
	Tolerance: FloatProperty(name="Tolerance",  default=0.0001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wires')
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name='Tolerance'
		self.outputs.new('SvStringsSocket', 'Shell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		wiresList = self.inputs['Wires'].sv_get(deepcopy=False)
		if not isinstance(wiresList[0], list):
			wiresList = [wiresList]
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		toleranceList = Replication.flatten(toleranceList)
		inputs = [wiresList, toleranceList]
		if ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(Replication.interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Shell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvShellByLoft)

def unregister():
	bpy.utils.unregister_class(SvShellByLoft)
