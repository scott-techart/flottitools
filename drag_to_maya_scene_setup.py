import os
import sys


def onMayaDroppedPythonFile(*args):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    repo_dir_path = os.path.dirname(dir_path)
    sys.path.append(repo_dir_path)
    import flottitools.install as install
    install.install()
    print args
    print dir_path
