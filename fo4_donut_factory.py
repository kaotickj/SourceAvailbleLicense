bl_info = {
    "name": "FO4 Donut Factory",
    "author": "Kaotick Jay",
    "version": (1, 9),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > FO4 Tools",
    "description": "FO4 WIP-aware donut generator with mod-relative texture paths",
    "category": "Object",
}


import bpy
import os

from pathlib import Path
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper


# =========================================================
# FO4 PATHS
# =========================================================

FO4_BASE_DIR = (
    r"C:\Program Files (x86)\Steam\steamapps\common\Fallout 4\Data"
)

FO4_MOD_NAME = "MTP_SlocumsJoe"


# Blender working locations

FO4_INPUT_DIR = os.path.join(
    FO4_BASE_DIR,
    "WIPs",
    "input"
)


FO4_MATERIAL_DIR = os.path.join(
    FO4_BASE_DIR,
    "WIPs",
    "materials"
)


# Actual mod output

FO4_OUTPUT_DIR = os.path.join(
    FO4_BASE_DIR,
    "Meshes",
    FO4_MOD_NAME
)


# Path written into NIF - FIXED: Capital T for Textures

FO4_TEXTURE_DIR = (
    "Textures\\"
    + FO4_MOD_NAME
)


# =========================================================
# VARIANTS
# =========================================================

DONUT_TYPES = [
    ("TARBERRY", "Tarberry Frosted", ""),
    ("PINK", "Pink Frosted", ""),
    ("PINK_SPRINKLES", "Pink w/ Sprinkles", ""),
    ("APPLE_FILLED", "Apple Filled", ""),
    ("PATRIOT", "Patriotic", ""),
    ("CHOCOLATE", "Chocolate", ""),
    ("ATOMICORANGE", "Atomic Orange", ""),
    ("MAPLE", "Maple", "")
]


# =========================================================
# DDS DISCOVERY
# =========================================================

def get_dds_files(self, context):

    if not os.path.exists(FO4_MATERIAL_DIR):
        return [
            ("NONE", "Missing WIP materials folder", "")
        ]


    files = []

    try:

        for f in sorted(
            os.listdir(FO4_MATERIAL_DIR)
        ):

            if f.lower().endswith("_d.dds"):

                full = os.path.join(
                    FO4_MATERIAL_DIR,
                    f
                )

                files.append(
                    (
                        full,
                        f,
                        "Diffuse texture"
                    )
                )


    except Exception as e:

        print(
            "[FO4] DDS scan error:",
            e
        )

        return [
            ("NONE", "Scan error", "")
        ]


    if not files:

        return [
            ("NONE", "No DDS files found", "")
        ]


    return files



# =========================================================
# CORE
# =========================================================

def clear_scene():

    bpy.ops.object.select_all(
        action='SELECT'
    )

    bpy.ops.object.delete(
        use_global=False
    )



def import_nif(path):

    bpy.ops.import_scene.pynifly(
        filepath=path
    )



def export_nif(path):

    bpy.ops.export_scene.pynifly(
        filepath=path
    )



# =========================================================
# MATERIAL BUILDER
# =========================================================

def build_material(
        variant,
        dds_path):


    mat = bpy.data.materials.new(
        name=f"Donut_{variant}"
    )

    mat.use_nodes = True


    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()


    output = nodes.new(
        "ShaderNodeOutputMaterial"
    )

    bsdf = nodes.new(
        "ShaderNodeBsdfPrincipled"
    )

    tex = nodes.new(
        "ShaderNodeTexImage"
    )


    if dds_path:

        try:

            tex.image = bpy.data.images.load(
                dds_path
            )

        except Exception as e:

            print(
                "[FO4] DDS load failed:",
                e
            )


    links.new(
        tex.outputs["Color"],
        bsdf.inputs["Base Color"]
    )

    links.new(
        bsdf.outputs["BSDF"],
        output.inputs["Surface"]
    )


    return mat



