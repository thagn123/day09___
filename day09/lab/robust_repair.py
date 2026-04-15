import os
import glob

def repair_file(f):
    print(f"Repairing {f}...")
    with open(f, 'rb') as rb:
        binary_content = rb.read()
    
    # Try different encodings
    for encoding in ['utf-8', 'windows-1258', 'latin-1']:
        try:
            text = binary_content.decode(encoding)
            print(f"  Successfully decoded with {encoding}")
            # Ensure it's now saved as clean UTF-8
            with open(f, 'w', encoding='utf-8') as wf:
                wf.write(text)
            return
        except UnicodeDecodeError:
            continue
    
    # Fallback: decode with utf-8 ignore
    print(f"  Fallback to utf-8 ignore for {f}")
    text = binary_content.decode('utf-8', errors='ignore')
    with open(f, 'w', encoding='utf-8') as wf:
        wf.write(text)

if __name__ == "__main__":
    for f in ['workers/retrieval.py', 'workers/policy_tool.py', 'workers/synthesis.py']:
        repair_file(f)
