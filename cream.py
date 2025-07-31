import os
import sys
import logging
import pyJianYingDraft as draft
from pyJianYingDraft import trange, VideoMaterial, ShrinkMode, ExtendMode
from typing import List, Tuple

# Redirect stderr to the log file
log_file = open('cream.log', 'a')
sys.stderr = log_file

logging.basicConfig(stream=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def check_paths(draft_folder_path: str, export_dir: str, replacements: List[Tuple[int, str]]) -> None:
    if not os.path.exists(draft_folder_path):
        raise FileNotFoundError(f"Draft folder path does not exist: {draft_folder_path}")
    if not os.path.exists(export_dir):
        logging.debug(f"Export directory does not exist, creating: {export_dir}")
        os.makedirs(export_dir, exist_ok=True)
    for _, path in replacements:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Replacement file does not exist: {path}")

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

def replace_main_track_materials(script: draft.ScriptFile, replacements: List[Tuple[int, str]]) -> None:
    video_track = script.get_imported_track(draft.TrackType.video, index=0)
    logging.debug(f'Video track info: {video_track}')
    logging.debug('Inspecting current video track materials:')
    for idx, seg in enumerate(video_track.segments):
        logging.debug(f'Clip {idx}: material_id={seg.material_id}, duration={seg.duration}')
    for clip_index, new_path in replacements:
        logging.debug(f'Replacing clip index {clip_index} with {new_path}')
        new_material = VideoMaterial(new_path)
        script.replace_material_by_seg(
            video_track,
            clip_index,
            new_material,
            source_timerange=None,
            handle_shrink=ShrinkMode.cut_tail,
            handle_extend=ExtendMode.push_tail
        )
        logging.debug(f'Replaced clip {clip_index} with {new_path}')
    script.save()
    logging.debug('Project saved after replacements')

def update_filter_strength(script: draft.ScriptFile, strength_percent: int) -> None:
    for fx in script.materials.filters:
        if hasattr(fx, 'strength'):
            old = fx.strength
            fx.strength = strength_percent / 100.0
            logging.debug(f"Updated filter strength from {old} to {fx.strength}")
    script.save()
    logging.debug(f'Filter strength set to {strength_percent}%')

def process_projects(draft_folder_path: str, project_names: List[str], replacements: List[Tuple[int, str]], export_dir: str) -> None:
    check_paths(draft_folder_path, export_dir, replacements)
    for name in project_names:
        target_name = name.rsplit('_', 1)[0] + '_5'
        logging.debug(f'Processing project: {name} -> {target_name}')
        script = clone_project(draft_folder_path, name, target_name)
        replace_main_track_materials(script, replacements)
        update_filter_strength(script, strength_percent=2)
        # export_path = os.path.normpath(os.path.join(export_dir, f"{target_name}.mp4"))
        # logging.debug(f'Exporting project {target_name} to {export_path}')
        # script.export(export_path)

if __name__ == "__main__":
    draft_folder_path = r"C:\\Users\\Admin\\AppData\\Local\\CapCut\\User Data\\Projects\\com.lveditor.draft"
    export_dir = r"C:\\Users\\Admin\\Downloads\\tmp\\vid\\kem\\final"
    project_list = [
        "b3"
    ]

    replacements = [
        [0, "/Users/chuongnh/Downloads/cream/vidkem/hook/Joane_dance.mp4"],
    ]
    process_projects(draft_folder_path, project_list, replacements, export_dir)

log_file.close()