def apply_material(mat):

    for obj in bpy.context.scene.objects:

        if obj.type == "MESH":

            obj.data.materials.clear()

            obj.data.materials.append(
                mat
            )



# =========================================================
# TEXTURE PATH FIX
# =========================================================

def fix_fo4_texture_paths():
    """
    Rewrite texture paths to be relative to Data folder (Fallout 4 format).
    Textures should already exist in Data\Textures\[mod_name]\
    """
    texture_dir = FO4_TEXTURE_DIR

    if not texture_dir.endswith("\\"):
        texture_dir += "\\"

    for image in list(bpy.data.images):
        if not image:
            continue

        if not image.filepath:
            continue

        if not image.filepath.lower().endswith(".dds"):
            continue

        filename = os.path.basename(
            image.filepath
        )

        # Path relative to Data folder (what Fallout 4 reads)
        game_path = (
            texture_dir
            + filename
        )

        game_path = game_path.replace(
            "/",
            "\\"
        )

        print(
            "[FO4] Texture path:",
            game_path
        )

        image.filepath = game_path

        image.filepath_raw = game_path

        # PyNifly fallback
        image["fo4_texture_path"] = game_path



# =========================================================
# BUILD
# =========================================================

def build_variant(
        input_path,
        output_path,
        variant,
        dds_path):


    clear_scene()


    import_nif(
        input_path
    )


    mat = build_material(
        variant,
        dds_path
    )


    apply_material(
        mat
    )


    fix_fo4_texture_paths()


    export_nif(
        output_path
    )



# =========================================================
# OPERATOR
# =========================================================

class DONUT_OT_picker(
        bpy.types.Operator,
        ImportHelper):


    bl_idname = "donut.pick"

    bl_label = "Generate Donuts"


    filename_ext = ".nif"


    filter_glob: StringProperty(
        default="*.nif",
        options={'HIDDEN'}
    )


    output_dir: StringProperty(
        name="Output Directory",
        default=FO4_OUTPUT_DIR,
        subtype='DIR_PATH'
    )


    variant: EnumProperty(
        items=DONUT_TYPES
    )


    batch: BoolProperty(
        default=False
    )


    dds_override: EnumProperty(
        name="DDS Texture",
        items=get_dds_files
    )



    def invoke(
            self,
            context,
            event):

        self.filepath = FO4_INPUT_DIR

        context.window_manager.fileselect_add(
            self
        )

        return {'RUNNING_MODAL'}



    def execute(
            self,
            context):


        out_folder = Path(
            self.output_dir
        )


        out_folder.mkdir(
            parents=True,
            exist_ok=True
        )


        dds_path = None


        if self.dds_override != "NONE":

            dds_path = self.dds_override



        def run(v):


            out_path = (
                out_folder
                /
                f"donut_{v.lower()}.nif"
            )


            build_variant(
                self.filepath,
                str(out_path),
                v,
                dds_path
            )


            self.report(
                {'INFO'},
                f"Exported {out_path}"
            )



        if self.batch:

            for v in DONUT_TYPES:

                run(v[0])


        else:

            run(
                self.variant
            )


        return {'FINISHED'}



# =========================================================
# UI
# =========================================================

class DONUT_PT_panel(
        bpy.types.Panel):


    bl_label = "FO4 Donut Factory"

    bl_idname = "DONUT_PT_panel"

    bl_space_type = 'VIEW_3D'

    bl_region_type = 'UI'

    bl_category = "FO4 Tools"



    def draw(
            self,
            context):

        self.layout.operator(
            "donut.pick",
            text="Generate Donuts"
        )



# =========================================================
# REGISTER
# =========================================================

def register():

    bpy.utils.register_class(
        DONUT_OT_picker
    )

    bpy.utils.register_class(
        DONUT_PT_panel
    )



def unregister():

    bpy.utils.unregister_class(
        DONUT_OT_picker
    )

    bpy.utils.unregister_class(
        DONUT_PT_panel
    )



if __name__ == "__main__":

    register()
