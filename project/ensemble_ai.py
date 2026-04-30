from colab_model import run_pytorch_inference
from ai import inference_helper as roboflow_inference
"""
This is the logic that decides which of the two AI models to use for each confidence level.
We will always choose the one with the highest confidence level

"""
def get_unified_inference(frame):
    # 1. Run both models
    roboflow_json, annotated_bytes, encoded_buffer = roboflow_inference(frame)
    pytorch_results = run_pytorch_inference(frame)
    
    if not roboflow_json or not isinstance(roboflow_json, dict):
        roboflow_json = {"predictions": []}

    # Tag all initial Roboflow results as 'Roboflow'
    for p in roboflow_json.get("predictions", []):
        p["source"] = "Roboflow"

    mapping = {"Blood": "Blood", "Pus": "Pus", "Redness": "Red Skin"}

    if not isinstance(pytorch_results, list):
        pytorch_results = [pytorch_results]

    # 2. Process PyTorch results without printing the whole object
    for py_pred in pytorch_results:
        py_cls = None
        py_conf = 0.0

        # Extraction logic
        if isinstance(py_pred, dict):
            py_cls = py_pred.get('class') or py_pred.get('label') or py_pred.get('name')
            py_conf = py_pred.get('confidence', 0.0)
        elif (isinstance(py_pred, (list, tuple))) and len(py_pred) >= 2:
            py_cls = py_pred[0]
            py_conf = py_pred[1]

        # Flatten class name
        while isinstance(py_cls, (list, tuple)) and len(py_cls) > 0:
            py_cls = py_cls[0]
        if isinstance(py_cls, dict):
            py_cls = py_cls.get('class') or py_cls.get('label') or py_cls.get('name') or "Unknown"

        # 3. Merge and Log Source
        target_cls = mapping.get(py_cls)
        
        if target_cls and isinstance(py_conf, (int, float)):
            found = False
            preds = roboflow_json.get("predictions", [])
            for r_pred in preds:
                if r_pred.get("class") == target_cls:
                    found = True
                    r_conf = r_pred.get("confidence", 0)
                    if py_conf > r_conf:
                        # PyTorch wins: Update confidence and change source
                        print(f"DEBUG: [Ensemble] {target_cls} updated by PyTorch ({py_conf:.2f} > {r_conf:.2f})")
                        r_pred["confidence"] = py_conf
                        r_pred["source"] = "PyTorch"
                    else:
                        print(f"DEBUG: [Ensemble] {target_cls} kept Roboflow ({r_conf:.2f} > {py_conf:.2f})")
                        r_pred["source"] = "Roboflow"
                    break
            
            if not found and py_conf > 0.4:
                print(f"DEBUG: [Ensemble] {target_cls} detected EXCLUSIVELY by PyTorch ({py_conf:.2f})")
                roboflow_json["predictions"].append({
                    "class": target_cls, 
                    "confidence": py_conf,
                    "source": "PyTorch",
                    "x": 0, "y": 0, "width": 0, "height": 0
                })

    return roboflow_json, annotated_bytes, encoded_buffer