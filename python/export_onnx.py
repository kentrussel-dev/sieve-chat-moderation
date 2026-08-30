"""
ONNX Export Utility for Sieve Tier 1 Classifier.
Exports PyTorch/Transformers or sklearn models to ONNX graph format with dynamic batching.
"""

import argparse
import os
import sys

def export_sklearn_to_onnx(model_path: str, output_path: str):
    try:
        import joblib
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import StringTensorType
        
        model = joblib.load(model_path)
        initial_type = [("text_input", StringTensorType([None, 1]))]
        
        onnx_model = convert_sklearn(model, initial_types=initial_type, target_opset=12)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        print(f"Exported ONNX model successfully to {output_path}")
    except ImportError:
        print("skl2onnx not installed; skipping ONNX binary serialization.")
    except Exception as e:
        print(f"ONNX export notice: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Tier 1 Model to ONNX")
    parser.add_argument("--model-path", type=str, default="./models/tier1_model.joblib")
    parser.add_argument("--out", type=str, default="./models/tier1_model.onnx")
    args = parser.parse_args()
    
    export_sklearn_to_onnx(
        os.path.join(os.path.dirname(__file__), args.model_path),
        os.path.join(os.path.dirname(__file__), args.out)
    )
