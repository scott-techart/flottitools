import pymel.core as pm

from flottitools.mayafbx import FbxExportOptions, export_fbx
import flottitools.utils.ioutils as ioutils
import flottitools.utils.meshutils as meshutils
import flottitools.utils.pathutils as pathutils
import flottitools.utils.transformutils as xformutils
import flottitools.utils.selectionutils as selutils


def export_selected_meshes_with_prompt():
    sel = pm.selected()
    if not sel:
        pm.error('Nothing selected. Select static meshes to export.')
        return
    meshes = meshutils.get_meshes_in_list(sel)
    export_paths = export_static_meshes(meshes)


def export_static_meshes(meshes):
    scene_path = pathutils.get_scene_path()
    dir_path = scene_path.parents[1]
    if not scene_path.parent.name.lower() == '_source':
        dir_path = scene_path.parent
    
    options = FbxExportOptions()
    export_paths = []
    with selutils.preserve_selection():
        for mesh in meshes:
            initial_pos = xformutils.get_worldspace_vector(mesh)
            mesh.setTranslation((0, 0, 0), space='world')
            name = '{}.fbx'.format(mesh.nodeName(stripNamespace=True))
            export_path = dir_path.joinpath(name)
            ioutils.ensure_file_is_writable(export_path)
            pm.select(mesh, replace=True)
            export_fbx(export_path, options, selection=True)
            print('Success! Exported {0} to {1}'.format(name, export_path))
            export_paths.append(export_path)
            mesh.setTranslation(initial_pos, space='world')
    return export_paths
