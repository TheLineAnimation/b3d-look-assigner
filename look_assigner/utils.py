import bpy
import sys
import logging
import os

from pathlib import Path

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def get_project_path():
    open_pype_server_root = os.getenv("OPENPYPE_PROJECT_ROOT_WORK") 
    open_pype_project = os.getenv("AVALON_PROJECT")
    
    if open_pype_server_root and open_pype_project:  
        project_path = Path() / open_pype_server_root / open_pype_project
        return str(project_path)
    else:
        return ""

class LoggerFactory:
    """
    A class to handle logging for the Blender addon.
    """

    LOGGER_NAME = "LookAssignerLogger"
    FORMAT_DEFAULT = "[%(name)s][%(levelname)s] %(message)s"
    LEVEL_DEFAULT = logging.INFO
    PROPAGATE_DEFAULT = True
    _logger_obj = None

    @classmethod
    def get_logger(cls):
        """
        Returns the singleton logger object, creating it if necessary.
        """
        if cls._logger_obj is None:
            cls._logger_obj = logging.getLogger(cls.LOGGER_NAME)
            cls._logger_obj.setLevel(cls.LEVEL_DEFAULT)
            cls._logger_obj.propagate = cls.PROPAGATE_DEFAULT

            fmt = logging.Formatter(cls.FORMAT_DEFAULT)
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(fmt)
            cls._logger_obj.addHandler(stream_handler)
        
        return cls._logger_obj

    @classmethod
    def set_level(cls, level):
        """
        Sets the logging level of the logger.
        """
        logger = cls.get_logger()
        logger.setLevel(level)
        
    @classmethod
    def set_propagate(cls, propagate):
        """
        Sets the propagation property of the logger.
        """
        logger = cls.get_logger()
        logger.propagate = propagate

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        cls.get_logger().debug(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg, *args, **kwargs):
        cls.get_logger().info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg, *args, **kwargs):
        cls.get_logger().warning(msg, *args, **kwargs)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        cls.get_logger().error(msg, *args, **kwargs)

    @classmethod
    def critical(cls, msg, *args, **kwargs):
        cls.get_logger().critical(msg, *args, **kwargs)

    @classmethod
    def log(cls, level, msg, *args, **kwargs):
        cls.get_logger().log(level, msg, *args, **kwargs)

    @classmethod
    def exception(cls, msg, *args, **kwargs):
        cls.get_logger().exception(msg, *args, **kwargs)

    @classmethod
    def write_to_file(cls, path, level=logging.WARNING):
        """
        Writes log messages to a specified file.
        """
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(level)

        fmt = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
        file_handler.setFormatter(fmt)

        logger = cls.get_logger()
        logger.addHandler(file_handler)


if __name__ == "__main__":
    LoggerFactory.set_propagate(False)

    LoggerFactory.debug("debug message")
    LoggerFactory.info("info message")
    LoggerFactory.warning("warning message")
    LoggerFactory.error("error message")
    LoggerFactory.critical("critical message")

