import pandas as pd
import datetime

from Modules.DataObjects.LogParser import LogParser as LP
from Modules.DataPreparers.VideoPreparer import VideoPreparer as VP

class ClusterPreparer():
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, projFileManager, workers):

		self.__version__ = '1.0.0'

		self.projFileManager = projFileManager
		self.workers = workers
		

	def validateInputData(self):
		assert os.path.exists(self.projFileManager.localVideoDir)
		for video in self.lp.videos:
			try:
				assert os.path.exists(self.projFileManager.localMasterDir + video.h264_file)
			except AssertionError:
				assert os.path.exists(self.projFileManager.localMasterDir + video.mp4_file)
		assert os.path.exists(self.projFileManager.localLogfile)
		assert os.path.exists(self.projFileManager.localTroubleshootingDir)
		assert os.path.exists(self.projFileManager.localAnalysisDir)
		assert os.path.exists(self.projFileManager.localTempDir)
		assert os.path.exists(self.projFileManager.localAllClipsDir)
		assert os.path.exists(self.projFileManager.localMLlClipsDir)
		assert os.path.exists(self.projFileManager.localMLFramesDir)

		self.lp = LP(projFileManager.localLogfile)

		self.uploads = [(self.projFileManager.localTroubleshootingDir, self.projFileManager.cloudTroubleshootingDir, False), 
						(self.projFileManager.localAnalysisDir, self.projFileManager.cloudAnalysisDir, False)
						(self.projFileManager.localAllClipsDir, self.projFileManager.cloudMasterDir, True)
						(self.projFileManager.localMLClipsDir, self.projFileManager.cloudMasterDir, True)
						(self.projFileManager.localMLFramesDir, self.projFileManager.cloudMasterDir, True)
						]

	def runClusterAnalysis(self):
		clusterData = []
		self.vp_objs = []
		for index in range(len(self.lp.movies)):
			print('Processing video: ' + self.lp.movies[index].mp4_file + ',,Time: ' + str(datetime.datetime.now()))
			self.vp_objs.append(VP(self.projFileManager, index, self.workers))
			clusterData.append(self.vp_objs[index].processVideo())
		allClusterData = pd.concat(clusterData)
		allClusterData.to_csv(self.projFileManager.localAllLabeledClustersFile, sep = ',')
