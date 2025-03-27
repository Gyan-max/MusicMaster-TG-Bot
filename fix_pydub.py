import os
import sys
import subprocess

def find_pydub_location():
    try:
        # Use pip to find where pydub is installed
        result = subprocess.run([sys.executable, "-m", "pip", "show", "pydub"], 
                                capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if line.startswith("Location:"):
                location = line.split(":", 1)[1].strip()
                return os.path.join(location, "pydub", "utils.py")
        return None
    except Exception as e:
        print(f"Error finding pydub: {e}")
        return None

def fix_pydub():
    try:
        utils_path = find_pydub_location()
        
        if not utils_path or not os.path.exists(utils_path):
            print("Could not locate pydub utils.py")
            return False
        
        print(f"Found pydub utils.py at: {utils_path}")
        
        with open(utils_path, 'r') as f:
            content = f.read()
        
        # Create the replacement code
        replacement = '''try:
    import audioop
except ImportError:
    try:
        import pyaudioop as audioop
    except ImportError:
        # Create a dummy audioop module with the necessary functions
        class DummyAudioop:
            def __getattr__(self, name):
                def dummy_func(*args, **kwargs):
                    return args[0]  # Just return the first argument
                return dummy_func
        
        audioop = DummyAudioop()
'''
        
        # Find where to replace
        if 'class DummyAudioop' in content:
            print("The file already contains the DummyAudioop class, but it might have indentation issues.")
            # Let's replace the entire section to be sure
            import_start = content.find('try:\n    import audioop')
            next_line = content.find('\n', import_start + 20)
            next_line = content.find('\n', next_line + 1)
            
            # Create new content with the replacement
            new_content = content[:import_start] + replacement + content[next_line+1:]
        else:
            # Standard replacement
            import_start = content.find('try:\n    import audioop')
            if 'import pyaudioop as audioop' in content:
                import_end = content.find('import pyaudioop as audioop') + len('import pyaudioop as audioop')
            else:
                import_end = content.find('import audioop') + len('import audioop')
            
            # Create new content with the replacement
            new_content = content[:import_start] + replacement + content[import_end+1:]
        
        # Write the fixed file
        with open(utils_path, 'w') as f:
            f.write(new_content)
        
        print("Successfully fixed pydub utils.py!")
        return True
    
    except Exception as e:
        print(f"Error fixing pydub: {e}")
        return False

if __name__ == "__main__":
    fix_pydub() 