from flask import Flask, request, jsonify
import subprocess
import json
import tempfile
import os

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute_script():
    try:
        # Input validation
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        
        if 'script' not in data:
            return jsonify({"error": "Missing 'script' field in request body"}), 400
        
        script = data['script']
        
        if not isinstance(script, str):
            return jsonify({"error": "'script' must be a string"}), 400
        
        if not script.strip():
            return jsonify({"error": "'script' cannot be empty"}), 400
        
        # Basic validation - check if main() function exists
        if 'def main()' not in script:
            return jsonify({"error": "Script must contain a 'def main():' function"}), 400
        
        # Create a wrapper script that captures the return value
        # Use separate file writes to avoid f-string injection with triple quotes
        wrapper_code = '''
import json
import sys
import io

# Redirect stdout to capture print statements BEFORE importing user code
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = captured_stdout = io.StringIO()
sys.stderr = captured_stderr = io.StringIO()

# User's script
'''
        wrapper_code += script
        wrapper_code += '''

# Execute main and capture result
try:
    result = main()
    
    # Restore stdout/stderr BEFORE outputting result
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    
    # Validate that result is JSON-serializable
    try:
        json.dumps(result)
    except (TypeError, ValueError):
        print(json.dumps({"error": "main() must return a JSON-serializable value"}), file=sys.stderr)
        sys.exit(1)
    
    # Output the result and stdout (only JSON to stdout now)
    output = {
        "result": result,
        "stdout": captured_stdout.getvalue()
    }
    print(json.dumps(output))
except Exception as e:
    # Restore streams if not already done
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    print(json.dumps({"error": f"Error executing main(): {str(e)}"}), file=sys.stderr)
    sys.exit(1)
'''
        wrapper_script = wrapper_code
        
        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='/tmp') as f:
            script_path = f.name
            f.write(wrapper_script)
        
        try:
            # For Cloud Run, use direct subprocess with resource limits
            # Cloud Run provides container-level isolation
            result = subprocess.run(
                ['/usr/local/bin/python3', script_path],
                capture_output=True,
                text=True,
                timeout=30,
                env={
                    'PYTHONDONTWRITEBYTECODE': '1',
                    'PYTHONUNBUFFERED': '1',
                    'OPENBLAS_NUM_THREADS': '1',
                    'OMP_NUM_THREADS': '1',
                    'MKL_NUM_THREADS': '1'
                },
                cwd='/tmp'
            )
            
            # Parse the output
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout.strip())
                    return jsonify(output), 200
                except json.JSONDecodeError:
                    return jsonify({
                        "error": "Failed to parse script output",
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }), 500
            else:
                # Try to parse error message
                try:
                    error_output = json.loads(result.stdout.strip())
                    return jsonify(error_output), 400
                except json.JSONDecodeError:
                    return jsonify({
                        "error": "Script execution failed",
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }), 500
        
        finally:
            # Clean up temporary file
            if os.path.exists(script_path):
                os.unlink(script_path)
    
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Script execution timeout (30s limit)"}), 408
    
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)