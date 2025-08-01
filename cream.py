import os
import sys
import logging
import pyJianYingDraft as draft
from pyJianYingDraft import trange, VideoMaterial, ShrinkMode, ExtendMode, TrackType
from typing import List, Tuple, Dict, Any
import json
from dataclasses import asdict, is_dataclass

# Constants for shifting behavior
SHIFT_NO = 0  # Keep duration and segment positions
SHIFT_YES = 1  # Allow timeline shift if necessary

# Redirect stderr to the log file
log_file = open('cream.log', 'a', encoding='utf-8')
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
        logging.debug(f'Replacing clip index {clip_index} with {new_path}, shift_mode={shift_mode}')
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
        logging.debug(f'Replaced clip {clip_index} with {new_path} using shift_mode {shift_mode}')
    script.save()
    logging.debug('Project saved after replacements')

def replace_text(script: draft.ScriptFile, replacements: List[Tuple[int, str]]):
    try:
        text_track = script.get_imported_track(track_type=TrackType.text, index=0)
        logging.debug(f"Text track loaded: name={getattr(text_track, 'name', None)}, index={getattr(text_track, 'index', None)}, segments={len(text_track.segments)}")
        for idx, new_text in replacements:
            script.replace_text(text_track, idx, new_text)
            logging.debug(f"Text segment {idx} replaced with: {new_text}")
        script.save()
    except Exception as e:
        logging.error(f"Failed to replace text: {type(e).__name__}: {e}")

def process_targets(draft_folder_path: str, source_name: str, targets: List[Dict[str, Any]], export_dir: str) -> None:
    check_paths(draft_folder_path, export_dir, targets)
    for target in targets:
        target_name = target['name']
        replacements = target.get('replacements', [])
        text_replacements = target.get('text_replacements', [])

        logging.debug(f'Processing target project: {target_name}')
        script = clone_project(draft_folder_path, source_name, target_name)
        # script.inspect_material()
        # sys.exit()
        if replacements:
            replace_main_track_materials(script, replacements)
        if text_replacements:
            replace_text(script, text_replacements)

if __name__ == "__main__":
    draft_folder_path = r"C:\\Users\\Admin\\AppData\\Local\\CapCut\\User Data\\Projects\\com.lveditor.draft"
    export_dir = r"C:\\Users\\Admin\\Downloads\\tmp\\vid\\kem\\final"
    source_project_name = "b3_h1_o3"

    projects = [
        {
            "name": "m3_h1_o3",
            "replacements": [
                [5, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\melasma\g5_kling_m1_desub.mp4", SHIFT_NO],
                [6, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\melasma\mf_open_1.mp4", SHIFT_NO],
                [7, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\melasma\mf_open_2.mp4", SHIFT_NO],
            ],
            "text_replacements": [
                [0, "Aku juga dulu begitu\nsampai nemu ini "],
                [1, "Beli melasma Sekarang Diskon Besa"],
            ],
            "filter_strength": 2
        },
        {
            "name": "ss3_h1_o3",
            "replacements": [
                [5, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\sun\g5_kling_ss1.mp4", SHIFT_NO],
                [6, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\sun\ssf_1.mp4", SHIFT_NO],
                [7, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\sun\ssf_2.mp4", SHIFT_NO],
            ],
            "text_replacements": [
                [0, "Kulitku makin rusak tiap\nhari karena matahari\nsampai aku ganti sunscreen "],
                [1, "Beli sunscreen Sekarang Diskon Besa"],
            ],
            "filter_strength": 7
        },
        {
            "name": "sr3_h1_o3",
            "replacements": [
                [5, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\serum\g5_kling_sr1.mp4", SHIFT_NO],
                [6, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\serum\srf_1.mp4", SHIFT_NO],
                [7, r"C:\Users\Admin\Downloads\tmp\vid\kem\source\serum\srf_2.mp4", SHIFT_NO],
            ],
            "text_replacements": [
                [0, "Bekas jerawat, tekstur kasar\nrasanya udah pasrah"],
                [1, "Diskon\nBesar-besaran\nSekarang"],
            ],
            "filter_strength": 15
        },
    ]

    for proj in projects:
        source_name = proj.get("source", source_project_name)
        process_targets(draft_folder_path, source_name, [proj], export_dir)

log_file.close()
