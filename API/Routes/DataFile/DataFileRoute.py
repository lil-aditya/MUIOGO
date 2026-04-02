from flask import Blueprint, Response, jsonify, request, send_file, session
from pathlib import Path
import logging
import time
from Classes.Case.DataFileClass import DataFile
from Classes.Base import Config

datafile_api = Blueprint('DataFileRoute', __name__)
logger = logging.getLogger(__name__)


def _resolve_allowed_file(allowed_root: Path, candidate: Path) -> Path:
    safe_root = allowed_root.resolve(strict=False)
    safe_path = candidate.resolve(strict=False)
    try:
        safe_path.relative_to(safe_root)
    except ValueError as exc:
        raise PermissionError(f"Refusing to read outside {safe_root}") from exc

    if not safe_path.is_file():
        raise FileNotFoundError(safe_path)

    return safe_path


def _read_text_response(allowed_root: Path, candidate: Path) -> Response:
    safe_path = _resolve_allowed_file(allowed_root, candidate)
    text = safe_path.read_text(encoding="utf-8", errors="replace")
    return Response(text, content_type="text/plain; charset=utf-8")

@datafile_api.route("/generateDataFile", methods=['POST'])
def generateDataFile():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']

        if casename != None:
            txtFile = DataFile(casename)
            txtFile.generateDatafile(caserunname)
            response = {
                "message": "You have created data file!",
                "status_code": "success"
            }      
        return jsonify(response), 200
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/createCaseRun", methods=['POST'])
def createCaseRun():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        data = request.json['data']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.createCaseRun(caserunname, data)
     
        return jsonify(response), 200
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/updateCaseRun", methods=['POST'])
def updateCaseRun():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        oldcaserunname = request.json['oldcaserunname']
        data = request.json['data']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.updateCaseRun(caserunname, oldcaserunname, data)
     
        return jsonify(response), 200
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/deleteCaseRun", methods=['POST'])
def deleteCaseRun():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        resultsOnly = request.json['resultsOnly']

        if not casename:
            return jsonify({'message': 'No model selected.', 'status_code': 'error'}), 400

        caserun = DataFile(casename)
        response = caserun.deleteCaseRun(caserunname, resultsOnly)
        return jsonify(response), 200
    except FileNotFoundError:
        return jsonify('No existing cases!'), 404
    except OSError:
        return jsonify({'message': 'A filesystem error occurred.', 'status_code': 'error'}), 500

@datafile_api.route("/deleteScenarioCaseRuns", methods=['POST'])
def deleteScenarioCaseRuns():
    try:
        scenarioId = request.json['scenarioId']
        casename = request.json['casename']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.deleteScenarioCaseRuns(scenarioId)
     
        return jsonify(response), 200
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/saveView", methods=['POST'])
def saveView():
    try:
        casename = request.json['casename']
        param = request.json['param']
        data = request.json['data']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.saveView(data, param)
     
        return jsonify(response), 200
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/updateViews", methods=['POST'])
def updateViews():
    try:
        casename = request.json['casename']
        param = request.json['param']
        data = request.json['data']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.updateViews(data, param)
     
        return jsonify(response), 200
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/readDataFile", methods=['POST'])
def readDataFile():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        if casename != None:
            txtFile = DataFile(casename)
            data = txtFile.readDataFile(caserunname)
            response = data    
        else:  
            response = None     
        return jsonify(response), 200
    except(IOError):
        return jsonify('No existing cases!'), 404


@datafile_api.route("/readModelFile", methods=['GET'])
def readModelFile():
    try:
        return _read_text_response(Config.SOLVERs_FOLDER, Config.SOLVER_MODEL_FILE)
    except FileNotFoundError:
        return jsonify({'message': 'Model file not found.', 'status_code': 'error'}), 404
    except PermissionError:
        return jsonify({'message': 'Access denied.', 'status_code': 'error'}), 403


@datafile_api.route("/readLogFile", methods=['GET'])
def readLogFile():
    try:
        return _read_text_response(Config.LOG_DIR, Config.APP_LOG_FILE)
    except FileNotFoundError:
        return jsonify({'message': 'Log file not found.', 'status_code': 'error'}), 404
    except PermissionError:
        return jsonify({'message': 'Access denied.', 'status_code': 'error'}), 403
    
