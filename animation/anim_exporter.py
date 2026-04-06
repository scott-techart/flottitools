import os.path
import json
from pathlib import Path

import pymel.core as pm

import flottitools.path_consts as path_consts
import flottitools.utils.ioutils as ioutils
import flottitools.utils.pathutils as pathutils
import flottitools.utils.rigutils as rigutils
import flottitools.utils.selectionutils as selutils
import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.skinutils as skinutils


RIG_REF_INVALID = 'Invalid Rig Reference'
ANIM_SEQUENCE_PREFIX = 'AS_'
METADATA_PREFIX = 'MD_'
CLIP_DEFAULT_NAME = 'Clip'
CLIP_RIG_PATH = 'rig_ref_abs_path'
CLIP_RIG_NAMESPACE = 'rig_ref_namespace'
CLIP_EXPORT_PATH = 'export_path'
CLIP_FRAME_END = 'frame_end'
CLIP_FRAME_START = 'frame_start'
CLIP_NAME = 'clip_name'
EXTENSION_FBX = '.fbx'
EXTENSION_METADATA = '.rad'
FILE_FILTER_METADATA = 'Animation Asset Data (*{0})'.format(EXTENSION_METADATA)
FILE_FILTER_FBX = 'Fbx (*{0})'.format(EXTENSION_FBX)


def export_animation(export_fbx_path, frame_start=None, frame_end=None, rig_reference=None):
    if frame_start is None:
        frame_start = int(pm.playbackOptions(minTime=True, q=True))
    if frame_end is None:
        frame_end = int(pm.playbackOptions(maxTime=True, q=True))
    with selutils.preserve_selection():
        with pm.UndoChunk():
            rig_reference = rig_reference or get_first_rig_reference_in_scene()
            root_joint, bind_skel = get_bind_skeleton_from_reference(rig_reference)
            for dag_node in pm.ls(assemblies=True):
                if root_joint.nodeName(stripNamespace=True).lower() == dag_node.nodeName().lower():
                    dag_node.rename('renamed_because_the_anim_skel_needs_this_name')
            locators = [l.getParent() for l in root_joint.getChildren(allDescendents=True, type=pm.nt.Locator)]
            bind_skel_and_locators = bind_skel + locators
            dup_bind_skel_and_locators = pm.duplicate(bind_skel_and_locators, parentOnly=True)
            dup_root = skelutils.get_root_joint_from_child(dup_bind_skel_and_locators[0])
            dup_root.setParent(world=True)
            
            constraints = []
            for bind_joint, dup_joint in zip(bind_skel_and_locators, dup_bind_skel_and_locators):
                con = rigutils.parent_constraint_shortest(bind_joint, dup_joint)
                constraints.append(con)
                bind_joint.scale.connect(dup_joint.scale)
                
            pm.bakeResults(dup_bind_skel_and_locators, simulation=True, time=str(frame_start) + ":" + str(frame_end), sampleBy=1,
                           oversamplingRate=1, disableImplicitControl=True, preserveOutsideKeys=False,
                           sparseAnimCurveBake=False, removeBakedAttributeFromLayer=True,
                           removeBakedAnimFromLayer=False,
                           bakeOnOverrideLayer=False, minimizeRotation=False, controlPoints=False, shape=True)
            pm.keyframe(dup_bind_skel_and_locators, edit=True, includeUpperBound=False, animation='objects',
                        time='{0}:{1}'.format(frame_start, frame_end), relative=True,
                        option='over', timeChange=frame_start*-1)
            pm.delete(constraints)
            [dj.scale.disconnect() for dj in dup_bind_skel_and_locators]
            new_start_frame = 0
            new_end_frame = frame_end-frame_start
            pm.playbackOptions(min=new_start_frame)
            pm.playbackOptions(max=new_end_frame)
            pm.filterCurve(dup_bind_skel_and_locators)
            ioutils.ensure_file_is_writable(export_fbx_path)
            result = ioutils.export_fbx(export_fbx_path, dup_bind_skel_and_locators)
            if result.lower() == 'success':
                print('Successfully exported animation clip to {0}: '.format(export_fbx_path))
        pm.undo()
    return result


