import json
import os

from flask import Blueprint, jsonify

yoga_bp = Blueprint("yoga", __name__)

POSES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "yoga_poses.json")


@yoga_bp.route("/poses", methods=["GET"])
def get_poses():
    with open(POSES_PATH, "r", encoding="utf-8") as f:
        poses = json.load(f)
    return jsonify(poses)


@yoga_bp.route("/poses/<pose_id>", methods=["GET"])
def get_pose(pose_id):
    with open(POSES_PATH, "r", encoding="utf-8") as f:
        poses = json.load(f)

    pose = next((p for p in poses if p["id"] == pose_id), None)
    if not pose:
        return jsonify({"error": "Pose not found"}), 404
    return jsonify(pose)