@datafile_api.route("/validateInputs", methods=['POST'])
def validateInputs():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        if casename != None:
            df = DataFile(casename)
            validation = df.validateInputs(caserunname)
            response = validation    
        else:  
            response = None     
        return jsonify(response), 200
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/downloadDataFile", methods=['GET'])
def downloadDataFile():
    try:
        #casename = request.json['casename']
        #casename = 'DEMO CASE'
        # txtFile = DataFile(casename)
        # downloadPath = txtFile.downloadDataFile()
        # response = {
        #     "message": "You have downloaded data.txt to "+ str(downloadPath) +"!",
        #     "status_code": "success"
        # }         
        # return jsonify(response), 200
        #path = "/Examples.pdf"
        case = session.get('osycase', None)
        caserunname = request.args.get('caserunname')
        dataFile = Path(Config.DATA_STORAGE,case, 'res',caserunname, 'data.txt')
        return send_file(dataFile.resolve(), as_attachment=True, max_age=0)
    
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/downloadFile", methods=['GET'])
def downloadFile():
    try:
        case = session.get('osycase', None)
        file = request.args.get('file')
        dataFile = Path(Config.DATA_STORAGE,case,'res','csv',file)
        return send_file(dataFile.resolve(), as_attachment=True, max_age=0)
    
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/downloadCSVFile", methods=['GET'])
def downloadCSVFile():
    try:
        case = session.get('osycase', None)
        file = request.args.get('file')
        caserunname = request.args.get('caserunname')
        dataFile = Path(Config.DATA_STORAGE,case,'res',caserunname,'csv',file)
        return send_file(dataFile.resolve(), as_attachment=True, max_age=0)
    
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/downloadResultsFile", methods=['GET'])
def downloadResultsFile():
    try:
        case = session.get('osycase', None)
        caserunname = request.args.get('caserunname')
        dataFile = Path(Config.DATA_STORAGE,case, 'res', caserunname,'results.txt')
        return send_file(dataFile.resolve(), as_attachment=True, max_age=0)
    
    except(IOError):
        return jsonify('No existing cases!'), 404

@datafile_api.route("/run", methods=['POST'])
def run():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        solver = request.json['solver']
        logger.info(
            "Starting optimization for model=%s caserun=%s solver=%s",
            casename,
            caserunname,
            solver,
        )
        txtFile = DataFile(casename)
        response = txtFile.run(solver, caserunname)
        logger.info(
            "Finished optimization for model=%s caserun=%s status=%s",
            casename,
            caserunname,
            response.get("status_code", "unknown"),
        )
        return jsonify(response), 200
    # except Exception as ex:
    #     print(ex)
    #     return ex, 404
    
    except(IOError):
        return jsonify('No existing cases!'), 404
    
@datafile_api.route("/batchRun", methods=['POST'])
def batchRun():
    try:
        start = time.time()
        modelname = request.json['modelname']
        cases = request.json['cases']

        if modelname != None:
            logger.info("Starting batch run for model=%s case_count=%s", modelname, len(cases))
            txtFile = DataFile(modelname)
            for caserun in cases:
                logger.info("Generating data file for model=%s caserun=%s", modelname, caserun)
                txtFile.generateDatafile(caserun)

            response = txtFile.batchRun( 'CBC', cases) 
            logger.info(
                "Finished batch run for model=%s status=%s",
                modelname,
                response.get("status", "unknown"),
            )
        end = time.time()  
        response['time'] = end-start 
        return jsonify(response), 200
    except(IOError):
        return jsonify('Error!'), 404
    
@datafile_api.route("/cleanUp", methods=['POST'])
def cleanUp():
    try:
        modelname = request.json['modelname']

        if modelname != None:
            model = DataFile(modelname)
            logger.info("Starting clean up for model=%s", modelname)
            response = model.cleanUp()
            logger.info("Finished clean up for model=%s", modelname)

        return jsonify(response), 200
    except(IOError):
        return jsonify('Error!'), 404
