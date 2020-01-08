import argparse, cv2, math

class VideoAnalyzer:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, videofile, output_directory, workers):
		self.videofile = videofile
		self.output_directory = output_directory if output_directory[-1] == '/' else output_directory + '/'
		self.workers = workers

		self._validateData()

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
				processes.append(subprocess.Popen(['python3', 'Modules/Scripts/HMM_row.py', self.videoObj.localTempDir + str(row) + '.npy']))
			for p in processes:
				p.communicate()
		print()
		all_data = []
		# Concatenate all data together
		for row in range(self.height):
			all_data.append(np.load(self.output_directory + str(row) + '.hmm.npy'))
		out_data = np.concatenate(all_data, axis = 0)

		# Save npy and txt files for future use
		baseName = self.videofile.split('/')[-1].split('.mp4')[0] + '_hmm'
		np.save(self.output_directory + baseName + '.npy', out_data)
		with open(self.output_directory + baseName + '.txt', 'w') as f:
			print('Width: ' + str(self.videoObj.width), file = f)
			print('Height: ' + str(self.videoObj.height), file = f)
			print('Frames: ' + str(int(self.HMMsecs*self.videoObj.framerate)), file = f)
			print('Resolution: ' + str(int(self.videoObj.framerate)), file = f)

		# Delete temp data


parser = argparse.ArgumentParser(description='This command runs HMM and cluster analysis on a single video.')
parser.add_argument('Videofile', type = str, help = 'The name of the video file that will be analyzed')
parser.add_argument('Outputdir', type = str, help = 'The name of the output directory that new data will be stored in')
parser.add_argument('Workers', type = int, help = 'The number of workers that should be used to analyze the video')

args = parser.parse_args()