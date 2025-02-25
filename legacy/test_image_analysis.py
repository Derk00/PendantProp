from analysis.image_analysis import PendantDropAnalysis
import cv2
test_image = cv2.imread("test.png")


analyzer = PendantDropAnalysis()
scale = analyzer.image2scale(test_image)

print(scale)
# pedran.load_raw_image(file_path="graphic/pendant_drop_sarstedtp10.png")
# pedran.process_image()
# pedran.analyse()
# pedran.show_analysis_image()
# pedran.show_processed_image()
# st, img = pedran.image2st(file_path_raw_image="graphic/pendant_drop_sarstedtp10.png")

