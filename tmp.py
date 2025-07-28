import os
import sys
import logging
import pyJianYingDraft as draft
from pyJianYingDraft import VideoMaterial, ShrinkMode, ExtendMode, ExportResolution, ExportFramerate

# Redirect stderr to the log file
log_file = open('pyjianying.log', 'a')
sys.stderr = log_file

logging.basicConfig(stream=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def load_existing_project(project_path):
    json_path = os.path.join(project_path, "draft_content.json")
    logging.debug(f'Loading existing project json: {json_path}')
    return draft.ScriptFile.load_template(json_path)

def clone_project(draft_folder_path, source_name, target_name):
    target_path = os.path.join(draft_folder_path, target_name)
    draft_folder = draft.DraftFolder(draft_folder_path)
    if os.path.exists(target_path):
        logging.debug(f'Target project already exists: {target_name}, skipping clone.')
        return load_existing_project(target_path)
    logging.debug(f'Cloning project: {source_name} -> {target_name}')
    script = draft_folder.duplicate_as_template(source_name, target_name)
    logging.debug(f'Cloned project: {target_name}')
    return script

def replace_main_track_materials(script, replacements):
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

def process_projects(draft_folder_path, project_names, replacements, export_dir):
    ctrl = draft.JianyingController()
    for name in project_names:
        target_name = name.rsplit('_', 1)[0] + '_5'
        logging.debug(f'Processing project: {name} -> {target_name}')
        script = clone_project(draft_folder_path, name, target_name)
        replace_main_track_materials(script, replacements)
        export_path = os.path.join(export_dir, f"{target_name}.mp4")
        logging.debug(f'Exporting project {target_name} to {export_path}')
        ctrl.export_draft(
            target_name,
            export_path,
            resolution=ExportResolution.RES_1080P,
            framerate=ExportFramerate.FR_24
        )

if __name__ == "__main__":
    draft_folder_path = r"C:\\Users\\Admin\\AppData\\Local\\CapCut\\User Data\\Projects\\com.lveditor.draft"
    export_dir = r"C:\\Users\\Admin\\Downloads\\tmp\\vid\\final"
    project_list = [
        "2D-VC-SYP-BP-260602_2",
        "2D-VC-SYP-BP-260603_2"
    ]
    replacements = [
        [0, r"C:\\path\\to\\new_clip_0.mp4"],
        [1, r"C:\\path\\to\\new_clip_1.mp4"]
    ]
    process_projects(draft_folder_path, project_list, replacements, export_dir)

log_file.close()
