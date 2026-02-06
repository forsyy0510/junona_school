"""
Централизованные модели приложения
"""

from .models import User, News, Announcement, File
from info.models import InfoSection

__all__ = ['User', 'News', 'Announcement', 'File', 'InfoSection']