def get_bind_skeleton_from_reference(reference):
    skinned_mesh = skinutils.get_skinnned_meshes_in_list(reference.nodes(recursive=True))[0]
    root_joint = skinutils.get_root_joint_from_skinned_mesh(skinned_mesh)
    skeleton = skelutils.get_hierarchy_from_root(root_joint, joints_only=True)
    return root_joint, skeleton


def get_locator_nodes_from_reference(reference):
    locator_shapes = set(pm.ls(reference.nodes(recursive=True), type=pm.nt.Locator))
    locator_transform_nodes = list(set([s.getParent() for s in locator_shapes]))
    return locator_transform_nodes


def get_locator_nodes_from_root_joint(root_joint):
    root_joint.getChildren(allDescendents=True)

def get_first_rig_reference_in_scene():
    references = pm.listReferences()
    return references[0]


def get_rad_clip_data_from_scene():
    scene_path = pathutils.get_scene_path() 
    frame_start = int(pm.playbackOptions(minTime=True, query=True))
    frame_end = int(pm.playbackOptions(maxTime=True, query=True))
    clip_name = scene_path.stem
    export_path = os.path.normpath(get_clip_export_default_path(clip_name, dir_path=scene_path.parents[1]))
    current_reference = pm.listReferences()[0]
    clip_data_dict = {CLIP_NAME: clip_name, CLIP_FRAME_START: frame_start, CLIP_FRAME_END: frame_end,
                 CLIP_EXPORT_PATH: export_path, CLIP_RIG_NAMESPACE: current_reference.namespace}
    return clip_data_dict


def get_metadata_default_path(scene_path=None):
    metadata_path = scene_path or pathutils.get_scene_path() 
    if metadata_path:
        metadata_path = metadata_path.with_suffix(EXTENSION_METADATA)
        metadata_name = metadata_path.name.replace(ANIM_SEQUENCE_PREFIX.lower(), METADATA_PREFIX)
        metadata_name = metadata_name.replace(ANIM_SEQUENCE_PREFIX, METADATA_PREFIX)
        metadata_path = metadata_path.parent.joinpath(metadata_name)
    return metadata_path


def get_clip_export_default_path(clip_name, dir_path=None):
    dir_path = dir_path or get_metadata_start_dir()
    clip_export_path = dir_path.joinpath(clip_name).with_suffix(EXTENSION_FBX)
    return clip_export_path


def get_metadata_start_dir():
    start_dir = path_consts.FLOTTITOOLS_DIR
    scene_path = pathutils.get_scene_path()
    if scene_path:
        start_dir = scene_path.parent
    return start_dir


def write_default_rad_metadata():
    metadata_path = get_metadata_default_path()
    clips_data = [get_rad_clip_data_from_scene()]
    norm_path = os.path.normpath(metadata_path)
    with open(norm_path, 'w', encoding='utf-8') as f:
        json.dump(clips_data, f, ensure_ascii=False, indent=4)
    return clips_data


def write_clips_to_rad_metadata(clips):
    metadata_path = get_metadata_default_path()
    norm_path = os.path.normpath(metadata_path)
    ioutils.ensure_file_is_writable(metadata_path)
    with open(norm_path, 'w', encoding='utf-8') as f:
        json.dump(clips, f, ensure_ascii=False, indent=4)


def get_default_rad_data_for_export():
    metadata_path = get_metadata_default_path()
    if not metadata_path.exists():
        return
    abs_metadata_path = os.path.normpath(metadata_path)
    with open(abs_metadata_path) as f:
        metadata = json.load(f)
    return metadata
    # return export_clip_dict(metadata)


def export_clip_dict(clip_dict):
    export_path = Path(clip_dict[CLIP_EXPORT_PATH])
    matching_reference = get_matching_reference(clip_dict[CLIP_RIG_NAMESPACE])
    result = export_animation(export_path, clip_dict[CLIP_FRAME_START], clip_dict[CLIP_FRAME_END],
                                            rig_reference=matching_reference)
    
    return result

def get_matching_reference(ref_ns, references_current_scene=None):
    references_current_scene = references_current_scene or pm.listReferences()
    matching_ref = None
    for ref in references_current_scene:
        if ref_ns == ref.namespace:
            matching_ref = ref
    return matching_ref
