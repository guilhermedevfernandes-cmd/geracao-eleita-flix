import bpy
import json
import sys
from pathlib import Path


def limpar_cena():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for bloco in (bpy.data.actions, bpy.data.armatures, bpy.data.meshes, bpy.data.materials):
        for item in list(bloco):
            if item.users == 0:
                bloco.remove(item)


def auditar(caminho):
    limpar_cena()
    bpy.ops.import_scene.gltf(filepath=str(caminho))

    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

    pontos = []
    for obj in meshes:
        pontos.extend(obj.matrix_world @ v.co for v in obj.data.vertices)

    if pontos:
        mins = [min(p[i] for p in pontos) for i in range(3)]
        maxs = [max(p[i] for p in pontos) for i in range(3)]
    else:
        mins = maxs = [0, 0, 0]

    return {
        "arquivo": caminho.name,
        "objetos": [(obj.name, obj.type) for obj in bpy.context.scene.objects],
        "bbox_min": [round(v, 5) for v in mins],
        "bbox_max": [round(v, 5) for v in maxs],
        "armatures": [
            {
                "nome": arm.name,
                "rotacao": [round(v, 5) for v in arm.rotation_euler],
                "escala": [round(v, 5) for v in arm.scale],
                "bones": [
                    {
                        "nome": bone.name,
                        "pai": bone.parent.name if bone.parent else None,
                        "head": [round(v, 5) for v in bone.head_local],
                        "tail": [round(v, 5) for v in bone.tail_local],
                    }
                    for bone in arm.data.bones
                ],
            }
            for arm in armatures
        ],
        "actions": [
            {
                "nome": action.name,
                "frame_range": [round(v, 3) for v in action.frame_range],
                "slots": len(action.slots) if hasattr(action, "slots") else None,
            }
            for action in bpy.data.actions
        ],
        "meshes": [
            {
                "nome": obj.name,
                "vertices": len(obj.data.vertices),
                "grupos": [grupo.name for grupo in obj.vertex_groups],
                "modificadores": [(mod.name, mod.type) for mod in obj.modifiers],
            }
            for obj in meshes
        ],
    }


argumentos = [Path(item) for item in sys.argv[sys.argv.index("--") + 1 :]]
resultado = [auditar(caminho) for caminho in argumentos]
print("AUDITORIA_JSON=" + json.dumps(resultado, ensure_ascii=False))
