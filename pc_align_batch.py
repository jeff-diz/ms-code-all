
import glob
import os
import re
import subprocess

# cwd = r'V:\pgc\data\scratch\jeff\coreg\data'
cwd = os.getcwd()
print(cwd)

dst_dir = os.path.join(cwd, 'coreg', 'pairs')
pairs_txt = os.path.join(cwd, 'coreg', 'data', 'filepath_pairs.txt') ## Change to argument to python

with open(pairs_txt, 'r') as pairs:
	content = pairs.readlines()
	for line in content:
		## Full paths to scene .tifs
		dem1, dem2, _null = line.split(',')
		
		## Get directory holding scene
		dem1_dir = os.path.dirname(dem1)
		print(dem1_dir)
		dem2_dir = os.path.dirname(dem2)

		## Get names of DEMs
		dem1_name = os.path.basename(dem1).split('.')[0]
		print(dem1_name)
		dem2_name = os.path.basename(dem2).split('.')[0]
		
		## Search for all DEM related files
		dem1_pattern = os.path.join(dem1_dir, '{}*'.format(dem1_name))
		dem2_pattern = os.path.join(dem2_dir, '{}*'.format(dem2_name))

		# dem1_files = glob.glob(dem1_pattern)
		# dem2_files = glob.glob(dem2_pattern)

		print(dem1_pattern)
		print(len(dem1_files))

		pair_dir = '{}-{}'.format(dem1_name[0:14], dem2_name[0:14])
		dst = os.path.join(cwd, dst_dir, pair_dir)
		if not os.path.isdir(dst):
			os.mkdir(dst)
		
		## Make symlinks from source to pair dirs
		for f in dem1_files:
			f_name = os.path.basename(f)
			# print(f, os.path.join(dst, f_name))
			#os.symlink(m, dst)
		break


		# cmd = 'qsub -v {} {} ./qsub_pc_align.sh'.format(pair1, pair2)
		# print(cmd)
		# subprocess.Popen(cmd)



