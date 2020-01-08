import os, subprocess, pdb, random
import pandas as pd

class AnFileManager():
	def __init__(self, localMasterDir, cloudMasterDir):
		self.annotationDir = '__AnnotatedData/'
		self.localMasterDir = localMasterDir + self.annotationDir
		self.cloudMasterDir = cloudMasterDir + self.annotationDir
		self._createFileDirectoryNames()

	def prepareVideoAnnotation(self, annotationID):
		self.cloudClipDir = self.cloudMasterDir + 'LabeledVideos/' + annotationID + '/'
		self.localClipDir = self.localMasterDir + 'LabeledVideos/' + annotationID + '/'
		
		# Download clip dir
		subprocess.run(['rclone', 'copy', self.cloudClipDir, self.localClipDir], stderr = subprocess.PIPE)
		if not os.path.exists(self.localClipDir):
			raise FileNotFoundError('Unable to download ' + self.cloudClipDir)

		# Untar clips
		for tarredClipDir in [self.localClipDir + 'Clips/' + x for x in os.listdir(self.localClipDir + 'Clips/') if '.tar' in x]:
			subprocess.run(['tar', '-xvf', tarredClipDir, '-C', self.localClipDir + 'Clips/'], stderr = subprocess.PIPE)
			subprocess.run(['rm', '-f', tarredClipDir])

		
		# Read in manual annotations
		dt = pd.read_csv(self.localClipDir + 'ManualLabels.csv', sep = ',')

		# Iterate through manual annotations and keep track of 
		for index, row in dt.iterrows():
			projectID = row.ClipName.split('__')[0]
			clipName = row.ClipName + '.mp4'
			label = row.ManualLabel

			if random.randint(0,5) == 0:
				dataset = 'validation/'
			else:
				dataset = 'training/'

			os.makedirs(self.localClipDir + 'LabeledClips/' + dataset + label, exist_ok = True)
			output = subprocess.run(['mv', self.localClipDir + 'Clips/' + projectID + '/' + clipName, self.localClipDir + 'LabeledClips/' + dataset + label], stderr = subprocess.PIPE, encoding = 'utf-8')
			if output.stderr != '':
				print(clipName)

		return self.localClipDir + 'LabeledClips/'

	def downloadBoxedProject(self, projectID):
		self.localBoxedImagesProjDir = self.localBoxedImagesDir + projectID + '/'
		self._createDirectory(self.localBoxedFishesDir)
		
		#print(['rclone', 'copy', self.cloudBoxesAnnotationFile, self.localBoxedFishesDir])
		subprocess.run(['rclone', 'copy', self.cloudBoxesAnnotationFile, self.localBoxedFishesDir], stderr = subprocess.PIPE)
		subprocess.run(['rclone', 'copy', self.cloudBoxedImagesDir + projectID + '.tar', self.localBoxedImagesDir], stderr = subprocess.PIPE)
		if os.path.exists(self.localBoxedImagesDir + projectID + '.tar'):
			output = subprocess.run(['tar', '-xvf', self.localBoxedImagesDir + projectID + '.tar', '-C', self.localBoxedImagesDir], stderr = subprocess.PIPE, encoding = 'utf-8')
			#print(output.stderr)
			#print(['tar', '-xvf', self.localBoxedImagesDir + projectID + '.tar', '-C', self.localBoxedImagesDir])
		else:
			self._createDirectory(self.localBoxedImagesProjDir)
		#subprocess.run(['rm', '-rf', self.localBoxedImagesDir + projectID + '.tar'], stderr = subprocess.PIPE)

	def backupBoxedProject(self, projectID):
		subprocess.run(['rclone', 'copy', self.localBoxesAnnotationFile, self.cloudBoxedFishesDir], stderr = subprocess.PIPE)
		subprocess.run(['tar', '-cvf', self.localBoxedImagesDir + projectID + '.tar', '-C', self.localBoxedImagesDir, projectID], stderr = subprocess.PIPE)
		subprocess.run(['rclone', 'copy', self.localBoxedImagesDir + projectID + '.tar', self.cloudBoxedImagesDir], stderr = subprocess.PIPE)
		subprocess.run(['rm', '-rf', self.localMasterDir], stderr = subprocess.PIPE)


	def _createFileDirectoryNames(self):
		self.localLabeledVideosDir = self.localMasterDir + 'LabeledVideos/'
		self.cloudLabeledVideosDir = self.cloudMasterDir + 'LabeledVideos/'
			
		self.boxedFishes = 'BoxedFishes/'
		self.localBoxedFishesDir = self.localMasterDir + 'BoxedFish/'
		self.cloudBoxedFishesDir = self.cloudMasterDir + 'BoxedFish/'

		self.boxesAnnotationFile = 'BoxedFish.csv'
		self.localBoxesAnnotationFile = self.localBoxedFishesDir + self.boxesAnnotationFile
		self.cloudBoxesAnnotationFile = self.cloudBoxedFishesDir + self.boxesAnnotationFile

		self.boxedImagesDir = 'BoxedImages/'
		self.localBoxedImagesDir = self.localBoxedFishesDir + self.boxedImagesDir
		self.cloudBoxedImagesDir = self.cloudBoxedFishesDir + self.boxedImagesDir

	
	def _createDirectory(self, directory):
		if not os.path.exists(directory):
			os.makedirs(directory)

