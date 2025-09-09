# py2app launcher for motionEye

import sys
from motioneye import meyectl

if __name__ == '__main__':
    # We want the app to run the startserver command.
    # We also need to make sure the path is set up correctly
    # for the bundled environment.
    sys.argv = ['meyectl', 'startserver']
    meyectl.main()
