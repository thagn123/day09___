import os

def clean_files():
    files = ['workers/retrieval.py', 'workers/policy_tool.py', 'workers/synthesis.py']
    for f in files:
        if os.path.exists(f):
            print(f"Cleaning {f}...")
            with open(f, 'rb') as fr:
                content = fr.read()
            clean_content = content.replace(b'\x00', b'')
            with open(f, 'wb') as fw:
                fw.write(clean_content)
            print(f"Done cleaning {f}. Size: {len(clean_content)}")

if __name__ == "__main__":
    clean_files()
