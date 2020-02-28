import os, subprocess, datetime

master_directory = os.getenv('HOME') + '/Dropbox (GaTech)/McGrath/Apps/CichlidPiData/'

#F2Dirs = [x for x in os.listdir(master_directory) if 'newtray' in x and 'F2_' in x]

F2Dirs = ['_newtray_MCxCVF2_15_2', '_newtray_TIxMCF2_19_1','_newtray_MCxCVF2_19_1','_newtray_TIxMCF2_17_2','_newtray_MCxCVF2_16_2','_newtray_TIxMCF2_2_2']

for projectID in F2Dirs:
	projectID = '_newtray_MCxCVF2_15_2'
	print(projectID)
	#print('   Downloading: ' + str(datetime.datetime.now()))
	#subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Depth', projectID, '-d'])
	#print('   Analyzing: '+ str(datetime.datetime.now()))
	#subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Depth', projectID])
	#print('   Backing up: '+ str(datetime.datetime.now()))
	#subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Backup', projectID])
	#print(projectID)
	print('   Downloading: ' + str(datetime.datetime.now()))
	subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Figures', projectID, '-d'])
	#print('   Analyzing: '+ str(datetime.datetime.now()))
	subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Figures', projectID])
	#print('   Backing up: '+ str(datetime.datetime.now()))
	subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Backup', projectID])
