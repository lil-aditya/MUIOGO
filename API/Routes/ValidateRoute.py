from flask import Blueprint, jsonify
from Services.ModelValidator import ModelValidator

validate_api = Blueprint("validate_api", __name__)


@validate_api.route("/validate/<casename>", methods=["GET"])
def validate_model(casename):

    try:

        validator = ModelValidator(casename)

        report = validator.validate()

        status = 200 if report["valid"] else 422

        return jsonify(report), status

    except Exception as e:

        return jsonify({"error": str(e)}), 500