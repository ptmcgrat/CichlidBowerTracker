from sklearn.cluster import DBSCAN
from sklearn.neighbors import radius_neighbors_graph
from sklearn.neighbors import NearestNeighbors

from Modules.DataObjects.HMMAnalyzer import HMMAnalyzer as HA

import numpy as np
import pandas as pd
import os, cv2, math, datetime, subprocess, pdb, random, sys, argparse

class VideoAnalyzer:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, videofile, output_directory, workers, minMagnitude, delta, timeScale, treeR, leafNum, neighborR, minPts, eps):
		self.videofile = videofile
		self.output_directory = output_directory if output_directory[-1] == '/' else output_directory + '/'
		self.workers = workers
		self.minMagnitude = minMagnitude
		self.delta = delta
		self.timeScale = timeScale
		self.treeR = treeR
		self.leafNum = leafNum
		self.neighborR = neighborR
		self.minPts = minPts
		self.eps = eps

		self.baseName = videofile.split('/')[-1].split('.mp4')[0]

		self._validateData()
		self._decompressVideo()
		self._calculateHMM()
		self._createClusters()

	def _validateData(self):
		try:
			assert '.mp4' in self.videofile
			assert os.path.isfile(self.videofile)

		except AssertionError as e:
			print('Error with videofile:' + print(e))

		cap = cv2.VideoCapture(self.videofile)
		self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
		self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
		self.framerate = int(cap.get(cv2.CAP_PROP_FPS))
		self.frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
		self.HMMsecs = int(self.frames/self.framerate)

		print('  HMM_Maker. VideoInfo: Size: ' + str((self.height,self.width)) + ',,fps: ' + str(self.framerate) + ',,Frames: ' + str(self.frames))

		cap.release()

		if not os.path.exists(self.output_directory):
			os.makedirs(self.output_directory)

	def _decompressVideo(self):

		self.blocksize = 5*60 # Decompress videos in 5 minute chunks

		totalBlocks = math.ceil(self.HMMsecs/(self.blocksize)) #Number of blocks that need to be analyzed for the full video
		print('  HMM_Maker:Decompressing video into 1 second chunks,,Time: ' + str(datetime.datetime.now()))
		print('    ' + str(totalBlocks) + ' total blocks. On block ', end = '', flush = True)
		
		for i in range(0, totalBlocks, self.workers):
			print(str(i) + '-' + str(min(i+self.workers, totalBlocks - 1)) + ',', end = '', flush = True)
			processes = []
			for j in range(self.workers):
				if i + j >= totalBlocks:
					break
				min_time = int((i+j)*self.blocksize)
				max_time = int(min((i+j+1)*self.blocksize, self.HMMsecs))
				
				if max_time < min_time:
					pdb.set_trace()

				arguments = [self.videofile, str(self.framerate), str(min_time), str(max_time), self.output_directory + 'Decompressed_' + str(i+j) + '.npy']
				processes.append(subprocess.Popen(['python3', 'Modules/Scripts/Decompress_block.py'] + arguments))
			
			for p in processes:
				p.communicate()
		
		
		print()
		print('  Combining data into rowfiles,,Time: ' + str(datetime.datetime.now()))
		for row in range(self.height):
			row_file = self.output_directory + str(row) + '.npy'
			if os.path.isfile(row_file):
				subprocess.run(['rm', '-f', row_file])
		print('    ' + str(totalBlocks) + ' total blocks. On block: ', end = '', flush = True)
		for i in range(0, totalBlocks, self.workers):
			print(str(i) + '-' + str(min(i+self.workers, totalBlocks - 1)) + ',', end = '', flush = True)
			data = []
			for j in range(self.workers):
				block = i + j
				if block >= totalBlocks:
					break

				data.append(np.load(self.output_directory + 'Decompressed_' + str(block) + '.npy'))

			alldata = np.concatenate(data, axis = 2)

			for row in range(self.height):
				row_file = self.output_directory + str(row) + '.npy'
				out_data = alldata[row]
				if os.path.isfile(row_file):
					out_data = np.concatenate([np.load(row_file),out_data], axis = 1)
				np.save(row_file, out_data)

				# Verify size is right
				if block + 1 == totalBlocks:
					try:
						assert out_data.shape == (self.width, self.HMMsecs)
					except AssertionError:
						pdb.set_trace()
			
			for j in range(self.workers):
				block = i + j
				subprocess.run(['rm', '-f', self.output_directory + 'Decompressed_' + str(block) + '.npy'])
		print()

	def _calculateHMM(self):
		print('  Calculating HMMs for each row,,Time: ' + str(datetime.datetime.now())) 
		# Calculate HMM on each block

		print('    ' + str(self.height) + ' total rows. On rows ', end = '', flush = True)

		for i in range(0, self.height, self.workers):
			start_row = i
			stop_row = min((i + self.workers,self.height))
			print(str(start_row) + '-' + str(stop_row - 1) + ',', end = '', flush = True)
			processes = []
			for row in range(start_row, stop_row):
				processes.append(subprocess.Popen(['python3', 'Modules/Scripts/HMM_row.py', self.output_directory + str(row) + '.npy']))
			for p in processes:
				p.communicate()
		print()
		all_data = []
		# Concatenate all data together
		for row in range(self.height):
			all_data.append(np.load(self.output_directory + str(row) + '.hmm.npy'))
			subprocess.run(['rm', '-f', self.output_directory + str(row) + '.hmm.npy'])
		out_data = np.concatenate(all_data, axis = 0)

		# Save npy and txt files for future use
		np.save(self.output_directory + self.baseName + '_hmm.npy', out_data)
		with open(self.output_directory + self.baseName + '_hmm.txt', 'w') as f:
			print('Width: ' + str(self.width), file = f)
			print('Height: ' + str(self.height), file = f)
			print('Frames: ' + str(int(self.HMMsecs*self.framerate)), file = f)
			print('Resolution: ' + str(int(self.framerate)), file = f)

		# Delete temp data
	def _createClusters(self):
		print('  Creating clusters from HMM transitions,,Time: ' + str(datetime.datetime.now())) 

		# Load in HMM data
		hmmObj = HA(self.output_directory + self.baseName + '_hmm')

		# Convert into coords object and save it
		coords = hmmObj.retDBScanMatrix(self.minMagnitude)
		np.save(self.output_directory + self.baseName + '_coords.npy', coords)
		
		# Run data in batches to avoid RAM override
		sortData = coords[coords[:,0].argsort()][:,0:3] #sort data by time for batch processing, throwing out 4th column (magnitude)
		numBatches = int(sortData[-1,0]/self.delta/3600) + 1 #delta is number of hours to batch together. Can be fraction.

		sortData[:,0] = sortData[:,0]*self.timeScale #scale time so that time distances between transitions are comparable to spatial differences
		labels = np.zeros(shape = (sortData.shape[0],1), dtype = sortData.dtype) # Initialize labels

		#Calculate clusters in batches to avoid RAM overuse
		curr_label = 0 #Labels for each batch start from zero - need to offset these 
		print('   ' + str(numBatches) + ' total batches. On batch: ', end = '', flush = True)
		for i in range(numBatches):
			print(str(i) + ',', end = '', flush = True)

			min_time, max_time = i*self.delta*self.timeScale*3600, (i+1)*self.delta*self.timeScale*3600 # Have to deal with rescaling of time. 3600 = # seconds in an hour
			hour_range = np.where((sortData[:,0] > min_time) & (sortData[:,0] <= max_time))
			min_index, max_index = hour_range[0][0], hour_range[0][-1] + 1
			X = NearestNeighbors(radius=self.treeR, metric='minkowski', p=2, algorithm='kd_tree',leaf_size=self.leafNum,n_jobs=24).fit(sortData[min_index:max_index])
			dist = X.radius_neighbors_graph(sortData[min_index:max_index], self.neighborR, 'distance')
			sub_label = DBSCAN(eps=self.eps, min_samples=self.minPts, metric='precomputed', n_jobs=self.workers).fit_predict(dist)
			new_labels = int(sub_label.max()) + 1
			sub_label[sub_label != -1] += curr_label
			labels[min_index:max_index,0] = sub_label
			curr_label += new_labels
		print()
		# Concatenate and save information
		sortData[:,0] = sortData[:,0]/self.timeScale
		labeledCoords = np.concatenate((sortData, labels), axis = 1).astype('int64')
		np.save(self.output_directory + self.baseName + '.labeledCoords.npy', labeledCoords)
		print('  Concatenating and summarizing clusters,,Time: ' + str(datetime.datetime.now())) 

		df = pd.DataFrame(labeledCoords, columns=['T','X','Y','LID'])
		clusterData = df.groupby('LID').apply(lambda x: pd.Series({
			'N': x['T'].count(),
			't': int(x['T'].mean()),
			'X': int(x['X'].mean()),
			'Y': int(x['Y'].mean()),
			't_span': int(x['T'].max() - x['T'].min()),
			'X_span': int(x['X'].max() - x['X'].min()),
			'Y_span': int(x['Y'].max() - x['Y'].min()),
		})
		)

		clusterData.to_csv(self.output_directory + self.baseName + '.clusters.csv', sep = ',')

parser = argparse.ArgumentParser(description='This command runs HMM and cluster analysis on a single video.')
parser.add_argument('Videofile', type = str, help = 'The name of the video file that will be analyzed')
parser.add_argument('Outputdir', type = str, help = 'The name of the output directory that new data will be stored in')
parser.add_argument('Workers', type = int, help = 'The number of workers that should be used to analyze the video')
parser.add_argument('--MinMagnitude', type = int, default = 0)
parser.add_argument('--Delta', type = float, default = 1.0)
parser.add_argument('--TimeScale', type = int, default = 10)
parser.add_argument('--TreeR', type = int, default = 22)
parser.add_argument('--LeafNum', type = int, default = 190)
parser.add_argument('--NeighborR', type = int, default = 22)
parser.add_argument('--MinPts', type = int, default = 90)
parser.add_argument('--Eps', type = int, default = 18)

args = parser.parse_args()

videoObj = VideoAnalyzer(args.Videofile, args.Outputdir, args.Workers, args.MinMagnitude, args.Delta, args.TimeScale, args.TreeR, args.LeafNum, args.NeighborR, args.MinPts, args.Eps)