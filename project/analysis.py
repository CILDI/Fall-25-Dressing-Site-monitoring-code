import csv
import os
#For testing purposes

def log_test_results_to_csv(photo_id, photo_url, result_json, filename="test_results.csv"):
    print("--- Entered log test ---")
    # 1. AI categories (These are the confidence levels the code fills automatically)
    ai_categories = ["Blood", "Pus", "Red Skin", "Dressing", "Catheter", "Catheter Dressing Damage"]
    # 2. Manual categories (These will be left empty for you to fill later)
    manual_columns = ["description", "act Blood", "act Pus", "act Red Skin", "act Dressing", "act Catheter", "act Catheter Dressing Damage"]
    file_exists = os.path.isfile(filename)
    current_confidences = {cat: 0.0 for cat in ai_categories}
    if isinstance(result_json, dict):
        for p in result_json.get("predictions", []):
            cls = p.get("class")
            conf = p.get("confidence", 0.0)
            if cls in current_confidences:
                current_confidences[cls] = max(current_confidences[cls], conf)

    with open(filename, mode='a', newline='') as f:
        writer = csv.writer(f)
        # Create Header: Picture ID | Link | AI Confidences... | Manual Columns...
        if not file_exists:
            header = ["Picture ID", "Link"] + ai_categories + manual_columns
            writer.writerow(header)
        # Build the Row: Data | Empty Strings for the 7 manual columns
        empty_placeholders = [""] * len(manual_columns)
        row = [photo_id, photo_url] + [current_confidences[cat] for cat in ai_categories] + empty_placeholders
       

        writer.writerow(row)
        print(f"DEBUG: Results logged to {filename}")

       

    print("--- Exited log test ---")

#For terminal output

def format_and_calculate_trends(current_json, previous_json=None):

    """

    Parses messy Roboflow JSON and calculates the delta from the last check.

    """

    report = []

   

    # Use .get() to prevent KeyError if 'predictions' is missing

    current_preds = current_json.get('predictions', []) if isinstance(current_json, dict) else []

    current_data = {p.get('class'): p.get('confidence', 0.0) for p in current_preds if p.get('class')}

   

    prev_preds = previous_json.get('predictions', []) if isinstance(previous_json, dict) else []

    prev_data = {p.get('class'): p.get('confidence', 0.0) for p in prev_preds if p.get('class')}



    print("\n--- Diagnostic Report ---")

    if not current_data:

        print("Status: No markers detected (Healthy/Clean Site)")

    else:

        for cls, conf in current_data.items():

            trend_val = conf - prev_data.get(cls, 0)

            trend_str = f"({'+' if trend_val >= 0 else ''}{trend_val:.3f})" if previous_json else ""

            line = f"{cls}: confidence {conf:.4f} {trend_str}"

            print(line)

            report.append(line)

    print("--- End Report ---\n")

    return report