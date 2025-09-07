import sys
p='auto_click_gui.py'
try:
    compile(open(p,'rb').read(), p, 'exec')
    print('OK')
except Exception as e:
    print('ERR', e)
