#!D:\flask\cms\venv\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'coscmd==1.8.6.16','console_scripts','coscmd'
__requires__ = 'coscmd==1.8.6.16'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('coscmd==1.8.6.16', 'console_scripts', 'coscmd')()
    )
