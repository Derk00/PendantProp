from analysis.image import PendantDropAnalysis

pedran = PendantDropAnalysis()
pedran.load_raw_image(file_path="graphic/pendant_drop_sarstedtp10.png")
pedran.process_image()
pedran.analyse()
pedran.show_analysis_image()
# pedran.show_processed_image()
# pedran.image2st(file_path_raw_image="graphic/pendant_drop_sarstedtp10.png")
