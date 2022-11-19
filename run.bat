@echo off
python main.py test.bic -o test.cpp && cl.bat /EHsc test.cpp