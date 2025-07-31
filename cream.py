import os
import sys
import logging
import pyJianYingDraft as draft
from pyJianYingDraft import trange, VideoMaterial, ShrinkMode, ExtendMode
from typing import List, Tuple, Dict, Any
import json
from dataclasses import asdict, is_dataclass

# Constants for duration behavior
SHIFT_NO = 0  # Keep duration and segment positions
SHIFT_YES = 1  # Allow timeline shift if necessary

# Redirect stderr to the log file
log_file = open('cream.log', 'a')
sys.stderr = log_file

logging.basicConfig(stream=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def check_paths(draft_folder_path: str, export_dir: str, targets: List[Dict[str, Any]]) -> None:
    if not os.path.exists(draft_folder_path):
        raise FileNotFoundError(f"Draft folder path does not exist: {draft_folder_path}")
    if not os.path.exists(export_dir):
        logging.debug(f"Export directory does not exist, creating: {export_dir}")
        os.makedirs(export_dir, exist_ok=True)
    for target in targets:
        for replacement in target['replacements']:
            if not os.path.isfile(replacement[1]):
                raise FileNotFoundError(f"Replacement file does not exist: {replacement[1]}")

def load_existing_project(project_path: str) -> draft.ScriptFile:
    json_path = os.path.normpath(os.path.join(project_path, "draft_content.json"))
    logging.debug(f'Loading existing project json: {json_path}')
    return draft.ScriptFile.load_template(json_path)

def clone_project(draft_folder_path: str, source_name: str, target_name: str) -> draft.ScriptFile:
    target_path = os.path.normpath(os.path.join(draft_folder_path, target_name))
    draft_folder = draft.DraftFolder(draft_folder_path)
    if os.path.exists(target_path):
        logging.debug(f'Target project already exists: {target_name}, skipping clone.')
        return load_existing_project(target_path)
    logging.debug(f'Cloning project: {source_name} -> {target_name}')
    script = draft_folder.duplicate_as_template(source_name, target_name)
    logging.debug(f'Cloned project: {target_name}')
    return script

def replace_main_track_materials(script: draft.ScriptFile, replacements: List[Tuple[int, str, int]]) -> None:
    video_track = script.get_imported_track(draft.TrackType.video, index=0)
    logging.debug(f'Video track info: {video_track}')
    logging.debug('Inspecting current video track materials:')
    for idx, seg in enumerate(video_track.segments):
        logging.debug(f'Clip {idx}: material_id={seg.material_id}, duration={seg.duration}')
    for replacement in replacements:
        clip_index, new_path, shift_mode = replacement
        logging.debug(f'Replacing clip index {clip_index} with {new_path}, duration_mode={shift_mode}')
        new_material = VideoMaterial(new_path)
        target_duration = video_track.segments[clip_index].duration

        if shift_mode == SHIFT_NO:
            shrink = ShrinkMode.cut_tail
            extend = ExtendMode.cut_material_tail
        else:
            shrink = ShrinkMode.cut_tail_align
            extend = ExtendMode.push_tail

        script.replace_material_by_seg(
            video_track,
            clip_index,
            new_material,
            source_timerange=trange(0, target_duration) if shift_mode == SHIFT_NO else None,
            handle_shrink=shrink,
            handle_extend=extend
        )
        logging.debug(f'Replaced clip {clip_index} with {new_path} using mode {shift_mode}')
    script.save()
    logging.debug('Project saved after replacements')

# shrink - What to do when the new material is shorter than the original segment:
#     cut_head:
#     Cut the head - Trim the start of the segment by moving the start time later.

#     cut_tail:
#     Cut the tail - Trim the end of the segment by moving the end time earlier (default in your script).

#     cut_tail_align:
#     Cut the tail and shift everything after - Like cut_tail, but also shifts all following segments earlier to eliminate any resulting gap.

#     shrink:
#     Shrink both ends toward the center - The center timestamp of the original segment is preserved, and both start and end times move inward to shorten the segment symmetrically.

# ExtendMode - What to do when the new material is longer than the original segment:

#     cut_material_tail:
#     Trim the end of the new material so it matches the original segment duration. It overrides any source_timerange. This is the safest and always succeeds.

#     extend_head:
#     Try to extend the start of the segment earlier. This can fail if there's another clip right before.

#     extend_tail:
#     Try to extend the end of the segment later. This can fail if there's another clip after it.

#     push_tail:
#     Extend the end and push later segments forward to make space. This always succeeds.

# def deep_log_materials(script: draft.ScriptFile):
#     try:
#         logging.debug("MATERIALS FIELDS:")
#         for attr in dir(script.materials):
#             if attr.startswith("_"):
#                 continue
#             val = getattr(script.materials, attr)
#             if isinstance(val, list):
#                 logging.debug(f"{attr}: list of {len(val)}")
#                 for i, item in enumerate(val[:5]):
#                     logging.debug(f"  {attr}[{i}] = {repr(item)}")
#             else:
#                 logging.debug(f"{attr}: {repr(val)}")
#     except Exception as e:
#         logging.error(f"Failed to inspect materials: {e}")

# def log_segment_effects(script: draft.ScriptFile):
#     try:
#         video_track = script.get_imported_track(draft.TrackType.video, index=0)
#         for idx, seg in enumerate(video_track.segments):
#             logging.debug(f"Segment {idx} id={seg.material_id}, duration={seg.duration}")
#             for attr in dir(seg):
#                 if attr.startswith("_"):
#                     continue
#                 val = getattr(seg, attr)
#                 if isinstance(val, list):
#                     logging.debug(f"  {attr}: list of {len(val)}")
#                     for i, item in enumerate(val[:3]):
#                         logging.debug(f"    {attr}[{i}] = {repr(item)}")
#                         for fx_attr in dir(item):
#                             if not fx_attr.startswith('_'):
#                                 logging.debug(f"      {fx_attr} = {getattr(item, fx_attr)}")
#                 else:
#                     logging.debug(f"  {attr}: {repr(val)}")
#     except Exception as e:
#         logging.error(f"Failed to inspect segments: {e}")

# def update_filter_strength(script: draft.ScriptFile, strength_percent: int) -> None:
#     updated = False
#     # logging.debug(script.materials.export_json())
#     # deep_log_materials(script)
#     # log_segment_effects(script)
#     # sys.exit()
#     if hasattr(script, "materials") and hasattr(script.materials, "effects"):
#         for fx in script.materials.effects:
#             if getattr(fx, "type", None) == "filter" and hasattr(fx, "value"):
#                 old = fx.value
#                 fx.value = strength_percent / 100.0
#                 logging.debug(f"Updated FILTER strength from {old} to {fx.value} (effect_id={getattr(fx, 'effect_id', '?')})")
#                 updated = True
#     if not updated:
#         logging.debug("No filter strength updated – no matching 'filter' effect found")
#     script.save()
#     logging.debug(f'Filter strength set to {strength_percent}%')

def process_targets(draft_folder_path: str, source_name: str, targets: List[Dict[str, Any]], export_dir: str) -> None:
    check_paths(draft_folder_path, export_dir, targets)
    for target in targets:
        target_name = target['name']
        replacements = target.get('replacements', [])
        # filter_strength = target.get('filter_strength', 100)

        logging.debug(f'Processing target project: {target_name}')
        script = clone_project(draft_folder_path, source_name, target_name)
        if replacements:
            replace_main_track_materials(script, replacements)
        # update_filter_strength(script, strength_percent=filter_strength)
        # export_path = os.path.normpath(os.path.join(export_dir, f"{target_name}.mp4"))
        # logging.debug(f'Exporting project {target_name} to {export_path}')
        # script.export(export_path)

if __name__ == "__main__":
    draft_folder_path = r"C:\\Users\\Admin\\AppData\\Local\\CapCut\\User Data\\Projects\\com.lveditor.draft"
    export_dir = r"C:\\Users\\Admin\\Downloads\\tmp\\vid\\kem\\final"
    source_project_name = "b3"

    target_projects = [
        {
            "name": "m3",
            "replacements": [
                [4, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\melasma\g5_kling_m1_desub.mp4", SHIFT_NO],
                [5, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\melasma\mf_open_1.mp4", SHIFT_NO],
                [6, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\melasma\mf_open_2.mp4", SHIFT_NO],
            ],
            "filter_strength": 2
        },
        {
            "name": "ss3",
            "replacements": [
                [4, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\sun\g5_kling_ss1.mp4", SHIFT_NO],
                [5, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\sun\ssf_1.mp4", SHIFT_NO],
                [6, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\sun\ssf_2.mp4", SHIFT_NO],
            ],
            "filter_strength": 7
        },
                {
            "name": "sr3",
            "replacements": [
                [4, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\serum\g5_kling_sr1.mp4", SHIFT_NO],
                [5, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\serum\srf_1.mp4", SHIFT_NO],
                [6, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\serum\srf_2.mp4", SHIFT_NO],
            ],
            "filter_strength": 15
        },
    ]

    process_targets(draft_folder_path, source_project_name, target_projects, export_dir)

log_file.close()
