from pathlib import Path
from Classes.Base.FileClass import File


class ModelValidator:

    def __init__(self, casename):
        self.casename = casename

        self.base_path = Path("DataStorage") / casename

        self.errors = []
        self.warnings = []

    def check_file_exists(self, filename, code):

        file_path = self.base_path / filename

        if not file_path.exists():

            self.errors.append({
                "code": code,
                "message": f"{filename} is missing",
                "fix": f"Add the required file: {filename}"
            })

    def validate(self):

        # Example checks
        self.check_file_exists("Demand.json", "E001")
        self.check_file_exists("Technologies.json", "E002")

        report = {
            "casename": self.casename,
            "valid": len(self.errors) == 0,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings
        }

        return report