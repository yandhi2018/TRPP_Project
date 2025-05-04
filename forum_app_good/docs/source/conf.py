import os
import sys
sys.path.insert(0, os.path.abspath('D:\МИРЭА\2КУРС\2СЕМ\ТРПП\Проект\forum_app_good'))  # Путь к проекту

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon'  # Поддержка NumPy/Google стиля
]

html_theme = 'sphinx_rtd_theme'