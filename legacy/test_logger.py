from utils.logger import Logger


log_1 = Logger("test_1", file_path="experiments")
log_2 = Logger("test_2", file_path="experiments")

log_1.info("test_1")
log_2.info("test_2")
