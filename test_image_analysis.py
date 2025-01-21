from analysis.image import PendantDropAnalysis
import cv2

pedran = PendantDropAnalysis()
pedran.load_raw_image(file_path="graphic/pendant_drop.jpg")
pedran.process_image()
# pedran.show_processed_image()
st = pedran.analyse()
# pedran.show_analysis_image()
pedran.save_analysis_image(file_path="C:/Users/pim/Documents/PhD/Code/PendantProp/graphic/test.png")
# pedran.show_processed_image()
