import logging


def setup_logger():
    project_logger = logging.getLogger("task_manager_logger")
    project_logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)

    project_logger.addHandler(ch)

    return project_logger


logger = setup_logger()
