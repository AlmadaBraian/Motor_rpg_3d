class LowPolyAsset:
    def __init__(self, name):
        self.name = name
        self.cubes = []

        self.tex_top = None
        self.tex_side = None

        self.mode = "voxel"
        self.mesh_vertices = []
        self.mesh_faces = []
        self.mesh_uvs = []
        self.mesh_tex = None

        self.mesh_texcoords = []
        self.mesh_face_uvs = []
        self.mesh_material = None
        self.mesh_face_materials = []
        self.mesh_material_textures = {}