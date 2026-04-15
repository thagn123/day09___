import os
import glob

def check_null_bytes():
    files = glob.glob('**/*.py', recursive=True) + glob.glob('**/*.json', recursive=True)
    for f in files:
        if os.path.isfile(f):
            try:
                content = open(f, 'rb').read()
                null_count = content.count(b'\x00')
                if null_count > 0:
                    print(f"{f}: {null_count} null bytes found")
            except Exception as e:
                print(f"Error reading {f}: {e}")

if __name__ == "__main__":
    check_null_bytes()
