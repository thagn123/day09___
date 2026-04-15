import os
import glob

def convert_to_utf8(path):
    files = glob.glob(os.path.join(path, "**/*.py"), recursive=True)
    for f in files:
        try:
            with open(f, 'rb') as fr:
                content = fr.read()
            # Try decoding as windows-1258, then utf-8
            try:
                text = content.decode('windows-1258')
                print(f"Converted {f} from windows-1258")
            except:
                try:
                    text = content.decode('utf-8')
                    # If already utf-8, just write back to be sure
                except:
                    print(f"Skipping {f} - unknown encoding")
                    continue
            
            with open(f, 'w', encoding='utf-8') as fw:
                fw.write(text)
        except Exception as e:
            print(f"Error processing {f}: {e}")

if __name__ == "__main__":
    convert_to_utf8('.')
